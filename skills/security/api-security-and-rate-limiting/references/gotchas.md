# Gotchas — API Security and Rate Limiting

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Refresh Tokens Bypass IP Restrictions at Token Exchange

**What happens:** When a Connected App's IP Relaxation is set to "Relax IP restrictions," the refresh token can be exchanged for a new access token from any source IP — not just the authorized IP ranges. The new access token is then valid for its full session duration. This means IP restrictions configured on the Connected App profile do not protect against use of a stolen refresh token if the relaxation policy is too permissive.

**When it occurs:** Affects any Connected App that stores refresh tokens (i.e., headless integrations using `refresh_token offline_access` scope) when the IP Relaxation setting is not set to "Enforce login IP ranges on every request."

**How to avoid:** For all server-to-server integrations, set IP Relaxation to "Enforce login IP ranges on every request." Test this by attempting a token refresh from an unauthorized IP — the request should be rejected. Additionally, configure IP ranges at the Connected App level (not just at the user profile level), as Connected App IP ranges are checked independently.

---

## Gotcha 2: Bulk API Daily Limit Is Measured in Records, Not Requests

**What happens:** Teams managing Salesforce API consumption often monitor "daily API calls" from Setup → API Usage Metrics. Bulk API usage does not appear in this metric because Bulk API has a separate daily limit measured in total records processed across all jobs, not in request count. An org can exhaust its Bulk API record limit while the REST/SOAP call counter still shows capacity, or vice versa.

**When it occurs:** Any org running high-volume Bulk API jobs (nightly ETL, data migrations, large-scale updates) alongside other API-heavy integrations. The daily Bulk API 2.0 limit is up to 150 million records per org for orgs with appropriate editions and add-ons; Bulk API 1.0 limit is lower.

**How to avoid:** Monitor Bulk API consumption separately. Check Setup → Company Information → Bulk API Daily Requests (for Bulk API 1.0) and the Bulk API 2.0 usage endpoint. When investigating limit exhaustion, always check both the REST/SOAP daily call counter and the Bulk API record counter before concluding which limit was hit.

---

## Gotcha 3: HTTP 429 and REQUEST_LIMIT_EXCEEDED Are Not the Same Condition

**What happens:** Integrations that handle 429 with exponential backoff and retry sometimes loop indefinitely because the underlying condition is not a momentary rate limit but a fully exhausted daily allocation. A `REQUEST_LIMIT_EXCEEDED` error (which Salesforce may return as a 403 with a SOAP fault body or as a structured error in a REST response body) means the daily limit is gone — retrying any number of times in the same 24-hour window will not succeed.

**When it occurs:** When an org hits its daily REST/SOAP API limit, subsequent requests return a `REQUEST_LIMIT_EXCEEDED` error. Integrations built to retry on any non-200 response (or that inspect only HTTP status code without reading the error body) may not distinguish 429 (transient throttle) from limit exhaustion (terminal for the day).

**How to avoid:** Parse the error body of non-200 responses. A 429 carries a `Retry-After` header. A `REQUEST_LIMIT_EXCEEDED` error carries a specific error code in the JSON or SOAP body. When the error is `REQUEST_LIMIT_EXCEEDED`, fail fast, emit an alert, and do not retry until the rolling 24-hour window resets. Use exponential backoff only for 429 responses.

---

## Gotcha 4: The Concurrent API Limit Applies Only to Requests Running Longer Than 20 Seconds

**What happens:** Teams experiencing concurrent limit errors often assume any high request volume will trigger it. In fact, Salesforce's concurrent request limit (25 long-running requests per org as of Spring '25) only counts requests that have been running for more than 20 seconds. Short-lived requests — even thousands per minute — do not consume the concurrent limit.

**When it occurs:** Concurrent limit errors surface when an integration sends queries or DML operations that take more than 20 seconds to complete, and more than 25 such operations are in flight simultaneously. This commonly occurs with complex SOQL queries over large datasets, callout-heavy Apex triggers invoked via API, or SOAP operations that trigger expensive automation.

**How to avoid:** Optimize slow queries and automation to reduce server-side execution time below 20 seconds where possible. For unavoidably long operations, serialize rather than parallelize those specific calls. Use Bulk API for high-volume operations that exceed 20-second execution times. Monitor for `EXCEEDED_ID_LIMIT` or `SERVER_UNAVAILABLE` errors in SOAP, or HTTP 503 with a concurrent-limit body in REST.

---

## Gotcha 5: Event Log Files Have a One-Day Lag and Cannot Be Used for Real-Time Incident Response

**What happens:** When an API limit incident occurs, teams immediately query `EventLogFile` looking for the current day's API calls to identify the offending consumer. They find no records or only yesterday's data. Event Log Files are generated once daily (typically in the early hours UTC) and cover the previous calendar day. There is no real-time ELF stream.

**When it occurs:** Any time a team needs to investigate an API limit spike that is happening now or happened in the last few hours. The ELF for today's events will not be available until tomorrow.

**How to avoid:** For real-time investigation, use Setup → API Usage Metrics (coarse-grained, available immediately) and connected app OAuth token counts in Setup → Connected Apps OAuth Usage (shows which apps hold active tokens and their last-used time). For forward-looking real-time monitoring, consider streaming EventLogFile data via the Pub/Sub API (Shield Event Monitoring) or integrating with a SIEM that can ingest Salesforce data in near-real-time. ELF analysis is best suited for post-incident review, not live triage.

---

## Gotcha 6: Connected App Session Timeout Does Not Override Org-Wide Session Timeout

**What happens:** An admin sets a long session timeout (e.g., 24 hours) on a Connected App to support a long-running batch integration, expecting API calls to remain valid for 24 hours. The org-wide Session Settings have a shorter timeout (e.g., 2 hours). The integration session expires at 2 hours, not 24 hours. The Connected App session timeout is a ceiling, not an override — the effective session duration is the minimum of the Connected App timeout and the org-wide timeout.

**When it occurs:** Any org where the Connected App session timeout exceeds the org-wide session setting. This is common when the org-wide timeout is tightened for security reasons after the Connected App was initially configured.

**How to avoid:** When configuring session timeout for API integrations, check both the Connected App's OAuth Policies → Session Timeout value and the org-wide Setup → Session Settings → Timeout Value. The effective timeout is the shorter of the two. For long-running integrations, either raise the org-wide timeout for API sessions specifically (Salesforce allows session-level timeout settings based on session security level) or implement re-authentication logic in the integration before the shorter timeout is reached.
