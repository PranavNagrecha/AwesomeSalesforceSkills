# Well-Architected Notes — SOAP API Patterns

## Relevant Pillars

### Reliability

SOAP integrations are reliability-critical because failures are often silent. Partial DML success, stale session IDs mid-batch, and ignored `queryMore()` pagination all cause data loss without raising alerts. Reliability guidance:

- Implement per-record result inspection on every DML call — do not rely on HTTP-level success alone.
- Build a dead-letter queue or retry table for records returned with `success=false` in `SaveResult[]`.
- Handle `INVALID_SESSION_ID` faults with automatic re-authentication and full query restart.
- Implement idempotency using External ID fields on upsert so retried batches do not create duplicates.
- Test with large data volumes to expose `queryMore()` gaps before production deployment.

### Security

SOAP authentication using `login()` with username/password is a credential-in-code risk if not handled carefully. Security guidance:

- Never embed Salesforce credentials or security tokens in source code, configuration files, or version control.
- Source credentials from environment variables, a secrets manager (AWS Secrets Manager, HashiCorp Vault), or an external client app OAuth flow.
- OAuth via an **external client app** is no longer merely preferable to `login()` — it is the only surviving option. `login()` was removed in API 65.0 and retires in versions 31.0–64.0 with Summer '27, and newly created orgs already gate it behind the `Any API Auth` user permission. Treat any remaining `login()` integration as carrying a dated liability, not just a credential-hygiene problem.
- The security token appended to the `login()` password is a static credential — treat it with the same security classification as the password itself.
- Apply IP range restrictions on the integration user's profile and set the minimum session timeout that the integration can tolerate.
- Integration users should have the minimum Permission Set assignments needed — avoid assigning `Modify All Data` or `System Administrator` profiles.

### Adaptability

Enterprise WSDL integrations are tightly coupled to the org schema. This creates a hidden change-management dependency: every org schema change requires an integration code change (WSDL regeneration and stub rebuild).

- Document the WSDL regeneration requirement in the integration runbook.
- Use partner WSDL for integrations expected to run across org lifecycles, managed packages, or multiple customer orgs.
- Pin API versions explicitly in endpoint URLs and include API version as a tracked dependency in the integration's release process.

---

## Architectural Tradeoffs

### SOAP vs REST for New Integrations

SOAP offers mature toolkits (WSC, Visual Studio WSDL import) and is required for the Metadata API. REST is simpler, JSON-native, and the Salesforce product direction. For any new integration that does not specifically require SOAP, REST is the correct choice. Maintaining existing SOAP integrations is reasonable — migrating working integrations to REST purely for technology preference adds risk without proportional benefit.

### Enterprise WSDL vs Partner WSDL

Enterprise WSDL gives compile-time safety and developer productivity for a known org schema. Partner WSDL gives portability and eliminates regeneration overhead at the cost of runtime type resolution. The tradeoff is schema change velocity: high-change orgs under active development pay a recurring tax for enterprise WSDL maintenance that partner WSDL eliminates.

### Session Management Strategy

`login()` with username/password is simple to implement but hard to operate securely — and it now has an end date, which removes the trade-off entirely. OAuth JWT Bearer flow adds initial setup complexity but eliminates credential storage, enables session scoping, and supports token revocation. The migration cost is smaller than it looks: SOAP API accepts JWT-based access tokens in the same `sessionId` header element, so the operation calls are untouched and only the auth step is rewritten. The real scheduling question is not *whether* to migrate but whether each integration can be re-credentialed before Summer '27 — inventory `login()` callers now, because the work is per-integration and cannot be done centrally.

---

## Anti-Patterns

1. **Hardcoded login endpoint as the SOAP service URL for all calls** — Using `login.salesforce.com` as the permanent SOAP endpoint works only on `na1`. All other instances fail silently or with connection errors. The `serverUrl` from `LoginResult` must be used for all post-authentication calls.

2. **Ignoring per-record `SaveResult` / `UpsertResult` errors** — SOAP DML calls do not throw exceptions for record-level failures. Checking only for a successful HTTP response or absence of a SOAP fault silently discards failed records. Every production SOAP integration must inspect each element of the result array.

3. **Sharing a single session token across long-running batch processes without expiry handling** — Treating the `sessionId` from `login()` as permanent causes random mid-batch failures when the session expires. Sessions must be treated as ephemeral credentials with a built-in expiry handler.

4. **Using enterprise WSDL for ISV / multi-org products** — An enterprise WSDL is org-specific. Distributing an integration built against one org's enterprise WSDL to another org will fail because the schema differs. ISV products must use the partner WSDL.

5. **Designing a new integration around `login()`, or pinning the endpoint back to v64.0 to keep it alive** — Both are dead ends. `login()` returns `UNSUPPORTED_API_VERSION` at v65.0+ and disappears from 31.0–64.0 at Summer '27, so version-pinning buys months and forfeits every intervening API improvement. Authenticate through an external client app with OAuth instead.

---

## Official Sources Used

- SOAP API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_quickstart_intro.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm (login flow, WSDL usage, WSC patterns)
- SOQL and SOSL Reference — Using Relationship Queries with the Partner WSDL — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_query_partner_wsdl.htm
- SOAP API Developer Guide — sObject (generic object / type resolution via DescribeSObjectResult name) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_partner_objects.htm
- SOAP API Developer Guide — Partner WSDL (loosely typed data model) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_partner.htm
- SOAP API Developer Guide — Queries and the Partner WSDL (QueryResult field ordering) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_partner_queries.htm
- Salesforce Developers Blog — Winter '26 for Developers — https://developer.salesforce.com/blogs/2025/09/winter26-developers (confirms SOAP `login()` is unavailable as of Winter '26 / API 65.0, returning HTTP 500 with `UNSUPPORTED_API_VERSION`; `login()` retained in versions 31.0–64.0 until Summer '27; external client apps are the prescribed replacement) (verified 2026-08-13)
- Salesforce Developers Blog — The Salesforce Developer's Guide to the Summer '26 Release — https://developer.salesforce.com/blogs/2026/06/the-salesforce-developers-guide-to-the-summer-26-release (confirms the `Any API Auth` user permission gating SOAP `login()` and enforced by default in newly created orgs; the Summer '27 retirement of `login()` in versions 31.0–64.0; and that SOAP API accepts JWT-based access tokens in the `sessionId` header element) (verified 2026-08-13)
- SOAP API Developer Guide — SOAP API End-of-Life Policy — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/api_eol_soap.htm (confirms versions 7.0–20.0 retired as of Summer '22, versions 21.0–30.0 retired as of Summer '25, versions 31.0–67.0 supported, and the 3-year support / 1-year notice policy) (verified 2026-08-13)
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
