# Gotchas: Care Coordination Requirements

Non-obvious Health Cloud behaviors that cause real production problems in care coordination designs. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 PDFs, written as `<guide> L<n>`; the Health Cloud developer guide is titled "Agentforce Health Developer Guide" in this release. A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Care gaps can be calculated, imported, or manually created

**What happens:** Earlier versions of this skill said `CareGap` records "cannot be created manually". The developer guide contradicts that. `CareGap` (API 59.0) lists `create()`, `update()`, and `upsert()` among its supported calls, and `RecordOriginType` "specifies the method used for retrieving or creating the care gap record" with the values `Calculated`, `Imported`, and `ManuallyCreated` (`health_cloud_dev_guide L36860-36866`, `L37036-37045`). Source-system fields (`SourceSystem`, `SourceSystemIdentifier`, `SourceSystemModified`) record where an imported gap came from.

**When it occurs:** A design forbids coordinators from opening a gap the measure engine missed, or an integration team is told it cannot load payer gaps with the standard API.

**How to avoid:** Decide the origin of every gap source at requirements time. Calculated gaps come from clinical measure evaluation (`ClinicalMeasure`, `ClinicalMeasureCriteria`, `CareGapCriteriaResult`). Imported gaps set the source-system fields. Manual gaps use `ManuallyCreated` and need a named owner and policy.

---

## Gotcha 2: `CareGap.Status` is not writable; closure runs through `MeasureEvaluationStatus`

**What happens:** `CareGap.Status` (`Open`, `Closed`, `Excluded`) shows only Filter, Group, Nillable, Restricted picklist, and Sort properties: no Create, no Update (`health_cloud_dev_guide L37092-37104`). The writable lifecycle field is `MeasureEvaluationStatus`, whose values include `EvaluationComplete`, `EvaluationError`, `EvaluationInProgress`, `ManuallyClosed`, `ManuallyExcluded`, and `ManuallyOpened` (`L36976-36990`). `StatusReason` holds "the reason for force closing the care gap" (`L37113-37117`).

**When it occurs:** A screen flow or integration tries to set `Status = 'Closed'` when a coordinator resolves a gap.

**How to avoid:** Design closure and exclusion as `MeasureEvaluationStatus` changes with a required `StatusReason`. UNVERIFIED (2026-10-03): how `Status` is derived from `MeasureEvaluationStatus` is not stated in the guide; confirm the resulting `Status` in a sandbox.

---

## Gotcha 3: ICM objects need two named settings, plus licences

**What happens:** The guide states: "To use this data model, go to Setup and enable the FHIR R4-Aligned Data Model setting on the FHIR R4 Support Settings page and the Enhanced Care Plans setting on the Integrated Care Management Settings page" (`health_cloud_dev_guide L36188-36195`). The social determinants objects also require the Health Cloud managed package, and are visible only to users with the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License and Health Cloud Social Determinants permission sets (`L66014-66020`).

**When it occurs:** A build starts on a sandbox where one setting or one permission set is missing, and objects or tabs do not appear.

**How to avoid:** Put both settings and the licence and permission set list in the requirements as prerequisites. UNVERIFIED (2026-10-03): the checkbox labels "Managing Care Plans" and "Calculating Care Gaps", and a permission set named `HealthCloudICM`, appeared in earlier versions of this skill but are not in the guide.

---

## Gotcha 4: `CareBarrier.CaseId` is optional; the patient lookup is not

**What happens:** Earlier versions of this skill said a barrier must link to both an Account and a Case. In the guide, `CareBarrier.CaseId` is a nillable lookup to Case, while `PatientId` is a lookup to Account with no Nillable property (`health_cloud_dev_guide L66070-66085`, `L66170-66180`).

**When it occurs:** Requirements force a Case onto every barrier, producing empty Cases, or skip the patient link and fail inserts.

**How to avoid:** Always set the patient. Create a Case only when a coordination or community resource intervention needs tracking. Record the rule in the requirements.

---

## Gotcha 5: The guide's supported-calls list for `CareBarrier` omits `create()`

**What happens:** The developer guide lists `CareBarrier` supported calls as `describeLayout()`, `describeSObjects()`, `getDeleted()`, `getUpdated()`, `query()`, `retrieve()`, and `search()` (`health_cloud_dev_guide L66049-66051`), even though several fields (for example `SurveyResponseId`, `SourceSystemIdentifier`) carry the Create property. The `Status` field (`Open`, `Addressed`) shows no Update property in the list.

**When it occurs:** A screening flow or integration is designed to insert barriers or move them to `Addressed`, and the design is signed off without a test.

**How to avoid:** Insert and update a barrier in a sandbox with the target user's permissions before design sign-off. UNVERIFIED (2026-10-03): whether the supported-calls list is complete or a documentation gap is not stated.

---

## Gotcha 6: Referrals need the FHIR-Aligned Clinical Data Model org pref

**What happens:** The clinical data model page lists `ClinicalServiceRequest` and `ClinicalServiceRequestDetail` under "Org Pref Required", meaning they appear only after the FHIR-Aligned Clinical Data Model org pref is enabled in FHIR R4 Support Settings (`health_cloud_dev_guide L8345-8368`).

**When it occurs:** A transition of care design depends on referrals in an org where only the care plan settings were enabled.

**How to avoid:** List the org pref as a prerequisite for any referral-based handoff. The deployable form is `IndustriesSettings.enableClinicalDataModel` (see `metadata-examples.md`). UNVERIFIED (2026-10-03): that `enableClinicalDataModel` is the metadata name for the "FHIR-Aligned Clinical Data Model" org pref is inferred from its description ("Indicates whether Clinical Data Model is enabled").

---

## Gotcha 7: Care Coordination for Slack is its own org setting

**What happens:** `IndustriesSettings.enableCareMgmtSlackAccess` "indicates whether Care Coordination for Slack app is enabled for your org" (API 56.0; `api_meta L119550-119551`). Slack-based care team steps do nothing in an org where it is off.

**When it occurs:** Designs assume Slack alerts for handoffs because Slack and Health Cloud are both in the org.

**How to avoid:** Record the Slack decision and the setting in the requirements. UNVERIFIED (2026-10-03): that the app is a separately licensed add-on, and that a base Slack and Health Cloud integration must already be deployed, are commercial and setup claims not in the guides read; confirm with the account team.

---

## Gotcha 8: There is no standard `CarePlanProblem` object

**What happens:** In ICM, "ProblemDefinition records create HealthCondition records that serve as problems in care plans", and template problems are `CarePlanTemplateProblem` records (`health_cloud_dev_guide L36243`, `L36283`). The name `CarePlanProblem` exists only as the legacy managed-package object `HC24__CarePlanProblem__c` (`L24866`).

**When it occurs:** Requirements, flows, or reports reference `CarePlanProblem` and fail at build time, or mix legacy package objects into an ICM design.

**How to avoid:** Use `HealthCondition` for instantiated problems and `CarePlanTemplateProblem` for templates. Keep legacy `HC24__` objects out of new ICM designs.
