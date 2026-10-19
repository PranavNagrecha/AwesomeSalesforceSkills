---
name: consent-data-model-health
description: "Designing, querying, or troubleshooting the Health Cloud consent data model — the five-object HIPAA authorization hierarchy (DataUsePurpose → AuthorizationForm → AuthorizationFormText → AuthorizationFormDataUse → AuthorizationFormConsent). Trigger keywords: authorization form consent, ConsentGiverId, AuthorizationFormConsent SOQL, CareProgramEnrollee consent gate, PHI consent trail, consent hierarchy setup. NOT for the Setup configuration of authorization forms, consent templates, and withdrawal handling — use admin/health-cloud-consent-management. NOT for marketing or GDPR opt-out on ContactPointTypeConsent — use security/gdpr-data-privacy."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I set up patient consent for Health Cloud before enrolling in a care program?"
  - "AuthorizationFormConsent SOQL query to verify a patient has signed a consent form before clinical record access"
  - "CareProgramEnrollee status won't move to Active — is there a consent prerequisite?"
  - "check that a patient signed the treatment authorization for the current form version"
  - "find consent records whose consent giver is a contact instead of an individual"
  - "record a patient's rejection of an authorization form without deleting the history"
tags:
  - health-cloud
  - consent
  - hipaa
  - phi
  - data-model
  - authorization
inputs:
  - "Target org with Health Cloud enabled"
  - "Patient Individual ID (not Contact ID) for ConsentGiverId population"
  - "List of data use purposes mapped to clinical workflows (e.g., treatment, research)"
  - "Intake flow or process that captures patient authorization signature"
outputs:
  - "Configured five-object consent hierarchy with at least one AuthorizationFormConsent record per enrolled patient"
  - "SOQL query pattern to verify consent status before PHI access"
  - "Checklist of sharing rule gaps that must be addressed separately"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Consent Data Model Health

This skill activates when building or auditing the authorization-form consent records a Health Cloud implementation relies on: which records make up the chain, which fields an auditor will read, how to check consent for a specific purpose before using patient data, and why the consent records and the sharing model must be designed separately.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the objects are available. The Object Reference marks DataUsePurpose, AuthorizationForm, AuthorizationFormText, AuthorizationFormDataUse, and AuthorizationFormConsent as "available if Data Protection and Privacy is enabled" (API 45.0 to 46.0 and later); Health Cloud's own objects, such as CareProgramEnrollee, come with Health Cloud.
- Decide which record represents the patient as consent giver. `ConsentGiverId` accepts Account, Contact, Individual, Lead, and User; the org's consent checks must all use the same one (this skill assumes Individual, reached through `Contact.IndividualId`).
- List the DataUsePurpose records that already exist (Treatment, Research, and so on) so the hierarchy is extended, not duplicated.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which object is the consent giver in every query and every intake path?" | `ConsentGiverId` is polymorphic; a Contact Id saves fine but won't match a check written for Individual Ids (Gotcha 2) | One documented giver type, enforced in the intake automation |
| "Which purposes does each form cover?" | AuthorizationFormDataUse links a form (not a form text) to a DataUsePurpose (Gotcha 6) | A purpose map per form, and a check that filters on the purpose |
| "How is a new legal version of the form introduced?" | Consents point at the form text they were given against; editing that text in place rewrites history (Gotcha 4) | A new AuthorizationFormText per version |
| "What counts as consent: Signed only, and how is a rejection recorded?" | `Status` is a restricted picklist with Rejected, Seen, and Signed (Gotcha 5) | A rule per form, and rejections stored as Rejected rather than deleted |
| "Must enrollment be blocked until consent exists?" | Nothing in the data model stops a CareProgramEnrollee from being activated without consent (Gotcha 3) | A before-save gate on enrollment |
| "Who should see a patient's clinical records, independent of consent?" | Consent records don't change sharing (Gotcha 1) | A separate sharing design for PHI objects |
| "What evidence will an auditor ask for?" | `ConsentCapturedDateTime`, `ConsentCapturedSource`, and `ConsentCapturedSourceType` are required fields (Gotcha 7) | Intake that fills all three, plus the form text Id |

A proper consent design adds a single giver type, purpose-specific checks, versioned form texts, and an enforced gate; "just storing a consent record" produces records no query can find and enrollments nobody can defend.

---

## Core Concepts

### The objects and the fields that matter

| Object | Purpose | Key fields |
|---|---|---|
| DataUsePurpose | Why data is used (Treatment, Research) | `Name`, `CanDataSubjectOptOut`, `LegalBasisId` |
| AuthorizationForm | A form, with effective dates | `IsSignatureRequired`, `DefaultAuthFormTextId`, `EffectiveFromDate`, `EffectiveToDate`, `RevisionNumber` |
| AuthorizationFormText | A form's text and language | `AuthorizationFormId`, `ContentDocumentId`, `DetailAuthorizationFormText`, `FullAuthorizationFormUrl`, `Locale` |
| AuthorizationFormDataUse | Links a form to a purpose | `AuthorizationFormId`, `DataUsePurposeId` |
| AuthorizationFormConsent | One person's consent to one form text | `ConsentGiverId`, `AuthorizationFormTextId`, `Status`, `ConsentCapturedDateTime`, `ConsentCapturedSource`, `ConsentCapturedSourceType`, `DocumentVersionId`, `RelatedRecordId` |

`Status` values are Rejected, Seen, and Signed (restricted picklist). `ConsentCapturedSourceType` is a restricted picklist (Email, InPerson, MailingAddress, Phone, Social, Video, Web); `ConsentCapturedSource` is free text such as an email address or URL.

### Consent records and record access are separate

AuthorizationFormConsent is a record of what a person agreed to. Each consent object has its own sharing (`...Share` objects and owner sharing rules), but no field on it changes who can see clinical records. PHI access is designed with OWDs, sharing rules, and permission sets.

### Marketing consent is a different model

ContactPointTypeConsent (consent for a contact point type, such as email or phone) and ContactPointConsent (consent to be contacted through a specific email address or phone number) record communication preferences. They are not authorization-form consents and don't satisfy a check written against AuthorizationFormConsent.

### Least-privilege access to the consent trail

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- permissionsets/Consent_Intake.permissionset-meta.xml: intake users can record consent but not edit or delete it -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Consent Intake</label>
    <objectPermissions>
        <object>AuthorizationFormConsent</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>AuthorizationFormText</object>
        <allowCreate>false</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
</PermissionSet>
```

---

## Common Patterns

### Pattern 1: Set up a form for treatment consent

1. Create (or reuse) DataUsePurpose `Treatment`.
2. Create AuthorizationForm `General Patient Consent` with `IsSignatureRequired = true` and effective dates.
3. Create AuthorizationFormText v1 (`AuthorizationFormId`, the document or text, `Locale`), and set it as the form's `DefaultAuthFormTextId`.
4. Create AuthorizationFormDataUse linking the form to `Treatment`.
5. At intake, create AuthorizationFormConsent with `ConsentGiverId` = the patient's Individual Id, `AuthorizationFormTextId` = the text shown, `Status = Signed`, and all three captured fields.

### Pattern 2: Check consent for a purpose before using data

```apex
public with sharing class ConsentCheck {
    public static Boolean hasSignedConsent(Id individualId, String purposeName) {
        Set<Id> formIds = new Set<Id>();
        for (AuthorizationFormDataUse du : [
            SELECT AuthorizationFormId FROM AuthorizationFormDataUse
            WHERE DataUsePurpose.Name = :purposeName
        ]) {
            formIds.add(du.AuthorizationFormId);
        }
        if (formIds.isEmpty()) {
            return false;
        }
        return ![
            SELECT Id FROM AuthorizationFormConsent
            WHERE ConsentGiverId = :individualId
            AND Status = 'Signed'
            AND AuthorizationFormText.AuthorizationFormId IN :formIds
            ORDER BY ConsentCapturedDateTime DESC
            LIMIT 1
        ].isEmpty();
    }
}
```

The purpose hangs off the form, so the check finds the forms for the purpose first, then a signed consent to any text of those forms.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Enrollment must wait for consent | Before-save Flow or Apex on CareProgramEnrollee using Pattern 2 | The data model doesn't enforce it |
| New legal wording | New AuthorizationFormText; update `DefaultAuthFormTextId` | Existing consents keep pointing at the text they were given against |
| Patient declines or withdraws | New AuthorizationFormConsent with `Status = Rejected` | Keeps the earlier record as history |
| Restrict PHI after withdrawal | Change sharing or permission set assignments | Consent status doesn't alter visibility |
| Communication preferences | ContactPointTypeConsent / ContactPointConsent | Separate model for contact preferences |

---

## Recommended Workflow

1. Export the hierarchy (`SELECT Id, Name FROM DataUsePurpose`, forms, texts, data uses) and record the giver-type decision and the purpose map in `templates/consent-data-model-health-template.md`.
2. Build or fix the hierarchy top-down (purpose, form, text, data use), one text per legal version.
3. Instrument intake so every consent row gets the Individual Id, the text Id, `Status`, and the three captured fields; add the enrollment gate.
4. Export consent rows with `ConsentGiver.Type` (`SELECT Id, ConsentGiverId, ConsentGiver.Type, Status, ConsentCapturedSource, ConsentCapturedSourceType, ConsentCapturedDateTime, AuthorizationFormTextId FROM AuthorizationFormConsent`) as JSON into a folder with the metadata export.
5. Run `python3 skills/data/consent-data-model-health/scripts/check_consent_data_model_health.py --manifest-dir <export folder>` and fix every ERROR; `references/consent-audit-worked-example.md` walks through one audit.
6. Review sharing for PHI objects separately and record the result.

---

## Review Checklist

- [ ] Every consent row's giver is the agreed type (Individual), checked through `ConsentGiver.Type`
- [ ] Every consent row has `AuthorizationFormTextId`, `ConsentCapturedDateTime`, `ConsentCapturedSource`, and `ConsentCapturedSourceType`
- [ ] Each form is linked to its purposes through AuthorizationFormDataUse
- [ ] New legal wording produced a new AuthorizationFormText
- [ ] Rejections are stored as `Rejected`, not as deleted rows
- [ ] CareProgramEnrollee activation is gated on a purpose-specific signed consent
- [ ] PHI sharing was reviewed independently of consent
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Consent records don't change who can see clinical records |
| 2 | `ConsentGiverId` accepts five object types |
| 3 | The enrollment gate isn't in the data model |
| 4 | Editing form text in place rewrites what patients appear to have signed |
| 5 | `Status` is a restricted picklist with three values |
| 6 | Purposes attach to the form, not the form text |
| 7 | Source and source type are different fields |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Consent hierarchy | Purposes, forms, versioned texts, and data uses, linked correctly |
| Intake changes | Automation that writes complete consent rows |
| Purpose-specific check | Apex or Flow implementing Pattern 2 |
| Enrollment gate | Before-save automation on CareProgramEnrollee |
| Audit report | Checker output and the filled template |

---

## Related Skills

- `admin/health-cloud-consent-management` — Setup configuration of consent forms and withdrawal handling
- `data/health-cloud-data-model` — the wider Health Cloud patient and care-plan model
- `security/gdpr-data-privacy` — communication consent and privacy requests on ContactPointTypeConsent
