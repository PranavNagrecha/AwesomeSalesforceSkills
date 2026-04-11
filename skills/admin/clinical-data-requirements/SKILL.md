---
name: clinical-data-requirements
description: "Use this skill when defining clinical data model requirements for Health Cloud: HL7/FHIR data mapping, interoperability requirements, FHIR R4-aligned object activation, CodeableConcept constraints, and middleware translation requirements. NOT for data migration procedures, Apex integration code, or generic data architecture unrelated to clinical interoperability."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "How do I enable and use the FHIR R4-aligned clinical data model in Health Cloud?"
  - "What objects does FHIR Patient resource map to in Salesforce Health Cloud?"
  - "CodeableConcept has too many codings and only 15 CodeSet references are available"
  - "Why are legacy EHR objects like EhrCondition no longer writable in new Health Cloud orgs?"
  - "HL7 v2 messages require middleware translation before storage in Salesforce clinical objects"
tags:
  - health-cloud
  - fhir-r4
  - clinical-data-model
  - hl7
  - interoperability
  - codeable-concept
inputs:
  - Health Cloud org with FHIR R4 Support Settings enabled (or to be enabled)
  - Source system data model (EHR/payer FHIR resource inventory or HL7 v2 message types)
  - Clinical use cases requiring data interoperability
outputs:
  - FHIR R4-aligned object activation checklist
  - FHIR resource to Salesforce object mapping for in-scope resources
  - CodeableConcept cardinality constraint documentation
  - Middleware translation requirements for HL7 v2 or non-conformant FHIR payloads
  - Legacy EHR object migration requirements (if applicable)
dependencies:
  - admin/health-cloud-patient-setup
  - admin/health-cloud-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Clinical Data Requirements

Use this skill when defining clinical data model requirements for Health Cloud: enabling the FHIR R4-aligned clinical data model, mapping FHIR resources to Salesforce objects, identifying CodeableConcept cardinality constraints, and specifying middleware translation requirements for HL7/FHIR integration. This skill covers requirements for clinical data interoperability design. It does NOT cover data migration procedures, Apex integration code, or generic data architecture not related to clinical standards.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether FHIR R4 Support Settings are enabled in Setup. The FHIR-Aligned Clinical Data Model must be explicitly enabled — it is NOT on by default in any Health Cloud org. Clinical objects like HealthCondition and CareObservation are unavailable until this org preference is enabled.
- Identify the source systems (EHR, payer, HIE) and the clinical data standards they use: FHIR R4, FHIR STU2, HL7 v2.x, or custom. Each requires different translation approaches before data can be stored in Salesforce.
- Confirm whether the org is a new org (Spring '23 or later) or a legacy org. New orgs cannot write to legacy packaged EHR objects (HC24__EhrCondition__c, HC24__EhrMedication__c) where FHIR R4-aligned standard objects exist. All new development must target FHIR R4-aligned standard objects.
- Identify CodeableConcept-heavy resources (Observation, Condition, Procedure). Salesforce's FHIR R4 implementation limits CodeableConcept.coding to 15 CodeSet references per object (CodeSet1Id through CodeSet15Id on CodeSetBundle). Sources with more than 15 codings per concept must have truncation logic designed in the middleware layer.

---

## Core Concepts

### FHIR R4-Aligned Clinical Data Model Activation

The FHIR-Aligned Clinical Data Model is an opt-in feature. To activate it:
1. Navigate to Setup > FHIR R4 Support Settings.
2. Enable "FHIR-Aligned Clinical Data Model."
3. For Experience Cloud portal access to FHIR objects: also enable "FHIR R4 for Experience Cloud."

Without this activation, FHIR R4-aligned objects (HealthCondition, CareObservation, PatientImmunization, AllergyIntolerance, etc.) are not available for data entry, querying, or API operations.

### Salesforce Is NOT a 1:1 FHIR R4 Implementation

Salesforce's FHIR R4 implementation deliberately deviates from HL7 FHIR R4 specification in important ways:

1. **Complex type flattening** — FHIR complex types (Period, Quantity, Range, Ratio, Coding) are flattened into multiple fields on the Salesforce object rather than represented as nested structures.
2. **CodeableConcept cardinality cap** — FHIR CodeableConcept supports zero-to-many Coding elements. Salesforce caps this at 15 CodeSet references (CodeSet1Id through CodeSet15Id on CodeSetBundle). Sources with more than 15 codings per concept must truncate in the middleware layer before storage.
3. **Mandatory vs. optional fields differ** — some FHIR fields that are optional in the spec are required in Salesforce (e.g., Condition.code has a required CodeSet lookup in Salesforce even though it is 0:1 in the FHIR spec).
4. **Identifiers as lookups not strings** — FHIR identifiers and references that are strings or complex types in the spec become lookup fields to specific Salesforce objects.

A middleware integration layer is required to translate FHIR payloads before storage. Direct FHIR bundle persistence without translation will silently drop or fail fields that do not map to the Salesforce implementation.

### Legacy EHR Object Deprecation

Starting Spring '23, Salesforce new orgs cannot write to legacy packaged EHR objects where FHIR R4-aligned standard objects exist:
- Deprecated: `HC24__EhrCondition__c` → Use: `HealthCondition`
- Deprecated: `HC24__EhrMedication__c` → Use: `PatientMedication`
- Deprecated: `HC24__EhrProcedure__c` → Use: `MedicalProcedure`
- Deprecated: `HC24__EhrLabResult__c` → Use: `CareObservation`

Legacy orgs with existing HC24__ object data must plan a migration to FHIR R4-aligned objects if they want to use new Health Cloud features, as future platform investment targets standard objects only.

---

## Common Patterns

### FHIR Patient Resource Mapping Requirements

**When to use:** Mapping incoming FHIR R4 Patient resources from an EHR system to Salesforce Health Cloud.

**How it works:**
The FHIR Patient resource does NOT map directly to a single Salesforce Account record. The mapping is:
- `Patient.name` → PersonName (child object linked to Account)
- `Patient.telecom` → ContactPointPhone / ContactPointEmail (child objects)
- `Patient.address` → ContactPointAddress (child object)
- `Patient.birthDate` / `Patient.gender` → Person Account fields (BirthDate, PersonGender)
- `Patient.identifier` → Individual Identifier records

Middleware must: (1) create the Person Account, (2) create all child contact point records, (3) create PersonName records with the correct type (official, nickname, etc.).

**Why not the alternative:** Writing Patient data directly to Account/Contact fields loses the structured data model that Health Cloud clinical UI components depend on. The PatientCard and Timeline components query child objects (PersonName, ContactPointPhone), not Account fields.

### HL7 v2 Inbound Requirements

**When to use:** An EHR sends HL7 v2 messages (ADT, ORU, ORM) that need to be stored in Salesforce Health Cloud.

**How it works:**
1. HL7 v2 messages must be translated to FHIR R4-aligned payloads by a middleware layer (e.g., MuleSoft HL7 connector, Mirth Connect, or a custom FHIR translator).
2. Salesforce does NOT natively receive or parse HL7 v2 messages.
3. Define the HL7 v2 message types in scope (ADT A01/A08 for admissions/updates, ORU R01 for lab results, ORM O01 for orders).
4. Map each HL7 segment/field to the corresponding FHIR R4 resource field.
5. Define error handling for unrecognized segments or out-of-range values.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Health Cloud org, clinical data needed | Enable FHIR R4 Support Settings first | Clinical objects not available without this activation |
| EHR sends FHIR R4 bundles | Middleware translation still required | Salesforce is not 1:1 FHIR; complex types need flattening |
| Source has >15 codings per concept | Truncation logic in middleware | CodeSetBundle caps at 15 CodeSet references |
| Legacy HC24__ EHR objects used | Plan migration to FHIR R4-aligned objects | Legacy objects receive no new Salesforce investment |
| HL7 v2 messages from EHR | Middleware HL7-to-FHIR translation | Salesforce does not natively parse HL7 v2 |

---

## Recommended Workflow

1. **Enable FHIR R4 Support Settings** — before any clinical data requirements work, confirm FHIR R4 Support Settings are enabled. This is the prerequisite for FHIR-aligned objects to be available.
2. **Inventory source system clinical data** — catalog all clinical data elements from the source EHR/payer: FHIR resources (or HL7 message types), cardinality, required vs. optional fields, coding systems used (SNOMED, LOINC, ICD-10, RxNorm).
3. **Map FHIR resources to Salesforce objects** — for each FHIR resource in scope, document the field-level mapping from FHIR to Salesforce using the official FHIR R4 to Salesforce mapping documentation. Flag all deviation points (flattened complex types, cardinality caps, mandatory field differences).
4. **Identify CodeableConcept constraints** — for any resource where coding systems produce more than 15 codings per concept (common with SNOMED hierarchies), specify middleware truncation logic. Prioritize which coding systems are included in the first 15 slots.
5. **Define middleware translation requirements** — specify the middleware layer responsible for: FHIR complex type flattening, CodeableConcept truncation, HL7 v2 to FHIR R4 conversion (if applicable), identifier mapping, and error handling.
6. **Document legacy EHR object migration needs** — if the org has existing HC24__ EHR object data, assess migration requirements to FHIR R4-aligned standard objects and plan the migration as a separate workstream.

---

## Review Checklist

- [ ] FHIR R4 Support Settings confirmed enabled (or activation planned)
- [ ] All FHIR resources in scope identified and mapped to Salesforce objects
- [ ] CodeableConcept 15-coding limit addressed for affected resources
- [ ] FHIR-to-Salesforce deviations documented (complex type flattening, cardinality differences)
- [ ] Middleware translation requirements specified for all inbound data
- [ ] Legacy HC24__ EHR object usage assessed and migration plan defined (if applicable)
- [ ] Experience Cloud FHIR R4 permission set planned (if portal access to clinical data needed)

---

## Salesforce-Specific Gotchas

1. **FHIR R4 Support Settings must be manually enabled** — the FHIR-Aligned Clinical Data Model is not active by default. All FHIR R4-aligned standard clinical objects are unavailable until this org preference is enabled in Setup. This is the first step for any clinical data requirements work.

2. **CodeableConcept coding is capped at 15 references** — FHIR's CodeableConcept supports unlimited codings. Salesforce caps this at 15 CodeSet references on the CodeSetBundle object. Any source system that sends more than 15 codings per concept will have data silently truncated if the middleware does not enforce the cap and prioritize the most important coding systems.

3. **Patient demographics go to child objects, not Account fields** — FHIR Patient demographic data (name, address, phone) maps to child objects in Salesforce (PersonName, ContactPointAddress, ContactPointPhone), not directly to Account fields. Writing directly to Account fields bypasses the structured model required by Health Cloud clinical UI components.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FHIR-to-Salesforce field mapping | Detailed field-level mapping for each in-scope FHIR resource |
| CodeableConcept constraint specification | Which resources are affected, how truncation is handled |
| Middleware translation requirements | HL7/FHIR transformation rules for the integration layer |
| Legacy EHR object migration assessment | Current HC24__ usage and migration scope |

---

## Related Skills

- admin/health-cloud-data-model — Health Cloud object reference and data model overview
- admin/fhir-data-mapping — FHIR resource to Health Cloud object mapping reference
- apex/fhir-integration-patterns — FHIR R4 integration code patterns and API usage
