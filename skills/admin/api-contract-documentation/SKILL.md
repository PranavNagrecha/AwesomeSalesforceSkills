---
name: api-contract-documentation
description: "Use this skill when producing or reviewing API contract documentation for Salesforce integrations: versioning policy artifacts, request/response schema specs, error code catalogs, rate limit documentation, and OpenAPI generation for sObjects. Trigger keywords: Salesforce API versioning policy, API end-of-life policy, document API endpoints, REST API rate limits, OpenAPI sObjects. NOT for API implementation (building the API endpoint), Apex REST service coding, or Connected App setup — those are covered by apex-rest-services and connected-app-security."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "what is Salesforce API versioning policy and how long is each version supported"
  - "how do I document Salesforce REST API rate limits for my integration consumers"
  - "how do I generate an OpenAPI spec for Salesforce sObject endpoints"
  - "what HTTP header shows remaining API call quota in Salesforce"
  - "how do I find out which API versions are still supported in my Salesforce org"
  - "what is the difference between REQUEST_LIMIT_EXCEEDED and HTTP 429 in Salesforce API"
tags:
  - rest-api
  - api-versioning
  - api-documentation
  - rate-limits
  - openapi
  - integration
inputs:
  - "List of Salesforce API endpoints to document"
  - "Current API version in use"
  - "Consumer systems needing to know rate limit and versioning policies"
  - "Whether custom Apex REST (@RestResource) endpoints exist alongside standard APIs"
outputs:
  - "API versioning policy summary with support window and retirement notice requirements"
  - "Rate limit documentation format with Sforce-Limit-Info header guidance"
  - "Error code catalog covering HTTP 4xx/5xx responses"
  - "OpenAPI 3.0 generation guidance for sObject endpoints (beta)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# API Contract Documentation

Use this skill when producing documentation artifacts for Salesforce REST API integrations — versioning policies, error code catalogs, rate limit specifications, and request/response schema documentation. Distinct from API implementation: this skill addresses the documentation layer that consumer teams use to build integrations safely.

---

## Before Starting

Gather this context before working on anything in this domain:

- What API version is the integration using? (e.g., v60.0). Is there a risk this version is approaching end-of-life?
- Does the integration use standard sObjects REST API, custom Apex REST (@RestResource) endpoints, or both?
- What are the daily API request limits for this org? (Check `/services/data/vXX.0/limits` or the Sforce-Limit-Info response header.)
- Is an OpenAPI 3.0 document required? Note: Salesforce's OpenAPI beta covers sObjects REST API only — custom Apex REST endpoints must be hand-authored.

---

## Core Concepts

### Salesforce API Versioning Policy

Salesforce REST API versioning uses **integer version numbers** (e.g., v60.0, v61.0). The official policy guarantees:
- A **minimum 3-year support window** for each released version
- At **least 1 year's advance notice** before a version is retired
- The `/services/data/` endpoint enumerates all currently live API versions with their `version`, `label`, and `url` properties

The API end-of-life (EOL) policy is documented at `developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/api_rest_eol.htm`. Integrations should document the API version in use and set calendar reminders to check the EOL list with each Salesforce seasonal release.

### Rate Limits and the Sforce-Limit-Info Header

Salesforce API request limits are tracked in a **rolling 24-hour window**. Two indicators:

1. **`Sforce-Limit-Info` response header** — Every REST API response includes this header with the format: `api-usage=XXXX/YYYY` where XXXX is the number of calls used and YYYY is the daily limit. Consumer systems should log this header to track consumption trends.
2. **`/services/data/vXX.0/limits` resource** — Returns the current org's limits across all limit types including `DailyApiRequests`. Poll this endpoint to proactively detect approaching exhaustion.

When the daily limit is exhausted:
- HTTP 403 with error code `REQUEST_LIMIT_EXCEEDED` (Salesforce REST API behavior)
- HTTP 429 (rate limit response — also used in some contexts)

The exact numeric daily limit depends on the org edition and add-on licenses — it is NOT a fixed published value. Retrieve it dynamically from the `/limits` resource or from the **Salesforce Developer Limits Quick Reference** cheatsheet at `developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/`.

### OpenAPI 3.0 for sObjects REST API (Beta)

Salesforce provides a **beta OpenAPI 3.0 document generator** for the sObjects REST API (standard Create/Read/Update/Delete operations on SObjects). Access via:
```
GET /services/data/vXX.0/sobjects/{SObjectName}/describe/openapi3_0
```

**Critical limitation:** This beta feature generates OpenAPI specs only for **standard sObjects REST endpoints**. It does NOT cover:
- Custom Apex REST endpoints (`@RestResource` classes)
- Composite API resources (`/composite`, `/composite/batch`)
- Connect REST API (Chatter, Experience Cloud)

Custom Apex REST endpoints must have their request/response contracts hand-authored using OpenAPI 3.0 or another specification format.

---

## Common Patterns

### Pattern: API Versioning Policy Documentation

**When to use:** When onboarding a new integration consumer team or producing architecture documentation for an existing integration.

**How it works:**
1. Enumerate live API versions: `GET /services/data/` — returns an array of available versions.
2. Record the integration's pinned version and its `label` from the response.
3. Document the retirement policy: 3-year support window, 1-year advance notice.
4. Add a recurring review step (quarterly) to check the Salesforce EOL notice list: check Release Notes and `api_rest_eol.htm` with each seasonal release.
5. Define the version upgrade SLA for the integration team (e.g., "upgrade within 6 months of deprecation notice").

### Pattern: Rate Limit Documentation and Monitoring

**When to use:** When consumer teams need to understand how to avoid API limit exhaustion during bulk operations or high-frequency integrations.

**How it works:**
1. Document the daily limit retrieval method: `GET /limits` returns `DailyApiRequests.Max` for the org.
2. Establish a monitoring pattern: log the `Sforce-Limit-Info: api-usage=X/Y` header from every response and alert when X/Y > 80%.
3. Document the error: HTTP 403 `REQUEST_LIMIT_EXCEEDED` means daily limit is exhausted; HTTP 429 is transient rate throttling. These have different recovery patterns: 403 requires waiting until the 24-hour window resets; 429 requires exponential backoff retry.
4. For bulk operations, recommend Bulk API 2.0 which has a separate request budget from the REST API limit.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Documenting standard CRUD API endpoints | Use sObjects OpenAPI beta + hand-authored supplement | Beta covers CRUD; manually document composite and custom endpoints |
| Documenting custom Apex REST endpoints | Hand-author OpenAPI 3.0 spec | Beta does not cover @RestResource endpoints |
| Consumer needs rate limit ceiling | Retrieve from /limits dynamically, not from documentation | Limit varies by org edition and license |
| Integration hitting REQUEST_LIMIT_EXCEEDED | Wait for 24-hour window reset; switch to Bulk API 2.0 for bulk ops | Daily limit resets on rolling 24-hour basis |
| Checking if API version is near retirement | Check api_rest_eol.htm with each seasonal release | EOL list is updated per Salesforce release cycle |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Enumerate live API versions** — `GET /services/data/` to record available versions and confirm the integration's version is active.
2. **Retrieve org limits** — `GET /services/data/vXX.0/limits` and document the `DailyApiRequests.Max` value for the org.
3. **Document error codes** — Catalog the HTTP status codes the integration must handle: 200/201/204 (success), 400 (malformed request), 401 (authentication), 403 (REQUEST_LIMIT_EXCEEDED or insufficient access), 404 (record not found), 429 (rate throttle), 500 (server error).
4. **Generate sObjects OpenAPI spec (if applicable)** — Use the beta endpoint `GET /sobjects/{SObjectName}/describe/openapi3_0`. Save the response as the baseline schema document.
5. **Hand-author Apex REST contracts** — For any `@RestResource` endpoints, write the OpenAPI 3.0 spec manually based on the Apex class definition. Include request body schema, response schema, and all error responses.
6. **Document versioning policy** — Record pinned API version, support window, and the team's version upgrade SLA.
7. **Establish limit monitoring** — Define how the `Sforce-Limit-Info` header is logged and at what threshold an alert is triggered.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] API version documented and checked against EOL list
- [ ] Daily API limit retrieved from /limits resource (not hardcoded)
- [ ] Error code catalog includes 400, 401, 403 (REQUEST_LIMIT_EXCEEDED), 404, 429, 500
- [ ] Sforce-Limit-Info header monitoring pattern documented
- [ ] OpenAPI spec covers all endpoints (standard + hand-authored for Apex REST)
- [ ] Version upgrade SLA defined for integration team
- [ ] No hardcoded rate limit numbers that could become stale

---

## Salesforce-Specific Gotchas

1. **Fabricating specific numeric rate limits is dangerous** — API request limits are NOT a fixed universal number. They vary by org edition, add-on licenses, and Salesforce's adjustments. Never document a specific hardcoded number. Always reference the `/limits` resource or the developer limits quick reference cheatsheet.

2. **OpenAPI beta does not cover custom Apex REST** — Teams often assume the OpenAPI endpoint generates documentation for all their APIs. Custom `@RestResource` endpoints have no auto-generated spec. They must be hand-authored.

3. **SLA uptime commitments are not in developer docs** — API SLA percentages (uptime, latency) are in trust.salesforce.com and Order of Service agreements, not in the developer documentation. Do not document SLA percentages from developer docs — they do not exist there.

4. **REQUEST_LIMIT_EXCEEDED (403) vs 429 rate throttling have different recovery** — 403 means the 24-hour allocation is exhausted and requires waiting for the rolling window reset. 429 is a transient throttle that responds to exponential backoff retry. Treating them identically (e.g., immediate retry on 403) will not work.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API versioning policy document | Pinned version, support window, EOL check cadence, upgrade SLA |
| Rate limit specification | DailyApiRequests.Max from /limits, Sforce-Limit-Info monitoring pattern |
| Error code catalog | All HTTP status codes the integration must handle with recovery guidance |
| OpenAPI 3.0 spec | Generated for sObjects endpoints, hand-authored for Apex REST |

---

## Related Skills

- `integration/apex-rest-services` — Use for implementing custom Apex REST endpoints (@RestResource) — the implementation layer this skill documents
- `integration/connected-app-security` — Use for OAuth flow setup and Connected App configuration
- `integration/api-led-connectivity` — Use for designing the API layer architecture before documenting individual endpoints
