# Callout and DML Transaction Boundaries — Work Template

Use this template when diagnosing or refactoring code that mixes callouts and DML.

## Scope

**Skill:** `callout-and-dml-transaction-boundaries`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Transaction context:** (trigger / controller / Queueable / Batch / @future / scheduled)
- **Full execution path DML sources:** (list every class, trigger, or flow that performs DML before the callout)
- **Callout dependency:** (does the callout result determine what gets saved, or can it be deferred?)
- **Async constraints:** (Queueable limit, chaining needs, existing @future usage)

## Transaction Map

Trace the execution order. Mark each operation as DML or CALLOUT.

| Step | Class/Trigger/Flow | Operation | Type |
|------|-------------------|-----------|------|
| 1 | | | DML / CALLOUT |
| 2 | | | DML / CALLOUT |
| 3 | | | DML / CALLOUT |

## Boundary Violation

Identify the exact point where a callout follows uncommitted DML:

- **Blocking DML at step:** ___
- **Failed callout at step:** ___
- **Fix strategy:** (reorder / Queueable / @future / split)

## Approach

Which pattern from SKILL.md applies and why:

- [ ] Pattern 1: Callout first, DML second (synchronous)
- [ ] Pattern 2: DML first, Queueable callout after commit
- [ ] Pattern 3: Callout-DML-Callout split with chained Queueables

## Review Checklist

- [ ] No DML occurs before any callout in the same synchronous transaction
- [ ] Queueable classes that make callouts implement `Database.AllowsCallouts`
- [ ] Record IDs (not sObjects) are passed to async boundaries
- [ ] The callout-dependent path has error handling for async failure scenarios
- [ ] Trigger handlers do not attempt direct callouts
- [ ] Test classes use `Test.setMock()` and verify both sync DML and async callout behavior

## Notes

Record any deviations from the standard pattern and why.
