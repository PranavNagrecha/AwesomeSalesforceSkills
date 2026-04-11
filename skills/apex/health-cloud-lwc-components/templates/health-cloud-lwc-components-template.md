# Health Cloud LWC Components — Work Template

Use this template when building or reviewing custom LWC components for Health Cloud.

## Scope

**Skill:** `health-cloud-lwc-components`

**Request summary:** (fill in what the user asked for)

## Component Type Classification

| Component Need | Implementation Path |
|---------------|---------------------|
| Add fields to Patient Card | Health Cloud Setup > Patient Card Configuration |
| Add object to Industries Timeline | TimelineObjectDefinition metadata |
| Display clinical data in new LWC | Custom LWC + Apex controller querying clinical objects |
| Care plan visualization | Custom LWC + Apex querying CarePlan hierarchy |

**Component type for this work:** _______________

## Clinical Data Source Mapping

| Data Needed | Clinical Object | Account Lookup Field | Apex Query |
|------------|----------------|---------------------|------------|
| Patient conditions | HealthCondition | PatientId | WHERE PatientId = :accountId |
| Patient medications | PatientMedication | PatientId | WHERE PatientId = :accountId |
| Clinical encounters | ClinicalEncounter | PatientId | WHERE PatientId = :accountId |
| (add rows) | | | |

## Apex Controller Checklist

- [ ] `@AuraEnabled(cacheable=true)` for read-only queries
- [ ] `WITH SECURITY_ENFORCED` on all clinical object SOQL queries
- [ ] Null checks on results before returning to LWC
- [ ] Account ID parameter validated before use in query

## Timeline Configuration Checklist (if applicable)

- [ ] Timeline component confirmed as Industries Timeline (not legacy HC package)
- [ ] Custom object has Account lookup field
- [ ] TimelineObjectDefinition metadata created with correct baseObject and dateField
- [ ] Metadata deployed and timeline entry visible on test patient record

## Security Review

- [ ] Apex controller enforces FLS for all clinical fields
- [ ] No debug log levels that would expose clinical data in production
- [ ] Component does not cache PHI in browser storage (localStorage, sessionStorage)

## Notes

(Timeline vs. legacy component determination, patient card configuration path, clinical object query results)
