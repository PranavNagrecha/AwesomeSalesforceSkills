# LLM Anti-Patterns: Care Coordination Requirements

Common mistakes AI assistants make when advising on Health Cloud care coordination. Several of these were present in earlier versions of this skill; the corrections are grounded in `gotchas.md`.

## Anti-Pattern 1: Declaring That Care Gaps Can Never Be Created Manually

**What the LLM generates:** "CareGap records are system-generated and cannot be created via the UI, Flow, or the API," followed by a design that blocks coordinators from opening gaps and forbids standard API loads.

**Why it happens:** Care gaps are usually produced by measure engines, so the model generalizes "usually calculated" into "never creatable". The claim also circulated in earlier documentation-derived content.

**Correct pattern:** `CareGap` supports `create()`, `update()`, and `upsert()`. `RecordOriginType` records `Calculated`, `Imported`, or `ManuallyCreated`. Design a source and an owner for each origin, and set source-system fields on imports.

**Detection hint:** Any "cannot be created" statement about `CareGap`, or an integration design that avoids the standard API for gap loads.

---

## Anti-Pattern 2: Setting `CareGap.Status` Directly

**What the LLM generates:** A "Close Gap" flow with an Update Records element that sets `Status = 'Closed'`.

**Why it happens:** Most objects let you write their status field, so the model assumes this one is writable.

**Correct pattern:** `Status` has no Create or Update property. Change `MeasureEvaluationStatus` to `ManuallyClosed` or `ManuallyExcluded` and require `StatusReason`. Confirm the resulting `Status` in a sandbox.

**Detection hint:** Any DML, flow element, or data load that writes `CareGap.Status`.

---

## Anti-Pattern 3: Inventing a `CarePlanProblem` Object

**What the LLM generates:** "Use CarePlanProblem for clinical problems and CareBarrier for social barriers," with flows and reports built on `CarePlanProblem`.

**Why it happens:** The name sounds right and appears in older Health Cloud material, where it is the legacy managed-package object `HC24__CarePlanProblem__c`.

**Correct pattern:** In ICM, `ProblemDefinition` records instantiate `HealthCondition` records as care plan problems; templates use `CarePlanTemplateProblem`. Social determinants use `CareBarrier`.

**Detection hint:** `CarePlanProblem` without the `HC24__` prefix in any ICM design.

---

## Anti-Pattern 4: Naming Settings and Permission Sets That Are Not in the Documentation

**What the LLM generates:** "Enable the two ICM checkboxes, Managing Care Plans and Calculating Care Gaps, and assign the HealthCloudICM permission set."

**Why it happens:** The model fills the gap between "ICM needs setup" and the real setting names with plausible labels.

**Correct pattern:** The guide names the FHIR R4-Aligned Data Model setting (FHIR R4 Support Settings) and the Enhanced Care Plans setting (Integrated Care Management Settings). The social determinants objects need the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License and Health Cloud Social Determinants permission sets. Say "confirm in Setup" for anything else.

**Detection hint:** Setting labels or permission set API names stated as fact with no source.

---

## Anti-Pattern 5: Forcing a Case Onto Every Barrier, or Skipping the Patient

**What the LLM generates:** "Create the Case first, then create the CareBarrier linked to both Account and Case," presented as a platform requirement; or a barrier insert with only a Case.

**Why it happens:** The Case lookup is visible in the schema, and the model treats every lookup as mandatory or every link as optional.

**Correct pattern:** `PatientId` is required; `CaseId` is nillable. Create a Case only when an intervention needs tracking, and write that rule into the requirements.

**Detection hint:** "Both are required" language about `CareBarrier`, or a barrier payload without `PatientId`.

---

## Anti-Pattern 6: Designing Barrier Automation Without an Insert Test

**What the LLM generates:** A screening flow that creates `CareBarrier` records, delivered with no note that the documented supported calls omit `create()`.

**Why it happens:** The model assumes standard objects accept standard DML.

**Correct pattern:** Insert and update a barrier in a sandbox as the target user before design sign-off, and keep a fallback (task on the Case) if inserts are refused.

**Detection hint:** Barrier-creating automation with no test step in the plan.

---

## Anti-Pattern 7: Assuming Referrals Exist Once Care Plans Are On

**What the LLM generates:** A transition of care design using `ClinicalServiceRequest` with prerequisites that list only the care plan settings.

**Why it happens:** Referrals feel like part of care coordination, so the model assumes the same switch enables them.

**Correct pattern:** `ClinicalServiceRequest` and `ClinicalServiceRequestDetail` are listed under "Org Pref Required" for the FHIR-Aligned Clinical Data Model. Add that org pref (`IndustriesSettings.enableClinicalDataModel` in metadata) to the prerequisites.

**Detection hint:** A referral-based design with no FHIR-aligned org pref in its prerequisites.

---

## Anti-Pattern 8: Assuming Slack Coordination Is Simply On

**What the LLM generates:** Slack alerts for handoffs and referrals described as standard Health Cloud behavior.

**Why it happens:** Slack and Health Cloud are often in the same org, and marketing material presents them together.

**Correct pattern:** Care Coordination for Slack is controlled by `IndustriesSettings.enableCareMgmtSlackAccess`. Treat licensing and the base Slack integration as items to confirm with the account team, and design Slack steps only after the setting is on.

**Detection hint:** Slack-dependent care team steps with no setting or licence check.
