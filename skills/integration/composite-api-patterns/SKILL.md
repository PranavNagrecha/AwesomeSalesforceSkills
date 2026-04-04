---
name: composite-api-patterns
description: "Use when designing, implementing, or troubleshooting Salesforce Composite API requests — covering the /composite/ resource with cross-subrequest referenceId wiring, /composite/sobjects/ bulk CRUD, /composite/tree/ hierarchical inserts, and /composite/batch/ independent subrequest bundling. Triggers: 'composite API', 'sObject Tree', 'sObject Collection', 'composite batch', 'subrequest', 'referenceId', 'allOrNone', 'parent child insert one call', 'bulk CRUD same object', 'batch API requests'. NOT for single REST API calls, Bulk API 2.0 large-data-load jobs, GraphQL API queries, Metadata API deployments, or custom Apex REST endpoints."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - composite-api
  - sobject-collection
  - sobject-tree
  - composite-batch
  - subrequest
  - referenceId
  - allOrNone
  - rest-api
  - integration
triggers:
  - "how do I create a parent and child record in one Salesforce API call without multiple round trips"
  - "which composite API resource should I use when subrequests depend on each other's results"
  - "how do I bulk upsert 150 records of the same object type in a single Salesforce REST call"
  - "what is the difference between composite batch and composite in Salesforce REST API"
  - "how do I use referenceId to wire an Account ID into a Contact insert in the same request"
  - "how do I insert an Account with related Contacts in one call using sObject Tree"
inputs:
  - "operation type: dependent parent-child creation, bulk CRUD on same object, hierarchical insert, or bundled independent requests"
  - "record volume per call to determine which Composite resource to use"
  - "dependency requirements: do subrequests reference each other's results?"
  - "atomicity requirements: should all-or-none rollback apply?"
  - "org API version (Spring '25 = v63.0)"
outputs:
  - "Composite resource selection (composite, sobjects, tree, batch) with justification"
  - "Complete JSON request body with subrequests, referenceId chains, and allOrNone flag"
  - "Error handling strategy for per-subrequest failure inspection"
  - "Governor limit impact assessment for the chosen resource"
  - "Review findings for an existing Composite API integration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Composite API Patterns

Use this skill when an integration needs to group multiple Salesforce REST API operations into a single HTTP round trip. The Composite family of resources — `/composite/`, `/composite/sobjects/`, `/composite/tree/`, and `/composite/batch/` — each serve distinct use cases and carry distinct limits. Choosing the wrong resource wastes API calls, violates atomicity requirements, or silently drops errors.

This skill focuses on the four Composite resources, their request/response shapes, limit boundaries, dependency management via referenceId, and the `allOrNone` flag behavior. It does not cover single-resource REST CRUD, SOQL pagination, Bulk API 2.0, or GraphQL.

---

## Before Starting

Gather this context before working on anything in this domain:

- What Salesforce API version is in use? Spring '25 = v63.0. Always pin the version in all endpoint URLs.
- Do any subrequests depend on results from earlier subrequests? If yes, only `/composite/` supports cross-subrequest referenceId resolution. `/composite/batch/` does not.
- How many records are involved? `/composite/` and `/composite/batch/` each support up to 25 subrequests. `/composite/sobjects/` supports up to 200 records per call. `/composite/tree/` supports up to 200 records across up to 5 nesting levels.
- Is atomicity required? `/composite/` with `allOrNone: true` and `/composite/tree/` are always atomic. `/composite/` with `allOrNone: false` and `/composite/batch/` allow partial success and require per-subrequest response inspection.
- What is the DML budget? Governor limits still apply per subrequest. 25 subrequests each touching 200 records = 5,000 DML rows — this can hit org limits. Composite counts as one API call total toward the daily limit.

---

## Core Concepts

### The Four Composite Resources

Salesforce exposes four distinct resources under the `/composite/` path. They are not interchangeable.

**`/composite/` — Ordered, dependent subrequests**
```
POST /services/data/v63.0/composite
```
Executes up to 25 subrequests in sequence within a single HTTP call. The key differentiator: results from earlier subrequests can be referenced in later subrequests using `@{referenceId.fieldName}` syntax. Salesforce resolves references server-side before executing the dependent subrequest. Supports `allOrNone: true` (atomic rollback on any failure) or `allOrNone: false` (partial success, each result independent).

**`/composite/sobjects/` — Bulk CRUD on same-type records**
```
POST   /services/data/v63.0/composite/sobjects          (create up to 200)
PATCH  /services/data/v63.0/composite/sobjects          (update up to 200)
DELETE /services/data/v63.0/composite/sobjects?ids=...  (delete up to 200)
GET    /services/data/v63.0/composite/sobjects?ids=...  (read up to 2000)
```
The sObject Collection resource processes up to 200 records of a uniform type in a single call. Records are not required to be the same object type for reads, but DML operations (create, update, delete) require uniform type. Supports `allOrNone` flag. No cross-record referencing.

**`/composite/tree/{SObject}/` — Hierarchical parent-child inserts**
```
POST /services/data/v63.0/composite/tree/Account/
```
Inserts a parent record with its related child records in one atomic call. Up to 200 total records across up to 5 nesting levels. Always atomic — no partial success. All records in the tree use temporary `referenceId` labels for response correlation, but child records reference parents via the `attributes.referenceId` + nested structure, not the `@{}` syntax used in `/composite/`.

**`/composite/batch/` — Bundled independent subrequests**
```
POST /services/data/v63.0/composite/batch
```
Executes up to 25 subrequests that cannot reference each other. Each subrequest is a complete, standalone REST call. Results are independent. The `haltOnError` flag stops processing on the first failure but does not roll back completed subrequests. Use when you want to reduce round trips for logically unrelated operations.

### referenceId and Cross-Subrequest Dependency

In `/composite/` requests, each subrequest carries a `referenceId` string. Later subrequests in the same call can embed `@{referenceId.fieldPath}` anywhere in their request body or URL. Field paths follow dot notation for nested fields.

```json
"body": {
  "AccountId": "@{NewAccount.id}"
}
```

`referenceId` values are case-sensitive. A typo in the reference token causes the subrequest to receive a literal string rather than the resolved value, which typically results in a validation error that is reported in the per-subrequest response body — not in the outer HTTP status.

References can also appear in URL segments for GET subrequests:
```
"url": "/services/data/v63.0/sobjects/Contact/@{NewContact.id}"
```

### allOrNone Flag and Error Behavior

The `allOrNone` flag controls atomicity:

- **`allOrNone: true`** — If any subrequest fails, all subrequests in the call are rolled back. The response still returns HTTP 200. Failed subrequests report their error in the per-subrequest `body` with an HTTP status code in the `httpStatusCode` field. Successful subrequests that were rolled back show `httpStatusCode: 400` with `PROCESSING_HALTED` errorCode.
- **`allOrNone: false`** — Each subrequest executes independently. A failure in one does not affect others. You must inspect every subrequest response in `compositeResponse[]` to determine which succeeded and which failed. The outer HTTP response is always 200.

For `/composite/tree/`, atomicity is always enforced — there is no `allOrNone` option. One invalid record rolls back the entire tree.

### Governor Limits and API Call Accounting

The entire Composite request counts as **one API call** toward the org's daily REST API limit. However, each subrequest's DML operations count individually against DML governor limits and row limits. Key limits to track:

- 25 subrequests maximum per `/composite/` or `/composite/batch/` call
- 200 records maximum per `/composite/sobjects/` DML call
- 200 total records maximum per `/composite/tree/` call, up to 5 levels deep
- Per-transaction DML row limit (150 statements) still applies cumulatively across subrequests
- CPU time and heap limits still apply per subrequest
- Callouts within subrequests are not permitted (Apex trigger callouts from subrequest-triggered DML follow normal Apex rules)

---

## Common Patterns

### Pattern 1: Create Account + Related Records in One Atomic Call

**When to use:** You need to create a parent Account and one or more child Contacts and/or Opportunities in a single transaction without knowing the Account ID in advance and without separate round trips.

**How it works:** Use `/composite/` with `allOrNone: true`. Assign a `referenceId` to the Account subrequest and reference `@{refId.id}` in each child subrequest's relationship field. Order subrequests so the parent appears before any child that references it.

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
        "FirstName": "Jane",
        "AccountId": "@{NewAccount.id}"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Opportunity/",
      "referenceId": "NewOpportunity",
      "body": {
        "Name": "Acme Corp — Q3 Deal",
        "AccountId": "@{NewAccount.id}",
        "StageName": "Prospecting",
        "CloseDate": "2025-12-31"
      }
    }
  ]
}
```

**Why not the alternative:** Three separate REST calls require the caller to store the Account ID between calls, manage partial failure compensation (Account inserted, Opportunity failed — now you have an orphaned Account), and make three HTTP round trips. The composite approach is atomic and uses one API call.

### Pattern 2: Bulk Upsert Same-Type Records

**When to use:** An external system sends a batch of 200 or fewer records of the same object type that need to be created or updated in Salesforce. Record volume is too large for individual calls but too small to warrant Bulk API 2.0 async job overhead.

**How it works:** Use `/composite/sobjects/` with a PATCH request and an `externalIdFieldName` for upsert semantics. All records in the request body go into `records[]`. Set `allOrNone: false` to allow partial success, then inspect per-record results.

```json
PATCH /services/data/v63.0/composite/sobjects/Contact/External_Id__c
{
  "allOrNone": false,
  "records": [
    {
      "attributes": { "type": "Contact" },
      "External_Id__c": "EXT-001",
      "LastName": "Adams",
      "Email": "adams@example.com"
    },
    {
      "attributes": { "type": "Contact" },
      "External_Id__c": "EXT-002",
      "LastName": "Brown",
      "Email": "brown@example.com"
    }
  ]
}
```

**Why not the alternative:** Individual upsert calls against `/sobjects/{SObject}/{ExternalIdField}/{value}` for 150 records = 150 HTTP round trips and 150 API calls against the daily limit. The sObject Collection reduces this to 1 API call and 1 round trip.

### Pattern 3: Hierarchical Account-Contact Tree Insert

**When to use:** You need to insert a set of Accounts each with their own Contacts, and the parent Account IDs are not known in advance. The total record count is 200 or fewer and the tree is 5 levels or fewer deep.

**How it works:** Use `/composite/tree/Account/`. Each Account in the `records[]` array can include a `Contacts` key whose `records[]` hold the child Contact objects. Assign a `referenceId` to each record for response correlation.

```json
POST /services/data/v63.0/composite/tree/Account/
{
  "records": [
    {
      "attributes": { "type": "Account", "referenceId": "AcctRef1" },
      "Name": "Globex Corp",
      "Contacts": {
        "records": [
          {
            "attributes": { "type": "Contact", "referenceId": "ContRef1" },
            "LastName": "Simpson",
            "FirstName": "Homer"
          }
        ]
      }
    }
  ]
}
```

**Why not the alternative:** Using `/composite/` with multiple parent-then-child subrequests is limited to 25 subrequests total. sObject Tree supports up to 200 records across the entire hierarchy in one call, with a cleaner request shape for deeply nested trees.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Create parent + children, IDs unknown, must be atomic | `/composite/` with `allOrNone: true` and referenceId | Only resource with cross-subrequest ID wiring |
| Insert hierarchical parent-child tree (≤ 200 records, ≤ 5 levels) | `/composite/tree/{SObject}/` | Cleaner shape for trees, one atomic call |
| Bulk create/update/upsert same object type (≤ 200 records) | `/composite/sobjects/` | Highest record throughput per API call |
| Bundle independent requests to reduce round trips | `/composite/batch/` | No ordering dependency, simpler response handling |
| Mixed object type bulk DML with dependencies | `/composite/` (up to 25 subrequests) | Only option for cross-object, cross-reference operations |
| Volume > 200 records per operation | Bulk API 2.0 | Composite resources are not designed for large volumes |
| Single record CRUD | `/sobjects/{SObject}/` | No overhead; Composite adds complexity without benefit |

---

## Recommended Workflow

1. **Clarify the dependency structure** — Determine whether any subrequest needs a result (typically an ID) from a preceding subrequest. If yes, only `/composite/` supports this via `@{referenceId.field}`.
2. **Select the correct Composite resource** — Apply the Decision Guidance table above. Confirm record count and nesting depth are within resource limits.
3. **Design the atomicity strategy** — Choose `allOrNone: true` for all-or-nothing transactions, or `allOrNone: false` and build per-subrequest error handling into the caller.
4. **Build and validate the request body** — Confirm all `referenceId` values are unique, case-correct, and referenced before they are needed. Verify all record types, required fields, and field API names.
5. **Implement response parsing** — Do not rely on the outer HTTP status. Always iterate `compositeResponse[]` or per-record result arrays and inspect each `httpStatusCode`.
6. **Assess governor impact** — Calculate DML rows, CPU time, and API call count. Confirm the pattern fits within org limits before testing at scale.
7. **Run the checker script** — Execute `scripts/check_composite_api.py` against integration files to catch common structural issues before code review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Correct Composite resource is used for the dependency and volume profile (composite / sobjects / tree / batch).
- [ ] All `referenceId` values are unique within the request and case matches their `@{}` references exactly.
- [ ] `allOrNone` flag is explicitly set; its atomicity implications are documented in the integration design.
- [ ] Response parsing inspects every subrequest's `httpStatusCode`, not just the outer HTTP 200.
- [ ] DML row count is estimated (subrequests × records per subrequest) and confirmed within org limits.
- [ ] Record count per call does not exceed resource limits (25 subrequests for composite/batch; 200 records for sobjects/tree).
- [ ] API version is pinned to v60.0+ in all endpoint URLs.
- [ ] Partial failure path is handled when `allOrNone: false`: caller identifies failed subrequests and acts (retry, DLQ, alert).

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Outer HTTP 200 does not mean success** — All four Composite resources return HTTP 200 on the outer response even when individual subrequests or records fail. Any integration that checks only the outer status code silently discards errors. Always parse `compositeResponse[].httpStatusCode` or per-record result arrays.

2. **referenceId is case-sensitive** — If a subrequest sets `"referenceId": "NewAccount"` but a later subrequest references `@{newaccount.id}` (lowercase), Salesforce does not resolve the reference. The literal string `@{newaccount.id}` is passed as the field value, which then fails validation with a confusing error message.

3. **`allOrNone: true` rolls back ALL subrequests, including successful ones** — When any single subrequest fails with `allOrNone: true`, Salesforce rolls back every subrequest in the call, including those that had already succeeded. Rolled-back subrequests report `httpStatusCode: 400` and `errorCode: PROCESSING_HALTED` in their individual response — not a 2xx. This can be misread as a failure of those subrequests rather than a rollback.

4. **DML governor limits are not waived per subrequest** — 25 composite subrequests, each triggering 200 DML rows, equals 5,000 DML rows in a single transaction. Org-wide DML row limits (150 DML statements, unlimited rows but SOQL and CPU caps) can still be hit. Apex triggers, validation rules, and workflow rules fired by composite subrequests count against the same governor limits as any other transaction.

5. **sObject Tree is always atomic — partial success is not available** — Unlike `/composite/` with `allOrNone: false`, the tree resource has no partial-success mode. One invalid record in a 200-record tree rolls back the entire payload. Validate records client-side (required fields, field lengths, relationship IDs) before sending large trees.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Composite resource selection guide | Which resource (composite/sobjects/tree/batch) fits the use case and why |
| JSON request body scaffold | Complete request with subrequests, referenceIds, allOrNone, and record arrays |
| Response parsing logic | Per-subrequest iteration pattern with httpStatusCode inspection |
| Governor limit estimate | DML rows, API calls, and subrequest count projection |
| Integration review findings | Assessment of an existing Composite API implementation against this skill |

---

## Related Skills

- `integration/rest-api-patterns` — use for single-resource REST CRUD, SOQL pagination, OAuth Bearer token setup, and overall REST API decision-making.
- `data/bulk-api-and-large-data-loads` — use when record volumes exceed 200 per operation and Bulk API 2.0 async job patterns are needed.
- `integration/oauth-flows-and-connected-apps` — use when the authentication setup, Connected App scoping, or token refresh is the actual blocker.
- `apex/apex-rest-services` — use when a custom REST endpoint must be exposed from the org, not consumed.
