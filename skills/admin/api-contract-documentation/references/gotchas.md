# Gotchas — API Contract Documentation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: API Rate Limits Are Not a Fixed Published Number

**What happens:** Teams document a specific numeric daily API limit (e.g., "50,000 calls/day") sourced from general knowledge or old documentation. The actual limit depends on org edition, licenses, and Salesforce adjustments.

**Impact:** Documentation becomes stale or incorrect, leading consumer teams to design integrations around wrong limits.

**How to avoid:** Always retrieve the actual limit dynamically from `GET /services/data/vXX.0/limits` and reference the Salesforce Developer Limits Quick Reference cheatsheet. Never document a hardcoded number without sourcing it from the org's actual `/limits` response.

---

## Gotcha 2: OpenAPI Beta Does Not Cover Custom Apex REST Endpoints

**What happens:** Teams use the Salesforce sObjects OpenAPI beta endpoint to generate documentation and assume it covers all their APIs, including custom `@RestResource` Apex classes.

**Impact:** Custom Apex REST endpoints remain undocumented because the beta generator only covers sObjects CRUD endpoints.

**How to avoid:** The OpenAPI beta covers standard sObjects REST API only. All custom Apex REST endpoints must be hand-authored in OpenAPI 3.0 or another specification format.

---

## Gotcha 3: REQUEST_LIMIT_EXCEEDED (403) and HTTP 429 Have Different Recovery Paths

**What happens:** Integrations treat HTTP 403 REQUEST_LIMIT_EXCEEDED identically to HTTP 429 transient rate throttling, implementing the same exponential backoff retry.

**Impact:** Immediate retry on 403 fails repeatedly because the daily limit is not a transient state — it will not recover until the 24-hour rolling window resets.

**How to avoid:** HTTP 403 REQUEST_LIMIT_EXCEEDED requires waiting for the 24-hour window to reset (check the Sforce-Limit-Info header to estimate reset timing). HTTP 429 is transient throttling that responds to exponential backoff. Document these as separate error conditions with separate recovery procedures.

**A refinement on the 429 half of this gotcha:** the REST API Developer Guide's Status Codes and Error Responses table lists 300, 304, 400, 401, 403, 404, 405, 409, 410, 412, 414, 415, 420, 428, 431, 500, 502 and 503 — but **not 429**. Where a 429 is observed it is almost always a gateway, proxy or middleware tier in front of Salesforce, not the platform. Attribute it to that tier in the contract. *UNVERIFIED (2026-09-04): the REST API Developer Guide available here does not document 429 as a REST API status code; whether any Salesforce edge tier emits it is not established by these guides.*

---

## Gotcha 4: The Same errorCode Covers Two Unrelated Limit Conditions

**What happens:** A contract documents `REQUEST_LIMIT_EXCEEDED` as "the daily allocation is exhausted" and gives the partner one recovery: wait for the window. But the same exception code is returned when the **concurrent long-running request** limit is exceeded — a completely different condition that clears in seconds.

**When it occurs:** The Developer Limits Quick Reference (Concurrent API Request Limits) caps inbound requests lasting **20 seconds or longer** at 5 for Developer Edition and Trial orgs, and 25 for production orgs and sandboxes. There is no limit on requests shorter than 20 seconds. Exceeding the cap returns `REQUEST_LIMIT_EXCEEDED`, and new concurrent requests are refused until the count drops below the limit. Long SOQL-heavy reads and Apex REST resources that do real work are the usual triggers, and they cluster — a slow dependency makes every in-flight request long-running at once.

**How to avoid:** Make the partner branch on the `Sforce-Limit-Info` header rather than on the code alone. If `api-usage` is at or near the ceiling, the allocation is genuinely gone and only the rolling window helps. If `api-usage` has headroom, it is the concurrency cap: back off for tens of seconds and resume at reduced parallelism. Write both branches into the error contract row, as `worked-examples.md` § 1.1 does.

---

## Gotcha 5: The Error Body Is an Array, Not an Object

**What happens:** A consumer's client is generated (or hand-written) against an error schema modelled as a single object — `{ "message": ..., "errorCode": ... }`. Salesforce returns a JSON **array** of error objects, each with `message`, `errorCode`, and optionally `fields`.

**When it occurs:** On every error response from the REST API. The guide's own examples show it: a bad Id returns `[{ "fields": ["Id"], "message": "...", "errorCode": "MALFORMED_ID" }]`, and a misspelled object name returns `[{ "message": "The requested resource does not exist", "errorCode": "NOT_FOUND" }]`. It is a list because a single request can fail for more than one reason.

**How to avoid:** Model the error type as `array` in the OpenAPI document (see the `SalesforceErrors` schema in `worked-examples.md` § 2) and make the partner's handler iterate. A client that deserialises the first element only will still work for most single-cause failures, which is what makes this bug survive UAT and surface in production on a multi-field validation failure.

---

## Gotcha 6: An External Id Upsert That Matches Twice Returns 300 and Writes Nothing

**What happens:** The integration upserts on an External Id field and gets HTTP 300 back. The partner's retry logic, which treats any 3xx as a redirect or any non-2xx as retryable, replays the request — forever, because the condition is data, not transport.

**When it occurs:** The REST API Developer Guide's upsert semantics are three-way: if the external Id is not matched, a new record is created; if it is matched once, the record is updated; **if it is matched multiple times, a 300 error is reported and the record is neither created nor updated**. The status-code table describes 300 as "the value returned when an external ID exists in more than one record", with the list of matching records in the body. Duplicate external Id values arise from a data migration that loaded the field before it was marked Unique, or from a merge that left two survivors.

**How to avoid:** Mark 300 explicitly non-retryable in the error contract, park the message, and give the partner a named runbook: de-duplicate the matching Salesforce records, then replay. If the partner must never create records, add `?updateOnly=true` to the URL so an unmatched key fails loudly instead of silently introducing a record. Choosing the External Id field itself is `data/external-id-strategy`.

---

## Gotcha 7: Batching Resources Count as One Call but Have Hard Structural Caps

**What happens:** A contract promises "we batch, so allocation is not a concern", and the partner builds a client that puts 300 operations in one composite request. The request is rejected — not on allocation, on structure.

**When it occurs:** Composite and Collections resources do collapse into a single call: the Composite resource executes a series of REST API requests where "the entire series of requests counts as a single call toward your API limits", and the same is stated for sObject Collections and Composite Tree. But each carries its own cap: **regular composite requests are limited to 25 subrequests**, composite graphs raise that to **500**, **sObject Collections handles up to 200 records** per request (available in API version 42.0 and later; 46.0 and later for upsert), and Composite Tree allows up to 200 records across all trees, up to five records of different types, five levels deep. Separately, the 10-minute REST/SOAP call timeout applies **to the entire composite request, not to each subrequest** — so 25 subrequests each taking 30 seconds exceed the timeout that none of them individually approaches.

**How to avoid:** Put the cap in the schema, not the prose — `maxItems: 200` on the array, as in `worked-examples.md` § 2 — so the partner's generated client enforces it. Document the allocation benefit and the structural cap in the same clause; they are the two halves of one fact.

---

## Gotcha 8: sObject Collections Returns 200 OK Even When Rows Failed

**What happens:** A batch upsert is monitored on HTTP status. Every response is 200, the dashboard is green, and rows have been silently dropping for weeks.

**When it occurs:** For sObject Collections, the guide is explicit: if the request is not well formed the API returns 400 Bad Request, but **if the request is well formed the API returns 200 OK** — per-item outcomes then live in the response, where each item carries a `success` flag and an `errors` array. A well-formed request containing 200 rows of which 199 failed validation is still a 200.

**How to avoid:** Never let a batch contract's success criterion be the HTTP status. Require per-row reconciliation: the partner counts `success: true` items against items sent and reconciles the difference. Decide `allOrNone` deliberately and record the decision — with `allOrNone: true` the whole request rolls back on any error, which turns a partial-success problem into an all-or-nothing one, and that is a business decision rather than a technical default.

---

## Gotcha 9: A Retired API Version Returns 410 GONE, and the Only Warning Is a Header Most Clients Discard

**What happens:** An integration that has run untouched for years starts returning 410 on every call, overnight, with no deploy on either side.

**When it occurs:** Salesforce supports each API version for a minimum of 3 years from first release and notifies customers at least 1 year before support ends. Once a version is retired, "if you request any resource or use an operation from a retired API version, REST API returns the 410:GONE error code" — there is no fallback to a newer version. As published in the Summer '26 guide, versions 31.0 through 66.0 are supported; **21.0 through 30.0 are retired and unavailable as of Summer '25**; 7.0 through 20.0 as of Summer '22. Before retirement, a call on a deprecated version returns a `Warning` response header whose `warningCode` is **299**, carrying text naming the release in which the version will be removed. Most HTTP clients never surface response headers they were not told to read, so the year of warning is delivered to nobody.

**How to avoid:** Two mechanical steps, neither of which is "remember". First, log the `Warning` header alongside `Sforce-Limit-Info` on every response and alert on `299`. Second, use the **API Total Usage** event type to identify which callers are still on old versions — it answers "who would break" without asking each team. Then put the answer in the contract's `eol_review_date` with an owner's name against it.

---

## Gotcha 10: Two Apex REST Classes Can Claim the Same URL, and the Loser Is Decided by Save Order

**What happens:** A documented endpoint starts returning a different response shape than the contract says, after an unrelated class was deployed.

**When it occurs:** The Apex Developer Guide states that the URL patterns `URLpattern` and `URLpattern/*` **match the same URL**, and that if one class has a `urlMapping` of `URLpattern` while another has `URLpattern/*`, a REST request for that pattern "resolves to the class that was saved first". Nothing warns at compile time or deploy time. Related sharp edges from the same section: a single `@RestResource` class cannot have two methods annotated with the same HTTP request method; methods annotated `@HttpGet` or `@HttpDelete` must take no parameters; sending XML for a parameter type XML cannot represent returns **HTTP 415**, and requesting XML for such a return type returns **HTTP 406**; duplicate parameter names in the body return **HTTP 400**. For classes in a managed package, the namespace must appear in the REST URL — `/services/apexrest/packageNamespace/MyMethod/`.

**How to avoid:** Record the exact `urlMapping` string in the contract record's `endpoint`, and treat the mapping as owned by the contract: a review of any new `@RestResource` class checks its mapping against the documented endpoints. Document 406 and 415 in the error contract for any resource that advertises XML at all — most should advertise JSON only, which removes both codes from the surface.

---

## Gotcha 11: Changing a Named Credential's URL Silently Retargets Every Documented Endpoint

**What happens:** The contract documents an outbound endpoint as a partner URL. Someone repoints the Named Credential — to a new partner host, a migrated region, a temporary stub — and every consumer of that credential follows, while the documentation still names the old host.

**When it occurs:** Apex resolves the endpoint at runtime from the `callout:<NamedCredential>/<path>` form (the Apex Developer Guide's Named Credential callout examples use exactly this shape, e.g. `'callout:WeatherAPI/current'`). The credential name in code never changes when the URL behind it does, so no code diff records the change and no test that stubs the callout notices.

**How to avoid:** Document the *credential name plus path* as the contract's `endpoint`, and the resolved host as a separately dated field — as `worked-examples.md` § 1.2 does with `endpoint: "callout:Northwind_OMS/v1/..."` and a `named_credential` reference. Then the Named Credential record, not the document, is the single source of the host, and `agents/integration-catalog-builder/AGENT.md` is the thing that reconciles the two. A contract that hardcodes the host is guaranteed to drift; a contract that names the credential can only drift if the credential is repointed, which is a change someone had to make in Setup.
