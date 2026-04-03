# Apex Layering Worksheet

## Entry Points

- Trigger:
- Controller / REST / Invocable:
- Scheduler / Async:

## Proposed Layers

| Concern | Class | Notes |
|---|---|---|
| Orchestration | `...Service` | |
| Data access | `...Selector` | |
| Object-specific rules | `...Domain` | |
| External dependency | `...Gateway` / interface | |
| Factory or resolver | `...Factory` | |

## Review Guardrails

- [ ] Entry points are thin adapters
- [ ] Query definitions are centralized where reuse exists
- [ ] Domain rules are not duplicated across entry points
- [ ] Dependency seams avoid `Test.isRunningTest()`
- [ ] Class names match real responsibilities
