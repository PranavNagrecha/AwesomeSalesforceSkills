# SAQL Query Development — Work Template

Use this template when writing, debugging, or reviewing a SAQL query for CRM Analytics.

## Scope

**Skill:** `saql-query-development`

**Request summary:** (describe the analytic question to answer — e.g., "rank reps by revenue within region", "join orders to accounts", "subtotals by region and year")

---

## Context Gathered

Answer these before writing any SAQL:

- **Dataset developer name(s):** (the name used in `load "..."`)
- **Execution context:** [ ] Dashboard step  [ ] Lens  [ ] REST API
- **If REST API:** datasetId: ___  |  datasetVersionId: ___
- **Field names and types:** (list dimensions and measures needed; confirm types in Data Manager)
- **Is this a piggyback query (pigql)?** [ ] Yes  [ ] No
- **Are subtotals required?** [ ] Yes — use rollup  [ ] No
- **Is a join across datasets required?** [ ] Yes — use cogroup  [ ] No
- **Is per-row ranking or running total required?** [ ] Yes — use windowing  [ ] No — plain aggregation

---

## SAQL Pipeline Draft

```
-- Load
q = load "<dataset_developer_name>";

-- Filter (move as early as possible)
q = filter q by <dimension> == "<value>" && <date_field> >= date(<year>, <month>, <day>);

-- Group (omit if windowing only)
q = group q by (<dimension1> [, <dimension2>]) [rollup];

-- Project
q = foreach q generate
  <dimension1>,
  [<dimension2>,]
  <aggregate>(<measure>) as "<Label>"
  [, grouping(<dimension1>) as "Is<Dimension1>Total"]
  [, rank() over ([partition by <dimension1>] order by <aggregate>(<measure>) desc) as "Rank"];

-- Optional: second foreach for windowing after aggregation
-- q = foreach q generate ..., rank() over (...) as "Rank";

-- Order and limit
q = order q by <field> [asc|desc];
q = limit q <N>;
```

---

## cogroup Template (when joining two datasets)

```
-- Load and pre-filter each stream
stream1 = load "<primary_dataset>";
stream1 = filter stream1 by <filter_expression>;

stream2 = load "<lookup_dataset>";

-- Join on shared key
q = cogroup stream1 by <SharedKey>, stream2 by <Id>;

-- Project with qualified field references
q = foreach q generate
  stream1.<SharedKey> as "<KeyLabel>",
  stream2.<LookupField> as "<LookupLabel>",
  sum(stream1.<MeasureField>) as "<AggLabel>",
  count() as "Count";

q = order q by <AggLabel> desc;
q = limit q 500;
```

---

## Piggyback Query Checklist

If this step uses `pigql`:

- [ ] All filtering is expressed inside the `pigql` SAQL string — NOT in `query.filter`
- [ ] `query.limit` and `query.order` are empty or absent — NOT used to constrain the pigql result
- [ ] Dashboard filter widget bindings target the `pigql` attribute value, not the `query` attribute

---

## Pre-Submit Review Checklist

- [ ] No SQL/SOQL keywords (`SELECT`, `FROM`, `WHERE`, `GROUP BY`, `JOIN`, `HAVING`) in the query
- [ ] Every `foreach generate` after `cogroup` uses qualified `streamName.fieldName` references
- [ ] `rollup(...)` is paired with `grouping(<dimension>)` for each rollup dimension
- [ ] Windowing functions have an explicit `over ([partition by ...] order by ...)` clause
- [ ] Aggregate and windowing functions are in separate `foreach` statements
- [ ] For REST API: payload includes `datasetId` and `datasetVersionId`
- [ ] Tested in the Analytics Studio SAQL editor before embedding in dashboard JSON or API call

---

## Notes

(Record any deviations from the standard pattern and the reason — e.g., why rollup was skipped, or why a cogroup uses FULL instead of INNER semantics.)
