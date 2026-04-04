# SOQL Query Optimization Report

Use this template to document a query optimization investigation and its outcome.

---

## Query Under Investigation

```soql
<!-- Paste the exact SOQL query here -->
```

---

## Object and Record Count

| Field | Value |
|---|---|
| Object API Name | |
| Approximate total record count (live) | |
| Approximate soft-deleted record count | |
| Total count (live + deleted, for selectivity calc) | |
| Source of count | e.g., Storage Usage page / SOQL COUNT query |

---

## Query Plan Output

Run via Developer Console > Debug > Open Query Plan.

| Plan Step | Cost | Cardinality | Leading Operation |
|---|---|---|---|
| Plan 1 (selected) | | | |
| Plan 2 (alternative) | | | |

**Overall assessment:**
- [ ] Cost < 1.0 — index used (acceptable)
- [ ] Cost 1.0–2.0 — marginal; monitor in production
- [ ] Cost > 2.0 — full-table scan; high timeout risk on large objects

**Query Plan notes:**

<!-- Any additional observations from the Query Plan output -->

---

## Selectivity Analysis

For each WHERE clause field:

| Field API Name | Indexed? | Index Type | Estimated Match Count | Match % of Total | Selective? |
|---|---|---|---|---|---|
| | Yes / No | Standard / Custom / None | | | Yes / No |
| | Yes / No | Standard / Custom / None | | | Yes / No |

**Selectivity verdict:**
- [ ] All filters are individually selective — query should use indexes
- [ ] One or more filters are non-selective — optimization required
- [ ] OR condition present — all OR branches must be individually indexed and selective

**Non-selective patterns identified:**

<!-- List any of the following found in this query: -->
- [ ] Leading LIKE wildcard (`LIKE '%...`)
- [ ] Formula field in WHERE clause
- [ ] NULL filter on non-null-inclusive index
- [ ] OR across non-indexed fields
- [ ] ORDER BY on non-selective base query
- [ ] No indexed field in WHERE clause

---

## Recommended Rewrite or Index Strategy

**Approach selected:**
- [ ] Query rewrite — use existing indexed field
- [ ] Custom index request on existing field
- [ ] Two-column composite index request
- [ ] Null-inclusive index request
- [ ] OR decomposition into multiple queries
- [ ] Stored field to replace non-deterministic formula
- [ ] Skinny table request (for 10M+ record objects)

**Optimized query:**

```soql
<!-- Paste the optimized query here -->
```

**Explanation of changes:**

<!-- Describe what changed and why -->

---

## Custom Index Request (if applicable)

Complete this section if a custom index is needed from Salesforce Support.

| Field | Value |
|---|---|
| Object API Name | |
| Field API Name | |
| Index type | Single-column / Two-column composite / Null-inclusive |
| Second column (if composite) | |
| Null-inclusive required? | Yes / No |
| Justification | |
| Selectivity evidence | e.g., "Field value 'X' matches 8% of records (GROUP BY query result)" |
| Query pattern this index serves | |

**Support case reference:** (fill after submission)

---

## Skinny Table Request (if applicable)

Complete this section if a skinny table is appropriate (10M+ records, recurring read-heavy pattern).

| Field | Value |
|---|---|
| Object API Name | |
| Fields to include in skinny table | |
| Recurring query pattern served | |
| Estimated read frequency | e.g., "Nightly batch, daily reports, hourly list view loads" |

**Support case reference:** (fill after submission)

---

## Expected Improvement

| Metric | Before | After (expected) |
|---|---|---|
| Query Plan cost | | < 1.0 |
| Query execution time (observed) | | |
| Batch job completion time | | |
| Report load time | | |

---

## Outcome (fill after implementation)

- [ ] Custom index confirmed active in production
- [ ] Query Plan re-run shows cost < 1.0
- [ ] Performance improvement observed in production monitoring
- [ ] Optimization documented in architecture decision log
