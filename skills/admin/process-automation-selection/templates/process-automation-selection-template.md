# Process Automation Selection — Decision Record

Copy this file to `docs/adr/ADR-AUTO-<nnnn>.md`, fill every field, then lint the copy:

```bash
python3 scripts/check_process_automation_selection.py --decision-record docs/adr/ADR-AUTO-<nnnn>.md
```

The linter checks the blank form too, and will report it as incomplete — that is expected.
It passes only on a filled record. Worked examples live in
`references/decision-record-examples.md`.

```yaml
---
record_id: ADR-AUTO-0000
requirement: >
  One or two sentences. What must happen, to which object, under what condition.
trigger:                          # record_change | user_action | clock | inbound_call | event
volume:
  per_transaction:                # records in the largest single save — measured, not guessed
  per_day:                        # peak 24h volume
cross_object:                     # true | false — does it write anything but the triggering record?
timing:                           # before_save | after_save | scheduled | screen | async | n/a
chosen_mechanism:                 # e.g. before_save_record_triggered_flow, apex_trigger_handler, batch_apex
tree_steps_cited:
  - "automation-selection.md Q1 — <what the answer was and where it routed>"
  - "automation-selection.md Q<n> — <...>"
rejected:
  - alternative:                  # the mechanism not chosen
    reason: >
      Why it loses, in terms of a tree condition or a documented platform behaviour.
owner:                            # the team that answers for this rule in 18 months
review_date:                      # YYYY-MM-DD — when the volume assumptions get re-tested
---
```

## Scope

**Skill:** `process-automation-selection`

**Request summary:** Describe the requirement and why the current automation boundary is in question.

## Context Gathered

Answer all seven questions from SKILL.md § Questions to Ask Before Configuring:

- Triggering event:
- Same-record, related-record, user-guided, or scheduled work:
- Expected volume and transaction pressure (per transaction / per day):
- Existing Flow, trigger, or legacy automation already in play:
- Rollback, retry, or coverage-gate requirement:
- Owner in eighteen months:
- What would have to be true for this choice to be wrong:

## Automation Inventory (before)

Produced by the queries in `references/decision-record-examples.md` § One Object, One Order.

| Object | Surface | API name | Timing / TriggerOrder | Active | Owns |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Selected Automation Boundary

- Recommended tool:
- Tree steps that resolved it:
- Why this tool fits better than the alternatives:
- Skeleton to scaffold from (`templates/flow/RecordTriggered_Skeleton.flow-meta.xml` or `templates/apex/TriggerHandler.cls`):
- Migration or consolidation actions required:
- Hand-off skill:

## Checklist

- [ ] Trigger model matches the chosen tool
- [ ] Every branch cites a tree question number
- [ ] Each rejected alternative carries a reason
- [ ] Object inventory was captured before the proposal
- [ ] Same-record work was not over-engineered
- [ ] Flow and Apex boundaries are intentional
- [ ] Legacy Workflow Rule or Process Builder logic is treated as migration scope
- [ ] Transaction budget estimated across the whole save
- [ ] Ownership of the business rule is clear and a review date is set
- [ ] `check_process_automation_selection.py --decision-record` passes

## Notes

Record any order-of-execution, migration, or overlap risks.
