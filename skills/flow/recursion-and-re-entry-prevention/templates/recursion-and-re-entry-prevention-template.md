# Flow Recursion and Re-Entry Prevention — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `recursion-and-re-entry-prevention`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record answers to the Before Starting questions from SKILL.md.

- Object and Flow(s) involved:
- Trigger configuration (before-save / after-save, Create / Update / CreateAndUpdate):
- Entry criteria expression(s):
- Fields the Flow updates that also appear in any entry condition:
- Other automations on the same object (Apex triggers, Process Builder, Workflow Rules, other Flows):
- Loop shape (self-re-entry / mutual / cross-object cascade):

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — tighten entry criteria with record-state guard
- [ ] Pattern 2 — hash-based idempotency marker
- [ ] Pattern 3 — shared lock field across related objects
- [ ] Consolidate two flows into one (the strategic alternative)

## Checklist

- [ ] Entry criteria of every record-triggered Flow on the object excludes the post-update state
- [ ] No "create or update" trigger fires unconditionally (every after-save Flow has at least one ISCHANGED, ISNEW, or formula condition)
- [ ] Cross-object cascades have a shared lock with one party as owner
- [ ] Apex triggers and Flows on the same object audited together
- [ ] Regression test reproduces the original loop and confirms the fix
- [ ] Guard's purpose documented inline (entry condition comment, field description, or Flow description)
- [ ] Any deprecated Process Builder or Workflow Rules involved are migrated or excluded

## Notes

Record any deviations from the standard pattern and why.
