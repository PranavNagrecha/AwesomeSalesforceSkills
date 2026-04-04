# Gotchas — REST API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Outer HTTP 200 Does Not Mean All Composite Subrequests Succeeded

**What happens:** A POST to `/composite/` or `/composite/batch/` returns HTTP 200 for the outer response envelope even when individual subrequests failed with 4xx status codes. Integrations that stop at the outer status code silently discard errors and may assume records were written when they were not.

**When it occurs:** Any time you use the Composite or Composite Batch resources and do not iterate over `compositeResponse` entries to inspect per-subrequest `httpStatusCode`.

**How to avoid:** Always iterate over every entry in `compositeResponse` and treat any `httpStatusCode` ≥ 400 as an error requiring handling. Log the `referenceId`, status, and body. When `allOrNone: true` is set, a single 4xx subrequest triggers a full rollback — but you still need to read the response to identify which subrequest triggered the rollback.

---

## Gotcha 2: `nextRecordsUrl` Is a Path, Not a Full URL

**What happens:** The `nextRecordsUrl` value returned in paginated SOQL query responses is a relative path (e.g., `/services/data/v63.0/query/01gXXX-2000`), not a complete URL. Clients that use this value as-is (without prepending the instance hostname) get a connection error or an incorrect request to the wrong host. Clients that try to reconstruct a query locator URL from scratch get a 404.

**When it occurs:** Whenever a SOQL query returns `"done": false`, which happens for any result set with more records than the batch size (default 2,000).

**How to avoid:** Always prepend the org's instance URL (e.g., `https://myorg.salesforce.com`) to `nextRecordsUrl` before issuing the next GET. Store the instance URL at authentication time from the OAuth token response (`instance_url` field) and reuse it for the duration of the pagination loop. Never reconstruct the query locator manually.

---

## Gotcha 3: API Version Deprecation Causes Silent Breakage at Retirement

**What happens:** Salesforce retires REST API versions periodically. Integrations pinned to a retired version stop receiving responses for that version's endpoint path. The platform does not warn at runtime before retirement — calls simply fail after the retirement date.

**When it occurs:** When an integration was built against an old API version (roughly v20.0–v40.0 range as of 2025) and has never been updated. Salesforce publishes retirement timelines in release notes, but integrations running without active monitoring miss the announcements.

**How to avoid:** Pin to a version within the last four Salesforce releases (e.g., v60.0+). Track the REST API version in configuration (not hard-coded deep in integration code) so it can be bumped without a full redeploy. Subscribe to Salesforce API deprecation announcements in release notes.

---

## Gotcha 4: Concurrent Long-Running Request Limit Is Independent of Daily Limit

**What happens:** Salesforce enforces a limit of 25 concurrent API requests that run longer than 20 seconds per org (the "long-running" concurrent limit). Polling integrations or batch scripts that hold many open REST calls simultaneously hit this ceiling before touching the daily API limit. Requests exceeding the concurrent limit receive HTTP 503 or `REQUEST_LIMIT_EXCEEDED`.

**When it occurs:** High-frequency polling loops, parallel export jobs, or integrations that issue many SOQL queries simultaneously and wait for large result sets can exhaust the concurrent limit while the daily limit still appears healthy.

**How to avoid:** Implement request throttling and back-off in the integration client. Prefer async patterns (Platform Events, Change Data Capture) for high-frequency polling scenarios. Monitor `REQUEST_LIMIT_EXCEEDED` errors separately from daily limit metrics.

---

## Gotcha 5: 429 Rate Limiting Returns a `Retry-After` Header

**What happens:** When an integration exceeds the rate at which Salesforce accepts requests, the API returns HTTP 429 with a `Retry-After` header indicating how many seconds to wait. Integrations that retry immediately without reading `Retry-After` enter a hammering loop that extends the throttling period and may trigger additional protective measures.

**When it occurs:** High-volume REST integrations during peak load periods or during Salesforce maintenance windows when the effective limits are reduced.

**How to avoid:** Implement exponential back-off with jitter as the baseline retry strategy. On receipt of HTTP 429, read `Retry-After` and wait at least that many seconds before retrying. Cap total retry attempts to avoid indefinite retry storms.

---

## Gotcha 6: PATCH on a Non-Existent Record ID Returns 404, Not an Upsert

**What happens:** `PATCH /sobjects/{SObject}/{id}` updates a record if it exists. If the provided Salesforce record ID does not exist (deleted, wrong ID), the API returns HTTP 404. This surprises integrations that expect PATCH to behave as upsert.

**When it occurs:** When an integration caches Salesforce IDs and uses them for PATCH updates without validating that the records still exist. Common after org refreshes, data cleanup scripts, or record merges.

**How to avoid:** Use External ID upsert (`PATCH /sobjects/{SObject}/{ExternalIdField}/{value}`) when the create-or-update semantic is required. If using Salesforce IDs directly, add 404 handling that falls back to a POST create or re-queries for the current ID.
