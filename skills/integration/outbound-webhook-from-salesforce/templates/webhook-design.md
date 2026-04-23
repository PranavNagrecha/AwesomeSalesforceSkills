# Outbound Webhook Design

## Trigger

- Source (record change / platform event / schedule):
- Estimated events / minute:

## Mechanism

- [ ] Outbound Message (only for legacy receivers; justify)
- [ ] Flow HTTP Callout (admin-owned, low volume)
- [ ] Apex Queueable callout
- [ ] Event Relay → EventBridge → Lambda dispatcher

Decision rationale:

## Payload

- Schema version:
- Fields:
- PII scrubbed / minimized:
- Idempotency key field:

## Signing

- [ ] HMAC-SHA256
- Secret storage (External Credential name):
- Timestamp window:

## Retry

- Status codes retried:
- Backoff sequence:
- Max attempts:
- Delivery tracking object:

## Dead-Letter

- DLQ target:
- Replay UI:
- Alert threshold:

## Observability

- Correlation id source:
- Dashboard link:

## Sign-Off

- [ ] No callouts from trigger.
- [ ] Secret in External Credential.
- [ ] Retry on 5xx/408/429 only.
- [ ] Idempotency key on every request.
- [ ] DLQ + replay path tested.
