# FHIR Integration Patterns — Work Template

Use this template when building or reviewing FHIR R4 integration patterns for Health Cloud.

## Scope

**Skill:** `fhir-integration-patterns`

**Request summary:** (fill in what the user asked for)

## Integration Prerequisites

- [ ] FHIR R4 Support Settings enabled in Setup
- [ ] Source EHR FHIR version confirmed (R4 required)
- [ ] Org provisioning date verified (Spring '23+ = no HC24__ write access)
- [ ] Integration direction: [ ] Inbound [ ] Outbound [ ] Bidirectional

## FHIR Resource Mapping Summary

| FHIR Resource | Salesforce Object | Key Deviations | Middleware Transformation |
|--------------|-------------------|---------------|--------------------------|
| Patient | Person Account + PersonName + ContactPoint* | Demographics → child objects | Create Account first, then child records |
| Condition | HealthCondition | Code required in SF | Coding normalization |
| Observation | CareObservation + Component | | |
| (add rows) | | | |

## CDS Hooks Architecture (if applicable)

- CDS Hook service endpoint: MuleSoft API (NOT Salesforce directly)
- Hook types in scope: 
- Salesforce data queried: ClinicalAlert / CareGap / other
- MuleSoft → Salesforce query method: SOQL / FHIR Healthcare API

## Connected App Configuration

- OAuth scopes required: `api` + `healthcare`
- SMART on FHIR launch: [ ] Required [ ] Not required
- Experience Cloud portal access: [ ] FHIR R4 for Experience Cloud perm set needed

## Middleware Layer Requirements

| Integration Flow | Middleware | Transformation Type | Error Handling |
|-----------------|-----------|--------------------|-|
| EHR → Salesforce (inbound) | MuleSoft | FHIR complex type flattening | Retry + DLQ |
| Salesforce → EHR (outbound) | | | |

## Notes

(EHR vendor, FHIR capability statement limitations, specific resource mapping decisions, CodeableConcept truncation policy)
