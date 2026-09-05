# CPU / Heap Review Worksheet

## Symptom

| Item | Value |
|---|---|
| Exception or hotspot | |
| CPU, heap, or both? | |
| Transaction type (sync / batch / future / scheduled) | |
| Applicable ceiling (10,000 ms + 6 MB sync; 60,000 ms + 12 MB batch/future; scheduled uses the sync pair) | |
| Approximate data or payload volume | |
| Managed package code in the same save order? | |

## Baseline Measurement

Paste the `LIMIT_USAGE_FOR_NS` block from a failing bulk run.

| Reading | Before | After | Ceiling |
|---|---|---|---|
| `Limits.getCpuTime()` (ms) | | | |
| `Limits.getHeapSize()` (bytes) | | | |
| Record volume in the run | | | |

## Suspect Patterns

- [ ] Nested loops
- [ ] Large JSON payload handling
- [ ] String concatenation in loops
- [ ] Regex or parsing in loops
- [ ] Debug serialization or oversized logs
- [ ] `Database.Stateful` member or static cache retained across chunks
- [ ] `Schema.getGlobalDescribe()` resolved per record
- [ ] Defensive `clone()` of a large sObject list

## Remediation

- Primary structural fix:
- Measurement checkpoint plan:
- Async/cache follow-up if needed:
- Ceiling traded (which limit was spent to buy the other):
- Headroom left after the fix (% of `Limits.getLimit*()`):
- Bulk test asserting that headroom:
