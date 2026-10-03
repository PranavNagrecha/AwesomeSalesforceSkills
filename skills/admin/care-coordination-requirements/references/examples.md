# Examples: Care Coordination Requirements

## Example 1: Mapping SDOH Barrier Tracking for a Community Health Worker Program

**Context:** A federally qualified health center implements Health Cloud for community health workers (CHWs) who run social needs screenings and connect patients to community resources.

**Problem:** The team designed a custom `SocialBarrier__c` object for SDOH findings, not knowing that Health Cloud has a native social determinants model (`CareBarrier`, `CareBarrierType`, `CareDeterminant`, `CareDeterminantType`, `CareInterventionType`).

**Solution:**
1. Confirm the Health Cloud managed package is installed and CHWs hold the Health Cloud permission set licenses and the Health Cloud Social Determinants permission sets. The social determinants objects are invisible without them.
2. Define a `CareBarrierType` for each barrier category in scope (food insecurity, housing instability, transportation, social isolation, utilities) and a `CareDeterminantType` for each determinant domain.
3. Design the screening assessment so a positive answer records a `CareBarrier` with the patient (`PatientId`), the barrier type, a `Priority`, and the `SurveyResponseId` of the screening.
4. Create a Case only when a community resource referral must be tracked; set `CareBarrier.CaseId` to it.
5. Generate intervention tasks on the Case with an Action Plan (template in `metadata-examples.md`).
6. Set the barrier to `Addressed` when the intervention is complete, and report barrier resolution by type for population health.
7. Insert and update one barrier in a sandbox with a CHW user before sign-off, because the guide's supported-calls list for `CareBarrier` omits `create()`.

**Why it works:** Native barrier objects come with history, sharing, and change events (`CareBarrierHistory`, `CareBarrierShare`, `CareBarrierChangeEvent`) that a custom object would need to rebuild.

---

## Example 2: Sourcing and Closing Care Gaps for a Quality Improvement Program

**Context:** A health plan wants care coordinators to see open quality gaps (overdue screenings, missing vaccinations) and prioritize outreach.

**Problem:** The first requirements draft said coordinators could never create gaps, and that a "Close Gap" button would set `Status` to `Closed`. Both are wrong. `CareGap` supports `create()`, records its origin in `RecordOriginType` (`Calculated`, `Imported`, `ManuallyCreated`), and `Status` is not writable.

**Solution:**
1. Classify every gap source: measure evaluation in Salesforce (`Calculated`), the plan's quality analytics system (`Imported`), and coordinator chart review (`ManuallyCreated`, with a supervisor-approved policy).
2. Load imported gaps with upsert on the source identifier, setting `SourceSystem`, `SourceSystemIdentifier`, and the reporting period.
3. Close or exclude gaps by changing `MeasureEvaluationStatus` to `ManuallyClosed` or `ManuallyExcluded`, with a required `StatusReason`.
4. Build the coordinator's worklist from open gaps by measure.

A coordinator worklist query:

```sql
SELECT Id, Name, AccountId, ClinicalMeasure.Name, TargetResolutionDate,
       MeasureEvaluationStatus, RecordOriginType, SourceSystem
FROM CareGap
WHERE Status = 'Open'
  AND ReportingPeriodEndDate >= TODAY
ORDER BY TargetResolutionDate ASC NULLS LAST
LIMIT 200
```

An imported gap as a REST upsert body (`PATCH /services/data/v67.0/sobjects/CareGap/SourceSystemIdentifier/QM-2026-000481`):

```json
{
  "Name": "Colorectal cancer screening overdue",
  "AccountId": "001xx000003DGb2AAG",
  "ClinicalMeasureId": "0zXxx0000004CqWEAU",
  "RecordOriginType": "Imported",
  "SourceSystem": "PlanQualityHub",
  "ReportingPeriodStartDate": "2026-01-01",
  "ReportingPeriodEndDate": "2026-12-31",
  "TargetResolutionDate": "2026-11-30"
}
```

UNVERIFIED (2026-10-03): `SourceSystemIdentifier` is shown here as the upsert key. The guide lists it as a filterable string field but does not state that it is an external ID; if it is not, query by it and update by `Id` instead.

**Why it works:** Every gap carries its origin and source, so coordinators can tell a calculated gap from a payer import, and closures leave a reason instead of a silent status edit.

---

## Anti-Pattern: Treating `CareBarrier` and a Care Plan Problem as Interchangeable

**What practitioners do:** Record "Transportation barrier" as a care plan problem, or record "Uncontrolled hypertension" as a `CareBarrier`, because both are "problems the care team addresses". Some designs reference a `CarePlanProblem` object that does not exist as a standard object.

**What goes wrong:** Care plan problems are `HealthCondition` records instantiated from `ProblemDefinition` records in the PGI library, with goals and interventions beneath them. Social barriers have their own lifecycle (`Open`, `Addressed`), types, and determinants. Mixing them pollutes the clinical plan and breaks SDOH reporting.

**Correct approach:** `CareBarrier` for social determinants and community interventions; `HealthCondition` (from `ProblemDefinition`) for clinical problems in a care plan. Link a barrier to a related gap with `CareGap.CareBarrierId` when one causes the other.
