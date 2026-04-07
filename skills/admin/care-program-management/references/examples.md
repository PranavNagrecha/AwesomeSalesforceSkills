# Examples — Care Program Management

## Example 1: Consent Document Not Displaying During Enrollment

**Context:** A Health Cloud org has Care Programs configured. The enrollment UI has been deployed and tested by an admin. When a call center agent (logged in with `en_US` locale) tries to enroll a patient, the consent step is blank — no document appears and the flow cannot proceed.

**Problem:** The `AuthorizationFormText` record was created with `locale` set to `en` (generic English). The agent's user locale is `en_US`. Salesforce performs an exact string match on this field, not a fuzzy or fallback match. The consent document silently fails to render.

**Solution:**

```
AuthorizationFormText record:
  AuthorizationFormId: [ID of the parent AuthorizationForm]
  locale: en_US          ← must match exactly, not just "en"
  ContentDocument: [consent document content]
  Name: "Patient Consent — US English"
```

Correction steps:
1. Navigate to the `AuthorizationFormText` record.
2. Edit the `locale` field from `en` to `en_US`.
3. Save and re-test enrollment as the affected user role.
4. If multiple user locales exist in the org (e.g., `fr_FR`, `de_DE`), create a separate `AuthorizationFormText` record for each locale linked to the same parent `AuthorizationForm`.

**Why it works:** Salesforce looks up the consent document by finding an `AuthorizationFormText` record whose `locale` exactly matches the running user's locale. There is no fallback to a parent locale. Creating locale-specific records for each user population ensures every user sees the correct consent document.

---

## Example 2: Enrollee Created but Outcome Tracking Throws Insufficient Privileges

**Context:** A Life Sciences org has Care Programs with active `CareProgramEnrollee` records. The team attempts to use Patient Program Outcome Management to track clinical metrics. Users with a custom profile receive "Insufficient Privileges" when trying to create or view `PatientProgramOutcome` records.

**Problem:** Patient Program Outcome Management requires a separate licensed permission set that must be assigned in addition to the base Health Cloud permission sets. It is not included in any standard Health Cloud profile or permission set. The feature requires API v61.0 or later.

**Solution:**

```
1. Confirm the org has the Patient Program Outcome Management add-on license.
2. In Setup → Permission Sets, locate the "Patient Program Outcome Management" permission set.
3. Assign the permission set to all users who need to create or view PatientProgramOutcome records.
4. Verify the org API version is v61.0 or later (Setup → API → confirm Salesforce version).
5. Test creating a PatientProgramOutcome record linked to a CareProgramEnrollee.
```

**Why it works:** Salesforce gates this feature behind a separate licensed permission set to support independent add-on billing. Without the permission set, the `PatientProgramOutcome` object exists in the schema but all DML operations are blocked. The error message ("Insufficient Privileges") points toward profile/sharing, but the actual fix is license and permission set assignment.

---

## Example 3: Full CareProgram Hierarchy Setup for a Medication Support Program

**Context:** A pharmaceutical company is launching a patient support program for a new medication. They need to enroll patients, track which specific drug formulation each patient receives, and associate two healthcare provider organizations as program sponsors.

**Problem:** Without following the correct hierarchy creation order, foreign key lookups fail and DML errors cascade. Teams often try to create `CareProgramEnrollee` records before the `CareProgram` is Active, or create `CareProgramEnrolleeProduct` records before `CareProgramProduct` records exist.

**Solution:**

```
Step 1 — Create CareProgram:
  Name: "MedX Patient Support Program"
  Status: Active
  StartDate: 2026-01-01
  EndDate: 2027-12-31

Step 2 — Create CareProgramProduct records (one per formulation):
  CareProgramId: [ID from Step 1]
  ProductId: [Salesforce Product2 ID for 10mg tablet]
  Name: "MedX 10mg Tablet"

  CareProgramId: [ID from Step 1]
  ProductId: [Salesforce Product2 ID for 20mg tablet]
  Name: "MedX 20mg Tablet"

Step 3 — Create CareProgramProvider records:
  CareProgramId: [ID from Step 1]
  AccountId: [Healthcare Org Account ID — Provider 1]
  Role: Sponsor

  CareProgramId: [ID from Step 1]
  AccountId: [Healthcare Org Account ID — Provider 2]
  Role: Sponsor

Step 4 — Configure consent (AuthorizationForm + AuthorizationFormText, locale = en_US)

Step 5 — Enroll patient:
  CareProgram: [ID from Step 1]
  AccountId: [Patient Person Account ID]
  Status: Active
  (after capturing AuthorizationFormConsent)

Step 6 — Create CareProgramEnrolleeProduct:
  CareProgramEnrolleeId: [ID from Step 5]
  CareProgramProductId: [ID of the 10mg product from Step 2]
  Status: Active
```

**Why it works:** Following the hierarchy creation order ensures all lookup fields resolve correctly. `CareProgramEnrolleeProduct` cannot be created until both the `CareProgramEnrollee` and the `CareProgramProduct` it references exist. Attempting to create records out of order results in required field validation errors on the foreign key fields.

---

## Anti-Pattern: Using Care Plans Instead of Care Programs for Population-Level Enrollment

**What practitioners do:** Administrators asked to "set up a care program for diabetes patients" create `CarePlan` records and `CarePlanTemplate` objects, associating them with a population of patients.

**What goes wrong:** `CarePlan` is a per-patient task/goal/problem management framework — it is not a population-level container. There is no concept of "enrolling" a patient into a Care Plan. Reporting across patients enrolled in a program, consent management, and product-level outcome tracking are all unavailable through the Care Plan data model.

**Correct approach:** Use `CareProgram` and `CareProgramEnrollee` for population-level program enrollment. Use `CarePlan` (linked via the enrollee's patient record) only when per-patient care delivery tasks, goals, and problems need to be tracked after enrollment. These two frameworks are complementary, not interchangeable.
