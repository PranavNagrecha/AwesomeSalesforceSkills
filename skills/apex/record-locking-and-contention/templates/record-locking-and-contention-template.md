# Record Locking and Contention — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `record-locking-and-contention`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Error observed (UNABLE_TO_LOCK_ROW, timeout, rollback):
- Contention source (Bulk API, concurrent Apex, platform events, user actions):
- Objects and relationships involved:
- Data skew profile (max children per parent):
- Current processing mode (parallel/serial):

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Sort-Before-DML (deadlock from inconsistent ordering)
- [ ] Queueable Retry (transient contention, async-tolerant process)
- [ ] Bulk API Serial Mode (parallel batches on skewed data)
- [ ] FOR UPDATE (read-modify-write race condition)
- [ ] Granular Locking request (extreme data skew)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Lock contention source identified
- [ ] Records sorted by deterministic key before DML
- [ ] FOR UPDATE queries followed by minimal logic
- [ ] Retry logic exists for transient contention
- [ ] Bulk API jobs use serial mode for skewed data
- [ ] Data skew assessed and Granular Locking considered
- [ ] No inconsistent lock ordering across concurrent paths

## Notes

Record any deviations from standard patterns and why.
