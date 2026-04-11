---
name: health-cloud-data-model
description: "Use this skill when choosing, enabling, or querying Health Cloud clinical data objects — including the dual-layer architecture of legacy managed-package EHR objects (HC24__ namespace) and FHIR R4-aligned standard objects (ClinicalEncounter, HealthCondition, CarePlan, etc.). Covers setup prerequisites, object relationships, migration considerations, and integration strategy. NOT for standard Salesforce data model or generic CRM objects."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "Which Health Cloud clinical objects should I use for a new integration — HC24__ or the FHIR-aligned standard objects?"
  - "FHIR R4 clinical objects are not showing up in my Health Cloud org — how do I enable them?"
  - "I need to store patient conditions, encounters, or care plans in Salesforce Health Cloud — what objects should I use?"
  - "How do I migrate from legacy HC24__ EHR objects to the new FHIR-aligned standard objects?"
  - "What permissions are needed for Experience Cloud users to access clinical data in Health Cloud?"
tags:
  - health-cloud
  - data-model
  - clinical-data
  - fhir
  - healthcare
inputs:
  - "Health Cloud org edition and license type (Health Cloud license vs Life Sciences Cloud)"
  - "Whether the FHIR-Aligned Clinical Data Model org preference is enabled in the target org"
  - "Whether Experience Cloud (community) users need access to clinical objects"
  - "Spring '23 or later? (determines whether HC24__ write access is frozen for standard-object counterparts)"
  - "Integration source: FHIR R4 API, HL7 v2, or proprietary EHR system"
outputs:
  - "Recommended object layer (HC24__ vs FHIR R4-aligned) with rationale"
  - "Setup checklist for enabling FHIR-Aligned Clinical Data Model org preference"
  - "Mapping of FHIR R4 resources to Salesforce standard clinical objects"
  - "Migration guidance for moving from legacy packaged objects to standard objects"
  - "Permission and sharing configuration recommendations for clinical data access"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Health Cloud Data Model

Use this skill when selecting, enabling, or working with Health Cloud clinical data objects. Health Cloud ships two parallel clinical data layers, and choosing the wrong one — or failing to enable the right one — causes silent failures, missing objects, and blocked integrations.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the FHIR-Aligned Clinical Data Model org preference enabled?** Navigate to Setup > FHIR R4 Support Settings and confirm the toggle is on. Standard clinical objects (ClinicalEncounter, HealthCondition, etc.) do not exist in the org's schema until this preference is active.
- **What is the org's provisioning date?** Orgs provisioned before Spring '23 may have existing data in HC24__ packaged objects. Orgs provisioned after Spring '23 cannot write to HC24__ objects where a standard-object counterpart exists.
- **Are Experience Cloud (community) users involved?** If so, the "FHIR R4 for Experience Cloud" permission set must be assigned in addition to the org preference.
- **What is the integration source format?** FHIR R4 REST integrations map cleanly to standard objects. HL7 v2 or proprietary EHR payloads may require transformation before they fit the standard-object schema.

---

## Core Concepts

### Dual-Layer Clinical Data Architecture

Health Cloud ships with two distinct clinical object layers that coexist in the same org but serve different populations:

**Layer 1 — Legacy Managed-Package EHR Objects (HC24__ namespace)**
These are custom objects delivered inside the Health Cloud managed package, identified by the `HC24__` namespace prefix (e.g., `HC24__EhrCarePlan__c`, `HC24__EhrCondition__c`, `HC24__EhrMedication__c`, `HC24__EhrEncounter__c`). They predate the FHIR standard and were the only clinical storage option before Spring '23. As of Spring '23, Salesforce froze write access to HC24__ objects where a standard-object counterpart exists. Orgs that were using these objects before the cutoff can still read existing data, but cannot write new records to the frozen objects.

**Layer 2 — FHIR R4-Aligned Standard Objects**
These are first-class Salesforce standard objects introduced to align Health Cloud with the HL7 FHIR R4 standard. They include:

| FHIR R4 Resource | Salesforce Standard Object |
|---|---|
| Patient | PersonAccount (with HC record type) |
| Encounter | ClinicalEncounter |
| Condition | HealthCondition |
| CarePlan | CarePlan |
| AllergyIntolerance | AllergyIntolerance |
| Immunization | PatientImmunization |
| MedicationRequest | MedicationRequest |
| Procedure | ClinicalProcedure |
| Observation | ClinicalObservation |
| Goal | Goal (Health Cloud record type) |

These objects require the FHIR-Aligned Clinical Data Model org preference to be active. They do not appear in Object Manager or SOQL until that preference is enabled.

### FHIR-Aligned Clinical Data Model Org Preference

The org preference is the gating control for the entire standard-object layer. Without it:
- Standard clinical objects are absent from the schema
- SOQL queries against these objects fail with "object not found" errors
- Data Loader and Apex code that reference these objects fail at compile or runtime

To enable: Setup > FHIR R4 Support Settings > toggle "FHIR-Aligned Clinical Data Model" to ON. This is a one-way preference in most orgs — verify with Salesforce support before disabling in production.

### Experience Cloud Permission Boundary

Experience Cloud (community) users are governed by a separate permission layer. Even when the org preference is active, Experience Cloud users cannot access standard clinical objects unless the **"FHIR R4 for Experience Cloud"** permission set is assigned to their profiles or directly to users. This is a distinct permission from the standard Health Cloud user permissions. Patient portal users accessing their own CarePlan or HealthCondition records need this permission set.

### Object Relationships and Key Fields

Standard clinical objects relate to each other through standard lookup fields:

- `ClinicalEncounter.AccountId` — links to the patient's Person Account
- `HealthCondition.ClinicalEncounterId` — links a condition to the encounter where it was diagnosed
- `CarePlan.AccountId` — links the care plan to the patient
- `AllergyIntolerance.AccountId` — links to the patient's Person Account
- `PatientImmunization.AccountId` — links to the patient's Person Account
- `MedicationRequest.ClinicalEncounterId` — links prescriptions to the originating encounter
- `ClinicalProcedure.ClinicalEncounterId` — links procedures to their encounter

External system identifiers (e.g., EHR encounter IDs) should be stored using an External ID field or a dedicated `ExternalId__c` custom field on the relevant object. Do not use Salesforce record IDs as the primary cross-system key.

---

## Common Patterns

### Pattern: New FHIR R4 Integration Using Standard Objects

**When to use:** Any new integration built on Spring '23 or later. Any org that does not have existing HC24__ data. Any integration consuming or producing FHIR R4 REST payloads.

**How it works:**
1. Enable the FHIR-Aligned Clinical Data Model org preference in Setup.
2. Verify that target standard objects appear in Object Manager (ClinicalEncounter, HealthCondition, etc.).
3. Map incoming FHIR R4 resource fields to the corresponding standard-object fields. Use the Health Cloud Object Reference for the complete field mapping.
4. Upsert records using an External ID field to support idempotent re-ingestion from the source EHR.
5. Assign the FHIR R4 for Experience Cloud permission set if patient portal access is required.

**Why not HC24__:** HC24__ objects are frozen for new writes where standard counterparts exist. Integrations that attempt to insert or update HC24__ objects post-Spring '23 will receive DML errors. HC24__ objects also do not expose FHIR-compliant field names, making bidirectional FHIR integration harder to maintain.

### Pattern: Migrating Existing HC24__ Data to Standard Objects

**When to use:** Orgs that have existing clinical data in HC24__ objects and want to move to the standard-object layer for new integrations or to enable FHIR R4 APIs.

**How it works:**
1. Audit existing HC24__ data volume by object (HC24__EhrEncounter__c, HC24__EhrCondition__c, etc.) using SOQL count queries.
2. Build a field mapping document translating HC24__ field API names to their standard-object counterparts using the Health Cloud Object Reference.
3. Extract HC24__ records via Bulk API 2.0 or Data Loader.
4. Transform and load into standard objects, preserving the original HC24__ record ID in an External ID or reference field for traceability.
5. Update all downstream automations (Flows, Apex, reports) to reference standard objects rather than HC24__ objects.
6. Validate that the FHIR-Aligned Clinical Data Model org preference is enabled before attempting the load.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org, any date | FHIR R4-aligned standard objects | HC24__ is frozen; standard objects are the supported path forward |
| Existing org with HC24__ data, building new features | Standard objects for new records; read-only access to HC24__ for historical data | Cannot write to frozen HC24__ objects; new data should go to standard layer |
| Existing org migrating to standard objects | Phased migration with Bulk API 2.0 extraction and reload | Minimizes data loss risk; allows parallel validation |
| FHIR R4 REST API integration | Standard objects with ClinicalEncounter, HealthCondition, etc. | Direct FHIR resource-to-object mapping; no custom transformation overhead |
| HL7 v2 legacy integration | Standard objects after transformation layer | Requires field-level mapping; standard objects still preferred over HC24__ |
| Experience Cloud patient portal | Standard objects + FHIR R4 for Experience Cloud permission set | HC24__ objects not accessible to community users via FHIR APIs |
| Reporting on historical clinical data only | Read from HC24__ if data pre-dates migration | Historical records may exist only in HC24__ until migration completes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org state** — Verify whether the FHIR-Aligned Clinical Data Model org preference is active. Check Setup > FHIR R4 Support Settings. If it is off, all subsequent steps require enabling it first. Also confirm whether existing HC24__ data is present that constrains the migration approach.
2. **Identify the target layer** — Using the decision table above, determine whether the integration should write to FHIR R4-aligned standard objects (default for new work) or must read historical HC24__ data. Document this decision with rationale.
3. **Map objects and fields** — Build a complete object-to-object and field-to-field mapping between the source system (FHIR R4 resource, HL7 message, or CSV) and the target Salesforce standard objects. Reference the Health Cloud Object Reference for canonical field names and data types.
4. **Configure permissions** — Assign appropriate Health Cloud permission sets to integration users and end users. If Experience Cloud is involved, assign the FHIR R4 for Experience Cloud permission set to affected profiles or users. Validate with a test login before deploying.
5. **Implement and validate** — Build the integration or data load using the standard-object schema. Use External ID fields for upsert operations to ensure idempotency. After loading, query records using SOQL to confirm field values, relationship links, and record counts match expectations.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] FHIR-Aligned Clinical Data Model org preference is enabled in Setup
- [ ] No new DML operations target HC24__ objects where a standard counterpart exists
- [ ] All standard clinical objects referenced in code or config exist in the target org's schema
- [ ] Experience Cloud users (if any) have the FHIR R4 for Experience Cloud permission set assigned
- [ ] External ID fields are used for upsert operations to support idempotent re-ingestion
- [ ] Relationship fields (e.g., ClinicalEncounterId) are populated on child clinical objects
- [ ] SOQL queries have been tested against the target org to confirm object availability

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HC24__ write freeze is silent by default** — When you attempt to insert or update an HC24__ object that has a standard-object counterpart in an org provisioned after Spring '23, you receive a DML error rather than a deprecation warning. The error message does not always name the specific freeze policy. Always check the provisioning date and the Health Cloud release notes before writing to HC24__ objects.
2. **Standard objects are absent until the org preference is toggled** — The FHIR-Aligned Clinical Data Model org preference is off by default in many orgs. ClinicalEncounter, HealthCondition, and peer objects simply do not exist in Object Manager until the preference is active. Apex code referencing these objects will fail to compile. SOQL queries will return "object not found" errors. This is frequently mistaken for a permissions issue.
3. **Experience Cloud FHIR permission is a separate gate** — Having the org preference enabled and a Health Cloud user license is not sufficient for Experience Cloud users. The "FHIR R4 for Experience Cloud" permission set is a distinct gate. Patient portal users who cannot see their own care plans or conditions despite correct Health Cloud configuration are almost always missing this permission set assignment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Object layer recommendation | Written decision (HC24__ vs FHIR R4-aligned) with rationale based on org provisioning date and use case |
| Field mapping document | Source-to-target field mapping between FHIR R4 resources or HC24__ fields and standard Salesforce clinical objects |
| Setup checklist | Step-by-step FHIR-Aligned Clinical Data Model enablement checklist for the target org |
| Permission configuration plan | List of permission sets required for integration users, internal Health Cloud users, and Experience Cloud users |
| Migration plan (if applicable) | Phased plan for extracting HC24__ data and loading into standard clinical objects |

---

## Related Skills

- admin/clinical-data-requirements — FHIR R4 object activation requirements and CodeableConcept field mapping patterns; use alongside this skill when defining clinical data requirements at the admin layer
- apex/health-cloud-apis — Apex and REST API patterns for reading and writing to standard clinical objects once the data model layer is established
- apex/fhir-integration-patterns — FHIR R4 integration patterns including CDS Hooks and SMART on FHIR; use when building server-to-server FHIR integrations on top of this data model
- data/data-migration-planning — General large-scale migration planning; reference for the HC24__-to-standard-object migration pattern
