# Examples — Consent Data Model Health

## Example 1: Setting Up the Consent Hierarchy for a Patient Portal Intake Flow

**Context:** A healthcare organization is launching a patient portal built on Experience Cloud. Before a patient can be enrolled in a care program, they must view and sign a HIPAA Authorization for Treatment. The development team needs to configure the consent hierarchy and wire it to an intake Screen Flow.

**Problem:** Without a properly structured hierarchy, the AuthorizationFormConsent record created at intake will have no traceable link to a specific form version or data use purpose. Auditors cannot verify what the patient consented to, and the CareProgramEnrollee activation gate cannot reliably filter by purpose.

**Solution:**

Step 1 — Create the DataUsePurpose record (can be done via Setup UI or data load):

```apex
DataUsePurpose dup = new DataUsePurpose();
dup.Name = 'Treatment Authorization';
dup.CanDataSubjectOptOut = false; // HIPAA treatment authorization is not opt-out
insert dup;
```

Step 2 — Create the AuthorizationForm:

```apex
AuthorizationForm af = new AuthorizationForm();
af.Name = 'HIPAA Authorization for Treatment';
af.IsSignatureRequired = true;
insert af;
```

Step 3 — Create the AuthorizationFormText with the legal body text:

```apex
AuthorizationFormText aft = new AuthorizationFormText();
aft.AuthorizationFormId = af.Id;
aft.Name = 'HIPAA Authorization v1.0';
aft.ContentDocument = 'By signing this form, you authorize...'; // abbreviated
aft.Language = 'en_US';
insert aft;
```

Step 4 — Create the AuthorizationFormDataUse junction:

```apex
AuthorizationFormDataUse afdu = new AuthorizationFormDataUse();
afdu.AuthorizationFormTextId = aft.Id;
afdu.DataUsePurposeId = dup.Id;
insert afdu;
```

Step 5 — At intake flow completion, create the AuthorizationFormConsent using the patient's Individual ID:

```apex
// individualId is the Id of the Individual record, NOT the Contact Id
AuthorizationFormConsent afc = new AuthorizationFormConsent();
afc.ConsentGiverId = individualId;
afc.AuthorizationFormTextId = aft.Id;
afc.Status = 'Signed';
afc.ConsentCapturedSource = 'Web';
afc.ConsentCapturedDateTime = Datetime.now();
insert afc;
```

**Why it works:** The chain DataUsePurpose → AuthorizationForm → AuthorizationFormText → AuthorizationFormDataUse ensures each consent record is fully traceable. The `IsSignatureRequired = true` flag on the form means only `Signed` status satisfies downstream consent checks. Populating `ConsentCapturedSource` and `ConsentCapturedDateTime` satisfies HIPAA audit trail requirements.

---

## Example 2: Querying AuthorizationFormConsent to Verify Consent Before Clinical Record Access

**Context:** An Apex service class exposes a method called before displaying a patient's clinical records in an LWC. The method must confirm the patient has a valid signed Treatment authorization before returning any data.

**Problem:** A naive check queries only `Status = 'Signed'` without filtering on DataUsePurpose. This returns true if the patient signed a Research consent form but not a Treatment authorization — a false positive that could result in unauthorized PHI disclosure.

**Solution:**

```apex
public static Boolean hasSignedTreatmentConsent(Id individualId) {
    List<AuthorizationFormConsent> consents = [
        SELECT Id, Status, ConsentCapturedDateTime
        FROM AuthorizationFormConsent
        WHERE ConsentGiverId = :individualId
          AND Status = 'Signed'
          AND AuthorizationFormText.AuthorizationFormDataUses.DataUsePurpose.Name
              = 'Treatment Authorization'
        ORDER BY ConsentCapturedDateTime DESC
        LIMIT 1
    ];
    return !consents.isEmpty();
}
```

Usage in the service class:

```apex
public static ClinicalRecord__c getClinicalRecord(Id patientIndividualId, Id recordId) {
    if (!hasSignedTreatmentConsent(patientIndividualId)) {
        throw new ConsentException(
            'Patient does not have signed Treatment Authorization. ' +
            'Route to consent intake before accessing clinical records.'
        );
    }
    return [SELECT Id, Name, ClinicalNotes__c FROM ClinicalRecord__c WHERE Id = :recordId LIMIT 1];
}
```

**Why it works:** Filtering on `AuthorizationFormText.AuthorizationFormDataUses.DataUsePurpose.Name` traverses the full hierarchy and ensures only a consent record linked to the correct data use purpose satisfies the check. The `ORDER BY ConsentCapturedDateTime DESC LIMIT 1` pattern retrieves the most recent authorization in case of multiple records.

---

## Anti-Pattern: Using ContactPointConsent to Check HIPAA Authorization

**What practitioners do:** Query `ContactPointConsent` (the marketing/communication consent object) to verify whether a patient has authorized PHI access before displaying clinical records.

**What goes wrong:** `ContactPointConsent` tracks communication channel preferences (email opt-in, SMS opt-out). It has no relationship to `AuthorizationFormConsent` or the DataUsePurpose hierarchy. A query against this object will always return empty results for HIPAA authorization checks, causing either false denials (all patients blocked) or false clearances (if the absence check is inverted). This is an architecturally silent failure — no error is thrown and no warning is logged.

**Correct approach:** Always use `AuthorizationFormConsent` with a `ConsentGiverId` (Individual ID) filter and a DataUsePurpose filter for HIPAA authorization checks. Reserve `ContactPointConsent` exclusively for communication preference management.
