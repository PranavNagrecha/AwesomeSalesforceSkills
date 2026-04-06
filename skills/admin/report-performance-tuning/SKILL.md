---
name: report-performance-tuning
description: "Use when a report or dashboard is slow, timing out, hitting row limits, or consuming excessive system resources on large-volume objects — covers selective filter strategy, custom report type optimization, async report execution via Analytics API, dashboard refresh scheduling, and grouping/aggregation tuning. Triggers: 'report times out', 'report is slow', 'dashboard not refreshing', 'report row limit hit', 'too many report results'. NOT for CRM Analytics / Tableau CRM performance (separate skill). NOT for sharing-model or visibility issues causing missing rows (use admin/sharing-and-visibility). NOT for building or designing reports from scratch (use admin/reports-and-dashboards-fundamentals)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
  - Reliability
triggers:
  - "report times out or takes too long to load on a large object"
  - "dashboard is slow to refresh or shows stale data"
  - "report is hitting the 2000 row display limit and users are missing data"
  - "custom report type with 4 objects is slower than the standard equivalent"
  - "how do I run a report on millions of records without it failing"
  - "async report execution via Analytics API for large data sets"
  - "scheduled dashboard refresh not keeping up with data changes"
tags:
  - reports
  - dashboards
  - performance
  - large-data-volumes
  - analytics-api
  - report-filters
  - async-reports
  - dashboard-refresh
inputs:
  - "The report or dashboard name and the primary object it is built on"
  - "Approximate record volume on the primary object (orders of magnitude sufficient)"
  - "Current filters applied — or confirmation that no filters exist"
  - "Report type: standard or custom, and how many objects are spanned"
  - "Whether the report is run interactively, on subscription, via dashboard, or via API"
outputs:
  - "Filter strategy recommendation with specific fields to use (date range, owner, record type)"
  - "Report type simplification recommendation if applicable"
  - "Async execution pattern using Analytics API for reports over 2,000 rows"
  - "Dashboard refresh schedule and component count guidance"
  - "Grouping and aggregation design to reduce processing overhead"
  - "Review checklist for performance sign-off"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Report Performance Tuning

Use this skill when a Salesforce report or dashboard is slow, timing out, or returning incomplete results due to data volume. It applies selective filter strategy, report type optimization, async execution patterns, and dashboard scheduling guidance to resolve performance issues on large objects.

---

## Before Starting

Gather this context before working in this domain:

- **Primary object record count**: Reports on objects with millions of records will time out or degrade unless at least one selective filter limits the query scan. Ask for an estimate; even "hundreds of thousands" vs "tens of millions" changes the recommendation.
- **Current filters**: Reports with no date range, no owner, and no record type filter will perform a full table scan. This is the most common root cause of timeouts.
- **Report type and object span**: Standard report types (pre-joined by Salesforce) are faster than custom report types spanning 4+ objects. A custom report type spanning 4 objects triggers extra join processing for every row.
- **Execution context**: Interactive (UI), scheduled subscription, dashboard component, or Analytics API — each has different timeout thresholds and row limits.
- **Org edition**: Async report execution via Analytics API requires API access. Dynamic dashboard running-user count caps vary by edition.

---

## Core Concepts

### Selective Filters and Full Table Scans

Salesforce Reports query the underlying database. Without a selective filter — a field with high selectivity that limits rows early in the execution plan — the engine must scan the entire object. The three most consistently selective filter fields on any standard object are:

1. **Date range on a standard date field** (e.g., Close Date, Created Date) — restricts the scan window.
2. **Owner / assigned-to field** — partitions by user, reducing rows significantly in large orgs.
3. **Record Type** — partitions by type when multiple record types share the same object.

At least one of these must be present on any report targeting an object with more than ~500,000 records. Combining two or more dramatically reduces query time.

### Row Limits: Displayed vs. Queryable

The report UI displays a maximum of **2,000 detail rows** in the Lightning interface. This is a display limit, not a query limit. The underlying query can access up to approximately 2 billion rows when filters are applied. Practitioners who hit the 2,000-row cap and need all results must use the **Analytics API** — either synchronous for smaller datasets or asynchronous for larger ones. Async API calls return a job ID; results are polled and downloaded from the response payload.

### Custom Report Types and Join Complexity

Custom report types (CRTs) allow spanning up to 4 objects with configurable inner/outer join behavior. Each additional object added to a CRT increases join complexity. A CRT spanning 4 objects on high-volume data can perform 3–10x slower than the equivalent standard report type on the same objects. When a CRT spans more than 2 objects and the report is slow, check whether a standard report type covers the same data before optimizing filters.

### Dashboard Refresh Behavior

Dashboard data is cached. There are three refresh modes:

1. **Manual refresh** — user clicks Refresh; a real-time query runs against all component reports.
2. **Scheduled refresh** — the minimum interval for dynamic dashboards is **24 hours**; static dashboards can also be scheduled during off-peak windows.
3. **Dashboard subscriptions** — email snapshot delivery; does not refresh the cached dashboard view.

Adding too many components (more than 20 on a single dashboard) multiplies query load on every refresh cycle. Each component runs its underlying report independently.

---

## Common Patterns

### Pattern: Selective Filter Layer

**When to use:** A report is timing out or very slow and the underlying object has high record volume (>500K records).

**How it works:**
1. Identify the most selective standard field available — typically a date field on the object.
2. Add a date range filter (e.g., "Close Date equals THIS YEAR" or a relative range covering 90 days).
3. If date alone is insufficient, layer an Owner = Current User or Record Type = [specific type] filter.
4. Communicate to end users that they must narrow the date range if they need to search further back. Provide multiple saved reports with different pre-set ranges when needed.

**Why not filter-free:** A report without a date or owner filter on Opportunity with 10M records can take 60+ seconds or time out entirely, even when the user only needs the last quarter's data.

### Pattern: Async Analytics API for Full Result Sets

**When to use:** Users need all rows, not just the 2,000 displayed in the UI, and the result set is large.

**How it works:**
1. Submit the report execution using `POST /services/data/vXX.0/analytics/reports/{reportId}/instances` with `reportMetadata` filters in the request body.
2. Capture the returned `id` (instance ID) from the response.
3. Poll `GET /services/data/vXX.0/analytics/reports/{reportId}/instances/{instanceId}` until the `status` field returns `Success`.
4. Parse the `factMap` from the response. Use `includeDetails: true` in the request body to include row-level detail.
5. For reports exceeding ~2M rows, break the date range into time-bounded chunks and submit multiple async requests, then merge results downstream.

**Why not synchronous API:** The synchronous `GET /analytics/reports/{reportId}` endpoint applies the same 2,000-row display cap and can time out for complex or large reports.

### Pattern: Report Type Simplification

**When to use:** A custom report type spans 3–4 objects and performance is poor even with selective filters applied.

**How it works:**
1. List every field displayed in the report and map each to the object it comes from.
2. If fields from only 1–2 objects are actively used, rebuild on the closest standard report type.
3. If a CRT is required, remove every object from the relationship chain that contributes no active fields.
4. Consider producing separate reports per object pair and joining results outside Salesforce (via export or CRM Analytics) when a join cannot be simplified further.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Report on fewer than 100K records is slow | Add a selective filter; no other changes needed | Low volume — filters alone resolve it |
| Report on more than 500K records times out | Mandatory selective filter (date + owner or record type) | Full table scan on large objects is the primary cause |
| Users need more than 2,000 rows | Analytics API async execution | UI hard-caps at 2,000 display rows |
| CRT spans 4 objects and query is slow | Simplify to fewer objects or use standard report type | Each additional CRT object adds join overhead |
| Dashboard refresh shows stale data | Check refresh schedule; reduce component count | Minimum scheduled refresh is 24hr; many components multiply query load |
| Report must run nightly for large data | Schedule via Analytics API during off-peak hours | Avoids resource contention with interactive users |
| Report subscription not delivering | Verify report is under 2,000 rows or switch to async API export | Subscriptions use the same row cap as the UI |

---

## Recommended Workflow

1. **Identify the object and volume.** Confirm the primary object and approximate record count. Ask whether the slowness appears in the UI, a subscription, a dashboard component, or an API call — the correct fix differs across these contexts.
2. **Audit current filters.** List every active filter on the report. If there is no date range, owner, or record type filter on a large object, that is the root cause. Add at least one selective filter before making any other changes.
3. **Evaluate the report type.** Determine whether it is a standard or custom report type. If it is a CRT spanning 3–4 objects, count which objects contribute fields that are actually displayed in the report. Remove any object from the CRT that contributes no active fields.
4. **Address row limit requirements.** If the user needs more than 2,000 rows, switch to the Analytics API async pattern. Confirm API access is available in the org and provide the polling pattern with error handling for `Error` and `Running` status states.
5. **Optimize dashboard component count.** If the complaint is a slow or stale dashboard, count components. Recommend splitting dashboards over 20 components into multiple focused dashboards. Adjust the refresh schedule to off-peak hours.
6. **Test and validate.** Run the modified report and measure load time. For async API executions, confirm the job completes with `Success` status and the row count matches expectations.
7. **Document the filter contract.** Record the required filters in the report description and in the work template so future editors understand they must not remove them.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] At least one selective filter (date range, owner, or record type) is applied to every report on an object with more than 500K records
- [ ] Custom report type spans no more objects than required by the active field set
- [ ] Reports requiring more than 2,000 rows use Analytics API async execution, not UI export
- [ ] Dashboard component count is 20 or fewer per dashboard
- [ ] Dashboard refresh is scheduled during off-peak hours if automated
- [ ] Required filters are documented in the report description to prevent accidental removal
- [ ] Async API polling code includes error handling for `Error` and `Running` status states

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The 2,000-row limit is a display cap, not a query cap** — Practitioners often believe Salesforce "only stores 2,000 records" in a report. In reality, the filter can scan up to approximately 2 billion rows; the 2,000 limit is only what the UI renders. Removing filters to "see more data" makes the query slower without returning more rows to the screen.
2. **Scheduled dashboard minimum refresh is 24 hours** — Dynamic dashboards cannot be scheduled to refresh more frequently than once every 24 hours. Teams expecting near-real-time data on a scheduled dashboard will always see stale results; they must use manual refresh or move to a report subscription for timely delivery.
3. **CRT outer joins inflate row counts unpredictably** — Custom report types configured with "with or without" (outer join) behavior on a high-volume child object can return far more rows than expected, causing timeouts that do not occur with inner joins. Always verify join type when a CRT report is slower than a comparable standard report.
4. **Analytics API synchronous endpoint still caps at 2,000 rows** — The synchronous `GET /analytics/reports/{id}` endpoint does not bypass the display row limit. Many developers assume that calling the API removes the cap; it does not. The async `POST /analytics/reports/{id}/instances` endpoint is required for full result sets.
5. **Report subscriptions run as the subscriber** — When a subscription fails or delivers partial data, the root cause is often that the subscriber's sharing access restricts rows, or the report times out at the subscriber's data volume. Debugging as an admin will show more rows and a faster run, masking the real issue.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Filter strategy recommendation | Which fields to filter on, with relative date range suggestions tailored to the object |
| Report type assessment | Recommendation to keep or simplify the CRT, with rationale for any object removals |
| Async API execution pattern | Polling logic sketch and parameter guidance for Analytics API async report execution |
| Dashboard optimization plan | Component count target, refresh schedule, and split recommendation |
| Performance sign-off checklist | Completed checklist confirming all criteria are met before handoff |

---

## Related Skills

- admin/reports-and-dashboards-fundamentals — for designing a report or dashboard from scratch before performance becomes a concern
- admin/data-skew-and-sharing-performance — for sharing model issues that cause slow sharing recalculations on the same large objects
- admin/sharing-and-visibility — when missing rows in a report are caused by sharing access, not query performance
