# Examples — Einstein Activity Capture API

> **Architecture note.** Examples 1 and 2 target **legacy EAC**, where `ActivityMetric` is the only aggregate surface. That surface retires in Spring '27 (February 2027) and returns null before then. Read them for orgs that have not yet migrated; for new work, start at Example 3.

## Example 1: Custom Activity Score Using ActivityMetric (Legacy EAC)

**Context:** A sales ops team wants a custom "Engagement Score" field on Contact, calculated from the last 60 days of EAC email and meeting activity. The score feeds a list view filter for reps to prioritize outreach.

**Problem:** A developer queries `[SELECT Id FROM Task WHERE ActivityDate >= :cutoff AND WhoId = :contactId]` expecting EAC emails to appear. The query returns zero rows. The developer spends hours checking sharing rules and FLS, finding nothing wrong — because the data simply is not in the Task object for legacy EAC orgs.

**Solution:**

```apex
public with sharing class ContactEngagementScoreService {

    public static Map<Id, Decimal> computeScores(Set<Id> contactIds) {
        Date cutoff = Date.today().addDays(-60);

        List<ActivityMetric> metrics = [
            SELECT WhoId, EmailCount, EmailOpenCount, EmailReplyCount, MeetingCount
            FROM ActivityMetric
            WHERE WhoId IN :contactIds
              AND ActivityDate >= :cutoff
        ];

        Map<Id, Decimal> scoreByContact = new Map<Id, Decimal>();
        // Initialise to zero so contacts with no EAC data are still returned
        for (Id cId : contactIds) {
            scoreByContact.put(cId, 0);
        }

        for (ActivityMetric m : metrics) {
            Decimal score = scoreByContact.get(m.WhoId);
            // Weight: email sent = 1pt, open = 2pt, reply = 5pt, meeting = 10pt
            score += (m.EmailCount      ?? 0) * 1
                   + (m.EmailOpenCount  ?? 0) * 2
                   + (m.EmailReplyCount ?? 0) * 5
                   + (m.MeetingCount    ?? 0) * 10;
            scoreByContact.put(m.WhoId, score);
        }

        return scoreByContact;
    }
}
```

**Why it works:** `ActivityMetric` is the only SOQL-accessible aggregate surface for EAC data on **legacy** EAC orgs. Querying it with `WhoId IN :contactIds` is efficient and within governor limits. Initialising the map with zeros before the query loop means contacts with no connected accounts receive a score of zero rather than being absent from the result.

---

## Example 2: Lightning Web Component Displaying Engagement Metrics (Legacy EAC)

**Context:** A product team wants a custom LWC on the Contact record page that shows a 90-day email engagement summary. The org is on legacy EAC.

**Problem:** The developer builds an LWC that calls an Apex method querying `EmailMessage WHERE ToAddress = :contact.Email`. The component always shows "No activity" because EAC-synced emails are not in the `EmailMessage` object in legacy EAC orgs.

**Solution:**

```apex
// EacEngagementController.cls
public with sharing class EacEngagementController {

    @AuraEnabled(cacheable=true)
    public static EngagementSummary getEngagementSummary(Id contactId) {
        Date cutoff = Date.today().addDays(-90);

        List<ActivityMetric> rows = [
            SELECT ActivityDate, EmailCount, EmailOpenCount,
                   EmailReplyCount, MeetingCount
            FROM ActivityMetric
            WHERE WhoId = :contactId
              AND ActivityDate >= :cutoff
            ORDER BY ActivityDate DESC
        ];

        EngagementSummary summary = new EngagementSummary();
        for (ActivityMetric m : rows) {
            summary.totalEmails   += (Integer)(m.EmailCount      ?? 0);
            summary.totalOpens    += (Integer)(m.EmailOpenCount  ?? 0);
            summary.totalReplies  += (Integer)(m.EmailReplyCount ?? 0);
            summary.totalMeetings += (Integer)(m.MeetingCount    ?? 0);
        }
        summary.dataAvailable = !rows.isEmpty();
        return summary;
    }

    public class EngagementSummary {
        @AuraEnabled public Integer totalEmails   = 0;
        @AuraEnabled public Integer totalOpens    = 0;
        @AuraEnabled public Integer totalReplies  = 0;
        @AuraEnabled public Integer totalMeetings = 0;
        @AuraEnabled public Boolean dataAvailable = false;
    }
}
```

```javascript
// engagementSummary.js (LWC wire call)
import { LightningElement, api, wire } from 'lwc';
import getEngagementSummary from '@salesforce/apex/EacEngagementController.getEngagementSummary';

export default class EngagementSummary extends LightningElement {
    @api recordId;

    @wire(getEngagementSummary, { contactId: '$recordId' })
    summary;

    get hasData() {
        return this.summary?.data?.dataAvailable;
    }
}
```

**Why it works:** The Apex controller queries `ActivityMetric` — the correct SOQL surface — rather than `EmailMessage`. The `cacheable=true` annotation allows the platform to cache results and reduce SOQL calls on repeat page loads. The `dataAvailable` flag lets the component show a meaningful "No EAC data" message when the contact's owner has no connected account.

---

## Example 3: Migrating Example 1 Off the Retiring Activity Metrics Layer

**Context:** The `ContactEngagementScoreService` from Example 1 has been in production for two years. The org has moved to Sync Email as Salesforce Activity. Salesforce Help now states that "Activity Metrics fields no longer populate. Custom code or reports referencing these fields return null values," ahead of retirement in "Spring '27 (February 2027)."

**Problem:** Nothing breaks. The class compiles, the query runs, the tests pass — they seed their own `ActivityMetric` rows in `@isTest`, so the suite never touches the real surface. Production quietly returns 0 for every contact, and the sales team reads a fabricated engagement collapse.

**Solution:** Aggregate the standard Activity records the new architecture writes — "Recreate your activity reporting on Task and EmailMessage objects grouped by Account or Opportunity."

```apex
public with sharing class ContactEngagementScoreService {

    public static Map<Id, Decimal> computeScores(Set<Id> contactIds) {
        Date cutoff = Date.today().addDays(-60);

        Map<Id, Decimal> scoreByContact = new Map<Id, Decimal>();
        for (Id cId : contactIds) {
            scoreByContact.put(cId, 0);   // absent != disengaged
        }

        // Captured email is a standard Task under Sync Email as Salesforce Activity.
        // WITH USER_MODE: this reads synced private correspondence, so enforce the
        // running user's object/field permissions and sharing rather than inherit a
        // default that depends on the class's apiVersion.
        for (AggregateResult ar : [
            SELECT WhoId whoId, COUNT(Id) taskCount
            FROM Task
            WHERE WhoId IN :contactIds
              AND ActivityDate >= :cutoff
            WITH USER_MODE
            GROUP BY WhoId
        ]) {
            Id whoId = (Id) ar.get('whoId');
            // COUNT() returns an Integer. Casting the Object straight to Decimal
            // throws System.TypeException: Invalid conversion from runtime type
            // Integer to Decimal — cast to Integer and let it widen.
            Integer taskCount = (Integer) ar.get('taskCount');
            scoreByContact.put(whoId, taskCount);
        }
        return scoreByContact;
    }
}
```

**Why it works:** It reads a surface with no retirement date. `GROUP BY` does the rollup in the query rather than the heap, so the aggregate cost does not grow with activity volume. The zero-initialisation from Example 1 is kept deliberately — it still distinguishes "no activity measured" from "contact not in scope," which is the one thing the null-return failure destroys.

**What this example does not do:** it does not reproduce Example 1's weighted open/reply scoring, because `EmailOpenCount` and `EmailReplyCount` have no direct standard-object equivalent. Engagement weighting that depended on those fields is a product decision to re-take, not a mechanical port — and per Help, a score that must stay filterable should "use flows or scheduled jobs to compute and persist engagement scores into custom fields."

---

## Anti-Pattern: Querying Task or Event for EAC Synced Activities

**What practitioners do:** Developers write `[SELECT Id, Subject FROM Task WHERE WhoId = :contactId AND ActivitySource = 'EAC']` or similar, assuming EAC creates standard Task records that can be filtered.

**What goes wrong:** The query compiles and runs without error. It returns zero rows. Developers spend time debugging sharing rules, field-level security, and object permissions — none of which are the problem. The root cause is that legacy EAC does not write records into the Task object. The SOQL engine correctly reports no results because no records exist in that object.

**Correct approach:** Establish the architecture first. On **Sync Email as Salesforce Activity** the `Task` query is right and only the invented `ActivitySource = 'EAC'` filter is wrong — captured email is a standard Task. On **legacy** EAC, query `ActivityMetric` for aggregate counts, use `UnifiedActivity` if provisioned, or fall back to the Activity Timeline UI component, which reads the external store directly. Do not present `ActivityMetric` as the durable answer: it retires in Spring '27 and returns null before then (see Example 3).
