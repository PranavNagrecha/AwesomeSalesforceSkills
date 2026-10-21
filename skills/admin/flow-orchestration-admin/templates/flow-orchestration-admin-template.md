# Flow Orchestration Admin — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `flow-orchestration-admin`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Which Common Pattern from SKILL.md applies (parallel review, long-wait with external callback, conditional rework loop), and why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Stage and step diagram matches whiteboarded process
- [ ] Evaluation Flows tested for each branch
- [ ] Every `stepInteractive` step has `assignees` (user, group, or queue)
- [ ] Aging report and reassignment path in place for long-wait stages (UNVERIFIED (2026-10-20): no corpus line documents a stage timeout)
- [ ] Fault paths defined inside each background step's flow
- [ ] `check_flow_orchestration_admin.py` run with no ERROR

## Notes

Record any deviations from the standard pattern and why.
