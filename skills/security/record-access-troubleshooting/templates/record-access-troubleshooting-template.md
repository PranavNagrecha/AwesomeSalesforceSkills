# Record Access Troubleshooting — Work Template

Use this template when diagnosing why a user can or cannot access a record.

## Scope

**Skill:** `record-access-troubleshooting`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the `## Before Starting` and `## Questions to Ask Before Configuring` items in SKILL.md here.

- User Id / Record Id / access level expected:
- Object org-wide default and "Grant Access Using Hierarchies" setting:
- Admin-bypass permissions held (View All Data, Modify All Data, object-level View All / Modify All):
- Symptom (too much or too little access) and any recent ownership or configuration change:
- Failure modes to watch for: manual shares cleared on ownership change, implicit parent share not reaching custom children, restriction rules applied after sharing, System Mode bypassing restriction rules

## Approach

Which diagnostic pattern from SKILL.md applies (minimal diagnostic query, `__Share` trace, admin bypass check) and why. Follow the Recommended Workflow order: `UserRecordAccess`, admin bypass, Sharing detail "Why can this user access?", `__Share` by ParentId, role hierarchy, restriction rules, then root cause and remediation.

## Checklist

Review checklist from SKILL.md; tick items as you complete them.

- [ ] `UserRecordAccess` query run first to confirm state
- [ ] Admin-bypass permissions ruled in/out
- [ ] `__Share` RowCause chain enumerated
- [ ] Role hierarchy relationship checked
- [ ] Restriction rules checked for the object
- [ ] If a restriction rule is the control, every Apex/Flow entry point confirmed to run in user mode
- [ ] Implicit-parent-share considered for child objects
- [ ] Remediation aligns with `sharing-selection` decision tree

## Notes

Record any deviations from the standard pattern and why.
