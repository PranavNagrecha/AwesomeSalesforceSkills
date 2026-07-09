# Examples — SOQL FOR VIEW and FOR REFERENCE

All code below is illustrative scaffolding authored from the official SOQL and SOSL Reference.
Replace object/field names and namespaces with your own. `FOR VIEW` / `FOR REFERENCE` are
documented as current in the Summer '26 (API 67.0) reference; the docs do not stamp them
Beta, Pilot, or deprecated — do not assert a maturity level they do not state.

## Example 1: Custom record viewer marks a record viewed (FOR VIEW)

**Context:** a custom LWC opens a single Opportunity for the user to read, standing in for a
standard record page. The team notices these records never appear in the user's Recent Items.

**Problem:** a custom surface running its own SOQL does not write recency data — only standard
Lightning record pages do. Without opting in, the record stays out of Recent Items and
global-search auto-complete.

**Solution:**

Keep the query in the selector layer (see `templates/apex/BaseSelector.cls`), bound it to the
specific record, and append `FOR VIEW`:

```apex
public with sharing class OpportunityViewSelector extends BaseSelector {
    // Called only from a user-facing controller when the user opens this record.
    public Opportunity selectForView(Id recordId) {
        assertNotNull(recordId, 'recordId');
        List<Opportunity> rows = Database.queryWithBinds(
            'SELECT Id, Name, StageName, Amount ' +
            'FROM Opportunity WHERE Id = :recordId LIMIT 1 FOR VIEW',
            new Map<String, Object>{ 'recordId' => recordId },
            userMode()  // AccessLevel.USER_MODE — only touch records the user can see
        );
        return rows.isEmpty() ? null : rows[0];
    }
}
```

**Why it works:** `FOR VIEW` updates `LastViewedDate` and inserts a `RecentlyViewed` row for the
one record the user actually opened, so it enters Recent Items. The `WHERE Id =` + `LIMIT 1`
guarantees the write is scoped to exactly that record; user mode prevents stamping records the
user cannot see.

---

## Example 2: Mobile reference without a full view (FOR REFERENCE)

**Context:** a mobile app shows Accounts as reference cards in a list. Tapping does not open a
full page, but the business wants "recently referenced" accounts to surface in search.

**Problem:** using `FOR VIEW` here would claim the user *viewed* each account, inflating Recent
Items with records they only glanced at. The interaction is a reference, not a view.

**Solution:**

```apex
public with sharing class AccountReferenceSelector extends BaseSelector {
    public Account selectForReference(Id accountId) {
        assertNotNull(accountId, 'accountId');
        List<Account> rows = Database.queryWithBinds(
            'SELECT Id, Name, Industry ' +
            'FROM Account WHERE Id = :accountId LIMIT 1 FOR REFERENCE',
            new Map<String, Object>{ 'accountId' => accountId },
            userMode()
        );
        return rows.isEmpty() ? null : rows[0];
    }
}
```

**Why it works:** `FOR REFERENCE` writes `LastReferencedDate` (not `LastViewedDate`), matching the
lighter interaction. The record still enters the `RecentlyViewed` surface, but as a reference
rather than a full view.

---

## Example 3: Enabling the fields on a custom object

**Context:** the same pattern applied to a custom object `Invoice__c` throws at query time:

```
System.QueryException: No such column 'LastViewedDate' on entity 'Invoice__c'.
```

**Problem:** `LastViewedDate` / `LastReferencedDate` do not exist on a custom object until the
object has a custom tab. Standard objects already have them.

**Solution:** in Setup, create a custom tab for `Invoice__c` (Setup → Tabs → Custom Object Tabs
→ New). The tab does **not** need to be visible in the navigation bar — creating it is enough to
activate the fields. After the tab exists, the clause works:

```sql
SELECT Id, Name FROM Invoice__c WHERE Id = :invoiceId LIMIT 1 FOR VIEW
```

**Why it works:** the recency fields are provisioned as part of the object's tab definition, so a
tab (even a hidden one) is the prerequisite for both querying the fields and using the clauses.

---

## Anti-Pattern: FOR VIEW in a batch or unbounded query

**What practitioners do:** append `FOR VIEW` to a broad query, often in a batch, scheduled job,
or a "warm the cache / mark processed" routine — sometimes with no `WHERE` and no `LIMIT`:

```apex
// Anti-pattern: runs as the batch/integration user; no user is "viewing" anything,
// and it stamps recency on every row returned.
for (Account a : [SELECT Id, Name FROM Account WHERE Region__c = 'EMEA' FOR VIEW]) {
    process(a);
}
```

**What goes wrong:** the docs are explicit — use the clauses "only when you are sure that the
retrieved records will definitely be viewed by the logged-in user, else the clause incorrectly
updates the usage information for the records." A batch/integration context has no viewing user,
so every EMEA account is falsely marked "recently viewed," polluting Recent Items and
search auto-complete for whoever owns the running context. It also adds needless DML.

**Correct approach:** drop the clause entirely in non-user-facing code. Only add `FOR VIEW` /
`FOR REFERENCE` on a bounded, by-Id query issued from a genuine user-facing view/reference
request, as in Examples 1 and 2.
