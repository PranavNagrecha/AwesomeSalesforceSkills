---
name: clinical-data-requirements
description: "Use this skill when defining clinical data model requirements for Health Cloud: HL7/FHIR data mapping, interoperability requirements, FHIR R4-aligned object activation, CodeableConcept constraints, and middleware translation requirements. NOT for the field-level mapping work itself — use data/fhir-data-mapping. NOT for choosing legacy HC24__ EHR objects vs standard clinical objects — use data/health-cloud-data-model."
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
  - "turn on the clinical data model in a Health Cloud sandbox before an EHR integration"
  - "map FHIR Condition resources to HealthCondition and CodeSetBundle"
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
  - data/health-cloud-data-model
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Clinical Data Requirements

Use this skill when defining clinical data model requirements for Health Cloud: enabling the FHIR R4-aligned clinical data model, mapping FHIR resources to Salesforce objects, identifying CodeableConcept and cardinality constraints, and specifying middleware translation for HL7 and FHIR integration. It does NOT cover migration procedures, Apex integration code, or generic data architecture.

Licence gate: the clinical data model is part of Health Cloud and Life Sciences Cloud and is documented as available in Enterprise and Unlimited Editions. The developer guide is titled "Agentforce Health Developer Guide" in Summer '26.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the FHIR-Aligned Clinical Data Model org pref is enabled. The guide says: "To enable these objects in your org, go to FHIR R4 Support Settings in Setup and enable the FHIR-Aligned Clinical Data Model org pref." It also says some objects exist before the pref is on because other data models use them (for example `CareObservation`, `CodeSet`, `CodeSetBundle`, `Identifier`, `PersonName`). In metadata the setting is `IndustriesSettings.enableClinicalDataModel` (API 51.0, default false).
- Identify the source systems (EHR, payer, HIE) and their standard: FHIR R4, HL7 v2.3, or custom. Each needs a different translation approach.
- Confirm whether the org is new or legacy. "Starting with the Spring '23 release, new customers won't be able to create records in the packaged EHR objects that have counterpart standard objects in the FHIR R4-aligned data model."
- Identify CodeableConcept-heavy resources (Condition, Observation, Procedure). `CodeSetBundle` flattens a CodeableConcept's codings to 15 references (`CodeSet1Id` through `CodeSet15Id`).

---

## Questions to Ask Before Configuring

Ask these before mapping a single resource. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which FHIR resources or HL7 v2.3 messages arrive, and from which systems?" | The org pref, the objects, and the middleware all depend on the resource list (gotchas 1, 5) | A resource inventory with volumes and source systems | Objects enabled and mapped before integration build starts |
| "Do any source concepts carry more than 15 codings?" | `CodeSetBundle` holds 15 coding references (gotcha 2) | A coding-priority policy per resource | Deliberate, documented truncation instead of silent loss |
| "Is this a new org or one that already holds `HC24__` EHR data?" | New customers cannot create records in packaged EHR objects that have standard counterparts (gotcha 3) | The target objects per data type, and a migration decision | No integration written against objects the org cannot write |
| "Will patients or caregivers see clinical data in an Experience Cloud site?" | Community users need the FHIR R4 for Experience Cloud Sites permission set (gotcha 6) | The external audience and the records they may see | Portal access designed with the right permission set from the start |
| "Which source fields are required in Salesforce but optional in FHIR?" | `condition.code` is 0..1 in FHIR but `HealthCondition.ConditionCodeId` is 1..1 (gotcha 4) | A rule for records that arrive without the field | Fewer rejected loads and a defined error path |
| "How do multi-line addresses and multiple names arrive?" | `address.line` maps to a single `Street` string, and names map to `PersonName` child records (gotcha 7) | Merge and split rules for the middleware | Demographics that render correctly in Health Cloud components |

What a proper requirements package adds over "just loading clinical data": every resource has a target object, every deviation from FHIR is handled on purpose in the middleware, and no record depends on an object the org cannot write.

---

## Core Concepts

### Activating the FHIR-Aligned Clinical Data Model

The org pref lives on the FHIR R4 Support Settings page in Setup. The guide lists which objects need it:

| Needs the org pref | Available without it |
|---|---|
| `AllergyIntolerance`, `ClinicalEncounter` (and its child objects), `ClinicalServiceRequest`, `DiagnosticSummary`, `HealthCondition`, `MedicationRequest`, `MedicationStatement`, `PatientHealthReaction`, `PatientImmunization`, `PatientMedicalProcedure`, `PatientMedicationDosage` | `CareObservation`, `CodeSet`, `CodeSetBundle`, `HealthcareProvider`, `Identifier`, `Medication`, `PersonLanguage`, `PersonName`, `Specimen` |

Enabling the pref also adds fields to standard objects, for example `ContactPointPhone.UsageType`, `Account.SourceSystemIdentifier`, `Contact.Gender`, and `Contact.DeceasedDate`. The deployable setting is in `references/metadata-examples.md`.

### Salesforce Is Not a 1:1 FHIR R4 Implementation

The guide states that "a middleware integration solution is required to convert messages from HL7 and FHIR-based systems to the fields and objects in Salesforce", and lists the deviations:

| FHIR construct | Salesforce implementation |
|---|---|
| CodeableConcept (0..* codings) | `CodeSetBundle` with 15 zero-to-one `CodeSet` references |
| Simple value-set codes | Picklists (for example `Identifier.IdUsageType`) |
| `code` data type | String (for example `CodeSet.Code`) |
| `uri` for code and identifier systems | String (`CodeSet.SourceSystem`, `Identifier.SourceSystem`) |
| Period, Quantity, Range, Ratio | Flattened into two or three fields, with a lookup to `UnitofMeasure` where a unit applies |
| HumanName | `PersonName` with `FirstName`, `LastName`, `FullName`, related to the person through `ParentRecordId` |

### HL7 v2.3

The clinical data model "also supports many of the HL7 v2.3 message types": ADT, ORM, ORU, MDM, VXU, and RDE messages "can be stored in Salesforce by mapping their constituent segments to fields in Salesforce standard objects". The guide documents segment mappings (PID, PV1, PV2, OBX, AL1, ORC, OBR, RXA, RXE, RXR, RXC). It does not describe a native HL7 v2 listener, so a translation layer still parses the message and writes the mapped fields.

### Legacy EHR Objects

New customers since Spring '23 cannot create records in packaged EHR objects that have counterpart standard objects, and future development targets the FHIR R4-aligned model. Typical pairs:

| Legacy packaged object | Standard counterpart |
|---|---|
| `HC24__EhrCondition__c` | `HealthCondition` |
| `HC24__EhrMedicationStatement__c`, `HC24__EhrMedicationPrescription__c` | `MedicationStatement`, `MedicationRequest` |
| `HC24__EHRProcedure__c` | `PatientMedicalProcedure` |
| `HC24__EhrObservation__c` | `CareObservation` |
| `HC24__EhrImmunization__c` | `PatientImmunization` |
| `HC24__EhrAllergyIntolerance__c` | `AllergyIntolerance` |

Earlier versions of this skill named `HC24__EhrMedication__c`, `HC24__EhrLabResult__c`, `PatientMedication`, and `MedicalProcedure`. None of those names appears in the guide. UNVERIFIED (2026-10-03): the pairing in this table is by resource meaning; the guide does not publish a one-to-one legacy mapping table.

---

## Common Patterns

### FHIR Patient Resource Mapping Requirements

**When to use:** Incoming FHIR R4 Patient resources from an EHR.

**How it works:**
- `Patient.name` maps to `PersonName` records whose `ParentRecordId` references the person's Account or Contact.
- `Patient.telecom` maps to `ContactPointPhone` and `ContactPointEmail` records.
- `Patient.address` maps to `ContactPointAddress`; multiple `line` values must be merged into one `Street` string, and `type` and `text` are not supported.
- `Patient.identifier` maps to `Identifier` records.
- `Patient.gender` and deceased details map to `Contact.Gender` and `Contact.DeceasedDate`, fields added by the org pref.

Middleware must create the Person Account first, then the child records. UNVERIFIED (2026-10-03): that the Patient Card and Timeline components read only the child objects is stated by earlier versions of this skill, not by the guide.

### HL7 v2.3 Inbound Requirements

**When to use:** An EHR sends HL7 v2.3 ADT, ORM, ORU, MDM, VXU, or RDE messages.

**How it works:**
1. List the message types and segments in scope.
2. Map each segment field to the standard object field documented in the guide's HL7 v2.3 segment tables.
3. Choose the translation layer that parses the message and calls the Salesforce APIs.
4. Define error handling for unrecognized segments and out-of-range values.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Health Cloud org, clinical data needed | Enable the FHIR-Aligned Clinical Data Model org pref first | Most clinical objects do not exist without it |
| EHR sends FHIR R4 bundles | Middleware translation still required | The guide requires middleware; complex types are flattened |
| Source has more than 15 codings per concept | Priority-based truncation in middleware | `CodeSetBundle` holds 15 references |
| Org holds legacy `HC24__` EHR data | Plan migration to standard objects | New development targets the FHIR R4-aligned model |
| HL7 v2.3 messages from EHR | Segment-to-field mapping in a translation layer | Mappings are documented; parsing is not native |
| Portal users must see clinical data | FHIR R4 for Experience Cloud Sites permission set | Required for community users |

---

## Recommended Workflow

1. **Enable the org pref.** Turn on the FHIR-Aligned Clinical Data Model (Setup, FHIR R4 Support Settings, or `IndustriesSettings.enableClinicalDataModel`), then confirm the objects exist with a SOQL query.
2. **Inventory source clinical data.** FHIR resources or HL7 v2.3 messages, cardinality, required and optional fields, and coding systems (SNOMED CT, LOINC, ICD-10, RxNorm).
3. **Map resources to objects.** Use the guide's FHIR v4.0 mapping tables. Flag every deviation: flattened types, the 15-coding cap, fields that are 1..1 in Salesforce but 0..1 in FHIR, and unsupported elements.
4. **Set coding-priority rules.** For concepts with more than 15 codings, define which systems fill the 15 slots, in order.
5. **Specify middleware.** Flattening, truncation, address-line merging, identifier mapping, HL7 v2.3 parsing, and error handling.
6. **Assess legacy objects.** If `HC24__` EHR data exists, scope the migration as a separate workstream and target standard objects for all new integrations.

---

## Review Checklist

- [ ] FHIR-Aligned Clinical Data Model org pref enabled or planned, with the objects it unlocks listed
- [ ] Every in-scope FHIR resource or HL7 v2.3 message mapped to Salesforce objects
- [ ] 15-coding limit handled with a documented priority policy
- [ ] FHIR deviations documented (flattening, cardinality, unsupported elements)
- [ ] Middleware requirements specified for every inbound source
- [ ] Legacy `HC24__` usage assessed and a migration decision recorded
- [ ] FHIR R4 for Experience Cloud Sites permission set planned if portal users need clinical data

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Most clinical objects need the org pref; some do not | Integration tests fail on missing objects, or teams wrongly wait for objects that already exist |
| 2 | 15 coding references per CodeableConcept | Codings past 15 are lost unless the middleware prioritizes |
| 3 | New customers cannot create records in packaged EHR objects with standard counterparts | Legacy-targeted integrations fail |
| 4 | Some fields are 1..1 in Salesforce but 0..1 in FHIR | Conditions without a code are rejected |
| 5 | HL7 v2.3 is a mapping, not a listener | A direct HL7 feed has nowhere to land without a translator |
| 6 | Portal access needs a specific permission set | Community users see nothing |
| 7 | Address lines and names have their own shapes | Demographics arrive truncated or in the wrong place |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FHIR-to-Salesforce field mapping | Field-level mapping for each in-scope resource |
| CodeableConcept constraint specification | Affected resources and the coding-priority policy |
| Middleware translation requirements | HL7 and FHIR transformation rules for the integration layer |
| Legacy EHR object migration assessment | Current `HC24__` usage and migration scope |
| Org pref deployment | `Industries.settings` with `enableClinicalDataModel` |

---

## Related Skills

- `data/health-cloud-data-model`: Health Cloud object reference and data model overview
- `data/fhir-data-mapping`: FHIR resource to Health Cloud object mapping reference
- `apex/fhir-integration-patterns`: FHIR R4 integration code patterns and API usage
- `admin/care-coordination-requirements`: referrals and care episodes that depend on the clinical data model
