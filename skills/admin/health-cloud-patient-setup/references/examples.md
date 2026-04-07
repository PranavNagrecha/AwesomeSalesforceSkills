# Examples — Health Cloud Patient Setup

## Example 1: Enabling Person Accounts and Creating the Health Cloud Patient Record Type

**Context:** A new Health Cloud implementation. The org has Enterprise Edition with Health Cloud installed but no Person Accounts enabled. The implementation team needs to create patient records that display clinical components (Patient Card, Timeline, Care Plans).

**Problem:** Without Person Accounts enabled, Health Cloud cannot represent individual patients — the platform requires Person Accounts to merge Account and Contact into a single person record. Beyond that, simply enabling Person Accounts is not enough; the Health Cloud patient record type must be separately created and assigned.

**Solution — Step 1: Enable Person Accounts**

Before enabling, verify at least one Account record type exists (required by Salesforce). Then go to Setup > Account Settings and enable Person Accounts. In some orgs this requires a support ticket if the self-serve toggle is not available.

After enablement, verify in the Developer Console:

```soql
-- Verify Person Accounts enabled: IsPersonAccount field should exist on Account
SELECT Id, IsPersonAccount, FirstName, LastName
FROM Account
WHERE IsPersonAccount = true
LIMIT 1
```

If this query runs without error (even returning zero rows), Person Accounts are enabled.

**Solution — Step 2: Create the Patient Record Type**

In Setup, navigate to Object Manager > Account > Record Types. Create a new record type with the following settings:

```
Record Type Label:  Patient
Record Type Name:   Patient
Description:        Health Cloud patient record type for individual patients/members
Active:             true
Make Available:     [assign to appropriate profiles]
```

Assign the Health Cloud-provided "Patient" page layout (installed with the Health Cloud package, e.g., `HealthCloudGA__Patient`) to this record type for all relevant profiles.

**Solution — Step 3: Assign the Record Type in Health Cloud Settings**

Navigate to Health Cloud Setup (App Launcher > Health Cloud Setup) and confirm the Patient record type is recognized. Health Cloud Setup surfaces configuration errors if the record type is missing or misconfigured.

**Why it works:** Person Account enablement unlocks the `IsPersonAccount` field and the merged Account/Contact model. The separate Health Cloud patient record type then associates the correct page layout — which includes Health Cloud Lightning components like the Patient Card and Timeline — with patient records. These are sequential, not interchangeable steps.

---

## Example 2: Configuring Care Team Roles and Patient Card Layout

**Context:** Patient record type is set up. Clinicians report that they cannot assign a "Social Worker" role when adding members to a care team, and the patient card does not show the patient's active medications.

**Problem 1 — Missing Care Team Role:** Care team roles in Health Cloud are not drawn from the standard Salesforce Role Hierarchy. They are managed separately in Health Cloud Settings. The "Social Worker" role must be explicitly created there.

**Solution — Configure Care Team Roles:**

Navigate to Setup > Health Cloud Settings > Care Team Roles. Add a new role:

```
Role Name:        Social Worker
Role Type:        Non-Clinical
Default Role:     false
Active:           true
```

Add additional clinical roles as needed (Primary Care Physician, Care Manager, Nurse Practitioner, Behavioral Health Specialist). After saving, navigate to a patient record and attempt to add a care team member — the new role should appear in the role picklist.

**Problem 2 — Medications Not Showing on Patient Card:** The EHR integration is populating `EhrPatientMedication` records correctly, but medications do not display on the Patient Card.

**Solution — Configure Patient Card for Medications:**

Navigate to Setup > Health Cloud > Patient Card Configuration. Locate the Medications section (or create a custom section). Add the following fields from the `EhrPatientMedication` object:

```
Object:           EhrPatientMedication (lookup: Account)
Fields to display:
  - Medication Name (MedicationName__c or Name)
  - Status (Status__c)
  - Start Date (StartDate__c)
  - Prescribing Physician (PrescribingPhysician__c)
```

Verify that `EhrPatientMedication` records have the patient Account ID populated in the Account lookup field — the Patient Card only surfaces records with a matching patient Account lookup.

**Why it works:** Care team role management is a Health Cloud–specific configuration layer separate from the standard org-wide role hierarchy. Patient Card configuration drives what is displayed in the clinical summary panel; it is independent of the Lightning record page layout and must be configured through the dedicated Health Cloud Setup UI.

---

## Anti-Pattern: Storing Clinical Data in Custom Account Fields

**What practitioners do:** Add custom fields to the Account object (e.g., `Current_Medications__c`, `Active_Diagnoses__c`) and populate them from FHIR integrations rather than using Health Cloud clinical objects.

**What goes wrong:** The Patient Card, Health Cloud Timeline, Care Plans, and clinical reporting all depend on Health Cloud's data model (EhrPatientMedication, PatientHealthCondition, etc.). Custom Account fields do not appear in these components. Timeline entries for medications require `EhrPatientMedication` records, not Account fields. Care gap detection algorithms operate on structured clinical objects. The workaround of displaying Account fields on the page layout creates a shadow data model that duplicates data and diverges from the official Health Cloud integration pattern — causing maintenance issues as the Health Cloud package is updated.

**Correct approach:** Populate `EhrPatientMedication` for medications, `PatientHealthCondition` for diagnoses, `PatientImmunization` for immunizations, etc. Configure the Patient Card to display fields from these objects. The objects hold a lookup to the patient Account, which is how the Patient Card joins them to the patient record.
