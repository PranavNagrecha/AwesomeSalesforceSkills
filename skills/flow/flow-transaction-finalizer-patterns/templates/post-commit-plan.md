# Flow Post-Commit Plan Template

## Work To Run Post-Commit

- Trigger:
- Effect (email / callout / event / compensating update):
- Consumers (internal, external):

## Durability Requirement

- [ ] Nice to have
- [ ] Must run if trigger commits
- [ ] Must report success/failure and alert on failure
- [ ] Must support retry N times, then dead-letter

## Chosen Mechanism

- [ ] Scheduled Path (0 min)
- [ ] Platform Event (publish-after-commit)
- [ ] Apex Queueable + Finalizer

Rationale:

## Idempotency

- Correlation key:
- Duplicate-suppression logic:

## Logging

- Record produced per run (object / event):
- Alerting threshold:

## Sign-Off

- [ ] No pre-commit external effects.
- [ ] Retry behavior documented and tested.
- [ ] Finalizer / subscriber logs success AND failure.
- [ ] Runbook lists manual replay procedure.
