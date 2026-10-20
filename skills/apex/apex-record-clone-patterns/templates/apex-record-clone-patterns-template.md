# Apex Record Clone Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-record-clone-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the SKILL.md pattern ("Copy of" with new autonumber, deep copy of Opportunity with line items, bulk clone 1→N, or clone with duplicate-rule bypass) and the Decision Guidance row that selected it.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Child records explicitly queried + reparented (clone does NOT do this)
- [ ] Autonumber preservation decision intentional
- [ ] Audit-field preservation paired with `CreateAuditFields` permission
- [ ] Bulk clone keeps DML inside limits
- [ ] Clone traceability (e.g., source-record lookup) persisted
- [ ] Duplicate rule behavior considered

## Notes

Record any deviations from the standard pattern and why.
