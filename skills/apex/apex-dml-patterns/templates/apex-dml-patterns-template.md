# Apex DML Patterns — Work Template

Use this template when working on DML-related tasks in Apex.

## Scope

**Skill:** `apex-dml-patterns`

**Request summary:** (fill in what the user asked for — insert/update/upsert/delete, object type, partial success needed?)

## Context Gathered

Answer the Before Starting questions from SKILL.md:

- DML operation type (insert / update / upsert / delete / merge):
- Partial success acceptable? (yes → `Database.class, false` / no → DML statement):
- Assignment rule firing needed? (yes → `DMLOptions.assignmentRuleHeader`):
- Duplicate rule bypass needed? (yes → `DMLOptions.duplicateRuleHeader.allowSave`):
- Multi-step atomicity needed? (yes → Savepoint/rollback):
- Object type (Account/Contact/Lead for merge?):

## Selected Approach

| Decision | Choice | Reason |
|---|---|---|
| DML method | DML statement / `Database.insert` | |
| allOrNone | `true` / `false` | |
| DMLOptions needed | yes / no | |
| Savepoint needed | yes / no | |

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them:

- [ ] No DML inside loops — all records collected into lists first
- [ ] DML operation count (not row count) verified under 150
- [ ] `SaveResult.isSuccess()` checked per row when `allOrNone=false`
- [ ] `DmlException` caught and re-thrown or logged at appropriate level
- [ ] `Database.DMLOptions` used where assignment rules or duplicate suppression is needed
- [ ] `Database.merge` only called for Account, Contact, or Lead
- [ ] Savepoints used when multi-step DML must be transactionally consistent

## Notes

Record any deviations from the standard pattern and why.
