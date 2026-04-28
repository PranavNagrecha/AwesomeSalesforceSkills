---
name: apex-callout-retry-and-resilience
description: "Strategy layer for resilient Apex HTTP callouts: bounded retry with backoff, queueable async retry chains, circuit-breaker via Platform Cache, idempotency keys, dead-letter pattern. NOT for callout authentication — see apex-named-credentials-patterns. NOT for transaction-boundary rules — see callout-and-dml-transaction-boundaries. NOT a re-write of the HttpClient template — this is the policy and orchestration layer that calls it."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - apex
  - callout
  - retry
  - circuit-breaker
  - resilience
  - idempotency
  - dead-letter-queue
triggers:
  - "how to retry failed http callout in apex"
  - "exponential backoff for salesforce apex callout"
  - "circuit breaker pattern apex http endpoint"
  - "idempotency key on retried payment callout"
  - "dead letter queue for failed apex http calls"
  - "queueable chain for async retry of webhook"
inputs:
  - Target endpoint and method (GET/POST/PUT/DELETE)
  - Idempotency expectation (safe to retry vs not)
  - Failure modes observed (timeout, 5xx, 429, network)
  - Latency budget (sync vs async tolerable)
  - Volume (per-day callout count and 100-per-tx ceiling)
outputs:
  - Retry policy (attempts, backoff schedule, jitter)
  - Circuit-breaker configuration (threshold, cooldown, partition key)
  - Idempotency-Key strategy (header or dedup table)
  - Dead-letter sObject schema and reprocessing job
  - MockHttpResponseGenerator test sequence
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex Callout Retry and Resilience

Activate when an Apex integration must survive transient failures from a downstream system: 5xx errors, network timeouts, 429 rate limits, brief endpoint outages. This skill is the **strategy layer** — it tells you when to retry, how many times, on what schedule, when to stop, and where to park failures. The HTTP plumbing itself lives in `templates/apex/HttpClient.cls`.

## Before Starting

- Confirm the operation is **idempotent** (safe to repeat) before retrying writes. If not, an Idempotency-Key contract with the downstream is mandatory.
- Decide **sync vs async** up front. Synchronous retries fight a 120-second cumulative cap; async retries (Queueable / Platform Event) get a fresh transaction per attempt.
- Identify **what's retry-eligible** vs not. 5xx, network timeouts, 408, 429, 503 retry. 400, 401, 403, 404, 422 do NOT retry; these are caller bugs or auth failures.

## Core Concepts

### Retry classification

| Status / Failure | Retry? | Why |
|---|---|---|
| Network timeout, no response | Yes | Transient |
| 408 Request Timeout | Yes | Transient |
| 429 Too Many Requests | Yes (honor `Retry-After`) | Rate limit |
| 500, 502, 503, 504 | Yes | Server-side transient |
| 400, 422 | No | Caller payload bug |
| 401, 403 | No | Auth / authz; refresh token elsewhere |
| 404 | No | Resource doesn't exist |

### The Apex synchronous constraint

A synchronous Apex transaction has a **120-second cumulative callout cap** and **no usable `Thread.sleep`** (Apex offers no sleep primitive — busy-wait loops via `System.now()` polling are governor-killers and forbidden). This forces synchronous retries to be:

- **Bounded** — typical 3 attempts max.
- **Short-backoff** — 100ms / 500ms / 2000ms via the only legal "delay": staying inside the same callout's longer timeout, OR doing minimal CPU work between attempts.
- **Aware of the 100-callout-per-transaction limit** — every retry counts against it.

For real exponential backoff (seconds-to-minutes), go async.

### Async retry — Queueable chain or Platform Event

The right pattern for backoff > a few seconds:

1. First attempt fires sync (or from a Queueable).
2. On retryable failure, the Queueable enqueues itself with `attempt + 1` and a stored `nextAttemptAt`.
3. A Scheduled Apex job (or Platform Event subscriber) picks up the work when `nextAttemptAt <= now`.

Each retry runs in a **fresh transaction** with fresh governor limits. Backoff schedules of 1s / 5s / 30s / 5min are achievable.

### Circuit breaker

Track per-endpoint failure rate in `Cache.Org` (org-partition Platform Cache). Three states:

- **CLOSED** — calls flow normally; failures increment a counter.
- **OPEN** — counter exceeds threshold (e.g. 10 failures in 60 seconds); subsequent calls short-circuit and throw immediately. No callout consumed.
- **HALF-OPEN** — after a cooldown (e.g. 30 seconds), one probe call is allowed. Success returns state to CLOSED; failure returns to OPEN with a longer cooldown.

The cache key MUST be per-endpoint (e.g. `ckt:payment-api`), not global. One bad endpoint shouldn't blackhole every integration.

### Idempotency

For retryable **writes**, the downstream must dedup. Two patterns:

- **Idempotency-Key HTTP header** — generate a UUID, send it on every retry of the same logical operation. Downstream returns the original response on duplicate. Stripe, Square, and most modern payment APIs support this.
- **Salesforce-side dedup table** — `Outbound_Callout_Log__c` keyed by `(endpoint + payload_hash + minute_bucket)`. Before retrying, query the log; if already succeeded, skip.

### Dead-letter pattern

When retries exhaust (e.g. 5 attempts over 1 hour), write the failed payload to `Failed_Callout__c` with: endpoint, payload, last response, attempt count, last error. A scheduled job or admin UI can reprocess. **Without this, retries that exhaust silently disappear.**

### Governor budget reminder

- 100 callouts per transaction (sync or async). Retries count.
- 120s cumulative callout time per transaction.
- Platform Cache: 10MB org partition free; 1KB per cache entry recommended.

### Testing

`MockHttpResponseGenerator` can return a **sequence** of responses by storing call-count state in the mock class. Test patterns: 3 timeouts then success; 5 5xx triggering circuit-open; 4xx never retried.

## Recommended Workflow

1. Classify the integration: idempotent vs non-idempotent; sync vs async tolerable; latency budget.
2. Pick the retry policy: max attempts, backoff schedule, jitter (10-20% randomization to avoid thundering herd).
3. Decide circuit-breaker thresholds per endpoint and store config in Custom Metadata (`Callout_Resilience_Config__mdt`).
4. Implement Idempotency-Key generation (UUID per logical request, persisted on the source record so retries reuse it).
5. Design the dead-letter sObject and the reprocessing path (scheduled Apex + admin reprocess UI).
6. Write `MockHttpResponseGenerator` returning a sequence — assert retry count, circuit-open behavior, and dead-letter writes.
7. Deploy with circuit-breaker thresholds tuned conservatively; monitor `Failed_Callout__c` volume in week 1.

## Review Checklist

- [ ] 4xx responses (except 408/429) NEVER trigger retry
- [ ] Synchronous retry bounded to <= 3 attempts and total time < 120s
- [ ] Async retries use Queueable chain or Platform Event, not sync polling
- [ ] Circuit-breaker state stored per endpoint in `Cache.Org`, not as static var
- [ ] Idempotency-Key header sent for write operations, persisted on source record
- [ ] Dead-letter sObject populated on exhaustion; reprocessing path documented
- [ ] No `System.now()` busy-wait loops anywhere
- [ ] `Limits.getCallouts()` checked before issuing retry inside a transaction
- [ ] Test class with `MockHttpResponseGenerator` covers: success-on-retry, exhaustion-to-dead-letter, circuit-open, 4xx-not-retried

## Salesforce-Specific Gotchas

1. **120-second cumulative callout cap is HARD.** Three retries with 30s timeouts each plus backoff burns the budget fast. Measure actual P95 latency before sizing retries.
2. **Platform Cache keys are case-sensitive.** `ckt:Payment-Api` and `ckt:payment-api` are different breakers — pick a convention and lint it.
3. **`Limits.getCallouts()` is per-transaction, not per-class.** A trigger that fires three handlers each issuing 40 callouts will hit 100 even though no single class did.
4. **`Test.setMock` returns a single mock instance.** To return a sequence, store call-count state inside the mock class and switch on it.

## Output Artifacts

| Artifact | Description |
|---|---|
| Retry policy spec | Attempts, backoff, jitter, eligible status codes |
| Circuit-breaker config | Threshold, window, cooldown, partition key — per endpoint |
| Idempotency strategy | Header-based or dedup-table; key persistence rule |
| `Failed_Callout__c` schema | Dead-letter object + reprocessing job |
| Test class | MockHttpResponseGenerator with response-sequence support |

## Related Skills

- `apex/apex-named-credentials-patterns` — auth and endpoint config (NOT this skill)
- `apex/callout-and-dml-transaction-boundaries` — DML-then-callout ordering (NOT this skill)
- `apex/apex-queueable-patterns` — chaining queueables for async retry
- `apex/apex-platform-cache-patterns` — Cache.Org partitioning for circuit state
- `templates/apex/HttpClient.cls` — the underlying HTTP plumbing
