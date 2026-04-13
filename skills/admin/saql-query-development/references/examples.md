# Examples — SAQL Query Development

## Example 1: Windowing vs Aggregation — Ranking Sales Reps Within a Region

**Scenario:** A sales operations analyst wants a CRM Analytics dashboard table showing every sales rep's total revenue for 2024, with each rep ranked within their region (1 = highest revenue in that region). The top 3 per region should be highlighted.

**Problem:** The analyst first writes a plain `group ... foreach` aggregation, which collapses all rows to one per region-rep combination and provides the total revenue. But there is no way to compute a rank within region from a single aggregation pass — a second sort and manual numbering would be required outside the query, which is not possible in a dashboard step.

**Solution:**

```
-- Step 1: aggregate to get revenue per region + rep
q = load "opportunities_dataset";
q = filter q by 'CloseDate_Year' == "2024" && 'IsWon' == "true";
q = group q by (Region__c, OwnerId);
q = foreach q generate
  Region__c as "Region",
  OwnerId as "SalesRepId",
  sum(Amount) as "TotalRevenue",
  count() as "DealCount";

-- Step 2: apply windowing to rank within partition
q = foreach q generate
  Region,
  SalesRepId,
  TotalRevenue,
  DealCount,
  rank() over ([partition by Region] order by TotalRevenue desc) as "RegionRank";

-- Step 3: filter to top 3 per region
q = filter q by RegionRank <= 3;
q = order q by Region asc, RegionRank asc;
```

**Why it matters:** `rank()` with an `over ([partition by ...] order by ...)` clause operates across a logical window of rows without changing the row count. This is fundamentally different from `group`: aggregation collapses N rows into 1 per group, while windowing appends a computed value to every row. Using `dense_rank()` instead of `rank()` would eliminate the gap when two reps tie (e.g., 1, 1, 2 instead of 1, 1, 3). The second `foreach` step is required because windowing functions cannot be applied in the same `foreach` that contains aggregate functions.

---

## Example 2: cogroup to Join Orders to Account Attributes

**Scenario:** A finance team needs a CRM Analytics lens showing total order revenue per account, enriched with the account's Industry and BillingCountry fields. Orders and account attributes live in separate datasets.

**Problem:** An analyst attempts to write a single `load` from the orders dataset and reference `Industry` directly, not realizing those fields do not exist in the orders dataset. Alternatively, they try a SQL-style `FROM orders JOIN accounts ON ...` which is not valid SAQL syntax.

**Solution:**

```
-- Load the orders stream
orders = load "crm_orders";
orders = filter orders by CloseDate >= date(2024, 1, 1);

-- Load the accounts stream
accts = load "crm_accounts";

-- cogroup on the shared key
q = cogroup orders by AccountId, accts by Id;

-- Project into a flat stream with qualified references
q = foreach q generate
  orders.AccountId as "AccountId",
  accts.Name as "AccountName",
  accts.Industry as "Industry",
  accts.BillingCountry as "Country",
  sum(orders.Amount) as "TotalRevenue",
  count(orders.Id) as "OrderCount";

q = order q by TotalRevenue desc;
q = limit q 500;
```

**Why it matters:** `cogroup` is the only join primitive in SAQL. The default semantics are INNER — accounts with no orders and orders with no matching account are dropped. If the analyst needs to retain unmatched records, they use `FULL` on both sides: `cogroup orders by AccountId FULL, accts by Id FULL`. After `cogroup`, all field references must be qualified with the stream name (`orders.Amount`, `accts.Industry`) until the `foreach generate` step projects them to flat aliases. Forgetting the qualifier causes an ambiguous field error when the same field name exists in both streams.

---

## Example 3: Subtotals with rollup and grouping()

**Scenario:** A regional manager wants a dashboard table showing revenue by Region and FiscalYear, with a subtotal row for each region (summing across all years) and a grand total row at the bottom.

**Problem:** The analyst uses a plain `group q by (Region, FiscalYear)` and gets one row per region-year pair but no subtotal rows. They then attempt to add a separate query for region totals and manually merge the results — which is not possible inside a single SAQL step.

**Solution:**

```
q = load "opportunities_dataset";
q = group q by rollup(Region__c, FiscalYear);
q = foreach q generate
  Region__c as "Region",
  FiscalYear,
  sum(Amount) as "TotalRevenue",
  grouping(Region__c) as "IsRegionTotal",
  grouping(FiscalYear) as "IsFiscalYearTotal";
q = order q by Region asc, FiscalYear asc;
```

**Why it matters:** The `rollup` modifier on the `group` statement instructs the engine to generate additional aggregate rows for each prefix of the dimension list, plus a grand total. For `rollup(Region, FiscalYear)` the engine produces: one row per (Region, FiscalYear) pair; one subtotal row per Region (FiscalYear is null); and one grand total row (both dimensions are null). The `grouping()` function returns `1` on subtotal rows for that dimension and `0` on detail rows. Without `grouping()`, a genuine null dimension value is indistinguishable from a rollup subtotal row — the dashboard widget cannot format them differently.

---

## Anti-Pattern: Using SQL Syntax in SAQL

**What practitioners do:** Write a query using SQL `SELECT ... FROM ... WHERE ... GROUP BY` syntax inside a CRM Analytics dashboard step or SAQL editor, expecting it to behave like SOQL or standard SQL.

```sql
-- WRONG: this is SQL/SOQL, not SAQL
SELECT StageName, SUM(Amount) AS TotalRevenue
FROM Opportunity
WHERE CloseDate >= 2024-01-01
GROUP BY StageName
ORDER BY TotalRevenue DESC
```

**What goes wrong:** SAQL is not SQL. The parser rejects `SELECT` at the first token. No partial execution occurs — the entire step fails with a parse error. Dashboard steps using this pattern return no data and often display a generic error state in the widget.

**Correct approach:**

```
q = load "opportunities_dataset";
q = filter q by CloseDate >= date(2024, 1, 1);
q = group q by StageName;
q = foreach q generate StageName, sum(Amount) as "TotalRevenue";
q = order q by TotalRevenue desc;
```
