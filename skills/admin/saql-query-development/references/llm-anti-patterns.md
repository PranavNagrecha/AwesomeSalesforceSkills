# LLM Anti-Patterns — SAQL Query Development

Common mistakes AI coding assistants make when generating or advising on SAQL queries.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing SAQL with SQL or SOQL Syntax

**What the LLM generates:**

```sql
SELECT StageName, SUM(Amount) AS TotalRevenue
FROM Opportunity
WHERE CloseDate >= 2024-01-01
  AND IsWon = true
GROUP BY StageName
ORDER BY TotalRevenue DESC
LIMIT 10
```

**Why it happens:** SQL syntax vastly dominates LLM training data. When asked to "write a query for CRM Analytics," models default to SQL because the surface-level task description (query, aggregate, filter) maps to SQL in training. SAQL's pipeline assignment syntax is far less common in training corpora and is not intuitively recognizable as a query language without explicit grounding.

**Correct pattern:**

```
q = load "opportunities";
q = filter q by CloseDate >= date(2024, 1, 1) && 'IsWon' == "true";
q = group q by StageName;
q = foreach q generate StageName, sum(Amount) as "TotalRevenue";
q = order q by TotalRevenue desc;
q = limit q 10;
```

**Detection hint:** Any SAQL snippet containing the keywords `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `JOIN`, or `LIMIT <n>` (without the stream name before N) is SQL/SOQL, not SAQL. Flag immediately.

---

## Anti-Pattern 2: Mixing Aggregate and Windowing Functions in the Same foreach

**What the LLM generates:**

```
q = group q by (Region, SalesRep);
q = foreach q generate
  Region,
  SalesRep,
  sum(Amount) as "Revenue",
  rank() over ([partition by Region] order by sum(Amount) desc) as "Rank";
```

**Why it happens:** LLMs model SAQL `foreach` loosely as analogous to SQL `SELECT`, where mixing `SUM()` and `RANK() OVER (...)` in the same clause is valid. In SAQL the two function classes operate at different pipeline stages and cannot be mixed in one `foreach` block.

**Correct pattern:**

```
q = group q by (Region, SalesRep);
q = foreach q generate Region, SalesRep, sum(Amount) as "Revenue";
q = foreach q generate
  Region,
  SalesRep,
  Revenue,
  rank() over ([partition by Region] order by Revenue desc) as "Rank";
```

**Detection hint:** Any `foreach generate` block that contains both a bare aggregate function (`sum(...)`, `count()`, `avg(...)`) and a windowing function (`rank()`, `dense_rank()`, `row_number()`, `moving_average(...)`) with an `over` clause in the same statement is invalid. The windowing step must be a separate `foreach`.

---

## Anti-Pattern 3: Using cogroup Without Qualifying Field References

**What the LLM generates:**

```
q = cogroup orders by AccountId, accounts by Id;
q = foreach q generate AccountId, Name, sum(Amount) as "Total";
```

**Why it happens:** LLMs model `cogroup` as similar to SQL `JOIN`, after which field names are directly accessible. In SAQL, after `cogroup` the result stream retains both source streams as nested collections. Fields must be qualified with the source stream name until a `foreach generate` projects them into a flat named stream.

**Correct pattern:**

```
q = cogroup orders by AccountId, accounts by Id;
q = foreach q generate
  orders.AccountId as "AccountId",
  accounts.Name as "AccountName",
  sum(orders.Amount) as "Total";
```

**Detection hint:** Any `foreach generate` immediately after a `cogroup` that references fields without a `streamName.` prefix is incorrect. Look for bare field names like `AccountId`, `Name`, or `Amount` following a `cogroup` statement.

---

## Anti-Pattern 4: Using Dataset Developer Name in REST API Payload

**What the LLM generates:**

```json
{
  "query": "q = load \"my_opportunities\"; q = foreach q generate count() as \"n\"; q = limit q 1;",
  "queryLanguage": "SAQL"
}
```

**Why it happens:** LLMs learn from documentation examples and community posts where SAQL is written for the Analytics Studio UI, where the dataset developer name resolves correctly. They generalize this to REST API usage, not recognizing that the REST API query endpoint requires explicit `datasetId` and `datasetVersionId` parameters.

**Correct pattern:**

```json
{
  "query": "q = load \"my_opportunities\"; q = foreach q generate count() as \"n\"; q = limit q 1;",
  "queryLanguage": "SAQL",
  "datasetId": "0Fbxx0000000001AAA",
  "datasetVersionId": "0Fcxx0000000001AAA"
}
```

**Detection hint:** Any REST API call to `/wave/query` that does not include both `datasetId` and `datasetVersionId` in the request body is incomplete. These values must be resolved via `GET /wave/datasets` and `GET /wave/datasets/{id}/versions` before the query call.

---

## Anti-Pattern 5: Advising That Dashboard Filters Apply to Piggyback Query Steps via the query Attribute

**What the LLM generates:** "To apply a date range filter to your piggyback query step, bind the filter widget to the step's `query.filter` field as you would for a standard step."

**Why it happens:** LLMs model all dashboard step types as behaving the same way with respect to filter bindings. The special behavior of piggyback queries — where the presence of `pigql` silently suppresses all `query.filter`, `query.limit`, and `query.order` processing — is a non-obvious platform-specific behavior that is not evident from the surface-level API shape.

**Correct pattern:**

Any filtering, ordering, or limiting that must apply to a piggyback step must be embedded inside the `pigql` SAQL string:

```json
{
  "pigql": "q = load \"dataset\"; q = filter q by CloseDate >= date(2024, 1, 1); q = foreach q generate ...",
  "query": { }
}
```

Do not instruct users to bind filters to the `query.filter` field on a step where `pigql` is set. The binding will appear to succeed but the filter will have no effect on query results.

**Detection hint:** Any recommendation to use `query.filter`, `query.limit`, or `query.order` on a dashboard step that has a non-empty `pigql` attribute is incorrect guidance. Confirm whether `pigql` is set before advising on how to attach dynamic filters.

---

## Anti-Pattern 6: Claiming rollup Produces Subtotals Without grouping() Required for Row Identification

**What the LLM generates:** "Use `group q by rollup(Region, Year)` to get subtotal rows. The null values in Region and Year on those rows indicate they are subtotals."

**Why it happens:** LLMs understand that rollup generates null-valued dimension fields on subtotal rows (this is SQL ROLLUP behavior and is consistent in SAQL). They fail to note that genuine null values in real data are indistinguishable from rollup-generated nulls without the `grouping()` function, and that downstream consumers need `grouping()` output to reliably identify subtotal rows.

**Correct pattern:**

```
q = group q by rollup(Region, FiscalYear);
q = foreach q generate
  Region,
  FiscalYear,
  sum(Amount) as "TotalRevenue",
  grouping(Region) as "IsRegionTotal",
  grouping(FiscalYear) as "IsFiscalYearTotal";
```

**Detection hint:** Any `group q by rollup(...)` that is not paired with a `grouping(...)` call for each rollup dimension in the `foreach generate` is incomplete. Flag the omission and explain why `grouping()` is required when dimension fields can be genuinely null in the source data.
