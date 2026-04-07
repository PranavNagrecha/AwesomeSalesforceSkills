# Gotchas — Health Cloud Patient Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Person Account Enablement Is Irreversible and Org-Wide

**What happens:** Enabling Person Accounts permanently changes the Account object model for the entire org. A new `IsPersonAccount` Boolean field appears on every Account record. The platform merges Account and Contact for person-type records. All SOQL queries that join Account and Contact (e.g., `SELECT Id FROM Contact WHERE AccountId = ...`) behave differently for person accounts because the Contact record is embedded in the Account — it still exists as a Contact ID queryable via `PersonContactId`, but it cannot be updated independently. Triggers, validation rules, flows, and integrations that assume all Accounts are business accounts will fail or produce incorrect results.

**When it occurs:** Immediately and permanently after enablement. There is no grace period, no rollback, and no support path to reverse it. Even Salesforce Support cannot disable Person Accounts once enabled.

**How to avoid:** Always enable Person Accounts in a full sandbox first. Run a complete regression test of all Account and Contact automations, integrations, and reports. Confirm with all integration partners (EHR, billing, claims) that they support Person Accounts. Only promote to production after full sign-off. Document the impact in architecture decision records.

---

## Gotcha 2: Enabling Person Accounts ≠ Creating the Health Cloud Patient Record Type

**What happens:** Administrators complete Person Account enablement and assume the org is ready to create patient records with Health Cloud components. They navigate to Accounts, create a new person account, and find no Patient Card, no Timeline, and no care team features. The Health Cloud clinical components are absent because they are tied to the Health Cloud patient page layout — which is only applied after a separate "Patient" record type is created and configured in Health Cloud Setup.

**When it occurs:** Every new Health Cloud implementation where the admin treats Person Account enablement as a single monolithic step rather than two distinct steps.

**How to avoid:** Treat these as two separate, sequential configuration tasks. Step 1: enable Person Accounts at the org level. Step 2: create the Health Cloud patient record type on Account in Object Manager, assign the Health Cloud patient page layout to it, and assign the record type to appropriate profiles. Do not mark the setup complete until both steps are done and verified with a test patient record.

---

## Gotcha 3: Clinical Data Lives in Dedicated Health Cloud Objects, Not Standard Fields

**What happens:** Integration teams map FHIR medication data into custom Account or Contact fields (e.g., `Current_Medications__c`), or store diagnoses as notes, because it feels simpler than learning the Health Cloud object model. The Patient Card, Health Cloud Timeline, Care Plan features, and clinical analytics all ignore these custom fields — they only read from Health Cloud clinical objects like `EhrPatientMedication`, `PatientHealthCondition`, `PatientImmunization`, and `PatientMedicalProcedure`. The result is clinical data that is technically in Salesforce but invisible to every Health Cloud clinical UI component.

**When it occurs:** During initial EHR or FHIR integration design when the developer is unfamiliar with the Health Cloud data model and defaults to standard object customization patterns.

**How to avoid:** Map all clinical data to the correct Health Cloud objects. Use the Health Cloud FHIR APIs or direct DML to populate `EhrPatientMedication` (medications), `PatientHealthCondition` (diagnoses/conditions), `PatientImmunization` (immunizations), `PatientMedicalProcedure` (procedures). Each of these objects requires a lookup to the patient Account record (`Account` lookup field) to be surfaced by the Patient Card and Timeline.

---

## Gotcha 4: Patient Card Configuration Is Not the Lightning App Builder

**What happens:** Administrators trying to add clinical fields to the Patient Card open the Lightning App Builder for the patient record page and attempt to add fields to the record detail component or add new field sections. The fields appear on the page, but outside the Patient Card component — they show as standard record detail fields, not as part of the clinician-facing patient summary panel. The actual Patient Card configuration is a separate Health Cloud Setup screen.

**When it occurs:** When admins are familiar with standard Lightning App Builder customization and apply the same pattern to the Patient Card. The Patient Card component (`healthCloudUtility:patientCard`) is a self-contained Aura/LWC component with its own configuration API.

**How to avoid:** Go to Setup > Health Cloud > Patient Card Configuration (or the equivalent in the Health Cloud Setup app). This is the only way to add, remove, or reorder fields within the Patient Card component. Changes here propagate automatically without re-publishing the Lightning page.

---

## Gotcha 5: Care Team Roles Are Not Salesforce Role Hierarchy Entries

**What happens:** Admins look for care team roles in Setup > Roles (the standard Salesforce role hierarchy) and attempt to add "Nurse Practitioner" or "Care Manager" as hierarchy roles. These entries do not appear in care team role picklists on patient records. Health Cloud care team roles are a separate configuration concept managed through Health Cloud Settings, not through the standard role hierarchy.

**When it occurs:** When admins conflate Salesforce's role hierarchy (used for record visibility and OWD sharing) with Health Cloud's care team role framework (used for clinical team composition on a patient record).

**How to avoid:** Navigate to Setup > Health Cloud Settings > Care Team Roles to add, edit, or deactivate care team roles. The standard Salesforce role hierarchy remains completely separate and continues to govern record sharing and visibility. Care team roles govern who is listed on a patient care team and in what clinical capacity — they have no impact on record access by themselves.
