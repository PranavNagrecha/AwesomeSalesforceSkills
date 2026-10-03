---
name: health-cloud-consent-management
description: "Use this skill when configuring Health Cloud patient consent management: setting up HIPAA authorization forms, consent templates, consent tracking per patient, and withdrawal handling. NOT for querying the AuthorizationFormConsent object hierarchy or its required field values — use data/consent-data-model-health. NOT for GDPR/CCPA marketing opt-out on ContactPointTypeConsent — use security/gdpr-data-privacy."
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
  - "record a patient revoking a HIPAA authorization without deleting the consent history"
  - "capture IP address and browser details when a patient signs an authorization form"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Health Cloud Consent Management

Use this skill when configuring patient consent in Health Cloud: HIPAA authorization forms, form text per language, consent records per patient, and withdrawal. It covers the authorization form lifecycle: template creation, enrollment-linked capture, and status management. It does NOT cover marketing consent (`ContactPointTypeConsent`, `ContactPointConsent`), general Experience Cloud consent flows, or consent for non-clinical purposes.

Licence and feature gate: the authorization form objects are standard objects that are "available if Data Protection and Privacy is enabled" (Object Reference). Health Cloud adds `IndustriesSettings.enableAuthorizationCustomSharingPCU` for portal sharing of consent forms.

---

## Before Starting

- Confirm Data Protection and Privacy is enabled. Every object in the hierarchy (`DataUsePurpose`, `AuthorizationForm`, `AuthorizationFormText`, `AuthorizationFormDataUse`, `AuthorizationFormConsent`) carries the access rule "This object is available if Data Protection and Privacy is enabled." In metadata the switch is `PartyDataModelSettings.enableConsentManagement`, and "setting this field to false purges all data protection details, such as privacy preferences and stored consent forms."
- Identify each clinical purpose that needs authorization (treatment, payment, healthcare operations, research). Each becomes a `DataUsePurpose` record with a `Name` and the required `CanDataSubjectOptOut` flag, optionally linked to a `DataUseLegalBasis`.
- Plan the default form text. The default lives on the form, not the text: `AuthorizationForm.DefaultAuthFormTextId` is "the ID of the default authorization form text to use if text isn't available for a specific language". Earlier versions of this skill described an `IsDefault` field on `AuthorizationFormText`; that field does not exist in the Object Reference.
- Keep clinical authorization separate from marketing consent. `AuthorizationFormConsent` records consent to a form; `ContactPointConsent` and `ContactPointTypeConsent` record channel preferences.

---

## Questions to Ask Before Configuring

Ask these before creating a single form. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Who can turn Data Protection and Privacy off, and is that change controlled?" | Turning `enableConsentManagement` off purges stored consent forms (gotcha 1) | A named owner and a change-control rule for the setting | Consent evidence that cannot vanish through a settings deploy |
| "Which languages must each form be shown in, and which is the fallback?" | `DefaultAuthFormTextId` on the form is the fallback when no text matches (gotcha 2) | A text record per language and a chosen default | Every patient sees a form, in their language where one exists |
| "How do we record a withdrawal, and how do we prove the earlier signature?" | `Status` allows only `Rejected`, `Seen`, `Signed` (gotcha 3) | A withdrawal design that keeps the signed record and history | An audit trail that shows when consent was given and when it ended |
| "How is consent captured: in person, phone, web, email?" | `ConsentCapturedSourceType` is a restricted picklist and `ConsentCapturedSource` is a required free-text field (gotcha 4) | The source type per channel and what goes in the source text | Consent records that load and report cleanly |
| "Do we need IP, browser, email, or location evidence for e-signatures?" | `PrivacySettings` can capture these during authorization consent (gotcha 6) | The capture settings to enable | Stronger evidence without custom code |
| "Will portal users or caregivers manage consent forms?" | Custom sharing for consent forms is a separate setting (gotcha 7) | The external audience and what they may see | Portal consent without opening records too widely |

What a proper consent configuration adds over "just creating records": consent that renders in the patient's language, a withdrawal trail that survives audits, and a settings model that cannot silently erase evidence.

---

## Core Concepts

### The consent hierarchy

| Object | Role | Key fields (Object Reference) |
|---|---|---|
| `DataUsePurpose` | Why PHI is used (treatment, research) | `Name` (required), `CanDataSubjectOptOut` (required), `Description`, `LegalBasisId` |
| `AuthorizationForm` | The form and its version | `Name`, `DefaultAuthFormTextId` (required in description), `IsSignatureRequired`, `RevisionNumber`, `EffectiveFromDate`, `EffectiveToDate` |
| `AuthorizationFormText` | Form text in one language | `AuthorizationFormId` (required), `Locale` or `LocaleSelection` (same function), `SummaryAuthFormText`, `DetailAuthorizationFormText`, `FullAuthorizationFormUrl`, `ContentDocumentId` |
| `AuthorizationFormDataUse` | Links a form to a purpose | `AuthorizationFormId`, `DataUsePurposeId` (both required) |
| `AuthorizationFormConsent` | One person's consent to one form text | `AuthorizationFormTextId`, `ConsentGiverId`, `ConsentCapturedDateTime`, `ConsentCapturedSource`, `ConsentCapturedSourceType` (all required), `Status`, `RelatedRecordId`, `DocumentVersionId` |

`ConsentGiverId` is polymorphic: Account, Contact, Individual, Lead, or User. `Status` values are `Rejected`, `Seen`, and `Signed`. `ConsentCapturedSourceType` values are `Email`, `InPerson`, `MailingAddress`, `Phone`, `Social`, `Video`, and `Web`.

### Clinical authorization vs marketing consent

`AuthorizationFormConsent` records consent to a specific form text, with its capture time and source. `ContactPointConsent` and `ContactPointTypeConsent` record communication channel preferences. Using channel consent objects for HIPAA authorization records the wrong thing.

### Withdrawal

Do not delete consent records. There is no `Withdrawn` status value. Two designs keep the trail; choose one and document it:

| Design | How | Trade-off |
|---|---|---|
| New record per event | Keep the `Signed` record; insert a new `AuthorizationFormConsent` for the same giver and text with `Status = Rejected` and the withdrawal time | Full trail in data; queries must take the latest record per giver and form |
| Update with history | Change `Status` to `Rejected` and `ConsentCapturedDateTime` on the existing record, with field history tracking on `AuthorizationFormConsent` (and a Field Audit Trail policy where available) | One record per giver and form; the trail lives in history |

---

## Common Patterns

### Consent capture at care program enrollment

**When to use:** A patient enrolls in a care program and HIPAA authorization must be recorded first.

**How it works:**
1. Create a `DataUsePurpose` per clinical use (for example Treatment), with `CanDataSubjectOptOut` set deliberately.
2. Create the `AuthorizationForm`, then one `AuthorizationFormText` per language, then set the form's `DefaultAuthFormTextId` to the fallback text.
3. Create the `AuthorizationFormDataUse` linking the form to its purpose.
4. In the enrollment flow, create an `AuthorizationFormConsent` with `Status = Seen` when the form is shown, filling the required capture fields.
5. On signature, set `Status = Signed` (or insert the signed record, per the chosen design).
6. Mark the `CareProgramEnrollee` active only after every required authorization is `Signed`.

### Withdrawal processing

**When to use:** A patient revokes an authorization.

**How it works:**
1. Find the patient's consent records by `ConsentGiverId` and the form text for the purpose.
2. Record the withdrawal with `Status = Rejected`, using the chosen design (new record, or update with history).
3. Set `ConsentCapturedSourceType` to the channel used (for example `Phone`) and `ConsentCapturedSource` to the source detail (for example the staff member or address).
4. Update the related enrollment if the withdrawal restricts it.
5. Never delete consent records, and exclude them from cleanup jobs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Form shows no text for some patients | Set `AuthorizationForm.DefaultAuthFormTextId`; add text for the missing language | The default is the fallback when no language matches |
| Patient withdraws | Record `Status = Rejected`; keep the `Signed` record or its history | No `Withdrawn` value exists; deletion destroys evidence |
| Marketing email opt-out | `ContactPointTypeConsent`, not `AuthorizationFormConsent` | Different regulatory purpose and object |
| Several languages | One `AuthorizationFormText` per language, one default on the form | `Locale` and `LocaleSelection` select the text |
| E-signature evidence needed | `PrivacySettings` authorization capture fields | Captures IP, email, browser, location during consent |
| Portal users manage consent | `enableAuthorizationCustomSharingPCU` and sharing design | Custom sharing for consent forms is opt-in |

---

## Recommended Workflow

1. **Secure the feature switch.** Confirm Data Protection and Privacy is on, and put `PartyDataModelSettings.enableConsentManagement` under change control (deployable settings in `references/metadata-examples.md`).
2. **Inventory purposes and forms.** One `DataUsePurpose` per clinical use; one form per authorization; the languages each form needs.
3. **Build the hierarchy.** Form, then texts, then set `DefaultAuthFormTextId`, then `AuthorizationFormDataUse`.
4. **Build capture into enrollment.** Create consent records with all required capture fields, set `Seen` then `Signed`, and gate enrollment activation on `Signed`.
5. **Build withdrawal.** Choose the new-record or update-with-history design, record `Rejected`, and exclude consent objects from every deletion job.
6. **Test per language and per channel.** Show each form in each language, record consent through each channel, and confirm reporting finds the latest status per patient and form.

---

## Review Checklist

- [ ] Data Protection and Privacy enabled; `enableConsentManagement` under change control
- [ ] `DataUsePurpose` records created with `CanDataSubjectOptOut` set deliberately
- [ ] Every `AuthorizationForm` has `DefaultAuthFormTextId` set to a real text record
- [ ] One `AuthorizationFormText` per required language
- [ ] `AuthorizationFormDataUse` links every form to its purpose
- [ ] Enrollment flow fills every required consent field and gates activation on `Signed`
- [ ] Withdrawal design chosen and documented; no deletion of consent records
- [ ] Authorization capture settings decided

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Turning off consent management purges stored consent forms | One settings deploy can erase evidence |
| 2 | The default text is a lookup on the form, not a flag on the text | Forms render nothing for unmatched languages |
| 3 | `Status` has no `Withdrawn` value | Withdrawal flows fail or overwrite the signature |
| 4 | Capture source type is a restricted picklist; source text is required | Loads fail on "Verbal" or "Written" |
| 5 | `DataUsePurpose` has no `PurposeId` field | Scripts copied from old examples fail |
| 6 | Evidence capture is a settings decision | IP and browser are not recorded unless enabled |
| 7 | Portal sharing of consent forms is opt-in | Portal users cannot see forms they must sign |
| 8 | Consent records do not enforce access to PHI | Sharing must be designed separately |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Consent settings | `PartyDataModel` and `Privacy` settings files under change control |
| Authorization form hierarchy | Purposes, forms, language texts, default text, data-use links |
| Enrollment flow with consent capture | Required capture fields, `Seen` and `Signed`, enrollment gate |
| Withdrawal design | `Rejected` recording with preserved history, no deletion |

---

## Related Skills

- `admin/health-cloud-patient-setup`: Person Account and care team setup before consent configuration
- `admin/care-program-management`: enrollment workflow that consent gates
- `data/consent-data-model-health`: detailed data model reference for the consent objects
- `admin/hipaa-workflow-design`: audit trail and access design around consent
