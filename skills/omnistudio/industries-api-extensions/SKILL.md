---
name: industries-api-extensions
description: "Use this skill when integrating with Salesforce Industries-specific API layers — Insurance Policy Business Connect API, Communications Cloud TM Forum Open APIs (TMF679, TMF680, etc.), Energy and Utilities Update Asset Status API, and Service Process Studio Connect APIs. Trigger keywords: Insurance policy issuance API, endorsement API, TMF679, Communications Cloud REST API, Update Asset Status, Service Process API, InsurancePolicy Connect API, sfiEnergy, industry-specific REST endpoint. NOT for standard Salesforce REST API, SOAP API, Bulk API, or platform event integration unrelated to an industry vertical."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
tags:
  - industries-api
  - insurance
  - communications-cloud
  - energy-utilities
  - omnistudio
  - connect-api
  - tmforum
  - rest-api
triggers:
  - "How do I call the insurance policy issuance API in Salesforce Insurance Cloud?"
  - "We need to submit a product order to Communications Cloud using TM Forum TMF622 REST API"
  - "What is the correct way to update a ServicePoint status in Energy and Utilities Cloud?"
  - "How do I invoke a Service Process from an external system using Connect API?"
  - "Should we use Direct Access or MuleSoft gateway for Communications Cloud TM Forum APIs?"
inputs:
  - "Industry vertical (Insurance, Communications, Energy and Utilities, or cross-vertical)"
  - "API operation being implemented (issuance, endorsement, renewal, cancellation, asset status update, TMF order, process execution)"
  - "Integration access model (Direct Access vs MuleSoft gateway for Comms Cloud)"
  - "Target Salesforce Industries org edition and installed Industry Cloud license"
outputs:
  - "Correct endpoint path and HTTP method for the target industry API operation"
  - "Required request payload structure and key field constraints"
  - "Integration Procedure or Connect API delegation chain for the operation"
  - "Pattern recommendations for error handling and consistency guarantees"
  - "Migration guidance away from deprecated gateway patterns (Comms Cloud)"
dependencies: []
runtime_orphan: true
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Industries API Extensions

This skill activates when a practitioner needs to call or design integrations against industry-vertical REST APIs provided by Salesforce Industries — specifically the Insurance Policy Business Connect API, Communications Cloud TM Forum Open APIs, Energy and Utilities Update Asset Status API, and Service Process Studio Connect APIs. It does NOT cover the standard Salesforce REST API, Bulk API, or generic platform integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Salesforce Industries license is provisioned (Insurance Cloud, Communications Cloud, Energy and Utilities Cloud, or a cross-vertical OmniStudio runtime). Industry API endpoints do not exist without the corresponding license.
- Confirm whether the org uses Salesforce-managed Direct Access for Communications Cloud TM Forum APIs or was previously relying on a MuleSoft gateway integration. The MuleSoft gateway path is deprecated as of Winter '27; Direct Access is the only forward-compatible path.
- Verify the OmniStudio runtime version. Integration Procedures backing industry APIs (for example, `sfiEnergy_UpdateAssetStatus`) are version-stamped and may require activation of a specific IP version in managed package orgs.
- The most common wrong assumption is that standard Salesforce REST CRUD (`/services/data/vXX.X/sobjects/InsurancePolicy`) is the correct way to create or update industry records. It is not — industry objects require the industry-specific Connect API layer or Integration Procedure invocation to preserve cross-object consistency guarantees.

---

## Core Concepts

### Insurance Policy Business Connect API

The Insurance Policy Business Connect API exposes atomic lifecycle transaction endpoints for the Insurance Cloud. Each endpoint performs a combined, consistency-guaranteed operation across `InsurancePolicy`, `InsurancePolicyCoverage`, `InsurancePolicyParticipant`, and related objects in a single transaction. The available operations are:

- **Issuance** (`POST /connect/insurance/policy-issuances`) — creates a new policy with all associated coverages.
- **Endorsement** (`POST /connect/insurance/policy-endorsements`) — modifies an in-force policy mid-term, updating coverages atomically.
- **Renewal** (`POST /connect/insurance/policy-renewals`) — creates a successor term policy linked to the original.
- **Cancellation** (`POST /connect/insurance/policy-cancellations`) — terminates an in-force policy and sets cancellation reason fields.

All endpoints are versioned Connect APIs accessed via `/services/data/vXX.X/connect/insurance/...`. They are not available in non-Insurance-Cloud orgs. The body is a JSON representation of the policy transaction, not a raw sObject payload.

### Communications Cloud TM Forum Open APIs

Communications Cloud exposes industry-standard TM Forum Open API specifications as inbound REST endpoints within the Salesforce platform. The key APIs include:

- **TMF679 Product Offering Qualification** — determines which product offerings can be delivered to a given address or customer.
- **TMF680 Shopping Cart** — manages cart lifecycle for B2C and B2B quoting flows.
- **TMF622 Commercial Order Management** — submits and manages commercial product orders.

Critical behavior: TM Forum APIs in Salesforce are **ID-driven, not name-driven**. Requests must reference Salesforce record IDs for products, offerings, and accounts. Passing product names or catalog codes results in a 404 or validation error. The implementation delegate for each TMF API operation is an OmniScript or Integration Procedure configured in Communications Cloud setup.

Access model: **Direct Access only**. The MuleSoft gateway integration that previously surfaced TM Forum APIs is deprecated as of Winter '27 and will not be supported in future releases. New implementations must use Direct Access, where the TM Forum API endpoints are served directly by the Salesforce org on its instance URL.

### Energy and Utilities Update Asset Status API

The E&U Cloud exposes an `Update Asset Status` API (`POST /connect/energy/asset-status-updates`) that changes the operational status of a ServicePoint or related energy asset (for example, from Active to Inactive or from Inactive to Disconnected). This API delegates internally to the `sfiEnergy_UpdateAssetStatus` Integration Procedure, which applies validation rules and orchestrates the downstream sObject updates.

Calling the standard REST API to update the `Status` field on a `ServicePoint` record directly bypasses this Integration Procedure and skips E&U-specific business rule validation, including disconnection sequencing and metering notifications.

### Service Process Studio Connect APIs

Service Process Studio Connect APIs allow external systems and OmniScripts to invoke Service Process definitions as REST calls. The endpoint pattern is:

```
POST /services/data/vXX.X/connect/service-processes/{processApiName}/runs
```

The body carries input parameters defined in the Service Process definition. Service Process APIs are cross-vertical: they work in Insurance Cloud, Communications Cloud, and E&U Cloud where Service Process Studio is licensed. Response shape is defined by the Service Process output parameters, not a fixed schema.

---

## Common Patterns

### Pattern 1: Atomic Policy Issuance (Insurance Cloud)

**When to use:** An external system or OmniScript needs to create a new insurance policy including coverages, participants, and policy period in a single transaction.

**How it works:**

1. Authenticate with a Connected App using OAuth 2.0 (JWT or web-server flow).
2. POST to `/services/data/v62.0/connect/insurance/policy-issuances` with the JSON policy issuance payload. Key fields: `policyName`, `effectiveDate`, `expirationDate`, `productId` (Salesforce ID of the InsuranceProduct record), and a `coverages` array containing `coverageType` and `coverageAmount` per coverage.
3. The API creates `InsurancePolicy` and `InsurancePolicyCoverage` records atomically. On success it returns the newly created `InsurancePolicy` ID and a `201 Created` response.
4. Handle the `409 Conflict` status code, which the API returns when a duplicate policy is detected (same product + holder + effective date).
5. On failure, no partial records are committed — the transaction rolls back entirely.

**Why not the alternative:** A direct `insert InsurancePolicy` DML followed by separate `insert InsurancePolicyCoverage` DML allows a partial commit if the coverage insert fails. This leaves orphaned policy records and violates Insurance Cloud referential integrity rules.

### Pattern 2: TM Forum Order Submission (Communications Cloud — Direct Access)

**When to use:** A BSS system submits a commercial product order to Communications Cloud using the TMF622 API.

**How it works:**

1. Verify Direct Access is enabled in Setup > Communications Cloud > TM Forum API Settings. Confirm the API version endpoint is active.
2. POST to `https://<org-instance>.my.salesforce.com/services/apexrest/tmf-api/productOrderingManagement/v4/productOrder` with the TMF622 JSON body. The `productOffering.id` field must be the Salesforce ID of the `ProductOffering__c` record, not the product catalog code.
3. The platform routes the request to the configured Integration Procedure for order processing. The response returns a `productOrder.id` (Salesforce record ID) and `state: acknowledged`.
4. Poll `GET .../productOrder/{id}` for state transitions (`inProgress` → `completed` or `failed`).
5. Error responses follow the TM Forum error schema: `{ "code": "...", "reason": "...", "message": "..." }`.

**Why not the alternative:** Routing through the legacy MuleSoft gateway creates a dependency on a deprecated integration path. Winter '27 deprecation means orgs relying on the MuleSoft path will lose connectivity and require emergency re-architecture. Direct Access aligns with the Salesforce-supported roadmap.

### Pattern 3: Asset Status Update (Energy and Utilities Cloud)

**When to use:** A field management system or meter operations process needs to change a ServicePoint's operational status.

**How it works:**

1. POST to `/services/data/v62.0/connect/energy/asset-status-updates` with body `{ "assetId": "<ServicePoint_ID>", "newStatus": "Inactive", "reason": "CustomerRequest" }`.
2. The API delegates to the `sfiEnergy_UpdateAssetStatus` Integration Procedure, which validates transition rules (e.g., Active → Inactive is permitted; Inactive → Active requires a re-energization reason code).
3. On success, the ServicePoint `Status` field is updated and a `StatusChange` event record is created.
4. On validation failure, the API returns a `422 Unprocessable Entity` with an `errorCode` from the Integration Procedure output.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Creating a new insurance policy with coverages | Insurance Policy Business Connect API (`/connect/insurance/policy-issuances`) | Guarantees atomic creation across InsurancePolicy and InsurancePolicyCoverage; standard DML does not |
| Modifying an in-force insurance policy mid-term | Connect API endorsement endpoint | Ensures endorsement audit trail and coverage consistency are maintained |
| Submitting a product order from a BSS system to Comms Cloud | TMF622 via Direct Access | MuleSoft gateway is deprecated Winter '27; Direct Access is the only supported path |
| Querying product offering availability for an address | TMF679 via Direct Access (ID-driven) | Pass Salesforce record IDs, not product names; name-based lookups are not supported |
| Changing a ServicePoint's operational status | E&U Update Asset Status Connect API | Bypassing via direct DML skips Integration Procedure validation and business rules |
| Invoking a cross-vertical service process from an external system | Service Process Studio Connect API (`/connect/service-processes/{name}/runs`) | Standard for orchestrating multi-step industry processes; returns process-defined output schema |
| Standard Salesforce CRUD on non-industry objects in an Industries org | Standard REST API (`/sobjects/`) | Industry API extensions are only required for industry-specific objects and lifecycle transactions |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the vertical and operation** — confirm the Salesforce Industries license (Insurance, Communications, or E&U) and the specific lifecycle operation (issuance, endorsement, renewal, cancellation, asset status update, TM Forum order, or service process execution). This determines which endpoint family to use.
2. **Verify the access model and API version** — for Communications Cloud, confirm Direct Access is enabled and the MuleSoft gateway is not in use. For Insurance and E&U, confirm the org is on the API version that supports the target endpoint (Spring '25+ for current endpoint paths).
3. **Obtain record IDs for all referenced entities** — industry APIs are ID-driven. Resolve Salesforce record IDs for products, offerings, policies, and assets before constructing the request body. Do not use names, codes, or catalog identifiers as primary keys in the payload.
4. **Construct and validate the request payload** — follow the Connect API request schema for Insurance/E&U, or the TM Forum JSON schema for Comms Cloud. For insurance operations, include all required coverage array entries; partial payloads fail validation before any DML occurs.
5. **Handle vertical-specific error codes** — industry APIs return structured error responses distinct from standard Salesforce REST error responses. Map `409 Conflict` (insurance duplicate), `422 Unprocessable Entity` (E&U validation failure), and TM Forum error schema (`code`/`reason`/`message`) to retry or escalation logic.
6. **Test with a scratch org that has the industry feature flag** — industry API endpoints are not present in standard Developer Edition orgs. Use a partner developer org provisioned with the relevant industry feature, or an industry scratch org with the feature enabled in `project-scratch-def.json`.
7. **Confirm no direct DML is used for industry objects** — verify that no Apex, Flow, or REST CRUD operates directly on `InsurancePolicy`, `InsurancePolicyCoverage`, or `ServicePoint` status fields. All mutations must flow through the industry Connect API or Integration Procedure layer.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Industry license confirmed in target org (Insurance Cloud, Communications Cloud, or E&U Cloud)
- [ ] All entity references in request payloads use Salesforce record IDs, not names or catalog codes
- [ ] For Comms Cloud: Direct Access is the integration path; no MuleSoft gateway dependency exists
- [ ] No direct DML on InsurancePolicy, InsurancePolicyCoverage, or ServicePoint status fields
- [ ] Error handling covers vertical-specific response codes (409, 422, TM Forum error schema)
- [ ] API tested against an industry-licensed org or scratch org with the feature flag enabled
- [ ] Integration Procedure delegation confirmed for E&U (`sfiEnergy_UpdateAssetStatus`) and Service Process operations

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **TM Forum API product lookup is ID-only** — Passing a product catalog code or product name in a TMF679 or TMF622 request body results in a 404 or silent validation failure. The TM Forum endpoint implementations in Salesforce resolve all product and offering references by Salesforce record ID exclusively. There is no name-to-ID resolution built into the API layer.
2. **Insurance Connect API does not fall back to DML on error** — If the Connect API call fails (e.g., missing coverage type), the entire transaction is rolled back, including parent policy records. No partial records are persisted. Practitioners who check `InsurancePolicy` for a record after a failed API call and find none often incorrectly conclude the API did not attempt the operation.
3. **MuleSoft gateway deprecation is a breaking change in Winter '27** — Orgs that integrated with Communications Cloud through the legacy MuleSoft gateway endpoint will lose connectivity after the deprecation date. The error will surface as an unreachable endpoint, not a Salesforce API error, making diagnosis difficult at the time of failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Endpoint and payload specification | Correct URL path, HTTP method, and JSON body structure for the target industry API operation |
| Error handling matrix | Mapping of HTTP status codes and error code values to retry/escalation logic |
| Integration Procedure delegation diagram | Shows the Connect API → Integration Procedure chain for E&U and Service Process operations |
| Access model confirmation | Direct Access vs deprecated gateway assessment for Communications Cloud |

---

## Related Skills

- `omnistudio/dataraptor-patterns` — DataRaptor transformations are frequently used to map inbound industry API payloads to OmniScript or Integration Procedure inputs
- `admin/industries-process-design` — Service Process Studio process definition is the configuration prerequisite for Service Process Studio Connect API calls
- `omnistudio/industries-cpq-vs-salesforce-cpq` — TMF order APIs interact with the Industries CPQ catalog layer in Communications Cloud
