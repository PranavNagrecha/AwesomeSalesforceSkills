# Examples — Health Cloud Consent Management

## Example 1: Configuring HIPAA Authorization Form Hierarchy

**Context:** A healthcare organization is implementing Health Cloud for chronic disease management. Before patients can be enrolled in care programs and their PHI accessed, HIPAA authorization must be captured and tracked.

**Problem:** The team is unsure which objects to create and in what order, and a previously attempted configuration resulted in consent forms not displaying during enrollment testing.

**Solution:**
1. Create a `DataUsePurpose` record: Name = "Treatment", PurposeId = treatment, CanDataSubjectOptOut = false.
2. Create an `AuthorizationForm` record: Name = "HIPAA Authorization for Treatment", IsSignatureRequired = true.
3. Create an `AuthorizationFormText` record: AuthorizationFormId = [form above], Locale = "en_US", IsDefault = true, SummaryAuthFormText = "This form authorizes [Org Name] to use your health information for treatment purposes...". (Full legal text goes in the text field.)
4. Create an `AuthorizationFormDataUse` record: AuthorizationFormId = [form above], DataUsePurposeId = [treatment purpose above].
5. In the enrollment Record-Triggered Flow: after creating the CareProgramEnrollee record in Draft status, create an `AuthorizationFormConsent` record with Status = Seen, ConsentGiverId = [patient Individual ID], AuthorizationFormTextId = [form text above].
6. When the patient acknowledges/signs: update the AuthorizationFormConsent Status to Signed.
7. Add a Flow decision: only update CareProgramEnrollee to Active if related AuthorizationFormConsent Status = Signed.

**Why it works:** The five-object hierarchy separates the reusable form template from the per-patient consent record. Setting IsDefault = true on AuthorizationFormText ensures the form renders correctly. The CareProgramEnrollee status gate prevents PHI access before consent is documented.

---

## Example 2: Handling Patient Consent Withdrawal

**Context:** A patient calls requesting to withdraw their HIPAA authorization for research purposes. A care coordinator needs to process the withdrawal in Health Cloud.

**Problem:** A junior admin deleted the AuthorizationFormConsent record, which destroyed the consent history and created a HIPAA audit trail gap.

**Solution:**
1. Query the patient's AuthorizationFormConsent records: look up records where ConsentGiverId = [patient Individual ID] and the related AuthorizationForm covers the research purpose.
2. Update the AuthorizationFormConsent record: set Status = Withdrawn, set ConsentCapturedDateTime to the withdrawal date/time, and update ConsentCapturedSource to reflect how the withdrawal was communicated (e.g., "Written").
3. Do NOT delete the AuthorizationFormConsent record. The history of when consent was obtained and when it was withdrawn must be preserved.
4. Optionally, update the related CareProgramEnrollee status if the withdrawn consent makes the enrollment invalid.
5. Document the withdrawal action in a related Activity/Note on the patient record for care coordinator reference.

**Why it works:** HIPAA requires retention of the complete consent history — including when consent was given and when it was revoked. Updating Status rather than deleting preserves the audit trail. The platform's field audit trail captures all status changes if Shield Field Audit Trail is enabled for this object.

---

## Anti-Pattern: Using ContactPointConsent for HIPAA Clinical Authorization

**What practitioners do:** Configure ContactPointConsent and ContactPointTypeConsent records to track whether a patient has authorized clinical use of their PHI, because these objects appear under "Consent Management" in Salesforce documentation.

**What goes wrong:** ContactPointConsent is designed for GDPR/CCPA marketing opt-in/opt-out. It tracks communication channel preferences (email, phone), not clinical authorization for PHI use. Using ContactPointConsent for HIPAA purposes means: (a) the required HIPAA authorization fields (clinical purpose, specific PHI categories, expiration) cannot be captured; (b) the object is not integrated with Health Cloud's enrollment workflow; (c) HIPAA regulators will not accept ContactPointConsent records as evidence of valid patient authorization.

**Correct approach:** Use AuthorizationFormConsent for HIPAA clinical authorization. Use ContactPointConsent for marketing and communication preferences. These are separate regulatory requirements with separate object implementations.
