# Flow Bulkification Review Template

## Context

| Item | Value |
|---|---|
| Flow type | |
| Trigger volume | UI / import / integration / schedule |
| Queries performed | |
| Related-record writes | |
| Apex actions used | |

## Loop Audit

| Loop Name | Elements executed per iteration | Risk | Refactor needed |
|---|---|---|---|
| | | | |

## Checklist

- [ ] No query, DML, or Apex action runs per loop iteration without justification.
- [ ] Same-record field updates use before-save when possible.
- [ ] Related-record updates are collected and committed intentionally.
- [ ] Import and API scenarios were considered.
- [ ] Async or Apex escalation was evaluated for high-volume logic.

## Recommended Refactor

State whether the flow should use query-once patterns, collection DML, before-save refactoring, or a move to Apex.

## Scale Math (fill in before approving)

| Quantity | Value | Where it came from |
|---|---|---|
| Records per transaction (cardinality) | | Default 200 — a Bulk API chunk, limits reset between chunks (`apexdev.txt` L14904–14907) |
| Worst-case related records per triggering record | | Not the average — the outlier parent |
| SOQL per interview (elements above the loop) | | Count `recordLookups` on the straight-line path |
| SOQL per interview (elements on the loop path) | | Count x worst-case fan-out |
| DML per interview | | Count `recordCreates` / `recordUpdates` / `recordDeletes` executions |
| Apex triggers on the object: SOQL / DML | | Same transaction, same budget (`apex/trigger-and-flow-coexistence`) |
| **Combined SOQL x cardinality** | | Must be < 100 synchronous (`apexdev.txt` L19544) |
| **Combined DML x cardinality** | | Must be < 150 (`apexdev.txt` L19554) |

## Measured Limit Usage (fill in after the load test)

Run a real chunk at the cardinality above, with the `Workflow` debug category at `FINER`.
Record what the log said, not what the estimate predicted.

| Debug event | Reading | Notes |
|---|---|---|
| `FLOW_BULK_ELEMENT_LIMIT_USAGE` — peak SOQL queries | | Per bulk element (`apexdev.txt` L38730–38744) |
| `FLOW_BULK_ELEMENT_LIMIT_USAGE` — peak DML statements | | |
| `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` — heap, CPU ms | | |
| `FLOW_BULK_ELEMENT_NOT_SUPPORTED` entries | | Anything listed here was **not** bulkified (`apexdev.txt` L38746–38747) |
| Records loaded / records correctly stamped | | A gap is a rolled-back or truncated chunk, not a data problem |

## Failure Semantics Decision

| Question | Decision |
|---|---|
| Does one bad row fail the whole write, or should good rows land? | |
| If partial: is this a Create-as-upsert with `doesUpsertAllOrNone` explicitly `false`? | |
| If per-row results are needed: what invocable Apex owns it? | |

Record the decision even when it is "all-or-none, by default" — `recordUpdates` has no
switch and `recordCreates` defaults to `true` (`api_meta.txt` L70953–70963), so an
unrecorded decision reads as an accident later.

## Checker Output

```
python3 skills/flow/flow-bulkification/scripts/check_flow_bulkification.py \
  --manifest-dir <source tree> --max-dml 3
```

Paste the run here. An empty run is evidence; "we ran it" is not.
