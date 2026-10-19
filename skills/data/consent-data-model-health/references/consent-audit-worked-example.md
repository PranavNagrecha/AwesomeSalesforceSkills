# Worked Example — Auditing an Existing Consent Trail

**Situation:** A Health Cloud org has run patient intake for two years. Compliance asks: can we prove that every active care-program enrollee signed a treatment authorization, and what wording they signed?

## Step 1: Export what exists

```sql
SELECT Id, Name, CanDataSubjectOptOut FROM DataUsePurpose
SELECT Id, Name, IsSignatureRequired, DefaultAuthFormTextId, EffectiveFromDate, EffectiveToDate, RevisionNumber FROM AuthorizationForm
SELECT Id, Name, AuthorizationFormId, ContentDocumentId, Locale, LastModifiedDate FROM AuthorizationFormText
SELECT Id, AuthorizationFormId, DataUsePurposeId FROM AuthorizationFormDataUse
SELECT Id, ConsentGiverId, ConsentGiver.Type, Status, ConsentCapturedSource,
       ConsentCapturedSourceType, ConsentCapturedDateTime, AuthorizationFormTextId
FROM AuthorizationFormConsent
```

Save each result as JSON in one folder and run:

```bash
python3 skills/data/consent-data-model-health/scripts/check_consent_data_model_health.py --manifest-dir audit-export
```

## Step 2: Read the findings

| Finding | Count | Meaning | Action |
|---|---|---|---|
| Consent giver is Contact | 3,410 | Intake v1 wrote Contact Ids; the enrollment gate looks for Individual Ids | Insert corrected rows with the Individual Id (via `Contact.IndividualId`) copying the original capture fields; keep the originals as history |
| `ConsentCapturedSourceType` empty | 3,410 | Same rows; v1 put `Web` into `ConsentCapturedSource` | Note the gap in the audit; fix intake so both fields are written |
| `Status` = `Seen` on enrollees | 212 | Patients viewed but didn't sign; the form has `IsSignatureRequired` = true | Route to re-consent; review how these were enrolled |
| Form text edited after first use | 1 | `LastModifiedDate` on text v1 is later than the first consent pointing at it | Retrieve the earlier wording from document version history; create a v2 text instead of editing |
| Data use missing purpose | 0 | — | — |

## Step 3: Check enrollees against signed treatment consent

```apex
Set<Id> treatmentForms = new Set<Id>();
for (AuthorizationFormDataUse du : [SELECT AuthorizationFormId FROM AuthorizationFormDataUse WHERE DataUsePurpose.Name = 'Treatment Authorization']) {
    treatmentForms.add(du.AuthorizationFormId);
}
Set<Id> signedGivers = new Set<Id>();
for (AuthorizationFormConsent c : [
    SELECT ConsentGiverId FROM AuthorizationFormConsent
    WHERE Status = 'Signed' AND AuthorizationFormText.AuthorizationFormId IN :treatmentForms
]) {
    signedGivers.add(c.ConsentGiverId);
}
System.debug(LoggingLevel.INFO, 'Givers with signed treatment consent: ' + signedGivers.size());
```

Compare that set with the Individual Ids of active enrollees (resolved the same way the enrollment gate resolves them). Every enrollee outside the set is an audit exception.

## Step 4: Close the loop

- Ship the corrected intake (Individual Id, source type, source, capture time) and the enrollment gate together.
- Re-run the checker on a fresh export; the target is zero ERROR lines and no Contact-type givers.
- File the exceptions list and the form-text history with compliance, separately from the PHI sharing review.
