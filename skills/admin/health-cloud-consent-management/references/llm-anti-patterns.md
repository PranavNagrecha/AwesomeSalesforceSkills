# LLM Anti-Patterns — Health Cloud Consent Management

Common mistakes AI coding assistants make when generating or advising on Health Cloud consent management.

## Anti-Pattern 1: Using ContactPointConsent for HIPAA Clinical Authorization

**What the LLM generates:** Instructions to create ContactPointTypeConsent and ContactPointConsent records to track whether a patient has authorized clinical use of their PHI, citing Salesforce Consent Management documentation.

**Why it happens:** ContactPointConsent appears in Salesforce's general "Consent Management" documentation alongside AuthorizationFormConsent. LLMs conflate these because both are called "consent" and both appear in the same product documentation section. GDPR/CCPA marketing consent has far more online training data.

**Correct pattern:**
Use `AuthorizationFormConsent` for HIPAA clinical authorization. Use `ContactPointConsent` for marketing communication channel preferences. HIPAA authorization requires specific fields (clinical purpose, PHI categories, expiration date, ConsentGiverId) not present on ContactPointConsent.

**Detection hint:** If the consent solution uses `ContactPointConsent`, `ContactPointTypeConsent`, or `ContactPointAddress` for a HIPAA clinical authorization use case, the wrong object family is being applied.

---

## Anti-Pattern 2: Deleting AuthorizationFormConsent on Withdrawal

**What the LLM generates:** Code or instructions to delete `AuthorizationFormConsent` records when a patient withdraws consent, treating withdrawal as a "remove the consent record" operation.

**Why it happens:** LLMs model withdrawal as the inverse of consent creation. In most data models, "undo" means deletion. HIPAA's audit trail requirement — which mandates retaining the history of when consent was obtained and when it was revoked — is a compliance-specific requirement not present in general training data.

**Correct pattern:**
Update the `Status` field on the existing `AuthorizationFormConsent` record to a terminal value such as "Withdrawn". Never delete consent records. The audit trail must show when consent was obtained, when it was in effect, and when it was withdrawn.

**Detection hint:** If the withdrawal implementation includes `delete [authFormConsentRecord]` or equivalent DML, it is destroying the HIPAA audit trail.

---

## Anti-Pattern 3: Assuming AuthorizationFormConsent Enforces PHI Access Control

**What the LLM generates:** Claims that creating AuthorizationFormConsent records automatically restricts PHI record access for patients who have not consented, or that enrolling a patient without consent will be blocked by the platform automatically.

**Why it happens:** LLMs often assume that data model objects that represent restrictions also enforce those restrictions. In Salesforce, data model objects are records — access control is a separate concern governed by sharing rules, profiles, and permission sets.

**Correct pattern:**
`AuthorizationFormConsent` is a tracking and audit object. It documents that consent was obtained — it does not technically enforce PHI access restrictions. Access control must be implemented separately through OWD settings, sharing rules, and care team role-based record access. The enrollment Flow must explicitly check consent status before proceeding.

**Detection hint:** If the implementation relies on AuthorizationFormConsent alone to enforce access control without separate sharing rule configuration, the access control gap is present.

---

## Anti-Pattern 4: Creating Multiple Default AuthorizationFormTexts

**What the LLM generates:** Instructions to create multiple `AuthorizationFormText` records for the same form (one per locale) and set `IsDefault = true` on all of them to ensure the form works for all languages.

**Why it happens:** LLMs interpret "default" as a per-locale flag and logically conclude that each locale variant should be its default. The platform constraint — exactly one IsDefault = true per form — is a specific implementation detail not inferrable from the field name alone.

**Correct pattern:**
Only one `AuthorizationFormText` per `AuthorizationForm` can have `IsDefault = true`. This is the fallback text when no locale match is found. For multilingual consent, create one AuthorizationFormText per locale but set IsDefault = true on only one (typically the primary language). The platform uses locale matching to select the appropriate text.

**Detection hint:** If instructions set `IsDefault = true` on multiple AuthorizationFormText records for the same form, the implementation will fail at runtime.

---

## Anti-Pattern 5: Skipping AuthorizationFormDataUse Junction Records

**What the LLM generates:** Instructions that create DataUsePurpose and AuthorizationForm records but skip creating the `AuthorizationFormDataUse` junction object, assuming the relationship is established elsewhere.

**Why it happens:** Junction objects are commonly omitted in LLM-generated configuration steps because the two primary objects can exist independently. The junction record is a less prominent part of the documentation and is easy to miss.

**Correct pattern:**
`AuthorizationFormDataUse` must be created explicitly to link each `AuthorizationForm` to its `DataUsePurpose`. Without this junction record, the consent form is not associated with any clinical use purpose, breaking the full consent hierarchy and potentially causing consent records to be created with no stated purpose.

**Detection hint:** If the consent setup steps do not include creating `AuthorizationFormDataUse` records, the hierarchy is incomplete.
