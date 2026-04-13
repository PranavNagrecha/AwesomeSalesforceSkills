# Gotchas — SAQL Query Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SQL and SOQL Syntax Are Immediate Parse Errors in SAQL

**What happens:** Any use of SQL or SOQL syntax — `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `JOIN` — causes an immediate parse failure. SAQL does not attempt partial execution or fallback. The entire query is rejected at the first invalid keyword, and the dashboard step or lens returns no data.

**When it occurs:** Every time a practitioner writes a SAQL query from memory after working primarily with SQL or SOQL. It also occurs when an AI assistant generates SAQL without explicit grounding in SAQL syntax — LLMs default to SQL because SQL training data vastly outnumbers SAQL training data.

**How to avoid:** Use the SAQL pipeline template: `q = load ...; q = filter q by ...; q = group q by ...; q = foreach q generate ...; q = order q by ...; q = limit q N;`. Scan every generated query for SQL keywords before submitting. The CRM Analytics SAQL editor in Analytics Studio highlights parse errors inline.

---

## Gotcha 2: Piggyback Query filter/limit/order on the query Attribute Are Silently Ignored

**What happens:** When a dashboard step has a `pigql` attribute set, the `filter`, `limit`, and `order` fields on the sibling `query` attribute are silently discarded. No error is raised, no warning appears in the UI, and no log entry is written. The pigql expression executes in full and the constraints on `query` have no effect whatsoever.

**When it occurs:** When a developer adds dashboard-level filters (e.g., a date range widget) to a step that already uses piggyback queries. The filter binding writes to the `query` attribute's `filter` field, which is ignored because `pigql` is present. The widget appears to respond to filter selections (no error state), but the underlying data does not change.

**How to avoid:** In steps that use `pigql`, express all filtering, ordering, and limiting inside the `pigql` SAQL string itself. Do not rely on the `filter`, `limit`, or `order` fields on the `query` attribute when `pigql` is set. If dynamic dashboard filters must interact with a piggyback step, the filter expression must be injected into the `pigql` attribute value, not the `query` attribute.

---

## Gotcha 3: REST API Requires datasetId and datasetVersionId, Not Dataset Developer Name

**What happens:** When executing a SAQL query via the CRM Analytics REST API (`POST /wave/query`), the payload must specify the target dataset using `datasetId` and `datasetVersionId`. Using only the dataset developer name in the SAQL `load` statement or omitting the version identifier causes the API to return an error. The developer name is resolved in the UI context but not by the REST endpoint.

**When it occurs:** When a developer copies a SAQL query from Analytics Studio (where it works by developer name) into a REST API call or integration. The SAQL string references `load "my_dataset_dev_name"` but the REST payload does not include the required ID fields, or includes only the name.

**How to avoid:** Before calling `/wave/query`, retrieve the dataset's `id` and current version's `id` using `GET /wave/datasets` (filter by developer name) and `GET /wave/datasets/{id}/versions`. Include both values in the query payload:

```json
{
  "query": "q = load \"my_dataset\"; q = foreach q generate count() as \"n\"; q = limit q 1;",
  "queryLanguage": "SAQL",
  "datasetId": "0Fbxx0000000001AAA",
  "datasetVersionId": "0Fcxx0000000001AAA"
}
```

---

## Gotcha 4: rollup Without grouping() Makes Subtotal Rows Indistinguishable from Genuine Nulls

**What happens:** `group q by rollup(A, B)` generates subtotal and grand-total rows where the rolled-up dimension fields contain `null`. If the underlying data also contains genuine null values in those dimension fields, the dashboard widget cannot distinguish a subtotal row from a detail row with a missing dimension value. Both display identically and sorting, formatting, and conditional coloring logic based on dimension values silently misclassifies rows.

**When it occurs:** When a developer adds `rollup` to enable subtotals but does not include `grouping()` calls for each rolled-up dimension. It is particularly problematic when the dimension field (e.g., Region, Stage) occasionally has null values in real data.

**How to avoid:** Always pair `rollup(A, B)` with `grouping(A) as "IsATotal"` and `grouping(B) as "IsBTotal"` in the `foreach generate` clause. The `grouping()` function returns `1` only on synthetic subtotal rows and `0` on all detail rows (including genuine-null detail rows). Use these flag fields in dashboard widget formatting rules rather than testing for null on the dimension itself.

---

## Gotcha 5: Windowing Functions Cannot Be Mixed with Aggregate Functions in the Same foreach

**What happens:** Attempting to use both an aggregate function (e.g., `sum(Amount)`) and a windowing function (e.g., `rank() over (...)`) in a single `foreach generate` block causes a query error. The two classes of function operate at different stages of the pipeline and cannot be composed in a single step.

**When it occurs:** When a developer tries to write a compact query that computes the aggregate and the rank in one step, such as:

```
-- WRONG: mixing aggregate and windowing in one foreach
q = group q by (Region, SalesRep);
q = foreach q generate Region, SalesRep, sum(Amount) as "Revenue",
  rank() over ([partition by Region] order by sum(Amount) desc) as "Rank";
```

**How to avoid:** Split into two `foreach` statements. The first applies the aggregate (`sum`, `count`, `avg`) after the `group` step. The second applies the windowing function to the already-aggregated stream:

```
q = group q by (Region, SalesRep);
q = foreach q generate Region, SalesRep, sum(Amount) as "Revenue";
q = foreach q generate Region, SalesRep, Revenue,
  rank() over ([partition by Region] order by Revenue desc) as "Rank";
```
