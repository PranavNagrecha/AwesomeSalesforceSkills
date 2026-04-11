# Clinical Data Requirements — Work Template

Use this template when defining clinical data model requirements for Health Cloud.

## Scope

**Skill:** `clinical-data-requirements`

**Request summary:** (fill in what the user asked for)

## Prerequisites

- [ ] FHIR R4 Support Settings enabled in Setup (FHIR-Aligned Clinical Data Model)
- [ ] FHIR R4 for Experience Cloud enabled (if portal access to clinical data needed)
- [ ] Org provisioning date confirmed (new = Spring '23+; legacy = pre-Spring '23)

## Source System Clinical Data Inventory

| Source System | Data Standard | FHIR Resources / HL7 Message Types | Notes |
|--------------|--------------|-----------------------------------|-------|
| | FHIR R4 / HL7 v2 | | |

## FHIR Resource to Salesforce Object Mapping

| FHIR Resource | Salesforce Object | Key Mapping Notes | Deviations from Spec |
|--------------|-------------------|------------------|---------------------|
| Patient | Person Account + PersonName + ContactPoint* | Demographics → child objects | Direct Account fields do NOT work |
| Condition | HealthCondition | Code required in SF; optional in FHIR | |
| Observation | CareObservation + CareObservationComponent | | |
| (add rows) | | | |

## CodeableConcept Constraint Assessment

| Resource | Field | Max Codings in Source | Truncation Policy |
|---------|-------|----------------------|-------------------|
| Condition | code | | ICD-10 priority 1, SNOMED priority 2 |
| Observation | code | | LOINC priority 1 |

## Legacy EHR Object Migration Assessment

| Legacy Object (HC24__) | Replacement Object | Data Volume | Migration Required? |
|-----------------------|-------------------|-------------|---------------------|
| HC24__EhrCondition__c | HealthCondition | | |
| HC24__EhrMedication__c | PatientMedication | | |

## Middleware Translation Requirements

| Source Format | Target Format | Translation Tool | Responsible Team |
|--------------|--------------|-----------------|-----------------|
| FHIR R4 bundle | FHIR R4 (Salesforce-normalized) | | |
| HL7 v2 ADT/ORU | FHIR R4 | | |

## Notes

(Custom coding system priorities, org edition, specific FHIR resource deviations requiring middleware logic)
