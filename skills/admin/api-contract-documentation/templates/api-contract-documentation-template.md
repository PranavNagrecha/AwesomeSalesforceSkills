# API Contract Documentation — Work Template

Use this template when producing or reviewing API contract documentation for a Salesforce integration.
One record per endpoint **per direction**. A filled example of every section below is in
`../references/worked-examples.md`.

---

## Scope

**Integration name:** _______________
**Direction:** [ ] inbound (partner → Salesforce)  [ ] outbound (Salesforce → partner)  [ ] bidirectional (write two records)
**API type:** [ ] Standard sObjects REST  [ ] Custom Apex REST (@RestResource)  [ ] Composite / sObject Collections  [ ] Bulk API 2.0
**Current API version in use:** _______________

---

## Versioning Policy Documentation

| Item | Value |
|---|---|
| Current API version | |
| Version release date (from `GET /services/data/`) | |
| Retirement risk (check the API End-of-Life Policy) | |
| Upgrade SLA (team commitment) | |
| Next EOL check date | |
| Who is alerted on a `Warning: 299` header | |

Policy facts to restate in the partner-facing document: Salesforce supports each API version for a
minimum of 3 years from first release, gives at least 1 year of notice before support ends, and
returns `410 GONE` — with no fallback — for any request against a retired version.

---

## Rate Limit Documentation

**Source:** Retrieved from `GET /services/data/vXX.0/limits` on [date]: _______________
**DailyApiRequests.Max:** _______________
**This integration's agreed budget inside that allocation:** _______________

Remember the allocation is **org-wide per 24-hour period**, shared with every other integration.

Monitoring pattern:
- Log `Sforce-Limit-Info: api-usage=X/Y; api-bursts=A/B` from each response
- Alert when this integration exceeds 80% of its own budget, or org `api-usage` exceeds 85%
- On a 403, branch on the header: at the ceiling → allocation exhausted; with headroom → the
  concurrent long-running-request cap (20-second requests: 5 in DE/Trial, 25 in production/sandbox)

---

## Error Code Catalog

Every row must end in a partner action. A code without an action is a glossary entry.

| HTTP Status | Salesforce `errorCode` | Meaning | Partner action | Retryable |
|---|---|---|---|---|
| 200 / 201 / 204 | (none) | Success — 201 on create, 200 on update | Mark delivered | — |
| 300 | (multiple external Id matches) | External Id matched more than one record; nothing written | | No |
| 400 | `JSON_PARSER_ERROR` / `MALFORMED_ID` | Malformed body, bad Id, or duplicate parameter name | | No |
| 401 | `INVALID_SESSION_ID` | Session ID or OAuth token expired or invalid | | Once, after re-auth |
| 403 | `REQUEST_LIMIT_EXCEEDED` | 24-hour allocation exhausted **or** concurrent long-running cap hit | | Conditionally |
| 403 | `INSUFFICIENT_ACCESS` | Running user lacks the permission | | No |
| 404 | `NOT_FOUND` | Bad URI **or** a sharing issue — indistinguishable by design | | No |
| 405 | (method not allowed) | Method not allowed for that resource | | No |
| 409 | (conflict) | Conflicts with current state; check version/resource compatibility | | No |
| 410 | (retired version) | Pinned API version retired | | No |
| 412 / 428 | (precondition) | Conditional-request headers unsatisfied or missing | | No |
| 414 / 431 | (too long) | URI, or URI + headers, exceeds the 16,384-byte limit | | No |
| 415 / 406 | (format) | Unsupported request entity format / unrepresentable XML return type | | No |
| 500 / 502 / 503 | (platform) | Platform error, Edge failure, or maintenance | | Yes |

> The error **body** is a JSON array: `[{ "message": …, "errorCode": …, "fields": [ … ] }]`.
> HTTP 429 is **not** in the REST API Developer Guide's status-code table — if you observe one,
> attribute it to the gateway or middleware in front of Salesforce, not to the platform.

---

## Idempotency

**Key strategy:** [ ] External Id upsert  [ ] Record Id  [ ] Read-only  [ ] Not idempotent (say so explicitly)
**External Id field API name:** _______________
**On HTTP 300 (duplicate key), the partner:** _______________
**`updateOnly=true` used?** [ ] yes (never create)  [ ] no

---

## Batching

| Resource | Cap | Counts as |
|---|---|---|
| Composite | 25 subrequests | 1 API call |
| Composite graphs | 500 subrequests | 1 API call |
| Composite tree | 200 records, 5 types, 5 levels | 1 API call |
| sObject Collections | 200 records | 1 API call |

**`allOrNone` decision and why:** _______________
**Per-row reconciliation step** (a well-formed Collections request returns `200 OK` even when rows
failed — per-item outcomes are in the `errors` array): _______________

---

## OpenAPI Spec Location

- Standard sObjects: generated via `GET /services/data/vXX.0/sobjects/{SObjectName}/describe/openapi3_0` (beta)
- Custom Apex REST: hand-authored at: _______________ (the beta generates nothing for `@RestResource`)
- Exact `urlMapping` string recorded: _______________ (two classes can claim the same URL; save order wins)

---

## The lintable record

Fill this, save as `<integration>-<direction>.yaml`, and run:

```
python3 ../scripts/check_api_contract_documentation.py --file <integration>-<direction>.yaml
```

```yaml
id: ""                          # unique across the contract set
name: ""
direction:                      # inbound | outbound | bidirectional
status:                         # draft | active | deprecated | retired
endpoint: ""
endpoint_kind:                  # apex-rest | sobjects-rest | composite | named-credential-callout | bulk-api
salesforce_api_version: ""      # vNN.0 - or n/a on an outbound contract only

auth:
  type:                         # named-credential | connected-app-oauth | jwt-bearer |
                                # client-credentials | session-id | mutual-tls | external-credential
  connected_app: ""             # at least one of connected_app / named_credential /
  named_credential: ""          # external_credential must be named
  running_user: ""

versioning:
  pinned_version: ""
  eol_review_date: ""           # YYYY-MM-DD
  upgrade_sla: ""
  breaking_change_notice_days: 90

schema:
  openapi_document: ""
  openapi_authoring:            # generated | hand-authored

idempotency:
  key_strategy:                 # external-id-upsert | record-id | read-only | none
  external_id_field: ""
  duplicate_key_runbook: ""

rate_limit:
  allocation_scope: ""
  org_allocation_source: ""     # GET /limits -> DailyApiRequests.Max, with the date read
  this_integration_budget: ""
  observability: ""
  alert_threshold: ""

error_contract:                 # one row per code the partner can receive
  - http_status: 0
    salesforce_error_code: ""
    meaning: ""
    partner_action: ""
    retryable: false

retry_policy:
  strategy: ""
  max_attempts: 0
  initial_delay_seconds: 0
  max_delay_seconds: 0
  retry_only_when: "The error_contract row for the returned code has retryable: true."

change_control:
  owner: ""
  approver: ""
  notice_period_days: 0
  breaking_change_definition: ""

owner: ""                       # a named human, not a team alias alone
review_date: ""                 # YYYY-MM-DD

consumed_by:
  - "agents/integration-catalog-builder/AGENT.md"
references:
  - "skills/apex/apex-rest-services"
```

**Do not document an SLA uptime or latency percentage here.** Salesforce publishes availability
commitments through trust.salesforce.com and the Order of Service, not in developer documentation.
Record your own internal commitment and say which side measures it.
