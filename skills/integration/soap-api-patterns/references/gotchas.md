# Gotchas — SOAP API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enterprise WSDL Becomes Stale on Schema Changes

**What happens:** After a custom field or custom object is added to the Salesforce org, SOAP calls using the old enterprise WSDL stubs silently omit the new field. No error is thrown — the field is simply not present in the generated class, so the client never sends it and the response never populates it.

**When it occurs:** Any time the org's schema changes after the last enterprise WSDL generation: new custom fields, renamed fields, new custom objects, or changed picklist values. This is especially common in orgs under active development where admins add fields between release cycles.

**How to avoid:** Establish a CI/CD gate that regenerates enterprise WSDL stubs whenever the Salesforce org schema is released to production. Track the WSDL file in version control and diff it on each deployment. For ISV or multi-org use cases, switch to the partner WSDL to eliminate the regeneration dependency entirely.

---

## Gotcha 2: `serverUrl` from LoginResult Must Be Used — Not the Login Endpoint

**What happens:** Calls made to the login endpoint (`login.salesforce.com` or `test.salesforce.com`) after authentication fail or return incorrect data. This manifests as `SOAP:Server` faults, connection refused errors, or data visible in one context but not another.

**When it occurs:** Any org hosted on a non-`na1` instance (all EU/APAC/Hyperforce orgs, most sandbox instances, and increasingly most production orgs). The login endpoint is a routing layer; actual data lives on a specific instance. Using the login URL for post-authentication calls bypasses instance routing and targets the wrong host.

**How to avoid:** After every `login()` call, immediately update the SOAP binding's URL to `LoginResult.serverUrl`. For WSC-based Java clients, `ConnectorConfig.getServiceEndpoint()` is automatically set after login — use it as the source of truth. Never hardcode `na1.salesforce.com`, `login.salesforce.com`, or any static instance host in the SOAP endpoint configuration.

---

## Gotcha 3: Session Expiry Invalidates `queryLocator` Mid-Pagination

**What happens:** A `query()` + `queryMore()` loop that runs longer than the org's session timeout receives an `INVALID_SESSION_ID` fault on a subsequent `queryMore()` call. The entire query must be restarted from scratch — there is no way to resume a paginated query across a session boundary with a new session.

**When it occurs:** Orgs with short session timeouts (15–30 minutes, common in high-security orgs) combined with large query results or slow processing between pages. Also occurs when a session is explicitly invalidated by a security policy (e.g., same-user concurrent login limit).

**How to avoid:** Set a generous session timeout for integration users in Setup > Session Settings, or divide large queries into time-bounded slices (e.g., `WHERE CreatedDate >= :startDate AND CreatedDate < :endDate`) that complete within a single session window. Implement a retry wrapper that catches `INVALID_SESSION_ID`, re-authenticates, and re-executes the full query. Never assume a `queryLocator` remains valid across a re-authentication.

---

## Gotcha 4: Security Token Must Be Appended to Password — No Separator

**What happens:** The `login()` call fails with `LOGIN_MUST_USE_SECURITY_TOKEN` even though a valid token is provided. Alternatively, the call returns `INVALID_PASSWORD` when the token is being passed correctly but in the wrong position.

**When it occurs:** When the user's IP address is not in the org's trusted IP ranges, Salesforce requires the security token to be appended to the password string. The token must be concatenated directly to the end of the password with no space, delimiter, or separator character (e.g., if password is `tiger123` and token is `ABCXYZ`, the password field must contain `tiger123ABCXYZ`).

**How to avoid:** Build the password string as `password + securityToken` in code, sourcing both from environment variables or a secrets manager. Never store the combined string in config files. Document this concatenation in your integration's runbook — it surprises every developer who encounters it for the first time.

---

## Gotcha 5: SOAP DML Has No All-or-None Semantics by Default

**What happens:** A `create()` or `update()` call with 200 records partially succeeds. Some records save; others fail with validation errors. The SOAP call does not throw a fault — it returns HTTP 200 with a `SaveResult[]` response where some entries have `success=false`. Integrations that only check for exceptions silently discard failed records with no data loss alert.

**When it occurs:** Whenever any record in the batch triggers a required-field check, validation rule, duplicate rule, or field-level permission error. This is common in integrations that process data from external systems where field values cannot be fully validated client-side.

**How to avoid:** Always iterate over every `SaveResult` or `UpsertResult` in the response. Route failed records to a dead-letter queue or retry table rather than discarding them. Alert on batch failure rates above a threshold. If the business requirement is truly all-or-none, call records one at a time (accepting higher API call counts) or switch to REST Composite with `allOrNone: true`.

---

## Gotcha 6: Retired API Versions Return `UNSUPPORTED_API_VERSION` at Runtime

**What happens:** SOAP calls return a `500 UNSUPPORTED_API_VERSION` fault with no other explanation. The integration worked for years and then started failing after a Salesforce release.

**When it occurs:** Salesforce periodically retires old API versions (typically versions below v21.0 as of recent announcements, with ongoing deprecation of older versions). Integrations that have not been updated in years and are pinned to old endpoint URLs hit this error after retirement.

**How to avoid:** Pin endpoint URLs to API version v56.0 or later and audit SOAP endpoint URLs during annual integration reviews. Monitor the Salesforce release notes for API version retirement announcements. Treat the API version as a first-class dependency in your integration's configuration, not a buried constant.
