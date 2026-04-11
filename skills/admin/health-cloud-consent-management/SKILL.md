---
name: health-cloud-consent-management
description: "Use this skill when configuring Health Cloud patient consent management: setting up HIPAA authorization forms, consent templates, consent tracking per patient, and withdrawal handling. NOT for marketing consent (ContactPointTypeConsent/ContactPointConsent), GDPR opt-out workflows, or Experience Cloud consent forms unrelated to clinical authorization."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I set up HIPAA authorization forms and consent tracking in Health Cloud?"
  - "Patient consent form is not displaying in Health Cloud enrollment workflow"
  - "How does AuthorizationFormConsent work and how is it different from marketing consent objects?"
  - "How to track when a patient withdraws consent for a clinical care program in Salesforce"
  - "AuthorizationFormText locale must match user locale or consent document fails to display"
tags:
  - health-cloud
  - consent-management
  - hipaa
  - authorization-form
  - phi-compliance
inputs:
  - Health Cloud org with Consent Management feature enabled
  - Patient records as Person Accounts
  - Care program enrollment workflow (CareProgramEnrollee)
  - DataUsePurpose records defining the clinical use cases for PHI
outputs:
  - Configured AuthorizationForm hierarchy (Form → Text → DataUse → Consent)
  - AuthorizationFormConsent records per patient per consent form
  - Withdrawal workflow for revoking consent without deleting records
  - Consent tracking integration with care program enrollment
dependencies:
  - admin/health-cloud-patient-setup
  - admin/care-program-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Health Cloud Consent Management

Use this skill when configuring Health Cloud patient consent management: setting up HIPAA authorization forms, creating consent templates, tracking consent status per patient, and handling withdrawal. This skill covers the clinical consent form lifecycle — template creation, enrollment-linked consent capture, and status management. It does NOT cover marketing consent objects (ContactPointTypeConsent, ContactPointConsent for GDPR/CCPA opt-out), general Experience Cloud consent flows, or consent for non-clinical purposes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Health Cloud is enabled and Consent Management is configured in Setup. Verify that the DataUsePurpose standard object is available — this is the root of the consent hierarchy.
- Identify the clinical use cases that require HIPAA consent (e.g., treatment, payment, healthcare operations, research). Each becomes a separate DataUsePurpose record.
- Confirm that every AuthorizationForm has at least one AuthorizationFormText with the `IsDefault` flag set to true. A missing default text causes the consent form to silently fail to display during enrollment.
- Distinguish clinical consent (HIPAA Privacy Rule authorization) from marketing consent (GDPR/CCPA opt-out). These use completely different object families. Do not confuse AuthorizationFormConsent with ContactPointConsent.

---

## Core Concepts

### The Five-Object Consent Hierarchy

Health Cloud patient consent uses a five-object hierarchy:

1. **DataUsePurpose** — Defines the clinical reason PHI is being used (e.g., Treatment, Payment, Research). This is the root anchor of the consent model.
2. **AuthorizationForm** — The form template that describes what the patient is consenting to. One form per consent type (e.g., "HIPAA Authorization for Treatment").
3. **AuthorizationFormText** — The actual text/content of the form in a specific language/locale. Every AuthorizationForm must have exactly one default AuthorizationFormText (`IsDefault = true`). Missing this causes the form to fail to display.
4. **AuthorizationFormDataUse** — Junction object linking AuthorizationForm to DataUsePurpose. Establishes which clinical use purpose each form covers.
5. **AuthorizationFormConsent** — The per-patient consent record. One record per patient per form with fields: `ConsentGiverId` (Individual ID), `AuthorizationFormTextId`, `ConsentCapturedSource` (how consent was obtained), `Status` (Seen, Signed, Rejected), and timestamp.

This hierarchy separates form templates (reusable) from patient consent records (one per patient per form instance).

### AuthorizationFormConsent vs. ContactPointConsent

These are architecturally distinct objects for different regulatory purposes:

- **AuthorizationFormConsent** — HIPAA clinical authorization. Tracks whether a patient has authorized specific uses of their PHI. Required before a `CareProgramEnrollee` can be marked Active in most implementations.
- **ContactPointConsent / ContactPointTypeConsent** — GDPR/CCPA marketing consent. Tracks whether an individual has opted in or out of specific communication channels (email, phone, direct mail).

Using ContactPointConsent for HIPAA clinical authorization is a compliance violation — the objects have different fields, different reporting requirements, and different legal purposes.

### Withdrawal Handling

When a patient withdraws consent, the correct action is to **update the Status field** on the existing `AuthorizationFormConsent` record to a terminal status value (e.g., Withdrawn or Revoked) — NOT to delete the record. Deleting the consent record destroys the audit trail required for HIPAA compliance. The consent history must be preserved to demonstrate that consent was previously obtained and when it was withdrawn.

---

## Common Patterns

### Consent Capture at Care Program Enrollment

**When to use:** Every time a patient is enrolled in a care program and HIPAA authorization must be obtained before accessing PHI.

**How it works:**
1. Create `DataUsePurpose` records for each clinical use category (Treatment, Payment, Healthcare Operations).
2. Create `AuthorizationForm` for each use category.
3. Create `AuthorizationFormText` with the form content, set `IsDefault = true`, and link to the AuthorizationForm. Ensure the Locale field matches the patient's expected language/locale (or the logged-in user's locale).
4. Create `AuthorizationFormDataUse` linking each form to its DataUsePurpose.
5. During enrollment Flow, create an `AuthorizationFormConsent` record for the patient with `Status = Seen`. After the patient signs, update `Status = Signed`.
6. Only mark `CareProgramEnrollee` as Active after all required `AuthorizationFormConsent` records have `Status = Signed`.

**Why not the alternative:** Skipping consent capture and marking enrollment as active immediately is a HIPAA Privacy Rule violation. The consent record creates the required audit trail.

### Withdrawal Processing

**When to use:** A patient requests revocation of HIPAA authorization.

**How it works:**
1. Locate all `AuthorizationFormConsent` records for the patient (query by `ConsentGiverId = [Individual ID]`).
2. Update `Status` on each relevant record to a terminal value (e.g., Withdrawn).
3. Record `ConsentCapturedSource = Verbal` or `Written` based on how withdrawal was communicated.
4. Optionally update related `CareProgramEnrollee` status to reflect restricted access.
5. Do NOT delete the `AuthorizationFormConsent` record. The historical consent record must be preserved.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Patient consent form not displaying at enrollment | Check AuthorizationFormText IsDefault flag and locale | Missing default text is the #1 cause of form display failure |
| Patient withdraws HIPAA authorization | Update AuthorizationFormConsent Status to Withdrawn | Never delete — HIPAA requires audit trail |
| Marketing email opt-out | Use ContactPointConsent, not AuthorizationFormConsent | Different regulatory purpose, different object |
| Multiple languages needed for consent forms | Create one AuthorizationFormText per locale, one IsDefault = true | Platform uses locale matching to select the displayed text |
| Consent needed before enrollment active | Gate CareProgramEnrollee status update on AuthorizationFormConsent.Status = Signed | Prevents PHI access before consent is captured |

---

## Recommended Workflow

1. **Inventory clinical consent requirements** — identify each type of PHI use that requires patient authorization (Treatment, Payment, Research, etc.). Each becomes a DataUsePurpose record. Confirm scope with compliance/legal team.
2. **Create the consent hierarchy** — create DataUsePurpose records, then AuthorizationForm for each form template, then AuthorizationFormText (with IsDefault = true and correct Locale), then AuthorizationFormDataUse junction records linking forms to purposes.
3. **Build enrollment-linked consent capture** — add consent form display and capture steps to the care program enrollment Flow. Create AuthorizationFormConsent records when the patient is shown the form (Status = Seen) and update to Signed after acknowledgment.
4. **Gate enrollment activation** — add a validation check in the enrollment Flow or validation rule to prevent CareProgramEnrollee from being marked Active until all required AuthorizationFormConsent records have Status = Signed.
5. **Configure withdrawal workflow** — build a Flow or quick action that updates AuthorizationFormConsent Status to Withdrawn when a patient revokes consent. Ensure the record is never deleted.
6. **Test with multiple locales** — if the org serves patients in multiple languages, test consent form display for each locale. Verify that the correct AuthorizationFormText language is displayed based on user/patient locale.

---

## Review Checklist

- [ ] DataUsePurpose records created for all clinical use categories
- [ ] Each AuthorizationForm has at least one AuthorizationFormText with IsDefault = true
- [ ] AuthorizationFormText Locale matches the expected user/patient locale
- [ ] AuthorizationFormDataUse junction records link all forms to their DataUsePurpose
- [ ] Enrollment Flow creates AuthorizationFormConsent records with correct Status
- [ ] CareProgramEnrollee activation is gated on consent Status = Signed
- [ ] Withdrawal process updates Status (does not delete the consent record)
- [ ] HIPAA consent objects tested end-to-end in sandbox before go-live

---

## Salesforce-Specific Gotchas

1. **Missing default AuthorizationFormText causes silent form display failure** — If an AuthorizationForm has no AuthorizationFormText with IsDefault = true, the consent form component returns no content at runtime. The patient sees nothing to consent to, and no error is shown. Always verify that exactly one AuthorizationFormText per form has IsDefault = true before testing.

2. **Locale mismatch prevents correct text selection** — AuthorizationFormText has a Locale field. If the patient's or logged-in user's locale does not match any AuthorizationFormText locale, the platform may fail to display the correct form text. Test consent display from user accounts with the exact locale your patient population uses.

3. **Deleting AuthorizationFormConsent destroys HIPAA audit trail** — The consent record must persist even after withdrawal. Update Status to Withdrawn; never delete. Bulk data cleanup processes must explicitly exclude AuthorizationFormConsent from deletion operations.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataUsePurpose records | Defines clinical use categories requiring patient authorization |
| AuthorizationForm hierarchy | Form templates with text, locale variants, and data use linkages |
| Enrollment Flow with consent capture | Flow that creates and updates AuthorizationFormConsent during enrollment |
| Withdrawal workflow | Quick action or Flow that updates consent status without deleting records |

---

## Related Skills

- admin/health-cloud-patient-setup — Person account and care team setup that precedes consent configuration
- admin/care-program-management — Care program enrollment workflow that consent is integrated with
- admin/consent-data-model-health — Detailed data model reference for the consent object hierarchy
