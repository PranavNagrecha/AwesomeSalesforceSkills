# Health Cloud Consent Data Model — Work Template

Use this template when designing, implementing, or auditing the Health Cloud consent hierarchy.

## Scope

**Skill:** `consent-data-model-health`

**Request summary:** (describe what the user asked for — e.g., "Set up consent hierarchy for patient portal intake" or "Audit existing consent records for completeness")

---

## Context Gathered

Before starting, answer these questions:

- **Health Cloud provisioned?** Yes / No
- **Patient model:** Person Accounts / Standard Contacts with Individual records
- **ConsentGiverId source:** Individual ID resolved from `Contact.IndividualId` = _______________
- **Existing DataUsePurpose records:** (list names and IDs) _______________
- **Existing AuthorizationForm records:** (list names and IDs) _______________
- **Form version to use (AuthorizationFormText ID):** _______________
- **Consent capture channel (ConsentCapturedSourceType):** Email / InPerson / MailingAddress / Phone / Social / Video / Web

---

## Hierarchy Build Plan

| Object | Action | Key Field Values |
|--------|--------|-----------------|
| DataUsePurpose | Create / Use existing | Name: ___, CanDataSubjectOptOut: ___ |
| AuthorizationForm | Create / Use existing | Name: ___, IsSignatureRequired: ___ |
| AuthorizationFormText | Create new version | Name (version): ___, AuthorizationFormId: ___, Locale: ___ (then set the form's DefaultAuthFormTextId) |
| AuthorizationFormDataUse | Create once per form and purpose | Links: [AuthorizationForm ID] → [DataUsePurpose ID] |
| AuthorizationFormConsent | Create at intake | Name: ___, ConsentGiverId (Individual): ___, Status: Signed, SourceType: ___, Source: ___, DateTime: ___ |

---

## AuthorizationFormConsent Record Template

Fill in at patient intake flow completion:

```
Name:                      [required]
ConsentGiverId:            [Individual ID — NOT Contact ID]
AuthorizationFormTextId:   [ID of form version presented to patient]
Status:                    Signed            (values: Rejected | Seen | Signed)
ConsentCapturedSourceType: [Email | InPerson | MailingAddress | Phone | Social | Video | Web]
ConsentCapturedSource:     [free text, e.g. portal URL or email address]
ConsentCapturedDateTime:   [Datetime.now() at form submission]
```

---

## CareProgramEnrollee Gate Configuration

Describe the gate implementation:

- **Gate type:** Record-Triggered Flow / Apex Trigger
- **Object:** CareProgramEnrollee
- **Trigger:** Before Save, on Status change to 'Active'
- **Query:** forms for the purpose from AuthorizationFormDataUse (DataUsePurpose.Name = [___]), then AuthorizationFormConsent WHERE ConsentGiverId = [Individual ID] AND Status = 'Signed' AND AuthorizationFormText.AuthorizationFormId IN [those forms]
- **Block condition:** Zero rows returned
- **Error message:** _______________

---

## Consent Verification Query

Use this query to verify a patient's consent before clinical record access:

```soql
-- Step 1: forms that cover the purpose
SELECT AuthorizationFormId FROM AuthorizationFormDataUse WHERE DataUsePurpose.Name = '[Purpose Name]'

-- Step 2: latest signed consent to any text of those forms
SELECT Id, Status, ConsentCapturedSourceType, ConsentCapturedSource, ConsentCapturedDateTime,
       AuthorizationFormText.Name, AuthorizationFormText.AuthorizationForm.Name
FROM AuthorizationFormConsent
WHERE ConsentGiverId = '[Individual ID]'
  AND Status = 'Signed'
  AND AuthorizationFormText.AuthorizationFormId IN ('[form Id from step 1]')
ORDER BY ConsentCapturedDateTime DESC
LIMIT 1
```

Result: _______________

---

## Sharing Rule Review (Separate from Consent)

Note: AuthorizationFormConsent does NOT control record visibility. Document the sharing model separately.

| PHI Object | OWD | Sharing Rule Type | Notes |
|------------|-----|-------------------|-------|
| ClinicalNote | ___ | ___ | ___ |
| EpisodeOfCare | ___ | ___ | ___ |
| PatientEncounter | ___ | ___ | ___ |
| CareProgramEnrollee | ___ | ___ | ___ |

---

## Review Checklist

- [ ] ConsentGiverId populated with Individual ID (not Contact ID)
- [ ] Status uses only Rejected, Seen, Signed; executed authorizations are Signed
- [ ] ConsentCapturedSource and ConsentCapturedSourceType populated on all records
- [ ] ConsentCapturedDateTime populated on all records
- [ ] AuthorizationFormDataUse links each form to the correct DataUsePurpose
- [ ] CareProgramEnrollee activation gate implemented and tested
- [ ] Sharing rules reviewed and confirmed independent of consent hierarchy
- [ ] AuthorizationFormText treated as append-only — no in-place edits after go-live

---

## Notes and Deviations

Record any deviations from the standard pattern and the reason:

_______________
