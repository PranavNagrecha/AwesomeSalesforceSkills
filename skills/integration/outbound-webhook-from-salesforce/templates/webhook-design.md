# Outbound Webhook Design

One per outbound integration. Fill it before writing the producer — the questions
you cannot answer are the ones that will be answered by an incident instead.

Checked by `scripts/check_outbound_webhook_from_salesforce.py --src-dir <dir>`.

## Trigger

- Source (record change / platform event / schedule / manual):
- Triggering object and the specific transition:
- Estimated events per minute at **peak**, not average:
- Largest single burst modelled (mass update / data load / migration):
- Ordering: does the receiver apply deltas? (If yes, see Payload.)

## Mechanism

- [ ] Apex Queueable + outbox (default for anything with a reliability requirement)
- [ ] Flow HTTP Callout (admin-owned, low volume, **loss tolerated — stated below**)
- [ ] Platform Event + Apex subscriber (two or more consumers of the same signal)
- [ ] Event Relay → Amazon EventBridge (destination is an AWS estate, not an HTTPS endpoint)
- [ ] Outbound Message (existing only — host reached end of support 31 Dec 2025)

Decision-tree branch that resolved this
(`standards/decision-trees/integration-pattern-selection.md`, Direction 1, Q1–Q4):

Decision rationale:

If Flow HTTP Callout: who has agreed that event loss is acceptable, and where is
that recorded?

## Receiver Contract

- Endpoint (Named Credential developer name):
- Auth protocol (External Credential type):
- Documented rate limit, and whether they send `Retry-After`:
- What their 2xx promises — accepted, or processed?
- Idempotency: which header/field do they deduplicate on, and **who confirmed it**?
- Reconciliation mechanism, if any (count or checksum endpoint):
- Their documented retry expectations of you:

## Payload

- Schema version:
- Fields included (explicit list — never `JSON.serialize(record)`):
- PII assessment: which fields are personal data, and is each one necessary?
- Absolute state + version, not a delta? (Retry reorders. Always.)
- Version field and its source (`SystemModstamp`, a sequence, a revision number):
- Correlation id source:
- Idempotency key construction (must be stable across retries, unique per event):
- Approximate payload size, and whether notification-plus-pull is warranted:

## Signing

- [ ] HMAC-SHA256 over `"{timestamp}.{body}"`
- [ ] Asymmetric (receiver holds a public key)
- [ ] None — and the receiver has confirmed they do not require it
- Secret storage: External Credential name:
- [ ] The signed `String` and the sent `String` are the same instance
- Timestamp window the receiver enforces:
- Rotation runbook (must be a Setup change, not a deployment):

## Outbox

- Object API name:
- Idempotency field is External Id **and** Unique:
- Status values:
- Next-attempt field:
- Payload retained? If yes, retention period and purge job:
- Object access restricted to which permission set:

## Retry

- Status codes retried (5xx / 408 / 429 only):
- Status codes dead-lettered immediately:
- `Retry-After` honoured:
- Backoff sequence:
- Jitter applied:
- Max attempts before dead-letter:
- Batch size × per-callout timeout, and the arithmetic against the 120-second
  cumulative budget:
  > e.g. 10 deliveries × 8 s = 80 s < 120 s
- Finalizer role (immediate re-enqueue; platform cap is five successive):
- Sweeper schedule (the long tail; no cap):

## Dead-Letter

- Dead state name and how it differs from "still retrying":
- Alert threshold on DLQ depth:
- Alert threshold on **oldest-pending age** (the earlier signal):
- Replay procedure — written down, and tested at least once:
- Who is paged, and during which hours:

## Observability

- Correlation id threaded from record → delivery → receiver:
- Dashboard: status by hour, attempt-count distribution, oldest pending:
- [ ] Nothing logs the payload, the signature, or any credential

## Tests

- [ ] 2xx → `Sent`
- [ ] 5xx → stays `Pending`, `Next_Attempt_At__c` in the future
- [ ] 4xx (non-408/429) → dead-lettered without retry
- [ ] 429 with `Retry-After` → next attempt honours the header
- [ ] Timeout / `CalloutException` → treated as transient
- [ ] Duplicate event → converges on one row via the External Id
- [ ] 200-record bulk update → `Limits.getQueueableJobs()` is 1
- [ ] All callouts mocked with `MockHttpResponseGenerator`; no test hits a real endpoint

## Sign-Off

- [ ] No callout in any path that runs after DML in the same transaction
- [ ] `@future(callout=true)` is not being used as a delivery mechanism
- [ ] Delivery intent is persisted atomically with the record change
- [ ] Secret in an External Credential; endpoint via `callout:`
- [ ] Retry on 5xx / 408 / 429 only, with scheduled backoff
- [ ] Idempotency key on every request, and the receiver honours it
- [ ] Payload is an explicit field list carrying absolute state and a version
- [ ] DLQ depth **and** oldest-pending-age alerts exist
- [ ] Replay path tested, not just designed
- [ ] Outbox retention policy set and access restricted
