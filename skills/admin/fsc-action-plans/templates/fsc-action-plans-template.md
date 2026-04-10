# FSC Action Plans — Work Template

Use this template when designing, building, or troubleshooting an FSC Action Plan template.
Fill in each section before starting implementation.

## Scope

**Skill:** `fsc-action-plans`

**Request summary:** (Describe what the client or stakeholder asked for — e.g., "Build a client onboarding Action Plan template for FinancialAccount records with 5 tasks and BusinessDays deadline mode.")

---

## Context Gathered

Answer these questions before doing any configuration work:

- **FSC enabled?** Yes / No — (Verify in Setup > Financial Services > Settings)
- **Target object type:** (FinancialAccount | FinancialGoal | InsurancePolicy | ResidentialLoanApplication | PersonLifeEvent | BusinessMilestone | Account | Contact | Opportunity | Other)
- **Deadline mode:** Calendar / BusinessDays — (Does the regulatory context require skipping weekends? Does it require skipping holidays? Note: BusinessDays skips weekends only.)
- **Estimated task count:** ___ (Must be ≤ 75. If > 75, plan for multi-phase templates.)
- **Plan launch mechanism:** Manual (related list) / Automated (Flow / Process Builder) / Both
- **Known constraints or compliance requirements:** (e.g., KYC tasks must be marked Required; tasks must be assigned to named queues, not users)

---

## Template Design

**Template name:** `[Use Case] v[N]` — e.g., `Client Onboarding v1`

**TargetEntityType:** _______________

**TaskDeadlineType:** Calendar / BusinessDays

| # | Task Subject | DaysFromStart | AssignedTo (Queue or User) | Required? | Priority |
|---|---|---|---|---|---|
| 1 | | | | Yes / No | Normal / High |
| 2 | | | | Yes / No | Normal / High |
| 3 | | | | Yes / No | Normal / High |
| 4 | | | | Yes / No | Normal / High |
| 5 | | | | Yes / No | Normal / High |
| (add rows as needed, max 75 total) | | | | | |

---

## Versioning Plan

**Current active version name:** _______________

**New version name (if updating):** _______________

**Existing in-flight plans on old version:** Yes / No — (If Yes: retain old template until all in-flight plans are closed.)

**Steps to complete this change:**
- [ ] Clone active template to create Draft
- [ ] Rename clone to new version name
- [ ] Apply task list changes to Draft clone
- [ ] Verify total item count ≤ 75
- [ ] Publish clone (set Status = Active)
- [ ] Communicate new template name to plan launchers
- [ ] Document old template retirement date (when all in-flight plans close)

---

## Test Plan

- [ ] Launch a test plan from a sandbox record of the target object type
- [ ] Verify all tasks appear with correct subjects and assignments
- [ ] Verify due dates match expected DaysFromStart offsets from plan start date
- [ ] Verify Required tasks block plan completion when left open
- [ ] Verify non-Required tasks allow plan completion when skipped
- [ ] Confirm BusinessDays deadline mode correctly skips weekends (if applicable)
- [ ] Confirm task count on launched plan = template item count (no missing items)

---

## Review Checklist

Copy from SKILL.md and tick items as you complete them:

- [ ] TargetEntityType matches the intended FSC or standard object
- [ ] TaskDeadlineType is correct (Calendar vs. BusinessDays) for the regulatory context
- [ ] All items have non-negative DaysFromStart and a valid AssignedTo
- [ ] Template Status is Active before attempting to launch any plan
- [ ] Test plan launched from a real target object record with correct due dates verified
- [ ] Versioning convention documented; prior template not deleted if in-flight plans exist
- [ ] Task count is under the 75-item platform limit

---

## Monitoring Setup

- **Report name:** (e.g., "FSC Action Plans — Incomplete Plans by Template")
- **Report filters:** ActionPlan.Status != Completed, ActionPlan.ActionPlanTemplateId = [Template Id]
- **Escalation alert:** (Flow or email alert for Required tasks overdue by X days)

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, or decisions made about required-task configuration, queue assignments, or versioning timeline.)
