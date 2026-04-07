# Gotchas — Care Program Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: AuthorizationFormText Locale Exact-Match Failure Is Silent

**What happens:** When the `locale` field on an `AuthorizationFormText` record does not exactly match the logged-in user's locale, the consent document silently fails to display in the enrollment UI. No error message is shown. The enrollment flow simply appears to have a blank consent step.

**When it occurs:** Any time an `AuthorizationFormText` record is created with a locale like `en` (generic English) but the enrolling user's locale is `en_US`. Also occurs when new user populations are added to the org in a different locale (e.g., `fr_FR`) without creating a corresponding locale-specific `AuthorizationFormText` record.

**How to avoid:** Always check the exact locale string used on the `AuthorizationFormText` record against the User record's locale field. They must be character-for-character identical. If multiple locales are in use, create one `AuthorizationFormText` record per locale, all linked to the same parent `AuthorizationForm`. Test consent document rendering by logging in as a user in each target locale, not as an admin.

---

## Gotcha 2: Patient Program Outcome Management Is a Separately Licensed Feature — Not Part of Base Health Cloud

**What happens:** Attempting to create, view, or update `PatientProgramOutcome` records without the separate Patient Program Outcome Management permission set returns "Insufficient Privileges" errors. Because the object exists in the schema, the error is consistently misdiagnosed as a profile permission or sharing rule issue. Admins spend hours chasing sharing and OWD settings that have no effect.

**When it occurs:** Whenever a user without the dedicated permission set accesses Patient Program Outcome data. The feature requires API v61.0 or later AND the separately licensed add-on permission set. Org edition or Health Cloud license alone is not sufficient.

**How to avoid:** Before beginning any Patient Program Outcome implementation, confirm the org has the add-on license in Setup → Company Information → Licenses and check that the "Patient Program Outcome Management" permission set exists. If the permission set does not appear, the feature is not licensed — no amount of profile editing will fix the access error.

---

## Gotcha 3: CareProgramEnrolleeProduct Requires Both Parent Records to Exist First

**What happens:** Creating a `CareProgramEnrolleeProduct` record fails with a required-field validation error if the referenced `CareProgramEnrollee` or `CareProgramProduct` record does not yet exist. Because these are lookup fields — not master-detail — the error message does not always clearly identify which parent is missing.

**When it occurs:** During bulk data loads where records are loaded in the wrong order, or in Flows/Apex that attempt to insert `CareProgramEnrolleeProduct` in the same transaction before the parent `CareProgramEnrollee` insert is committed.

**How to avoid:** Always follow the hierarchy creation order: `CareProgram` → `CareProgramProduct` → `CareProgramProvider` → `CareProgramEnrollee` → `CareProgramEnrolleeProduct`. In data loads, split into separate files per object and load in order. In Apex or Flow, insert parent records first and query back their IDs before creating child records.

---

## Gotcha 4: Inactive CareProgram Blocks All Enrollment Operations

**What happens:** If the `CareProgram` record's `Status` field is not set to `Active`, attempts to create `CareProgramEnrollee` records against it fail. The error can appear as a generic DML error or validation rule violation, not an explicit "program is inactive" message.

**When it occurs:** During initial setup when records are created in a draft/inactive state and enrollment is attempted before the program is formally activated. Also occurs when a program is deactivated or reaches its `EndDate` and legacy automation attempts to enroll additional patients.

**How to avoid:** Build automation or pre-enrollment checks that verify `CareProgram.Status = 'Active'` and that the current date falls within the program's `StartDate` and `EndDate` range before attempting to create `CareProgramEnrollee` records. Surface clear error messages to the end user rather than allowing the DML to fail silently.

---

## Gotcha 5: Care Programs and Care Plans Are Different Objects — Automation Must Not Cross Them

**What happens:** Automations, validation rules, or Apex triggers built for `CarePlan` objects do not fire on `CareProgram` objects, and vice versa. When admins confuse the two, they build automation on the wrong object and are surprised when it has no effect on the intended records.

**When it occurs:** When terminology in business requirements uses "care program" loosely to mean any patient care workflow, causing the implementing admin to use `CarePlan` (the task/goal framework) instead of `CareProgram` (the population enrollment container). Common in orgs where both features are enabled.

**How to avoid:** Establish a shared lexicon with stakeholders early. In Salesforce, a "Care Program" is population-level enrollment; a "Care Plan" is per-patient task management. Document which object each business requirement maps to before building. Always verify object API names (`CareProgram` vs `CarePlan`) before writing automation.
