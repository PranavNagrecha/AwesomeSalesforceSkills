# Roll-Up Summary Decision Worksheet

## Relationship And Summary

| Question | Answer |
|---|---|
| Relationship type | Master-detail / Lookup |
| Summary type | Count / Sum / Min / Max (native) or Average / Count Distinct / Concatenate / First / Last (not native) |
| Real-time required | Yes / No |
| Largest number of children on one parent | |
| Child rows changed per load | |

## Child-Change Paths

| Path | Covered by |
|---|---|
| Insert | |
| Update, including reparent (old and new parent) | |
| Delete (Flow: before delete, exclude `$Record.Id`) | |
| Undelete (no Flow trigger exists) | |
| Merge reparenting (no child trigger fires) | |
| Cascaded delete (no child trigger fires) | |

## Pattern Choice

- Native fit:
- Flow option:
- Apex option:
- Tooling option (DLRS mode: Realtime / Scheduled / Developer API):
- Scheduled recompute (repair) job:

## Guardrails

- [ ] Native roll-up was rejected for a real reason
- [ ] Every path in the table above is covered
- [ ] Child loads are grouped by parent
- [ ] `python3 scripts/check_roll_up_summary_alternatives.py --manifest-dir force-app` reviewed
- [ ] There is an owner for repair or re-sync operations
