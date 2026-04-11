# Financial Planning Process — Work Template

Use this template when configuring FSC financial planning objects, designing a review cycle, modeling risk tolerance data, or validating goal progress tracking.

## Scope

**Skill:** `financial-planning-process`

**Request summary:** (fill in what the user asked for)

## Org Context

Before working, confirm and record the following:

| Item | Value |
|---|---|
| Org type | Managed-package FSC (FinServ__ namespace) / FSC Core (Summer 2025+ standard objects) |
| FSC license | Confirm in Setup > Installed Packages or Company Information |
| Revenue Insights licensed? | Yes / No — confirm in Setup > Company Information > Feature Licenses |
| FinancialGoal API name | `FinServ__FinancialGoal__c` (managed) OR `FinancialGoal` (Core) |
| FinancialPlan API name | `FinServ__FinancialPlan__c` (managed) OR `FinancialPlan` (Core) |
| Goal → Plan lookup field | `FinServ__FinancialPlan__c` (managed) OR `FinancialPlanId` (Core) |
| ActualValue field API name | `FinServ__ActualValue__c` (managed) OR `ActualValue` (Core) |
| TargetValue field API name | `FinServ__TargetValue__c` (managed) OR `TargetValue` (Core) |

## Risk Tolerance Approach

Record the chosen risk tolerance modeling method:

- [ ] Discovery Framework (questionnaire delivery + custom scoring logic)
- [ ] Custom fields on Account/Household (Risk_Profile__c picklist + Risk_Tolerance_Score__c number)
- [ ] Third-party integration (tool name: ____________, output field: ____________)

## Review Cycle Design

| Item | Value |
|---|---|
| Review cadence | Annual / Semi-annual / Quarterly |
| Action Plan target object | FinancialAccount / Account / FinancialGoal |
| TaskDeadlineType | Calendar / BusinessDays |
| Plan launch mechanism | Manual / Flow / Batch process |
| Template name convention | e.g., "Annual Client Review v1" |

### Task Sequence Draft

| # | Task Subject | DaysFromStart | AssignedTo | Required? |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |

## Goal Progress Tracking

Record the goal status update mechanism:

- [ ] Record-Triggered Flow on ActualValue change
- [ ] Nightly scheduled batch
- [ ] Integration process updates Status during custodial sync
- [ ] Manual advisor update (not recommended — document reason)

Progress formula field installed: `Goal_Progress_Pct__c` — Yes / No

## Revenue Insights Decision

If analytics dashboards for goal progress are in scope:

- [ ] Revenue Intelligence for Financial Services license confirmed in production org
- [ ] CRM Analytics for Financial Services enabled in Setup
- [ ] Pre-built "Goals" dashboard reviewed and meets requirements
- [ ] Custom dashboard design documented (if pre-built is insufficient)

## Checklist

Copy from SKILL.md Review Checklist and tick as completed:

- [ ] Correct API names confirmed for this org type (managed-package vs. FSC Core)
- [ ] FinancialPlan-to-FinancialGoal relationship populated for all active goals
- [ ] Goal ActualValue and Status fields have a defined update mechanism
- [ ] Action Plan template TargetEntityType matches the intended FSC object and Status is Active
- [ ] DaysFromStart offsets verified with a test plan launch
- [ ] Risk tolerance capture method selected and fields/framework configured
- [ ] Revenue Insights license confirmed before building analytics dependencies
- [ ] No mixed-namespace API name references in any metadata or code artifact

## Deviations from Standard Pattern

Record any departures from the standard skill guidance and the reason:

(fill in as needed)

## Notes

(free-form notes, decisions, and open items)
