# Care Coordination Requirements — Work Template

Use this template when gathering and mapping care coordination process requirements for Health Cloud ICM.

## Scope

**Skill:** `care-coordination-requirements`

**Request summary:** (fill in what the user asked for)

## ICM Prerequisites Verified

- [ ] FHIR R4-Aligned Data Model setting enabled (Setup > FHIR R4 Support Settings)
- [ ] Enhanced Care Plans setting enabled (Setup > Integrated Care Management Settings)
- [ ] Health Cloud permission set licenses and Health Cloud Social Determinants permission sets assigned
- [ ] Care Coordination for Slack license confirmed (if Slack workflows in scope)

## Care Coordination Scenario Mapping

| Scenario | ICM Object Family | Objects Used |
|----------|------------------|--------------|
| SDOH barrier identification | SDOH | CareDeterminant, CareBarrier, CareBarrierType |
| Referral to specialist | Referrals | ClinicalServiceRequest |
| Preventive care quality gaps | Care Gaps | CareGap (origin: Calculated, Imported, or ManuallyCreated) |
| Episode of care management | Care Episodes | CareEpisode |

## SDOH Barrier Taxonomy

| CareDeterminant | CareBarrierType Values |
|----------------|------------------------|
| Food Security | |
| Housing | |
| Transportation | |
| (add as needed) | |

## Care Gap Integration Requirements

| Source System | Integration Method | Ingestion Frequency |
|--------------|-------------------|---------------------|
| | FHIR R4 API / Direct API | |

Note: CareGap supports create, update, and upsert. Record each gap's origin in RecordOriginType, and close or exclude gaps through MeasureEvaluationStatus with a StatusReason; Status itself is not writable.

## Transition of Care Handoff Design

| Handoff Scenario | From Role | To Role | Objects Created |
|-----------------|-----------|---------|-----------------|
| | | | ClinicalServiceRequest + CareEpisode |

## Notes

(Record any custom object requirements, deviations from standard ICM patterns, or licensing decisions)
