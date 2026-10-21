# Gotchas — Report Performance Tuning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. `rdapi limits` / `rdapi run` / `rdapi error codes` are the Reports and Dashboards REST API Developer Guide 262 pages "Requirements and Limitations", "Run Reports Synchronously or Asynchronously" and "Report Error Codes" (developer.salesforce.com, not in the corpus files).

## Gotcha 1: Removing a Filter to "See All Data" Makes Performance Worse, Not Better

**What happens:** A user complains the report is slow. An admin removes the date range filter to "simplify" the report or to return "all records." The report then becomes even slower — often timing out entirely — rather than returning a complete result set faster.

**When it occurs:** Any report on a large-volume object where the date range or owner filter is removed. Without a selective, indexed filter "the query optimizer must perform a full scan to fetch the target rows" (ldv 264 L305-307).

**How to avoid:** Treat selective filters as mandatory infrastructure on large objects, not optional user preferences. Document required filters in the report description. If a user genuinely needs historical data beyond the filter window, use a Bulk API 2.0 query (api_asynch 264 L136-137) or a set of filter-windowed report runs that each return fewer than 2,000 rows — never an unfiltered interactive report.

---

## Gotcha 2: The Analytics API Returns Only the First 2,000 Rows — Synchronous and Asynchronous Alike

**What happens:** A developer calls the Reports and Dashboards REST API expecting all rows. "The API returns up to the first 2,000 report rows. You can narrow results using filters" (rdapi limits; the same sentence for the Apex flavour, apexdev 264 L33689), and "the API returns data for the same number of records that are available when the report is run in the Salesforce user interface" (rdapi run). Switching to the async `POST /analytics/reports/{reportId}/instances` endpoint does not change that. Any processing built on the response silently omits data beyond row 2,000.

**When it occurs:** Any API run of a report with more than 2,000 detail rows, sync or async. Earlier versions of this skill told readers that the async endpoint bypasses the cap — it does not.

**How to avoid:** For complete extracts, use a Bulk API 2.0 query job (api_asynch 264 L136-137). If it must be a report, split the run into filter windows that each return fewer than 2,000 rows. Use async for what it is documented to do: avoid the 2-minute API timeout and keep results for a 24-hour rolling period (rdapi run). Poll the instance until `status` is `Success` or `Error` (`New` and `Running` are the in-flight values; Instances List, rdapi 262).

---

## Gotcha 3: Custom Report Type Outer Joins Can Multiply Row Counts Unexpectedly

**What happens:** A custom report type is configured with "with or without" (outer join) behavior. "An outer join returns a row even if the joined table doesn't contain a matching value in the join column" (api_meta 264 L108493-108495), so the result set grows with unmatched rows. UNVERIFIED (2026-10-21): the "10,000 to 500,000+ rows after an import" illustration.

**When it occurs:** CRTs with outer joins on child objects with high cardinality. When more than two objects are joined, "an inner join isn't allowed if there has been an outer join earlier in the join sequence" (api_meta 264 L108487-108489), so one outer join constrains every later join.

**How to avoid:** Audit CRT join types (`outerJoin` on each `ObjectRelationship`) when building or after any large data import. Use inner joins on high-cardinality child objects unless outer join behavior is explicitly required. Test the CRT report against production-scale data before deploying.

---

## Gotcha 4: Scheduled Dashboard Refresh Limits Are Help-Only (UNVERIFIED)

**What happens:** UNVERIFIED (2026-10-21): the claim this skill carried — that a dynamic dashboard scheduled more often than every 24 hours refreshes only once a day — is not in any corpus guide. Grounded facts: scheduled dashboard refreshes are `CronJobDetail.JobType` `3` — Dashboard Refresh (obj 264 L86824, L86850); the REST API allows "up to 200 dashboard refreshes per hour" (rdapi limits); `dashboardType` `LoggedInUser` means each user sees data by their own access (api_meta 264 L50170-50186).

**When it occurs:** Stakeholders expect near-real-time numbers from a scheduled dashboard.

**How to avoid:** Confirm the org's scheduling options in Setup before promising a cadence. For near-real-time needs, users click Refresh, or the use case moves to a different tool. Document the refresh cadence in the dashboard description.

---

## Gotcha 5: Report Subscriptions and the Subscriber's Sharing Access (UNVERIFIED)

**What happens:** An admin builds a report that runs cleanly as themselves. Delivered as a subscription to a sales rep, it returns fewer rows or fails. UNVERIFIED (2026-10-21): that the subscription engine runs the report as the subscriber with their sharing access — Help-only. Grounded: "Each user can subscribe to up to 5 reports" (rdapi limits).

**When it occurs:** Any report subscription where the subscriber's access differs from the admin's.

**How to avoid:** Test subscriptions by running the report as a user with the subscriber's access. If the subscriber's data volume is still too large, apply filters specific to the subscriber's context (e.g. an owner scope such as `MyAccounts`, api_meta 264 L106822-106829) or redesign the report.

---

## Gotcha 6: The Analytics API Refuses a 100-Column Report Outright — It Does Not Run It Slowly

**What happens:** A wide "one report to rule them all" extract accumulates columns over years of requests. Once it reaches 100 columns, the Analytics API stops running it at all: the request fails with HTTP 400 and the exact message (rdapi error codes):

```
Only a report with fewer than 100 columns can be run. The columns are fields
specified as detail columns, summaries, or custom summary formulas. Remove
unneeded columns from the report and try again.
```

This is a hard refusal, not a degradation — no partial result, no truncation, nothing to tune.

**When it occurs:** Any report at or above 100 columns run through the Analytics API, where the count sums detail columns, summaries and custom summary formulas. "The API can process only reports that contain up to 100 fields selected as columns" (rdapi limits; apexdev 264 L33681). The two sources pull different ways at exactly 100 — the limits page says "up to 100", the error text says "fewer than 100" — so design for 99 or fewer.

**How to avoid:** Treat 100 as a design ceiling. The API also accepts "up to 20 custom field filters when you run a report" (rdapi limits). UNVERIFIED (2026-10-21): the report-builder allocations this skill lists — 20 field filters (10 in the legacy wizard), 3 cross filters, 5 custom summary formulas (joined reports 10 per block, 50 per report) — are Help-only. Grounded: each cross filter takes "up to five subfilters" (`ReportCrossFilter.criteriaItems`, api_meta 264 L107813-107814). When an extract genuinely needs more than 100 columns, it is not a report; pull the fields directly via a Bulk API 2.0 query.

---

## Gotcha 7: Filter Logic Governs Field Filters Only — Cross Filters Are Always ANDed (UNVERIFIED)

**What happens:** An admin writes filter logic like `1 AND (2 OR 3)` and expects it to cover a cross filter such as "Accounts without Opportunities." UNVERIFIED (2026-10-21): that the cross filter is applied as an unconditional AND — the quoted Help lines ("You can't apply filter logic to standard report filters", "Filter logic doesn't apply to cross filters") are not in the corpus. Consistent with them, Report metadata keeps filter logic in `ReportFilter.booleanFilter` (api_meta 264 L107292-107296) and cross filters in the separate `Report.crossFilters` list (L106680; marked API 68.0 and later at L106682, though the cross-filter sample says it was generated at API 23.0, L107853), and the REST API notes that "Cross filters, standard report filters, and filtering by row limit are unavailable when filtering data" (rdapi limits; apexdev 264 L33671).

**When it occurs:** Any report combining filter logic with a cross filter.

**How to avoid:** Before writing filter logic, confirm every condition it must cover is a field filter. If an OR branch must include a cross-object condition, build separate reports or move the condition into a formula field that can be filtered as a field filter.

---

## Gotcha 8: Huge Tabular Dumps and Unscheduled Dashboards

**What happens:** UNVERIFIED (2026-10-21): that an interactive report returning more than 50,000 rows cannot be opened, and that tabular reports cannot feed most dashboard charts — Help-only. Grounded: a scheduled dashboard refresh is a `CronJobDetail` with `JobType` `3` (Dashboard Refresh) — `JobType` is a `CronJobDetail` field (obj 264 L86824, L86850), reached from `CronTrigger.CronJobDetailId` (obj 264 L86903); zero such jobs means every number is as stale as the last click.

**When it occurs:** Lead / CampaignMember / activity list-dumps; "export everything" reports.

**How to avoid:** Metric tiles and summary/matrix reports, not tabular dumps. Bulk API 2.0 for extracts. Schedule dashboard refresh (`SELECT Id FROM CronTrigger WHERE CronJobDetail.JobType = '3'` to audit). Re-point subscriptions before offboarding (UNVERIFIED (2026-10-21): what happens to a departed user's subscriptions is Help-only). Do not read LastRunDate as adoption.
