# Health Cloud Consent Management — Work Template

Use this template when configuring or troubleshooting Health Cloud patient consent management.

## Scope

**Skill:** `health-cloud-consent-management`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Health Cloud version installed:
- Is consent needed for clinical HIPAA authorization or marketing communications?
- How many consent form types are needed (one per clinical use category)?
- Is multi-language support required? Which locales?
- Is consent gating CareProgramEnrollee activation?

## Consent Hierarchy Configuration

| Object | Record Name | Key Fields |
|--------|-------------|------------|
| DataUsePurpose | | Name, CanDataSubjectOptOut, LegalBasisId |
| AuthorizationForm | | IsSignatureRequired |
| AuthorizationFormText | | AuthorizationFormId, Locale, SummaryAuthFormText (then set AuthorizationForm.DefaultAuthFormTextId) |
| AuthorizationFormDataUse | | AuthorizationFormId, DataUsePurposeId |
| AuthorizationFormConsent | Per-patient | Status, ConsentGiverId, AuthorizationFormTextId |

## Consent Capture Workflow Checklist

- [ ] DataUsePurpose records created for each clinical use category
- [ ] AuthorizationForm records created for each consent form type
- [ ] AuthorizationFormText created per language with the correct Locale, and AuthorizationForm.DefaultAuthFormTextId set to the fallback text
- [ ] AuthorizationFormDataUse junction records created
- [ ] Enrollment Flow creates AuthorizationFormConsent with Status = Seen when form is shown
- [ ] Enrollment Flow updates Status to Signed after patient acknowledgment
- [ ] CareProgramEnrollee activation gated on AuthorizationFormConsent Status = Signed

## Withdrawal Workflow Checklist

- [ ] Withdrawal workflow records Status = Rejected (new record or update with field history); no deletion
- [ ] Withdrawal workflow does NOT delete the AuthorizationFormConsent record
- [ ] Withdrawal date/time and capture source are recorded
- [ ] Related enrollment status updated if needed

## Notes

(Record any deviations from standard pattern, custom status values, or multi-locale requirements)
