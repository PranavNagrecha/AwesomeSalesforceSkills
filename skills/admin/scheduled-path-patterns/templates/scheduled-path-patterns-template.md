# Scheduled Path Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `scheduled-path-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the SKILL.md pattern (follow-up after creation, reminder before a date field, or re-check at path execution) and the Decision Guidance row that selected a Scheduled Path over a Scheduled Flow or Apex.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Offset type explicit (event vs field)
- [ ] Entry criteria scoped tightly (no "always queue")
- [ ] Scheduled branch re-checks current record state
- [ ] Batch size reviewed for volume profile
- [ ] Paused Flow Interview monitoring documented
- [ ] Admin notification on scheduled-path errors enabled
- [ ] Bulk insert test confirms expected behavior

## Notes

Record any deviations from the standard pattern and why.
