# Gotchas — Data Cloud Query API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Two-Step Token Exchange Is Mandatory

**What happens:** Calls to the Query API with a standard Salesforce OAuth2 access token return 401 Unauthorized, even though the token is valid for other Salesforce APIs.

**When it occurs:** Any time a developer reuses a token from `/services/oauth2/token` directly for Data Cloud API calls without first exchanging it at `/services/a360/token`.

**How to avoid:** Always perform the two-step token flow. First obtain a standard Salesforce token, then POST it to `/services/a360/token` with the Data Cloud grant type. Cache the resulting `dc_access_token` and `dcInstanceUrl` separately from the standard token.

---

## Gotcha 2: Cursor Expires Silently After 3-Minute Gap

**What happens:** A follow-up GET to `/api/v2/query/{nextBatchId}` returns 404 or an error with no indication that the cursor expired — it looks like a missing resource.

**When it occurs:** When more than 3 minutes elapse between pagination requests. This commonly happens when downstream processing (e.g., database inserts) is too slow and the paginator waits for processing to complete before fetching the next page.

**How to avoid:** Separate fetching from processing. Fetch all pages into memory first (or a fast buffer), then process. Alternatively, use the Query Connect API which extends result availability to 24 hours and is designed for large exports.

---

## Gotcha 3: Calculated Insights Return Empty with No Error Before Publication

**What happens:** A SQL query against a Calculated Insight returns zero rows and an HTTP 200, with no indication that the CI is unpublished.

**When it occurs:** When querying a CI that exists in the schema but has never been published, or whose last batch run failed.

**How to avoid:** Before querying a CI, verify in Data Cloud Setup > Calculated Insights that the status is Published and the last run shows success. Add a pre-flight check to your pipeline that queries the CI metadata API.

---

## Gotcha 4: ANSI SQL Object Names Are Case-Sensitive and Namespace-Qualified

**What happens:** A query like `SELECT Id FROM Individual LIMIT 10` returns an error — the table is not found.

**When it occurs:** When developers use informal names or omit the namespace prefix and DLM suffix (e.g., `ssot__Individual__dlm` is correct; `Individual` is not recognized).

**How to avoid:** Use Data Cloud Setup > Data Model Explorer to look up the exact API name for every DMO, DLO, or Calculated Insight before writing queries. Include the full namespace and suffix in all SQL statements.

---

## Gotcha 5: dcInstanceUrl Is Not Always the Same as instance_url

**What happens:** All Data Cloud API calls return 404 despite valid authentication.

**When it occurs:** When `instance_url` from the standard token is used as the base URL instead of `dcInstanceUrl` from the Data Cloud token exchange response. In many orgs these URLs differ — `dcInstanceUrl` points to a Data Cloud-specific subdomain.

**How to avoid:** Always parse `dcInstanceUrl` from the `/services/a360/token` response and use it exclusively for all Data Cloud endpoints. Log and store it separately from the standard `instance_url`.
