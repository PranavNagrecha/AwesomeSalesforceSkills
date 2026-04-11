# Gotchas — Consent Data Model Health

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: AuthorizationFormConsent Does Not Grant or Restrict PHI Access

**What happens:** Creating an `AuthorizationFormConsent` record with `Status = Signed` has no effect on the Salesforce sharing model. A patient's clinical records remain exactly as accessible — or inaccessible — as they were before the consent record was created. There is no platform mechanism that automatically tightens or relaxes record visibility based on consent status.

**When it occurs:** Any time a team assumes that the consent data model enforces data access. This is especially common when a team migrates from a non-Salesforce system where consent and access control were coupled in the same table.

**How to avoid:** Treat the consent hierarchy and the sharing model as two entirely separate subsystems. After implementing the consent hierarchy, explicitly audit OWD settings, criteria-based sharing rules, and permission set assignments for all PHI objects (ClinicalNote, EpisodeOfCare, PatientEncounter, etc.). Document the access control design in a separate architecture decision record. Never test PHI access by checking consent status — test it by running the sharing calculator on the specific records.

---

## Gotcha 2: ConsentGiverId Silently Accepts Contact IDs But Breaks Downstream Consent Gates

**What happens:** The `ConsentGiverId` field on `AuthorizationFormConsent` is a polymorphic lookup that accepts Contact, Individual, and Account record IDs. Salesforce does not raise a validation error if a Contact ID is inserted. The record saves successfully. However, the CareProgramEnrollee consent gate query filters against the Individual ID of the enrollee — not the Contact ID. The mismatch means the gate query returns zero results even though a consent record exists, and enrollment is blocked indefinitely.

**When it occurs:** When developers or data loaders map `ConsentGiverId` from a Contact ID field (common in implementations that started without Person Accounts). Also occurs when a Flow retrieves the Contact ID from the trigger context and passes it to the consent record create action without first querying for the associated Individual.

**How to avoid:** Always resolve the Individual ID before creating AuthorizationFormConsent. The Individual is accessible via `Contact.IndividualId` (for standard Contact records) or `PersonContact.IndividualId` (for Person Accounts). Validate with a SOQL check: `SELECT IndividualId FROM Contact WHERE Id = :contactId`. Add a validation rule on `AuthorizationFormConsent` that uses `GETRECORDIDS(ConsentGiver)` to assert the record type is `Individual` if your org requires it.

---

## Gotcha 3: CareProgramEnrollee Activation Gate Is Not Native — It Must Be Built

**What happens:** Salesforce Health Cloud does not ship with a built-in validation rule or workflow that prevents a `CareProgramEnrollee` record from moving to `Active` status without a signed consent record. The status field can be manually set to `Active` via UI or API with no consent records present, creating an enrollment record that violates HIPAA authorization requirements.

**When it occurs:** In any Health Cloud implementation that has not explicitly built this gate. It also re-emerges after org refreshes if the gate Flow or Apex is not included in the deployment package.

**How to avoid:** Implement the gate as a before-save Record-Triggered Flow (or Apex before-insert/before-update trigger) on the `CareProgramEnrollee` object. The Flow should:
1. Get the related Individual ID from the CareProgramEnrollee record.
2. Query `AuthorizationFormConsent` filtered by `ConsentGiverId = [individualId]`, `Status = 'Signed'`, and the DataUsePurpose linked to the care program.
3. If the query returns zero rows, use the Add Error action to block the DML with a descriptive message.
Include this component in all deployment packages and in your Health Cloud implementation checklist.

---

## Gotcha 4: Updating AuthorizationFormText In Place Corrupts Historical Consent Records

**What happens:** If a legal team updates the consent form language and a developer edits the `ContentDocument` field on an existing `AuthorizationFormText` record in place, all historical `AuthorizationFormConsent` records linked to that text ID now appear to reference the new version. An auditor querying what a patient consented to will see the updated language, not the language that was actually presented at the time of signing.

**When it occurs:** Form revision cycles, especially when the implementation team treats `AuthorizationFormText` as a configuration record rather than an immutable consent artifact.

**How to avoid:** Treat every `AuthorizationFormText` record as append-only. On form revision, create a new `AuthorizationFormText` record (e.g., `HIPAA Authorization v2.0`) linked to the same `AuthorizationForm`. Create new `AuthorizationFormDataUse` junction records for the new text version. Update the intake flow to present the new version. Existing consent records continue to reference the old text version ID, preserving the exact language the patient signed. Optionally, archive the old text record by adding a suffix to the name.

---

## Gotcha 5: Status Value Casing Is Exact — Typos Pass Validation

**What happens:** The `Status` picklist on `AuthorizationFormConsent` accepts exactly `Seen` and `Signed`. Both are sentence-case. If a data loader, integration, or Apex script inserts a value like `signed`, `SIGNED`, or `Approved`, Salesforce will accept the insert (picklist fields in the API do not always enforce case sensitivity at the record layer) but the value will not match the expected picklist value. Downstream Flow checks using `{!record.Status} = 'Signed'` will evaluate to false, silently blocking enrollment and PHI access.

**When it occurs:** Data migrations from legacy systems with different status vocabularies, or integrations that normalize status strings to lowercase or uppercase before sending to Salesforce.

**How to avoid:** Enforce exact casing in all data load scripts and integration mappings. In Apex, use constants or an enum pattern: `private static final String STATUS_SIGNED = 'Signed';`. In Flows, use the picklist value resource rather than a hardcoded text string. Run a post-load SOQL audit: `SELECT Status, COUNT(Id) FROM AuthorizationFormConsent GROUP BY Status` and investigate any values outside `Seen` and `Signed`.
