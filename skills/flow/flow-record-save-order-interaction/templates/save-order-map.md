# Save Order Map — <Object>

## Object

Name:
Volume (records/day):
High-traffic events (insert/update):

## Automations Registered

| Slot | Step                   | Automation Name | Owner | Purpose |
|------|------------------------|-----------------|-------|---------|
| 1    | System validation      |                 |       |         |
| 2    | Before-save Flow       |                 |       |         |
| 3    | Before trigger         |                 |       |         |
| 4    | Duplicate rule         |                 |       |         |
| 5    | Validation rule        |                 |       |         |
| 7    | After trigger          |                 |       |         |
| 8    | Assignment rule        |                 |       |         |
| 9    | Auto-response rule     |                 |       |         |
| 10   | Workflow (legacy)      |                 |       |         |
| 11   | After-save Flow        |                 |       |         |
| 14   | Roll-up / sharing recalc|                |       |         |
| 16   | Post-commit (async)    |                 |       |         |

## Observed Recursion

- Chain description:
- Guard / fix:

## Sign-Off

- [ ] No duplicate field ownership between workflow and flow.
- [ ] Before-save flow limited to same-record field updates.
- [ ] Recursion guards documented.
