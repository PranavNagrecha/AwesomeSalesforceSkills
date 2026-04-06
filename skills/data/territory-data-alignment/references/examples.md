# Examples — Territory Data Alignment

## Example 1: Annual Territory Realignment — Bulk Loading Manual Associations for a Named Account Book

**Context:** A sales operations team completed a territory realignment. Named account reps have new account books that were not captured by assignment rules. The team has a spreadsheet of 1,200 account-territory pairs that must be loaded manually before the new fiscal year kickoff.

**Problem:** The UI supports individual account assignment but has no bulk import capability. Loading 1,200 rows one at a time is not feasible. The team also needs to dedup against existing associations to avoid API insert errors.

**Solution:**

Step 1 — Export existing manual associations for the active model:

```soql
SELECT Id, ObjectId, Territory2Id, AssociationCause
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'
  AND AssociationCause = 'Manual'
```

Step 2 — Export Territory2 records to resolve names to IDs:

```soql
SELECT Id, Name, DeveloperName
FROM Territory2
WHERE Territory2Model.State = 'Active'
ORDER BY Name ASC
```

Step 3 — Prepare the insert CSV (deduplicated against step 1):

```
ObjectId,Territory2Id,AssociationCause
001xxxxxxxxxxxx1,0MWxxxxxxxxxxxx1,Manual
001xxxxxxxxxxxx2,0MWxxxxxxxxxxxx2,Manual
...
```

Step 4 — Load via Data Loader (Insert operation, object: `ObjectTerritory2Association`).

Step 5 — Verify with post-load coverage check:

```soql
SELECT Territory2.Name, COUNT(Id) AssociationCount
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'
  AND AssociationCause = 'Manual'
GROUP BY Territory2.Name
ORDER BY Territory2.Name ASC
```

**Why it works:** Bulk API 2.0 (used by Data Loader under the hood) supports `ObjectTerritory2Association` inserts without governor limits that would block Apex. Deduplication before insert prevents partial-failure batches caused by duplicate key violations.

---

## Example 2: Coverage Gap Analysis Before a Territory Model Activation

**Context:** A new territory model has been built in Planning state. Before activating it and archiving the old model, the sales ops team wants to verify that all 45,000 accounts in the org will have at least one territory assignment in the new model after the assignment rules run.

**Problem:** Running a full rule evaluation on the new model before activation is not possible. The team needs to simulate gap detection by comparing rule criteria coverage to the account population without actually running rules.

**Solution:**

Step 1 — After activating the new model, run assignment rules, then execute the coverage gap query:

```soql
SELECT Id, Name, BillingState, BillingCountry, AnnualRevenue, OwnerId
FROM Account
WHERE IsDeleted = false
  AND Id NOT IN (
    SELECT ObjectId
    FROM ObjectTerritory2Association
    WHERE Territory2.Territory2Model.State = 'Active'
  )
ORDER BY AnnualRevenue DESC NULLS LAST
LIMIT 2000
```

Step 2 — For orgs exceeding the 50K subquery limit, use Bulk API 2.0 query to export all `ObjectTerritory2Association.ObjectId` values, then compare against a full Account export externally (e.g., in Python or Excel VLOOKUP).

Step 3 — For each gap account, determine which rule criteria they fail to match (typically unrecognized BillingState/Country values, null picklist fields, or AnnualRevenue outside all range bands).

Step 4 — Either: (a) add a catch-all territory rule, (b) bulk-insert manual associations for gap accounts, or (c) correct the account data that prevents rule matching.

**Why it works:** The NOT IN subquery approach is the canonical way to detect coverage gaps in ETM without custom code. For large orgs, externalizing the set comparison avoids governor limits and allows the gap analysis to run against the full account population.

---

## Anti-Pattern: Deleting Rule-Driven Associations to Remove an Account from a Territory

**What practitioners do:** When an account needs to be removed from a territory quickly (e.g., the account was reassigned to a different rep), practitioners query the `ObjectTerritory2Association` row and delete it via API, regardless of whether `AssociationCause` is `Territory` or `Manual`.

**What goes wrong:** The next assignment rule run re-creates the deleted row because the account still matches the territory's rule criteria. The account returns to the territory without any visible warning. The practitioner repeats the deletion and the problem persists. Some practitioners respond by disabling rule runs entirely, which causes broader coverage drift.

**Correct approach:** Check `AssociationCause` before any delete operation. For `AssociationCause = 'Territory'` rows, the correct remediation is to either (a) update the account's field values so they no longer match the territory's criteria, (b) create an exclusion territory with higher priority, or (c) modify the assignment rule to exclude this account. Only after the rule logic is corrected should you delete the row — and the next rule run will confirm the account stays out.
