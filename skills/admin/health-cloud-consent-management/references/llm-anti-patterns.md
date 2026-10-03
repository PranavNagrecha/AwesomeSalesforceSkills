# LLM Anti-Patterns: Health Cloud Consent Management

Common mistakes AI assistants make when advising on Health Cloud patient consent. Several were present in earlier versions of this skill; the corrections are grounded in `gotchas.md`.

## Anti-Pattern 1: Using ContactPointConsent for HIPAA Clinical Authorization

**What the LLM generates:** Instructions to create `ContactPointTypeConsent` and `ContactPointConsent` records to track whether a patient authorized clinical use of their PHI.

**Why it happens:** Both object families sit under "consent" in Salesforce material, and marketing consent dominates training data.

**Correct pattern:** Use `AuthorizationFormConsent` against an `AuthorizationFormText` for clinical authorization, with the form linked to a `DataUsePurpose` through `AuthorizationFormDataUse`. Use the contact point consent objects for communication preferences.

**Detection hint:** `ContactPointConsent` or `ContactPointTypeConsent` in a HIPAA authorization design.

---

## Anti-Pattern 2: Inventing an `IsDefault` Flag on `AuthorizationFormText`

**What the LLM generates:** "Set `IsDefault = true` on exactly one AuthorizationFormText per form," and validation SOQL that selects `IsDefault`.

**Why it happens:** "One default child record" is a common pattern, and an earlier version of this skill stated it.

**Correct pattern:** The default is `AuthorizationForm.DefaultAuthFormTextId`, "the ID of the default authorization form text to use if text isn't available for a specific language". Create the form, create the texts, then set the lookup on the form.

**Detection hint:** `IsDefault` anywhere near `AuthorizationFormText`.

---

## Anti-Pattern 3: Setting `Status = 'Withdrawn'`, or Deleting the Consent

**What the LLM generates:** A withdrawal flow that sets `Status = 'Withdrawn'` or `'Revoked'`, or that deletes the `AuthorizationFormConsent` record.

**Why it happens:** The model invents a natural-sounding terminal value, or models withdrawal as the inverse of creation.

**Correct pattern:** The documented values are `Rejected`, `Seen`, and `Signed`. Record withdrawal as `Rejected`, and preserve the signed evidence with a new record per event or an update with field history tracking. Never delete consent records.

**Detection hint:** `Withdrawn`, `Revoked`, or `delete` against `AuthorizationFormConsent`.

---

## Anti-Pattern 4: Putting "Verbal" or "Written" in the Capture Fields

**What the LLM generates:** `ConsentCapturedSource = 'Verbal'` or `'Written'`, with `ConsentCapturedSourceType` left empty.

**Why it happens:** The two field names look like one concept, and "verbal or written" is how consent is described in clinical policy.

**Correct pattern:** `ConsentCapturedSourceType` is a required restricted picklist (`Email`, `InPerson`, `MailingAddress`, `Phone`, `Social`, `Video`, `Web`). `ConsentCapturedSource` is a required string describing the source (for example a staff member or URL). `ConsentCapturedDateTime` and `ConsentGiverId` are also required.

**Detection hint:** A source type value outside the list, or a consent insert missing any required capture field.

---

## Anti-Pattern 5: Assuming Consent Records Enforce Access to PHI

**What the LLM generates:** "Once the AuthorizationFormConsent exists, unconsented patients' records are protected automatically."

**Why it happens:** Models assume objects that describe restrictions also enforce them.

**Correct pattern:** Consent records document consent; they do not change record access. Implement access through org-wide defaults, sharing, and permission sets, and make the enrollment flow check consent status before it activates enrollment.

**Detection hint:** Access control described only in terms of consent records.

---

## Anti-Pattern 6: Toggling Data Protection and Privacy Casually

**What the LLM generates:** "If consent objects behave strangely, turn Data Protection and Privacy off and on again," or a settings deploy copied from an org where it is off.

**Why it happens:** Feature toggles are usually reversible, and the model does not know this one deletes data.

**Correct pattern:** `PartyDataModelSettings.enableConsentManagement` set to false "purges all data protection details, such as privacy preferences and stored consent forms." Keep the setting under change control and never use it for troubleshooting.

**Detection hint:** Any instruction to disable Data Protection and Privacy, or a settings diff that sets it to false.

---

## Anti-Pattern 7: Copying a `PurposeId` Field Onto `DataUsePurpose`

**What the LLM generates:** `new DataUsePurpose(Name = 'Treatment', PurposeId = 'treatment')`.

**Why it happens:** The model invents a code field to pair with the name, as an earlier example in this skill did.

**Correct pattern:** `DataUsePurpose` has `Name`, `Description`, `CanDataSubjectOptOut` (required), and `LegalBasisId` (lookup to `DataUseLegalBasis`). Set `CanDataSubjectOptOut` deliberately for each purpose.

**Detection hint:** `PurposeId` on `DataUsePurpose`, or a purpose insert without `CanDataSubjectOptOut`.

---

## Anti-Pattern 8: Forgetting Electronic Signature Evidence

**What the LLM generates:** An electronic consent design that records status and time, with no mention of IP address, email, or browser.

**Why it happens:** Evidence capture is a settings decision, not a field on the consent object, so the model does not see it.

**Correct pattern:** Decide evidence requirements with compliance and deploy `PrivacySettings` with the needed `authorizationCapture*` fields (API 59.0, default false), plus `authorizationLockingAndVersioning` if records must lock after capture.

**Detection hint:** An electronic signature design with no `PrivacySettings` decision.
