# Examples — Einstein Activity Capture API

## Example 1: Custom Activity Score Using ActivityMetric

**Context:** A sales ops team wants a custom "Engagement Score" field on Contact, calculated from the last 60 days of EAC email and meeting activity. The score feeds a list view filter for reps to prioritize outreach.

**Problem:** A developer queries `[SELECT Id FROM Task WHERE ActivityDate >= :cutoff AND WhoId = :contactId]` expecting EAC emails to appear. The query returns zero rows. The developer spends hours checking sharing rules and FLS, finding nothing wrong — because the data simply is not in the Task object for standard EAC orgs.

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

**Why it works:** `ActivityMetric` is the only SOQL-accessible aggregate surface for EAC data in standard (non-Write-Back) orgs. Querying it with `WhoId IN :contactIds` is efficient and within governor limits. Initialising the map with zeros before the query loop means contacts with no connected accounts receive a score of zero rather than being absent from the result.

---

## Example 2: Lightning Web Component Displaying Engagement Metrics

**Context:** A product team wants a custom LWC on the Contact record page that shows a 90-day email engagement summary. The org is on standard EAC without Write-Back.

**Problem:** The developer builds an LWC that calls an Apex method querying `EmailMessage WHERE ToAddress = :contact.Email`. The component always shows "No activity" because EAC-synced emails are not in the `EmailMessage` object in standard EAC orgs.

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

## Anti-Pattern: Querying Task or Event for EAC Synced Activities

**What practitioners do:** Developers write `[SELECT Id, Subject FROM Task WHERE WhoId = :contactId AND ActivitySource = 'EAC']` or similar, assuming EAC creates standard Task records that can be filtered.

**What goes wrong:** The query compiles and runs without error. It returns zero rows. Developers spend time debugging sharing rules, field-level security, and object permissions — none of which are the problem. The root cause is that standard EAC does not write records into the Task object. The SOQL engine correctly reports no results because no records exist in that object.

**Correct approach:** Query `ActivityMetric` for aggregate counts. If individual activity records are required, confirm whether the org has EAC Write-Back (Summer '25+) enabled and whether `UnifiedActivity` is provisioned. If neither is available, use the Activity Timeline UI component for visual display — it reads from the EAC external store directly.
