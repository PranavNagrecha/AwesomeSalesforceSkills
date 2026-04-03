# Examples - Roll Up Summary Alternatives

## Example 1: Native Roll-Up On Master-Detail

**Context:** Opportunity Products must sum into a parent custom object on a master-detail relationship.

**Problem:** The team starts discussing Apex even though the relationship fits native behavior.

**Solution:** Use the native Roll-Up Summary field and avoid extra automation entirely.

**Why it works:** Native platform behavior is simpler and more reliable when it fits.

---

## Example 2: Lookup Rollup With Aggregate Apex

**Context:** A parent Account needs a filtered count of related custom child records on a lookup relationship.

**Problem:** Native roll-up summary is not available.

**Solution:**

```apex
AggregateResult[] results = [
    SELECT Account__c accountId, COUNT(Id) recordCount
    FROM Case_Alert__c
    WHERE Account__c IN :accountIds
    GROUP BY Account__c
];
```

Map the aggregate results back to parent Accounts and update them in one bulk DML operation.

**Why it works:** The design recalculates from source truth instead of trying to keep a fragile counter in sync line by line.

---

## Anti-Pattern: Aggregate Query Per Child Record

**What practitioners do:** They recalculate the parent total inside a loop for each changed child.

**What goes wrong:** SOQL usage, locking, and performance all degrade quickly.

**Correct approach:** Collect affected parents, aggregate once, then update once.
