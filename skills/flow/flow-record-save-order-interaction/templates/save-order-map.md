# Save Order Map — <Object>

## Object

Name:
Volume (records/day):
High-traffic events (insert/update):

## Automations Registered

Step numbers follow the Apex Developer Guide's 20-step list
(`apexdev.txt` L15416-L15489). Generate the flow rows mechanically rather than
typing them:

```bash
python3 skills/flow/flow-record-save-order-interaction/scripts/check_flow_record_save_order_interaction.py \
    --manifest-dir force-app/main/default --map-only
```

| Step | Platform Action                      | Automation Name | Owner | Purpose |
|------|--------------------------------------|-----------------|-------|---------|
| 2    | Load values + system validation      |                 |       |         |
| 3    | Before-save Flow                     |                 |       |         |
| 4    | Before trigger (overwrites step 3)   |                 |       |         |
| 5    | System validation + validation rules |                 |       |         |
| 6    | Duplicate rule                       |                 |       |         |
| 7    | Save to DB (no commit)               |                 |       |         |
| 8    | After trigger                        |                 |       |         |
| 9    | Assignment rule (Lead/Case)          |                 |       |         |
| 10   | Auto-response rule (Lead/Case)       |                 |       |         |
| 11   | Workflow rule (+ field-update re-fire)|                |       |         |
| 12   | Escalation rule (Case)               |                 |       |         |
| 13   | Process Builder / WF-launched Flow   |                 |       |         |
| 14   | After-save Flow                      |                 |       |         |
| 15   | Entitlement rule                     |                 |       |         |
| 16   | Roll-up summary → parent save        |                 |       |         |
| 17   | Roll-up summary → grandparent save   |                 |       |         |
| 18   | Criteria-based sharing recalc        |                 |       |         |
| 19   | Commit                               |                 |       |         |
| 20   | Post-commit (async, email)           |                 |       |         |

## Observed Recursion

- Chain description:
- Guard / fix:

## Sign-Off

- [ ] No duplicate field ownership between workflow and flow.
- [ ] No field written by both the step-3 Flow and the step-4 before
      trigger (the trigger would silently win).
- [ ] Before-save flow limited to same-record field updates.
- [ ] No parent after-save Flow (step 14) relied on to fire from a child
      roll-up — a recursive save skips steps 9–17.
- [ ] Every co-resident Active flow on this object declares `triggerOrder`.
- [ ] Any platform event published from a flow here declares
      `publishBehavior` deliberately (the default is `PublishImmediately`,
      which fires before the step-19 commit).
- [ ] Every `AsyncAfterCommit` path has its own failure and replay story — it
      runs at step 20 and cannot roll the save back.
- [ ] Recursion guards documented.
