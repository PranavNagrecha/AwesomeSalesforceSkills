---
name: care-plan-configuration
description: "Use this skill when configuring care plan templates, care plan problems, goals, and tasks in Salesforce Health Cloud — covering both the Integrated Care Management (ICM) model (Spring '23+, FHIR R4-aligned, recommended) and the legacy managed-package model (CarePlanTemplate__c + Case Tasks). Trigger keywords: care plan template, ICM care plan, PGI library, action plan template, problem definition, goal definition, care plan setup. NOT for general case management configuration, non-Health-Cloud task management, or clinical program enrollment (see admin/care-program-management)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "set up care plan templates in Health Cloud"
  - "configure integrated care management problems and goals"
  - "how do I create a care plan in Health Cloud for a patient"
  - "PGI library setup for care plan action plan templates"
  - "migrate care plan from legacy CarePlanTemplate to ICM model"
  - "care plan tasks not showing up for care coordinators"
  - "action plan template not referencing standardized problems or goals"
tags:
  - health-cloud
  - care-plan
  - integrated-care-management
  - icm
  - pgi-library
  - action-plan-template
inputs:
  - Health Cloud org with the Health Cloud managed package installed (HealthCloudGA namespace)
  - "Confirmation of which care plan architecture is in use: legacy (CarePlanTemplate__c) or ICM"
  - List of clinical conditions, goals, and tasks to model as care plan templates
  - Determination of whether PGI (Problem/Goal/Intervention) library has been set up
  - User profiles and permission sets that need access to care plan features
outputs:
  - Care plan templates configured in the correct architecture for the org
  - PGI library populated with standardized ProblemDefinition and GoalDefinition records (ICM only)
  - ActionPlanTemplate records linked to the PGI library (ICM only)
  - Care plan problems, goals, and tasks visible to care coordinators on patient/member records
  - Decision guidance on legacy vs. ICM model for the org's investment horizon
dependencies:
  - admin/health-cloud-patient-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Care Plan Configuration

This skill activates when a practitioner needs to configure care plan templates, problems, goals, or tasks in Salesforce Health Cloud. It covers both the Integrated Care Management (ICM) model — the FHIR R4-aligned, platform-native architecture introduced in Spring '23 and the target of all future Salesforce investment — and the legacy managed-package model based on `CarePlanTemplate__c` and Case Tasks. The skill provides decision guidance on which model to use, prerequisite setup steps (including PGI library), and template configuration procedures. It is NOT for general case management, clinical program enrollment, or non-Health-Cloud task frameworks.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine which care plan architecture the org uses. The two models share no object schema — using advice intended for one model in an org running the other will produce configuration that does not work. Check for the presence of `CarePlanTemplate__c` records (legacy) or `ActionPlanTemplate` + `ProblemDefinition` records (ICM).
- If the org intends to use ICM, confirm whether the PGI (Problem/Goal/Intervention) library has been set up. The PGI library is a prerequisite for ICM care plan templates to reference standardized problems and goals. Skipping this step is the single most common ICM configuration failure.
- Understand the org's investment horizon. Salesforce has publicly stated that the legacy managed-package care plan model (CarePlanTemplate__c + Case Tasks) receives no future investment. New implementations should target ICM. Existing legacy implementations should plan migration.
- Identify which Health Cloud permission sets are assigned to care coordinator and care manager profiles. Both models require specific permission sets beyond HealthCloudFoundation for care plan creation and access.
- Confirm Health Cloud managed package version. ICM features are available from Spring '23 onwards; orgs on older package versions cannot use the ICM model without upgrading.

---

## Core Concepts

### The Two Care Plan Architectures

Health Cloud has two architecturally distinct care plan models that cannot be used interchangeably.

**Legacy Managed-Package Model** uses `CarePlanTemplate__c` (a custom object in the HealthCloudGA namespace), with care plan tasks modeled as Case Tasks linked to the patient's case record. Configuration happens through Health Cloud Setup in the managed-package admin UI. Salesforce has explicitly stated this model receives no future investment and exists only for backward compatibility.

**Integrated Care Management (ICM) Model** was introduced in Spring '23. It is FHIR R4-aligned, uses platform-native standard objects (`ActionPlanTemplate`, `ProblemDefinition`, `GoalDefinition`, `CareDiagnosis`, `CareObservation`), and is the target of all new feature development. ICM care plans are not backed by cases — they are independent records linked directly to patient/member records. The ICM model supports interoperability with external clinical systems through the FHIR R4 data model.

The objects, setup steps, admin UI screens, and permission sets for these two models are entirely separate. Always confirm the architecture before giving configuration guidance.

### The PGI Library (ICM Prerequisite)

The PGI (Problem/Goal/Intervention) library is a repository of standardized `ProblemDefinition` and `GoalDefinition` records that care plan templates reference. In ICM, an `ActionPlanTemplate` is a reusable care plan blueprint. For the template to attach standardized clinical problems and goals — rather than ad hoc free-text entries — those problems and goals must first exist as records in the PGI library.

PGI library setup involves:
1. Enabling the Integrated Care Management feature in Health Cloud Setup.
2. Creating `ProblemDefinition` records for each clinical condition the org manages (e.g., Type 2 Diabetes, Hypertension, COPD).
3. Creating `GoalDefinition` records for each clinical goal (e.g., HbA1c below 7%, Blood pressure below 130/80).
4. Associating goals with problems through `ProblemGoalDefinition` junction records.

Without PGI library records, `ActionPlanTemplate` configurations cannot reference standardized clinical content — care coordinators will see empty problem and goal pickers.

### ActionPlanTemplate in the ICM Model

An `ActionPlanTemplate` is the ICM equivalent of a care plan template. It defines the reusable structure: which problems, goals, and interventions (tasks) apply to a patient cohort with a given condition. `ActionPlanTemplate` is a standard Salesforce object (not a managed-package object), which means it follows standard object permissions, sharing rules, and Metadata API deployment patterns.

Key behaviors:
- An `ActionPlanTemplate` can reference multiple `ProblemDefinition` and `GoalDefinition` records from the PGI library.
- Activating a template against a patient record instantiates a `CarePlan` record with associated `CarePlanProblem`, `CarePlanGoal`, and `CarePlanActivity` records.
- Template versioning is supported — publishing a new version does not affect in-flight care plans already instantiated from previous versions.

### Legacy CarePlanTemplate__c

In the legacy model, `CarePlanTemplate__c` is a custom object in the HealthCloudGA managed package. Care plan tasks are modeled as `Task` records of type `CarePlanTask`, associated with the patient's `Case` record. Configuration is done through the Health Cloud Setup managed-package UI under "Care Plan Templates." This model does not support FHIR alignment, has no PGI library concept, and cannot reference standardized clinical terminology records.

---

## Common Patterns

### Pattern 1: New ICM Implementation — Full Setup from Scratch

**When to use:** Org is on Spring '23 or later, is either new to Health Cloud or ready to adopt ICM, and wants care plans aligned to FHIR R4 with future-proof architecture.

**How it works:**
1. Enable Integrated Care Management in Health Cloud Setup (Setup > Health Cloud > Integrated Care Management > Enable).
2. Assign the `HealthCloudICM` permission set to care coordinator and care manager profiles.
3. Populate the PGI library: create `ProblemDefinition` records for each clinical condition, `GoalDefinition` records for each clinical goal, and `ProblemGoalDefinition` junction records linking goals to problems.
4. Create `ActionPlanTemplate` records for each care plan type (e.g., Diabetes Management, Post-Discharge). Set the template status to Draft while configuring.
5. Add `ActionPlanTemplateItem` records to each template to define the intervention tasks (activities) with assignee roles and target durations.
6. Link `ProblemDefinition` and `GoalDefinition` records from the PGI library to the template through the template's problem and goal association records.
7. Publish the template (set status to Active). Apply the template to a patient record to instantiate a `CarePlan`.

**Why not the alternative:** The legacy model requires Case-based care plans, which adds case management overhead, cannot align to FHIR R4, and will not receive new feature investment. New ICM implementations avoid inheriting that architectural debt.

### Pattern 2: Legacy Configuration — Adding Templates to an Existing CarePlanTemplate__c Setup

**When to use:** Org already has production care plans running on the legacy model and cannot migrate immediately. A new care plan type is needed.

**How it works:**
1. In Health Cloud Setup, navigate to Care Plan Templates (legacy managed-package admin UI).
2. Create a new `CarePlanTemplate__c` record with the template name and description.
3. Add `CarePlanTemplateTask__c` records to define the tasks associated with the template, including task subject, due date offset (days from plan creation), and assignee role.
4. Associate the template with the relevant clinical condition using the template's condition picklist field.
5. Test by manually applying the template from a patient's case record.

**Why not the alternative:** Introducing ICM objects into an org still running the legacy model without a full migration plan creates a split architecture that care coordinators cannot navigate and that the standard Health Cloud UI does not reconcile.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Health Cloud implementation, Spring '23 or later | Use ICM model (ActionPlanTemplate + PGI library) | All future Salesforce investment targets ICM; FHIR R4 alignment enables interoperability |
| Existing legacy implementation, no immediate migration budget | Continue legacy model, plan ICM migration | Abruptly mixing models without migration creates split architecture and UX confusion |
| Org on Health Cloud package older than Spring '23 | Upgrade package, then implement ICM | ICM objects are not available on older package versions |
| Org needs FHIR R4 interoperability for care plans | ICM model only | Legacy model has no FHIR alignment; CarePlanTemplate__c is not exposed through the FHIR API |
| Temporary new care plan type during migration period | Add to legacy model with migration note | Avoids split architecture mid-migration; document for cutover |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm architecture** — Query the org for both `CarePlanTemplate__c` records (legacy indicator) and `ActionPlanTemplate` records (ICM indicator). Determine which model is active. Do not proceed with configuration guidance until the architecture is confirmed.
2. **Verify prerequisites** — For ICM: confirm the Integrated Care Management feature is enabled in Health Cloud Setup and that the `HealthCloudICM` permission set is assigned to relevant profiles. For legacy: confirm the HealthCloudGA package is installed and Care Plan Template admin UI is accessible.
3. **Set up PGI library (ICM only)** — Before creating any `ActionPlanTemplate`, populate `ProblemDefinition`, `GoalDefinition`, and `ProblemGoalDefinition` records. This is the most frequently skipped step and the most common cause of empty problem/goal pickers in ICM care plan templates.
4. **Create and configure templates** — For ICM: create `ActionPlanTemplate` records in Draft status, add `ActionPlanTemplateItem` task records, and link PGI library entries. For legacy: create `CarePlanTemplate__c` and associated `CarePlanTemplateTask__c` records through the managed-package UI.
5. **Assign permissions** — Confirm that care coordinator profiles have the correct permission sets for the chosen model. ICM and legacy models require different permission sets; do not assume HealthCloudFoundation alone is sufficient.
6. **Test template instantiation** — Apply a care plan template to a test patient record. Verify that all expected problems, goals, and tasks appear correctly. For ICM, confirm `CarePlanProblem`, `CarePlanGoal`, and `CarePlanActivity` records are created. For legacy, confirm Case Tasks appear on the patient's case.
7. **Review and publish** — For ICM, set the `ActionPlanTemplate` status to Active. Document the template version and confirm template versioning behavior is understood before putting live care plans into production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Care plan architecture confirmed (ICM vs. legacy) before any configuration was done
- [ ] PGI library populated with ProblemDefinition and GoalDefinition records (ICM orgs only)
- [ ] ActionPlanTemplate or CarePlanTemplate__c records created and in correct status
- [ ] Correct permission sets assigned to care coordinator and care manager profiles
- [ ] Template instantiation tested on a patient record — all expected records created
- [ ] Template versioning behavior understood and documented for live-plan scenarios
- [ ] No CarePlanTemplate__c objects referenced in an ICM-model org (and vice versa)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PGI library omission breaks ICM template pickers silently** — Creating an `ActionPlanTemplate` without first populating the PGI library does not produce an error. The template saves successfully, but when a care coordinator tries to add problems or goals, the picker is empty. There is no validation warning. Administrators frequently mistake this for a permission issue and spend time debugging the wrong thing.

2. **Legacy CarePlanTemplate__c fields do not exist in ICM orgs** — In orgs that have migrated to ICM or were provisioned for ICM from the start, `CarePlanTemplate__c` may not be present or may be an empty legacy table. Any SOQL queries, workflow rules, or formula fields referencing `CarePlanTemplate__c` fields — such as `CarePlanTemplate__c.Description__c` or `CarePlanTemplate__c.TemplateName__c` — will throw "No such column" errors. This is the most common breakage when applying legacy guidance to an ICM org.

3. **ActionPlanTemplate versioning does not update in-flight CarePlans** — Publishing a new version of an `ActionPlanTemplate` does not retroactively update `CarePlan` records that were instantiated from previous versions. In-flight care plans continue to use the task structure from the version that was active at the time of instantiation. Administrators expecting a template update to cascade to open care plans are surprised when nothing changes for existing patients.

4. **ICM requires Health Cloud package version upgrade for Spring '23 features** — Orgs that installed Health Cloud before Spring '23 must explicitly upgrade the managed package before ICM objects become available. The feature flag in Health Cloud Setup will not appear on older package versions. Upgrading the managed package in production requires a sandbox test cycle and a Salesforce support-coordinated upgrade window for some editions.

5. **Care plan permission sets are model-specific and not interchangeable** — The `HealthCloudICM` permission set (ICM model) and the `HealthCloudCarePlan` permission set (legacy model) grant different object access. Assigning the wrong permission set results in care coordinators who can see the care plan UI but cannot create, edit, or view records. Both sets may need to coexist temporarily in orgs mid-migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PGI library records | ProblemDefinition, GoalDefinition, and ProblemGoalDefinition records in the ICM org that serve as the standardized clinical content library for all care plan templates |
| ActionPlanTemplate configuration | Active ICM care plan template with linked task items and PGI library associations, ready to instantiate CarePlan records against patient records |
| CarePlanTemplate__c configuration | Legacy care plan template with associated CarePlanTemplateTask__c records, configured through the HealthCloudGA managed-package admin UI |
| Permission set assignment matrix | Documentation of which permission sets (HealthCloudICM vs. HealthCloudCarePlan vs. HealthCloudFoundation) are required for each user profile in the org |

---

## Related Skills

- `admin/health-cloud-patient-setup` — Required prerequisite: Person Accounts, patient record types, and Health Cloud managed package must be in place before care plan configuration
- `admin/care-program-management` — Care programs (clinical program enrollment) are distinct from care plans; this skill covers care plans only
