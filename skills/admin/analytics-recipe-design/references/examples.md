# Examples — Analytics Recipe Design

## Example 1: Lookup Join Enriching Opportunities with Account Data

**Context:** A sales analytics team builds a recipe to produce an Opportunity dataset enriched with Account industry and annual revenue for segmentation dashboards. The Opportunity dataset has 45,000 rows. The Account dataset has 12,000 rows. Some Opportunities have a null `AccountId` (internal test records).

**Problem:** A first attempt used an Inner join on `AccountId = Id`. The output dataset contained only 39,200 rows — 5,800 Opportunities were silently dropped because their `AccountId` either was null or referenced an Account not present in the Account dataset. No error or warning appeared in the recipe run log.

**Solution:**

Change the Join node type from Inner to **Lookup**:

```
Node: Join
  Type: Lookup
  Left input: Opportunities dataset (Load node)
  Right input: Accounts dataset (Load node)
  Join keys:
    Left key:  AccountId
    Right key: Id
  Columns added from right:
    - Industry
    - AnnualRevenue
    - BillingState
```

After switching to Lookup, the output contains all 45,000 Opportunity rows. The 5,800 rows with no Account match have null values for `Industry`, `AnnualRevenue`, and `BillingState` — they are present in the output and visually distinguishable as unmatched.

**Why it works:** Lookup semantics are "enrich the left dataset." Every left-side row is preserved. Matched right-side columns are appended where a match exists; null is written where there is no match. This is fundamentally different from Inner join semantics, which filter rather than enrich.

**Verification step:** After running the recipe, compare the input Opportunities dataset row count (visible in Analytics Studio dataset detail) against the output dataset row count. If they match (45,000 = 45,000), the Lookup is working correctly.

---

## Example 2: Measure Bucket Creating a Revenue Tier Dimension

**Context:** A CRM Analytics dataset contains an `AnnualRevenue` measure field on Account records. A dashboard requirement asks for a segment filter — "SMB", "Mid-Market", "Enterprise" — but the source data only has the raw numeric value. SAQL can bin values at query time but this creates repeated logic across every lens that needs segmentation.

**Problem:** Without a persistent bucket column, every SAQL query must re-implement the binning logic, increasing query complexity and making global segment definition changes require edits to every lens individually.

**Solution:**

Add a **Bucket** node immediately after the Accounts Load node:

```
Node: Bucket
  Source field: AnnualRevenue
  Bucket type: Measure
  Output column name: Revenue_Tier
  Buckets:
    - Label: "SMB"          Range: 0 to < 10000
    - Label: "Mid-Market"   Range: 10000 to < 100000
    - Label: "Enterprise"   Range: >= 100000
    - Label: "Unknown"      (Other / null fallback)
```

The output dataset schema now contains `Revenue_Tier` as a dimension (string) column alongside the original `AnnualRevenue` measure. Dashboard lenses can group and filter by `Revenue_Tier` without any SAQL binning logic.

**Why it works:** The Bucket node persists the segmentation logic in the dataset itself. The source `AnnualRevenue` field is unchanged. All downstream lenses inherit the canonical tier definition with no duplication.

---

## Example 3: Formula Node Adding a Computed Fiscal Quarter Label

**Context:** A recipe produces an Opportunity dataset. The `CloseDate` field is available as a date. The dashboard requires a `FiscalQuarter` string column (e.g., "FY26-Q1") based on a February fiscal year start.

**Problem:** There is no built-in fiscal quarter field in the recipe input. A practitioner attempts to write the formula using SAQL syntax (e.g., `toDate(CloseDate, "yyyy-MM-dd")`), which fails — the recipe expression language is not SAQL.

**Solution:**

Use the recipe Formula node with the recipe expression language:

```
Node: Formula
  Output column name: FiscalQuarter
  Output type: Text
  Expression:
    CONCAT(
      IF(MONTH(CloseDate) >= 2,
         CONCAT("FY", TEXT(YEAR(CloseDate) + 1)),
         CONCAT("FY", TEXT(YEAR(CloseDate)))
      ),
      IF(MONTH(CloseDate) >= 2 && MONTH(CloseDate) <= 4, "-Q1",
         IF(MONTH(CloseDate) >= 5 && MONTH(CloseDate) <= 7, "-Q2",
            IF(MONTH(CloseDate) >= 8 && MONTH(CloseDate) <= 10, "-Q3",
               "-Q4"
            )
         )
      )
    )
```

**Why it works:** The formula is written for the recipe engine, not for SAQL. The Data Prep Recipe REST API declares a formula's `expressionType` as `Sql` or `Legacy`, so SAQL functions such as `toDate()` or `dateValue()` are the wrong language for this node.

UNVERIFIED (2026-10-03): the function names used above (`CONCAT()`, `IF()`, `MONTH()`, `YEAR()`, `TEXT()`) are not documented in the REST API guide; the recipe function reference is published only on help.salesforce.com, which did not fetch for this pass. Paste the expression into the formula editor and confirm it validates, and rewrite it with the editor's suggested functions if it does not. A `Sql` expression may need `case when ... then ... end` syntax instead of nested `IF()`.

---

## Anti-Pattern: Using Inner Join as the Default Join Type

**What practitioners do:** Accept the default join type (often Inner) in the Join node configuration UI without considering whether all left-side rows need to be preserved.

**What goes wrong:** Any left-side row without a match in the right dataset is silently dropped from the output. Run logs show a successful completion with no errors. The row count discrepancy is only visible by comparing input and output dataset counts. On large datasets this can mean tens of thousands of records vanishing without any alert.

**Correct approach:** Explicitly choose the join type for every Join node. Default to Lookup when the intent is enrichment (adding columns from a secondary dataset to a primary dataset). Use Inner only when the business requirement is genuinely "return only records that exist in both datasets." Document the join type rationale in the recipe description field so the intent is auditable.

---

## Example 4: Event-Based Schedule After the Local Sync

**Context:** The enrichment recipe from Example 1 reads connected objects for Opportunity and Account. The sales team wants fresh data each morning, and the org already runs six dataflows longer than two minutes.

**Problem:** An hourly schedule would add 24 counted runs a day to a 60-run rolling budget that six dataflows already share, and it would often start before the local sync finished.

**Solution:** Replace the time-based schedule with an event-based one, so the recipe runs once after the Salesforce Local connection syncs.

```json
{
  "frequency": "eventdriven",
  "triggerRule": "$ALL_SALESFORCE_OBJECTS"
}
```

Send it with `PUT /services/data/v67.0/wave/asset/<recipeId>/schedule`. Read it back with `GET` on the same URL.

**Why it works:** Event-based schedules apply to dataflows and recipes and run after the Salesforce Local connection syncs (CRM Analytics REST API Developer Guide, Schedule Dataflows, Recipes, and Data Syncs). A recipe that runs once per sync uses one counted run a day instead of up to 24. An event-based schedule can have at most 5 dependent jobs (Analytics Platform Setup Guide, Recipe and Dataflow Limits), so count the jobs already chained to the sync before adding this one.

