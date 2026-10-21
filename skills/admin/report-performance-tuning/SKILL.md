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
  - "I want to a report or dashboard is slow"
  - "report cannot open more than 50000 rows"
  - "tabular report dump as excel substitute"
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
  - "Extraction path for result sets over 2,000 rows: filter-chunked report runs (the Reports and Dashboards REST API returns only the first 2,000 rows, sync or async) or a Bulk API 2.0 query"
  - "Dashboard refresh schedule and component count guidance (UNVERIFIED Help-only caps flagged)"
  - "Grouping and aggregation design to reduce processing overhead"
  - "Review checklist for performance sign-off"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---


# Report Performance Tuning

Use this skill when a Salesforce report or dashboard is slow, timing out, or returning incomplete results due to data volume. It applies selective filter strategy, report type optimization, API execution patterns, and dashboard scheduling guidance to resolve performance issues on large objects.

Sources used below: the Large Data Volumes guide (`ldv 264`), the Metadata API guide (`api_meta 264`), and the Reports and Dashboards REST API Developer Guide 262 pages "Requirements and Limitations" (`rdapi limits`) and "Run Reports Synchronously or Asynchronously" (`rdapi run`), fetched from developer.salesforce.com because that guide is not in the corpus. The same limits are in the corpus for the Apex flavour of the API: "The API returns up to the first 2,000 report rows" (apexdev 264 L33689), 1,200 async / 500 sync runs per hour, 24-hour async results (L33683-33688), and "When you run a report, the API returns data for the same number of records that are available when the report is run in the Salesforce user interface" (L33714-33715).

---

## Before Starting

Gather this context before working in this domain:

| Context | Why it matters |
|---|---|
| Primary object record count | Reports, like SOQL and list views, "depend on selectivity and indexes" (ldv 264 L225-226); an index is used only below its threshold — standard indexes under 30% of the first million records, custom under 10% (ldv 264 L463, L468). Ask for an estimate; "hundreds of thousands" vs "tens of millions" changes the recommendation. |
| Current filters | Without a selective, indexed filter "the query optimizer must perform a full scan" (ldv 264 L305-307). Fields indexed by default include Id, Name, OwnerId, CreatedDate, SystemModstamp and RecordType, plus lookup and master-detail fields (ldv 264 L308-309). |
| Report type and object span | A custom report type joins at most four objects (api_meta 264 L108487); the LDV guide says to minimize the objects and relationships a report queries (ldv 264 L794-796). |
| Execution context | Interactive (UI), subscription, dashboard component, or the REST API. The API "returns data for the same number of records that are available when the report is run in the Salesforce user interface" (rdapi run) and "up to the first 2,000 report rows" (rdapi limits). |
| Org edition | The Reports and Dashboards REST API "is available for any organization that has API enabled" (rdapi limits). |

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How many records are on the primary object, and which filter fields are indexed? | Index thresholds decide whether a filter avoids a full scan (ldv 264 L463, L468) — Gotcha 1 | The filter field the optimizer can actually use |
| Does anyone need more than 2,000 detail rows? | The REST API returns only the first 2,000 rows, sync or async (rdapi limits) — Gotcha 2 | Filter-chunked runs or a Bulk API 2.0 query instead of a "bigger report" |
| Is the report on a custom report type, and does it use outer joins? | Up to four objects; an outer join "returns a row even if the joined table doesn't contain a matching value" (api_meta 264 L108487, L108493-108495) — Gotcha 3 | A shorter join chain or inner joins |
| Is the dashboard dynamic (`LoggedInUser`) or `SpecifiedUser`? | `SpecifiedUser` shows every viewer one user's data (api_meta 264 L50170-50174); scheduling limits are Help-only — Gotcha 4 | The right refresh plan and a security sign-off |
| Who receives the subscription, and what can they see? | Subscription run-as behaviour is UNVERIFIED (Help-only) — Gotcha 5 | A test run with the subscriber's access |
| How many detail columns, summaries and custom summary formulas does the report have? | The error text refuses a report that is not "fewer than 100 columns" (rdapi error codes), while the limits say "up to 100" (apexdev 264 L33681) — Gotcha 6 | A column budget of 99 or fewer |
| Is any filter logic expected to cover a cross filter? | Filter logic lives in `ReportFilter.booleanFilter` while cross filters are a separate `Report.crossFilters` list (api_meta 264 L107296, L106680; the field is marked API 68.0 and later at L106682, though the guide's cross-filter sample says API 23.0, L107853) — Gotcha 7 | Logic that covers only field filters |

A proper configuration makes each report selective on an indexed field and sized to what the platform will return, where "just doing it" removes filters until the report times out or silently stops at 2,000 rows.

## Core Concepts

### Selective Filters and Full Table Scans

The query optimizer determines filter selectivity for reports the same way it does for SOQL and list views (ldv 264 L225-226). A filter is useful only when it is selective **and** indexed: "Without the necessary indexes, the query optimizer must perform a full scan to fetch the target rows" (ldv 264 L305-307). Consistently useful filter fields:

1. **Date range on an indexed date field** — CreatedDate is indexed by default (ldv 264 L308-309); in Report metadata the standard date filter is `timeFrameFilter` with a Required `dateColumn` and `interval` (api_meta 264 L107791-107801). UNVERIFIED (2026-10-21): that Opportunity Close Date is indexed by default — it is not in the guide's list.
2. **Owner** — OwnerId is indexed by default (ldv 264 L309).
3. **Record Type** — RecordType is indexed by default (ldv 264 L309).

For AND conditions, the overall filter is selective when it targets fewer than twice each filter's threshold, or the threshold for the intersection (ldv 264 L280-282). UNVERIFIED (2026-10-21): this skill's "~500,000 records" trigger for mandatory filters is a rule of thumb, not a platform number.

### Row Limits: What the API Returns

UNVERIFIED (2026-10-21): the 2,000-detail-row display limit in the Lightning report run page is Help-only, and the earlier "approximately 2 billion rows" figure has no source. What the API guides state: the API returns "up to the first 2,000 report rows. You can narrow results using filters" (rdapi limits; apexdev 264 L33689), and it returns the same number of records as the UI (rdapi run; apexdev 264 L33714-33715). **Asynchronous runs do not lift the 2,000-row cap.** Via Apex, synchronous report rows also count toward the 50,000-rows-per-transaction SOQL limit, which async runs avoid (apexdev 264 L33700-33702). Their documented advantages are different: "The 2-minute overall Salesforce API timeout limit doesn't apply to asynchronous runs", more concurrent runs, and results "stored for a 24-hr rolling period" (rdapi run). To get every row, either split the run into filter windows that each return fewer than 2,000 rows, or query the object directly with Bulk API 2.0, which exists "to perform bulk queries on your org data" (api_asynch 264 L136-137).

### Custom Report Types and Join Complexity

"A maximum of four objects can be joined in a custom report type. When more than two objects are joined, an inner join isn't allowed if there has been an outer join earlier in the join sequence" (api_meta 264 L108487-108489). Reducing the objects and relationships a report queries is an LDV best practice (ldv 264 L794-796). UNVERIFIED (2026-10-21): the "3–10x slower" figure for a four-object CRT — no corpus measurement.

### Dashboard Refresh Behavior

`Dashboard.dashboardType` is `SpecifiedUser` ("All users see data at the access level of one specific running user"), `LoggedInUser` (each user sees data by their own access) or `MyTeamUser` (api_meta 264 L50170-50190). The REST API allows "up to 200 dashboard refreshes per hour" (rdapi limits). Scheduled refreshes are `CronJobDetail.JobType` `3` — Dashboard Refresh (obj 264 L86824, L86850). UNVERIFIED (2026-10-21): the refresh modes and scheduling minimums (this skill earlier said dynamic dashboards refresh at most every 24 hours), whether subscriptions update the cached view, and the 20-components guidance — all Help-only.

---

## Common Patterns

### Pattern: Selective Filter Layer

**When to use:** A report is timing out or very slow and the underlying object has high record volume.

**How it works:**
1. Identify the most selective **indexed** field — CreatedDate, OwnerId or RecordType are indexed by default (ldv 264 L308-309); measure selectivity with `GROUP BY ROLLUP` as the LDV guide shows (ldv 264 L245-248).
2. Add a date range (`timeFrameFilter`, e.g. a relative 90-day interval).
3. If date alone is insufficient, layer an Owner (`scope` such as `MyAccounts`, api_meta 264 L106822-106829) or Record Type filter.
4. Provide multiple saved reports with different pre-set ranges when users need to look further back.

**Why not filter-free:** Without a selective indexed filter the optimizer performs a full scan (ldv 264 L305-307). UNVERIFIED (2026-10-21): the "10M records, 60+ seconds" illustration.

### Pattern: Getting More Than 2,000 Rows

**When to use:** Users or an integration need every matching row.

**How it works:**
1. Accept that a report run returns at most the first 2,000 rows through the API (rdapi limits) — sync and async alike.
2. For a recurring extract, use a Bulk API 2.0 query job on the object (api_asynch 264 L136-137) instead of a report.
3. If it must be a report, split it into filter windows (e.g. one month of CreatedDate per run) that each return fewer than 2,000 rows, run each asynchronously — `POST /services/data/vXX.0/analytics/reports/{reportId}/instances` returns an instance ID (rdapi run) — and poll the instance until `status` is `Success` or `Error` (values `New`, `Running`, `Success`, `Error`; Instances List page, rdapi 262).
4. The guide's sync example passes `?includeDetails=true` as a URL parameter (rdapi run); UNVERIFIED (2026-10-21): its form on the async POST.

**Why async still helps:** the 2-minute API timeout does not apply and results stay available for 24 hours (rdapi run); the org may request up to 1,200 asynchronous runs per hour versus 500 synchronous (rdapi limits).

### Pattern: Report Type Simplification

**When to use:** A custom report type spans 3–4 objects and performance is poor even with selective filters applied.

**How it works:**
1. List every field displayed in the report and map each to the object it comes from.
2. If fields from only 1–2 objects are actively used, rebuild on the closest standard report type.
3. If a CRT is required, remove every object from the relationship chain that contributes no active fields, and use inner joins (`outerJoin` false, api_meta 264 L108493) unless "with or without" rows are needed.
4. For heavy aggregates, store summarized data on the parent: "This practice is more efficient than having the report summarize the child records" (ldv 264 L799-801).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Report on fewer than 100K records is slow | Add a selective filter; no other changes needed | Low volume — filters alone usually resolve it |
| Report on a large object times out | Mandatory selective, indexed filter (date + owner or record type) | Full scan without an index (ldv 264 L305-307) |
| Users need more than 2,000 rows | Bulk API 2.0 query, or filter-chunked report runs under 2,000 rows each | The REST API returns only the first 2,000 rows, sync or async (rdapi limits) |
| CRT spans 4 objects and query is slow | Simplify to fewer objects or use a standard report type | Minimize objects and relationships (ldv 264 L794-796) |
| Dashboard refresh shows stale data | Check the schedule (`CronJobDetail.JobType` 3) and component count | Scheduling minimums and component guidance are Help-only (UNVERIFIED) |
| Report must run nightly for large data | Bulk API 2.0 query job during off-peak hours | Reports cap at 2,000 rows via the API |
| Report subscription not delivering | Run the report with the subscriber's access and check its size | Subscription run-as and row behaviour are UNVERIFIED (Help-only) |

---

## Recommended Workflow

1. **Identify the object and volume.** Confirm the primary object and approximate record count, and where the slowness appears (UI, subscription, dashboard component, or API).
2. **Audit current filters.** List every filter, including `timeFrameFilter` and `scope`. If none is selective on an indexed field (ldv 264 L308-309), add one before anything else.
3. **Evaluate the report type.** For a CRT, count objects in the `ReportType` join chain and check `outerJoin` (api_meta 264 L108487-108495); remove objects that contribute no displayed fields.
4. **Address row limit requirements.** Over 2,000 rows → Bulk API 2.0 query, or filter windows under 2,000 rows each; never promise the async endpoint returns more (rdapi limits).
5. **Check dashboards.** Note `dashboardType` (api_meta 264 L50170) and the component count; split very large dashboards (component guidance UNVERIFIED).
6. **Run the checker.** `python3 skills/admin/report-performance-tuning/scripts/check_report_performance_tuning.py --manifest-dir force-app/main/default` (add `--strict` in CI), then run the modified report and measure load time.
7. **Document the filter contract.** Record the required filters in the report `description` (a Report metadata field, api_meta 264 L106706) and in the work template.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every report on a large object has at least one selective filter on an indexed field (date, owner, or record type)
- [ ] Custom report type spans no more objects than required by the active field set, with inner joins unless outer rows are needed
- [ ] No requirement assumes the API (sync or async) returns more than the first 2,000 rows
- [ ] Reports stay under 100 columns (detail columns + summaries + custom summary formulas)
- [ ] `SpecifiedUser` dashboards have a security sign-off for the running user's data scope
- [ ] Dashboard refresh is scheduled during off-peak hours if automated
- [ ] Required filters are documented in the report description to prevent accidental removal
- [ ] Async API polling code handles `New`, `Running`, `Success` and `Error`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The REST API returns only the first 2,000 report rows — async included** — "The API returns up to the first 2,000 report rows. You can narrow results using filters" (rdapi limits; apexdev 264 L33689). Async runs avoid the 2-minute API timeout and keep results 24 hours (rdapi run); they do not return more rows. UNVERIFIED (2026-10-21): the UI display cap and the "2 billion rows scanned" figure.
2. **Scheduled dashboard refresh limits are Help-only** — UNVERIFIED (2026-10-21): the 24-hour minimum this skill stated for dynamic dashboards. Grounded: `CronJobDetail.JobType` 3 = Dashboard Refresh (obj 264 L86850); the REST API allows 200 dashboard refreshes per hour (rdapi limits).
3. **CRT outer joins return unmatched rows** — "An outer join returns a row even if the joined table doesn't contain a matching value in the join column" (api_meta 264 L108493-108495). Always verify join type when a CRT report is slower than a comparable standard report.
4. **Async is not a row-limit bypass** — the async `POST /analytics/reports/{id}/instances` endpoint is for long runs and concurrency (rdapi run), not for more than 2,000 rows (rdapi limits); full extracts go through Bulk API 2.0 (api_asynch 264 L136-137).
5. **Report subscriptions may run with the subscriber's access** — UNVERIFIED (2026-10-21): Help-only. Grounded: "Each user can subscribe to up to 5 reports" (rdapi limits).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Filter strategy recommendation | Which indexed fields to filter on, with relative date range suggestions tailored to the object |
| Report type assessment | Recommendation to keep or simplify the CRT, with rationale for any object removals |
| Extraction plan | Bulk API 2.0 query or filter-chunked report runs for result sets over 2,000 rows |
| Dashboard optimization plan | `dashboardType` decision, component count target, refresh schedule, and split recommendation |
| Performance sign-off checklist | Completed checklist confirming all criteria are met before handoff |

---

## Related Skills

- admin/reports-and-dashboards-fundamentals — for designing a report or dashboard from scratch before performance becomes a concern
- admin/data-skew-and-sharing-performance — for sharing model issues that cause slow sharing recalculations on the same large objects
- admin/sharing-and-visibility — when missing rows in a report are caused by sharing access, not query performance
