# Flow Record Locking And Contention — Work Template

Use this template when a flow faults on a row lock or updates a hot parent record.

## Scope

**Skill:** `flow-record-locking-and-contention`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Shared row (object and record Id from the fault emails):
- Blocking transaction and what it holds the lock through:
- Update, Create or Delete inside a Loop?:
- Parent child-count per parent (skew):
- Ownership changes or reparenting in the flow:
- Callout after a `FOR UPDATE` query?:
- Publish behavior of any decoupling event:

## Approach

Which pattern from SKILL.md applies (collect-then-update, Platform Event decouple, Queueable handoff, Scheduled Path), and why.

## Checklist

- [ ] No Update, Create or Delete element inside a Loop; one DML after the loop
- [ ] Platform Event decouple evaluated for parent updates from high-traffic child flows
- [ ] Heavy parent recalculation handed off to Queueable Apex
- [ ] Every DML element has a fault path that logs to a central error log
- [ ] Event publish behavior chosen on purpose (Publish After Commit when the subscriber needs committed data)
- [ ] `FOR UPDATE` used only for a true read-modify-write race, with no callout after it
- [ ] Load-tested with parallel DML against the same parent
- [ ] `check_flow_record_locking_and_contention.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
