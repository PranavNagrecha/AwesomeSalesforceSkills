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
- **Consent capture channel:** Web / Email / Verbal / Paper

---

## Hierarchy Build Plan

| Object | Action | Key Field Values |
|--------|--------|-----------------|
| DataUsePurpose | Create / Use existing | Name: ___, CanDataSubjectOptOut: ___ |
| AuthorizationForm | Create / Use existing | Name: ___, IsSignatureRequired: ___ |
| AuthorizationFormText | Create new version | Name (version): ___, Language: ___ |
| AuthorizationFormDataUse | Create | Links: [AuthorizationFormText ID] → [DataUsePurpose ID] |
| AuthorizationFormConsent | Create at intake | ConsentGiverId (Individual): ___, Status: Signed, Source: ___, DateTime: ___ |

---

## AuthorizationFormConsent Record Template

Fill in at patient intake flow completion:

```
ConsentGiverId:         [Individual ID — NOT Contact ID]
AuthorizationFormTextId: [ID of form version presented to patient]
Status:                  Signed
ConsentCapturedSource:   [Web | Email | Verbal | Paper]
ConsentCapturedDateTime: [Datetime.now() at form submission]
```

---

## CareProgramEnrollee Gate Configuration

Describe the gate implementation:

- **Gate type:** Record-Triggered Flow / Apex Trigger
- **Object:** CareProgramEnrollee
- **Trigger:** Before Save, on Status change to 'Active'
- **Query:** AuthorizationFormConsent WHERE ConsentGiverId = [Individual ID] AND Status = 'Signed' AND DataUsePurpose.Name = [___]
- **Block condition:** Zero rows returned
- **Error message:** _______________

---

## Consent Verification Query

Use this query to verify a patient's consent before clinical record access:

```soql
SELECT Id, Status, ConsentCapturedSource, ConsentCapturedDateTime,
       AuthorizationFormText.Name,
       AuthorizationFormText.AuthorizationForm.Name
FROM AuthorizationFormConsent
WHERE ConsentGiverId = '[Individual ID]'
  AND Status = 'Signed'
  AND AuthorizationFormText.AuthorizationFormDataUses.DataUsePurpose.Name = '[Purpose Name]'
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
- [ ] Status = 'Signed' (exact case) for all executed authorizations
- [ ] ConsentCapturedSource populated on all records
- [ ] ConsentCapturedDateTime populated on all records
- [ ] AuthorizationFormDataUse links form version to correct DataUsePurpose
- [ ] CareProgramEnrollee activation gate implemented and tested
- [ ] Sharing rules reviewed and confirmed independent of consent hierarchy
- [ ] AuthorizationFormText treated as append-only — no in-place edits after go-live

---

## Notes and Deviations

Record any deviations from the standard pattern and the reason:

_______________
