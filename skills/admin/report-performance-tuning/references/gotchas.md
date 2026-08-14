# Gotchas — Report Performance Tuning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Removing a Filter to "See All Data" Makes Performance Worse, Not Better

**What happens:** A user complains the report is slow. An admin or developer removes the date range filter to "simplify" the report or to return "all records." The report then becomes even slower — often timing out entirely — rather than returning a complete result set faster.

**When it occurs:** Any report on a large-volume object (typically more than 500K records) where the date range or owner filter is removed. The UI gives no warning that removing the filter converts a selective range scan into a full table scan.

**How to avoid:** Treat selective filters as mandatory infrastructure on large objects, not optional user preferences. Document required filters in the report description. If a user genuinely needs historical data beyond the filter window, use async Analytics API execution with a chunked date range rather than removing filters from an interactive report.

---

## Gotcha 2: The Analytics API Synchronous Endpoint Still Caps at 2,000 Rows

**What happens:** A developer queries the Analytics API using the synchronous `GET /services/data/vXX.0/analytics/reports/{reportId}` endpoint and receives a JSON response. They assume the API returns all rows. In fact, the synchronous endpoint returns the same 2,000-row display-capped result as the UI. Any row processing or aggregation built on this response silently omits data beyond row 2,000.

**When it occurs:** Any time the synchronous endpoint is used for a report with more than 2,000 detail rows. The response does not include a warning or truncation indicator in the payload; the `factMap` simply stops at 2,000 rows.

**How to avoid:** Use the async endpoint (`POST /analytics/reports/{reportId}/instances` with `includeDetails: true`) for any report where the complete row count might exceed 2,000. Poll `GET .../instances/{instanceId}` until `status` is `Success`. Validate row count in the response against an expected count from a COUNT-type report before processing.

---

## Gotcha 3: Custom Report Type Outer Joins Can Multiply Row Counts Unexpectedly

**What happens:** A custom report type is configured with "with or without" (outer join) behavior. On a large child object, this causes the report to return a row for every child record even when the parent has no match, dramatically inflating the result set. Reports that returned 10,000 rows suddenly return 500,000+ rows after a data import, causing timeouts.

**When it occurs:** CRTs with outer joins on child objects with high cardinality. A common trigger is importing a large batch of child records (e.g., a data migration of OpportunityLineItems or CaseComments) that causes a previously fast CRT-based report to suddenly time out.

**How to avoid:** Audit CRT join types when building or after any large data import. Change "with or without" joins to "with" (inner join) on high-cardinality child objects unless outer join behavior is explicitly required. Test the CRT report against production-scale data before deploying.

---

## Gotcha 4: Dashboard Refresh Frequency Is Limited to 24 Hours for Dynamic Dashboards

**What happens:** An admin schedules a dynamic dashboard to refresh every hour to give the sales team real-time pipeline data. Salesforce silently ignores the sub-24-hour schedule and refreshes only once per day. The dashboard shows stale data throughout the day, and the sales team assumes it is a bug rather than a platform limit.

**When it occurs:** Any scheduled refresh configured for a dynamic dashboard with a frequency less than 24 hours. Static dashboards have the same 24-hour minimum for scheduled refresh via the UI.

**How to avoid:** Set accurate expectations with stakeholders: scheduled dashboard refresh is for daily snapshots, not real-time data. For near-real-time needs, users must click the Refresh button manually, or the org must use CRM Analytics / Tableau CRM for streaming data scenarios. Document the refresh cadence in the dashboard description.

---

## Gotcha 5: Report Subscriptions Run at the Subscriber's Sharing Access Level

**What happens:** An admin builds a report that runs cleanly and returns 5,000 rows (via async API). When deployed as a subscription for a sales rep, the subscription delivers an email with only 200 rows — or no email at all due to a timeout. The admin debugs the report as themselves, sees full results, and concludes the report is working correctly.

**When it occurs:** Any report subscription where the subscriber's sharing access is more restrictive than the report owner's or the admin's. The subscription engine runs the report as the subscriber, applying their OWD, sharing rules, and role hierarchy access. If the subscriber's scoped data set is still large enough to time out, the subscription silently fails.

**How to avoid:** Always test subscriptions by running the report impersonating the subscriber (or by temporarily giving a test user the subscriber's permissions and checking results). If the subscriber's data volume is still too large, apply additional filters specific to the subscriber's context (e.g., Owner = Current User) or redesign the report to include a user-scoped filter.

---

## Gotcha 6: The Analytics API Refuses a 100-Column Report Outright — It Does Not Run It Slowly

**What happens:** A wide "one report to rule them all" extract accumulates columns over years of requests. Once it crosses 99 columns, the Analytics API stops running it at all: the request fails with HTTP 400 and the exact message:

```
Only a report with fewer than 100 columns can be run. The columns are fields
specified as detail columns, summaries, or custom summary formulas. Remove
unneeded columns from the report and try again.
```

This is a hard refusal, not a degradation — no partial result, no truncation, nothing to tune.

**When it occurs:** Any report at or above 100 columns run through the Analytics API, where the count sums three categories that admins rarely add together: detail columns, summaries (each Sum/Average/Max/Min toggled on a column), and custom summary formulas. A report showing 80 detail columns with Sum enabled on 25 of them is already over. Salesforce documents this as an API processing limit — "The API can process only reports that contain up to 100 fields selected as columns" — not as a report-builder allocation, so do not assume the builder blocks you before you get there.

**How to avoid:** Treat 100 as a design ceiling, not a runtime surprise, and know the builder allocations that bite before it: **20 field filters per report** in the report builder (10 in the legacy report wizard), **3 cross filters per report with up to 5 subfilters each**, and **5 custom summary formulas per report** — hard-coded and not raisable by Salesforce Support, with joined reports the one exception (10 per block, 50 per report). When an extract genuinely needs more than 100 columns, it is not a report; split it by object or pull the fields directly via Bulk API 2.0 query.

---

## Gotcha 7: Filter Logic Governs Field Filters Only — Cross Filters Are Always ANDed

**What happens:** An admin writes filter logic like `1 AND (2 OR 3)` and expects it to cover every filter on the report, including a cross filter such as "Accounts without Opportunities." The cross filter is silently excluded from the expression and applied as an unconditional AND. The report returns fewer rows than the logic implies, and the discrepancy is read as a data problem rather than a filter-scope problem.

**When it occurs:** Any report combining filter logic with a cross filter. The same exclusion applies to standard report filters — per Salesforce Help, "You can't apply filter logic to standard report filters," and "Filter logic doesn't apply to cross filters." Only the numbered field filters participate.

**How to avoid:** Before writing filter logic, confirm every condition it must cover is a field filter. Cross filters and standard filters (the date range and scope selectors at the top of the builder) cannot be made optional through logic — if an OR branch must include a cross-object condition, build separate reports or move the condition into a formula field that can be filtered as a field filter.

---

## Gotcha 8: Interactive Reports That Return More Than 50,000 Rows Cannot Be Opened

**What happens:** The report "runs" and is unopenable. Tabular dumps used as Excel substitutes hit this wall. Tabular reports also cannot feed most dashboard charts. Zero scheduled dashboard-refresh jobs (`CronTrigger` JobType 3) means every number is as stale as the last click. Subscriptions owned by deactivated users deliver to nobody.

**When it occurs:** Lead / CampaignMember / activity list-dumps; "export everything" reports.

**How to avoid:** Metric tiles and summary/matrix reports, not tabular dumps. Async Analytics API or Bulk API for extracts. Schedule dashboard refresh. Re-point subscriptions before offboarding. Do not read LastRunDate as adoption.
