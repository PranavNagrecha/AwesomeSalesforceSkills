# Clinical Decision Support — Work Template

Use this template when implementing clinical decision support in Health Cloud.

## Scope

**Skill:** `clinical-decision-support`

**Request summary:** (fill in what the user asked for)

## CDS Alert Type Inventory

| Alert Type | Source Event | Creation Mechanism | Target Object |
|-----------|-------------|-------------------|---------------|
| Lab threshold alert | CareObservation insert/update | Apex trigger | ClinicalAlert |
| Care gap (quality measure) | External payer quality system | FHIR API ingestion | CareGap |
| Protocol deviation | HealthCondition + CareObservation | Apex/BRE | ClinicalAlert |
| (add rows) | | | |

## ClinicalAlert Creation Checklist (for each alert type)

- [ ] Trigger event defined (which clinical object change fires the alert)
- [ ] Clinical logic condition documented (threshold, rule criteria)
- [ ] Apex trigger written with bulkification (collect → evaluate → bulk insert)
- [ ] HealthCloudICM permission set on trigger/DML executing user
- [ ] Alert tested with real clinical data thresholds

## CareGap Ingestion Checklist

- [ ] External quality analytics system identified
- [ ] FHIR R4 CareGap resource mapping defined
- [ ] MuleSoft (or equivalent) integration designed
- [ ] Ingestion schedule defined (nightly recommended)
- [ ] Deduplication logic designed (avoid duplicate gap records)
- [ ] CareGap closure sync designed (mark gaps closed when quality system confirms)

## Business Rules Engine (if licensed)

- [ ] BRE license confirmed in contract
- [ ] Rule definitions documented for each clinical protocol
- [ ] BRE rule testing with representative clinical data

## Alert Display Configuration

- Alert display method: [ ] FlexCard [ ] Custom LWC [ ] Built-in HC component
- Alert acknowledgment workflow: 

## Notes

(Clinical thresholds, external quality system details, BRE licensing status, CDS Hooks requirements)
