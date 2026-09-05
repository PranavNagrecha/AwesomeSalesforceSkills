# Well-Architected Notes — API Contract Documentation

## Relevant Pillars

### Reliability
API contract documentation is a reliability prerequisite — consumer teams cannot build reliable integrations without knowing versioning policy, rate limits, and error handling requirements. The EOL check cadence and rate limit monitoring patterns in this skill directly support integration reliability.

The reliability argument is sharper than "documentation is good". Three of the failure modes in `gotchas.md` are *invisible until they are total*: a retired API version returns `410 GONE` with no degraded mode, a duplicate External Id returns `300` and writes nothing, and an sObject Collections batch returns `200 OK` while dropping rows. None of the three is detectable from the HTTP status alone, and all three are decided by a field in the contract record — `eol_review_date`, `idempotency.key_strategy`, and the `allOrNone` decision respectively. The contract is the control, not the description.

### Security
Documenting authentication requirements and error code meanings prevents consumer teams from implementing incorrect error handling that might expose sensitive data (e.g., treating 401 as a retriable error without re-authentication).

The `404 / NOT_FOUND` row carries a specific security property: the REST API Developer Guide notes that a 404 can mean either a bad URI **or** a sharing issue, and it deliberately does not distinguish them. That ambiguity is a feature — it prevents a caller from enumerating record existence through access failures — and a contract that "helpfully" tells the partner "404 means the record does not exist" both misleads them and misdescribes the platform's access model.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Change Management | API versioning policy documentation with upgrade SLA prevents surprise breaking changes |
| Observability | Sforce-Limit-Info monitoring pattern provides visibility into API consumption trends; the `Warning: 299` header and the API Total Usage event type cover the version-retirement dimension the limit header does not |
| Documentation Standards | OpenAPI 3.0 as the documentation format ensures machine-readable, tooling-compatible specs |
| Resilience | The `retryable` flag on every error-contract row is what makes a partner's retry loop safe; combined with an External Id upsert it makes redelivery idempotent by construction |
| Cost / capacity | The 24-hour API request allocation is org-wide, so a per-integration budget inside that allocation is a capacity control, not paperwork |

## Cross-Skill References

- `apex/apex-rest-services` — Use for implementing custom Apex REST endpoints that this skill documents
- `integration/rest-api-patterns` — Use for the request shapes (composite, sObject Collections) whose caps this skill writes into the schema
- `integration/api-versioning-strategy` — Use for the org's sunset policy that sets this skill's notice period
- `integration/api-led-connectivity` — Use for designing the API layer architecture before documenting individual endpoints
- `integration/api-governance-and-rate-limits` — Use for allocating the shared 24-hour budget across contracts
- `integration/named-credentials-setup` — Use for the endpoint and principal record behind an outbound contract
- `integration/oauth-flows-and-connected-apps` — Use for the OAuth flow setup referenced in API authentication documentation
- `admin/integration-pattern-selection` — Use before this skill, to choose the pattern the contract describes
- `admin/integration-admin-connected-apps` — Use for the Connected App inventory the contract's `auth` block points into
- `data/external-id-strategy` — Use for selecting the External Id field that becomes the idempotency key

## Official Sources Used

Salesforce documentation, as extracted from the Summer '26 PDFs:

- Salesforce REST API Developer Guide — **Status Codes and Error Responses**: the 300 / 304 / 400 / 401 / 403 / 404 / 405 / 409 / 410 / 412 / 414 / 415 / 420 / 428 / 431 / 500 / 502 / 503 table, the 16,384-byte URI limit, and the `[{ "message", "errorCode", "fields" }]` array shape of an error body (SKILL.md § The Error Contract; gotchas 3 and 5) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce REST API Developer Guide — **API End-of-Life Policy**: minimum 3-year support from first release, at least 1 year of notice, versions 31.0–66.0 supported, 21.0–30.0 retired as of Summer '25, 7.0–20.0 as of Summer '22, `410:GONE` on a retired version, and the API Total Usage event type for identifying old callers (SKILL.md § Salesforce API Versioning Policy; gotcha 9; worked-examples § 5) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/api_rest_eol.htm
- Salesforce REST API Developer Guide — **Warning Header**: `warningCode` 299 for deprecated API versions, with the removal release named in the message (gotcha 9) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce REST API Developer Guide — **Limit Info Header**: `Sforce-Limit-Info` returned on every request except the Versions URI, the `api-usage=10018/100000; api-bursts=1/750` field format, and the note that Functions calls draw on a separate allocation (SKILL.md § Rate Limits; examples § 2) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm
- Salesforce REST API Developer Guide — **Insert or Update (Upsert) a Record Using an External ID**: the three-way match semantics, HTTP 300 when the external Id matches multiple records, the `updateOnly` parameter, and `created` appearing in responses only in API version 46.0 and later (gotcha 6; worked-examples § 1.1 and § 1.3) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce REST API Developer Guide — **Composite, Composite Graphs, Composite Tree and sObject Collections**: 25-subrequest cap on regular composite requests, 500 on graphs, 200 records on sObject Collections and Composite Tree, "the entire series of requests counts as a single call toward your API limits", and the rule that a well-formed Collections request returns 200 OK with per-item `success` / `errors` (SKILL.md § Batching; gotchas 7 and 8) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce REST API Developer Guide — **Versions resource / Get the Salesforce Version**: the unauthenticated `GET /services/data/` call and its `label` / `url` / `version` response array (examples § 1) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce Apex Developer Guide — **Apex REST Annotations, Apex REST Methods, Apex REST Method Considerations, Request and Response Data Considerations**: `RestContext.request` / `RestContext.response`, the rule that `URLpattern` and `URLpattern/*` match the same URL and resolve to the class saved first, one HTTP-method annotation per class, no parameters on `@HttpGet` / `@HttpDelete`, HTTP 400 on duplicate parameter names, HTTP 415 / 406 for XML type mismatches, and the managed-package namespace in the REST URL (gotcha 10; worked-examples § 4) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Developer Limits and Allocations Quick Reference — **Total API Request Allocations, Concurrent API Request Limits, API Timeout Limits**: the per-org 24-hour allocation and its `100,000 + (licences × calls per licence) + add-ons` formula, 15,000 for Developer Edition, the 5 / 25 concurrent cap on requests of 20 seconds or longer also returning `REQUEST_LIMIT_EXCEEDED`, and the 10-minute call timeout that applies to a composite request as a whole (SKILL.md § Rate Limits and § Batching; gotchas 4 and 7) — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/
- OpenAPI 3.0 for sObjects REST API (Beta) — the `GET /services/data/vXX.0/sobjects/{SObjectName}/describe/openapi3_0` generator and its scope limitation to standard sObjects CRUD (SKILL.md § OpenAPI 3.0; gotcha 2; worked-examples § 2) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/openapi_beta.htm

Repo standards this skill's artefacts are shaped to:

- `agents/integration-catalog-builder/AGENT.md` § Output Contract ("Catalog — table: endpoint, type, principal, auth flow, cert expiry, usage count") — the fields a finished contract record must carry so it can become a catalog row without restatement (worked-examples § 6)
- `standards/decision-trees/integration-pattern-selection.md` — chooses REST vs. Bulk vs. Platform Events vs. Pub/Sub *before* this skill documents the result; cited rather than restated (SKILL.md § Decision Guidance)
- `agents/_shared/AGENT_CONTRACT.md` § Citations — the rule that every consumed skill and template is cited by resolvable path, which is why the contract record carries explicit `references:` and `consumed_by:` keys the checker validates
