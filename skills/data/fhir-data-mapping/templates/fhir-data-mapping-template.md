# FHIR Data Mapping — Work Template

Use this template when working on a FHIR-to-Health-Cloud data mapping task.

## Scope

**Skill:** `fhir-data-mapping`

**Request summary:** (fill in what the user asked for — e.g., "Map FHIR Patient and Condition resources from Epic EHR to Health Cloud for initial migration")

---

## Prerequisites Confirmed

Before beginning any mapping or load work, confirm the following:

- [ ] **FHIR-Aligned Clinical Data Model org preference enabled:** Setup > FHIR R4 Support Settings > FHIR-Aligned Clinical Data Model = ON
  - Verified by: (name / date)
- [ ] **Clinical SObjects visible in schema:** HealthCondition, CareObservation, PersonName, ContactPointPhone, ContactPointAddress all present in Object Manager
- [ ] **Target org type:** (Production / Full Sandbox / Developer Sandbox)
- [ ] **ExternalId fields defined** on all clinical objects for idempotent upsert:
  - HealthCondition: ExternalId field name: ______________
  - CareObservation: ExternalId field name: ______________
  - CarePlan: ExternalId field name: ______________
  - PersonName: ExternalId field name: ______________

---

## FHIR Resource Inventory

List all FHIR resource types present in the source bundle:

| FHIR Resource Type | Count | Has condition.code? | Max codings per CodeableConcept | Notes |
|---|---|---|---|---|
| Patient | | N/A | N/A | |
| Condition | | Yes / No / Mixed | | Flag code-less records |
| Observation | | N/A | | Check component count |
| CarePlan | | N/A | N/A | List careTeam member types |
| (other) | | | | |

**Code-less Condition count:** ______________ (these must be quarantined, not loaded)

**Max codings found on any single CodeableConcept:** ______________ (if > 15, truncation required)

---

## Field Mapping Table

Complete a row for each FHIR element being mapped. Add rows as needed.

### Patient → Person Account + Child Records

| FHIR Element | Cardinality | Salesforce Object | Salesforce Field | Notes |
|---|---|---|---|---|
| Patient.id | 1..1 | Account | ExternalId__c | Use as upsert key |
| Patient.name[].given | 0..* | PersonName | GivenName | Create one PersonName per name entry |
| Patient.name[].family | 0..1 | PersonName | FamilyName | |
| Patient.name[].use | 0..1 | PersonName | NameUse | Map: official→Official, nickname→Nickname |
| Patient.telecom[system=phone].value | 0..* | ContactPointPhone | TelephoneNumber | |
| Patient.telecom[system=phone].use | 0..1 | ContactPointPhone | AddressType | Map: home→Home, work→Work, mobile→Mobile |
| Patient.address[].line | 0..* | ContactPointAddress | Street | Join multiple lines with space |
| Patient.address[].city | 0..1 | ContactPointAddress | City | |
| Patient.address[].state | 0..1 | ContactPointAddress | StateCode | |
| Patient.address[].postalCode | 0..1 | ContactPointAddress | PostalCode | |
| Patient.address[].country | 0..1 | ContactPointAddress | CountryCode | ISO 3166 2-char code |
| Patient.address[].use | 0..1 | ContactPointAddress | AddressType | |

### Condition → HealthCondition

| FHIR Element | Cardinality (FHIR) | Cardinality (HC) | Salesforce Object | Salesforce Field | Notes |
|---|---|---|---|---|---|
| Condition.id | 1..1 | 1..1 | HealthCondition | ExternalId__c | Upsert key |
| Condition.code | 0..1 | **1..1** | HealthCondition | Code | **REQUIRED in HC — quarantine if absent** |
| Condition.subject (Patient ref) | 1..1 | 1..1 | HealthCondition | PatientId | Resolve to Person Account Id |
| Condition.clinicalStatus | 0..1 | 0..1 | HealthCondition | ClinicalStatus | |
| Condition.verificationStatus | 0..1 | 0..1 | HealthCondition | VerificationStatus | |
| Condition.onsetDateTime | 0..1 | 0..1 | HealthCondition | OnsetDate | |

### Observation → CareObservation + CareObservationComponent

| FHIR Element | Salesforce Object | Salesforce Field | Notes |
|---|---|---|---|
| Observation.id | CareObservation | ExternalId__c | Upsert key |
| Observation.code | CareObservation | Code | CodeSetBundle lookup |
| Observation.subject | CareObservation | PatientId | Person Account Id |
| Observation.effectiveDateTime | CareObservation | ObservationDate | |
| Observation.component[n].code | CareObservationComponent | Code | One child record per component |
| Observation.component[n].value | CareObservationComponent | Value | |

### CarePlan → CarePlan + CarePlanDetail + CarePlanActivity

| FHIR Element | Salesforce Object | Salesforce Field | Notes |
|---|---|---|---|
| CarePlan.id | CarePlan | ExternalId__c | Upsert key |
| CarePlan.subject | CarePlan | PatientId | Person Account Id |
| CarePlan.status | CarePlan | Status | Map FHIR status codes to HC picklist values |
| CarePlan.activity[n] | CarePlanActivity | — | One CarePlanActivity per activity element |
| CarePlan.careTeam | CaseTeamMember | MemberId | Add to parent Case's Case Team; NOT a CarePlan field |

### CodeableConcept → CodeSetBundle

| FHIR Element | Salesforce Object | Salesforce Field | Notes |
|---|---|---|---|
| coding[n].system | CodeSet | CodeSetName / System | Lookup or create CodeSet record per coding |
| coding[n].code | CodeSet | Code | |
| coding[n].display | CodeSet | Display | |
| (up to 15 codings) | CodeSetBundle | CodeSet1Id–CodeSet15Id | Truncate to top 15 by priority; audit discards |

---

## CodeableConcept Truncation Log

If any CodeableConcept in the source bundle has more than 15 codings, document the truncation decisions here:

**Priority order applied:**
1. SNOMED CT (`http://snomed.info/sct`)
2. LOINC (`http://loinc.org`)
3. ICD-10-CM (`http://hl7.org/fhir/sid/icd-10-cm`)
4. CPT (`http://www.ama-assn.org/go/cpt`)
5. Local/regional codes

**Audit log file location:** ______________ (attach or link the CSV produced by middleware)

**Clinical stakeholder who reviewed discards:** ______________ / Date: ______________

---

## Quarantine List

Conditions and other resources that could not be loaded due to missing required data:

| FHIR Resource Id | Resource Type | Reason for Quarantine | Clinical Owner | Resolution Status |
|---|---|---|---|---|
| | Condition | Missing condition.code | | Pending |
| | | | | |

---

## careTeam Resolution

For each CarePlan with a careTeam reference, document how team members were resolved:

**Parent Case Id:** ______________

| FHIR CareTeam Participant | FHIR Practitioner Id | Resolved to Salesforce User/Contact Id | Case Team Role | Added to Case Team? |
|---|---|---|---|---|
| | | | | Yes / No |
| | | | | Yes / No |

---

## Load Sequence Executed

Record the actual load order and outcomes:

| Step | Object | Load Method | Records Attempted | Records Succeeded | Records Failed | Notes |
|---|---|---|---|---|---|---|
| 1 | CodeSet | Bulk API 2.0 Upsert | | | | |
| 2 | CodeSetBundle | Bulk API 2.0 Upsert | | | | |
| 3 | Account (Person) | Bulk API 2.0 Upsert | | | | |
| 4 | PersonName | Bulk API 2.0 Upsert | | | | |
| 5 | ContactPointPhone | Bulk API 2.0 Upsert | | | | |
| 6 | ContactPointAddress | Bulk API 2.0 Upsert | | | | |
| 7 | HealthCondition | Bulk API 2.0 Upsert | | | | |
| 8 | CareObservation | Bulk API 2.0 Upsert | | | | |
| 9 | CareObservationComponent | Bulk API 2.0 Upsert | | | | |
| 10 | CarePlan | Bulk API 2.0 Upsert | | | | |
| 11 | CarePlanActivity | Bulk API 2.0 Upsert | | | | |
| 12 | CaseTeamMember (careTeam) | SOAP/REST API | | | | |

---

## Post-Load Validation

Spot-check queries to run after load:

```soql
-- Confirm all HealthCondition records have a Code
SELECT COUNT() FROM HealthCondition WHERE Code = null

-- Confirm PersonName records are linked to Person Accounts
SELECT COUNT() FROM PersonName WHERE ParentId = null

-- Confirm CareObservationComponent records have a parent
SELECT COUNT() FROM CareObservationComponent WHERE CareObservationId = null

-- Confirm Case Team members exist on Cases related to loaded CarePlans
SELECT ParentId, COUNT(Id) teamMembers FROM CaseTeamMember
WHERE ParentId IN (SELECT CaseId FROM CarePlan WHERE ExternalId__c != null)
GROUP BY ParentId
```

**Validation passed:** Yes / No — Date: ______________

---

## Checklist

- [ ] FHIR-Aligned Clinical Data Model org preference confirmed enabled
- [ ] All HealthCondition records have a non-null Code lookup
- [ ] No FHIR patient demographics written to Account or Contact fields directly
- [ ] CodeSetBundle records have no more than 15 CodeSet references; truncation audit log produced
- [ ] CarePlan careTeam members resolved to Case Team members on parent Case
- [ ] CareObservationComponent records linked to correct CareObservation parent
- [ ] Quarantined resources documented and reviewed by clinical stakeholder
- [ ] Post-load validation queries run and passed

---

## Deviations and Notes

Document any deviations from the standard pattern and the reason for each:

| Item | Standard Pattern | Deviation | Reason |
|---|---|---|---|
| | | | |
