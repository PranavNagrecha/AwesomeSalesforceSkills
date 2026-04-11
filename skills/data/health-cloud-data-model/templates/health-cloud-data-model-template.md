# Health Cloud Data Model — Work Template

Use this template when selecting, enabling, or implementing Health Cloud clinical data objects for a new or existing integration.

## Scope

**Skill:** `health-cloud-data-model`

**Request summary:** (fill in what the user asked for — e.g., "Enable FHIR R4 clinical objects for patient portal" or "Migrate HC24__ encounters to standard objects")

---

## Context Gathered

Answer these before proceeding:

- **Org provisioning date:** (pre-Spring '23 or Spring '23+?)
- **FHIR-Aligned Clinical Data Model org preference:** (enabled / disabled / unknown — check Setup > FHIR R4 Support Settings)
- **HC24__ data present:** (yes — estimate volume / no / unknown)
- **Experience Cloud users involved:** (yes / no — if yes, FHIR R4 for Experience Cloud permission set required)
- **Integration source format:** (FHIR R4 REST / HL7 v2 / proprietary EHR / CSV)
- **Clinical objects in scope:** (list, e.g. ClinicalEncounter, HealthCondition, CarePlan)

---

## Object Layer Decision

Based on the context above:

**Recommended layer:** (FHIR R4-aligned standard objects / HC24__ read-only for historical data / both during migration window)

**Rationale:** (reference the decision table in SKILL.md — e.g., "Org is post-Spring '23, no prior HC24__ data, new FHIR R4 integration → standard objects only")

---

## Object and Field Mapping

| Source Field | Source Object/Resource | Target Salesforce Object | Target Field API Name |
|---|---|---|---|
| (e.g.) id | FHIR Encounter | ClinicalEncounter | EhrEncounterId__c (External ID) |
| (e.g.) subject.reference | FHIR Encounter | ClinicalEncounter | AccountId |
| (e.g.) period.start | FHIR Encounter | ClinicalEncounter | StartTime |
| (e.g.) period.end | FHIR Encounter | ClinicalEncounter | EndTime |
| (e.g.) status | FHIR Encounter | ClinicalEncounter | Status |
| ... | ... | ... | ... |

---

## Setup Checklist

- [ ] Confirm FHIR-Aligned Clinical Data Model org preference is ON in Setup > FHIR R4 Support Settings
- [ ] Verify standard clinical objects are available: `SELECT Id FROM ClinicalEncounter LIMIT 1` returns without error
- [ ] Create External ID fields on each target standard object (e.g., `EhrEncounterId__c` on ClinicalEncounter)
- [ ] Assign Health Cloud permission sets to integration user
- [ ] If Experience Cloud is involved: assign "FHIR R4 for Experience Cloud" permission set to community users
- [ ] Validate sharing rules allow the integration user to read/write the target objects

---

## Migration Plan (if applicable)

Only fill in if migrating from HC24__ to standard objects:

- **HC24__ objects to migrate:** (list)
- **Estimated record volumes per object:** (fill in from SOQL COUNT queries)
- **Migration method:** (Bulk API 2.0 / Data Loader / custom Apex)
- **Migration window:** (date range during which both layers must be queried)
- **Rollback plan:** (HC24__ read access remains; re-query from source EHR if needed)

---

## Review Checklist

Copy from SKILL.md and tick as complete:

- [ ] FHIR-Aligned Clinical Data Model org preference is enabled in Setup
- [ ] No new DML operations target HC24__ objects where a standard counterpart exists
- [ ] All standard clinical objects referenced in code or config exist in the target org's schema
- [ ] Experience Cloud users (if any) have the FHIR R4 for Experience Cloud permission set assigned
- [ ] External ID fields are used for upsert operations to support idempotent re-ingestion
- [ ] Relationship fields (e.g., ClinicalEncounterId) are populated on child clinical objects
- [ ] SOQL queries have been tested against the target org to confirm object availability

---

## Notes

(Record any deviations from the standard pattern and why — e.g., "HC24__ read queries retained for historical reporting until Q3 migration completes")
