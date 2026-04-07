# LLM Anti-Patterns — Care Program Management

Common mistakes AI coding assistants make when generating or advising on Care Program Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating CarePlan with CareProgram

**What the LLM generates:** Instructions to create `CarePlan` records for population-level program enrollment, or SOQL queries joining `CarePlan` to enrolled patients as if `CarePlan` is the enrollment container.

**Why it happens:** The phrase "care program" appears in business requirements and documentation that also references "care plans." LLMs conflate the two terms because they are both Health Cloud concepts with "care" in the name. Training data frequently uses the terms interchangeably in non-technical contexts.

**Correct pattern:**

```
Population-level enrollment: CareProgram → CareProgramEnrollee
Per-patient task/goal management: CarePlan (linked to a specific patient, not a program)

WRONG: CarePlan records used to group patients into a "diabetes program"
RIGHT: CareProgram record with CareProgramEnrollee junction records for each patient
```

**Detection hint:** Look for `CarePlan` in any context involving enrollment, program membership, or population-level reporting. If the task is about enrolling patients into a program, `CareProgram` is the correct root object.

---

## Anti-Pattern 2: Assuming Patient Program Outcome Tracking Is Available in Base Health Cloud

**What the LLM generates:** Code or configuration steps that create `PatientProgramOutcome` records assuming the object is available in any Health Cloud org.

**Why it happens:** `PatientProgramOutcome` is documented in the Health Cloud Developer Guide and appears in the org's schema browser even without the add-on license. LLMs read documentation without license-gating context and generate implementations that will fail in production for most orgs.

**Correct pattern:**

```
WRONG: "Create a PatientProgramOutcome record linked to the CareProgramEnrollee."
RIGHT: "Patient Program Outcome Management requires a separately licensed permission set
        (API v61.0+). Verify the license exists in Setup → Company Information → Licenses
        and the 'Patient Program Outcome Management' permission set is available and assigned
        before creating PatientProgramOutcome records."
```

**Detection hint:** Any mention of `PatientProgramOutcome` without a preceding note about the separate license requirement is a red flag.

---

## Anti-Pattern 3: Omitting the AuthorizationFormText Locale Requirement

**What the LLM generates:** Consent setup instructions that create `AuthorizationForm` and `AuthorizationFormText` records without specifying the `locale` field, or with a generic locale value like `en`.

**Why it happens:** The `locale` field requirement is a non-obvious constraint that is not prominently featured in most LLM training data about consent setup. LLMs follow the obvious happy path (create the form, link it, done) and miss the locale exact-match requirement that causes silent failures.

**Correct pattern:**

```
WRONG: Create AuthorizationFormText with locale = "en"
RIGHT: Create AuthorizationFormText with locale = "en_US" (or the exact locale string
       of each target user population). Create one AuthorizationFormText record per
       locale. Validate by testing enrollment as a non-admin user in each active locale.
```

**Detection hint:** Any consent setup guidance that does not mention the `locale` field on `AuthorizationFormText` or does not call out the exact-match requirement is incomplete.

---

## Anti-Pattern 4: Creating CareProgramEnrolleeProduct Before Parent Records Exist

**What the LLM generates:** A single transaction that inserts `CareProgram`, `CareProgramProduct`, `CareProgramEnrollee`, and `CareProgramEnrolleeProduct` records in an undefined order, or a data load script that does not enforce hierarchy order.

**Why it happens:** LLMs tend to generate efficient-looking batch operations and do not always account for the foreign key dependency chain. The hierarchy order constraint is not enforced by an obvious schema constraint visible in the object model descriptions that LLMs are trained on.

**Correct pattern:**

```
Required insertion order:
1. CareProgram
2. CareProgramProduct (references CareProgram)
3. CareProgramProvider (references CareProgram)
4. CareProgramEnrollee (references CareProgram)
5. CareProgramEnrolleeProduct (references both CareProgramEnrollee AND CareProgramProduct)

WRONG: Single Apex transaction inserting all five object types simultaneously
RIGHT: Insert each level, capture IDs, then insert the next level using those IDs
```

**Detection hint:** Look for bulk insert operations across multiple levels of the Care Program hierarchy in a single DML statement or upsert call. These will fail if parent records have not been committed first.

---

## Anti-Pattern 5: Treating CareProgramEnrollee Status as Editable Without Consent

**What the LLM generates:** Instructions to directly set `CareProgramEnrollee.Status = 'Active'` programmatically without first creating the `AuthorizationFormConsent` record.

**Why it happens:** `Status` is a standard picklist field on `CareProgramEnrollee`. LLMs see it as a simple field update and do not account for the consent prerequisite, which is enforced through a combination of UI validation, downstream process expectations, and — in some configurations — Salesforce-provided validation rules.

**Correct pattern:**

```
WRONG:
  CareProgramEnrollee e = new CareProgramEnrollee(
      CareProgramId = programId,
      AccountId = patientId,
      Status = 'Active'
  );
  insert e;

RIGHT:
  1. Insert CareProgramEnrollee with Status = 'Pending'
  2. Create AuthorizationFormConsent linked to the enrollee
  3. Update CareProgramEnrollee.Status = 'Active' after consent is confirmed
```

**Detection hint:** Any code that creates a `CareProgramEnrollee` with `Status = 'Active'` in the same statement as the initial insert, without referencing `AuthorizationFormConsent`, is bypassing the consent model.

---

## Anti-Pattern 6: Using Custom Fields on CareProgramEnrollee for Outcome Tracking Instead of the Dedicated Outcome Object

**What the LLM generates:** A data model using custom fields on `CareProgramEnrollee` (e.g., `OutcomeScore__c`, `ClinicalMetric__c`) to track patient outcomes within a program.

**Why it happens:** Custom fields are the path of least resistance and do not require any additional license verification. LLMs default to custom field solutions when the correct dedicated object (Patient Program Outcome Management) requires a license check that the LLM cannot perform.

**Correct pattern:**

```
WRONG: Add custom fields OutcomeScore__c, HbA1cValue__c to CareProgramEnrollee
RIGHT: Use PatientProgramOutcome (with the separately licensed permission set)
       for structured, reportable outcome tracking per enrollee.
       Custom fields on CareProgramEnrollee are appropriate only for simple
       flags or non-structured metadata, not clinical outcome data.
```

**Detection hint:** Any data model for "outcome tracking" within a care program that does not mention `PatientProgramOutcome` and only proposes custom fields on `CareProgramEnrollee` is likely incomplete or using the wrong approach.
