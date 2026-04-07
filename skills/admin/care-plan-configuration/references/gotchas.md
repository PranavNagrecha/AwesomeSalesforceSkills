# Gotchas — Care Plan Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PGI Library Omission Produces No Error But Silently Breaks ICM Templates

**What happens:** An administrator creates an `ActionPlanTemplate` in the ICM model without first populating the PGI library. The template record saves successfully with no validation errors, is published to Active status, and appears correctly in the care plan template list. When a care coordinator attempts to instantiate the template against a patient record, the problem and goal picker fields are empty — no problems or goals can be selected. The care plan instantiates with task activities only, missing the clinical structure.

**When it occurs:** Any time an `ActionPlanTemplate` is configured before `ProblemDefinition` and `GoalDefinition` records exist in the PGI library, or when the template's problem and goal association records are not explicitly linked after PGI records are created.

**How to avoid:** Always populate the PGI library (`ProblemDefinition`, `GoalDefinition`, `ProblemGoalDefinition`) as a discrete prerequisite step before creating any `ActionPlanTemplate` records. Validate with SOQL: `SELECT COUNT() FROM ProblemDefinition` and `SELECT COUNT() FROM GoalDefinition` should both return non-zero counts before template creation begins. If a template already exists without PGI links, add the associations after creating PGI records — the template does not need to be recreated.

---

## Gotcha 2: ActionPlanTemplate Versioning Does Not Retroactively Update Live CarePlans

**What happens:** An administrator updates an `ActionPlanTemplate` — changing task names, adding new goals, removing outdated interventions — and publishes the new version. They expect all active `CarePlan` records previously instantiated from this template to reflect the changes. Nothing changes on the existing care plans. Patients and care coordinators continue to see the old task structure.

**When it occurs:** Any time a template is updated after care plans have already been instantiated from it. The ICM model treats template instantiation as a point-in-time snapshot: the `CarePlan`, `CarePlanProblem`, `CarePlanGoal`, and `CarePlanActivity` records created at instantiation time are independent records — they are not dynamically linked to the template after creation.

**How to avoid:** Communicate to operations teams before go-live that template updates are not retroactive. For organizations that need to update in-flight care plans when templates change, a process must be defined for manually updating affected `CarePlanActivity` records or re-instantiating plans under the new version. Document the template version used for each instantiation cohort so audits are possible.

---

## Gotcha 3: Legacy and ICM Permission Sets Are Not Interchangeable

**What happens:** An administrator assigns the `HealthCloudCarePlan` permission set (legacy model) to care coordinators in an org that has migrated to ICM. Care coordinators can navigate to the care plan section of the patient record but cannot create, edit, or save care plan records. The error messages vary — some see "Insufficient privileges," others see blank save buttons — because the permission set grants access to legacy care plan objects (`CarePlanTemplate__c`, Case Task records) but not to ICM objects (`ActionPlanTemplate`, `CarePlan`, `CarePlanActivity`).

**When it occurs:** During or after a migration from the legacy model to ICM, when permission set assignments are not updated as part of the migration checklist. Also occurs when documentation for an older Health Cloud implementation is reused verbatim for a new ICM-based implementation.

**How to avoid:** After migrating to ICM, replace `HealthCloudCarePlan` with `HealthCloudICM` on all affected profiles. During a migration transition period, both sets may need to coexist if some users still access legacy care plans while new ones are being created in ICM. Audit permission set assignments explicitly using: `SELECT Assignee.Name, PermissionSet.Name FROM PermissionSetAssignment WHERE PermissionSet.Name IN ('HealthCloudCarePlan', 'HealthCloudICM')`.

---

## Gotcha 4: Health Cloud Package Upgrade Required Before ICM Features Appear

**What happens:** An administrator on a pre-Spring '23 Health Cloud org navigates to Health Cloud Setup looking for the Integrated Care Management toggle. The toggle does not exist. They may also find that `ActionPlanTemplate` and `ProblemDefinition` objects are not listed in the Object Manager, even though their Salesforce org is on a recent API version. The ICM setup screens are entirely absent.

**When it occurs:** Any org that installed the HealthCloudGA managed package before Spring '23 (package version prior to 238.0 approximately) and has not performed a managed package upgrade. The ICM data model and setup screens are bundled in the managed package upgrade, not automatically provisioned to existing orgs by the platform release.

**How to avoid:** Before attempting ICM configuration, confirm the installed HealthCloudGA package version in Setup > Installed Packages. If the version predates Spring '23, coordinate a managed package upgrade. Upgrades require a full sandbox test cycle and, for some orgs, a Salesforce-coordinated upgrade window. Do not attempt an unplanned production package upgrade to access ICM features.

---

## Gotcha 5: CarePlan Records Are Not Case-Linked in ICM — Existing Case-Based Automations Will Miss Them

**What happens:** An org migrates care plans from the legacy model to ICM. Post-migration, existing Flow automations, triggers, or reports that relied on the relationship between `Case` records and `CarePlanTemplate__c` / Case Tasks stop receiving ICM care plan data. ICM `CarePlan` records are platform-native standard objects linked directly to the patient (person account) record — they are not associated with a `Case` record. Any downstream logic assuming a care plan lives on a case will silently miss all ICM care plans.

**When it occurs:** Migrations from legacy to ICM that do not audit all automations, reports, and integrations that reference the legacy Case-based care plan relationship before going live.

**How to avoid:** As part of any ICM migration, audit all Flows, Process Builder automations, triggers, and reports that query or reference `Case.CarePlanTemplate__c` relationships or Case Tasks with `Type = 'CarePlanTask'`. Rewrite these to reference `CarePlan`, `CarePlanActivity`, and `CarePlanProblem` objects instead. Run a side-by-side comparison of legacy and ICM report outputs on a test data set before cutting over.
