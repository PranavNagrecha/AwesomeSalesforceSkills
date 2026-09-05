# Worked Examples — API Contract Documentation

One integration, documented end to end. **Northwind OMS** (an external order-management system) pushes orders into Salesforce over a custom Apex REST resource, and reads Account credit status back over the standard sObjects REST API. Two directions, therefore two contract records.

Everything below is copy-and-adapt material. Replace `Northwind`, `OMS-`, `CRM-`, the Named Credential names and the owner names; keep the field set.

Platform facts in this file are grounded in the Summer '26 REST API Developer Guide (`api_rest`), the Apex Developer Guide (`salesforce_apex_developer_guide`) and the Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet`). Sources are listed in `well-architected.md` § Official Sources Used.

---

## 1. The API contract records

### 1.1 Inbound — Northwind OMS pushes orders into Salesforce

Lint this file with `python3 scripts/check_api_contract_documentation.py --file northwind-oms-order-intake.yaml`.

```yaml
# northwind-oms-order-intake.yaml
id: NW-OMS-001
name: "Northwind OMS -> Salesforce order intake"
direction: inbound
status: active
endpoint: "/services/apexrest/northwind/v1/orders"
endpoint_kind: apex-rest
salesforce_api_version: "v62.0"

auth:
  type: connected-app-oauth
  connected_app: "Northwind OMS Integration"
  oauth_flow: jwt-bearer
  running_user: "svc.northwind.oms@example.com.prod"
  # The Connected App inventory row lives with the catalog agent, not here.
  see_also: "skills/admin/integration-admin-connected-apps"

versioning:
  policy: "Pin to a single Salesforce API version; never float."
  pinned_version: "v62.0"
  support_basis: "Salesforce supports each API version for a minimum of 3 years from first release and gives at least 1 year of notice before support ends (REST API Developer Guide, API End-of-Life Policy)."
  retired_versions_note: "Versions 21.0-30.0 are retired and unavailable as of Summer '25; a call on a retired version returns 410 GONE."
  eol_review_date: "2027-01-15"
  upgrade_sla: "Upgrade within 6 months of any Salesforce deprecation notice naming v62.0."
  breaking_change_notice_days: 90

schema:
  request_example_ref: "worked-examples.md 1.3"
  response_example_ref: "worked-examples.md 1.3"
  openapi_document: "docs/api/northwind-oms-order-intake.openapi.yaml"
  openapi_authoring: "hand-authored"
  openapi_authoring_reason: "The sObjects OpenAPI 3.0 beta generator does not emit a document for @RestResource classes."

idempotency:
  key_strategy: external-id-upsert
  external_id_field: "Order.Northwind_Order_Id__c"
  semantics: "Unmatched external Id creates a record; a single match updates it; more than one match returns HTTP 300 and nothing is written (REST API Developer Guide, Insert or Update (Upsert) a Record Using an External ID)."
  duplicate_key_runbook: "On 300, do not retry. Park the message, alert #crm-integrations, and de-duplicate the matching Salesforce records before replaying."
  update_only_option: "Add ?updateOnly=true to the URL to suppress creation when the partner must never introduce new records."
  see_also: "skills/data/external-id-strategy"

rate_limit:
  allocation_scope: "Org-wide. The total inbound API request allocation is per org per 24-hour period and is shared by every integration in this org (Developer Limits Quick Reference, Total API Request Allocations)."
  org_allocation_formula: "100,000 + (licenses x calls per license type) + purchased API Call Add-Ons for Enterprise, Unlimited and Performance Editions; 15,000 flat for Developer Edition."
  org_allocation_source: "GET /services/data/v62.0/limits -> DailyApiRequests.Max. Retrieved 2026-09-01."
  this_integration_budget: "12,000 calls per 24 hours (a named slice of the org allocation, agreed with the API governance owner)."
  observability: "Log the Sforce-Limit-Info response header on every call. Documented example: 'api-usage=10018/100000; api-bursts=1/750'."
  alert_threshold: "Page when this integration's own counter exceeds 80% of its 12,000 budget, or when org api-usage exceeds 85%."
  concurrency: "Requests running 20 seconds or longer are capped at 25 concurrently in production orgs and sandboxes, 5 in Developer Edition and Trial orgs; exceeding it also returns REQUEST_LIMIT_EXCEEDED."
  batching: "Northwind sends up to 200 order lines per message. Composite requests allow 25 subrequests; composite graphs allow 500; sObject Collections allows 200 records - each counts as one call toward the allocation."

error_contract:
  - http_status: 300
    salesforce_error_code: "(none - multiple external Id matches)"
    meaning: "External Id matched more than one Order; nothing was created or updated."
    partner_action: "Park the message in the OMS dead-letter queue and raise a P2. Do not retry."
    retryable: false
  - http_status: 400
    salesforce_error_code: "JSON_PARSER_ERROR"
    meaning: "Request body is malformed, or the same parameter name appears twice."
    partner_action: "Fail the message permanently and alert the OMS owner. A retry sends the same bad body."
    retryable: false
  - http_status: 401
    salesforce_error_code: "INVALID_SESSION_ID"
    meaning: "The OAuth token expired or was revoked."
    partner_action: "Re-run the JWT bearer flow once, then retry the original request exactly once."
    retryable: true
  - http_status: 403
    salesforce_error_code: "REQUEST_LIMIT_EXCEEDED"
    meaning: "Either the org's 24-hour allocation is exhausted, or the concurrent long-running-request cap was hit."
    partner_action: "Stop the sender. If Sforce-Limit-Info shows api-usage at the ceiling, wait for the rolling window. Otherwise back off 60s and resume at half rate."
    retryable: true
  - http_status: 403
    salesforce_error_code: "INSUFFICIENT_ACCESS"
    meaning: "The running user cannot create or edit the record."
    partner_action: "Park and raise a P1 against the integration user's permission set group. Retrying will not help."
    retryable: false
  - http_status: 404
    salesforce_error_code: "NOT_FOUND"
    meaning: "Bad URI, or a sharing rule hides the record from the running user. The status cannot distinguish the two."
    partner_action: "Park and raise a P2. Include the full request URI in the ticket so Salesforce can tell URI error from sharing error."
    retryable: false
  - http_status: 409
    salesforce_error_code: "(version conflict)"
    meaning: "The request conflicts with the resource's current state; check the API version is compatible with the resource."
    partner_action: "Park and escalate to the contract owner - this usually means the pinned version no longer supports the resource."
    retryable: false
  - http_status: 410
    salesforce_error_code: "(retired API version)"
    meaning: "The pinned API version has been retired and is unavailable."
    partner_action: "Halt the integration. This is a P1 contract breach - the eol_review_date was missed."
    retryable: false
  - http_status: 415
    salesforce_error_code: "(unsupported entity format)"
    meaning: "The body format is not supported by the method. Apex REST returns 415 when XML is sent for a parameter type XML cannot represent."
    partner_action: "Fail permanently. Send application/json."
    retryable: false
  - http_status: 500
    salesforce_error_code: "(platform error)"
    meaning: "An error occurred within Lightning Platform."
    partner_action: "Retry per retry_policy. If it persists past max_attempts, raise a Salesforce support case with the request Id."
    retryable: true
  - http_status: 503
    salesforce_error_code: "(server unavailable)"
    meaning: "Server down for maintenance or overloaded."
    partner_action: "Retry per retry_policy; check trust.salesforce.com before escalating."
    retryable: true

retry_policy:
  strategy: exponential-backoff-with-jitter
  max_attempts: 5
  initial_delay_seconds: 2
  max_delay_seconds: 300
  retry_only_when: "The error_contract row for the returned code has retryable: true."
  idempotency_guarantee: "Every retry replays the same external Id upsert, so a duplicate delivery updates rather than duplicates."
  timeout_note: "The REST and SOAP API call timeout is 10 minutes except for query calls; for Composite resources the timeout covers the whole composite request, not each subrequest. Set the client timeout below this."

sla:
  availability_source: "trust.salesforce.com and the Order of Service. Salesforce developer documentation publishes no uptime or latency percentage - do not quote one here."
  internal_commitment: "Northwind orders are acknowledged within 5 minutes of receipt during business hours; measured on the OMS side, not asserted of the platform."
  measurement: "OMS emits a per-message ack latency metric; Salesforce side is measured with the API Total Usage event type."

change_control:
  owner: "Priya Raman (CRM Integration Lead)"
  approver: "CRM Architecture Review Board"
  review_date: "2026-12-01"
  notice_period_days: 90
  breaking_change_definition: "Removing or renaming a response field, tightening a validation, changing the idempotency key, or moving the pinned API version."
  deprecation_notice_template: "worked-examples.md 5"

owner: "Priya Raman (CRM Integration Lead)"
review_date: "2026-12-01"

consumed_by:
  - "agents/integration-catalog-builder/AGENT.md"
references:
  - "skills/apex/apex-rest-services"
  - "skills/integration/api-versioning-strategy"
  - "skills/integration/rest-api-patterns"
  - "skills/data/external-id-strategy"
```

### 1.2 Outbound — Salesforce reads Account credit status from Northwind

The second direction is a separate record because the auth principal, the error surface and the idempotency question are all different. Only the fields that differ are shown; the rest carry over.

```yaml
# northwind-oms-account-status.yaml (delta from 1.1)
id: NW-OMS-002
name: "Salesforce -> Northwind OMS account credit status read"
direction: outbound
status: active
endpoint: "callout:Northwind_OMS/v1/accounts/{externalCustomerId}/credit-status"
endpoint_kind: named-credential-callout
salesforce_api_version: "n/a"

auth:
  type: named-credential
  named_credential: "Northwind_OMS"
  external_credential: "Northwind_OMS_OAuth"
  principal_type: "Named Principal"
  see_also: "skills/integration/named-credentials-setup"

idempotency:
  key_strategy: read-only
  semantics: "GET is safe to repeat. No key required."
  duplicate_key_runbook: "n/a - read-only."

rate_limit:
  allocation_scope: "Northwind's own quota, not the Salesforce 24-hour allocation. Outbound callouts do not draw on the org's inbound API request allocation."
  this_integration_budget: "Northwind grants 600 requests per minute; the Apex caller must not exceed it."
  observability: "Log Northwind's own X-RateLimit-Remaining header; Sforce-Limit-Info is not returned on outbound callouts."
  alert_threshold: "Alert at 80% of 600/min sustained for 5 minutes."

error_contract:
  - http_status: 401
    salesforce_error_code: "(partner 401)"
    meaning: "Named Credential token rejected by Northwind."
    partner_action: "Salesforce side re-authenticates via the External Credential and retries once; if it fails again, alert the Named Credential owner."
    retryable: true
  - http_status: 404
    salesforce_error_code: "(partner 404)"
    meaning: "Northwind does not know this external customer Id."
    partner_action: "Treat as 'no credit status', not an error. Write CreditStatus__c = 'Unknown' and continue."
    retryable: false
  - http_status: 429
    salesforce_error_code: "(partner throttle)"
    meaning: "Northwind's own gateway throttled us. This is a partner status code, not a Salesforce one."
    partner_action: "Exponential backoff per retry_policy. Honour Retry-After if present."
    retryable: true

owner: "Priya Raman (CRM Integration Lead)"
review_date: "2026-12-01"
retry_policy:
  strategy: exponential-backoff-with-jitter
  max_attempts: 3
  initial_delay_seconds: 1
  max_delay_seconds: 30
  retry_only_when: "The error_contract row for the returned code has retryable: true."
```

**Why 429 appears here and not in 1.1:** the REST API Developer Guide's Status Codes and Error Responses table does not list 429. It is Northwind's gateway status, so it belongs on the outbound record. Attributing it to Salesforce in the inbound contract is the mistake `llm-anti-patterns.md` § 3 describes.

### 1.3 Request and response examples

Inbound request body, as Northwind sends it:

```json
{
  "externalOrderId": "OMS-1001",
  "accountExternalId": "CRM-42",
  "orderDate": "2026-09-01",
  "currencyIsoCode": "GBP",
  "totalAmount": 1250.00,
  "lines": [
    { "sku": "NW-WIDGET-01", "quantity": 5, "unitPrice": 250.00 }
  ]
}
```

Success acknowledgement, as the Apex REST resource returns it:

```json
{
  "status": "ACCEPTED",
  "externalOrderId": "OMS-1001",
  "salesforceOrderId": "801Kj000000XyZaIAK",
  "created": true,
  "apiVersion": "v62.0"
}
```

Failure, as Salesforce returns it — note it is an **array**, and note that `created` is present in upsert responses only in API version 46.0 and later:

```json
[
  {
    "fields": ["Northwind_Order_Id__c"],
    "message": "The requested resource does not exist",
    "errorCode": "NOT_FOUND"
  }
]
```

---

## 2. OpenAPI 3.0 excerpt for the custom Apex REST resource

Hand-authored, because the sObjects OpenAPI 3.0 beta generator (`GET /services/data/vXX.0/sobjects/{SObjectName}/describe/openapi3_0`) emits nothing for `@RestResource` classes. Save as `docs/api/northwind-oms-order-intake.openapi.yaml`.

```yaml
openapi: 3.0.3
info:
  title: Northwind OMS Order Intake (Salesforce Apex REST)
  version: 1.0.0
  description: >-
    Inbound order intake. Idempotent on Order.Northwind_Order_Id__c.
    Contract record: NW-OMS-001. Pinned to Salesforce API v62.0.
servers:
  - url: https://example.my.salesforce.com/services/apexrest/northwind/v1
paths:
  /orders:
    post:
      operationId: createOrUpdateOrder
      summary: Upsert an order by Northwind external order Id
      security:
        - salesforceOAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/OrderRequest' }
      responses:
        '200': { description: Existing order updated,  content: { application/json: { schema: { $ref: '#/components/schemas/OrderAck' } } } }
        '201': { description: New order created,       content: { application/json: { schema: { $ref: '#/components/schemas/OrderAck' } } } }
        '300': { description: External Id matched more than one Order; nothing written, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '400': { description: Malformed body or duplicate parameter name, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '401': { description: Session or OAuth token expired or invalid,  content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '403': { description: Refused - REQUEST_LIMIT_EXCEEDED or INSUFFICIENT_ACCESS, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '410': { description: The pinned API version has been retired, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '415': { description: Unsupported request entity format, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
        '500': { description: Lightning Platform error, content: { application/json: { schema: { $ref: '#/components/schemas/SalesforceErrors' } } } }
components:
  securitySchemes:
    salesforceOAuth:
      type: oauth2
      description: JWT bearer flow against the "Northwind OMS Integration" Connected App.
      flows:
        clientCredentials:
          tokenUrl: https://example.my.salesforce.com/services/oauth2/token
          scopes:
            api: Access and manage your data
  schemas:
    OrderRequest:
      type: object
      required: [externalOrderId, accountExternalId, orderDate, totalAmount]
      properties:
        externalOrderId:   { type: string, maxLength: 255, description: "Maps to Order.Northwind_Order_Id__c (External Id, Unique)" }
        accountExternalId: { type: string, maxLength: 255, description: Maps to Account.Northwind_Customer_Id__c }
        orderDate:         { type: string, format: date, description: yyyy-MM-dd. Salesforce date fields do not accept a timezone offset }
        currencyIsoCode:   { type: string, minLength: 3, maxLength: 3 }
        totalAmount:       { type: number, format: double }
        lines:
          type: array
          maxItems: 200
          description: Capped at 200 to match the sObject Collections per-request record limit.
          items: { $ref: '#/components/schemas/OrderLine' }
    OrderLine:
      type: object
      required: [sku, quantity, unitPrice]
      properties:
        sku:       { type: string }
        quantity:  { type: integer, minimum: 1 }
        unitPrice: { type: number, format: double }
    OrderAck:
      type: object
      required: [status, externalOrderId, salesforceOrderId]
      properties:
        status:            { type: string, enum: [ACCEPTED, REJECTED] }
        externalOrderId:   { type: string }
        salesforceOrderId: { type: string, pattern: '^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$' }
        created:           { type: boolean, description: Present in API version 46.0 and later }
        apiVersion:        { type: string }
    # The canonical Salesforce error shape: an ARRAY of error objects, never a single object.
    SalesforceErrors:
      type: array
      items:
        type: object
        required: [message, errorCode]
        properties:
          message:   { type: string }
          errorCode: { type: string, example: NOT_FOUND }
          fields:
            type: array
            items: { type: string }
```

**How to read it:**
- `SalesforceErrors` is an **array** type, not an object. Every error response `$ref`s it. A spec that models the error as a single object will generate a client that crashes on the first real failure.
- Both `200` and `201` are success. An upsert returns 201 when it created and 200 when it updated — a client that treats only 200 as success will reprocess every new order.
- `410` is in the spec on purpose. It is the response the partner gets the day the pinned version retires, and putting it in the contract is what makes the deprecation notice in § 5 non-negotiable.
- `maxItems: 200` on `lines` is not arbitrary — it mirrors the 200-record cap on sObject Collections so the resource never has to reject a payload it accepted at the contract layer.
- The `orderDate` description carries the platform constraint (no timezone offset on `date` fields) into the schema, where a code generator will see it.

---

## 3. The error contract as a partner-facing table

The YAML in § 1.1 is what the linter reads. This is the same content rendered for the partner's runbook — one row per code, and every row ends in an action.

| HTTP | Salesforce `errorCode` | What it means | Northwind does | Retry? |
|---|---|---|---|---|
| 200 | — | Existing order updated | Mark delivered | — |
| 201 | — | New order created | Mark delivered | — |
| 300 | (multiple external Id matches) | The external Id matched more than one Order; nothing written | Dead-letter + P2 | No |
| 400 | `JSON_PARSER_ERROR` | Malformed body, or the same parameter name sent twice | Permanent fail + alert | No |
| 401 | `INVALID_SESSION_ID` | Token expired or invalid | Re-auth once, replay once | Yes (once) |
| 403 | `REQUEST_LIMIT_EXCEEDED` | 24-hour allocation exhausted **or** concurrent long-running cap hit | Stop sender; inspect `Sforce-Limit-Info` before choosing wait vs. backoff | Yes (conditionally) |
| 403 | `INSUFFICIENT_ACCESS` | Running user lacks create/edit | Park + P1 on the PSG | No |
| 404 | `NOT_FOUND` | Bad URI **or** sharing hides the record | Park + P2, include full URI | No |
| 409 | (version conflict) | API version incompatible with the resource | Park + escalate to contract owner | No |
| 410 | (retired version) | Pinned API version retired | Halt + P1 contract breach | No |
| 415 | (unsupported format) | Body format unsupported for the method | Permanent fail; send JSON | No |
| 500 / 502 / 503 | (platform) | Platform error, Edge failure, or maintenance | Backoff per retry policy | Yes |

Two rows carry the whole design: **403 is ambiguous** (two distinct causes, two different recoveries), and **404 is ambiguous** (URI error vs. sharing). A contract that does not say so hands the partner a coin flip.

---

## 4. The Salesforce-side contract test

An **excerpt**, not a complete test class. The class structure, `@IsTest` setup, bulk cases and the `TestDataFactory` it should call are `skills/apex/apex-rest-services` and `templates/apex/tests/` territory — this skill only owns the assertion that the *shape the contract promises* is the shape the resource returns.

```apex
// EXCERPT - contract assertions only. Class scaffold: skills/apex/apex-rest-services
@IsTest static void doPost_returnsContractedAckShape() {
    RestContext.request = new RestRequest();                 // RestContext exposes request/response
    RestContext.request.requestURI  = '/services/apexrest/northwind/v1/orders';
    RestContext.request.httpMethod  = 'POST';
    RestContext.request.requestBody = Blob.valueOf('{"externalOrderId":"OMS-1001",' +
        '"accountExternalId":"CRM-42","orderDate":"2026-09-01","totalAmount":1250.00}');
    RestContext.response = new RestResponse();
    OrderIntakeResource.OrderAck ack = OrderIntakeResource.doPost();
    Assert.areEqual('ACCEPTED', ack.status);                 // contract field: status
    Assert.areEqual('OMS-1001', ack.externalOrderId);        // contract field: echoed key
    Assert.isNotNull(ack.salesforceOrderId);                 // contract field: salesforceOrderId
}
```

Two platform facts this excerpt depends on, both from the Apex Developer Guide (Apex REST Method Considerations): `RestRequest` and `RestResponse` are reachable through the static `RestContext` object, and a method annotated `@HttpGet` or `@HttpDelete` must take no parameters — which is why the POST path is the one worth contract-testing.

Add a second assertion set for every `retryable: false` row in § 3. The value of a contract test is not that the happy path works; it is that a refactor which changes `ACCEPTED` to `Accepted` fails a build instead of a partner.

---

## 5. Deprecation notice template

Grounded on the published policy: Salesforce supports each API version for a **minimum of 3 years** from first release, notifies customers **at least 1 year** before support for a version ends, and returns **`410 GONE`** for any request against a retired version. Versions 21.0–30.0 are retired and unavailable as of Summer '25; versions 7.0–20.0 as of Summer '22.

```markdown
Subject: [Action required] Northwind OMS integration NW-OMS-001 moves to Salesforce API v65.0

Contract:        NW-OMS-001 - Northwind OMS -> Salesforce order intake
Current version: v62.0
Target version:  v65.0
Notice date:     2026-09-04
Change window:   2026-12-04 to 2026-12-18   (90 days' notice, per the contract's change_control)
Hard cutover:    2026-12-18
Owner:           Priya Raman (CRM Integration Lead)
Approver:        CRM Architecture Review Board

Why now
  Salesforce supports each API version for a minimum of three years from first
  release and gives at least one year of notice before support for a version
  ends. Once a version is retired, every request against it returns 410 GONE -
  there is no grace period and no fallback to a newer version.

What changes for you
  1. The base path changes from .../v62.0/... to .../v65.0/... . Nothing else in
     the request or response schema changes; the OpenAPI document at
     docs/api/northwind-oms-order-intake.openapi.yaml is updated in the same PR.
  2. The idempotency key is unchanged: Order.Northwind_Order_Id__c.
  3. The error contract is unchanged. 410 remains in the contract as the symptom
     of a missed cutover.

What we need from you
  [ ] Confirm by 2026-10-04 that your client reads the API version from
      configuration, not from a compiled constant.
  [ ] Run against the full-copy sandbox between 2026-12-04 and 2026-12-11.
  [ ] Confirm sign-off by 2026-12-15.

If we hear nothing
  We hold at v62.0 and re-notice. We do not cut over an unconfirmed consumer -
  but note that the underlying Salesforce retirement date, when one is announced,
  is not ours to move.

Questions: #crm-integrations
```

**Fill the notice from the record, not from memory.** Every field above maps to a key in § 1.1: `pinned_version`, `change_control.notice_period_days`, `change_control.owner`, `change_control.approver`, `idempotency.external_id_field`, `schema.openapi_document`. If a field in the notice has no source in the record, the record is incomplete — which is precisely what `scripts/check_api_contract_documentation.py` exits 1 on.

---

## 6. Where these artefacts go next

| Artefact | Consumed by | How |
|---|---|---|
| Contract record (§ 1) | `agents/integration-catalog-builder/AGENT.md` § Output Contract | Becomes a row in the catalog table: endpoint, type, principal, auth flow, usage count |
| Error contract (§ 3) | The partner's runbook, and `skills/integration/api-governance-and-rate-limits` | The `retryable` column is what governance uses to model retry-driven allocation draw |
| OpenAPI document (§ 2) | The partner's client generator | Checked into `docs/api/`, versioned alongside the contract record |
| Contract test (§ 4) | `skills/apex/apex-rest-services` and the org's CI | Runs on every deploy touching the `@RestResource` class |
| Deprecation notice (§ 5) | `skills/integration/api-versioning-strategy` | The org's sunset policy sets `notice_period_days`; this skill renders it |
