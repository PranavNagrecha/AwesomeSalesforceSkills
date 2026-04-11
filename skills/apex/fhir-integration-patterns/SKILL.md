---
name: fhir-integration-patterns
description: "Use this skill when implementing FHIR R4 integration patterns for Health Cloud: FHIR resource mapping to Salesforce objects, REST API patterns for inbound/outbound FHIR, CDS Hooks via MuleSoft middleware, SMART on FHIR setup, and HL7 v2 to FHIR R4 conversion. NOT for generic REST API integration, standard Salesforce API patterns unrelated to FHIR, or Health Cloud admin setup."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "How do I implement FHIR R4 integration from an EHR into Salesforce Health Cloud?"
  - "FHIR R4 resource mapping to Salesforce clinical objects has field cardinality differences"
  - "How to set up CDS Hooks with Salesforce Health Cloud using MuleSoft"
  - "SMART on FHIR OAuth setup for Health Cloud patient-facing FHIR app"
  - "Legacy EHR objects frozen in Spring 2023 and all new integration must target FHIR R4 standard objects"
tags:
  - health-cloud
  - fhir-r4
  - integration
  - cds-hooks
  - smart-on-fhir
  - mulesoft
  - hl7-v2
  - fhir-mapping
inputs:
  - Health Cloud org with FHIR R4 Support Settings enabled
  - Source EHR system FHIR R4 capability statement or HL7 v2 message types
  - Integration pattern requirements (inbound, outbound, real-time, batch)
outputs:
  - FHIR resource to Salesforce object field mapping with deviation documentation
  - Inbound FHIR integration architecture (middleware → Salesforce)
  - Outbound FHIR integration architecture (Salesforce → external FHIR client)
  - CDS Hooks middleware architecture (MuleSoft required)
  - SMART on FHIR OAuth app registration requirements
dependencies:
  - admin/clinical-data-requirements
  - apex/health-cloud-apis
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FHIR Integration Patterns for Health Cloud

Use this skill when implementing FHIR R4 integration patterns for Health Cloud: mapping FHIR resources to Salesforce clinical objects, building inbound/outbound FHIR REST API patterns, implementing CDS Hooks via MuleSoft, and setting up SMART on FHIR for patient-facing applications. This skill covers FHIR integration code and architecture patterns. It does NOT cover Health Cloud admin setup, generic REST API development, or standard Salesforce integration patterns unrelated to clinical FHIR standards.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm FHIR R4 Support Settings are enabled (`FHIR-Aligned Clinical Data Model` org preference). Without this, FHIR R4-aligned objects are unavailable.
- Determine the FHIR version of the source EHR: FHIR R4, FHIR STU2/DSTU2, or HL7 v2.x. Each requires a different translation approach. Salesforce's FHIR implementation targets R4 only.
- Identify integration direction: inbound (EHR → Salesforce), outbound (Salesforce → EHR/payer), or bidirectional. Each direction has different pattern requirements.
- Confirm whether CDS Hooks is in scope. There is NO native Salesforce endpoint that serves CDS Hooks responses. CDS Hooks requires MuleSoft as middleware to translate between CDS Hook service calls and Salesforce platform logic.
- Identify legacy EHR object usage. Starting Spring '23, new orgs cannot write to legacy packaged EHR objects (`HC24__EhrCondition__c`, etc.). All new integration must target FHIR R4-aligned standard objects.

---

## Core Concepts

### Salesforce FHIR R4 Deviations from Spec

Salesforce's FHIR R4 implementation deliberately deviates from the HL7 spec in key ways that affect integration code:

1. **CodeableConcept cardinality** — FHIR CodeableConcept supports 0-to-many Coding elements. Salesforce flattens this to a single lookup on most objects, with an optional CodeSetBundle for multi-coding (max 15).
2. **Complex type flattening** — FHIR Period, Quantity, Range, Ratio are flattened into multi-field representations rather than nested JSON.
3. **Mandatory fields differ** — Some FHIR optional fields are required in Salesforce (e.g., `Condition.code` has a required CodeSet lookup in SF vs. 0:1 in FHIR spec).
4. **No raw FHIR bundle persistence** — inbound FHIR payloads cannot be stored as-is; they must be normalized to the Salesforce flat object model by middleware.

Every field-level mapping must be verified against the official Salesforce FHIR R4 mapping guide — do not assume 1:1 field equivalence.

### CDS Hooks Requires MuleSoft Middleware

CDS (Clinical Decision Support) Hooks is an HL7 standard for injecting real-time clinical decision support alerts into EHR workflows. A CDS Hook service receives an HTTP POST when a clinician opens a patient record or orders a medication, and must return card recommendations.

Salesforce has NO native CDS Hook service endpoint. To implement CDS Hooks with Salesforce:
1. MuleSoft acts as the CDS Hook service (receives HTTP POST from EHR).
2. MuleSoft queries Salesforce (ClinicalAlert records, CareGap records, FlexCard data) to build the CDS response.
3. MuleSoft returns the CDS Hook card JSON to the EHR.

Any architecture that assumes Salesforce can directly serve CDS Hook responses is incorrect.

### SMART on FHIR for Patient Apps

SMART (Substitutable Medical Applications, Reusable Technologies) on FHIR is an OAuth-based authorization framework for EHR-integrated clinical applications. For SMART on FHIR with Salesforce Health Cloud:
- Register a Connected App with the `healthcare` and `api` OAuth scopes.
- Configure the SMART launch parameter in the Connected App metadata.
- Patient-facing apps need the FHIR R4 for Experience Cloud permission set on portal users.
- The SMART launch context (patient ID, encounter context) is passed as a JWT claim from the EHR.

---

## Common Patterns

### Inbound FHIR R4 Integration (EHR → Salesforce)

**When to use:** An EHR sends patient clinical data (Conditions, Observations, Medications) to Salesforce on an event-driven or scheduled basis.

**How it works:**
1. EHR sends FHIR R4 bundle to middleware (MuleSoft).
2. Middleware validates the FHIR bundle and checks resource types.
3. Middleware translates FHIR resource fields to Salesforce object fields: complex type flattening, CodeableConcept normalization, identifier resolution.
4. Middleware calls Salesforce FHIR Healthcare API or SObject API to create/update clinical records.
5. Salesforce returns response; middleware handles errors and implements retry for transient failures.
6. Middleware sends acknowledgment to EHR.

**Why not the alternative:** Sending raw FHIR bundles directly to Salesforce APIs without translation results in silent data loss (unmapped fields dropped), validation errors (required field differences), and incorrect data (complex type flattening not applied).

### Outbound FHIR R4 Query (Salesforce → External FHIR Client)

**When to use:** An external FHIR client (payer, HIE, patient app) needs to query patient clinical data from Salesforce in FHIR R4 format.

**How it works:**
1. External FHIR client authenticates via OAuth (with `healthcare` scope for FHIR Healthcare API).
2. Client queries Salesforce FHIR Healthcare API: `GET /services/data/v60.0/healthcare/fhir/R4/Patient/{id}/$everything`
3. Salesforce returns a FHIR Bundle with up to 30 entries.
4. For large result sets, client must implement FHIR pagination (`_count` and `_page` parameters).
5. Client processes each entry and maps FHIR resources to its own data model.

---

## Decision Guidance

| Situation | Pattern | Middleware Required? |
|---|---|---|
| EHR sends FHIR R4 bundles to Salesforce | Inbound FHIR with middleware translation | Yes (MuleSoft or custom) |
| External FHIR client reads Salesforce data | Outbound FHIR Healthcare API | No middleware needed |
| CDS Hooks alerts to EHR | MuleSoft CDS Hook service | Yes (MuleSoft required) |
| HL7 v2 from EHR to Salesforce | HL7 → FHIR translation middleware | Yes (MuleSoft HL7 connector) |
| SMART on FHIR app launch | Connected App + healthcare scope | No middleware needed |

---

## Recommended Workflow

1. **Verify FHIR prerequisites** — confirm FHIR R4 Support Settings enabled, legacy EHR object status assessed, integration direction and pattern determined.
2. **Obtain source FHIR capability statement** — request the EHR's CapabilityStatement resource to understand which FHIR resources it supports, which FHIR version it uses, and which operations (read, search, write) are available.
3. **Build field-level mapping** — for each FHIR resource in scope, map every field to its Salesforce equivalent using the official FHIR R4 mapping guide. Document all deviation points: complex types to flatten, CodeableConcept truncation, mandatory field differences.
4. **Design middleware layer** — specify the middleware (MuleSoft or custom) responsible for translation, error handling, and retry. For CDS Hooks, MuleSoft is required.
5. **Implement and test field mappings** — implement mapping logic in middleware. Test with representative FHIR payloads including edge cases: missing optional fields, multi-coding CodeableConcepts, complex types.
6. **Configure SMART on FHIR** — if patient-facing apps are in scope, configure the Connected App with correct OAuth scopes, SMART launch parameters, and permission set assignments for portal users.

---

## Review Checklist

- [ ] FHIR R4 Support Settings enabled
- [ ] Source EHR's FHIR version confirmed (R4 only natively supported)
- [ ] Field-level mapping documented with deviation points identified
- [ ] Middleware layer specified for inbound translation
- [ ] CDS Hooks architecture uses MuleSoft as the CDS service endpoint (not Salesforce directly)
- [ ] `healthcare` OAuth scope configured on Connected App
- [ ] Legacy HC24__ EHR objects NOT used in new integration

---

## Salesforce-Specific Gotchas

1. **Salesforce is not a 1:1 FHIR R4 server** — CodeableConcept cardinality, complex type flattening, and mandatory field differences mean every integration needs field-by-field validation against the official Salesforce FHIR R4 mapping guide. Never assume field names match the FHIR spec.

2. **CDS Hooks requires MuleSoft middleware** — there is no native Salesforce endpoint that serves CDS Hook responses. MuleSoft must act as the CDS service, querying Salesforce and assembling the CDS card response.

3. **Legacy HC24__ EHR objects are frozen in new orgs** — Spring '23+ orgs cannot write to legacy managed-package EHR objects. All new integrations must target FHIR R4-aligned standard objects. Documentation predating Spring '23 that references HC24__ objects is obsolete for new orgs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FHIR resource field mapping | Field-level mapping with deviation documentation for all in-scope resources |
| Middleware translation specification | Input/output format, transformation rules, error handling for each integration |
| CDS Hooks architecture diagram | MuleSoft → Salesforce CDS alert/gap query → card response flow |
| Connected App SMART on FHIR configuration | OAuth scopes, launch parameters, permission set assignments |

---

## Related Skills

- apex/health-cloud-apis — Health Cloud API endpoint selection and bundle limits
- admin/clinical-data-requirements — FHIR R4 object activation and data model requirements
- admin/fhir-data-mapping — Detailed FHIR resource to Salesforce object mapping reference
