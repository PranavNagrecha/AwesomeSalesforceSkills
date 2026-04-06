# System Field Behavior and Audit — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `system-field-behavior-and-audit`

**Request summary:** (fill in what the user asked for)

**Use case type:** (delta sync / data migration / soft-delete recovery / audit understanding)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Which system fields are involved:** (SystemModstamp, LastModifiedDate, CreatedDate, IsDeleted, etc.)
- **Use case:** (incremental sync / migration date preservation / deleted record recovery / field behavior clarification)
- **Create Audit Fields status:** (enabled / not enabled / not applicable)
- **Object volume:** (approximate record count on the target object)

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Delta Sync with SystemModstamp
- [ ] Data Migration with Audit Field Preservation
- [ ] Soft-Delete Recovery Query
- [ ] General field behavior guidance

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Delta sync queries use SystemModstamp, not LastModifiedDate
- [ ] Soft-delete recovery queries use ALL ROWS (SOQL) or queryAll (REST)
- [ ] Create Audit Fields permission is confirmed enabled before migration insert
- [ ] The migrating user has the "Set Audit Fields upon Record Creation" user permission
- [ ] Audit field values are included only in insert operations, not updates
- [ ] Watermark / checkpoint strategy is documented for incremental sync
- [ ] Recycle Bin retention window (15 days) is accounted for in recovery plans

## Notes

Record any deviations from the standard pattern and why.
