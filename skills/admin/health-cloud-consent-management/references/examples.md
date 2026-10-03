# Examples: Health Cloud Consent Management

## Example 1: Building a HIPAA Authorization for Treatment in Two Languages

**Context:** A health system implements Health Cloud for chronic disease management. Patients must authorize use of their health information for treatment before care program enrollment. Patients read English or Spanish.

**Problem:** A first attempt created two `AuthorizationFormText` records and tried to mark one with an `IsDefault` flag. That field does not exist. The form had no default text, and patients whose language matched neither text saw an empty consent step.

**Solution:** Build the records in dependency order. The default text is set on the form after the texts exist. This anonymous Apex script runs in a sandbox (Developer Console, or `sf apex run --file`):

```apex
// 1. Purpose
DataUsePurpose treatment = new DataUsePurpose(
    Name = 'Treatment',
    Description = 'Use of health information to provide and coordinate care',
    CanDataSubjectOptOut = true
);
insert treatment;

// 2. Form, then its texts
AuthorizationForm form = new AuthorizationForm(
    Name = 'HIPAA Authorization for Treatment',
    IsSignatureRequired = true,
    RevisionNumber = 'rev1.0',
    EffectiveFromDate = Date.today()
);
insert form;

AuthorizationFormText textEn = new AuthorizationFormText(
    Name = 'HIPAA Treatment Authorization (English)',
    AuthorizationFormId = form.Id,
    Locale = 'en_US',
    SummaryAuthFormText = 'I authorize the use of my health information for my treatment.'
);
AuthorizationFormText textEs = new AuthorizationFormText(
    Name = 'HIPAA Treatment Authorization (Spanish)',
    AuthorizationFormId = form.Id,
    Locale = 'es',
    SummaryAuthFormText = 'Autorizo el uso de mi informacion de salud para mi tratamiento.'
);
insert new List<AuthorizationFormText>{ textEn, textEs };

// 3. Default text lives on the form
form.DefaultAuthFormTextId = textEn.Id;
update form;

// 4. Link the form to its purpose
insert new AuthorizationFormDataUse(
    Name = 'Treatment authorization data use',
    AuthorizationFormId = form.Id,
    DataUsePurposeId = treatment.Id
);
```

Then, in the enrollment flow, create the patient's consent when the form is shown and update it when they sign:

```apex
AuthorizationFormConsent consent = new AuthorizationFormConsent(
    Name = 'Treatment authorization - Maria Lopez',
    ConsentGiverId = patientPersonAccountId,      // Account, Contact, Individual, Lead, or User
    AuthorizationFormTextId = textEs.Id,
    ConsentCapturedDateTime = System.now(),
    ConsentCapturedSourceType = 'InPerson',
    ConsentCapturedSource = 'Front desk tablet, Eastside Clinic',
    Status = 'Seen'
);
insert consent;
// on signature
consent.Status = 'Signed';
consent.ConsentCapturedDateTime = System.now();
update consent;
```

**Why it works:** Every required field is set (`Name`, `AuthorizationFormTextId`, `ConsentGiverId`, `ConsentCapturedDateTime`, `ConsentCapturedSource`, `ConsentCapturedSourceType`), the status values are the documented `Seen` and `Signed`, and the form has a default text for unmatched languages. UNVERIFIED (2026-10-03): `en_US` and `es` are shown as `Locale` values; `Locale` is a restricted picklist, so read the org's allowed values with a describe call before loading. `patientPersonAccountId` and `textEs` stand for values from your own context.

---

## Example 2: Recording a Withdrawal Without Losing the Signature

**Context:** A patient calls to withdraw their authorization for research use.

**Problem:** A junior admin deleted the `AuthorizationFormConsent` record, so nothing showed that the patient had ever signed. A later attempt set `Status = 'Withdrawn'` and failed, because the picklist allows only `Rejected`, `Seen`, and `Signed`.

**Solution:** The team uses the "new record per event" design. The signed record stays untouched, and the withdrawal is its own record:

```apex
AuthorizationFormConsent signed = [
    SELECT Id, ConsentGiverId, AuthorizationFormTextId
    FROM AuthorizationFormConsent
    WHERE ConsentGiverId = :patientId
      AND AuthorizationFormText.AuthorizationForm.Name = 'HIPAA Authorization for Research'
      AND Status = 'Signed'
    ORDER BY ConsentCapturedDateTime DESC
    LIMIT 1
];
insert new AuthorizationFormConsent(
    Name = 'Research authorization withdrawn',
    ConsentGiverId = signed.ConsentGiverId,
    AuthorizationFormTextId = signed.AuthorizationFormTextId,
    ConsentCapturedDateTime = System.now(),
    ConsentCapturedSourceType = 'Phone',
    ConsentCapturedSource = 'Patient call logged by care coordinator',
    Status = 'Rejected'
);
```

Reports and the enrollment flow then read the latest record per patient and form:

```sql
SELECT ConsentGiverId, AuthorizationFormText.AuthorizationForm.Name, Status, ConsentCapturedDateTime
FROM AuthorizationFormConsent
WHERE ConsentGiverId = :patientId
ORDER BY ConsentCapturedDateTime DESC
```

**Why it works:** The signed record proves consent was given and when; the rejected record proves when it ended and how it was communicated. No record is deleted, and only documented status values are used. If the org prefers one record per patient and form, update `Status` to `Rejected` instead, with field history tracking on `AuthorizationFormConsent` so the earlier `Signed` value stays in history.

---

## Anti-Pattern: Using ContactPointConsent for HIPAA Clinical Authorization

**What practitioners do:** Configure `ContactPointConsent` and `ContactPointTypeConsent` records to track whether a patient authorized clinical use of their PHI, because these objects appear under "Consent Management" in Salesforce documentation.

**What goes wrong:** Channel consent records whether someone may be contacted on a channel. It does not record consent to a specific authorization form text, so the form version, language, capture time, and signature status are missing, and the record is not tied to enrollment.

**Correct approach:** Use `AuthorizationFormConsent` against an `AuthorizationFormText` for clinical authorization. Use the contact point consent objects for marketing and communication preferences.
