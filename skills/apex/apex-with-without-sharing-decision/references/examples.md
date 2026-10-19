### Examples — Apex With / Without / Inherited Sharing Decision

## Example 1: AuraEnabled controller for an LWC case-list

**Context:** A service-cloud LWC lists cases assigned to the running
user. The data comes from an Apex `@AuraEnabled` controller.

**Problem:** A previous version of the controller had no sharing keyword.
QA reported that during one test, a low-privilege agent saw cases
belonging to a different region. Root cause: the class was pinned below
API 67.0, where a bare class called transitively from a `without sharing`
async job ran without sharing. (At 67.0+ the bare default is `with
sharing` and this particular path would not have leaked — but the fix is
the same, because the default is not what you want a perimeter to rest
on.)

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

    // The caller states the access mode. At API 67.0+ an unqualified query
    // runs in user mode and enforces sharing whatever the caller's keyword.
    public List<Account> selectByIds(Set<Id> ids, AccessLevel mode) {
        return Database.queryWithBinds(
            'SELECT Id, Name, OwnerId FROM Account WHERE Id IN :ids',
            new Map<String, Object>{ 'ids' => ids },
            mode
        );
    }

    public List<Account> selectActive(AccessLevel mode) {
        return Database.query(
            'SELECT Id, Name FROM Account WHERE IsActive__c = true', mode
        );
    }
}
```

When called from `with sharing CaseController` with
`AccessLevel.USER_MODE`, queries enforce the agent's visibility. When
called from `without sharing NightlyAggregationBatch` with
`AccessLevel.SYSTEM_MODE`, queries see all accounts: system mode lifts
FLS/CRUD, and the row filter follows the inherited `without sharing`.
The `AccessLevel` parameter is what makes this work at API 67.0+, where
an unqualified query runs in user mode and enforces sharing whatever the
caller's keyword (Apex Developer Guide L11954-11961). The selector
itself takes no opinion.

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
        // WITH SYSTEM_MODE is required at API 67.0+: without it the query
        // runs in user mode and enforces sharing despite `without sharing`.
        return Database.getQueryLocator(
            'SELECT Id, Amount, CloseDate FROM Opportunity WHERE IsClosed = true WITH SYSTEM_MODE'
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
no `@AuraEnabled` surface is exposed. The two axes are both stated:
`without sharing` lifts the row filter for system-mode queries, and
`WITH SYSTEM_MODE` puts the query in system mode.

---

## Example 4: One elevated read from a `with sharing` controller

**Context:** An LWC controller is `with sharing`. One method must load
the `Region_Config__c` record for the user's region; that object is
Private and the record is owned by an admin, so the user cannot see it.

**Problem:** The first fix added `WITH SYSTEM_MODE` to the query in the
controller. The FLS error on `Escalation_Queue__c` went away, but the
query still returned no row: in system mode, record sharing follows the
class keyword (Apex Developer Guide L11960-11961), and the class is
`with sharing`.

**Solution:**

```apex
public with sharing class RegionConfigController {

    @AuraEnabled(cacheable=true)
    public static Region_Config__c getConfig() {
        // Region comes from the running user's own record, never from the
        // client, so the elevated read cannot be pointed at another region.
        String region = [
            SELECT Region__c FROM User WHERE Id = :UserInfo.getUserId()
        ].Region__c;
        return ConfigReader.forRegion(region);
    }

    // reason: Region_Config__c is Private and admin-owned; users need the
    //         one row for their region, read-only, fields chosen here.
    private without sharing class ConfigReader {
        public static Region_Config__c forRegion(String region) {
            List<Region_Config__c> rows = [
                SELECT Id, Escalation_Queue__c, SLA_Hours__c
                FROM Region_Config__c
                WHERE Region__c = :region
                WITH SYSTEM_MODE
                LIMIT 1
            ];
            return rows.isEmpty() ? null : rows[0];
        }
    }
}
```

**Why it works:** the inner class carries its own keyword — "inner
classes don't adopt the sharing mode of the container class" (L4931) —
and its method runs in the mode of the class where it is defined
(L4927). `without sharing` lifts the row filter; `WITH SYSTEM_MODE` keeps
the query in system mode at API 67.0+, where an unqualified query would
run in user mode and enforce sharing anyway (L11954-11959). The
elevation is one query wide, its filter comes from the running user's
own record (nothing the client sends), and the `// reason:` comment sits above the class the checker
reads. Test it with `System.runAs` as a user who cannot see the record.

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
appear during development, fix the user's permission set. If the error
is FLS or object access on rows the user can already see, use
`WITH SYSTEM_MODE` on the *one* offending query with a comment
explaining why. If the user genuinely needs rows outside their
perimeter, `WITH SYSTEM_MODE` will not return them from a `with sharing`
class — use the inner `without sharing` helper of Example 4.
