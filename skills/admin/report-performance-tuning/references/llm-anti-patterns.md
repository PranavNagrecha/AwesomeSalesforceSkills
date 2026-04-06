# LLM Anti-Patterns — Report Performance Tuning

Common mistakes AI coding assistants make when generating or advising on Report Performance Tuning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising Users to Use the Synchronous Analytics API to Bypass the Row Limit

**What the LLM generates:** Instructions like "call `GET /analytics/reports/{reportId}` via the API to get all rows without the 2,000 limit."

**Why it happens:** LLMs conflate "using the API" with "bypassing UI limits." They know the row limit is a display constraint and incorrectly assume any API call bypasses it. The synchronous endpoint is the more prominently documented one, so it appears in training data more often than the async pattern.

**Correct pattern:**

```
Use the ASYNC endpoint to bypass the 2,000-row display limit:

POST /services/data/v60.0/analytics/reports/{reportId}/instances
Body: { "includeDetails": true }

Then poll:
GET /services/data/v60.0/analytics/reports/{reportId}/instances/{instanceId}

The synchronous GET /analytics/reports/{reportId} also caps at 2,000 rows
and does NOT bypass the limit.
```

**Detection hint:** Look for `GET /analytics/reports/{id}` being recommended as the solution for row-limit bypass. If the suggested solution does not include `/instances`, it will not return more than 2,000 rows.

---

## Anti-Pattern 2: Recommending Removal of Filters to "Return All Data"

**What the LLM generates:** Advice such as "remove the date filter so the report returns all records" or "if you want to see everything, clear the existing filters."

**Why it happens:** LLMs pattern-match on the general concept that fewer filters = more results and conflate data completeness with filter absence. They do not model the performance cost of full table scans on large Salesforce objects.

**Correct pattern:**

```
Never remove selective filters (date range, owner, record type) from reports
on large objects to return "all data." This causes a full table scan and leads
to timeouts.

To retrieve all records:
- Use the async Analytics API with a chunked date range filter
- Or query the object directly via SOQL Bulk API with appropriate WHERE clauses
- Provide multiple saved reports with pre-set date ranges for different windows
```

**Detection hint:** Any recommendation containing "remove the filter" or "clear the filters" on a large-volume object report should be flagged and reviewed.

---

## Anti-Pattern 3: Suggesting "Run as Specified User" on Dynamic Dashboards as a Performance Fix

**What the LLM generates:** A recommendation to switch a dynamic dashboard from "run as logged-in user" to "run as specified user" to make refreshes faster, on the basis that a single cached query is faster than per-user queries.

**Why it happens:** LLMs correctly know that "run as specified user" caches a single query result rather than generating per-user results, and they interpret this as a performance improvement. They do not surface the security implication: all viewers then see the specified user's data slice, which typically has broader access than individual viewers should have.

**Correct pattern:**

```
"Run as specified user" on a dynamic dashboard is a security decision, not a
performance optimization.

Correct performance fixes for slow dynamic dashboards:
- Add selective filters to the underlying report components
- Reduce total component count (aim for 20 or fewer per dashboard)
- Schedule refreshes during off-peak hours
- Split into multiple focused dashboards

Do not use "run as specified user" unless the data scope is intentionally shared
and the security implications are understood and accepted.
```

**Detection hint:** Any recommendation to change the dashboard running user as a performance fix should be reviewed for security impact before implementation.

---

## Anti-Pattern 4: Claiming CRM Analytics and Standard Reports Share the Same Row Limits

**What the LLM generates:** An explanation that applies the 2,000-row display limit from standard reports to CRM Analytics (Tableau CRM) dashboards and datasets, or vice versa.

**Why it happens:** LLMs conflate the two reporting systems, which share some Salesforce branding but have different architectures, limits, and performance models. CRM Analytics uses its own query engine (SAQL/SOQL) and has different limits than the standard Reports & Dashboards engine.

**Correct pattern:**

```
Standard Reports & Dashboards (this skill):
- 2,000 row display limit in UI
- Analytics API async endpoint for full results
- Performance governed by SOQL query optimizer and index selectivity

CRM Analytics / Tableau CRM (separate skill):
- Different query engine (SAQL)
- Different dataset size limits
- Different performance optimization patterns

Do not apply standard report performance guidance to CRM Analytics datasets
or vice versa.
```

**Detection hint:** If a response discusses "report performance" but references SAQL, datasets, or lenses without explicitly scoping to CRM Analytics, the boundary may be blurred.

---

## Anti-Pattern 5: Treating Report Subscription Failures as a Report Design Problem Without Checking Subscriber Access

**What the LLM generates:** When a subscription is not delivering email, advice to rebuild the report, add more filters, or check the subscription schedule — without investigating whether the failure is caused by the report timing out at the subscriber's sharing access level.

**Why it happens:** LLMs default to diagnosing the report itself (the more commonly documented failure mode) and do not model the execution context: subscriptions run as the subscriber, not the report owner or admin. They miss that debugging as the admin shows a passing report, masking the real failure.

**Correct pattern:**

```
When a report subscription is not delivering:

1. Test the report by impersonating the subscriber (or a user with equivalent access)
   - Setup > User Management > Login as [user] (if enabled)
   - Or: create a test user with the subscriber's profile/permission sets

2. If the report times out for the subscriber but not the admin:
   - The subscriber's data volume is too large for the report's current filter set
   - Add an Owner = Current User filter or a tighter date range
   - Do not remove filters tested only as admin

3. Only investigate subscription schedule after confirming the report runs cleanly
   as the subscriber.
```

**Detection hint:** If subscription debugging advice does not include testing as the subscriber specifically, it is incomplete. Look for absent language around "run as subscriber" or "impersonate user."

---

## Anti-Pattern 6: Recommending Export via Report UI for Compliance or Integration Use Cases

**What the LLM generates:** Instructions to download a report as CSV from the Lightning Report UI for use in compliance exports, system integrations, or data reconciliation processes.

**Why it happens:** The UI export is the most visible and intuitive export path. LLMs recommend it because it is well-documented and matches the surface-level request ("export the report data"). They do not track the 2,000-row truncation risk or that the export gives no indication when truncation occurs.

**Correct pattern:**

```
For any export used in compliance, integration, or audit contexts:
- Use Analytics API async execution (POST .../instances with includeDetails: true)
- Validate row count against a COUNT() summary report before processing
- Never rely on UI CSV export for datasets that may exceed 2,000 rows

The UI export provides no warning when it truncates at 2,000 rows.
A 50,000-row compliance export downloaded via the UI silently contains only 4% of the data.
```

**Detection hint:** Recommendations to "export as CSV from the report" for integration or compliance use cases without mention of the 2,000-row cap should be flagged.
