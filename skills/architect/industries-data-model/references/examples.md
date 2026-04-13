# Examples — Industries Data Model

## Example 1: Querying an InsurancePolicy with Coverage Lines and Policyholder Account

**Context:** An Insurance Cloud integration needs to retrieve a complete policy record — the policy itself, all coverage lines, and the identity of the policyholder — to send to an external policy administration system.

**Problem:** Developers familiar with Sales Cloud write the participant join against Contact. The query returns zero participant rows because InsurancePolicyParticipant links to Account, not Contact.

**Solution:**

```soql
SELECT
    Id,
    InsurancePolicyNumber,
    PolicyType,
    EffectiveDate,
    ExpirationDate,
    Status,
    (
        SELECT
            Id,
            CoverageType,
            CoverageAmount,
            Deductible,
            LimitAmount
        FROM InsurancePolicyCoverages
    ),
    (
        SELECT
            Id,
            RoleInPolicy,
            AccountId,
            Account.Name,
            Account.BillingStreet,
            Account.BillingCity,
            Account.BillingState,
            Account.BillingPostalCode
        FROM InsurancePolicyParticipants
        WHERE RoleInPolicy = 'Policyholder'
    )
FROM InsurancePolicy
WHERE Id = :policyId
```

**Why it works:** The subquery relationship name `InsurancePolicyParticipants` traverses the master-detail from InsurancePolicy to InsurancePolicyParticipant. The participant lookup is `AccountId` on the InsurancePolicyParticipant object. Filtering `RoleInPolicy = 'Policyholder'` isolates the primary holder from beneficiaries and named insureds. Account address fields are retrieved via the relationship rather than requiring a second query.

---

## Example 2: Querying Communications Cloud Accounts by Record Type Subtype

**Context:** A Communications Cloud org has Business, Consumer, Billing, and Service accounts all stored as standard Account records. A billing report page needs to retrieve only Billing_Account records.

**Problem:** Without a RecordType filter, the query returns all Account record types. The report page displays consumer accounts, business accounts, and service accounts mixed into the billing report, producing incorrect totals and broken UI logic.

**Solution:**

```soql
-- Retrieve only billing accounts
SELECT
    Id,
    Name,
    RecordType.DeveloperName,
    BillingStreet,
    BillingCity,
    BillingState,
    BillingPostalCode,
    Phone
FROM Account
WHERE RecordType.DeveloperName = 'Billing_Account'
ORDER BY Name

-- Retrieve all Communications Cloud account subtypes with type label
SELECT
    Id,
    Name,
    RecordType.DeveloperName,
    RecordType.Name
FROM Account
WHERE RecordType.DeveloperName IN (
    'Business_Account',
    'Consumer_Account',
    'Billing_Account',
    'Service_Account'
)
```

**Why it works:** All four Communications Cloud account subtypes are stored on the standard Account object differentiated only by RecordType. The `RecordType.DeveloperName` field is a reliable filter because DeveloperName is stable across sandbox and production environments, unlike `RecordType.Name` which can be renamed by admins. The `IN` clause variant is useful for pages that need to display all subtype counts together.

---

## Example 3: Querying Health Cloud CarePlan with Related Observations

**Context:** A Health Cloud care coordination page needs to display a patient's active care plan alongside recent clinical observations.

**Problem:** A developer uses FHIR resource name `Observation` as the Salesforce object API name in SOQL. The query fails with "sObject type 'Observation' is not supported."

**Solution:**

```soql
-- Query active care plans for a patient
SELECT
    Id,
    Name,
    Status,
    StartDate,
    EndDate,
    PatientId,
    Patient.Name,
    (
        SELECT
            Id,
            ObservationCode,
            ObservationValue,
            ObservationDate,
            Status
        FROM CareObservations
    )
FROM CarePlan
WHERE PatientId = :patientAccountId
AND Status = 'Active'
ORDER BY StartDate DESC
```

**Why it works:** The Salesforce Health Cloud object API name is `CarePlan` (not the FHIR `CarePlan` resource directly), and the child object is `CareObservation` (not the FHIR `Observation` resource). The relationship name for the subquery is `CareObservations`. The patient is referenced via `PatientId` which is a lookup to Account, consistent with the broader Industries pattern of using Account rather than Contact for the primary entity.

---

## Anti-Pattern: Linking InsurancePolicyParticipant to ContactId

**What practitioners do:** Write Apex or SOQL that assumes the policyholder on an InsurancePolicyParticipant is a Contact, matching the Sales Cloud pattern where people are Contacts.

**What goes wrong:** `InsurancePolicyParticipant` has an `AccountId` field and no `ContactId` field. Any Apex that assigns a Contact ID to a participant record's lookup field will fail with an invalid field error. SOQL filtering on `ContactId` returns zero rows and silently excludes all participants from results.

**Correct approach:** Always use `AccountId` on `InsurancePolicyParticipant`. In Insurance Cloud, individual policyholders are represented as Person Account records (Account records with IsPersonAccount = true) or standard Business Account records for commercial policies. The Contact-centric model does not apply to Insurance Cloud participant relationships.

```soql
-- WRONG — ContactId does not exist on InsurancePolicyParticipant
SELECT Id FROM InsurancePolicyParticipant WHERE ContactId = :contactId

-- CORRECT — use AccountId
SELECT Id, RoleInPolicy FROM InsurancePolicyParticipant WHERE AccountId = :accountId
```
