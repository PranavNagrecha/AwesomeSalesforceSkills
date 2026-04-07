---
name: health-cloud-patient-setup
description: "Use this skill when configuring patient or member records in Salesforce Health Cloud — including Person Account enablement, Health Cloud patient record type creation, care team role configuration, patient card customization, and clinical data display. Trigger keywords: patient setup, Health Cloud person account, patient card component, care team roles, clinical data display. NOT for standard account setup, general CRM contact configuration, or non-Health-Cloud person account questions."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - health-cloud
  - patient
  - person-accounts
  - care-team
inputs:
  - Health Cloud org with the Health Cloud managed package installed
  - Salesforce org edition that supports Person Accounts (Enterprise or above)
  - Confirmation of whether Person Accounts have already been enabled
  - List of care team roles needed (clinical and non-clinical)
  - Fields and related objects to display on the Patient Card component
outputs:
  - Person Accounts enabled and locked-in for the org (irreversible confirmation)
  - Health Cloud patient record type created and assigned to patient profiles
  - Care team roles configured with appropriate access levels
  - Patient Card component customized with clinical and administrative fields
  - Clinical object mapping confirmed (EhrPatientMedication, PatientHealthCondition, etc.)
triggers:
  - "configure patient records in Health Cloud"
  - "set up care team member roles Health Cloud"
  - "customize patient card component clinical data"
  - "enable person accounts for Health Cloud patients"
  - "health cloud patient record type setup"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Health Cloud Patient Setup

This skill activates when a practitioner needs to configure patient or member records in Salesforce Health Cloud — covering Person Account enablement, Health Cloud-specific patient record type creation, care team role setup, and patient card customization for clinical data display. It is NOT for standard Salesforce account setup or general person account tasks outside the Health Cloud context.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Health Cloud managed package is installed (package namespace `HealthCloudGA`). Person Account enablement is a prerequisite, but it is also an org-wide, irreversible operation. Never enable in production without a full impact assessment.
- Determine whether Person Accounts are already enabled. If they are, skip that step entirely — attempting to re-enable causes no change but wastes time and can be confusing.
- Identify the record types needed: Health Cloud typically requires at minimum a "Patient" (or "Member") person account record type alongside any existing business account record types. Understand what page layouts and profiles will be affected.
- Clarify what clinical data the org consumes: FHIR/HL7 data flows through dedicated Health Cloud objects (EhrPatientMedication, PatientHealthCondition, PatientImmunization, etc.) — it does not map to standard Contact or Account fields.
- Understand whether a care team is required and what roles exist (e.g., Primary Care Physician, Care Manager, Social Worker). Care team roles are configured in Health Cloud settings, not through standard role hierarchies.

---

## Core Concepts

### Person Accounts: Org-Wide, Irreversible Prerequisite

Health Cloud patients are represented as Person Accounts — a Salesforce platform feature that merges Account and Contact into a single record for individual people. Enabling Person Accounts is a permanent, org-wide change. Once enabled, every Account record gains an `IsPersonAccount` boolean field and the object model changes globally: person account records have no associated Contact record (the Contact fields are embedded on the Account). This cannot be reversed by Salesforce Support. All integrations, reports, SOQL queries, and third-party tools that assume standard Account/Contact separation must be reviewed and updated after enablement.

Source: [Health Cloud Administration Guide — Set Up Person Accounts](https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/)

### Health Cloud Patient Record Type vs. Person Account Enablement

Enabling Person Accounts at the org level is step one. Creating a Health Cloud patient record type is a distinct, sequential step two. These are not the same action. After Person Accounts are enabled, a new record type must be created (typically named "Patient" or "Member") on the Account object. This record type is assigned a Health Cloud-specific page layout that includes clinical components such as the Patient Card, Timeline, and Social Determinants sections. Practitioners who conflate these two steps often end up with Person Accounts that lack the Health Cloud UI components.

### Clinical Data Objects vs. Standard Fields

Clinical data in Health Cloud does not live on standard Account or Contact fields. Medications, health conditions, immunizations, procedures, and care gaps are stored on dedicated Health Cloud objects:

- `EhrPatientMedication` — medication records imported from EHR systems
- `PatientHealthCondition` — diagnoses and chronic conditions
- `PatientImmunization` — immunization records
- `PatientMedicalProcedure` — procedure history
- `CareDiagnosis` — diagnosis linked to a care plan

These objects hold a lookup to the patient Account record. Data flows into them via FHIR/HL7 integrations (using Health Cloud's FHIR APIs or MuleSoft) or direct DML from custom integrations. Attempting to store clinical data in custom fields on Account or Contact creates an unsupported data model that breaks Health Cloud reporting, timeline views, and care plan components.

### Patient Card Component

The Patient Card (`healthCloudUtility:patientCard` in the Aura namespace, or the equivalent LWC) is the primary clinical summary displayed on a patient record page. It can display fields from the patient Account record itself and from any related object that has a lookup relationship to the patient Account. Customization is done through the Health Cloud app in Setup (Patient Card Configuration) — not through the standard Lightning App Builder field configuration. A common mistake is attempting to add clinical fields directly to the Lightning record page layout instead of configuring them through the Patient Card settings.

---

## Common Patterns

### Pattern 1: Full Patient Setup from Scratch

**When to use:** New Health Cloud implementation — no Person Accounts enabled, no patient record type exists.

**How it works:**
1. Submit a case to Salesforce Support (or use the Setup wizard in some editions) to enable Person Accounts. Org must have at least one Account record type already.
2. Wait for confirmation that Person Accounts are enabled. Verify by checking that the `IsPersonAccount` field exists on Account.
3. In Health Cloud Setup, navigate to Patient Setup and create the Patient record type on Account.
4. Assign the Patient record type to the appropriate profile(s) via Profile > Record Type Settings.
5. Assign the Health Cloud patient page layout to the Patient record type.
6. Enable care team functionality in Health Cloud Settings if care team management is required.
7. Configure care team roles in Health Cloud Settings > Care Team Roles.

**Why not the alternative:** Some practitioners attempt to create a custom object for patients rather than using Person Accounts. This bypasses all Health Cloud clinical components (Patient Card, Timeline, Care Plans) since they are hardwired to Person Account records.

### Pattern 2: Patient Card Customization with Clinical Data

**When to use:** Patient record type exists, but the Patient Card needs to display additional fields from clinical objects or related records.

**How it works:**
1. In Setup, navigate to Health Cloud > Patient Card Configuration.
2. Select the card section to modify (e.g., Medications, Conditions, or a custom section).
3. Add the desired fields from the target object. The object must have a lookup to the patient Account record.
4. Save and verify the configuration on a test patient record.
5. For clinical objects fed by FHIR integrations, confirm the integration is populating the source objects before expecting data on the card.

**Why not the alternative:** Editing the Lightning record page layout directly to show clinical fields works only for Account-level fields. Clinical data from related objects (EhrPatientMedication, PatientHealthCondition) requires Patient Card configuration to display in the clinician-facing summary format.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Person Accounts not enabled, starting fresh | Enable via Setup wizard/Support, then create HC patient record type | Sequential prerequisites — cannot skip or reverse |
| Person Accounts already enabled, no patient record type | Go directly to Health Cloud Setup > Patient Setup | Do not re-enable; that step is done |
| Need to display medication data on patient record | Configure Patient Card via Health Cloud Settings | Clinical objects need Patient Card config, not LP layout fields |
| Need to add a non-standard care role (e.g., Social Worker) | Add role in Health Cloud Settings > Care Team Roles | Care team roles are HC-specific, not standard Salesforce role hierarchy |
| Org has mixed B2B and patient records | Create separate record types: Business Account and Patient | Person Account coexists with business accounts via record types |
| Clinical data not showing on Patient Card | Verify source HC object has data AND Patient Card config references that object | Both the data population and the card config must be correct |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Assess prerequisites:** Confirm Health Cloud managed package is installed and check whether Person Accounts are already enabled (`IsPersonAccount` field exists on Account). Document the current state before taking any action.
2. **Enable Person Accounts (if not already enabled):** Ensure at least one Account record type exists, then enable Person Accounts via Setup. Brief all stakeholders on the irreversibility and org-wide impact on Account/Contact queries, integrations, and reports before proceeding.
3. **Create the Health Cloud patient record type:** In Health Cloud Setup, create the Patient (or Member) record type on Account. Assign the Health Cloud patient page layout. Assign the record type to appropriate profiles.
4. **Configure care team roles:** In Health Cloud Settings > Care Team Roles, add all needed roles (clinical and non-clinical). Assign default roles to the care team template if applicable.
5. **Customize the Patient Card:** Navigate to Health Cloud > Patient Card Configuration in Setup. Add fields from the patient Account and from related clinical objects. Verify that any clinical objects used (EhrPatientMedication, PatientHealthCondition, etc.) already have a lookup to the patient Account and are populated with data.
6. **Validate with a test patient record:** Create a test person account with the Patient record type. Confirm the Patient Card renders, care team roles are selectable, and clinical data displays correctly.
7. **Review access and sharing:** Confirm that the patient record type is accessible to the correct profiles, that Health Cloud permission sets are assigned (HealthCloudFoundation, HealthCloudSocialDeterminants, etc.), and that field-level security is appropriate for any sensitive clinical fields.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Person Accounts confirmed enabled (`IsPersonAccount` field visible on Account object in Object Manager)
- [ ] Patient record type created on Account object and assigned to correct profiles
- [ ] Health Cloud patient page layout assigned to Patient record type (includes Patient Card, Timeline components)
- [ ] Care team roles configured in Health Cloud Settings and reflect all required clinical and non-clinical roles
- [ ] Patient Card configuration updated to display required clinical and administrative fields
- [ ] Test patient record created and visually verified (Patient Card displays, care team is selectable)
- [ ] Health Cloud permission sets assigned to all relevant user profiles
- [ ] Integration touchpoints (FHIR, HL7, MuleSoft) verified to populate clinical HC objects, not standard fields

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Person Account Enablement Is Permanent** — Once Person Accounts are enabled, the org-wide Account/Contact model changes irreversibly. All SOQL queries, Apex triggers, reports, and third-party integrations that assume separate Account and Contact records may break. There is no undo. Always enable in a sandbox first and run a full regression before enabling in production.
2. **Enabling Person Accounts Does Not Create the Patient Record Type** — Person Account enablement (org-level feature toggle) and Health Cloud patient record type creation (Health Cloud Setup action) are separate, sequential steps. Administrators who enable Person Accounts and stop there will see no Health Cloud clinical components on patient records. The Patient record type and its page layout must be explicitly created and assigned.
3. **Clinical HC Objects, Not Standard Fields** — Medications, conditions, immunizations, and procedures live in dedicated Health Cloud objects (EhrPatientMedication, PatientHealthCondition, etc.), not in custom fields on Account or Contact. Mapping FHIR data into custom Account fields breaks Health Cloud Timeline, Patient Card, and Care Plan components.
4. **Patient Card Requires HC-Specific Configuration** — The Patient Card cannot be configured via the standard Lightning App Builder field editor. It has its own configuration UI in Setup under Health Cloud. Attempts to drag clinical fields onto the record page layout will result in them appearing outside the Patient Card, not inside it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Patient record type | Account record type named "Patient" (or "Member") with Health Cloud page layout assigned |
| Care team role configuration | List of roles defined in Health Cloud Settings, ready for care team assignment |
| Patient Card configuration | Configured sections displaying clinical and administrative fields on the patient record |
| Test patient record | Verified person account used to validate end-to-end setup before go-live |

---

## Related Skills

- `data/person-accounts` — Core person account enablement details, SOQL impacts, and data model changes that apply across all clouds using person accounts
- `admin/care-program-management` — Care plans, care programs, and care gap management built on top of the patient setup established here
- `admin/health-cloud-data-model` — Deep reference for Health Cloud-specific objects including clinical data objects referenced in this skill
