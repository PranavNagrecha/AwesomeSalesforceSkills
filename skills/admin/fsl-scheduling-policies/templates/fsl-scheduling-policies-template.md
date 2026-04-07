# FSL Scheduling Policies — Work Template

Use this template when configuring or revising a Field Service Lightning scheduling policy.

## Scope

**Skill:** `fsl-scheduling-policies`

**Request summary:** (describe the scheduling problem or configuration task the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before proceeding.

- **Field Service enabled?** Yes / No — verified in Setup > Field Service Settings
- **Managed package installed?** Yes / No — verified in Setup > Installed Packages
- **Optimizer in use?** Salesforce Optimizer / Dispatcher Console / Both
- **Current active policy:** (name of the policy currently applied to relevant territories)
- **Primary business priority:** Customer satisfaction / Travel efficiency / SLA compliance / Overtime control
- **Skills/certifications in use on work orders?** Yes / No — (list if yes)
- **Territory boundary enforcement required?** Hard Boundary / Soft / None

## Policy Design

**Policy name:** (descriptive name reflecting use case — not a default policy name)

**Cloned from:** Customer First / High Intensity / Soft Boundaries / Emergency / Built from scratch

**Use case:** (one sentence describing when this policy applies)

### Work Rules

| Work Rule Name | Type | Required? | Notes |
|---|---|---|---|
| Service Resource Availability | Service Resource Availability | MANDATORY | Always include |
| (add rows as needed) | | | |

**Checklist:**
- [ ] Service Resource Availability is present
- [ ] Match Skills or Match Required Skills is present (if work types use skills)
- [ ] Territory boundary rule (Hard Boundary or Match Territory) is present if required
- [ ] Maximum Appointments is present if daily dispatch cap is needed
- [ ] Match Time Slot is present if customer preferred windows must be respected

### Service Objectives

| Objective | Weight (%) | Justification |
|---|---|---|
| ASAP | | |
| Minimize Travel | | |
| Minimize Overtime | | |
| Preferred Resource | | |
| Skill Level | | |
| **Total** | **100%** | Must sum to 100% |

## Policy Assignment

**Assigned to territories:**
- [ ] (territory name)
- [ ] (territory name)

**Applied via automation (if appointment-level override):**
- [ ] Flow rule: (describe trigger condition)
- [ ] Apex logic: (describe trigger condition)
- [ ] No automation — territory-level default only

## Validation Checklist

Copy and complete before marking the policy ready for production.

- [ ] Policy is a custom clone — the four default policies (Customer First, High Intensity, Soft Boundaries, Emergency) are unmodified
- [ ] Service Resource Availability work rule is present
- [ ] Service objective weights sum to 100%
- [ ] Policy has been tested by scheduling a representative test appointment
- [ ] Candidate ranking matches expected business priority (reviewed in Dispatcher Console or optimizer results)
- [ ] Yellow triangle rate post-deployment is acceptable (reviewed after initial live traffic)
- [ ] Policy name is descriptive and does not duplicate a default policy name

## Test Results

**Test appointment details:**
- Work Order: (Id or description)
- Territory: (territory name)
- Required skills: (list)
- Scheduled date/time: (expected window)

**Scheduling result:**
- Candidates surfaced: (number)
- Top-ranked candidate: (name or role)
- Work rules passed: (list)
- Work rules violated: (list)
- Yellow triangles shown: Yes / No

## Notes

Record any deviations from the standard pattern, edge cases encountered, or open questions.

- (note)
