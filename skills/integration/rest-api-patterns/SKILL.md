---
name: rest-api-patterns
description: "Use when designing, implementing, or reviewing Salesforce REST API integration — covering CRUD operations on sObjects, SOQL-based queries, paginated result sets, Composite requests, Composite Batch, and sObject Tree. Triggers: 'Salesforce REST API', 'composite API', 'nextRecordsUrl', 'sObject Tree', 'REST CRUD', 'REST pagination', 'API limits', 'OAuth Bearer token'. NOT for loading or extracting large record volumes as a job — use integration/bulk-api-2-patterns. NOT for GraphQL queries or the GraphQL-vs-REST choice — use integration/graphql-api-patterns."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - rest-api
  - composite
  - soql
  - pagination
  - oauth
  - api-limits
triggers:
  - "how do I call the Salesforce REST API to create or update a record"
  - "which composite resource should I use for related record creation"
  - "how do I handle nextRecordsUrl when my SOQL query returns more than 2000 records"
  - "what is the difference between composite batch and composite requests in Salesforce"
  - "how do I stay within Salesforce API rate limits in an integration"
  - "how do I pass an OAuth Bearer token to the Salesforce REST API"
  - "how to use Salesforce REST API composite to create related records in one call"
  - "upsert records from an external system by external ID over REST"
  - "check remaining daily API calls before a large sync"
inputs:
  - "operation type: CRUD on single record, batch of independent requests, parent-child insert, or paginated query"
  - "authentication context: OAuth 2.0 access token availability and Connected App configuration"
  - "org edition and API version to determine daily API limit and feature availability"
  - "record volume per call to choose between REST Composite, sObject Tree, or Bulk API"
outputs:
  - "REST endpoint selection with correct base URL and HTTP verb"
  - "composite or sObject Tree request structure with referenceId wiring"
  - "pagination loop design using nextRecordsUrl"
  - "error handling strategy for 4xx/5xx and partial-failure responses"
  - "review findings for an existing REST integration"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# REST API Patterns

Use this skill when the integration task involves calling the Salesforce REST API to read, create, update, or delete records, or when you need to compose multiple REST operations efficiently. This skill covers the standard sObject resources, SOQL query resources, the Composite family of resources, and the pagination and error handling patterns that hold an integration together in production.

---

## Before Starting

Gather this context before working on anything in this domain:

- What OAuth 2.0 flow is in use and is a valid access token available? Every REST call requires `Authorization: Bearer <token>`.
- What Salesforce edition is the target org? The 24-hour API request allocation differs by edition: Developer Edition is 15,000; Enterprise, Unlimited, and Performance are 100,000 plus (number of licenses x calls per license type) plus purchased add-ons, where a Salesforce license adds 1,000 (Enterprise) or 5,000 (Unlimited and Performance). An earlier version of this skill gave Enterprise as "1,000 per license with a minimum of 1,000"; the limits quick reference does not support that.
- What API version should be used? Use a recent version (Summer '26 = v67.0). Salesforce supports each version for at least 3 years from first release and notifies customers at least a year before support ends; retired versions return `410 GONE`. The base URL is `/services/data/vXX.X/`.
- What is the record volume per call? Use REST Composite (≤ 25 subrequests), sObject Tree (≤ 200 records), or Bulk API 2.0 (> 2,000 records) accordingly.

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "How many records per run, and how often?" | REST suits interactive and modest volumes; Composite caps at 25 subrequests, sObject Tree at 200 records; larger loads belong to Bulk API 2.0 | The resource per volume band | An integration that stays inside its allocation as data grows |
| "Which edition and how many licenses, and what else consumes API calls?" | The 24-hour allocation is shared across all integrations in the org | A call budget per integration | No midday lockout because another job used the allocation |
| "Must related writes succeed or fail together?" | Composite `allOrNone` and sObject Tree are atomic; Composite Batch is not | The transaction boundary per operation | Partial failures that match the business rule |
| "Does the source system own a stable key for each record?" | External ID upsert avoids query-then-write races; a key that matches two records returns 300 | The External ID field and its uniqueness | Idempotent retries without duplicates |
| "How will the client handle 401, 403 `REQUEST_LIMIT_EXCEEDED`, 410, and per-subrequest errors?" | Each means a different action: re-authenticate, back off, upgrade the version, or fix one record | An error-handling table | Failures that recover or alert instead of losing data |
| "Will any call run longer than 20 seconds?" | More than 25 concurrent long-running calls (5 in Developer Edition) are refused; REST calls time out after 10 minutes | A concurrency cap and a timeout plan | Polling and exports that do not starve each other |

What a proper configuration adds over "just calling the endpoint": the resource matches the volume, the call budget is planned against the shared allocation, transaction boundaries are explicit, and every documented error has a defined response.

---

## Core Concepts

### Base URL and Versioning

All REST API resources are relative to the instance base URL and include the API version:

```
https://<instance>.salesforce.com/services/data/v63.0/
```

Always pin the version explicitly. Unversioned or pinned-to-old-version calls risk hitting deprecated behavior after a Salesforce release upgrade.

### Authentication: OAuth Bearer Token

Every REST request must include the access token in the HTTP `Authorization` header:

```
Authorization: Bearer <access_token>
```

The token is obtained via an OAuth 2.0 flow (client credentials, JWT bearer, web server, or device). The username-password flow is blocked by default in orgs created Summer '23 or later; see `integration/oauth-flows-and-connected-apps`. The app must carry the appropriate OAuth scope (`api` or a more targeted scope). Tokens expire; integrations must handle 401 responses and refresh or re-authenticate.

### sObject CRUD Resources

Standard create/read/update/delete operations target the `/sobjects/` resource family:

| Operation | HTTP Verb | Endpoint |
|---|---|---|
| Describe an sObject | GET | `/services/data/v63.0/sobjects/{SObject}/` |
| Read by ID | GET | `/services/data/v63.0/sobjects/{SObject}/{id}` |
| Read by External ID | GET | `/services/data/v63.0/sobjects/{SObject}/{ExternalIdField}/{value}` |
| Create | POST | `/services/data/v63.0/sobjects/{SObject}/` |
| Update | PATCH | `/services/data/v63.0/sobjects/{SObject}/{id}` |
| Upsert by External ID | PATCH | `/services/data/v63.0/sobjects/{SObject}/{ExternalIdField}/{value}` |
| Delete | DELETE | `/services/data/v63.0/sobjects/{SObject}/{id}` |

A successful create returns HTTP 201 with a JSON body containing `{"id": "...", "success": true, "errors": []}`. A successful update or delete returns HTTP 204 with no body.

### SOQL Query Resource and Pagination

Execute SOQL via the `/query/` resource:

```
GET /services/data/v63.0/query/?q=SELECT+Id%2CName+FROM+Account+LIMIT+200
```

If the result set is larger than the batch size (default 2,000 records; the `Sforce-Query-Options: batchSize=` header accepts 200 to 2,000, and the platform may return fewer for large records), the response includes `"done": false` and a `"nextRecordsUrl"` field:

```json
{
  "totalSize": 5800,
  "done": false,
  "nextRecordsUrl": "/services/data/v63.0/query/01gXXXXXXXXXXXX-2000",
  "records": [...]
}
```

Fetch subsequent pages by making a GET request to the absolute path given in `nextRecordsUrl` (prepend the instance host). Continue until `"done": true`. Do not attempt to reconstruct the query locator URL manually — use the value exactly as returned.

### Composite Resource

The `/composite/` resource executes up to 25 subrequests in a single HTTP round trip, and the whole series counts as one call toward API limits. Up to 5 of the 25 can be sObject Collections or query operations (Query and QueryAll). Composite graphs raise the subrequest limit to 500. Subrequests are ordered, run as the same user, and results from earlier subrequests can be referenced in later subrequests using `@{referenceId.fieldName}` syntax.

```json
{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "referenceId": "NewAccount",
      "body": { "Name": "Acme Corp" }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "referenceId": "NewContact",
      "body": {
        "LastName": "Smith",
        "AccountId": "@{NewAccount.id}"
      }
    }
  ]
}
```

When `allOrNone` is `true`, any single subrequest failure rolls back all subrequests in the call. When `false`, each subrequest result is independent.

### Composite Batch Resource

The `/composite/batch/` resource executes up to 25 independent subrequests. Unlike `/composite/`, subrequests cannot reference each other's results. With `haltOnError: true`, a 4xx or 5xx subrequest stops the batch and every later subrequest returns 412 `BATCH_PROCESSING_HALTED`, while the top-level response is still 200 with `hasErrors: true`.

Use Composite Batch when:
- Requests are logically independent (no parent-child ID wiring)
- You want to reduce HTTP round trips for unrelated operations

### sObject Tree Resource

The `/composite/tree/{SObject}/` resource inserts up to 200 records in a single call, including parent-child related record trees:

```
POST /services/data/v63.0/composite/tree/Account/
```

Up to five levels of nesting and up to five different record types are supported. If any record fails, the entire request fails and the response names only the failing reference ID. Records across all trees count toward the 200-record limit, the request counts as one API call, and triggers and flows fire separately for each level (all root records, then all second-level records of the same type, and so on).

### Error Response Format

When a request fails, Salesforce returns an array of error objects:

```json
[
  {
    "message": "Required fields are missing: [Name]",
    "errorCode": "REQUIRED_FIELD_MISSING",
    "fields": ["Name"]
  }
]
```

Composite responses embed a `httpStatusCode` per subrequest alongside the error array. Always inspect individual subrequest bodies when using Composite or Composite Batch — an HTTP 200 outer response does not mean all subrequests succeeded.

---

## Common Patterns

### Composite Insert: Account with Related Contact

**When to use:** You need to create a parent Account and a child Contact in the same transaction without two round trips and without knowing the Account ID in advance.

**How it works:** Use `/composite/` with `allOrNone: true`. Set a `referenceId` on the Account subrequest and reference it in the Contact subrequest using `@{refId.id}`. The platform resolves the reference server-side before executing the Contact insert.

**Why not the alternative:** Two separate REST calls require the caller to persist the Account ID between calls and handle partial failure (Account created, Contact failed) with compensating logic. The composite approach keeps both in a single atomic transaction.

### Paginated SOQL Query Loop

**When to use:** Any query against a large data set where the result count may exceed 2,000 records.

**How it works:** Issue the initial `/query/` request. If `done` is `false`, read `nextRecordsUrl` from the response and issue a GET to that URL (prefixed with the instance hostname). Repeat until `done` is `true`. Buffer or stream records per page — do not assume all records fit in memory.

**Why not the alternative:** Setting an arbitrarily large `LIMIT` in SOQL does not bypass the batch size; the API still paginates. Ignoring `nextRecordsUrl` silently drops records — a hard-to-detect data integrity problem.

### Upsert by External ID

**When to use:** An external system owns a record identifier and you want to create-or-update without first querying for the Salesforce ID.

**How it works:** PATCH to `/sobjects/{SObject}/{ExternalIdField}/{value}`. If no record with that external ID exists, Salesforce creates it (HTTP 201, `"created": true`). If one exists, Salesforce updates it (HTTP 200 with `"created": false` in API 46.0 and later; 204 with no body in 45.0 and earlier). If the value matches more than one record, the API returns 300 with the matching records and changes nothing. Add `?updateOnly=true` to update without ever creating. The External ID field must be defined on the object.

**Why not the alternative:** A query-then-insert-or-update pattern doubles round trips and introduces a race condition between the read and the write.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single record CRUD | `/sobjects/{SObject}/` | Simplest, no overhead |
| Create parent + children with ID wiring | `/composite/` with `allOrNone: true` | Atomic, cross-reference support |
| Multiple independent updates in one call | `/composite/batch/` | Reduces round trips without requiring ordering |
| Bulk parent-child tree insert (≤ 200 records) | `/composite/tree/{SObject}/` | Atomic tree, fewer API calls |
| > 2,000 record inserts or bulk queries | Bulk API 2.0 | REST API is not designed for large-volume jobs |
| Query result set larger than 2,000 records | SOQL + `nextRecordsUrl` loop | Platform-managed pagination, no manual cursor math |
| Create-or-update with external system key | Upsert via External ID PATCH | No pre-query needed, atomic |

---


## Recommended Workflow

1. Size the job: records per run, runs per day, and the org's 24-hour allocation (`GET /services/data/vXX.X/limits/` or the `Sforce-Limit-Info` response header); move anything over a few thousand records per run to Bulk API 2.0.
2. Pick the resource per operation from the Decision Guidance table, and decide each transaction boundary (`allOrNone`, sObject Tree, or independent batch).
3. Pin one recent API version in configuration, not in code, and record its retirement horizon.
4. Implement the client: OAuth token handling (401 re-auth), pagination with `nextRecordsUrl` until `done`, per-subrequest status inspection, and the documented error codes (403 `REQUEST_LIMIT_EXCEEDED`, 300 for ambiguous external IDs, 410 for retired versions, 412 for halted batches).
5. Cap concurrency so no more than 25 calls (5 in Developer Edition) run longer than 20 seconds at once, and keep composite requests well under the 10-minute timeout. Worked requests are in [`references/request-examples.md`](references/request-examples.md).
6. Run `python3 skills/integration/rest-api-patterns/scripts/check_rest_api_patterns.py --manifest-dir <integration source>` and load-test against a sandbox before go-live.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] API version is pinned to a recent version (v60.0+) in all endpoint URLs.
- [ ] `Authorization: Bearer <token>` is present on every request; 401 is handled with refresh logic.
- [ ] Paginated queries check `done` flag and follow `nextRecordsUrl` until `true`.
- [ ] Composite requests inspect per-subrequest `httpStatusCode` — outer HTTP 200 is not sufficient.
- [ ] `allOrNone` setting on Composite requests is an explicit architectural choice, not a default.
- [ ] Record volume per call is within limits: ≤ 25 subrequests for Composite/Batch, ≤ 200 records for sObject Tree.
- [ ] Daily API limit is estimated against the org edition and load tested before go-live.
- [ ] Error responses parse the `[{message, errorCode, fields}]` array; generic string matching on HTTP status is not enough.
- [ ] External ID fields used for upserts are defined, indexed, and not shared across integration systems.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HTTP 200 outer response masks subrequest failures in Composite** — When using `/composite/` or `/composite/batch/`, the outer HTTP response code is 200 even if individual subrequests return 4xx. Integrations that only check the outer status silently discard errors.

2. **`nextRecordsUrl` is not a full URL — it is a path** — The value returned in `nextRecordsUrl` is a relative path like `/services/data/v63.0/query/01gXXX-2000`. You must prepend the instance hostname. Treating it as a complete URL or re-constructing it from the query locator ID causes 404s or incorrect page fetches.

3. **API version retirement is permanent**: Salesforce supports each version for at least 3 years and gives at least a year's notice; requests to a retired version get `410 GONE`. Versions 7.0 through 30.0 are retired as of Summer '25. Keep the version in configuration and upgrade on a schedule.

4. **Concurrent API request limits are separate from daily limits**: Production orgs and sandboxes allow 25 concurrent requests that run 20 seconds or longer (Developer Edition and trial orgs allow 5); further long-running requests get `REQUEST_LIMIT_EXCEEDED`. Polling integrations and exports that hold long calls open can hit this ceiling while the daily allocation looks healthy.

5. **sObject Tree is all-or-nothing at 200 records** — Unlike Composite with `allOrNone: false`, the sObject Tree resource does not support partial success. One invalid record in the tree rolls back the entire payload. Validate records client-side before sending large trees.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Endpoint selection guide | Correct REST resource URL, HTTP verb, and request body shape for the requested operation |
| Composite request scaffold | JSON request body with subrequests, referenceIds, and `allOrNone` setting |
| Pagination loop design | Logic for following `nextRecordsUrl` until `done: true` with record buffering |
| Error handling strategy | Per-subrequest error inspection pattern and 401 refresh logic |
| API limit estimate | Daily and concurrent limit projection based on org edition and call volume |

---

## Related Skills

- `integration/graphql-api-patterns` — use when the consumer needs flexible field selection from a single endpoint rather than fixed CRUD resources.
- `integration/oauth-flows-and-connected-apps` — use when the authentication setup, Connected App scoping, or token refresh flow is the actual blocker.
- `apex/apex-rest-services` — use when the org needs a custom command API exposed over REST, not a caller consuming the standard REST API.
- `data/bulk-api-and-large-data-loads` — use when record volumes exceed 2,000 per operation and Bulk API 2.0 async job patterns are needed.
