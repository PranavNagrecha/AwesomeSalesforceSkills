---
name: saql-query-development
description: "Use this skill when writing, debugging, or optimizing SAQL queries in CRM Analytics — covering pipeline syntax, aggregation, windowing functions (rank, dense_rank, moving_average), cogroup joins, rollup subtotals, piggyback queries, and REST API execution. NOT for SOQL, standard Salesforce reports, SQL databases, or any non-CRM Analytics query language."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "how do I write a SAQL query to rank rows within a group in CRM Analytics"
  - "my CRM Analytics dashboard step returns wrong results when I use windowing functions"
  - "how to join two datasets together in a SAQL query using cogroup"
  - "SAQL query is not returning subtotals even though I added rollup"
  - "piggyback query filter is being ignored in my dashboard JSON"
  - "REST API returns error when I use dataset name instead of datasetId in SAQL"
tags:
  - saql
  - crm-analytics
  - query
  - analytics
  - windowing
  - cogroup
  - piggyback
inputs:
  - "Name and version of the CRM Analytics dataset(s) to query"
  - "The analytic question to answer (aggregation, ranking, trend, join, subtotal)"
  - "Whether the query runs in a dashboard step, lens, or via REST API"
  - "Dashboard JSON step definition if debugging a piggyback query"
outputs:
  - "Valid SAQL query with correct pipeline syntax"
  - "Windowing or cogroup pattern matched to the stated requirement"
  - "Rollup/grouping() subtotal query where subtotals are required"
  - "Corrected REST API payload with datasetId and datasetVersionId"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# SAQL Query Development

This skill activates when a practitioner needs to write, debug, or optimize SAQL (Salesforce Analytics Query Language) queries in CRM Analytics. It covers the full pipeline syntax, windowing functions, cogroup joins, rollup subtotals, piggyback dashboard queries, and REST API execution — and explicitly guards against the most common failure mode: writing SQL or SOQL syntax that parses as an immediate error in SAQL.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Dataset identity:** You need the dataset developer name for load statements, but the REST API requires datasetId and datasetVersionId — not the developer name. Confirm which execution context applies (dashboard step, lens, REST API).
- **Most common wrong assumption:** Practitioners trained on SQL or SOQL write `SELECT ... FROM ... WHERE ...` which is not valid SAQL and produces an immediate parse error. SAQL is a dataflow pipeline language where every transformation is a named stream assignment.
- **Platform limits:** SAQL queries in dashboard steps run inside the Analytics query engine, not against the Salesforce database. Row limits, timeout behavior, and available functions differ from SOQL. REST API query execution requires OAuth with the CRM Analytics permission set.

---

## Core Concepts

### 1. SAQL Is a Pipeline Language, Not SQL

Every SAQL query is a series of named stream assignments. Each statement takes a stream as input and produces a new named stream as output. The statements execute in declaration order. The final named stream is returned as the query result.

The canonical pipeline:

```
q = load "dataset_developer_name";
q = filter q by <expression>;
q = group q by <dimension> [, <dimension>];
q = foreach q generate <dimension>, <aggregate>;
q = order q by <field> [asc|desc];
q = limit q <N>;
```

Every keyword (`load`, `filter`, `group`, `foreach`, `generate`, `order`, `limit`) is SAQL-specific. SQL keywords (`SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `JOIN`) are not valid and cause immediate parse errors.

### 2. Windowing Functions

Windowing functions compute values across a partition of rows without collapsing rows into groups. They are applied inside a `foreach` statement using the `over` clause.

Available windowing functions:
- `rank()` — assigns rank with gaps for ties (1, 1, 3)
- `dense_rank()` — assigns rank without gaps (1, 1, 2)
- `row_number()` — unique sequential integer per row
- `cume_dist()` — cumulative distribution (0 to 1)
- `moving_average(field, window_size)` — rolling average over N preceding rows
- `sum(field) over (...)` — running total

The `over` clause defines the partition and ordering:

```
foreach q generate
  Region,
  SalesRep,
  Revenue,
  rank() over ([partition by Region] order by Revenue desc) as "Rank";
```

Key behavior: windowing functions do not reduce the row count. Every input row appears in the output with the computed window value appended. This differs from `group ... foreach` aggregation, which collapses rows.

### 3. cogroup — Joining Two Streams

`cogroup` merges two named streams on a shared key field. It is the SAQL equivalent of a join.

```
q1 = load "orders";
q2 = load "accounts";
q = cogroup q1 by AccountId, q2 by Id;
q = foreach q generate q1.AccountId, sum(q1.Amount) as "TotalAmount", q2.Name;
```

Semantics:
- Default is an INNER cogroup — rows with no match in the other stream are dropped.
- `cogroup q1 by AccountId FULL, q2 by Id FULL` produces OUTER semantics — unmatched rows are retained with null for the missing side.
- After cogroup, field references must be qualified with the stream name (`q1.Amount`, `q2.Name`) until a `foreach generate` aliases them into a flat projection.

### 4. rollup and grouping()

The `rollup` modifier on a `group` statement adds subtotal rows for each grouping level, plus a grand total row.

```
q = load "opportunities";
q = group q by rollup(Stage, FiscalYear);
q = foreach q generate
  Stage,
  FiscalYear,
  sum(Amount) as "TotalAmount",
  grouping(Stage) as "IsStageSubtotal",
  grouping(FiscalYear) as "IsFiscalYearSubtotal";
```

`grouping(field)` returns `1` for rows where that field is the aggregation level (i.e., a subtotal for that dimension) and `0` for detail rows. Without `rollup`, `grouping()` always returns `0` and subtotal rows are not generated.

---

## Common Patterns

### Pattern 1: Rank Within a Partition

**When to use:** You need to rank sales reps by revenue within each region, or identify top-N records per group.

**How it works:**

```
q = load "opportunities";
q = filter q by 'CloseDate_Year' == "2024";
q = group q by (Region, SalesRep);
q = foreach q generate Region, SalesRep, sum(Amount) as "Revenue";
q = foreach q generate
  Region,
  SalesRep,
  Revenue,
  rank() over ([partition by Region] order by Revenue desc) as "RegionRank";
q = filter q by RegionRank <= 3;
```

**Why not simple group + foreach:** A plain `group` collapses all rows into one per group, giving you totals but not per-rep rankings within a region. Windowing preserves the row count while appending the computed rank.

### Pattern 2: Joining Datasets with cogroup

**When to use:** You need to combine facts from two datasets — for example, matching order amounts to account attributes.

**How it works:**

```
q1 = load "orders";
q1 = filter q1 by CloseDate >= date(2024, 1, 1);
q2 = load "accounts";
q = cogroup q1 by AccountId, q2 by Id;
q = foreach q generate
  q1.AccountId as "AccountId",
  q2.Name as "AccountName",
  q2.Industry as "Industry",
  sum(q1.Amount) as "TotalRevenue",
  count() as "OrderCount";
q = order q by TotalRevenue desc;
q = limit q 100;
```

**Why not two separate loads with a later merge:** SAQL does not have a `JOIN` keyword. `cogroup` is the only way to combine streams. Attempting SQL-style join syntax fails at parse time.

### Pattern 3: Subtotals with rollup

**When to use:** A dashboard needs a summary table where each region shows individual year totals plus a region subtotal row and an overall grand total.

**How it works:**

```
q = load "opportunities";
q = group q by rollup(Region, FiscalYear);
q = foreach q generate
  Region,
  FiscalYear,
  sum(Amount) as "TotalAmount",
  grouping(Region) as "IsRegionTotal",
  grouping(FiscalYear) as "IsYearTotal";
```

Use `grouping()` in the dashboard widget logic to format subtotal rows differently (bold, indent, or a label like "Region Total").

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need per-row rank or running total without collapsing rows | Windowing function in foreach with over clause | group collapses rows; windowing preserves them |
| Need to combine two datasets on a shared key | cogroup with qualified field references | No JOIN keyword exists in SAQL |
| Need subtotals and grand totals in one query | group by rollup(...) + grouping() | Without rollup modifier, subtotal rows are not generated |
| Executing SAQL via REST API | Use datasetId + datasetVersionId in payload | Dataset developer name is not accepted by the query endpoint |
| Dashboard piggyback query — filter not applying | Move filter into pigql attribute, not query attribute | When pigql is set, filter/limit/order on query are silently ignored |
| Need to express a date filter | Use date() function or string literal matching stored date format | toDate() does not recast text-typed date columns at query time |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on a SAQL task:

1. **Identify the execution context.** Determine whether the query runs in a dashboard step, a lens, or via the REST API. REST API execution requires `datasetId` and `datasetVersionId` — not the dataset developer name. Gather these from the CRM Analytics dataset detail page or via the REST API dataset list endpoint.
2. **Confirm dataset field names and types.** Open the dataset in CRM Analytics Data Manager or use the REST API fields endpoint (`/wave/datasets/{id}/versions/{vId}/fields`). Dimension fields use string equality; measure fields accept numeric functions. Using a measure field as a dimension grouping key (or vice versa) produces a query error.
3. **Draft the pipeline in declaration order.** Start with `load`, then `filter`, then `group` (if aggregating), then `foreach generate`, then `order`, then `limit`. For windowing queries, apply the window function in a second `foreach` after the aggregation step.
4. **Choose the right join or aggregation primitive.** Use `cogroup` for joining two streams. Use `rollup` on the `group` statement when subtotals are required. Use windowing functions when you need per-row computed values without collapsing rows.
5. **Check for SQL/SOQL syntax contamination.** Before finalizing, scan the query for `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, or `JOIN` — all are invalid SAQL and will produce parse errors. Replace with SAQL equivalents.
6. **For piggyback queries, move all filters to the pigql attribute.** In dashboard JSON, when the `pigql` attribute is set on a step, the `filter`, `limit`, and `order` fields on the `query` attribute are silently ignored. All filtering must be expressed inside `pigql`.
7. **Validate in the SAQL editor before committing.** CRM Analytics provides an inline SAQL editor in Analytics Studio. Run the query there first to catch parse errors and confirm result shape before embedding in dashboard JSON or a REST API call.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No SQL or SOQL keywords (`SELECT`, `FROM`, `WHERE`, `GROUP BY`, `JOIN`, `HAVING`) appear anywhere in the query
- [ ] Every stream reference after `cogroup` uses the qualified `streamName.fieldName` form until projected flat by `foreach generate`
- [ ] If `rollup` is used, `grouping()` is included for each rollup dimension so subtotal rows can be identified by consumers
- [ ] REST API payloads include `datasetId` and `datasetVersionId` — not the dataset developer name
- [ ] Piggyback queries express all filtering inside the `pigql` attribute, not on the `query` attribute `filter` field
- [ ] Windowing functions use the `over` clause with an explicit `order by`; a windowing function without `order by` returns undefined ordering

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SQL/SOQL syntax is a parse error, not a warning** — Writing `SELECT StageName, SUM(Amount) FROM Opportunity GROUP BY StageName` in a SAQL context produces an immediate parse error. There is no partial fallback. Every practitioner who has written SQL or SOQL will instinctively reach for this syntax, and every time it will fail.
2. **Piggyback filter/limit/order are silently ignored** — When a dashboard step has a `pigql` attribute, the `filter`, `limit`, and `order` fields on the sibling `query` attribute do nothing. No error is raised. The pigql expression executes in full and the other constraints are discarded. This causes invisible bugs where applied dashboard filters appear to have no effect.
3. **REST API requires datasetVersionId, not dataset name** — The SAQL query endpoint (`/wave/query`) requires `datasetId` and `datasetVersionId`. Substituting the dataset developer name in the SAQL `load` statement works in the UI but fails when constructing a REST API payload that specifies the dataset by name alone — the endpoint does not resolve developer names.
4. **rollup without grouping() produces unidentifiable subtotal rows** — `group q by rollup(A, B)` generates subtotal rows with null values in the rolled-up dimensions, but without `grouping(A)` and `grouping(B)` there is no programmatic way to distinguish a genuine null dimension value from a subtotal row.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SAQL pipeline query | Complete, valid query using load/filter/group/foreach/order/limit statements |
| Windowing query variant | Query using rank/dense_rank/row_number/moving_average with over clause |
| cogroup join query | Query merging two streams with qualified field references and flat foreach projection |
| rollup subtotal query | Query using group by rollup and grouping() for subtotal row identification |
| REST API payload | JSON body with datasetId, datasetVersionId, and SAQL string for /wave/query endpoint |

---

## Related Skills

- analytics-dashboard-design — Embed SAQL steps into dashboard JSON; piggyback query configuration
- crm-analytics-app-creation — Create the app container and dataset before writing SAQL queries
- analytics-dataset-management — Understand dataset field types, versions, and datasetId/datasetVersionId resolution
