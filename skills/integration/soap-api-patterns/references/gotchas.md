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

**When it occurs:** Salesforce retires old API versions in waves. Per the SOAP API End-of-Life Policy, versions 7.0 through 20.0 are retired ("As of Summer '22, these versions are retired and unavailable") and versions 21.0 through 30.0 are retired ("As of Summer '25, these versions are retired and unavailable"). Versions 31.0 through 67.0 are supported. Integrations pinned to a URL in a retired range fail outright — do not read "below v21.0" as the current boundary, it moved.

The same error code now has a second, unrelated cause: at API version 65.0 and later the `login()` **call** was removed while the version itself is perfectly current. A `login()` against `/services/Soap/u/65.0` returns `UNSUPPORTED_API_VERSION` even though every other operation on 65.0 works. Diagnose by asking which call failed, not just which version is in the URL — see Gotcha 8.

**How to avoid:** Pin endpoint URLs to API version v56.0 or later and audit SOAP endpoint URLs during annual integration reviews. Salesforce "is committed to supporting each API version for a minimum of 3 years from the date of first release" and "notifies customers who use an API version scheduled for deprecation at least 1 year before support for the version ends" — treat the API version as a first-class, tracked dependency in your integration's configuration, not a buried constant.

---

## Gotcha 7: Partner-WSDL Relationship Queries Require a `describeSObjects()` Discovery Step

**What happens:** A relationship SOQL query — a parent-to-child subquery such as `SELECT Id, (SELECT Id FROM Assets) FROM Account`, or a child-to-parent dot-walk such as `SELECT Id, Owner.Name FROM Case` — that an enterprise-WSDL client builds directly from its generated classes cannot be constructed the same way from a partner-WSDL client. The partner WSDL carries none of the relationship type metadata the enterprise WSDL bakes into its stubs, so the `relationshipName` for one-to-many subqueries and the reference-field names for child-to-parent traversal are not available at compile time.

**When it occurs:** Any ISV, packaged, or multi-org integration built on the partner WSDL — the same audience that chose the partner WSDL precisely to avoid per-org regeneration. The partner WSDL "doesn't contain the detailed type information that's available in the enterprise WSDL which you need for a relationship SOQL query," because it "defines a single, generic object (`sObject`) that represents all the objects."

**How to avoid:** Call `describeSObjects()` for the target object before building the query. From the `DescribeSObjectResult`, read the `relationshipName` for one-to-many relationships (for example, `Assets` on `Account`) to form subqueries, and identify the reference fields (for example, `WhoId`, `WhatId`, `OwnerId`, or custom lookups) for child-to-parent traversal. Because the query returns nested records as generic `sObject`s, resolve each nested record's real type from the `name` field of its `DescribeSObjectResult` instead of casting to a generated class, and parse fields in the order of your `SELECT` list rather than the WSDL's declared order.

---

## Gotcha 8: `login()` Is Already Gone at v65.0+ and Retires Everywhere in Summer '27

**What happens:** Three distinct failures, all from the same retirement programme, and they look nothing alike:

1. A `login()` call against an endpoint at API version 65.0 or later fails immediately. Per the Winter '26 release notes, "As of Winter '26 (API version 65.0), SOAP `login()` is no longer available. It will return an HTTP status code of 500 and the exception code `UNSUPPORTED_API_VERSION`." The version is current; only the `login()` call was withdrawn.
2. A `login()` that has worked for years against production is rejected the first time it runs against a newly created sandbox or scratch org. "A new Any API Auth user permission lets you control who can authenticate via SOAP `login()`, and it's enforced by default in newly created orgs." The credentials are fine; the running user lacks the **Any API Auth** permission.
3. On Summer '27, every remaining `login()` stops. Versions 31.0–64.0 keep it only "until Summer '27 is released."

**When it occurs:** Any integration — middleware, ETL job, Ant Migration Tool invocation, WSC client — that authenticates with username, password, and security token. Failure 1 hits whoever upgrades their endpoint version; failure 2 hits whoever spins up a fresh org; failure 3 hits everyone still on the pattern.

**How to avoid:** Migrate authentication to OAuth 2.0 — JWT bearer or client credentials flow for server-to-server, web server flow for browser-based — issued through an **external client app**, not a legacy connected app: "Before Summer '27 is released, customers and partners must modify or upgrade their applications to use external client apps for authentication." The migration is confined to the auth step, because "SOAP API now accepts JWT-based access tokens from Salesforce OAuth flows in the `sessionId` header element, reaching parity with REST authentication." Every `query()`, `create()`, `upsert()`, and `queryMore()` call stays exactly as written. Do not treat pinning the endpoint back to 64.0 as a remedy — it buys time against failure 1 and nothing against failure 3.
