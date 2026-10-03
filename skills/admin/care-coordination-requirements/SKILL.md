---
name: care-coordination-requirements
description: "Use this skill when mapping care coordination process requirements for Health Cloud: designing care team workflows, transition of care handoffs, social determinants of health (SDOH) barrier tracking, and care gap identification. NOT for building care plan templates, problems, and goals — use admin/care-plan-configuration. NOT for referral routing and provider networks — use admin/referral-management-health."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "How do I map care coordination workflows for transition of care in Health Cloud?"
  - "What objects support SDOH barrier tracking and care gap detection in Health Cloud Integrated Care Management?"
  - "How does care coordination for Slack work and what are the prerequisites?"
  - "What are the ICM object families for care coordination process design in Salesforce?"
  - "Difference between CareBarrier and CarePlanProblem for SDOH vs care plan workflows"
  - "design a hospital discharge handoff to outpatient care coordinators in Health Cloud"
  - "decide whether care gaps should be calculated, imported, or entered by coordinators"
tags:
  - health-cloud
  - care-coordination
  - integrated-care-management
  - sdoh
  - care-gap
  - care-episode
  - transition-of-care
inputs:
  - Health Cloud org with Integrated Care Management (ICM) enabled
  - Documented care coordination process requirements (care team roles, handoff triggers, SDOH categories)
  - Health Cloud permission set licenses and permission sets assigned to coordinators
outputs:
  - ICM object family mapping to care coordination process requirements
  - SDOH barrier tracking design using CareDeterminant/CareBarrier objects
  - Care gap detection requirements aligned to CareGap object constraints
  - Transition of care handoff workflow design
dependencies:
  - admin/health-cloud-patient-setup
  - admin/care-plan-configuration
  - admin/care-program-management
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Care Coordination Requirements

Use this skill when mapping care coordination process requirements for Health Cloud Integrated Care Management (ICM): care team workflows, transition of care handoffs, SDOH barrier tracking, and care gap identification. This skill covers requirements gathering and process-to-object mapping. It does NOT cover building individual components; for Apex, Flow, or configuration build steps, use the implementation skills listed at the end.

Licence gate: every object named here is a Health Cloud object. The developer guide titles itself "Agentforce Health Developer Guide" in Summer '26; the social determinants objects additionally require the Health Cloud managed package and its permission sets.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the ICM data model is enabled. The Health Cloud developer guide says: "go to Setup and enable the FHIR R4-Aligned Data Model setting on the FHIR R4 Support Settings page and the Enhanced Care Plans setting on the Integrated Care Management Settings page." UNVERIFIED (2026-10-03): earlier versions of this skill described two other checkboxes ("Managing Care Plans" and "Calculating Care Gaps"); those labels are not in the guide.
- Identify which coordination scenarios are in scope: SDOH barriers, referrals, care gaps, care episodes. Each maps to a different object family.
- Confirm permission set licenses and permission sets for coordinators. The social determinants objects "are visible to users with the Health Cloud and the Health Cloud Platform permission set licenses and the Health Cloud Permission Set License and Health Cloud Social Determinants permission sets." UNVERIFIED (2026-10-03): a permission set named `HealthCloudICM`, cited by earlier versions of this skill, is not named in the guide.
- If Slack-based coordination is in scope, the org setting is `IndustriesSettings.enableCareMgmtSlackAccess` ("Care Coordination for Slack app", API 56.0). UNVERIFIED (2026-10-03): that the app is a separately purchased add-on is a commercial claim not stated in the guides read.

---

## Questions to Ask Before Configuring

Ask these before mapping a single object. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Where do care gaps come from: calculated from clinical measures, imported from a payer system, or opened by a coordinator?" | `CareGap.RecordOriginType` distinguishes `Calculated`, `Imported`, and `ManuallyCreated` (gotcha 1) | The origin per gap source and who owns each | Gap lists a coordinator can trust, with the source system recorded on every record |
| "Who can close or exclude a gap, and what reason must they record?" | `CareGap.Status` is not writable; closure runs through `MeasureEvaluationStatus` and `StatusReason` (gotcha 2) | A closure and exclusion policy with required reasons | An auditable gap lifecycle instead of edits that fail or vanish |
| "Is the barrier always tied to a Case, or sometimes just to the patient?" | `CareBarrier.CaseId` is optional; the patient lookup is not (gotcha 4) | The rule for when a Case is created | Barriers that appear in the right views without forcing empty Cases |
| "Will barriers be written by screening automation or an integration?" | The guide's CareBarrier supported-calls list omits `create()` (gotcha 5) | A sandbox insert test planned before design sign-off | No late redesign of the screening flow |
| "Do referrals and episodes need the FHIR-aligned objects?" | `ClinicalServiceRequest` needs the FHIR-Aligned Clinical Data Model org pref (gotcha 6) | The org preferences to enable, in order | Objects that exist when the build starts |
| "Is Slack part of the care team's working day?" | Care Coordination for Slack is a separate org setting (gotcha 7) | The Slack decision and its prerequisites | No Slack-dependent workflow designed into an org where the app is off |

What a proper requirements map adds over "just using the objects": every gap, barrier, referral, and episode has an owner, an origin, and a lifecycle that the platform allows, decided before anyone builds a flow.

---

## Core Concepts

### ICM Object Families

| Family | Objects | API version | Notes |
|---|---|---|---|
| SDOH (social determinants) | `CareBarrier`, `CareBarrierDeterminant`, `CareBarrierType`, `CareDeterminant`, `CareDeterminantType`, `CareInterventionType` | 45.0 | Needs the Health Cloud managed package and the Social Determinants permission sets |
| Referrals | `ClinicalServiceRequest`, `ClinicalServiceRequestDetail` | See note | Listed among objects that need the FHIR-Aligned Clinical Data Model org pref |
| Care gaps | `CareGap`, `CareGapCriteriaResult`, `ClinicalMeasure`, `ClinicalMeasureCriteria`, `ClinicalMeasureCriteriaGrp` | 59.0 | Gaps are evaluated against clinical measures |
| Care episodes | `CareEpisode`, `CareEpisodeDetail` | 57.0 | Based on the FHIR EpisodeOfCare resource |
| Care plans | `CarePlan`, `CarePlanActivity`, `CarePlanTemplate`, `CarePlanTemplateProblem`, `GoalAssignment`, `ProblemDefinition`, `GoalDefinition`, `ActionPlanTemplateAssignment` | 56.0 to 57.0 | The PGI (problem, goal, intervention) library |

UNVERIFIED (2026-10-03): the API version for `ClinicalServiceRequest` (51.0 in earlier versions of this skill) was not re-read for this pass.

### SDOH Barrier vs Care Plan Problem

This is the most commonly confused distinction in care coordination requirements:

| Concept | Object | What it represents |
|---|---|---|
| Social barrier | `CareBarrier` | "The circumstances or obstacles affecting a patient or member"; status `Open` or `Addressed` |
| Care plan problem (instantiated) | `HealthCondition` | `ProblemDefinition` records "create HealthCondition records that serve as problems in care plans" |
| Care plan problem (template) | `CarePlanTemplateProblem` | Positions a problem in a care plan template |

There is no standard object named `CarePlanProblem`. The name exists only as the legacy managed-package object `HC24__CarePlanProblem__c`. A barrier can be linked to a care gap through `CareGap.CareBarrierId`.

### Care Gap Lifecycle

`CareGap` (API 59.0) supports `create()`, `update()`, and `upsert()`. Records carry a `RecordOriginType` of `Calculated`, `Imported`, or `ManuallyCreated`, a reporting period, and source-system fields. `Status` (`Open`, `Closed`, `Excluded`) has no Create or Update property in the field list. Coordinators act through `MeasureEvaluationStatus`, which includes `ManuallyOpened`, `ManuallyClosed`, and `ManuallyExcluded`, with `StatusReason` holding "the reason for force closing the care gap".

---

## Common Patterns

### Transition of Care Handoff Design

**When to use:** A patient is discharged from hospital and moves to outpatient care coordination.

**How it works:**
1. On discharge, a `CareEpisode` record covers the inpatient stay; `CareEpisodeDetail` can reference the referral that started it or the diagnoses it addresses.
2. A `ClinicalServiceRequest` (referral) goes to the receiving outpatient team.
3. The outpatient coordinator accepts the referral and creates a `CarePlan` for post-discharge management.
4. SDOH screening identifies transportation and food barriers; `CareBarrier` records are linked to the patient and, where coordination work is needed, to a Case.
5. Care gaps arrive by calculation or import and appear in the coordinator's list.
6. The coordinator works barrier interventions through tasks, and an Action Plan on the Case can generate them (see `references/metadata-examples.md`).

### SDOH Screening and Barrier Resolution

**When to use:** A coordinator runs social needs screening and finds barriers that need intervention.

**How it works:**
1. Run the screening assessment; `CareBarrier.SurveyResponseId` can reference the survey response.
2. For each positive finding, record a barrier with its `CareBarrierType` and `Priority` (`Low`, `Normal`, `High`).
3. Create a Case when a community resource intervention must be tracked.
4. Generate intervention tasks on the Case.
5. Set the barrier's `Status` to `Addressed` when the intervention is complete. UNVERIFIED (2026-10-03): earlier versions of this skill said the barrier status updates automatically when tasks close; the guide does not describe that automation.

---

## Decision Guidance

| Situation | Recommended Object | Reason |
|---|---|---|
| Screening found food insecurity | `CareBarrier` with a `CareBarrierType` | Social determinant, not a clinical diagnosis |
| Uncontrolled diabetes needs a care plan problem | `HealthCondition` instantiated from a `ProblemDefinition` | Clinical problem in the PGI hierarchy |
| Patient overdue for A1c screening | `CareGap` evaluated against a `ClinicalMeasure` | Quality measure gap with origin, period, and status |
| Coordinator knows of a gap the engine missed | `CareGap` with `RecordOriginType` = `ManuallyCreated` | The data model records manual origin explicitly |
| Patient referred to a specialist | `ClinicalServiceRequest` | Clinical referral; needs the FHIR-aligned org pref |
| Defined period of inpatient care | `CareEpisode` | Episode of care based on FHIR EpisodeOfCare |

---

## Recommended Workflow

1. **Verify prerequisites.** Confirm the FHIR R4-Aligned Data Model setting and the Enhanced Care Plans setting are enabled, the FHIR-Aligned Clinical Data Model org pref is on if referrals are in scope, and coordinators hold the Health Cloud permission set licenses and Social Determinants permission sets.
2. **Map scenarios to object families.** For each scenario in scope, name the objects from the table above and the record that anchors it (patient account, Case, care plan).
3. **Design SDOH tracking.** Define `CareBarrierType` and `CareDeterminantType` values, the screening-to-barrier rule, when a Case is created, and the intervention tasks. Test a barrier insert in a sandbox before sign-off.
4. **Design care gap sourcing and lifecycle.** Decide which gaps are calculated, imported, or manually created; who may close or exclude them; and the reasons they must record.
5. **Design transition of care handoffs.** Map each handoff to `ClinicalServiceRequest` and `CareEpisode`, and name the roles that send and receive.
6. **Decide on Slack.** If Slack is in scope, confirm `enableCareMgmtSlackAccess` and its prerequisites before designing Slack-dependent steps. Deployable settings are in `references/metadata-examples.md`.

---

## Review Checklist

- [ ] FHIR R4-Aligned Data Model and Enhanced Care Plans settings confirmed
- [ ] Permission set licenses and Social Determinants permission sets confirmed for coordinators
- [ ] Process-to-object mapping documented for each scenario
- [ ] Barrier vs care plan problem distinction applied (`CareBarrier` vs `HealthCondition`)
- [ ] Care gap origin (calculated, imported, manual) and closure policy documented
- [ ] Barrier insert tested in a sandbox
- [ ] Slack decision recorded with the `enableCareMgmtSlackAccess` setting

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Care gaps can be calculated, imported, or manually created | Designs that forbid manual gaps block a supported workflow |
| 2 | `CareGap.Status` is not writable | Flows that set Status fail; use `MeasureEvaluationStatus` |
| 3 | ICM needs two named settings plus licences | Objects are missing at build time |
| 4 | `CareBarrier.CaseId` is optional | Forcing a Case on every barrier creates empty Cases |
| 5 | The guide lists no `create()` call for `CareBarrier` | Screening automation may fail to insert barriers |
| 6 | Referrals need the FHIR-Aligned Clinical Data Model org pref | `ClinicalServiceRequest` is unavailable without it |
| 7 | Slack coordination is its own setting | Slack steps silently do nothing when the app is off |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ICM object family mapping | Each care coordination scenario mapped to its objects |
| SDOH screening to barrier resolution workflow | From screening through barrier, Case, tasks, and `Addressed` |
| Care gap sourcing and lifecycle | Origin per source, closure and exclusion policy, required reasons |
| Transition of care handoff design | `ClinicalServiceRequest` and `CareEpisode` workflow for care transitions |

---

## Related Skills

- `admin/care-plan-configuration`: ICM care plan template setup (ProblemDefinition, GoalDefinition, ActionPlanTemplate)
- `admin/care-program-management`: care program enrollment that precedes coordination workflow
- `admin/referral-management-health`: `ClinicalServiceRequest` referral configuration for handoffs
- `admin/clinical-data-requirements`: FHIR-aligned clinical data model prerequisites
