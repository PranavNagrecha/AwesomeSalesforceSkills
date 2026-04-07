# Care Program Management — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `care-program-management`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Health Cloud / Care Program feature licensed?** Yes / No / Unknown
- **Patient Program Outcome Management add-on licensed?** Yes / No / Not needed
- **Target user locale(s) for enrollment:** (e.g., `en_US`, `fr_FR`)
- **Known constraints:** (e.g., bulk enrollment via API, existing consent forms, EHR integration)
- **Failure modes to watch for:** (e.g., locale mismatch on consent, hierarchy order in bulk load)

## CareProgram Hierarchy Checklist

Work through this in order. Do not proceed to the next step until the current record is confirmed to exist and be Active.

- [ ] **CareProgram** record exists with `Status = Active` and valid `StartDate` / `EndDate`
  - CareProgram Name: _______________
  - CareProgram ID: _______________
- [ ] **CareProgramProduct** records created for all medications/services in scope
  - Product 1: _______________ (ID: _______________)
  - Product 2: _______________ (ID: _______________)
- [ ] **CareProgramProvider** records created for all delivering healthcare organizations
  - Provider 1: _______________ (Account ID: _______________)
  - Provider 2: _______________ (Account ID: _______________)

## Consent Configuration Checklist

- [ ] `AuthorizationForm` record exists
  - AuthorizationForm Name: _______________
  - AuthorizationForm ID: _______________
- [ ] `AuthorizationFormText` record(s) created — one per active user locale
  - Locale: `___________` (must match user locale exactly, e.g., `en_US` not `en`)
  - Locale: `___________`
- [ ] Consent document rendering tested by logging in as a non-admin user in each target locale

## Enrollment Checklist

- [ ] `CareProgramEnrollee` record(s) created
  - Patient (Person Account): _______________
  - Enrollee Status: Pending → Active (after consent)
- [ ] `AuthorizationFormConsent` record created and linked to each enrollee
- [ ] `CareProgramEnrollee.Status` updated to `Active` after consent confirmed
- [ ] `CareProgramEnrolleeProduct` records created (if product-level tracking required)

## Patient Program Outcome Management (if applicable)

- [ ] License confirmed in Setup → Company Information → Licenses
- [ ] "Patient Program Outcome Management" permission set exists in org
- [ ] Permission set assigned to all relevant users
- [ ] `PatientProgramOutcome` records created and linked to `CareProgramEnrollee`

## Approach

Which pattern from SKILL.md applies?

- [ ] Full Enrollment with Consent (standard UI-driven enrollment)
- [ ] Product-Level Enrollment for Outcome Tracking (requires CareProgramEnrolleeProduct)
- [ ] Bulk enrollment via API/Apex (requires hierarchy order enforcement)
- [ ] Troubleshooting existing enrollment issue (use gotchas.md)

Reason for choice: _______________

## Test Plan

- [ ] Enrolled one test patient end-to-end as a non-admin user in each target locale
- [ ] Consent document displayed correctly (not blank) during enrollment
- [ ] `CareProgramEnrollee.Status` is `Active` after consent captured
- [ ] Product-level `CareProgramEnrolleeProduct` records visible on enrollee (if applicable)
- [ ] `PatientProgramOutcome` records accessible to users with the permission set (if applicable)

## Notes

Record any deviations from the standard pattern and why:

(e.g., "Consent is being captured outside Salesforce via a third-party eConsent system; AuthorizationFormConsent records are being created via API after the fact.")
