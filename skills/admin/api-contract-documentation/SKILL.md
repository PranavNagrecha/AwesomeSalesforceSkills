---
name: api-contract-documentation
description: "Produce or review API contract documentation for Salesforce integrations: versioning policy artifacts, request/response schema specs, error code catalogs, rate limit documentation, OpenAPI generation for sObjects. Trigger keywords: Salesforce API versioning policy, API end-of-life policy, document API endpoints, REST API rate limits, OpenAPI sObjects, API contract record, error contract, errorCode catalog, 410 GONE retired API version, HTTP 300 external ID upsert, idempotency key, deprecation notice, composite subrequest limit. NOT for building the endpoint or writing the Apex REST service — use apex/apex-rest-services. NOT for upgrading the API version on your own Apex, LWC or sfdx-project.json — use devops/api-version-management."
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
  - "salesforce api suddenly returns 410 gone after we pinned an old api version"
  - "our integration got HTTP 300 back from an upsert by external id"
  - "write an API contract document between Salesforce and a partner system"
  - "hand-author an OpenAPI spec for a custom Apex REST endpoint"
  - "how many subrequests can a composite request contain and does it count as one API call"
  - "sObject Collections returned 200 OK but some rows did not save"
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
  - "A lintable API contract record (YAML) per endpoint and direction"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

## Questions to Ask Before Configuring

Ask these before the first line of the contract is written. Each answer becomes a field in the record, and each unasked question is a clause the partner will discover in production instead.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which Salesforce API version is this contract pinned to, and who owns the upgrade?" | Versions 21.0–30.0 are retired and unavailable as of Summer '25; a request on a retired version returns `410 GONE`, not a warning (REST API Guide, API End-of-Life Policy) | The `salesforce_api_version`, `owner` and `eol_review_date` fields of the contract record |
| "Is the partner's key our record Id, or their own identifier stored in an External Id field?" | If the external Id matches more than one record, REST API returns `300` and the record is neither created nor updated (REST API Guide, Insert or Update (Upsert) a Record Using an External ID) | The idempotency-key strategy plus a named runbook row for the duplicate-key case |
| "How many other integrations already draw on this org's 24-hour API allocation?" | The total inbound API request allocation is per org per 24-hour period, not per integration (Developer Limits Quick Reference, Total API Request Allocations) — one partner's retry storm exhausts every other integration's budget | A per-integration request budget in the rate-limit clause, not just the org ceiling |
| "For each Salesforce `errorCode` the partner can receive, what does the partner do — retry, alert, or park the record?" | The error response body is an *array* of error objects carrying `message`, `errorCode` and `fields`; a consumer that reads only the HTTP status discards the reason | One row per `errorCode` in the error contract, each with a partner-side action |
| "Does this integration send batches, and is a partial failure acceptable?" | An sObject Collections request that is well formed returns `200 OK` even when individual items failed — per-item outcomes live in the `errors` array (REST API Guide, Upsert Records Using sObject Collections) | The `allOrNone` decision and an explicit per-row reconciliation step |
| "Is any endpoint here a custom Apex REST class rather than a standard resource?" | The sObjects OpenAPI beta generates nothing for `@RestResource` classes, and a custom resource's URL mapping collides silently with another class's (see `references/gotchas.md` 7) | Which half of the OpenAPI document is generated and which half a human owns |
| "Who approves a breaking change, and how much notice does the partner get?" | Salesforce notifies customers at least 1 year before support for an API version ends; an internal contract with a shorter notice period is stricter than the platform it runs on | The change-control section: notice period, approver, and the deprecation-notice template |

What a proper configuration adds over just doing it: the partner's error handling is derived from the `errorCode` values Salesforce actually emits rather than from HTTP status alone, retries are idempotent by construction, and the version retirement date is a dated owner-assigned task instead of a `410 GONE` incident.

---

## Core Concepts

### Salesforce API Versioning Policy

Salesforce REST API versioning uses **integer version numbers** (e.g., v60.0, v61.0). The official policy guarantees:
- A **minimum 3-year support window** for each released version
- At **least 1 year's advance notice** before a version is retired
- The `/services/data/` endpoint enumerates all currently live API versions with their `version`, `label`, and `url` properties

Grounded status as published in the Summer '26 REST API Developer Guide (API End-of-Life Policy):

| Versions | Status |
|---|---|
| 31.0 through 66.0 | Supported |
| 21.0 through 30.0 | Retired and unavailable as of Summer '25 |
| 7.0 through 20.0 | Retired and unavailable as of Summer '22 |

A request against a retired version returns **`410 GONE`**. Before the version is retired, a call against a deprecated version returns a `Warning` response header with `warningCode` **299** and a message naming the release in which it will be removed — that header is the only advance signal the runtime gives you, and most HTTP clients drop it. To identify which callers are still on old versions, use the **API Total Usage** event type.

Calls to the Versions URI (`/services/data/`) do **not** count toward the org's API limit and do not require authentication, so an EOL check can run from anywhere.

### The Error Contract: Status Codes and the Errors Array

The response body of a failed REST API call is a JSON **array** of error objects, each carrying the message, the `errorCode`, and (where applicable) the offending fields:

```json
[
  {
    "fields": ["Id"],
    "message": "Account ID: id value of incorrect type: 001900K0001pPuOAAU",
    "errorCode": "MALFORMED_ID"
  }
]
```

Status codes the REST API Developer Guide documents (Status Codes and Error Responses) — the ones a contract must name explicitly:

| Code | What it means for the contract |
|---|---|
| 300 | The external Id matched more than one record. The body contains the list of matching records; nothing was written |
| 304 | Content unchanged since the `If-Modified-Since` value the caller sent |
| 400 | The JSON or XML body contains an error |
| 401 | The session ID or OAuth token expired or is invalid |
| 403 | Refused. If `errorCode` is `REQUEST_LIMIT_EXCEEDED`, the org's API request allocation is exhausted |
| 404 | Resource not found — a bad URI *or* a sharing issue, which the status alone cannot distinguish |
| 405 | Method not allowed for that resource |
| 409 | Conflict with the current state — check the API version is compatible with the resource |
| 410 | The resource has been retired or removed |
| 412 | A precondition in the request headers (for example `If-Unmodified-Since`) was not satisfied |
| 414 / 431 | The URI, or the URI plus headers, exceeds the 16,384-byte limit |
| 415 | The request entity is in a format the method does not support |
| 428 | The request was not conditional; add a conditional request header |
| 500 / 502 / 503 | Platform error, Salesforce Edge could not reach the instance, or the server is unavailable |

Note what is *not* in that table: **HTTP 429 is not listed as a REST API status code** in the guide's Status Codes and Error Responses section. Treat 429 as something a gateway, proxy or middleware layer in front of Salesforce may return, and say so in the contract rather than attributing it to the platform. UNVERIFIED (2026-09-04): the REST API Developer Guide's status-code table does not document 429; whether any Salesforce edge tier emits it is not established by the guides available here.

### Rate Limits and the Sforce-Limit-Info Header

Salesforce API request limits are tracked in a **rolling 24-hour window**. Two indicators:

1. **`Sforce-Limit-Info` response header** — Returned on every REST API request except calls to the Versions URI (`/`). The documented example carries two counters: `Sforce-Limit-Info: api-usage=10018/100000; api-bursts=1/750`. The first number in `api-usage` is calls used, the second is the org's limit. Consumer systems should log this header to track consumption trends.
2. **`/services/data/vXX.0/limits` resource** — Returns the current org's limits across all limit types including `DailyApiRequests`. Poll this endpoint to proactively detect approaching exhaustion.

When the daily limit is exhausted, the response is HTTP 403 with error code `REQUEST_LIMIT_EXCEEDED`. The same exception code is also returned when the **concurrent** limit on long-running requests is exceeded — a distinct condition documented in the Developer Limits Quick Reference (Concurrent API Request Limits): requests lasting 20 seconds or longer are capped at 5 for Developer Edition and Trial orgs, 25 for production orgs and sandboxes, with no limit on requests shorter than 20 seconds.

The exact numeric daily limit depends on the org edition and add-on licenses — it is NOT a fixed published value. The Developer Limits Quick Reference states the total as `100,000 + (number of licenses × calls per license type) + purchased API Call Add-Ons` for Enterprise, Unlimited and Performance Editions, and a flat 15,000 for Developer Edition. Retrieve the org's actual figure from the `/limits` resource rather than computing it.

### Batching and What Counts as One Call

| Resource | Contract-relevant limit |
|---|---|
| Composite (`/composite`) | Up to **25 subrequests**; the entire series counts as a single call toward API limits |
| Composite graphs | Up to **500** subrequests, and each graph either completes entirely or not at all |
| Composite tree (`/composite/tree`) | Up to 200 records across all trees, up to five records of different types, trees up to five levels deep; the entire request counts as a single call |
| sObject Collections | Up to **200 records** per request; the entire request counts as a single call. Available in API version 42.0 and later (46.0 and later for upsert) |
| API timeout | 10 minutes for REST and SOAP calls except query calls; for Composite resources the timeout applies to the **whole** composite request, not to each subrequest |

### OpenAPI 3.0 for sObjects REST API (Beta)

Salesforce provides a **beta OpenAPI 3.0 document generator** for the sObjects REST API (standard Create/Read/Update/Delete operations on SObjects). Access via:
```
GET /services/data/vXX.0/sobjects/{SObjectName}/describe/openapi3_0
```

**Critical limitation:** This beta feature generates OpenAPI specs only for **standard sObjects REST endpoints**. It does NOT cover:
- Custom Apex REST endpoints (`@RestResource` classes)
- Composite API resources (`/composite`, `/composite/batch`)
- Connect REST API (Chatter, Experience Cloud)

Custom Apex REST endpoints must have their request/response contracts hand-authored using OpenAPI 3.0 or another specification format. See `references/worked-examples.md` § 2 for a hand-authored excerpt.

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
3. Document the error: HTTP 403 `REQUEST_LIMIT_EXCEEDED` means daily limit is exhausted; a 429 from a fronting gateway is transient throttling. These have different recovery patterns: 403 requires waiting until the 24-hour window resets; a gateway throttle requires exponential backoff retry.
4. For bulk operations, recommend Bulk API 2.0 which has a separate request budget from the REST API limit.

### Pattern: The Contract Record as the Unit of Work

**When to use:** Whenever more than one endpoint or more than one direction exists — which is nearly always.

Write **one record per endpoint per direction**. An inbound order push and an outbound account-status read are two contracts even when the same partner and the same Named Credential are involved: they have different auth principals, different error surfaces and different idempotency keys. The filled record in `references/worked-examples.md` § 1 is the shape; `scripts/check_api_contract_documentation.py` is what tells you it is complete. Each finished record is a catalog row for `agents/integration-catalog-builder/AGENT.md` (§ Output Contract, "Catalog").

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Documenting standard CRUD API endpoints | Use sObjects OpenAPI beta + hand-authored supplement | Beta covers CRUD; manually document composite and custom endpoints |
| Documenting custom Apex REST endpoints | Hand-author OpenAPI 3.0 spec | Beta does not cover @RestResource endpoints |
| Consumer needs rate limit ceiling | Retrieve from /limits dynamically, not from documentation | Limit varies by org edition and license |
| Integration hitting REQUEST_LIMIT_EXCEEDED | Wait for 24-hour window reset; switch to Bulk API 2.0 for bulk ops | Daily limit resets on rolling 24-hour basis |
| Checking if API version is near retirement | Check api_rest_eol.htm with each seasonal release | EOL list is updated per Salesforce release cycle |
| Partner needs at-most-once write semantics | Upsert on an External Id field, not POST on a record Id | The external Id makes the retry idempotent; a repeated POST creates a duplicate |
| Partner sends 150 records per message | sObject Collections (200-record cap, one API call) rather than 150 single-row calls | Reduces the org allocation draw by two orders of magnitude for the same payload |
| Deciding which integration pattern the contract even describes | Read `standards/decision-trees/integration-pattern-selection.md` first | This skill documents the chosen pattern; it does not choose it |

---

## Recommended Workflow

1. **Inventory endpoints, one record per endpoint per direction.** Copy the skeleton from `templates/api-contract-documentation-template.md`; the filled equivalent is `references/worked-examples.md` § 1.
2. **Pin and justify the API version.** `GET /services/data/` (unauthenticated, does not count toward the allocation) lists every live version. Set `salesforce_api_version` and `eol_review_date`; cross-reference `integration/api-versioning-strategy` for the sunset policy the org has adopted.
3. **Fill the error contract before anything else.** One row per `errorCode` the partner can receive, each mapped to a partner-side action. Work from the status-code table in § Core Concepts and the catalogue in `references/worked-examples.md` § 3 — not from the HTTP status alone.
4. **State the idempotency key and the rate-limit clause.** Decide External Id upsert vs. record Id, and give this integration a request budget inside the org allocation. Read `references/gotchas.md` gotchas 1, 4, 5 and 6 before writing these two clauses.
5. **Hand-author the OpenAPI excerpt for every Apex REST resource.** `references/worked-examples.md` § 2 shows the shape including the Salesforce error schema; the class itself is `apex/apex-rest-services` territory, not this skill's.
6. **Lint the record.** `python3 scripts/check_api_contract_documentation.py --file <contract>.yaml` (or `--manifest-dir <dir>` for a set). It exits 1 on a missing owner or review date, an unmapped `errorCode`, an absent retry policy, or an out-of-set `direction`/`auth`/`status`.
7. **Publish, then hand off.** File the record where `agents/integration-catalog-builder/AGENT.md` § Output Contract expects its catalog row, and put `eol_review_date` on someone's calendar — see `references/worked-examples.md` § 5 for the deprecation notice you will eventually send.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] API version documented and checked against EOL list
- [ ] Daily API limit retrieved from /limits resource (not hardcoded)
- [ ] Error code catalog includes 300, 400, 401, 403 (REQUEST_LIMIT_EXCEEDED), 404, 409, 410, 500
- [ ] Every `errorCode` row states the partner-side action, not just the meaning
- [ ] Sforce-Limit-Info header monitoring pattern documented
- [ ] OpenAPI spec covers all endpoints (standard + hand-authored for Apex REST)
- [ ] Idempotency key named (External Id field API name, or an explicit "not idempotent" statement)
- [ ] Version upgrade SLA defined for integration team
- [ ] No hardcoded rate limit numbers that could become stale
- [ ] `check_api_contract_documentation.py` exits 0 against the finished record

---

## Salesforce-Specific Gotchas

1. **Fabricating specific numeric rate limits is dangerous** — API request limits are NOT a fixed universal number. They vary by org edition, add-on licenses, and Salesforce's adjustments. Never document a specific hardcoded number. Always reference the `/limits` resource or the developer limits quick reference cheatsheet.

2. **OpenAPI beta does not cover custom Apex REST** — Teams often assume the OpenAPI endpoint generates documentation for all their APIs. Custom `@RestResource` endpoints have no auto-generated spec. They must be hand-authored.

3. **SLA uptime commitments are not in developer docs** — API SLA percentages (uptime, latency) are in trust.salesforce.com and Order of Service agreements, not in the developer documentation. Do not document SLA percentages from developer docs — they do not exist there.

4. **REQUEST_LIMIT_EXCEEDED (403) means two different things** — it is returned both when the org's 24-hour allocation is exhausted and when the concurrent long-running-request limit is exceeded. The first needs the window to reset; the second clears as soon as in-flight requests finish. A contract that describes only the first leaves the partner retrying the wrong way.

The full set, with **What happens / When it occurs / How to avoid**, is in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API contract record (YAML) | One per endpoint per direction: auth, version, schema, error contract, idempotency, rate limit, owner, review date |
| API versioning policy document | Pinned version, support window, EOL check cadence, upgrade SLA |
| Rate limit specification | DailyApiRequests.Max from /limits, Sforce-Limit-Info monitoring pattern |
| Error code catalog | All HTTP status codes the integration must handle with recovery guidance |
| OpenAPI 3.0 spec | Generated for sObjects endpoints, hand-authored for Apex REST |
| Deprecation notice | Dated partner-facing notice tied to the version retirement schedule |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need a filled-in contract record, an OpenAPI excerpt, a contract test or a deprecation notice to copy and adapt |
| `references/gotchas.md` | Before writing the error, rate-limit, idempotency or versioning clause of any contract |
| `references/examples.md` | You want the two narrative walkthroughs — version retirement risk, and limit exhaustion during a nightly batch |
| `references/llm-anti-patterns.md` | Reviewing a contract document an AI assistant drafted |
| `references/well-architected.md` | Justifying the contract to an architecture review, or citing the sources behind a claim |

---

## Related Skills

- `apex/apex-rest-services` — Use for implementing custom Apex REST endpoints (@RestResource) — the implementation layer this skill documents
- `integration/rest-api-patterns` — Use for the request shapes themselves (composite, sObject Collections, query); this skill documents them, that skill designs them
- `integration/api-versioning-strategy` — Use for the org's sunset and contract-evolution policy that this skill's `salesforce_api_version` field must comply with
- `integration/named-credentials-setup` — Use for the endpoint and principal record this skill's `auth` field names
- `integration/api-governance-and-rate-limits` — Use for governing the shared 24-hour allocation across integrations, once more than one contract exists
- `integration/oauth-flows-and-connected-apps` — Use for OAuth flow selection and Connected App configuration for API consumers
- `integration/api-led-connectivity` — Use for designing the API layer architecture before documenting individual endpoints
- `admin/integration-pattern-selection` — Use before this skill, to choose the pattern the contract will describe
- `admin/integration-admin-connected-apps` — Use for the Connected App inventory the contract's `auth` field points into
- `data/external-id-strategy` — Use for choosing the External Id field that becomes the contract's idempotency key
- `devops/api-version-management` — Use for upgrading the API version on your own Apex, LWC and `sfdx-project.json`
