# Flow Performance Optimization — Work Template

Use this template when tuning a flow that is slow or near a governor limit.

## Scope

**Skill:** `flow-performance-optimization`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Target flow and entry point:
- Baseline: CPU ms, SOQL count, DML count, heap (read before `Test.stopTest`):
- Volume scenario (records per transaction):
- Other automations on the same object:
- Downstream consumers of asynchronous work:
- SLA and headroom:

## Approach

Which lever from the performance hierarchy applies (before-save, hoist DML or SOQL out of a loop, consolidate Get Records, cache lookups, asynchronous path), and why it is the dominant cost.

## Checklist

- [ ] Baseline measured inside `Test.startTest()` / `Test.stopTest()`
- [ ] Highest-impact lever applied first
- [ ] Per-iteration SOQL and DML hoisted out of loops
- [ ] Fault paths tested after the change
- [ ] Re-measured; delta recorded in the change description
- [ ] `check_flow_performance_optimization.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
