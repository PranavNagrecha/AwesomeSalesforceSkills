# Governor Limit Recovery Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `governor-limit-recovery-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Execution context (synchronous / async / batch / scheduled):
- Which limit is being hit (SOQL / DML / CPU / Heap / Callouts / Savepoints):
- Approximate record volume per transaction:
- Whether a BatchApexErrorEvent subscriber already exists:

## Recovery Strategy Selected

Check one:

- [ ] Limits class checkpoint inside loop — exit early and enqueue remaining work
- [ ] Savepoint-guarded DML block — rollback partial DML and defer atomically
- [ ] BatchApexErrorEvent subscriber — scope-level retry via status field
- [ ] CPU time checkpoint — early exit from expensive computation loop
- [ ] Other (describe):

## Approach

Which pattern from SKILL.md applies? Why is this pattern appropriate for this context?

## Implementation Notes

- Savepoints used: [ ] 0 [ ] 1 [ ] 2 [ ] 3 (max 5 per transaction — include setSavepoint() count)
- Static variables modified before savepoint that need explicit reset after rollback:
- sObject Id fields that need explicit null after rollback:
- DoesExceedJobScopeMaxLength handling: [ ] N/A [ ] Implemented

## Checklist

- [ ] No try/catch block is relied upon to intercept LimitException
- [ ] All Limits.* checkpoints are inside loops, not only at method entry
- [ ] Savepoint count in this transaction path does not exceed 5
- [ ] sObject Id fields explicitly nulled after every Database.rollback()
- [ ] Static variable caches reset alongside rollback
- [ ] BatchApexErrorEvent handler checks DoesExceedJobScopeMaxLength before parsing JobScope
- [ ] Unit tests exercise the headroom-exceeded branch, not just the happy path

## Notes

Record any deviations from the standard pattern and why.
