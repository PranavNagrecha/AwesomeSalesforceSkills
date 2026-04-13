# LLM Anti-Patterns — Industries Data Model

Common mistakes AI coding assistants make when generating or advising on Industries Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Linking InsurancePolicyParticipant to Contact Instead of Account

**What the LLM generates:** SOQL or Apex that filters InsurancePolicyParticipant using a ContactId lookup, or inserts InsurancePolicyParticipant records with a Contact ID in what appears to be a participant relationship field.

**Why it happens:** LLMs are trained on large volumes of standard Sales Cloud patterns where people are represented as Contacts. The policyholder-as-Contact assumption is deeply embedded in general Salesforce training data. Insurance Cloud's decision to use Account for all participants is a deliberate divergence that is underrepresented in public training corpora.

**Correct pattern:**

```soql
-- WRONG
SELECT Id FROM InsurancePolicyParticipant WHERE ContactId = :contactId

-- CORRECT
SELECT Id, RoleInPolicy, Account.Name
FROM InsurancePolicyParticipant
WHERE AccountId = :accountId
AND RoleInPolicy = 'Policyholder'
```

**Detection hint:** Search generated SOQL or Apex for `ContactId` on any reference to `InsurancePolicyParticipant`. Any match is an error.

---

## Anti-Pattern 2: Querying Communications Account Subtypes Without a RecordType Filter

**What the LLM generates:** SOQL against the Account object in a Communications Cloud context that retrieves all accounts without filtering by RecordType.DeveloperName, often relying on the Name field or a custom field to distinguish account types.

**Why it happens:** LLMs recognize that Account is the correct object but do not consistently apply the Communications Cloud-specific record type filtering requirement. The pattern of using record types as subtypes of a standard object is not universally applied in LLM-generated queries.

**Correct pattern:**

```soql
-- WRONG — returns all account types mixed together
SELECT Id, Name FROM Account WHERE Name LIKE '%Billing%'

-- CORRECT — filter by RecordType.DeveloperName
SELECT Id, Name, RecordType.DeveloperName
FROM Account
WHERE RecordType.DeveloperName = 'Billing_Account'
```

**Detection hint:** Any Account query in a Communications Cloud context that lacks a `RecordType.DeveloperName` filter in the WHERE clause is suspect. Flag Account queries that rely on Name-based filtering or have no record type condition.

---

## Anti-Pattern 3: Using FHIR Resource Names as Salesforce Object API Names

**What the LLM generates:** SOQL using `Observation`, `Condition`, `Encounter`, or `Patient` as Salesforce object API names when working with Health Cloud data. The LLM correctly identifies the FHIR alignment but incorrectly uses the FHIR resource names as the Salesforce API names.

**Why it happens:** Health Cloud's FHIR R4 alignment is well-documented in public sources, which causes LLMs to associate the FHIR terminology with the Salesforce implementation. The actual Salesforce API names (CareObservation, HealthCondition, ClinicalEncounter) are Salesforce-specific and differ from FHIR resource names.

**Correct pattern:**

```soql
-- WRONG — FHIR resource names are not Salesforce object API names
SELECT Id FROM Observation WHERE PatientId = :patientId
SELECT Id FROM Condition WHERE Subject = :patientId

-- CORRECT — use Salesforce Health Cloud API names
SELECT Id, ObservationCode, ObservationValue FROM CareObservation WHERE PatientId = :patientId
SELECT Id, Code, ClinicalStatus FROM HealthCondition WHERE PatientId = :patientId
```

**Detection hint:** Check any Health Cloud query for use of raw FHIR resource names: `Observation`, `Condition`, `Encounter`, `Patient`, `Procedure`, `MedicationRequest`. Each needs translation to the Salesforce API name.

---

## Anti-Pattern 4: Creating Custom Objects That Duplicate Standard Industries Objects

**What the LLM generates:** Custom object schemas for `Policy__c`, `Coverage__c`, `CarePlan__c`, `ServiceLocation__c`, or similar, when the org already has the corresponding standard Industries objects (InsurancePolicy, InsurancePolicyCoverage, CarePlan, ServicePoint).

**Why it happens:** LLMs default to the custom object pattern when asked to model domain concepts without first checking whether standard Industries objects already exist. This reflects general Salesforce training data bias toward custom object solutions rather than Industries-specific object awareness.

**Correct pattern:**

```
-- WRONG — building redundant custom objects
Policy__c with Fields: PolicyNumber__c, EffectiveDate__c, ExpirationDate__c
Coverage__c with Fields: CoverageType__c, CoverageAmount__c, Policy__c (lookup)

-- CORRECT — use standard Industries objects
InsurancePolicy (standard) with standard fields: InsurancePolicyNumber, EffectiveDate, ExpirationDate
InsurancePolicyCoverage (standard) with standard fields: CoverageType, CoverageAmount, InsurancePolicyId
```

**Detection hint:** If generated output proposes custom objects named Policy, Coverage, CarePlan, ServicePoint, ServiceContract, or BillingAccount in an Industries org context, flag for review against the standard Industries object catalog.

---

## Anti-Pattern 5: Assuming Industries Objects Are Available in All Salesforce Editions

**What the LLM generates:** Code, SOQL, or metadata that uses InsurancePolicy, CarePlan, ServicePoint, or other Industries objects without noting that these require specific Industries cloud licenses and are not available in standard Salesforce editions, Developer Edition orgs, or unlicensed sandboxes.

**Why it happens:** LLMs treat all Salesforce standard objects as universally available in the same way core objects like Account, Contact, and Case are available. The license-gating of Industries objects is not consistently reflected in general Salesforce training data.

**Correct pattern:**

```
-- WRONG — deploying without license verification
Metadata package includes InsurancePolicy__layouts, InsurancePolicyParticipant__fields
No note about license requirement in deployment documentation

-- CORRECT — document license requirement and add environment check
Deployment guide notes: "Target org must have Insurance Cloud license provisioned."
Pre-deployment validation step: verify InsurancePolicy object is accessible via DescribeSObjectResult
```

**Detection hint:** If generated deployment instructions, metadata packages, or Apex classes reference Industries-specific objects without any mention of license prerequisites or environment validation, flag the output for review. Check that CI/CD pipeline documentation confirms the validation org has the required Industries license.

---

## Anti-Pattern 6: Using RecordType.Name Instead of RecordType.DeveloperName for Communications Account Filtering

**What the LLM generates:** SOQL that filters Account by `RecordType.Name = 'Billing Account'` instead of `RecordType.DeveloperName = 'Billing_Account'`.

**Why it happens:** `RecordType.Name` is the human-readable label that appears in Salesforce UI tooltips and documentation screenshots, making it the more visible field in training data. LLMs default to the display name rather than the API-stable DeveloperName.

**Correct pattern:**

```soql
-- WRONG — Name is admin-editable and can differ between environments
SELECT Id FROM Account WHERE RecordType.Name = 'Billing Account'

-- CORRECT — DeveloperName is stable across orgs and environments
SELECT Id FROM Account WHERE RecordType.DeveloperName = 'Billing_Account'
```

**Detection hint:** Scan Communications Cloud Account queries for `RecordType.Name` comparisons. Every instance should be changed to `RecordType.DeveloperName` to ensure environment stability.
