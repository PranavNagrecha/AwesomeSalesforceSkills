# Batch Apex Design Worksheet

## Batch Shape

| Question | Answer |
|---|---|
| Why is Batch needed instead of Queueable? | |
| QueryLocator or Iterable? | |
| Scope size | |
| Callouts required? | Yes / No |
| Stateful required? | Yes / No |

## Lifecycle Decisions

- `start()` responsibility:
- `execute()` idempotency notes:
- `finish()` reporting or dispatch:
- Monitoring owner:

## Guardrails

- [ ] Scope size is deliberate
- [ ] `execute()` is safe to retry
- [ ] `Database.Stateful` stores only lightweight state
- [ ] `AsyncApexJob` visibility is part of the design
- [ ] `Database.AllowsCallouts` is present when needed
