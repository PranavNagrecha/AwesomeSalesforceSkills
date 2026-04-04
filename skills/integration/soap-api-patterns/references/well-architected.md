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
- Source credentials from environment variables, a secrets manager (AWS Secrets Manager, HashiCorp Vault), or a connected app OAuth flow.
- Prefer OAuth JWT Bearer or Web Server flow over `login()` username/password for production integrations — OAuth tokens are scoped, revocable, and do not require embedding user credentials.
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

`login()` with username/password is simple to implement but hard to operate securely. OAuth JWT Bearer flow adds initial setup complexity but eliminates credential storage, enables session scoping, and supports token revocation. For production integrations processing sensitive data, OAuth is the correct long-term architecture.

---

## Anti-Patterns

1. **Hardcoded login endpoint as the SOAP service URL for all calls** — Using `login.salesforce.com` as the permanent SOAP endpoint works only on `na1`. All other instances fail silently or with connection errors. The `serverUrl` from `LoginResult` must be used for all post-authentication calls.

2. **Ignoring per-record `SaveResult` / `UpsertResult` errors** — SOAP DML calls do not throw exceptions for record-level failures. Checking only for a successful HTTP response or absence of a SOAP fault silently discards failed records. Every production SOAP integration must inspect each element of the result array.

3. **Sharing a single session token across long-running batch processes without expiry handling** — Treating the `sessionId` from `login()` as permanent causes random mid-batch failures when the session expires. Sessions must be treated as ephemeral credentials with a built-in expiry handler.

4. **Using enterprise WSDL for ISV / multi-org products** — An enterprise WSDL is org-specific. Distributing an integration built against one org's enterprise WSDL to another org will fail because the schema differs. ISV products must use the partner WSDL.

---

## Official Sources Used

- SOAP API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_quickstart_intro.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm (login flow, WSDL usage, WSC patterns)
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
