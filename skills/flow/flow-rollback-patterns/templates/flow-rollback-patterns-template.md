# Flow Rollback Patterns — Work Template

Use this template when deciding where a flow rolls back and what must survive the rollback.

## Scope

**Skill:** `flow-rollback-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Flow type (Roll Back Records is screen-flow only; record-triggered flows use Custom Error):
- DML sequence, in order:
- Platform events published, and their publish behavior:
- Where the failure evidence is written:
- Callouts and emails in the path:
- Subflows and invocable actions (`flowTransactionModel`):
- Failures that must NOT roll back:

## Approach

Which pattern from SKILL.md applies (create-create with rollback, screen cancel, compensating event, no rollback on logging failure), and why.

## Checklist

- [ ] Rollback element matches the flow type
- [ ] Rollback placed on the fault path of the critical element only
- [ ] Failure evidence written to a Publish Immediately platform event, not only a record the rollback cancels
- [ ] Publish behavior of every published event checked; compensating event designed for Publish Immediately
- [ ] Callouts and emails sequenced so a rollback does not leave the outside world inconsistent
- [ ] Non-critical failures (logging, notification) end silently
- [ ] Fault path tested by forcing a failure
- [ ] `check_flow_rollback_patterns.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
