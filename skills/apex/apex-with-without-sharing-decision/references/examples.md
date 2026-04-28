### Examples — Apex With / Without / Inherited Sharing Decision

## Example 1: AuraEnabled controller for an LWC case-list

**Context:** A service-cloud LWC lists cases assigned to the running
user. The data comes from an Apex `@AuraEnabled` controller.

**Problem:** A previous version of the controller had no sharing keyword.
QA reported that during one test, a low-privilege agent saw cases
belonging to a different region. Root cause: the bare class was being
called transitively from a `without sharing` async job and ran without
sharing.

**Solution:**

```apex
public with sharing class CaseListController {

    @AuraEnabled(cacheable=true)
    public static List<Case> getMyCases(Id ownerId) {
        return [
            SELECT Id, CaseNumber, Subject, Status, Priority
            FROM Case
            WHERE OwnerId = :ownerId
            ORDER BY CreatedDate DESC
            LIMIT 200
        ];
    }
}
```

**Why it works:** explicit `with sharing` cannot be overridden by the
caller. Even if a `without sharing` job invokes
`CaseListController.getMyCases`, the query still enforces sharing rules.

---

## Example 2: Reusable selector with `inherited sharing`

**Context:** `AccountSelector` is a thin SOQL wrapper used by an
`@AuraEnabled` controller (user context) AND by a nightly batch (system
context). The same selector should respect each caller's intent.

**Problem:** Originally declared `with sharing`. The nightly batch
silently dropped 30% of accounts because the integration user lacked
visibility — discovered weeks later when MRR reports were short.

**Solution:**

```apex
public inherited sharing class AccountSelector {

    public List<Account> selectByIds(Set<Id> ids) {
        return [SELECT Id, Name, OwnerId FROM Account WHERE Id IN :ids];
    }

    public List<Account> selectActive() {
        return [SELECT Id, Name FROM Account WHERE IsActive__c = true];
    }
}
```

When called from `with sharing CaseController`, queries enforce the
agent's visibility. When called from `without sharing
NightlyAggregationBatch`, queries see all accounts. The selector itself
takes no opinion.

**Why it works:** `inherited sharing` makes the inheritance explicit and
auditable. Reviewers reading the selector know the keyword is
intentional, not an oversight.

---

## Example 3: Batch job aggregating across all tenants

**Context:** A scheduled batch nightly aggregates revenue across every
opportunity in the org regardless of who owns it, writing the result to
a custom `Org_Metric__c` record.

**Problem:** When run as the integration user (a Sales Cloud user with
limited role hierarchy access), a `with sharing` version of this batch
under-counted revenue by ~$2M because opportunities outside the user's
perimeter were filtered out of `start()`.

**Solution:**

```apex
// reason: org-wide revenue aggregation must include opportunities
//         outside the integration user's role hierarchy.
public without sharing class RevenueAggregationBatch
        implements Database.Batchable<SObject>, Schedulable {

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator(
            'SELECT Id, Amount, CloseDate FROM Opportunity WHERE IsClosed = true'
        );
    }

    public void execute(Database.BatchableContext ctx, List<Opportunity> scope) {
        Decimal total = 0;
        for (Opportunity o : scope) {
            total += (o.Amount == null ? 0 : o.Amount);
        }
        // ... upsert Org_Metric__c
    }

    public void finish(Database.BatchableContext ctx) {}

    public void execute(SchedulableContext sctx) {
        Database.executeBatch(this, 200);
    }
}
```

**Why it works:** the `// reason:` comment documents intent for future
reviewers. The class explicitly elevates only the data-aggregation job;
no `@AuraEnabled` surface is exposed.

---

## Anti-Pattern: Defaulting to `without sharing` "to avoid permission errors"

**What practitioners do:** Stack-overflow-driven development — copy a
snippet and paste `without sharing` to silence permission errors during
development.

**What goes wrong:** The class ships to production. Now every record the
controller surfaces ignores sharing rules — a textbook insecure direct
object reference. Security review months later finds the class can
return any record by ID.

**Correct approach:** keep the class `with sharing`. If permission errors
appear during development, fix the user's permission set or use
`WITH SYSTEM_MODE` on the *one* offending query with a comment
explaining why elevation is required there.
