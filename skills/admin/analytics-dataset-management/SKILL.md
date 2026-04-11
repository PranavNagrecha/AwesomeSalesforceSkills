---
name: analytics-dataset-management
description: "Use when creating or managing CRM Analytics datasets: configuring dataflows, scheduling refreshes, selecting fields, handling date types, managing row-count growth, or troubleshooting stale or broken datasets. Triggers: 'dataset creation', 'dataflow schedule', 'dataflow quota', 'date field not filterable', 'dataset row limit', 'CRM Analytics data refresh', 'field type mismatch in dataset'. NOT for standard Salesforce report types or choosing between analytics tools."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "dataflow is not running on schedule and data looks stale"
  - "date field in CRM Analytics cannot be grouped or filtered"
  - "dataset is hitting the row count limit and refreshes are failing"
  - "multiple dataflows running at the same time and some are being skipped"
  - "how do I schedule a CRM Analytics dataset to refresh every night"
  - "field is coming in as text but I need it as a date in SAQL queries"
tags:
  - crm-analytics
  - dataset-management
  - dataflow-scheduling
  - date-handling
  - data-refresh
inputs:
  - "Source Salesforce objects and fields that feed the dataset"
  - "Required refresh cadence (hourly, nightly, weekly)"
  - "Expected data volume (row count and field count)"
  - "Date fields that require filtering or grouping in SAQL"
  - "Number of dataflows currently running in the org"
outputs:
  - "Dataflow configuration plan with scheduling guidance"
  - "Field-type mapping for safe date ingestion"
  - "Dataset refresh schedule with quota impact assessment"
  - "Row-count management recommendations"
  - "Checklist for pre-production dataset validation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Analytics Dataset Management

Use this skill when building or maintaining CRM Analytics datasets — covering dataflow design, field type configuration (especially dates), refresh scheduling, and platform quota management. This skill activates whenever the work is about how data gets into and stays current in a CRM Analytics dataset, not which analytics tool to use.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many active dataflows are already scheduled in the org, and what are their run windows? (Org-wide limit: 60 dataflow runs per 24-hour rolling window.)
- Are there any date or datetime fields that must support SAQL filtering or grouping? These must be typed at ingest time.
- What is the approximate row volume per object? Datasets are capped at 500 million rows per org across all datasets.
- Does the team own the dataflow, or is it a managed-package-generated flow that should not be edited?
- Is Data Sync (direct connector) in use, or are dataflows built by hand as JSON transformations?

---

## Core Concepts

### Dataflow Scheduling and the 60-Run Quota

Every CRM Analytics org is limited to 60 dataflow runs in any rolling 24-hour period. This quota is org-wide, not per-dataflow. An org with five dataflows each set to run every four hours will consume 5 × 6 = 30 runs per day — half the budget. Orgs that also run Data Sync, recipe jobs, and managed-package dataflows from products like Revenue Intelligence can exhaust this quota silently: later-in-the-day jobs are queued and may simply not run. Salesforce does not raise an in-product alert by default when the quota is saturated.

When a job is skipped because the quota is exhausted, the dataset retains the data from the last successful run. Downstream dashboards then serve stale data without any visible error badge unless the admin has configured a dataset-freshness monitor.

**Design rule:** Map all dataflows and their run frequencies before adding a new schedule. Stagger run windows and reduce unnecessary overlap. Use a single multi-object dataflow in preference to several single-object flows wherever practical.

### Date Field Type Handling at Ingest

CRM Analytics stores each dataset column with a resolved type: Text, Numeric, or Date. The type is assigned during dataflow execution — it is not inferred post-hoc by the query engine. A field that arrives without an explicit `fiscalMonthOffset`, `format`, or `type: "Date"` declaration in the dataflow JSON is stored as Text.

Text columns cannot be used in SAQL `timeseries`, `group by`, or `date_to_epoch` expressions. A practitioner who builds a dataflow from an object with a Salesforce Date field will get a Text column in the dataset unless they explicitly declare the field type in the schema node or augment it with a `computeExpression` step that parses the text into a proper date using `toDate()`.

The safe pattern is to declare the type in the `schema` transformation step. For datetime fields from Salesforce objects, the standard format string is `"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"`. For plain Date fields, use `"yyyy-MM-dd"`.

### Dataset Row Limits and Growth Management

The per-org ceiling for CRM Analytics datasets is 500 million total rows across all datasets. Individual dataset uploads can be full-replace or upsert (incremental). Full-replace jobs re-ingest all rows on every run. Incremental (append) jobs add rows without removing old ones, which means datasets can grow without bound unless a trim step is explicitly included.

Orgs with high-frequency activity logs, email interaction records, or large historical objects routinely hit the row ceiling within a few quarters if datasets are append-only and never trimmed. Once the ceiling is reached, subsequent dataflow runs fail with a capacity error; no rows are written to any dataset until total row count drops below the limit.

---

## Common Patterns

### Staggered Multi-Object Dataflow

**When to use:** When multiple objects must be loaded into a single dataset, or when the org already has several independent dataflows competing for the same run window.

**How it works:**
1. Combine all object loads into one dataflow definition using `sfdcDigest` nodes for each object, a `augment` or `join` node to merge them, and a single `register` node at the end.
2. Schedule the combined dataflow for a single window (e.g., 02:00 UTC nightly).
3. Eliminate the individual single-object dataflows that previously ran separately.

**Why not separate flows:** Each separate flow consumes one run against the 60-run quota. Five separate nightly flows cost five quota slots. A single combined flow costs one.

### Explicit Date-Type Schema Declaration

**When to use:** Whenever a Salesforce Date or Datetime field must support time-series charts, date range filters, or SAQL date functions.

**How it works:**
In the dataflow JSON, add a `schema` transformation after the `sfdcDigest` node. Declare the field with `"type": "Date"` and the correct `"format"` string.

```json
{
  "schema_Opportunities": {
    "action": "schema",
    "parameters": {
      "fields": [
        {
          "name": "CloseDate",
          "newName": "CloseDate",
          "type": "Date",
          "format": "yyyy-MM-dd",
          "fiscalMonthOffset": 0
        }
      ],
      "source": "digest_Opportunities"
    }
  }
}
```

If the field was already ingested as Text, use a `computeExpression` node with `toDate(CloseDate, "yyyy-MM-dd")` to convert it before the `register` node.

**Why not leave it as Text:** Text columns silently pass through dataflow validation but fail at query time. SAQL `timeseries` expressions return no data, and dashboard date filters have no effect.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need nightly refresh of three objects into one dataset | Single combined dataflow, one schedule | Conserves the 60-run quota |
| Date field is stored as Text in existing dataset | Add `computeExpression` with `toDate()` before `register` node | Avoids re-ingesting all schema nodes; targeted fix |
| Dataset row count approaching 400M+ rows | Add a `filter` node or switch from append to full-replace with a date window | Prevents hitting 500M org ceiling and blocking all future runs |
| Multiple managed-package dataflows occupying peak run windows | Schedule custom dataflows to off-peak hours; contact package vendor for schedule controls | Managed flows cannot be edited directly |
| New object added to existing dataflow | Add `sfdcDigest` node for the object and augment into existing flow | Cleaner than creating a second flow that must be joined later |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit existing dataflows and quota usage** — List all active dataflows and recipes in the org, note their run frequencies and schedules, and calculate current 24-hour run consumption. Flag any orgs approaching 50+ runs/day before adding new schedules.
2. **Map source objects and required fields** — Identify every Salesforce object, field, and relationship needed. Mark all Date and Datetime fields explicitly; these require type declarations.
3. **Design the dataflow JSON** — Build or update the dataflow using `sfdcDigest` nodes for each object. Add `schema` nodes for date fields immediately after each digest. Add `augment` or `join` nodes for multi-object merges. End with a single `register` node.
4. **Set the refresh schedule** — Choose a run window that fits within the remaining quota budget. Prefer off-peak hours. Use staggered start times when multiple dataflows must run in the same day.
5. **Run and validate** — Execute the dataflow once manually. Inspect the dataset column list to confirm date fields show type `Date` not `Text`. Run a test SAQL query using a date filter to confirm filtering works.
6. **Monitor dataset row count** — After the first successful run, note the dataset row count. For append-mode datasets, project growth over 6 and 12 months. Add a trim or full-replace strategy if the projection approaches 400M rows.
7. **Document ownership** — Record the dataflow owner, refresh schedule, and escalation path for failure notifications. Configure email alerting on dataflow failure in CRM Analytics Studio > Data Manager.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All date and datetime fields have explicit `type: "Date"` and `format` string in the schema node
- [ ] 24-hour dataflow run count (including managed packages) is below 55 runs to preserve headroom
- [ ] Dataset row count is inventoried; append-mode datasets have a documented trim strategy
- [ ] Dataflow schedule is staggered away from competing flows and off-peak for the org's region
- [ ] A manual test run was executed and the dataset column types were verified in Data Manager
- [ ] Failure alerting is configured (email notification on dataflow run failure)
- [ ] A SAQL test query was run against any date field used in dashboard filters or timeseries charts

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Quota exhaustion is silent by default** — When the 60-run/day quota is hit, queued dataflows are not run and no in-product alert is raised. Dashboards serve yesterday's data and users assume the analytics is working. Only a monitoring alert on dataflow run history reveals the problem.
2. **Date fields ingested as Text cannot be patched by SAQL** — SAQL `timeseries` expressions require a column of type Date in the dataset. Wrapping a Text column in `toDate()` at query time does not work; the column must be declared as Date at ingest in the dataflow. The only fix for an already-live dataset is to add a `computeExpression` node to the dataflow and re-run it.
3. **Append-mode datasets grow without bound** — CRM Analytics does not automatically expire old rows. A dataset loaded in append mode with no filter or row-count cap will accumulate rows indefinitely until the org hits the 500M ceiling, at which point all dataset writes across the org fail.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dataflow JSON configuration | Ready-to-use dataflow definition with correct schema nodes, date type declarations, and register step |
| Quota impact assessment | Table of current dataflow run counts and projected daily usage after the proposed changes |
| Dataset row-count projection | Estimate of dataset growth over 6 and 12 months with recommended trim strategy |
| Refresh schedule plan | Staggered schedule for all org dataflows showing no window conflicts |

---

## Related Skills

- admin/einstein-analytics-basics — Use for deciding whether CRM Analytics is the right tool and for license/access troubleshooting. NOT for dataset construction or scheduling mechanics.
- admin/data-import-and-management — Use when source data quality or load strategy is the primary concern. NOT for CRM Analytics-specific dataset pipelines.
