# Apex Limits Monitoring — Review Template

Fill this in when auditing someone else's Apex for limit safety, or when planning a new
monitoring layer. Every row that stays blank is a decision the next person has to guess at.

## Scope

**Skill:** `apex-limits-monitoring`

**Target:** (class, trigger, batch, or the whole monitoring layer)

**Request summary:**

## Context (answers to `## Questions to Ask Before Configuring` in SKILL.md)

| Question | Answer |
|---|---|
| Degrade contract: partial result or hard fail? | |
| Execution context (trigger / Batch execute / Queueable / Scheduled / Finalizer) | |
| Per-record cost of the hot loop (SOQL, subqueries, DML rows, callouts) | |
| Managed packages in this transaction? Which namespaces? | |
| Limits the business cares about, with observed peaks | |
| Alert owner and the action that clears the alert | |
| How a consumption regression gets caught before production | |

## Ceilings That Apply Here

Fill from the sync/async table in SKILL.md, then confirm the two traps:

| Meter | Ceiling in this context | Source |
|---|---|---|
| SOQL queries | | `Limits.getLimitQueries()` |
| DML statements | | `Limits.getLimitDMLStatements()` |
| DML rows | | `Limits.getLimitDMLRows()` |
| CPU time | | `Limits.getLimitCpuTime()` |
| Heap | | `Limits.getLimitHeapSize()` |

- [ ] If this is Scheduled Apex, the **synchronous** column applies (`apexdev L19536`)
- [ ] If this is a Finalizer, synchronous applies except heap, `enqueueJob` count and `@future` calls (`apexdev L16297–16303`)

## Findings

| # | Location | Meter | What is wrong | Severity | Fix |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

## Checklist

Copied from `## Review Checklist` in SKILL.md — tick as verified against the source, not
from memory.

- [ ] No hardcoded limit constants; every ceiling from `Limits.getLimitX()`
- [ ] Scheduled Apex sized against synchronous ceilings
- [ ] Headroom check before every SOQL/DML inside or reachable from a loop
- [ ] Degrade behaviour documented and detectable by the caller
- [ ] No `catch (System.LimitException)`; no `finally` relied on for breach logging
- [ ] `getCpuTime()` not polled every iteration of a tight loop
- [ ] Queueable chains bounded via `AsyncOptions.MaximumQueueableStackDepth`
- [ ] Batch scope documented with its per-record derivation
- [ ] Threshold percentages in Custom Metadata, not literals in two classes
- [ ] Snapshot object carries a DateTime column
- [ ] Guard tests consume real budget before asserting
- [ ] CI queries `ApexTestResultLimits`, and the tests are shaped so it is populated

## Checker Run

```bash
python3 scripts/check_apex_limits_monitoring.py --manifest-dir <source root> --format text
```

Findings, and for each one either the fix applied or the reason it is accepted:

## Deviations

Record any place this code departs from the patterns in SKILL.md, and why the departure is
correct here rather than an oversight.
