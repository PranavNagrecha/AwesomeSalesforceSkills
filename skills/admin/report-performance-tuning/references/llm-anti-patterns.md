# LLM Anti-Patterns — Report Performance Tuning

Common mistakes AI coding assistants make when generating or advising on Report Performance Tuning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising Users to Use the Analytics API (Sync or Async) to Bypass the Row Limit

**What the LLM generates:** Instructions like "call `GET /analytics/reports/{reportId}` via the API to get all rows without the 2,000 limit", or "use the async `/instances` endpoint to bypass the 2,000-row display limit".

**Why it happens:** LLMs conflate "using the API" with "bypassing UI limits", and async with "bigger". Earlier versions of this very skill made the async claim.

**Correct pattern:**

```
Neither endpoint returns more than 2,000 rows:
"The API returns up to the first 2,000 report rows. You can narrow
results using filters." (Reports and Dashboards REST API 262,
Requirements and Limitations; same sentence in apexdev 264 L33689)

Async (POST .../analytics/reports/{reportId}/instances, then poll
GET .../instances/{instanceId} until status is Success or Error) is for
long runs: no 2-minute API timeout, results kept 24 hours (Run Reports
Synchronously or Asynchronously, same guide).

For every row: a Bulk API 2.0 query job on the object
(api_asynch 264 L136-137), or filter windows that each return
fewer than 2,000 rows.
```

**Detection hint:** Any sentence that says an Analytics API endpoint — sync or `/instances` — returns "all rows" or "bypasses" the 2,000-row limit.

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
- Query the object directly with a Bulk API 2.0 query job (api_asynch 264 L136-137)
- Or run the report in date-range chunks that each return fewer than 2,000 rows
- Provide multiple saved reports with pre-set date ranges for different windows
```

**Detection hint:** Any recommendation containing "remove the filter" or "clear the filters" on a large-volume object report should be flagged and reviewed.

---

## Anti-Pattern 3: Suggesting "Run as Specified User" on Dynamic Dashboards as a Performance Fix

**What the LLM generates:** A recommendation to switch a dynamic dashboard from "run as logged-in user" to "run as specified user" to make refreshes faster, on the basis that a single cached query is faster than per-user queries.

**Why it happens:** LLMs assume that "run as specified user" computes one result instead of per-user results (UNVERIFIED (2026-10-21) as a performance claim), and treat that as an optimization. They do not surface the security implication: with `dashboardType` `SpecifiedUser`, "All users see data at the access level of one specific running user ... regardless of their own security settings" (api_meta 264 L50170-50174).

**Correct pattern:**

```
"Run as specified user" on a dynamic dashboard is a security decision, not a
performance optimization.

Correct performance fixes for slow dynamic dashboards:
- Add selective filters to the underlying report components
- Reduce total component count (the "20 or fewer" target is Help-only, UNVERIFIED)
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
- The REST API returns up to the first 2,000 report rows, sync or async
- Bulk API 2.0 query for full extracts
- Performance governed by the query optimizer and index selectivity
  (ldv 264 L225-226)

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

**Why it happens:** LLMs default to diagnosing the report itself and do not model the execution context. UNVERIFIED (2026-10-21): that subscriptions run as the subscriber rather than the report owner — Help-only; test with the subscriber's access either way, because debugging as the admin can mask the real failure.

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

**Why it happens:** The UI export is the most visible and intuitive export path, and it matches the surface-level request ("export the report data"). UNVERIFIED (2026-10-21): whether a UI export truncates at 2,000 rows — Help-only; the earlier "4% of a 50,000-row export" figure depended on it.

**Correct pattern:**

```
For any export used in compliance, integration, or audit contexts:
- Use a Bulk API 2.0 query job on the object (api_asynch 264 L136-137)
- Do NOT use the Analytics API for it: sync and async both return only
  the first 2,000 report rows (REST API 262, Requirements and Limitations)
- Validate the row count against a COUNT() query before processing
```

**Detection hint:** Recommendations to "export as CSV from the report" or to "use the async Analytics API" for complete integration or compliance extracts should be flagged.

---

## Anti-Pattern 7: Specifying Reports That Exceed the Structural Caps on Columns and Filters

**What the LLM generates:** A "data extract" report spec listing 120+ fields as columns, or a filter design with 30 numbered filters, or filter logic written as `1 AND (2 OR 3)` where condition 3 is a cross filter. None of the caps are mentioned, because the model treats the report builder as an unbounded query surface.

**Why it happens:** LLMs model reports as SOQL with a UI attached, and SOQL has no comparable column or filter ceiling. Report performance guidance in training data is dominated by "add selective filters" advice, so the failure mode the model has learned to predict is *slow*, not *rejected*. It has no representation of a report that simply refuses to run.

**Correct pattern:**

```
Report builder allocations (Help-only, UNVERIFIED 2026-10-21), to check
before proposing any report spec:

  Field filters           20      (10 in the legacy report wizard)
  Cross filters           3       (up to 5 subfilters each — the 5 is
                                   grounded: api_meta 264 L107813-107814)
  Summary formulas        5       (hard-coded; joined reports get 10 per
                                   block, 50 per report)

Analytics API processing limit — a separate cap from the allocations above:

  Columns per report      < 100   (detail columns + summaries + custom
                                   summary formulas, counted together)

Exceeding the column cap is a hard refusal at run time, not slowness: the
API returns HTTP 400 "Only a report with fewer than 100 columns can be
run." (The limits page says "up to 100", apexdev 264 L33681 — the sources
disagree at exactly 100; stay at 99 or fewer.) For a >100-column extract, do not propose a report at all — use
Bulk API 2.0 query against the object directly.

See gotchas.md Gotcha 6 for the full error text, and Gotcha 7 for filter
logic and cross filters (that filter logic never covers a cross filter is
UNVERIFIED 2026-10-21, Help-only).
```

**Detection hint:** Count the columns in any generated report spec. If the response proposes a wide extract (100 or more columns), it is describing a report the Analytics API will refuse to run. Filter logic that references a cross filter by number is suspect too (UNVERIFIED, see Gotcha 7), but no corpus line says the API refuses it.
