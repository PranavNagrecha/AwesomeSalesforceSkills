---
name: apex-aggregate-queries
description: "Use this skill when writing SOQL aggregate queries in Apex — GROUP BY, GROUP BY ROLLUP/CUBE, HAVING, COUNT/SUM/AVG/MIN/MAX, AggregateResult, the GROUPING() subtotal function, and date grouping functions. Trigger keywords: soql aggregate groupby apex, count sum group by salesforce, aggregateresult get alias, having clause soql, rollup cube subtotals, grouping function subtotal detection soql. NOT for relationship subqueries or inner queries (use apex-soql-relationship-queries), NOT for the Reporting API or Analytics Wave API."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
triggers:
  - "soql aggregate groupby apex — practitioner needs GROUP BY with COUNT, SUM, AVG, MIN, or MAX in Apex"
  - "count sum group by salesforce aggregateresult — developer iterating AggregateResult rows and reading field values"
  - "aggregateresult get alias — practitioner accessing aggregate values via the get() method and needs alias rules"
  - "detect subtotal rows with grouping soql — practitioner using GROUP BY ROLLUP or CUBE who needs GROUPING() to tell subtotal rows from detail rows"
  - "distinguish real null from rollup placeholder — developer whose grouped field itself contains nulls and can't rely on a null check to find subtotals"
  - "count all rows in soql apex — practitioner needs a total row count and must choose bare COUNT() vs COUNT(fieldName) and read the right result shape (QueryResult.size vs AggregateResult)"
tags:
  - soql
  - aggregate-queries
  - groupby
  - having
  - aggregateresult
  - rollup
  - cube
  - grouping
inputs:
  - "Object(s) to aggregate and the metric fields (e.g. Amount on Opportunity)"
  - "Grouping dimension(s) — field API names or date functions"
  - "Any filter on aggregate values (threshold for HAVING) or pre-aggregate filters (WHERE)"
outputs:
  - "Correct SOQL aggregate query with properly aliased fields"
  - "Apex iteration code using AggregateResult.get('alias')"
  - "Guidance on row-cap implications and ROLLUP/CUBE subtotal rows"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Apex Aggregate Queries

This skill activates when a practitioner needs to write SOQL aggregate queries inside Apex — covering GROUP BY, GROUP BY ROLLUP, GROUP BY CUBE, HAVING, COUNT/SUM/AVG/MIN/MAX, AggregateResult field access, date grouping functions, and the platform limits unique to aggregate queries.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which object and fields will be aggregated. Numeric fields (Currency, Number, Percent) support SUM/AVG/MIN/MAX. Any field supports COUNT(fieldName).
- The most common wrong assumption is that aggregate queries share the flat-SOQL 50,000-row governor limit. They do not — aggregate queries cap at **2,000 rows** regardless of record volume.
- Verify whether GROUP BY ROLLUP or CUBE is needed; those variants generate subtotal rows that count toward the 2,000-row cap and require null-checking in Apex.

---

## Core Concepts

### AggregateResult and Field Access

Most SOQL aggregate queries return `List<AggregateResult>` instead of typed SObject lists (the exception is a bare `COUNT()` — see below). `AggregateResult` is a read-only sObject used only for query results; you cannot insert, update, or persist one. Every column in the result set — whether a grouped field or an aggregate function — must be accessed by alias string using `get('alias')`. There are no typed getters. The return type of `get()` is `Object`; cast to the expected type before use.

Aliases are assigned with the `alias` keyword in SOQL (e.g. `SUM(Amount) totalRevenue`). When an aggregate function appears without an explicit alias Salesforce auto-assigns names like `expr0`, `expr1` in declaration order. Relying on auto-assigned aliases is fragile — always supply explicit aliases. When the same function appears twice in one SELECT (e.g. `COUNT(Id)` on two different fields), explicit aliases are mandatory; without them one result overwrites the other.

### COUNT() vs COUNT(fieldName)

`COUNT()` (no argument) and `COUNT(fieldName)` look interchangeable but differ in three ways — null handling, syntax, and result shape — and conflating them is a common source of invalid queries and runtime casts against the wrong type.

**Null handling.** `COUNT()` counts every row that matches the filter, including rows where fields are null — it counts rows, not a specific field's populated values. `COUNT(fieldName)` counts only rows that have a non-null value for `fieldName`. The distinction matters when the counted field is optional or sparsely populated. `COUNT()` and `COUNT(Id)` are SOQL's equivalent of SQL's `COUNT(*)`.

**Syntax.** Bare `COUNT()` must be the **only** element in the SELECT list — it cannot be combined with other fields, with other aggregate functions, or with a `GROUP BY` grouping field. `SELECT COUNT(), LeadSource FROM Lead GROUP BY LeadSource` is invalid; to get a per-bucket count, use `COUNT(Id)`: `SELECT LeadSource, COUNT(Id) cnt FROM Lead GROUP BY LeadSource`. `COUNT()` also can't be paired with `ORDER BY`, though it is compatible with `LIMIT`. `COUNT(fieldName)` carries none of these restrictions — you can list several `COUNT(fieldName)` items alongside other aggregates and grouped fields in one SELECT.

**Result shape.** A bare `COUNT()` query does **not** return an `AggregateResult` — its result comes back through the `QueryResult` object's `size` field (the `records` field is null), so you assign it straight to an `Integer` with no iteration:

```apex
Integer leadCount = [SELECT COUNT() FROM Lead WHERE Status = 'Open'];
```

`COUNT(fieldName)` — like every other aggregate — returns inside an `AggregateResult` record; an unaliased `COUNT(fieldName)` lands under the implied alias `expr0`, so read it with `ar.get('expr0')` (or supply an explicit alias). Do not iterate a `List<AggregateResult>` over a bare `COUNT()` query, and do not assign a `COUNT(fieldName)` query to a bare `Integer`.

**Governor cost.** A `COUNT()` or `COUNT(fieldName)` query consumes just one query row against limits — unless it has a `GROUP BY`, in which case one query row per grouping is consumed.

### GROUP BY Variants, HAVING, and the 2,000-Row Cap

`GROUP BY fieldA` groups result rows by distinct values of `fieldA`. `GROUP BY ROLLUP(fieldA, fieldB)` adds subtotal rows for each leading subset of the grouping columns plus a grand total row; ROLLUP aggregates from right to left through the grouping columns, so field order determines which subtotal levels you get. `GROUP BY CUBE(fieldA, fieldB)` adds subtotals for every combination of grouping columns, useful for cross-tabular reports. Both ROLLUP and CUBE subtotal rows appear as `null` for the rolled-up dimension in the result — Apex code must null-check before casting (and see GROUPING() below when the grouped field can itself hold nulls).

Two constraints apply to both variants. First, they cap the grouping-field list at **three fields** (`GROUP BY ROLLUP(a, b, c)` is the maximum). Second, every grouped field must sit **inside** the parentheses — you cannot mix plain `GROUP BY` with `GROUP BY ROLLUP`/`CUBE` in one statement. `GROUP BY ROLLUP(Region__c), Family` is invalid; write `GROUP BY ROLLUP(Region__c, Family)`.

The **2,000-row hard cap** applies to the entire result set including subtotal rows generated by ROLLUP/CUBE. If the expected cardinality of grouped results exceeds 2,000, split the query with WHERE filters or switch to Batch Apex.

`HAVING` filters on aggregate values after grouping (e.g. `HAVING SUM(Amount) > 10000`). It cannot be replaced by `WHERE` because `WHERE` runs before aggregation and cannot reference aggregate function output.

`QueryMore` (cursor-based pagination) is **not supported** for aggregate queries. The full result must fit within 2,000 rows.

### Detecting Subtotal Rows with GROUPING()

`GROUPING(fieldName)` is the reliable way to tell a ROLLUP/CUBE subtotal row apart from a detail row. It returns `1` when the row is a subtotal for that field (the field was rolled up, not part of this row's grouping) and `0` when the row carries an actual value for that field. It can appear in the `SELECT`, `HAVING`, and `ORDER BY` clauses, and the value comes back through `ar.get('alias')` as an `Integer`.

Add one `GROUPING(field)` expression per rolled-up field, each with its own alias. In the ROLLUP example below, `GROUPING(LeadSource)=0, GROUPING(Rating)=1` marks a per-LeadSource subtotal, and both `=1` marks the grand total:

```sql
SELECT LeadSource, Rating,
       GROUPING(LeadSource) grpLS, GROUPING(Rating) grpRating,
       COUNT(Name) cnt
FROM Lead
GROUP BY ROLLUP(LeadSource, Rating)
```

The naive `ar.get('field') == null` subtotal check is only safe when the grouped field can never hold a real null. When the grouped field is nullable — LeadSource, an optional picklist, an unset lookup — a genuine null detail row and a subtotal placeholder row are both `null`, and the null check misclassifies real data as a subtotal. `GROUPING()` is the only way to separate the two, and it matters most when more than one field is in the ROLLUP or CUBE clause.

### Date Grouping Functions

`CALENDAR_YEAR(dateField)`, `CALENDAR_MONTH(dateField)`, `DAY_IN_WEEK(dateField)`, `FISCAL_YEAR(dateField)`, `FISCAL_QUARTER(dateField)`, `HOUR_IN_DAY(dateTimeField)`, and related functions can appear in both `SELECT` and `GROUP BY`. They allow time-series grouping without post-processing in Apex. The return type from `get('alias')` for these functions is `Integer`. Always pair the function in SELECT with an alias.

### GROUP BY Incompatibilities

`GROUP BY` cannot be used inside inner queries (subqueries). It is also incompatible with `WITH DATA CATEGORY`. Attempting either causes a compile-time or query parse error.

---

## Common Patterns

### Revenue Rollup by Dimension with HAVING Threshold

**When to use:** Dashboard-style aggregation — e.g. total closed revenue per Account, filtered to accounts with revenue above a threshold.

**How it works:** Write a GROUP BY query with SUM and a HAVING clause. Cast `get('totalRevenue')` to Decimal. Null-check before arithmetic.

**Why not the alternative:** Fetching all Opportunity records and summing in Apex loops burns heap and CPU. The aggregate query shifts computation to the database tier.

### Time-Series Grouping with Date Functions

**When to use:** Monthly or annual trend analysis — e.g. opportunities closed per month over the past year.

**How it works:** Use `CALENDAR_YEAR(CloseDate)` and `CALENDAR_MONTH(CloseDate)` in both SELECT and GROUP BY. Cast the returned values to Integer in Apex. Sort by year and month in the SOQL ORDER BY clause.

**Why not the alternative:** String-formatting the date in Apex after a flat query requires loading all records and iterating in memory — this blows governor limits at scale.

### ROLLUP for Subtotals

**When to use:** Hierarchical reports — e.g. revenue grouped by Region and Product Family, with subtotals per Region and a grand total.

**How it works:** `GROUP BY ROLLUP(Region__c, Family)` produces N+1 grouping levels. Detect subtotal rows by checking `if (ar.get('region') == null)` — but only when the grouped fields can never hold a real null; otherwise use GROUPING() (see the GROUPING() section above). The grand total row has both grouping fields null.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need a single total row count, no grouping | Bare `COUNT()` assigned to an `Integer` | Returns via `QueryResult.size`, not an `AggregateResult`; can't be combined with fields or `GROUP BY` |
| Need a count per group or alongside other columns | `COUNT(Id)` (or `COUNT(fieldName)`) in the SELECT | Bare `COUNT()` must be the only SELECT element; `COUNT(Id)` counts every row like SQL `COUNT(*)` |
| Aggregate metric from a single object, result < 2,000 groups | Inline aggregate SOQL in Apex | Simplest; all processing in DB tier |
| Aggregate metric, expected groups > 2,000 | Batch Apex with WHERE range partitioning | Aggregate query row cap is 2,000 |
| Need subtotals without post-processing | GROUP BY ROLLUP or CUBE | Subtotals generated by DB; null sentinel marks subtotal rows |
| Identify which subtotal level a row is, or grouped field is nullable | GROUPING(field) in SELECT | Null check can't tell a real null from a subtotal placeholder; GROUPING() returns 1 for subtotal, 0 for data |
| Filter on aggregate value (e.g. SUM > X) | HAVING clause | WHERE cannot reference aggregate output |
| Cross-object aggregate (e.g. parent field in GROUP BY) | Use dot-notation field in GROUP BY (e.g. Account.Industry) | Supported in aggregate SOQL; no join needed |
| Time-series grouping | CALENDAR_YEAR/CALENDAR_MONTH in SELECT and GROUP BY | DB-native; avoids heap-heavy Apex date parsing |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Define the metric and dimension** — identify the object, the numeric field to aggregate (or Id for COUNT), and the grouping dimension(s). Confirm whether the practitioner needs subtotals (ROLLUP/CUBE) or a simple GROUP BY.
2. **Estimate result cardinality** — if the number of distinct grouped values may exceed 2,000 (factoring in ROLLUP/CUBE subtotal rows), plan a partitioned approach (Batch Apex or WHERE-range splitting) before writing any query.
3. **Write the SOQL with explicit aliases** — assign an alias to every aggregate function. If the same function is used twice, aliases are required. Prefer descriptive aliases (`totalRevenue`, `oppCount`) over `expr0`.
4. **Add HAVING if filtering on aggregate output** — do not put aggregate-dependent filters in WHERE. Use HAVING for post-group filtering.
5. **Write the Apex iteration** — loop over `List<AggregateResult>`, call `ar.get('alias')` for each column, cast to the correct type (Decimal for SUM/AVG/MIN/MAX, Integer for COUNT and date functions), and null-check ROLLUP/CUBE subtotal rows.
6. **Validate governor limit exposure** — confirm the query is not inside a loop, and that the expected row count stays under 2,000. Add a unit test that mocks aggregate results.
7. **Run the query in Developer Console** — verify aliases match what Apex code expects; confirm HAVING filters produce the expected subset.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every aggregate function in SELECT has an explicit alias
- [ ] Apex code uses `ar.get('aliasName')` with cast — not a typed SObject getter
- [ ] Result row count (including ROLLUP/CUBE subtotals) is expected to stay under 2,000
- [ ] Filters on aggregate values use HAVING, not WHERE
- [ ] ROLLUP/CUBE subtotal rows are distinguished with GROUPING() (not a bare null check) whenever a grouped field is nullable
- [ ] No aggregate GROUP BY inside an inner/subquery
- [ ] No `WITH DATA CATEGORY` combined with GROUP BY
- [ ] Unit tests cover the aggregate iteration logic (mock or Test.setFixedSearchResults equivalent)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **2,000-row cap (not 50,000)** — Aggregate queries are subject to a separate 2,000-row governor limit that applies org-wide, not the 50,000-row flat SOQL limit. GROUP BY ROLLUP and CUBE inflate the row count with subtotal rows that count against this same cap. Queries that look safe based on record count can silently fail at runtime when subtotal rows push the result over 2,000.
2. **Missing alias causes NullPointerException** — Calling `ar.get('myAlias')` when the query used no alias (or a typo alias) returns `null`; subsequent casts like `(Decimal) ar.get('myAlias')` throw a `NullPointerException`. Auto-assigned aliases (`expr0`, `expr1`) can shift silently when the SELECT column order changes. Always use explicit, stable aliases.
3. **ROLLUP row count inflation vs actual data** — `GROUP BY ROLLUP(A, B)` produces rows for each (A, B) pair PLUS one row per distinct A PLUS one grand total row. For N groups of A and M groups of B the row count is N×M + N + 1. Practitioners who only consider the base GROUP BY cardinality underestimate total rows and hit the 2,000-row cap unexpectedly.
4. **A subtotal placeholder null looks exactly like a real null** — ROLLUP/CUBE fill the rolled-up dimension with `null` on subtotal rows. If the grouped field can also hold a legitimate null (an unset picklist, an empty lookup), a `get('field') == null` subtotal check treats those genuine detail rows as subtotals and double-counts or mislabels them. Use `GROUPING(field)` (returns `1` for a true subtotal, `0` for data) to discriminate.
5. **Bare COUNT() does not drop into GROUP BY like COUNT(fieldName)** — Because most examples use `COUNT(fieldName)`, practitioners assume bare `COUNT()` behaves the same way and write `SELECT COUNT(), LeadSource FROM Lead GROUP BY LeadSource`, which is invalid: `COUNT()` must be the only element in the SELECT list. Its result also arrives differently — through `QueryResult.size` as a scalar `Integer`, not an `AggregateResult` — so code that iterates `List<AggregateResult>` over a bare `COUNT()` (or assigns a `COUNT(fieldName)` query to an `Integer`) breaks. Use `COUNT(Id)` when you need a count inside a grouped or multi-column query.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SOQL aggregate query | A well-formed query with explicit aliases, HAVING if needed, and correct date functions |
| Apex iteration snippet | Loop over `List<AggregateResult>` with typed casts and ROLLUP null guards |
| Cardinality estimate | Assessment of expected row count vs. the 2,000-row cap |

---

## Related Skills

- apex-soql-relationship-queries — use when GROUP BY needs to traverse a relationship (parent or child subquery) or when the query is part of a larger join-style pattern
- soql-fundamentals — foundational SOQL syntax, LIMIT/OFFSET, WHERE filters, and flat query governor limits
- batch-apex-patterns — use when aggregate result set may exceed 2,000 rows and requires partitioned execution
- apex-performance-profiling — use when aggregate queries are suspected as a CPU or SOQL-query-count bottleneck
