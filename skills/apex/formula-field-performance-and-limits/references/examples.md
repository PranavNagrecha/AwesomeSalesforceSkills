# Examples — Formula Field Performance and Limits

## Example 1: Materializing a Formula Field to Fix a Full Table Scan on an LDV Object

**Context:** An org has 2.4 million Opportunity records. A nightly batch report filters on a formula checkbox field `Is_Strategic_Account__c` which returns `TRUE` when `Account.AnnualRevenue >= 1000000 AND Account.Type = 'Strategic Partner'`. Report execution times are exceeding 10 minutes and timing out.

**Problem:** The SOQL query driving the report includes `WHERE Is_Strategic_Account__c = true`. Because `Is_Strategic_Account__c` is a formula field, Salesforce cannot use an index. Every one of the 2.4 million rows is evaluated at query time. The Query Plan Tool shows `TableScan: true`.

**Solution:**

Step 1 — Create a stored Checkbox field `Is_Strategic_Account_Stored__c` on Opportunity.

Step 2 — Create a Record-Triggered Flow on Opportunity (fires on Create and Update):
- Entry condition: run only when `Account.AnnualRevenue` or `Account.Type` changes (use `$Record__Prior` comparison to avoid unnecessary evaluations).
- Update Records element: set `Is_Strategic_Account_Stored__c` = formula result (reproduce the logic as a Flow formula: `{!$Record.Account.AnnualRevenue} >= 1000000 AND {!$Record.Account.Type} = 'Strategic Partner'`).

Step 3 — Backfill existing records with a Batch Apex job:

```apex
public class BackfillStrategicAccountBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Is_Strategic_Account__c FROM Opportunity'
        );
    }

    public void execute(Database.BatchableContext bc, List<Opportunity> scope) {
        for (Opportunity opp : scope) {
            // Mirror the formula value into the stored field
            opp.Is_Strategic_Account_Stored__c = opp.Is_Strategic_Account__c;
        }
        update scope;
    }

    public void finish(Database.BatchableContext bc) {}
}
```

Step 4 — Request a custom index on `Is_Strategic_Account_Stored__c` from Salesforce Support (Checkbox fields on LDV objects benefit from custom indexes for selective queries).

Step 5 — Update the SOQL in the report to filter on `Is_Strategic_Account_Stored__c = true`.

**Why it works:** The stored Checkbox field contains a real database value that Salesforce can index. The Query Plan Tool will now show `TableScan: false` after the custom index is in place. Report execution drops from timeout to seconds.

---

## Example 2: Splitting a Formula to Resolve a Compile-Size Limit Error

**Context:** A billing team has a complex Opportunity formula `Adjusted_ARR__c` that calculates adjusted annual revenue using nested `IF()` branches for discount tier, region multiplier, currency conversion, and product type. A new branch is added for a government pricing tier and the formula save fails with "Formula is too large."

**Problem:** The formula has grown past the 5,000 compiled-character limit. The source text appears under 1,000 characters, but the compiled expansion of multiple cross-object field references pushes the compiled size over the limit.

**Solution:**

Step 1 — Identify a re-used sub-expression. The discount tier calculation (`IF(Discount_Pct__c >= 0.30, 0.70, IF(Discount_Pct__c >= 0.15, 0.85, 1.0))`) appears three times in the formula.

Step 2 — Create a helper formula field `Calc_Discount_Multiplier__c` (Number, 6 decimal places) containing only the discount tier logic:

```text
IF(Discount_Pct__c >= 0.30, 0.70,
  IF(Discount_Pct__c >= 0.15, 0.85, 1.0)
)
```

Step 3 — Replace all three inline occurrences in `Adjusted_ARR__c` with a reference to `Calc_Discount_Multiplier__c`. Each replacement trades the full expanded sub-expression for a single field reference, significantly reducing compiled size.

Step 4 — Save `Adjusted_ARR__c`. The compile-size check passes.

Step 5 — Hide `Calc_Discount_Multiplier__c` from page layouts and remove it from search (it is an intermediate calculation, not a user-facing field).

**Why it works:** Salesforce compiles a field reference to a single helper formula as one internal token rather than expanding the full sub-expression a second time. Three inline repetitions become one shared reference, and the compiled character budget is freed for the new government pricing branch.

---

## Anti-Pattern: Using a Formula Field in an Apex SOQL WHERE Clause

**What practitioners do:** Write Apex that queries records based on a formula field value:

```apex
// WRONG — formula field in WHERE clause forces full table scan
List<Account> highRisk = [
    SELECT Id, Name
    FROM Account
    WHERE Risk_Score_Formula__c > 75
    AND IsActive__c = true
];
```

**What goes wrong:** Even if `IsActive__c` is indexed and selective, the `Risk_Score_Formula__c > 75` predicate forces Salesforce to evaluate the formula for every candidate row. On an object with millions of records, this causes SOQL timeout errors, `UNABLE_TO_LOCK_ROW` exceptions during concurrent loads, and visible slowness in synchronous Apex transactions that hit the 10-second CPU limit.

**Correct approach:** Materialize `Risk_Score_Formula__c` into a stored Number field `Risk_Score__c` maintained by a Record-Triggered Flow, then query the stored field:

```apex
// CORRECT — queries the stored indexed field
List<Account> highRisk = [
    SELECT Id, Name
    FROM Account
    WHERE Risk_Score__c > 75
    AND IsActive__c = true
];
```

After a custom index is placed on `Risk_Score__c`, the query becomes selective and avoids the full table scan entirely.
