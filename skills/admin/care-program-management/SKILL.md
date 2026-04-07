---
name: care-program-management
description: "Use when configuring or troubleshooting Health Cloud Care Programs — including CareProgram hierarchy setup, patient enrollment (CareProgramEnrollee), consent prerequisites, product-level enrollment (CareProgramEnrolleeProduct), and provider associations (CareProgramProvider). Trigger keywords: care program, program enrollment, enrollee, program product, CareProgramEnrollee, consent for enrollment, patient program outcome. NOT for Care Plans (per-patient task/goal framework), case management workflows, or general Health Cloud patient setup unrelated to program enrollment."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I enroll a patient into a care program in Health Cloud"
  - "consent document is not showing up for care program enrollment"
  - "how to set up CareProgram hierarchy with products and providers"
  - "CareProgramEnrollee is not being created or linked correctly"
  - "patient program outcome tracking not working in Health Cloud"
  - "Authorization Form Text not displaying during care program enrollment"
  - "how do I associate medications or services with a care program"
tags:
  - care-program-management
  - health-cloud
  - care-program
  - enrollment
  - consent
  - life-sciences
  - patient-program-outcome
inputs:
  - "Health Cloud org with Care Program feature enabled"
  - "Patient (Person Account or Contact) records to enroll"
  - "List of products or services to associate with the program"
  - "Healthcare provider organization accounts (CareProgramProvider)"
  - "Consent / Authorization Form configuration including locale"
outputs:
  - "Configured CareProgram object hierarchy ready for enrollment"
  - "CareProgramEnrollee records linking patients to programs"
  - "Consent prerequisite setup checklist"
  - "Enrollment troubleshooting guidance"
  - "Patient Program Outcome configuration steps"
dependencies:
  - admin/health-cloud-patient-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Care Program Management

This skill activates when configuring Health Cloud Care Programs, enrolling patients into programs, setting up program-level products and providers, or troubleshooting enrollment consent issues. It covers the full CareProgram object hierarchy and the hard consent prerequisite that must be satisfied before any enrollment record can be created.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Health Cloud is enabled and the Care Program feature is licensed in the org. Care Programs are not available in standard Sales or Service Cloud.
- Confirm whether the org requires Patient Program Outcome Management. This feature requires a separate licensed permission set (introduced at API v61.0+) and is NOT included in base Health Cloud.
- Identify the locale(s) of the end users who will perform enrollment. Authorization Form Text records must have their locale field set to exactly match the logged-in user's locale, or consent documents silently fail to display — enrollment is then impossible without an obvious error message.

---

## Core Concepts

### CareProgram Object Hierarchy

Care Programs follow a strict parent-child hierarchy. Every downstream record depends on the root `CareProgram` record existing first:

```
CareProgram (root — defines the program, its status, and date range)
├── CareProgramProduct (medications, services, or devices offered by the program)
├── CareProgramProvider (healthcare organizations that deliver the program)
└── CareProgramEnrollee (junction — links a patient/account to a program)
    └── CareProgramEnrolleeProduct (links an enrollee to a specific program product)
```

`CareProgram` is the population-level container. It is not per-patient. One program can have thousands of enrollees. Creating the hierarchy in the wrong order (e.g., creating a `CareProgramEnrollee` before the `CareProgram` is active) causes lookup-validation failures that surface as generic DML errors.

### Consent as a Hard Enrollment Prerequisite

Salesforce enforces consent before a `CareProgramEnrollee` record can be marked active. The consent mechanism uses the `AuthorizationForm`, `AuthorizationFormText`, and `AuthorizationFormConsent` objects. The `AuthorizationFormText` record contains the locale-specific display text for the consent document.

Critical constraint: the `locale` field on `AuthorizationFormText` must exactly match the locale string of the logged-in user (e.g., `en_US`, not `en`). If there is a mismatch — even a subtle one like `en` vs `en_US` — the consent document will not render in the UI, and the enrollment flow will appear broken with no informative error message. This is a silent failure.

### CareProgramEnrollee and CareProgramEnrolleeProduct

`CareProgramEnrollee` is the junction object between a `CareProgram` and a patient (typically a Person Account). It holds enrollment status, effective dates, and consent status. `CareProgramEnrolleeProduct` links an individual enrollee to a specific `CareProgramProduct`, enabling product-level tracking (e.g., which medication a specific patient is receiving under the program).

These two objects are separate. Creating only `CareProgramEnrollee` without the corresponding `CareProgramEnrolleeProduct` records is correct when product-level enrollment is not needed, but omitting `CareProgramEnrolleeProduct` when outcome tracking is required will cause downstream gaps in Patient Program Outcome data.

### Patient Program Outcome Management

Patient Program Outcome Management tracks clinical or behavioral outcomes for a patient within a program. This is a separately licensed capability (API v61.0+). It is NOT part of base Health Cloud. Attempting to use Patient Program Outcome objects without the correct permission set results in "insufficient privileges" errors that are often misdiagnosed as sharing or profile issues.

---

## Common Patterns

### Pattern: Full Enrollment with Consent

**When to use:** Setting up a new patient enrollment end-to-end, including consent capture via the UI.

**How it works:**

1. Create or verify the `CareProgram` record is Active.
2. Create `CareProgramProduct` records for any medications/services under the program.
3. Create `CareProgramProvider` records linking healthcare organization accounts to the program.
4. Create or verify the `AuthorizationForm` and `AuthorizationFormText` records. Set the `locale` field on `AuthorizationFormText` to exactly match the target user locale (e.g., `en_US`).
5. Navigate to the patient's record and launch the enrollment flow or create `CareProgramEnrollee` directly, linking to the active `CareProgram`.
6. Capture consent via `AuthorizationFormConsent` linked to the enrollee.
7. Set `CareProgramEnrollee.Status` to `Active`.
8. Optionally create `CareProgramEnrolleeProduct` records for each product the patient is enrolled in.

**Why not the alternative:** Skipping consent setup and manually setting enrollee status to Active bypasses the consent model and creates compliance risk. Health Cloud consent enforcement is not merely UI-level in all configurations — consent status is a data field that downstream processes and integrations may check.

### Pattern: Product-Level Enrollment for Outcome Tracking

**When to use:** The program has multiple medications or services and clinical outcomes need to be tracked at the product level per patient.

**How it works:**

1. Ensure `CareProgramProduct` records exist for each medication/service under the `CareProgram`.
2. After creating `CareProgramEnrollee`, create one `CareProgramEnrolleeProduct` record per product the patient is receiving. Set `CareProgramEnrolleeProduct.CareProgramProductId` and `CareProgramEnrolleeProduct.CareProgramEnrolleeId`.
3. If Patient Program Outcome Management is licensed, assign the permission set to the relevant users and create `PatientProgramOutcome` records linked to the enrollee.

**Why not the alternative:** Tracking product-level outcomes at the `CareProgramEnrollee` level using custom fields is not scalable and breaks the standard data model, preventing use of Health Cloud reporting and the Patient Program Outcome API.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Consent document not showing during enrollment | Check `AuthorizationFormText.locale` exactly matches user locale string | Silent failure — no error is thrown when locale mismatches |
| Outcome tracking needed per medication | Use `CareProgramEnrolleeProduct` + Patient Program Outcome Management | Base Health Cloud does not include outcome tracking; separate license required |
| Multiple providers delivering same program | Create one `CareProgramProvider` per provider org, all linked to same `CareProgram` | `CareProgramProvider` is the correct junction; do not use custom relationships |
| Patient needs enrollment in multiple programs | Create one `CareProgramEnrollee` record per program | Enrollee records are per-program, not reusable across programs |
| Enrollment failing with DML error on `CareProgramEnrollee` | Verify `CareProgram` status is Active and consent form is configured | Inactive program or missing consent setup are the two most common root causes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify org prerequisites — confirm Health Cloud is enabled, the Care Program feature is licensed, and (if outcome tracking is needed) the Patient Program Outcome Management permission set is available.
2. Build the CareProgram root record — set Status to Active and populate the program start/end dates. All downstream records require an active root.
3. Create CareProgramProduct and CareProgramProvider records — link all relevant medications, services, and provider organizations to the program before enrollment begins.
4. Configure consent prerequisites — create `AuthorizationForm` and `AuthorizationFormText` records. Verify the `locale` field on each `AuthorizationFormText` exactly matches the locale of each user group that will perform enrollment.
5. Enroll patients — create `CareProgramEnrollee` records linking patient Person Accounts to the program. Capture `AuthorizationFormConsent` and set enrollee Status to Active.
6. Create CareProgramEnrolleeProduct records — if product-level tracking is required, link each active enrollee to the relevant program products.
7. Validate and test — run the enrollment flow as a non-admin user to confirm consent documents render correctly, enrollee records are created, and outcome objects (if licensed) are accessible.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `CareProgram` record exists with Status = Active and valid date range
- [ ] `AuthorizationFormText.locale` exactly matches the locale of the target user (not just similar — exact string match)
- [ ] `CareProgramEnrollee` records have consent captured via `AuthorizationFormConsent`
- [ ] If outcome tracking is in scope: Patient Program Outcome Management permission set is assigned and `CareProgramEnrolleeProduct` records exist
- [ ] End-to-end enrollment tested as a non-admin user in the target locale
- [ ] `CareProgramProvider` records exist for all delivering healthcare organizations

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Authorization Form Text locale silent failure** — If the `locale` field on `AuthorizationFormText` does not exactly match the logged-in user's locale (e.g., `en` vs `en_US`), the consent document silently fails to display. No error is thrown. The enrollment UI simply appears broken. Always verify the exact locale string.
2. **Patient Program Outcome Management is a separate licensed feature** — Attempting to create `PatientProgramOutcome` records without the separate permission set (required at API v61.0+) results in "insufficient privileges" errors. This is frequently misdiagnosed as a profile or sharing issue. Check license and permission set first.
3. **Care Program vs Care Plan conflation** — Care Programs are population-level enrollment containers. Care Plans are per-patient task/goal/problem frameworks. They share the word "care" but use entirely different objects. Applying Care Plan logic (CarePlan, CarePlanTemplate, Goal, Problem) to a Care Program setup, or vice versa, produces schema errors and incorrect data models.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CareProgram hierarchy setup checklist | Ordered list of records to create and field values to set |
| Consent configuration verification steps | Steps to confirm AuthorizationFormText locale is correctly set |
| Enrollment validation test script | Manual test steps to verify end-to-end enrollment as a non-admin user |
| Patient Program Outcome configuration guide | Steps to assign the licensed permission set and create outcome records |

---

## Related Skills

- `admin/health-cloud-patient-setup` — Core Health Cloud patient record configuration (Person Accounts, care teams) that must be complete before care program enrollment is possible
- `data/person-accounts` — Person Account data model details; Care Program enrollees are typically Person Accounts
