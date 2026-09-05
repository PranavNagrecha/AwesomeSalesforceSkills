# Flow Action Framework — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `flow-action-framework`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Flow type and bulk behavior:
- Declarative vs Apex vs subflow vs integration action fit:
- Apex class visibility and compilation status:
- Variable types (scalar vs collection) for the action boundary:

## The Seven Questions

One row per question in SKILL.md's `## Questions to Ask Before Configuring`. Fill every
row before writing XML; an unanswered row is the design decision you are about to make by
accident.

| # | Question | Answer | Consequence recorded |
|---|---|---|---|
| 1 | Which action family / `actionType`? | | |
| 2 | Who runs the flow — end user or admin? | | |
| 3 | Generic `sObject` or concrete? | | |
| 4 | On failure, do what — and is a timeout different here? | | |
| 5 | Does it call out, and has anything written yet? | | |
| 6 | Output read once, or branched on repeatedly? | | |
| 7 | What else ships with the flow for this action to resolve? | | |

## Action Inventory For This Flow

One row per action element. This table becomes the manifest and the review checklist.

| Element name | `actionType` | `actionName` | `flowTransactionModel` | Fault target | Extra metadata to package |
|---|---|---|---|---|---|
| | | | | | |

## Approach

Which pattern from SKILL.md applies? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Action category confirmed against the `actionType` taxonomy table
- [ ] List / bulk contract validated
- [ ] Permissions and visibility verified with a describe call as an end user
- [ ] Fault path or structured errors defined (and a timeout path if the action is async)
- [ ] `flowTransactionModel` set explicitly on every action call
- [ ] `dataTypeMappings` present for every generic-`sObject` parameter
- [ ] Manifest built from the action inventory, not from the flow
- [ ] `scripts/check_flow_action_framework.py --manifest-dir <dir>` run clean
- [ ] Bulk test scenario executed

## Notes

Record any deviations from the standard pattern and why.
