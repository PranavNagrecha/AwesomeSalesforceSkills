# Flow Batch Strategy Template

## Workload

- Flow or process name:
- Trigger (scheduled / record-triggered / manual):
- Records per run (today / projected 12 months):
- Complexity (simple update / multi-object / external callout):

## Measured Limits

| Limit | Observed today | Limit |
|---|---|---|
| CPU ms | | |
| DML statements | | |
| SOQL queries | | |
| Governor errors in logs | | |

## Decision

- [ ] Stay in Flow, no change
- [ ] Chunk in Flow (Platform Event / scheduled path / checkpoint)
- [ ] Escalate to Queueable
- [ ] Escalate to Database.Batchable

Reasoning / decision-tree citation:

## Implementation

- Chunk size:
- Retry behavior:
- Monitoring records emitted:
- Alert thresholds:

## Sign-Off

- [ ] Chunks stay under per-transaction limits.
- [ ] Failure handling tested with deliberate bad data.
- [ ] Monitoring + alert exists.
- [ ] Admin runbook for resume / requeue.
