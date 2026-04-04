---
name: soap-api-patterns
description: "Use when designing, implementing, or reviewing Salesforce SOAP API integrations — covering enterprise vs partner WSDL selection, login() and session management, core operations (query/create/update/upsert/delete), and Metadata API SOAP usage. Trigger keywords: 'enterprise WSDL', 'partner WSDL', 'login() call', 'sessionId', 'SOAP API', 'WSC', 'force-wsc', 'Ant Migration Tool', '.NET SOAP integration'. NOT for REST API, Bulk API 2.0, or GraphQL API."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
tags:
  - soap-api
  - enterprise-wsdl
  - partner-wsdl
  - session-management
  - metadata-api
  - legacy-integration
triggers:
  - "should I use the enterprise WSDL or the partner WSDL for my integration"
  - "how do I authenticate to the Salesforce SOAP API and manage the session"
  - "my .NET or Java integration uses WSDL-generated stubs and I need to query or update records"
  - "when should I use SOAP API instead of REST API for a Salesforce integration"
  - "the Metadata API requires SOAP — how do I set up login and deploy metadata"
inputs:
  - "integration consumer type: internal org integration vs ISV/cross-org integration"
  - "development platform: .NET (Visual Studio), Java (WSC), or other SOAP toolkit"
  - "authentication context: username-password login() vs OAuth session ID injection"
  - "target org edition and API version to confirm WSDL download location and endpoint"
  - "operation type: DML (create/update/upsert/delete), query/queryMore, or Metadata API deploy/retrieve"
outputs:
  - "WSDL selection decision with rationale (enterprise vs partner)"
  - "login() flow with sessionId extraction and serverUrl configuration"
  - "endpoint URL pattern for the selected API version"
  - "operation call structure for query(), queryMore(), create(), upsert(), and delete()"
  - "session expiry handling strategy"
  - "review findings for an existing SOAP integration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# SOAP API Patterns

Use this skill when the integration task involves the Salesforce SOAP API — whether you are selecting between the enterprise and partner WSDLs, implementing a login-and-session lifecycle, calling core DML or query operations, or working with the Metadata API (which is exclusively SOAP-based). This skill also covers the decision of when SOAP is the right choice over REST.

---

## Before Starting

Gather this context before working on anything in this domain:

- **WSDL type needed:** Is this integration internal to a single org (enterprise WSDL) or a product/ISV that must work with any org (partner WSDL)?
- **Development platform:** What SOAP toolkit generates the client stubs? Java uses WSC (`force-wsc`), .NET uses Visual Studio WSDL import, other languages use their native SOAP client.
- **API version:** Which version is the integration targeting? The endpoint URL must include the version explicitly (e.g., `https://<instance>.salesforce.com/services/Soap/c/63.0` for enterprise, `https://<instance>.salesforce.com/services/Soap/u/63.0` for partner). Spring '25 = v63.0.
- **Authentication method:** Is this a direct `login()` call with username/password/security-token, or is an OAuth session ID being injected into SOAP headers (preferred for connected apps)?
- **Org edition and daily API limits:** Enterprise Edition allows up to 1,000 API calls per Salesforce license per 24-hour period (minimum 1,000 total); Developer Edition is limited to 15,000 per day. SOAP and REST calls share the same daily limit pool.

---

## Core Concepts

### Enterprise WSDL vs Partner WSDL

The Salesforce SOAP API ships two distinct WSDLs with different type contracts:

| | Enterprise WSDL | Partner WSDL |
|---|---|---|
| **Type contract** | Strongly typed — each object and field has a generated Java/C# class | Weakly typed — generic `sObject` with string-keyed field maps |
| **Org-specificity** | Org-specific — generated from your org's schema, includes custom objects and fields | Generic — works with any Salesforce org without regeneration |
| **When to use** | Internal integrations for a specific org where developer productivity and compile-time safety matter | ISVs, packages, and cross-org integrations that must work against multiple or unknown orgs |
| **WSDL endpoint** | `Setup > API > Generate Enterprise WSDL` | `Setup > API > Generate Partner WSDL` |
| **SOAP service URL** | `/services/Soap/c/<version>/` | `/services/Soap/u/<version>/` |
| **Critical drawback** | Must be re-downloaded and regenerated every time custom fields or objects are added or changed | Developer must resolve field metadata at runtime; relationship queries require extra care |

Both WSDLs expose the same operations (`login`, `query`, `create`, `update`, `upsert`, `delete`, etc.). The difference is entirely in the type surface exposed to the client.

The Metadata API also requires WSDL-based access. Authentication is established via the enterprise or partner WSDL `login()` call first, and the resulting `sessionId` is then used to initialize the Metadata API connection.

### Authentication: login() and Session Management

The canonical SOAP authentication flow calls `login()` on the SOAP endpoint and extracts two values from the `LoginResult`:

1. **`sessionId`** — the session token included in every subsequent SOAP call via the `CallOptions` or `SessionHeader` SOAP header.
2. **`serverUrl`** — the instance-specific URL to use for all subsequent API calls. The login endpoint is a generic URL; after login you must switch to the `serverUrl`. Failing to do so causes calls to fail on sandbox and non-`na1` instances.

```xml
<!-- SOAP login request (partner WSDL) -->
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:partner.soap.sforce.com">
  <soapenv:Body>
    <urn:login>
      <urn:username>user@example.com</urn:username>
      <urn:password>passwordSECURITYTOKEN</urn:password>
    </urn:login>
  </soapenv:Body>
</soapenv:Envelope>
```

The response `LoginResult` contains:
- `serverUrl` — use this as the base for all subsequent SOAP calls
- `sessionId` — include in `SessionHeader` on every subsequent call
- `userId`, `userInfo` — metadata about the authenticated user

**Session expiry:** Sessions expire after the org's configured timeout (default 2 hours for most editions, configurable from 15 minutes to 24 hours in Setup > Session Settings). Expired sessions return `INVALID_SESSION_ID`. Integrations must catch this fault and re-authenticate — either by calling `login()` again or by refreshing the OAuth access token if using OAuth session injection.

**Security token:** When calling `login()` with username/password from an IP not in the org's trusted range, the security token must be appended directly to the password string (no separator). Use OAuth flows to avoid embedding credentials.

### Core SOAP Operations

| Operation | Description | Notes |
|---|---|---|
| `query()` | Execute a SOQL query; returns up to `queryBatchSize` records | Returns `QueryResult` with `done` flag and `queryLocator` |
| `queryMore()` | Fetch the next page of a `query()` result | Required when `done` is `false`; use the `queryLocator` from prior result |
| `create()` | Insert one or more sObjects (up to 200 per call) | Returns `SaveResult[]` with per-record success/error |
| `update()` | Update one or more sObjects by Salesforce ID (up to 200 per call) | Returns `SaveResult[]` |
| `upsert()` | Create-or-update using an external ID field (up to 200 per call) | Requires an indexed External ID field; returns `UpsertResult[]` |
| `delete()` | Delete one or more records by ID (up to 200 per call) | Soft delete; records go to Recycle Bin |
| `merge()` | Merge up to 3 records into a master record | Returns `MergeResult`; merged records are deleted |
| `retrieve()` | Fetch specific fields for a list of record IDs | Efficient alternative to query when IDs are known |
| `getUpdated()` / `getDeleted()` | Retrieve IDs of records changed or deleted in a time window | Useful for CDC-style polling when CDC/Streaming is not available |

Each DML call accepts an array of up to 200 records. Salesforce processes all records in the call even if some fail — there is no all-or-none semantics by default (unlike REST Composite with `allOrNone: true`). Inspect each `SaveResult` or `UpsertResult` for per-record `success` and `errors`.

### When to Use SOAP Over REST

Prefer REST API for new integrations — it is simpler, more widely supported, and the Salesforce product direction favors it. Use SOAP API when:

1. **Metadata API is involved** — The Metadata API is exclusively SOAP. Deployments via the Ant Migration Tool, Java/WSC-based deploy tools, and any retrieve/deploy operation must use SOAP.
2. **Legacy .NET or Java codebase already using WSDL-generated stubs** — Migrating a working integration to REST has cost and risk. Maintaining SOAP is reasonable if the integration is stable.
3. **Enterprise-grade SOAP toolkit ecosystem** — WS-Security, SOAP intermediaries, and certain ESB/middleware products (MuleSoft, IBM MQ, SAP PI) have first-class SOAP connectors. Using REST in these environments may require lower-level HTTP configuration.
4. **Compound field access on Address/Geolocation** — SOAP returns Address and Geolocation as nested complex types in the response, which some ETL tools handle better than the REST API's flat-field representation.

---

## Common Patterns

### Mode 1 — Implement a New SOAP Integration

**Step 1 — Choose WSDL type.** Internal to a single org? Use enterprise WSDL for compile-time safety. ISV or multi-org product? Use partner WSDL.

**Step 2 — Download and generate stubs.** In Setup > API, download the WSDL file. Use the platform's SOAP toolkit to generate client classes. For Java with WSC:

```bash
java -classpath force-wsc-XX.X.X-uber.jar \
  com.sforce.ws.tools.wsdlc enterprise.wsdl enterprise.jar
```

**Step 3 — Implement login() and capture serverUrl + sessionId.**

```java
ConnectorConfig config = new ConnectorConfig();
config.setAuthEndpoint("https://login.salesforce.com/services/Soap/c/63.0");
config.setUsername("user@example.com");
config.setPassword("passwordSECURITYTOKEN");

EnterpriseConnection connection = Connector.newConnection(config);
// config.getServiceEndpoint() now contains the instance serverUrl
// connection carries the sessionId automatically via WSC
```

**Step 4 — Execute operations and inspect per-record results.**

```java
SObject account = new SObject();
account.setType("Account");
account.setField("Name", "Acme Corp");

SaveResult[] results = connection.create(new SObject[]{ account });
for (SaveResult result : results) {
    if (!result.isSuccess()) {
        for (Error error : result.getErrors()) {
            System.err.println(error.getStatusCode() + ": " + error.getMessage());
        }
    }
}
```

**Step 5 — Implement session expiry handling.** Catch `InvalidSObjectFault` / `INVALID_SESSION_ID` faults, call `login()` again, and retry.

### Mode 2 — Review an Existing SOAP Integration

Check for these issues in priority order:

1. **Is `serverUrl` used after login?** Hardcoded production endpoints break sandbox or EU instances. The `serverUrl` from `LoginResult` must be the base for all subsequent calls.
2. **Is the API version current?** Endpoint URLs containing `/Soap/c/20.0` through `/Soap/c/40.0` are in the deprecated range. Salesforce retires API versions; update to v56.0 or later.
3. **Are `SaveResult[]` / `UpsertResult[]` errors inspected per record?** SOAP DML calls partially succeed — checking only the HTTP response code or outer fault misses record-level failures.
4. **Is the enterprise WSDL up to date?** If custom fields or objects were added since the last WSDL regeneration, those fields are inaccessible from the stubs.
5. **Are credentials hardcoded?** `login()` password with embedded security token must not be stored in source code.
6. **Is `queryMore()` called when `done` is false?** Failing to paginate silently truncates query results.

### Mode 3 — Troubleshoot a SOAP Integration

| Symptom | Likely Cause | Fix |
|---|---|---|
| `INVALID_SESSION_ID` fault | Session expired or wrong session header | Re-authenticate with `login()` and update `SessionHeader` |
| `UNSUPPORTED_API_VERSION` (500) | API version in endpoint URL is retired | Update endpoint URL to a current version (v56.0+) |
| Records found in login org, not in data org | `serverUrl` ignored; still using login endpoint | Switch all post-login calls to `serverUrl` from `LoginResult` |
| Custom fields return null or don't exist in stubs | Enterprise WSDL was not regenerated after field creation | Re-download enterprise WSDL and regenerate stubs |
| `REQUIRED_FIELD_MISSING` on create | Org validation rule or required field not set in request | Inspect `SaveResult.errors` for specific field names |
| `queryMore()` returns fault | `queryLocator` from prior page is stale (session reset) | Handle session expiry and re-execute query from scratch |
| Session expires mid-batch | Default session timeout reached during long operations | Increase session timeout in Setup > Session Settings or implement proactive re-authentication |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New integration from scratch | REST API | Simpler, JSON-native, broader modern tooling support |
| Metadata deployments (Ant Migration Tool, CI/CD deploy) | SOAP (Metadata API) | Metadata API is exclusively SOAP-based |
| Existing .NET/Java codebase with WSDL stubs | Maintain SOAP API | Rewrite cost outweighs benefit unless integration is failing |
| ISV building a managed package for any org | Partner WSDL | Works without regeneration across all customer orgs |
| Internal integration for a known single org | Enterprise WSDL | Strongly typed, compile-time safety, auto-generated classes |
| Auth from untrusted IP with username/password | Append security token to password | Salesforce requires token when IP not in trusted range |
| Auth in production systems | OAuth JWT Bearer or Web Server flow | Avoids embedding credentials; tokens are scoped and revocable |
| Query result > configured `queryBatchSize` | `query()` + `queryMore()` loop | `query()` returns partial results; must call `queryMore()` until `done = true` |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] WSDL type (enterprise vs partner) is appropriate for the consumer type (internal vs ISV/multi-org).
- [ ] Post-login calls use `serverUrl` from `LoginResult`, not a hardcoded endpoint.
- [ ] API version in endpoint URL is at or above v56.0 (ideally v63.0 for Spring '25).
- [ ] For enterprise WSDL integrations: WSDL was regenerated after any org schema changes.
- [ ] Session expiry (`INVALID_SESSION_ID`) is handled with re-authentication, not just logged as fatal.
- [ ] All `SaveResult[]` / `UpsertResult[]` arrays are inspected per record — partial DML success is expected.
- [ ] `queryMore()` is called when `QueryResult.isDone()` is `false`; results are not silently truncated.
- [ ] Credentials and security tokens are not stored in source code or configuration files in version control.
- [ ] Daily API call volume estimate fits within the org's edition limit (SOAP and REST share the same pool).
- [ ] Compound fields (Address, Geolocation) are handled as nested complex types, not flat strings.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Enterprise WSDL becomes stale when org schema changes** — The enterprise WSDL is generated from your org's exact schema at a point in time. Adding or changing a custom field after generation makes that field invisible to the generated stubs. The integration will not error — it will silently omit the field. Regenerate the WSDL and rebuild stubs any time the org schema changes.

2. **`serverUrl` must replace the login endpoint for all subsequent calls** — The `login()` call targets `login.salesforce.com` (or `test.salesforce.com` for sandbox). The `LoginResult.serverUrl` is the instance-specific URL you must use for all subsequent SOAP calls. Ignoring `serverUrl` and continuing to use the login host causes requests to fail on any instance other than `na1`, including all EU, APAC, and Hyperforce instances.

3. **Session expiry kills in-progress batch operations** — If a `query()` + `queryMore()` loop runs longer than the org's session timeout, the `queryLocator` becomes invalid and `queryMore()` returns `INVALID_SESSION_ID`. The entire query must restart from scratch after re-authentication. Mitigation: set a longer session timeout in Setup > Session Settings, or break large queries into smaller date-range slices that complete within a single session window.

4. **SOAP DML calls partially succeed — there is no implicit rollback** — Unlike REST Composite with `allOrNone: true`, a SOAP `create()` or `update()` call with 200 records will process all records regardless of individual failures. The response array contains a `SaveResult` per record; some will have `success=true` and others `success=false`. Integrations that only check the HTTP 200 outer response will miss failed records.

5. **Security token appended, not separate** — The `login()` password parameter is the user's password with the security token appended as a single string (e.g., `mypasswordXYZTOKEN`). There is no separator. A common mistake is passing the token as a separate parameter, which results in a `LOGIN_MUST_USE_SECURITY_TOKEN` fault.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| WSDL selection rationale | Enterprise vs partner decision with justification for the integration context |
| Login flow implementation | `login()` call pattern, `serverUrl` capture, and `SessionHeader` wiring |
| Operation call structure | Create/update/upsert/delete/query call scaffolds with per-record result inspection |
| Session expiry handler | Fault detection and re-authentication pattern |
| Review findings | Itemized issues from the Mode 2 review checklist with severity and remediation |

---

## Related Skills

- `integration/rest-api-patterns` — use for all new integrations where SOAP is not required; REST is the preferred API for new development.
- `integration/oauth-flows-and-connected-apps` — use when replacing `login()` username/password with OAuth JWT Bearer or Web Server flows.
- `integration/graphql-api-patterns` — use when the consumer needs flexible, field-selective queries from a single endpoint.
- `data/bulk-api-and-large-data-loads` — use when record volumes exceed what SOAP DML (200 records/call) can handle efficiently.
