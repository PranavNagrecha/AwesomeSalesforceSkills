# Apex Execute Anonymous — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-execute-anonymous`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the SKILL.md pattern (savepoint-guarded fix, iteration-bounded cleanup, or dry-run toggle) and the Decision Guidance row that selected it.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Target org confirmed explicitly (never rely on default config for prod)
- [ ] Savepoint or dry-run toggle present for DML scripts
- [ ] Record count bounded via `LIMIT` clause
- [ ] Debug output includes before/after counts
- [ ] Script saved to repo for audit trail
- [ ] Peer review for any production anonymous script

## Notes

Record any deviations from the standard pattern and why.
