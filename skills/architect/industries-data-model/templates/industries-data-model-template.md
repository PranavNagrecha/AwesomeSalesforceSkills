# Industries Data Model — Work Template

Use this template when working on tasks involving Salesforce Industries cloud data models.

## Scope

**Skill:** `industries-data-model`

**Request summary:** (fill in what the user asked for)

**Target Industries cloud:** [ ] Insurance Cloud  [ ] Communications Cloud  [ ] Energy & Utilities Cloud  [ ] Health Cloud

## Context Gathered

- **Industries license confirmed in org:** (yes / no / unknown — check Setup > Installed Packages)
- **Person Accounts enabled (Insurance Cloud):** (yes / no — required for individual policyholder modeling)
- **Account record types in use (Communications Cloud):** (list DeveloperNames found in org)
- **Key business entities to model:** (list the domain objects the user needs)
- **Integration requirements:** (external systems, data direction, participant/holder fields needed)

## Object Mapping

Map business entities to standard Industries objects before considering custom objects:

| Business Entity | Standard Industries Object | Notes |
|---|---|---|
| Insurance Policy | InsurancePolicy | Top-level policy record |
| Coverage Line | InsurancePolicyCoverage | Child of InsurancePolicy |
| Policyholder / Beneficiary | InsurancePolicyParticipant → AccountId | NOT ContactId |
| Insured Item | InsurancePolicyAsset | Links Asset to InsurancePolicy |
| Policy Transaction | InsurancePolicyTransaction | Premium, endorsement, cancellation history |
| Billing Account (Comms) | Account with RecordType.DeveloperName = 'Billing_Account' | Record type, not separate object |
| Service Account (Comms) | Account with RecordType.DeveloperName = 'Service_Account' | Record type, not separate object |
| Patient Care Plan (Health) | CarePlan | Coordinating plan for patient treatment |
| Clinical Observation (Health) | CareObservation | Labs, vitals — NOT FHIR 'Observation' |
| Clinical Visit (Health) | ClinicalEncounter | NOT FHIR 'Encounter' |
| Diagnosis (Health) | HealthCondition | NOT FHIR 'Condition' |
| Metering Location (Energy) | ServicePoint | Physical delivery/metering location |
| Service Agreement (Energy) | ServiceContract | Customer-utility service agreement |

## SOQL Patterns

### Insurance Policy with Participants

```soql
SELECT
    Id,
    InsurancePolicyNumber,
    PolicyType,
    EffectiveDate,
    ExpirationDate,
    (
        SELECT Id, CoverageType, CoverageAmount FROM InsurancePolicyCoverages
    ),
    (
        SELECT Id, RoleInPolicy, AccountId, Account.Name
        FROM InsurancePolicyParticipants
        WHERE RoleInPolicy = 'Policyholder'
    )
FROM InsurancePolicy
WHERE Id = :policyId
```

### Communications Cloud Account Subtype Query

```soql
SELECT Id, Name, RecordType.DeveloperName
FROM Account
WHERE RecordType.DeveloperName = 'Billing_Account'
-- Use DeveloperName, not Name — DeveloperName is stable across environments
```

### Health Cloud CarePlan with Observations

```soql
SELECT
    Id,
    Name,
    Status,
    PatientId,
    (
        SELECT Id, ObservationCode, ObservationValue, ObservationDate
        FROM CareObservations
    )
FROM CarePlan
WHERE PatientId = :patientAccountId
AND Status = 'Active'
```

## Approach

Which pattern from SKILL.md applies and why:

(fill in)

## Review Checklist

- [ ] InsurancePolicyParticipant relationships use AccountId, not ContactId
- [ ] Communications Cloud Account queries include RecordType.DeveloperName filter
- [ ] No custom objects duplicate standard Industries objects (Policy__c, Coverage__c, CarePlan__c, etc.)
- [ ] Health Cloud SOQL uses Salesforce API names (CareObservation, HealthCondition, ClinicalEncounter)
- [ ] InsurancePolicyCoverage records always have a parent InsurancePolicyId
- [ ] RecordType.DeveloperName used for filtering (not RecordType.Name)
- [ ] Industries cloud license confirmed in target org
- [ ] checker script run: `python3 scripts/check_industries_data_model.py --manifest-dir <path>`

## Notes

(Record any deviations from the standard pattern and why.)
