# Callout Limits And Async Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `callout-limits-and-async-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Execution context:** [ ] Trigger  [ ] Batch Apex  [ ] LWC/Aura controller  [ ] Scheduled Apex  [ ] REST endpoint
- **Estimated callout count per transaction:** ___
- **DML before callout?** [ ] Yes  [ ] No  [ ] Unknown
- **Result needed in UI?** [ ] Yes (→ Continuation)  [ ] No

## Pattern Selection

| Scenario | Selected Pattern |
|---|---|
| DML before callout needed | Queueable with Database.AllowsCallouts |
| Fire-and-forget, no sObjects | @future(callout=true) |
| Chained callouts or sObject params | Queueable chain |
| LWC needs callout result | Continuation |
| > 100 callouts needed | Batch Apex + Queueable per chunk |

**Selected pattern:** _______________

**Reason:** _______________

## Checklist

- [ ] No callout after uncommitted DML in same transaction
- [ ] @future only used for simple fire-and-forget with primitive parameters
- [ ] Queueable used for sObject params, chaining, or Batch Apex
- [ ] Continuation only used in LWC/Aura/Visualforce controller
- [ ] Callout count per transaction confirmed under 100
- [ ] Named Credentials used for all endpoints — no hardcoded URLs

## Notes

(Record any deviations from the standard pattern and why.)
