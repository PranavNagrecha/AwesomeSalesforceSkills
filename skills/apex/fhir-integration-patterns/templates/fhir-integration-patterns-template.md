# FHIR Integration Patterns: Work Template

Use this template when building or reviewing FHIR R4 integration patterns for Health Cloud.

## Scope

**Skill:** `fhir-integration-patterns`

**Request summary:** (fill in what the user asked for)

## Integration Prerequisites

- [ ] FHIR R4 Support Settings: FHIR-Aligned Clinical Data Model org preference enabled
- [ ] Source EHR FHIR version confirmed (R4 required)
- [ ] No writes to packaged `HC24__Ehr...__c` objects that have standard counterparts (closed to new customers since Spring '23)
- [ ] Integration direction: [ ] Inbound [ ] Outbound [ ] Bidirectional

## FHIR Resource Mapping Summary

| FHIR Resource | Salesforce Object | Key Deviations | Middleware Transformation |
|--------------|-------------------|---------------|--------------------------|
| Patient | Person Account + PersonName + ContactPoint* | HumanName maps to PersonName; Address.line merged into one Street | Create Account first, then child records |
| Condition | HealthCondition + CodeSetBundle + CodeSet | `ConditionCodeId` required (1..1); max 15 codings; onsetAge/Range/String unsupported | Coding priority, truncation log |
| Observation | CareObservation + Component | | |
| (add rows) | | | |

## CDS Hooks Architecture (if applicable)

- CDS Hook service endpoint: MuleSoft API (NOT Salesforce directly)
- Hook types in scope: 
- Salesforce data queried: ClinicalAlert / CareGap / other
- MuleSoft to Salesforce query method: SOQL / Salesforce Healthcare API

## Client App Configuration

- Client app type: external client app with OAuth 2.0
- Healthcare API custom scopes per resource and method (for example `user_condition_read`, `system_all_write`); no wildcard SMART scopes
- Concurrency: five or fewer concurrent Healthcare API requests; Bundles at 30 entries or fewer (up to 10 reads or searches)
- Experience Cloud portal access: [ ] FHIR R4 for Experience Cloud Sites permission set needed

## Middleware Layer Requirements

| Integration Flow | Middleware | Transformation Type | Error Handling |
|-----------------|-----------|--------------------|-|
| EHR to Salesforce (inbound) | MuleSoft | FHIR complex type flattening | Retry + DLQ |
| Salesforce to EHR (outbound) | | | |

## Notes

(EHR vendor, FHIR capability statement limitations, specific resource mapping decisions, CodeableConcept truncation policy, code validation owner)

- [ ] `python3 scripts/check_fhir_integration_patterns.py --manifest-dir force-app/main/default` reviewed
