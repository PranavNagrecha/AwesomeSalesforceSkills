# Care Plan Configuration — Work Template

Use this template when configuring care plan templates in Salesforce Health Cloud.
Fill in each section as you work through the setup.

---

## Scope

**Skill:** `care-plan-configuration`

**Request summary:** (describe what the user or project needs — e.g., "Create a Diabetes Management care plan template using ICM model")

**Target architecture:** [ ] ICM (ActionPlanTemplate + PGI library) [ ] Legacy (CarePlanTemplate__c + Case Tasks)

---

## Context Gathered

Answer these before starting any configuration:

- **Health Cloud managed package version:**
- **ICM feature enabled in Health Cloud Setup?** [ ] Yes [ ] No [ ] Unknown — needs verification
- **PGI library populated?** [ ] Yes — record counts: ProblemDefinition: ___ GoalDefinition: ___ [ ] No — setup required [ ] N/A (legacy model)
- **Care plan types to configure:** (list the templates needed)
- **Clinical conditions (ProblemDefinition records needed):**
- **Clinical goals (GoalDefinition records needed):**
- **Task types and assignee roles per template:**
- **Permission sets currently assigned to care coordinator profiles:**

---

## Architecture Decision

**Which model is in use?**

| Signal | Present? | Notes |
|---|---|---|
| CarePlanTemplate__c records exist in org | [ ] Yes [ ] No | Legacy indicator |
| ActionPlanTemplate records exist in org | [ ] Yes [ ] No | ICM indicator |
| HealthCloudICM permission set assigned | [ ] Yes [ ] No | ICM indicator |
| ICM toggle visible in Health Cloud Setup | [ ] Yes [ ] No | Spring '23+ package required |

**Decision:** [ ] Use ICM model [ ] Use legacy model [ ] Migration in progress — document transition state

---

## PGI Library Setup (ICM Only — Skip for Legacy)

Complete this section before creating any ActionPlanTemplate records.

| Record Type | Name | Code | Code System | Status |
|---|---|---|---|---|
| ProblemDefinition | | | | [ ] Created |
| ProblemDefinition | | | | [ ] Created |
| GoalDefinition | | | | [ ] Created |
| GoalDefinition | | | | [ ] Created |
| ProblemGoalDefinition | Links: Problem → Goal | — | — | [ ] Created |

**Validation query run?** [ ] Yes — `SELECT COUNT() FROM ProblemDefinition` returned: ___

---

## ActionPlanTemplate Configuration (ICM Only)

For each care plan template:

### Template: ___________________________

- **ActionPlanTemplate Name:**
- **Status:** [ ] Draft (during setup) [ ] Active (when published)
- **ProblemDefinition records linked:**
- **GoalDefinition records linked:**

**Tasks (ActionPlanTemplateItem records):**

| Task Name | Assignee Role | Due Days from Plan Start | Priority |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**Template published to Active?** [ ] Yes [ ] No

---

## CarePlanTemplate__c Configuration (Legacy Only)

For each care plan template (configured in Health Cloud Setup > Care Plan Templates):

### Template: ___________________________

- **CarePlanTemplate__c Name:**
- **Clinical Condition:**

**Tasks (CarePlanTemplateTask__c records):**

| Task Subject | Assignee Role | Due Days Offset | Notes |
|---|---|---|---|
| | | | |
| | | | |

---

## Permission Set Assignment

| User Profile | HealthCloudFoundation | HealthCloudICM | HealthCloudCarePlan | Assigned? |
|---|---|---|---|---|
| Care Coordinator | Required | Required (ICM) | Required (Legacy) | [ ] |
| Care Manager | Required | Required (ICM) | Required (Legacy) | [ ] |
| Clinical Supervisor | Required | As needed | As needed | [ ] |

---

## Testing Record

**Test patient/member record used:**

| Test Step | Expected Result | Actual Result | Pass? |
|---|---|---|---|
| Instantiate template from patient record | CarePlan record created | | [ ] |
| Verify CarePlanProblem records created (ICM) | Problems from PGI library present | | [ ] |
| Verify CarePlanGoal records created (ICM) | Goals from PGI library present | | [ ] |
| Verify CarePlanActivity / Case Task records | All tasks visible to care coordinator | | [ ] |
| Confirm care coordinator can edit care plan | No "Insufficient privileges" error | | [ ] |

---

## Review Checklist

- [ ] Care plan architecture confirmed (ICM vs. legacy) before any configuration was done
- [ ] PGI library populated with ProblemDefinition and GoalDefinition records (ICM orgs only)
- [ ] ActionPlanTemplate or CarePlanTemplate__c records created and in correct status
- [ ] Correct permission sets assigned to care coordinator and care manager profiles
- [ ] Template instantiation tested on a patient record — all expected records created
- [ ] Template versioning behavior understood and documented for live-plan scenarios
- [ ] No CarePlanTemplate__c objects referenced in an ICM-model org (and vice versa)

---

## Notes and Deviations

(Record any deviations from the standard pattern, exceptions encountered, or decisions made during implementation)

---

## Handoff Summary

**Architecture used:**
**Templates configured:**
**PGI library records created (ICM):**
**Permission sets assigned:**
**Outstanding items or known limitations:**
