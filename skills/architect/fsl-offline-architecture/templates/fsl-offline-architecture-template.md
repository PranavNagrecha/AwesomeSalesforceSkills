# FSL Offline Architecture — Work Template

Use this template when designing or reviewing FSL Mobile offline architecture.

## Scope

**Skill:** `fsl-offline-architecture`

**Request summary:** (fill in)

## Context Gathered

- **Technicians:** (count)
- **WOs per technician per day (avg / max):** (count)
- **WOLIs per WO (avg / max):** (count)
- **Related objects per WOLI:** (count)
- **Dispatcher + technician concurrent edit frequency:** (low / medium / high)
- **Connectivity pattern:** (mostly online / intermittent / extended offline)

## Priming Volume Calculation

```
Page references = WOs × (1 + WOLIs + WOLIs × child_objects_per_WOLI)
Max example:   20 × (1 + 15 + 15×4) = 20 × 76 = 1,520 — EXCEEDS LIMIT
Safe example:  15 × (1 + 10 + 10×4) = 15 × 51 = 765 — within limit
```

Current calculation: (fill in) — Within 1,000 limit? yes / no

## Conflict Resolution Strategy

- [ ] **MERGE_ACCEPT_YOURS** — field device wins (default, lower friction)
- [ ] **MERGE_FAIL_IF_CONFLICT** — surfaces conflict for human resolution (more accurate)

Decision rationale: (fill in)

If MERGE_FAIL_IF_CONFLICT: conflict resolution UI designed: yes / no

## Offline Quality Enforcement

- [ ] VRs are NOT relied upon for offline quality (they fire at sync)
- [ ] App-layer checks in custom LWC actions / OmniScript for required fields
- [ ] Post-sync VR failure handling documented

## Ghost Record Cleanup

- [ ] `cleanResyncGhosts()` integrated into post-sync SDK workflow
- [ ] Cleanup triggers automatically after each sync

## Architecture Checklist

- [ ] Page reference calculation complete and within 1,000 limit
- [ ] Conflict resolution strategy chosen and documented
- [ ] Ghost record cleanup automated
- [ ] Server-side VRs/triggers understood as sync-time, not offline-time
- [ ] Priming tested with production-representative data volumes in sandbox
- [ ] Offline scenario test plan includes: 4-hour full offline, concurrent server edits, conflict resolution, ghost records

## Notes

(Record design decisions and any scope constraints.)
