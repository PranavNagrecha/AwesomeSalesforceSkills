---
name: analytics-dataset-optimization
description: "Use this skill when tuning CRM Analytics dataset performance through field selection, date granularity choices, dataset splitting strategy, and run-budget optimization. Trigger keywords: dataset too many fields, SAQL timeseries slow, epoch vs date storage, dataset field count limit, dataset partition, split dataset by year, CRM Analytics performance tuning. NOT for SOQL optimization, Salesforce report tuning, Data Cloud segmentation performance, or choosing between analytics tools."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Operational Excellence
triggers:
  - "CRM Analytics dashboard is slow and the dataset has hundreds of fields"
  - "SAQL timeseries query is running slowly — should I store dates as epoch or date type?"
  - "Dataset is getting too large — should I split it into multiple datasets by year or region?"
  - "How do I reduce the field count in a CRM Analytics dataset without breaking dashboards?"
  - "Recipe is timing out on a wide dataset with 300+ columns pulled from Salesforce"
  - "Run budget is nearly exhausted — how do I schedule refreshes more efficiently?"
tags:
  - crm-analytics
  - dataset-performance
  - field-selection
  - date-granularity
  - dataset-splitting
  - run-budget
  - saql
inputs:
  - "Current dataset field list and approximate field count"
  - "SAQL queries and dashboard bindings that consume this dataset"
  - "Date and datetime fields used in timeseries charts or date range filters"
  - "Current recipe or dataflow run schedule and 24-hour run count"
  - "Estimated dataset row count and growth rate"
  - "Whether the dataset is sourced from a dataflow or a Recipe"
outputs:
  - "Trimmed field list containing only fields referenced in SAQL queries or dashboard bindings"
  - "Date granularity recommendation (epoch integer vs. Date type vs. Datetime type) per field"
  - "Dataset splitting design: criteria, naming convention, and SAQL union pattern if needed"
  - "Run-budget optimization plan with staggered schedules and consolidation recommendations"
  - "Dataflow or Recipe JSON snippet showing the optimized field selection and date declarations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Analytics Dataset Optimization

Use this skill when the work is specifically about reducing CRM Analytics dataset size and improving query performance through field pruning, date storage choices, dataset splitting, and refresh-schedule efficiency — not end-to-end architecture design. It activates when a practitioner has an existing or planned dataset and wants to make it faster, smaller, or cheaper to refresh.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What fields are actually used?** Pull the list of SAQL queries in all dashboards that read this dataset and extract every field reference. Fields not referenced by any SAQL query or dashboard binding are candidates for removal. This is the most impactful optimization available and is often skipped because it requires reading dashboard definitions.
- **What is the field-count ceiling?** CRM Analytics datasets support up to 5,000 fields per dataset. Beyond approximately 500 fields, sync time and query performance both degrade measurably even if the individual query only touches a small subset. Wide datasets cost more to process regardless of which fields a given query uses.
- **How are dates stored today?** Determine whether date/datetime fields are stored as epoch integers (seconds since 1970-01-01), Date type (YYYY-MM-DD string internally), or Datetime type. The storage choice affects SAQL expression complexity and timeseries performance.
- **Is the dataset a single large body or a candidate for splitting?** CRM Analytics has no native partition index. "Partitioning" in this platform means physically splitting data into multiple named datasets and querying each separately or combining them with SAQL `union`. This is an architectural pattern, not a platform feature.
- **How many runs does the org consume in a rolling 24-hour window?** The platform cap is 60 combined dataflow and Recipe runs per rolling 24-hour window (not a calendar-day reset). Orgs near this ceiling need schedule consolidation before adding or increasing refresh frequency.

---

## Core Concepts

### Field Selection: Only Include What Dashboards Actually Use

Every field included in a CRM Analytics dataset adds cost at three points: during the dataflow or Recipe run (more data is read from Salesforce and transformed), during the dataset write (more storage bytes written), and during every query execution (the query engine must address a wider schema even when a specific SAQL expression only touches a handful of columns).

The correct approach is to audit dashboard SAQL bindings first, produce a whitelist of referenced field names, and then configure the dataflow's `sfdcDigest` node (or the Recipe's Select Fields step) to include only those fields. A dataset that starts with 400 fields pulled from the Account object and is trimmed to 40 actually-used fields will sync roughly 10x faster and consume proportionally less storage.

CRM Analytics does not enforce minimum field counts for a dataset to function. A dataset with 10 fields is valid and fully queryable.

**Practical process:**
1. Export the dashboard JSON or use the Analytics REST API to retrieve lens and dashboard definitions.
2. Extract every field name appearing in `q` (SAQL query) parameters.
3. Add system fields required by row-level security predicates (e.g., `OwnerId`, `Role.Name`).
4. Add any fields used in the dataflow as join keys that must carry through to the output.
5. Use this whitelist as the field list in the `sfdcDigest` or Recipe Select Fields node.

### Date Granularity: Epoch vs. Date vs. Datetime

CRM Analytics supports three ways to represent a point in time in a dataset:

| Storage type | Internal representation | SAQL timeseries | Arithmetic | Storage cost |
|---|---|---|---|---|
| Epoch (numeric) | 64-bit integer (seconds since 1970-01-01 UTC) | Requires `toDate()` conversion | Fast integer arithmetic | Lowest |
| Date | Internally stored as epoch; dataflow declares `"type": "Date"` and a format string | Native; `timeseries` works directly | Date functions available | Low |
| Datetime | Epoch with sub-second precision; declared with datetime format string | Native | Date + time functions | Moderate |

**When to choose each:**

- **Date type** — The right default for most business date fields (CloseDate, CreatedDate, BillingDate). SAQL `timeseries`, `group by date`, and `date_to_epoch` all work natively. Dashboard date range pickers bind correctly.
- **Epoch integer** — Use when the dataset feeds complex SAQL math: computing durations, comparing two date fields as a difference, or feeding a numeric formula. Storing dates as epoch eliminates repeated `date_to_epoch()` calls at query time, which improves performance on large datasets. The tradeoff is that epoch integers are opaque to humans and require `toDate()` for any display formatting.
- **Datetime** — Use only when time-of-day granularity is genuinely needed for the dashboard. Datetime precision costs additional storage and makes SAQL grouping expressions more complex. If no dashboard filters or groupings use time-of-day, storing as Date is cheaper and sufficient.

**The common mistake:** Accepting Salesforce Datetime fields as-is without declaring an explicit type in the dataflow schema node. The field then arrives as a Text column in the dataset, making it unusable in SAQL timeseries expressions. See gotchas.

### Dataset Splitting: No Native Partition Index

CRM Analytics datasets do not have a native partition index. Unlike a database table with a partition key, a CRM Analytics dataset does not skip rows based on a filter at the storage level — every query scans the dataset. This means:

- A filter like `CloseDate >= date(2024, 1, 1)` on a 50-million-row dataset still reads all 50 million rows before filtering.
- Row count, not field count, is the primary driver of query scan time on large datasets.

**The architectural response** is to split data into separate named datasets — for example, `Opportunity_2022`, `Opportunity_2023`, `Opportunity_2024` — and query only the dataset relevant to the user's current time context. This is called dataset splitting, and it is a design pattern, not a platform feature.

Dataset splitting works best when:
- The dominant dashboard filter is always a specific year or fiscal period.
- Row counts per individual dataset drop below 5–10 million rows after splitting.
- The SAQL query can be written (or the dashboard configured) to target the appropriate dataset dynamically.

When a cross-period query is needed (e.g., a 3-year trend), SAQL supports `union` across two datasets. However, multi-dataset SAQL unions have performance limits and should be used sparingly.

### Run-Budget Optimization: The 60-Run Rolling Window

The platform permits at most 60 combined dataflow and Recipe runs within any rolling 24-hour window. This is a true rolling window: if 60 runs fire between 08:00 and 09:00, no further runs can start until 08:00 the next day as each slot expires.

Mature orgs frequently approach this ceiling when managed-package dataflows (Revenue Intelligence, Service Cloud Einstein, etc.) are running alongside custom dataflows. The correct optimization levers are:

- **Consolidate**: replace multiple single-object dataflows with a single multi-object dataflow (one run slot instead of N).
- **Tier refresh frequency**: identify datasets that power live operational dashboards (refresh every 2–4 hours) vs. datasets that power weekly reports (refresh once nightly). Reduce high-frequency runs to the minimum cadence the business actually requires.
- **Avoid redundant full-replace runs**: if a dataset is append-only and an incremental pattern is feasible, switching to incremental reduces run time and keeps the slot open sooner for other jobs.

---

## Common Patterns

### Pattern 1: Selective Field Include (Whitelist-Driven Field Pruning)

**When to use:** A dataset contains more fields than are referenced by any dashboard or SAQL query, typically because it was created by pulling all fields from a Salesforce object using `*` or because the original scope has since narrowed.

**How it works:**
1. Collect all SAQL queries from dashboards that read the dataset (use the Analytics REST API: `GET /wave/dashboards/{id}` and inspect the `steps` array for query strings, or export the dashboard bundle).
2. Extract every field name mentioned in the SAQL `q` parameter strings. Include fields used in `filter`, `group by`, `foreach`, `order by`, and `select` clauses.
3. Add any fields required by security predicates (`OwnerId`, `Name`, `UniqueUserName`, etc.).
4. Add join-key fields that are needed by downstream augment steps in other dataflows.
5. In the dataflow `sfdcDigest` node, replace the `fields` array with the whitelist. In a Recipe, use the Select Fields node to deselect all non-whitelisted columns.
6. Run the dataflow and confirm the dataset has the expected column count. Re-run any SAQL queries to confirm no "field not found" errors.

**Why not the alternative:** Pulling all fields avoids upfront analysis work but produces datasets that take significantly longer to sync (the Salesforce REST API call inside `sfdcDigest` must read every field value for every row) and query (wider datasets require more memory during execution).

### Pattern 2: Epoch Pre-Computation for Duration Math

**When to use:** A dashboard computes a duration between two date fields (e.g., days to close, days in stage, age of a case), and SAQL `date_to_epoch()` is being called repeatedly at query time on large datasets.

**How it works:**
1. In the dataflow or Recipe, add a `computeExpression` transformation after the `sfdcDigest` node.
2. Compute the duration as an integer at ELT time: `DaysToClose = (CloseDate_epoch - CreatedDate_epoch) / 86400` where `CloseDate_epoch` and `CreatedDate_epoch` are epoch integers.
3. Store the result as a numeric field `DaysToClose` in the dataset.
4. In SAQL, reference `DaysToClose` directly — no `date_to_epoch()` call needed at query time.

**Why not the alternative:** When `date_to_epoch()` is called in SAQL on a field stored as Date type, the conversion runs for every row on every query execution. On a 10-million-row dataset queried by 50 concurrent users, this is a significant and avoidable cost.

### Pattern 3: Year-Based Dataset Splitting

**When to use:** A dataset has grown to 20+ million rows and the dominant dashboard use case filters to a single fiscal year. Full-dataset scans are visibly slow (>5-second query times on simple aggregations).

**How it works:**
1. Identify the date field that determines which year a row belongs to (e.g., `CloseDate`).
2. Create separate Recipes (or dataflow branches) that filter source data to each year: `CloseDate >= "2022-01-01" AND CloseDate < "2023-01-01"` → writes `Opportunity_2022`; similar for 2023, 2024, and current year.
3. Schedule the current-year dataset to refresh frequently (nightly or more often). Schedule prior-year datasets to refresh weekly or not at all (they are immutable once the year is complete).
4. Update dashboards to target the appropriate year-specific dataset. If the dashboard has a year selector, use a SAQL binding that routes the query to the correct dataset name.
5. For cross-year trend views, implement a lightweight SAQL union across the relevant year datasets, or pre-aggregate the historical datasets into a summary dataset with month-level granularity.

**Why not the alternative:** Without splitting, every query — even one filtering to a single quarter — scans the full multi-year row set. CRM Analytics has no partition pruning, so the physical data split into separate datasets is the only way to limit scan scope.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Dataset has 300+ fields; dashboards use fewer than 50 | Whitelist-driven field pruning in sfdcDigest / Recipe Select Fields | Reduces sync time and query memory proportionally to fields removed |
| SAQL timeseries or date grouping is not working | Verify field is declared as Date type with explicit format string in schema node | Text columns cannot be used in SAQL date expressions |
| Dashboard computes duration between two date fields | Pre-compute duration as epoch integer at ELT time | Eliminates repeated date_to_epoch() at query time for every user query |
| Dataset exceeds 20M rows with a dominant year filter | Split into year-specific named datasets | No native partition pruning — physical split is the only way to limit scan scope |
| Run budget approaching 55 of 60 slots | Consolidate single-object dataflows; tier refresh frequency | Fewer, larger runs conserve budget; reduce high-frequency refreshes to minimum cadence |
| Historical years are immutable but scheduled to refresh nightly | Switch prior-year datasets to weekly or manual refresh | Historical data does not change; nightly refreshes waste run budget and compute time |
| Cross-year SAQL union is slow | Pre-aggregate historical years to month-level summary dataset | Month-level aggregation reduces scan rows dramatically for trend views |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit field usage.** Retrieve all SAQL queries from dashboards that reference the dataset (via Analytics REST API or dashboard bundle export). Extract every field name used in any SAQL clause. Produce a whitelist including all dashboard-referenced fields, row-level security predicate fields, and dataflow join keys. Count the total against the current dataset field list.
2. **Audit date field storage.** Inspect the dataset schema in Data Manager or via the Analytics REST API dataset metadata endpoint. For each date or datetime field, confirm the stored type (Date vs. Numeric/Text). Identify fields used in SAQL `timeseries`, `date_to_epoch()`, or duration math as candidates for granularity optimization.
3. **Assess row count and split candidates.** Retrieve the current row count and growth rate. If row count exceeds 10–20 million and dashboards have a dominant year or dimension filter, evaluate whether year-based or dimension-based dataset splitting would reduce per-dataset row counts below 5 million.
4. **Implement field pruning.** Update the dataflow `sfdcDigest` node `fields` array or the Recipe Select Fields node to include only the whitelisted fields. Re-run and validate that no "field not found" errors appear in dashboard queries.
5. **Fix date type declarations.** For any field stored as Text that should be Date, add or update the `schema` transformation node in the dataflow JSON with the correct `"type": "Date"` and `"format"` string. For fields used in duration math, add a `computeExpression` node to pre-calculate the duration as an epoch-based integer at ELT time.
6. **Implement dataset splitting if warranted.** Create separate Recipes or dataflow branches per year (or per dimension). Update dashboards to target year-specific dataset names. Set differential refresh schedules: current year refreshes frequently, prior years refresh infrequently or manually.
7. **Rebalance the run schedule.** Count all dataflow and Recipe runs in the org per rolling 24-hour window. If approaching 55 runs, consolidate single-object dataflows, reduce historical-year refresh frequency, and ensure no over-scheduled datasets consume slots unnecessarily. Document the revised schedule.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Dataset field list contains only fields actually referenced by SAQL queries, dashboard bindings, security predicates, or join keys
- [ ] All date and datetime fields used in SAQL timeseries or grouping expressions are declared as type `Date` (not Text or Numeric) with an explicit format string
- [ ] Duration or date-math fields are pre-computed at ELT time as epoch integers rather than computed at query time via `date_to_epoch()`
- [ ] Row count assessed; year-based or dimension-based splitting applied if row count exceeds 10–20 million and dashboards filter on a dominant dimension
- [ ] Historical (prior-year) datasets scheduled at weekly or manual cadence; only current-period datasets run at high frequency
- [ ] 24-hour run count across all dataflows and Recipes confirmed below 55 (leaving headroom for managed-package jobs and ad-hoc runs)
- [ ] SAQL test queries verified on the optimized dataset to confirm no field-not-found errors and correct date grouping behavior

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Field-count impact is invisible during development** — A wide dataset with 400 fields passes all dataflow validations and loads successfully. The performance cost only manifests at query time and at scale. Development orgs with small row counts show no slowdown; production orgs with millions of rows can show 5–10x query time differences between a 50-field and 400-field dataset containing the same rows.
2. **Datetime fields from Salesforce objects arrive as Text if the schema node is missing** — The `sfdcDigest` action reads Salesforce datetime values as ISO-8601 strings. Without an explicit `"type": "Date"` declaration in the `schema` transformation, CRM Analytics stores the column as Text. SAQL `timeseries` on a Text column returns no data and raises no visible error — the chart is simply empty.
3. **CRM Analytics "partitioning" is not database partitioning** — The platform has no partition index, no partition key, no partition pruning, and no DDL syntax for partitions. A query filtered to `year == 2024` on a multi-year dataset still scans all rows. The only way to achieve partition-like scan reduction is to physically separate data into multiple named datasets. LLM-generated advice that says "partition the dataset by year" without explaining this distinction will mislead practitioners into expecting automatic pruning.
4. **The 60-run rolling window resets per-slot, not at midnight** — If 60 runs fired between 08:00 and 10:00, the first slot clears at 08:00 the next day and each subsequent slot clears as it ages out of the 24-hour window. An org that exhausted its budget in the morning cannot recover until the earliest run slots begin to expire. Capacity planning that assumes midnight resets will systematically under-schedule recovery time.
5. **SAQL union across multiple datasets has row-count limits** — When implementing cross-year trend views via `union`, very large combined row sets (tens of millions of rows across all unioned datasets) can produce slow queries or timeouts. The correct response is to pre-aggregate historical datasets to month-level summaries before unioning, not to union raw-row datasets spanning multiple years.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field whitelist | Sorted list of fields confirmed as used in SAQL queries, security predicates, and join keys; forms the input for updated sfdcDigest / Recipe Select Fields configuration |
| Date granularity map | Per-field recommendation (Date type, epoch integer, or Datetime) with rationale for each field used in time-based SAQL expressions |
| Dataset splitting design | Naming convention, filter criteria per dataset, refresh schedule per dataset, and SAQL union pattern for cross-period queries |
| Run-budget analysis | Table of all org dataflows and Recipes with run frequency and daily slot consumption; proposed consolidated schedule |
| Updated dataflow or Recipe configuration | JSON snippet or Recipe step list showing optimized field selection, date schema declarations, and epoch pre-computation nodes |

---

## Related Skills

- architect/analytics-data-architecture — End-to-end CRM Analytics pipeline design, incremental load strategy, ELT push-down patterns, and dataset row-limit architecture. Use when the design work is structural rather than performance-tuning an existing dataset.
- admin/analytics-dataset-management — Admin-level dataset configuration, refresh scheduling, and quota management. Use when the task is operational (schedule changes, dataset refresh failures) rather than optimization-focused.
- admin/analytics-dataflow-development — Dataflow JSON authoring, transformation nodes, and debugging. Use when the optimization requires significant dataflow restructuring.
