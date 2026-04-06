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
