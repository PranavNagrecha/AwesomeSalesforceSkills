# Event Relay Configuration Template

## Channel

- Channel name (`/event/...` or `/data/...`):
- Channel type (High-Volume PE / CDC):
- Expected events / minute (peak):

## AWS Side

- Account id:
- Region:
- Target EventBridge bus:
- IAM role arn:
- External id (rotate cadence):

## Salesforce Side

- Named Credential:
- Connection name:
- Relay Config name:
- Replay setting (LATEST / EARLIEST / specific id):

## Filter

- Field:
- Operator:
- Value:

## Consumer Contract

- Idempotency key:
- Retry behavior:
- Dead-letter target:

## Ops

- Lag alert threshold:
- Failure alert threshold:
- Replay runbook link:

## Sign-Off

- [ ] High-Volume channel (if PE).
- [ ] IAM with external id.
- [ ] Watermark tracked downstream.
- [ ] Consumer idempotent.
- [ ] Monitoring wired in.
