# Examples — Consent Data Model Health

## Example 1: Setting Up the Consent Hierarchy for a Patient Portal Intake Flow

**Context:** A healthcare organization launches an Experience Cloud patient portal. Before a patient is enrolled in a care program, they must view and sign an authorization for treatment. The team needs the consent records and the intake write.

**Problem:** Without a linked hierarchy, the consent row written at intake can't be traced to the wording shown or to the purpose it covers, and the enrollment gate can't filter by purpose.

**Solution (anonymous Apex for a sandbox; field names from the Object Reference):**

```apex
DataUsePurpose treatment = new DataUsePurpose(
    Name = 'Treatment Authorization',
    CanDataSubjectOptOut = false
);
insert treatment;

AuthorizationForm form = new AuthorizationForm(
    Name = 'HIPAA Authorization for Treatment',
    IsSignatureRequired = true,
    EffectiveFromDate = Date.today(),
    RevisionNumber = 'rev1.0'
);
insert form;

AuthorizationFormText textV1 = new AuthorizationFormText(
    Name = 'HIPAA Authorization v1.0',
    AuthorizationFormId = form.Id,
    DetailAuthorizationFormText = 'By signing this form, you authorize...'
);
insert textV1;

form.DefaultAuthFormTextId = textV1.Id;
update form;

// Purposes attach to the form, not to the text
insert new AuthorizationFormDataUse(
    Name = 'HIPAA Treatment - Treatment Authorization',
    AuthorizationFormId = form.Id,
    DataUsePurposeId = treatment.Id
);
```

At intake completion (Apex invocable or flow Create Records with the same fields):

```apex
public with sharing class ConsentIntake {
    public static void recordSignature(Id individualId, Id formTextId, String portalUrl) {
        if (individualId.getSObjectType() != Individual.SObjectType) {
            throw new IllegalArgumentException('Consent giver must be an Individual Id');
        }
        insert new AuthorizationFormConsent(
            Name = 'Treatment consent ' + Datetime.now().format('yyyy-MM-dd'),
            ConsentGiverId = individualId,
            AuthorizationFormTextId = formTextId,
            Status = 'Signed',
            ConsentCapturedSourceType = 'Web',
            ConsentCapturedSource = portalUrl,
            ConsentCapturedDateTime = Datetime.now()
        );
    }
}
```

**Why it works:** Each consent row points at the exact text shown, the text belongs to a form, and the form is linked to its purpose, so any purpose-specific check can follow the chain. The row carries the required name, capture time, source, and source type, and the giver type is enforced before insert.

---

## Example 2: Checking Treatment Consent Before Showing Clinical Records

**Context:** An Apex service behind an LWC must confirm a signed treatment authorization before returning clinical data.

**Problem:** A check on `Status = 'Signed'` alone returns true for a patient who signed only a research authorization. And a filter like `AuthorizationFormText.AuthorizationFormDataUses...` doesn't work: data uses hang off the form, not the text, and a WHERE clause can't walk down a child relationship that way.

**Solution:** Use the two-step check from SKILL.md Pattern 2 (`ConsentCheck.hasSignedConsent(individualId, 'Treatment Authorization')`), then:

```apex
public with sharing class ClinicalRecordService {
    public class ConsentException extends Exception {}

    public static ClinicalRecord__c getClinicalRecord(Id patientIndividualId, Id recordId) {
        if (!ConsentCheck.hasSignedConsent(patientIndividualId, 'Treatment Authorization')) {
            throw new ConsentException('No signed treatment authorization on file; route to consent intake.');
        }
        return [SELECT Id, Name, Clinical_Notes__c FROM ClinicalRecord__c WHERE Id = :recordId WITH USER_MODE LIMIT 1];
    }
}
```

**Why it works:** The purpose filter is applied where the data model keeps it (AuthorizationFormDataUse), and the record query still runs in user mode, because consent is a precondition, not an access grant.

---

## Anti-Pattern: Using ContactPointConsent to Check Treatment Authorization

**What practitioners do:** Query ContactPointConsent (consent to be contacted through a specific email address or phone number) to decide whether clinical data may be used.

**What goes wrong:** Contact-point consents record communication preferences. They aren't authorization-form consents, so the check returns nothing useful: every patient is blocked, or, if the absence check is inverted, everyone is cleared.

**Correct approach:** Check AuthorizationFormConsent through its form text, form, and the form's data uses, filtered on the consent giver and `Status = 'Signed'`. Keep ContactPointConsent and ContactPointTypeConsent for communication preferences.
