---
name: fhir-integration-patterns
description: "Use this skill when implementing FHIR R4 integration for Health Cloud in code: inbound and outbound FHIR REST API patterns, CDS Hooks via MuleSoft middleware, SMART on FHIR setup, and HL7 v2 to FHIR R4 conversion. Trigger keywords: FHIR R4 integration, Healthcare API, CodeSetBundle, HealthCondition mapping, ingest a FHIR bundle. NOT for mapping a FHIR resource to Health Cloud objects field by field — use data/fhir-data-mapping. NOT for choosing the EHR sync topology or MuleSoft Accelerator design — use architect/fhir-integration-architecture."
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
  - "map a FHIR Condition with several codings into HealthCondition and CodeSetBundle"
  - "call the Salesforce Healthcare API to read a patient's conditions"
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
  - Apex normalization class and test for FHIR Condition to HealthCondition, CodeSetBundle, and CodeSet
dependencies:
  - admin/clinical-data-requirements
  - apex/health-cloud-apis
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# FHIR Integration Patterns for Health Cloud

Use this skill when implementing FHIR R4 integration for Health Cloud: normalizing inbound FHIR resources into the FHIR-aligned Clinical Data Model, calling the Salesforce Healthcare API, routing CDS Hooks and HL7 v2 through MuleSoft, and authorizing client apps. It covers integration code and patterns, not Health Cloud admin setup or generic REST development.

---

## Before Starting

- Is the **FHIR-Aligned Clinical Data Model** org preference enabled (Setup > FHIR R4 Support Settings)? Objects such as HealthCondition, AllergyIntolerance, ClinicalEncounter, and MedicationRequest need it; CareObservation, CodeSet, CodeSetBundle, Identifier, and PersonName do not.
- Which **direction and surface**? Inbound records written to the Clinical Data Model through the standard APIs, or the **Salesforce Healthcare API** (FHIR R4 REST at `api.healthcloud.salesforce.com`, regional hosts for EU, CA, and AU).
- What does the source send? FHIR R4 resources, HL7 v2 messages, or C-CDA documents. MuleSoft Direct Integration apps exist for HL7 v2 event ingestion, EMR synchronization, CDS Hooks, bulk FHIR data, and more.
- Does the org still use packaged EHR objects (`HC24__Ehr...__c`)? Starting with Spring '23, new customers can't create records in packaged EHR objects that have counterpart standard objects.
- Will Experience Cloud users see clinical records? They need the **FHIR R4 for Experience Cloud Sites** permission set.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which FHIR resources and which code systems will arrive, and how many codings per concept?" | A CodeableConcept flattens to at most 15 CodeSet references on CodeSetBundle, and Salesforce doesn't validate codes | A coding priority rule and a truncation log | No silently dropped codes and no invalid codes stored |
| "Will we write through the Clinical Data Model objects or call the Salesforce Healthcare API?" | They are different surfaces: standard sObject APIs versus FHIR R4 REST at `api.healthcloud.salesforce.com` with its own scopes and limits | The chosen surface per flow | Calls that use the right host, scopes, and limits |
| "How many requests can run at once, and how big are the batches?" | The Healthcare API guide recommends at most five concurrent requests and allows up to 30 Bundle entries, up to 10 of them reads or searches | Throttling and batch sizing in middleware | No failed calls under load |
| "What OAuth scopes will each client request?" | The Healthcare API uses custom scopes such as `user_condition_read`; SMART-style wildcard scopes aren't supported | A scope list per client app | Clients that authorize on the first try with least privilege |
| "Do any clinicians need decision support inside the EHR?" | CDS Hooks reaches Health Cloud through a MuleSoft Direct Integration app; Salesforce itself is not the CDS service | A MuleSoft CDS Hooks service in the design | An EHR integration that the EHR can actually call |
| "Is any code still writing HC24 EHR objects?" | New customers can't create records in packaged EHR objects that have standard counterparts | A migration list to HealthCondition, ClinicalEncounter, and the rest | Integrations that keep working on new orgs |

What a proper integration adds over posting FHIR JSON at Salesforce: every resource lands in the right objects with its codings preserved up to the documented limit, clients use supported scopes and stay within the concurrency guidance, and decision support runs where the platform supports it.

---

## Core Concepts

### The Clinical Data Model is FHIR-aligned, not a FHIR server

The Health Cloud developer guide says a middleware integration solution is required to convert HL7 and FHIR messages to Salesforce fields and objects, and lists the deviations:

| FHIR construct | Salesforce representation |
|---|---|
| CodeableConcept (0..* Coding) | CodeSetBundle with `CodeSet1Id` to `CodeSet15Id`; `text` maps to `CodeSetBundle.Name` |
| Coding | CodeSet: `SourceSystem` (system), `SystemVersion`, `Code`, `Name` (display), `IsPrimary` (userSelected) |
| Simple value sets | Picklists (for example `Identifier.IdUsageType`) |
| Period | Start and end date fields (for example `OnsetStartDateTime`, `OnsetEndDateTime`) |
| Quantity, Range, Ratio | Value and unit fields, lower and upper limits, numerator and denominator, with a UnitOfMeasure lookup |
| HumanName | PersonName (`FirstName`, `LastName`, `FullName`, `ParentRecordId`) |
| Address.line (0..*) | One `ContactPointAddress.Street` string; merge lines first |

For Condition to HealthCondition: `code` is a required lookup to CodeSetBundle (`ConditionCodeId`, 1..1, where FHIR allows 0..1); `subject` is a master-detail to Account and doesn't support groups; `category` becomes a single picklist; `onsetAge`, `onsetRange`, and `onsetString` aren't supported.

### Salesforce Healthcare API

| Item | Value (Salesforce Healthcare API guide) |
|---|---|
| URL shape | `https://api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource>`; sandbox adds `/sandBox/` after the host |
| Modules | `admin`, `bundle`, `care_management`, `clinical-summary`, `clinical-diagnostics`, `clinical-workflow`, `clinical-medications`, `prior-auth`, `forms` |
| Bundle | Batch type only; up to 30 entries per call, up to 10 of them reads or searches; dependent failures return 424 |
| Authorization | External client app with OAuth 2.0 and custom scopes such as `user_condition_read`, `system_all_write` |
| Guidance | About 3 seconds per call; keep concurrent requests at five or fewer; no FHIR semantic (code set) validation |
| Availability | Winter '23 (API 56.0) and later; a $0 SKU is required |

### CDS Hooks and HL7 v2 go through MuleSoft

The MuleSoft Direct Integration apps include a CDS Hooks integration that connects EMR workflows to clinical decision support from Health Cloud, and an event-based ingestion app that consumes HL7 v2 feeds into the Clinical Data Model. The Coverage Requirement Discovery data model maps CDS Hooks fields for payer use cases (Hls Clinical Decision Support permission set).

---

## Common Patterns

### Inbound FHIR R4 to the Clinical Data Model

1. Middleware receives the FHIR resource or bundle from the EHR.
2. It resolves the patient (Person Account) and upserts CodeSet records by `SourceSystem` and `Code`.
3. It builds a CodeSetBundle with up to 15 CodeSet references and records any truncation.
4. It flattens Period, Quantity, Range, and Ratio values and maps picklist values.
5. It writes HealthCondition (or the target object) and Identifier child records.
6. It retries transient failures and acknowledges the source.

An Apex version of steps 2 to 5 with a test class is in `references/code-examples.md`.

### Reading or writing through the Healthcare API

The client authorizes with the custom scopes it needs, calls `GET https://api.healthcloud.salesforce.com/clinical-summary/fhir-r4/v1/Condition` (with search parameters) or posts a batch Bundle to the `bundle` module, throttles to five concurrent requests, and handles 424 responses for dependent entries.

---

## Decision Guidance

| Situation | Pattern | Middleware required? |
|---|---|---|
| EHR sends FHIR R4 resources to Health Cloud | Middleware normalization into Clinical Data Model objects | Yes (the guide requires a middleware solution) |
| External FHIR client reads or writes clinical data | Salesforce Healthcare API with custom scopes | No MuleSoft purchase needed to call the API |
| CDS Hooks cards in the EHR | MuleSoft CDS Hooks Direct Integration app | Yes (MuleSoft) |
| HL7 v2 feeds | MuleSoft event-based ingestion app | Yes (MuleSoft) |
| SMART on FHIR client | External client app with Healthcare API custom scopes | No; wildcard SMART scopes aren't supported |

---

## Recommended Workflow

1. **Confirm prerequisites.** Org preference, permission sets (including FHIR R4 for Experience Cloud Sites for portal users), Healthcare API terms and SKU if that surface is used.
2. **Inventory resources and codings.** Use the EHR CapabilityStatement and sample payloads; count codings per concept against the 15-reference limit.
3. **Map field by field.** Use the guide's "Mapping FHIR v4.0 to Salesforce Standard Objects" tables; record unsupported elements.
4. **Build the normalizer.** MuleSoft app or custom code; start from the Apex example in `references/code-examples.md`.
5. **Set authorization and throttling.** Custom scopes per client, five concurrent requests, Bundle sizes within 30 entries.
6. **Test and scan.** Edge cases (no coding, more than 15 codings, onsetPeriod, unsupported onsetAge), then `python3 scripts/check_fhir_integration_patterns.py --manifest-dir force-app/main/default`.

---

## Review Checklist

- [ ] FHIR-Aligned Clinical Data Model org preference enabled where the target objects need it
- [ ] Field mapping documented from the guide's tables, with unsupported elements listed
- [ ] CodeableConcepts capped at 15 codings with a priority rule and truncation log
- [ ] Codes validated upstream (Salesforce doesn't validate code sets)
- [ ] No writes to packaged `HC24__Ehr...__c` objects that have standard counterparts
- [ ] Healthcare API clients use custom scopes, no wildcard SMART scopes
- [ ] Middleware throttles to five concurrent Healthcare API requests and keeps Bundles at 30 entries or fewer
- [ ] CDS Hooks and HL7 v2 run through MuleSoft

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The two that cause the most rework: Salesforce does not validate FHIR codes, and SMART-style wildcard scopes are not supported by the Healthcare API.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FHIR resource field mapping | Field-level mapping with deviations and unsupported elements |
| Normalization code | Middleware flow or Apex class with tests |
| Client authorization spec | External client app, custom scopes per resource and method |
| CDS Hooks and HL7 v2 design | MuleSoft Direct Integration app selection |

---

## Related Skills

- `apex/health-cloud-apis`: Health Cloud API endpoint selection
- `admin/clinical-data-requirements`: FHIR R4 object activation and data model requirements
- `data/fhir-data-mapping`: detailed FHIR resource to Salesforce object mapping reference
- `architect/fhir-integration-architecture`: EHR sync topology and MuleSoft design
