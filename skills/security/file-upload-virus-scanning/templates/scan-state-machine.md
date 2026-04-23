# File Scan State Machine

## States

| State | Readable by | Shareable externally | Previewable |
|---|---|---|---|
| `Scan_Pending` |   |   |   |
| `Scan_Clean` |   |   |   |
| `Scan_Infected` |   |   |   |
| `Scan_Error` |   |   |   |

## Transitions

- Insert → `Scan_Pending`
- `Scan_Pending` → `Scan_Clean` on verdict=clean
- `Scan_Pending` → `Scan_Infected` on verdict=infected
- `Scan_Pending` → `Scan_Error` on timeout/unreachable
- `Scan_Error` → retry (scheduled) → `Scan_Pending`
- `Scan_Clean` → `Scan_Pending` (scheduled rescan) → (`Clean` or `Infected`)

## Enforcement Surfaces

- [ ] UI (LWC) honors state.
- [ ] Sharing layer honors state.
- [ ] API access honors state.
- [ ] Content Delivery / public links honor state.

## Policy

- Fail-open or fail-closed on `Scan_Error`:
- Rescan cadence:
- Quarantine action (redact / move / tag):
- Retention period for infected records:
