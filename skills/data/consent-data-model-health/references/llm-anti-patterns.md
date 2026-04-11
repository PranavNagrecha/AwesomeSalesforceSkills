# LLM Anti-Patterns — Consent Data Model Health

Common mistakes AI coding assistants make when generating or advising on the Health Cloud consent data model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating HIPAA Consent with Marketing Consent Objects

**What the LLM generates:** Code or advice that queries `ContactPointConsent` or `ContactPointTypeConsent` to verify patient HIPAA authorization before clinical record access, or that recommends using the Privacy Center consent UI to manage Health Cloud patient consent.

**Why it happens:** Training data contains significantly more content about Salesforce Privacy Center and Marketing Cloud consent management (ContactPointConsent) than about Health Cloud's HIPAA-specific consent model. LLMs default to the more commonly described pattern.

**Correct pattern:**

```apex
// WRONG — ContactPointConsent is for marketing communication preferences
List<ContactPointConsent> cpc = [
    SELECT Id FROM ContactPointConsent WHERE DataUsePurposeId = :purposeId
    AND ConsentGiverId = :individualId
];

// CORRECT — AuthorizationFormConsent is the HIPAA authorization trail
List<AuthorizationFormConsent> afc = [
    SELECT Id, Status FROM AuthorizationFormConsent
    WHERE ConsentGiverId = :individualId
    AND Status = 'Signed'
];
```

**Detection hint:** Any code or recommendation referencing `ContactPointConsent`, `ContactPointTypeConsent`, or Privacy Center in the context of Health Cloud clinical enrollment or PHI access is likely wrong. Flag for review.

---

## Anti-Pattern 2: Assuming AuthorizationFormConsent Grants PHI Record Access

**What the LLM generates:** Instructions that tell practitioners to create AuthorizationFormConsent records as the step that "enables access" to a patient's clinical records, without any mention of sharing rules or OWD settings.

**Why it happens:** The word "consent" implies permission, which LLMs map to access control. The model hallucinates a causal relationship between the consent record and record visibility that does not exist in the Salesforce platform.

**Correct pattern:**

```
AuthorizationFormConsent = HIPAA authorization audit trail only.
Record visibility = OWD + sharing rules + permission sets.

These are independent systems. Both must be correctly configured.
Creating a consent record does NOT change who can see the record.
```

**Detection hint:** Any statement like "once the patient signs the form, care team members will be able to see the record" without mention of sharing rules is an anti-pattern. Flag and add explicit sharing rule guidance.

---

## Anti-Pattern 3: Using Contact ID Instead of Individual ID in ConsentGiverId

**What the LLM generates:** Apex or Flow code that sets `ConsentGiverId` to a Contact record ID retrieved from the trigger context or a related field, rather than first resolving the Contact's associated Individual ID.

**Why it happens:** Contact is the most familiar person-level object in Salesforce. LLMs default to Contact when they need a person record ID, missing the Health Cloud requirement that consent links to Individual.

**Correct pattern:**

```apex
// WRONG — passes Contact Id directly
afc.ConsentGiverId = contactRecord.Id;

// CORRECT — resolves Individual Id from Contact first
Contact c = [SELECT IndividualId FROM Contact WHERE Id = :contactRecord.Id LIMIT 1];
afc.ConsentGiverId = c.IndividualId;
```

**Detection hint:** Any `ConsentGiverId =` assignment that sources the value directly from a Contact, Account, or PersonAccount ID field (without a prior `IndividualId` lookup) is this anti-pattern. Search for `ConsentGiverId = :` followed by a variable that doesn't have `Individual` in its name.

---

## Anti-Pattern 4: Treating the CareProgramEnrollee Consent Gate as Optional

**What the LLM generates:** Health Cloud implementation guides or code reviews that describe the consent hierarchy setup steps but omit any mention of blocking CareProgramEnrollee activation when consent is absent, treating consent records as a reporting-only concern.

**Why it happens:** LLMs generate documentation-style outputs that describe what each object stores but do not reason about the operational gate that enforces the requirement. The gate is a custom-built control, not a native platform feature, so it does not appear in standard API references that LLMs are trained on.

**Correct pattern:**

```
After implementing the consent hierarchy, ALWAYS implement a before-save
Flow or Apex trigger on CareProgramEnrollee that:
1. Queries AuthorizationFormConsent for the enrollee's Individual ID
2. Filters by Status = 'Signed' and the relevant DataUsePurpose
3. Blocks the status transition to 'Active' if no signed consent exists
```

**Detection hint:** Any Health Cloud consent implementation plan that does not include a validation step on CareProgramEnrollee is incomplete. Look for the absence of "before-save," "validation rule," or "consent gate" in enrollment workflow descriptions.

---

## Anti-Pattern 5: Using Wrong Status Values or Case

**What the LLM generates:** Consent record creation code or data migration scripts that use status values like `'Approved'`, `'Active'`, `'Consented'`, `'signed'` (lowercase), or `'SIGNED'` (uppercase) instead of the exact picklist values `'Seen'` or `'Signed'`.

**Why it happens:** LLMs generalize from other Salesforce objects (Case Status, Opportunity Stage, Lead Status) that use `Active`, `Closed`, `Approved` vocabulary. The exact two-value picklist on AuthorizationFormConsent is not well-represented in training data.

**Correct pattern:**

```apex
// WRONG — these are not valid AuthorizationFormConsent Status values
afc.Status = 'Approved';
afc.Status = 'signed';    // wrong case
afc.Status = 'SIGNED';    // wrong case
afc.Status = 'Consented'; // not a valid value

// CORRECT — exact picklist values
afc.Status = 'Signed';  // patient executed the authorization
afc.Status = 'Seen';    // patient viewed but did not sign
```

**Detection hint:** Any string literal in `Status =` assignments that is not exactly `'Seen'` or `'Signed'` (sentence case) is this anti-pattern. Search for `.Status = '` and verify the value against the two valid options.

---

## Anti-Pattern 6: Editing AuthorizationFormText In Place for Form Revisions

**What the LLM generates:** Guidance to update the `ContentDocument` field on an existing `AuthorizationFormText` record when the legal team revises the consent form language, treating the record like an editable configuration item.

**Why it happens:** LLMs model "update the form" as editing the existing record, following standard CRUD patterns. The audit trail implication of mutating a record that historical consent records point to is not surfaced in generic API documentation.

**Correct pattern:**

```
DO NOT update existing AuthorizationFormText records.
AuthorizationFormText is append-only.

On form revision:
1. Create a new AuthorizationFormText record (e.g., "HIPAA Authorization v2.0")
2. Link it to the same AuthorizationForm
3. Create new AuthorizationFormDataUse records for the new text
4. Update the intake Flow to present the new AuthorizationFormText ID
5. Old consent records retain their reference to the old text version
```

**Detection hint:** Any instruction to "update" or "edit" an `AuthorizationFormText` record in the context of a form revision is this anti-pattern.
