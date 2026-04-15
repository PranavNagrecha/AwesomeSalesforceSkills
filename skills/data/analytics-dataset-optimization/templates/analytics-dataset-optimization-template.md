# Analytics Dataset Optimization — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `analytics-dataset-optimization`

**Request summary:** (fill in what the user asked for)

**Dataset name(s) in scope:** _____

---

## Context Gathered

### Dataset Basics

| Property | Value |
|---|---|
| Dataset name | |
| Current row count | |
| Current field count | |
| Source: Dataflow or Recipe | |
| Refresh frequency | |
| Daily run-slot consumption (this dataset) | |

### Org Run-Budget Status

| Property | Value |
|---|---|
| Total org runs per 24h (all dataflows + Recipes) | |
| Managed-package dataflow runs per 24h (estimate) | |
| Available headroom (60 minus total) | |

### Date Fields in This Dataset

| Field name | Current storage type (Date / Datetime / Text / Numeric) | Used in SAQL timeseries or date grouping? | Used in duration math? | Recommended type |
|---|---|---|---|---|
| | | | | |

---

## Field Audit Results

**Method used to extract SAQL field references:**
- [ ] Analytics REST API dashboard export
- [ ] Manual dashboard inspection
- [ ] Lens/dataset lineage tool

**Fields confirmed as used in SAQL queries or dashboard bindings:**

| Field name | Used in which dashboards / lenses | Required for security predicate | Required as join key |
|---|---|---|---|
| | | | |

**Fields confirmed as unused (candidates for removal):**

| Field name | Reason it is unused | Safe to remove? |
|---|---|---|
| | | |

**Net field count after pruning:** _____ (from _____  current fields)

---

## Date Granularity Decisions

For each date field in the dataset:

| Field name | Recommended storage | Rationale |
|---|---|---|
| | Date (yyyy-MM-dd) | Used in date range filters; no time-of-day needed |
| | Datetime (full ISO) | Used in intraday filtering |
| | Epoch pre-computed integer | Used in duration math (store as Numeric) |

---

## Dataset Splitting Assessment

**Current row count:** _____

**Dominant dashboard filter dimension:** _____ (e.g., fiscal year, region, record type)

**Split recommended?**
- [ ] Yes — row count exceeds 10–20 million and dominant queries filter to a single period or dimension
- [ ] No — row count is manageable as a single dataset

**If splitting:**

| Dataset name | Filter criteria | Refresh frequency | Responsible Recipe / Dataflow |
|---|---|---|---|
| | | | |

**Cross-period query strategy:**
- [ ] Pre-aggregated summary dataset (recommended for trend views)
- [ ] SAQL union across year-specific datasets (only for low-row-count unions)
- [ ] Not required — no cross-period queries in scope

---

## Run-Budget Optimization Plan

**Proposed changes to refresh schedules:**

| Dataset | Current frequency | Proposed frequency | Slots saved per 24h | Rationale |
|---|---|---|---|---|
| | | | | |

**Dataflow consolidation opportunities:**

| Current separate dataflows | Proposed combined dataflow | Slots saved |
|---|---|---|
| | | |

---

## Implementation Checklist

Copy from SKILL.md Review Checklist and tick items as completed:

- [ ] Dataset field list contains only fields referenced in SAQL queries, dashboard bindings, security predicates, or join keys
- [ ] All date and datetime fields used in SAQL timeseries or grouping expressions declared as type `Date` with explicit format string
- [ ] Duration or date-math fields pre-computed at ELT time as epoch integers
- [ ] Row count assessed; splitting applied if warranted
- [ ] Historical datasets scheduled at weekly or manual cadence
- [ ] 24-hour run count across all dataflows and Recipes confirmed below 55
- [ ] SAQL test queries verified on optimized dataset — no field-not-found errors, correct date grouping

---

## Notes and Deviations

Record any deviations from the standard pattern and why:

_____

---

## Output Artifacts Produced

| Artifact | Location / Description |
|---|---|
| Field whitelist | |
| Date granularity map | |
| Dataset splitting design | |
| Run-budget analysis | |
| Updated dataflow / Recipe configuration | |
