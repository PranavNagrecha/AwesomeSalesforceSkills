# Flow Runtime Context And Sharing — Work Template

Use this template when choosing or auditing the run mode of a flow.

## Scope

**Skill:** `flow-runtime-context-and-sharing`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Flow type and how it is launched:
- `apiVersion` and current `runInMode` (flow-level field):
- Objects and fields read and written, and their sensitivity tier:
- Any single operation that needs more access than the rest of the flow:
- Running user on each invocation path:
- Dependence on recently granted sharing:
- Experience Cloud or guest-user entry point?:

## Approach

Which run mode (`DefaultMode`, `SystemModeWithSharing`, `SystemModeWithoutSharing`, `UserMode`) and which subflow escalations apply, and why.

## Checklist

- [ ] Explicit `runInMode` and `apiVersion` set on the flow
- [ ] Every `SystemModeWithoutSharing` flow has a description with the justification
- [ ] Each escalation is a subflow with its own documented `runInMode`
- [ ] No `$Permission` or `$User` branching on a path whose running user is unverified
- [ ] Screen flows and guest entry points stay in user context
- [ ] Persona test run as the lowest-privileged user who can trigger the flow
- [ ] `check_flow_runtime_context_and_sharing.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
