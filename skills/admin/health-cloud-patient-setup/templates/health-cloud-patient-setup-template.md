# Health Cloud Patient Setup — Work Template

Use this template when configuring patient or member records in Salesforce Health Cloud. Fill in each section as you work through the setup.

## Scope

**Skill:** `health-cloud-patient-setup`

**Request summary:** (describe what the user or project needs — e.g., "configure patient records for Epic EHR integration in new Health Cloud org")

**In scope:**
- [ ] Person Account enablement
- [ ] Health Cloud patient record type creation
- [ ] Care team role configuration
- [ ] Patient Card customization
- [ ] Clinical object mapping verification

**Out of scope for this skill:** Standard CRM account setup, general person account design without Health Cloud, non-patient member configuration outside Health Cloud.

---

## Pre-Flight Context

Answer these before taking any action:

| Question | Answer |
|---|---|
| Is Health Cloud managed package installed? | |
| Are Person Accounts already enabled? (`IsPersonAccount` field on Account?) | |
| Does a Patient (or Member) record type already exist on Account? | |
| What clinical data needs to display on the Patient Card? (medications, conditions, immunizations, etc.) | |
| What care team roles are needed? | |
| Are there existing FHIR/HL7 integrations populating clinical HC objects? | |
| What profiles need access to patient records? | |
| What Health Cloud permission sets are currently assigned? | |

---

## Person Account Enablement

**Status:** [ ] Not started  [ ] Already enabled (skip this section)  [ ] Completed this session

**Pre-enablement checklist:**
- [ ] At least one Account record type already exists in the org
- [ ] All integration partners notified of org-wide Account/Contact model change
- [ ] Full sandbox regression test completed and signed off
- [ ] Existing Account/Contact automation (triggers, flows, validation rules) reviewed for person account impact
- [ ] All SOQL queries joining Account + Contact reviewed

**Enablement path:** Setup > Account Settings > Enable Person Accounts

**Verification:**
```soql
SELECT Id, IsPersonAccount, FirstName, LastName
FROM Account
WHERE IsPersonAccount = true
LIMIT 1
```
If query runs without field error, Person Accounts are enabled (zero rows is OK).

**Post-enablement notes:** (record any unexpected behaviors observed)

---

## Health Cloud Patient Record Type

**Status:** [ ] Not started  [ ] Already exists (skip this section)  [ ] Completed this session

**Record type details:**

| Field | Value |
|---|---|
| Record Type Label | Patient (or Member) |
| Record Type Name | Patient |
| Description | Health Cloud patient record type for individual patients/members |
| Active | true |
| Page Layout | (name of Health Cloud patient page layout from managed package) |

**Profile assignments:**

| Profile | Assigned? |
|---|---|
| (Clinical User profile name) | [ ] |
| (Care Manager profile name) | [ ] |
| (Admin profile name) | [ ] |

**Verification:** Create a test person account with the Patient record type. Confirm Patient Card and Timeline components are visible on the record page.

---

## Care Team Roles

**Status:** [ ] Not started  [ ] Not required  [ ] Completed this session

**Navigation:** Setup > Health Cloud Settings > Care Team Roles

**Roles to configure:**

| Role Name | Role Type | Default Role | Notes |
|---|---|---|---|
| Primary Care Physician | Clinical | false | |
| Care Manager | Clinical | false | |
| Nurse Practitioner | Clinical | false | |
| Social Worker | Non-Clinical | false | |
| (add rows as needed) | | | |

**Verification:** Open a test patient record > Care Team tab > Add Care Team Member. Confirm all configured roles appear in the role picklist.

**Important:** Care team roles are NOT the same as the Salesforce Role Hierarchy (Setup > Roles). They are Health Cloud-specific and have no impact on record sharing or OWD.

---

## Patient Card Configuration

**Status:** [ ] Not started  [ ] Not required  [ ] Completed this session

**Navigation:** Setup > Health Cloud > Patient Card Configuration

**Fields to add per section:**

### Medications Section
Source object: `EhrPatientMedication` (requires lookup to patient Account)

| Field API Name | Display Label | Notes |
|---|---|---|
| (field name) | (label) | |

### Conditions / Diagnoses Section
Source object: `PatientHealthCondition` (requires lookup to patient Account)

| Field API Name | Display Label | Notes |
|---|---|---|
| (field name) | (label) | |

### Additional Sections
(add rows for Immunizations, Procedures, Allergies, etc. as needed)

**Verification:** On a test patient record with clinical data populated in source objects, confirm all configured fields display correctly in the Patient Card.

**Note:** Clinical data must exist in the source HC object AND the source object must have the patient Account ID in its Account lookup field. If either is missing, the Patient Card will show no data.

---

## Health Cloud Permission Set Assignment

**Status:** [ ] Not started  [ ] Already assigned  [ ] Completed this session

**Required permission sets (from Health Cloud managed package):**

| Permission Set | Assigned To |
|---|---|
| HealthCloudFoundation | (all clinical users) |
| HealthCloudSocialDeterminants | (social work users if applicable) |
| (additional HC permission sets per feature) | |

---

## Clinical Object Integration Verification

Confirm that FHIR/HL7 or direct integrations populate the correct Health Cloud objects, not custom Account/Contact fields:

| Clinical Data Type | Correct HC Object | Integration Verified? |
|---|---|---|
| Medications | EhrPatientMedication | [ ] |
| Diagnoses / Conditions | PatientHealthCondition | [ ] |
| Immunizations | PatientImmunization | [ ] |
| Procedures | PatientMedicalProcedure | [ ] |
| Care Diagnoses | CareDiagnosis | [ ] |

---

## Final Review Checklist

- [ ] Person Accounts confirmed enabled (`IsPersonAccount` field visible on Account in Object Manager)
- [ ] Patient record type created and active on Account
- [ ] Health Cloud patient page layout assigned to Patient record type for all relevant profiles
- [ ] Care team roles configured and verified via patient record care team picklist
- [ ] Patient Card sections configured with fields from correct HC clinical objects
- [ ] Health Cloud permission sets assigned to all clinical user profiles
- [ ] Test patient record created and all components verified visually
- [ ] Integration touchpoints confirmed to populate HC clinical objects (not custom Account fields)
- [ ] Field-level security reviewed for sensitive clinical fields (PHI)
- [ ] Sharing settings reviewed — patient Account OWD should not be Public Read/Write

---

## Notes and Deviations

(Record any deviations from standard patterns, org-specific constraints, or decisions made during setup)
