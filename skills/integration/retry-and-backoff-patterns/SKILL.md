---
name: retry-and-backoff-patterns
description: "Implementing resilient integration retry logic in Salesforce: exponential backoff, jitter, idempotency keys, dead-letter queues, and circuit breaker patterns for Apex callouts. Use when designing callout retry behavior, preventing thundering-herd issues, or handling persistent integration failures. NOT for Apex async patterns without callouts (use apex-queueable-patterns). NOT for callout governor limits (use callout-limits-and-async-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I retry a failed callout in Salesforce"
  - "exponential backoff pattern in Apex"
  - "prevent duplicate records when retrying integration"
  - "circuit breaker pattern for Salesforce callouts"
  - "dead letter queue pattern in Salesforce integration"
tags:
  - retry
  - backoff
  - idempotency
  - circuit-breaker
  - integration-resilience
inputs:
  - "Target external system endpoint and expected error codes (5xx, 429, timeouts)"
  - "Acceptable retry budget (max retries, max elapsed time)"
  - "Idempotency requirements of the external system"
  - "Whether the callout is synchronous (Apex trigger/controller) or already async (Queueable/Batch)"
outputs:
  - "Queueable Apex class with exponential backoff + jitter retry chain"
  - "Custom Metadata record definition for circuit breaker configuration"
  - "Failed_Integration_Log__c dead-letter custom object definition"
  - "Retry counter and idempotency key field design on the driving SObject"
dependencies:
  - callout-limits-and-async-patterns
  - apex-queueable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Retry and Backoff Patterns

This skill activates when a practitioner needs to implement resilient retry logic for Apex callouts — covering exponential backoff with jitter, idempotency via External Id upserts, dead-letter queue handling, and circuit breaker patterns using Custom Metadata. It does not cover native platform retry mechanisms (Outbound Messages, Platform Events) beyond documenting them as alternatives.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Execution context of the callout:** Is it currently synchronous (trigger, Visualforce, LWC controller)? If so, a retry loop in the same transaction is not viable — the callout must be moved to a Queueable first.
- **Idempotency of the target system:** Can the same payload be safely sent twice? If not, an External Id + upsert guard is mandatory before any retry is safe.
- **Governor limits already consumed:** Each Queueable re-enqueue counts against the org's daily async Apex limit (250,000 per 24 hours for most orgs). A burst retry storm can exhaust this budget.

---

## Core Concepts

### No Thread.sleep() in Apex — Use Queueable Chaining for Delay

Apex has no `Thread.sleep()` equivalent. Attempting a synchronous retry loop in the same transaction violates callout-after-DML rules and cannot introduce meaningful delay. The idiomatic pattern is **Queueable chaining**: when a callout fails, the Queueable job re-enqueues itself (via `System.enqueueJob()`) with an incremented retry counter. Each enqueue schedules a new async execution, not an immediate one. The platform schedules the next attempt based on worker availability, which naturally provides seconds-to-minutes of delay without explicit sleep.

### Exponential Backoff with Jitter

Exponential backoff calculates the delay between retries as `baseDelay * 2^retryCount`. Without jitter, every concurrent failing job wakes at the same moment and hammers the external system simultaneously — the **thundering-herd problem**. Adding jitter (`+ (Math.random() * baseDelay)`) scatters retry times across the time window. The base delay is typically 1–5 seconds, capped at a maximum (e.g., 60 seconds). Because Apex cannot enforce exact timing, the delay calculation is stored as metadata on the retry job and logged, but the actual elapsed time depends on Queueable scheduling.

### Idempotency Key via External Id Upsert

On retry, the same payload may be sent and accepted by the external system, but if the original request succeeded and only the response was lost (network timeout), a naive retry creates a duplicate. The defense is to assign a **stable idempotency key** before the first attempt — typically a UUID stored in `External_Id__c` on the driving record — and pass it as a request header or body field. On the Salesforce side, use `upsert` on `External_Id__c` to prevent duplicate SObject creation from reprocessing. The key must survive retries unchanged.

### Max Retry Guard and Dead-Letter Queue

Every retry implementation must have an explicit maximum retry count (3–5 is typical). When `retryCount >= maxRetries`, the job must not re-enqueue. Instead, write a **dead-letter record** — a `Failed_Integration_Log__c` custom object capturing the payload, error message, HTTP status, retry count, and timestamp — and optionally fire an alert (Platform Event or email). Without this guard, a permanently failing integration exhausts the async Apex limit silently.

---

## Common Patterns

### Pattern 1: Queueable Retry Chain with Exponential Backoff

**When to use:** An Apex callout fails with a transient error (HTTP 429, 503, or timeout) and must be retried automatically with increasing delay.

**How it works:**

1. The initial callout attempt is made from a Queueable `execute()` method.
2. On failure, increment `retryCount` on the job instance. Calculate `delaySeconds = baseDelay * Math.pow(2, retryCount) + (Math.random() * baseDelay)`.
3. If `retryCount < maxRetries`, call `System.enqueueJob(new RetryCalloutJob(payload, retryCount, maxRetries))`.
4. If `retryCount >= maxRetries`, write a `Failed_Integration_Log__c` record and stop.

**Why not a for-loop retry in the same transaction:** Each `Http.send()` call consumes a callout from the 100-per-transaction limit. More critically, you cannot introduce real delay in a synchronous loop, so you just hammer the endpoint repeatedly in milliseconds — worse than no retry.

### Pattern 2: Circuit Breaker via Custom Metadata

**When to use:** An external system is degraded for extended periods. Rather than retrying every call and burning async limits, a circuit breaker detects open-circuit state and skips the callout entirely until the system recovers.

**How it works:**

1. Create a `Circuit_Breaker_Config__c` Custom Metadata record with fields: `Is_Open__c` (Boolean), `Opened_At__c` (DateTime), `Cool_Down_Minutes__c` (Number).
2. At the start of the Queueable `execute()`, query (or cache via a static variable) the CMDT record.
3. If `Is_Open__c = true` AND `Opened_At__c + Cool_Down_Minutes__c > now`, skip the callout and write a log entry.
4. If the cool-down has elapsed, treat the circuit as half-open: attempt one callout. Success → flip `Is_Open__c = false` (via an Apex `update` or a named flow). Failure → keep open and reset `Opened_At__c`.
5. Toggling `Is_Open__c` manually also enables operators to manually open or close the circuit without a code deploy.

**Why not a flag on a custom object:** CMDT records are cached at the platform level and do not consume SOQL queries per transaction (after the first load in a request). Custom objects do.

### Pattern 3: Idempotency Key Guard

**When to use:** The external system does not natively deduplicate requests (no idempotency-key header support), and a duplicate call creates duplicate data.

**How it works:**

1. Before the first callout attempt, generate `String idempotencyKey = [String UUID or ExternalId from driving record]`.
2. Include the key in the request body or a custom header (`X-Idempotency-Key`).
3. On the Salesforce side, use `Database.upsert(record, Schema.SObject.Fields.External_Id__c, false)` to prevent double-insert on reprocessing.
4. Log the key on `Failed_Integration_Log__c` so support teams can trace retried requests.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Callout fails in a trigger or LWC controller | Move callout to Queueable first, then add retry chain | Synchronous context cannot support delay or re-attempt patterns |
| Transient HTTP 429 or 503 error | Queueable retry chain with exponential backoff + jitter | Handles temporary unavailability without thundering-herd |
| Timeout (no HTTP response received) | Retry with idempotency key — success confirmation is unknown | Without idempotency key, retry may double-process |
| External system down for hours | Circuit breaker via CMDT + dead-letter log | Retrying endlessly burns async Apex quota for no benefit |
| Max retries exceeded | Write Failed_Integration_Log__c and alert | Enables manual intervention; prevents silent data loss |
| Outbound Messages or Platform Events | Use native retry — no Apex needed | Outbound Messages retry for up to 24 hours; Platform Events replay for 3 days |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner implementing retry logic for an Apex callout:

1. **Confirm execution context:** Verify that the callout is already in a Queueable or Batch context. If it originates from a trigger or controller, extract it to a Queueable job first before adding retry logic.
2. **Define retry parameters:** Decide `maxRetries` (3–5), `baseDelaySeconds` (1–5), and `maxDelaySeconds` (30–60). Document these as Custom Metadata fields in `Retry_Config__mdt` so they can be adjusted without a deploy.
3. **Add retry counter and idempotency key fields:** Add `Retry_Count__c` (Integer, default 0) and `Integration_Idempotency_Key__c` (Text, External Id) to the driving SObject. Populate the idempotency key before the first enqueue.
4. **Implement the Queueable retry chain:** In the `execute()` method, wrap the callout in a try-catch. On caught exceptions or non-2xx responses, increment the counter, calculate backoff delay (for logging/metadata — actual delay comes from Queueable scheduling), and re-enqueue if under the limit.
5. **Implement the dead-letter path:** When `retryCount >= maxRetries`, insert a `Failed_Integration_Log__c` record with payload, error, HTTP status, retry count, and timestamp. Optionally publish a Platform Event to notify an operations flow.
6. **Add the circuit breaker check:** At the start of `execute()`, read `Circuit_Breaker_Config__mdt`. If the circuit is open and cool-down has not elapsed, log and return without attempting the callout.
7. **Test failure modes explicitly:** Write Apex tests that mock HTTP 429, 503, and timeout responses. Assert that retry count increments, dead-letter records are written at max retries, and idempotency keys are preserved across re-enqueues.

---

## Review Checklist

Run through these before marking integration retry work complete:

- [ ] Callout is in a Queueable or Batch context — no synchronous retry loops
- [ ] `maxRetries` is explicitly defined and enforced — no unbounded retry possible
- [ ] Exponential backoff formula is present with jitter (`Math.random()`)
- [ ] Idempotency key (`External_Id__c`) is generated before first attempt and passed in the request
- [ ] Dead-letter path writes `Failed_Integration_Log__c` when max retries exceeded
- [ ] Circuit breaker CMDT flag is checked before each callout attempt
- [ ] Apex tests mock all failure scenarios (429, 503, timeout) and assert dead-letter creation
- [ ] Retry config (maxRetries, baseDelay) is in Custom Metadata — not hardcoded

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Queueable re-enqueue does not guarantee delay** — `System.enqueueJob()` schedules the job for the next available worker, which may be seconds or minutes later. You cannot control the exact retry interval. Document this for stakeholders: the backoff delay is approximate, not guaranteed.
2. **Callout-after-DML rule applies inside Queueable** — If you write a `Failed_Integration_Log__c` record (DML) and then attempt a callout in the same `execute()` method, you hit the "callout after uncommitted work" exception. Always perform DML after the callout block, or use a separate inner Queueable for the logging path.
3. **Daily async Apex limit is shared across all jobs** — Unlimited retry storms (e.g., a broken endpoint during peak processing) can consume the 250,000 daily Queueable executions, blocking all other background processing. The `maxRetries` guard and circuit breaker are critical safety valves, not optional.
4. **`System.enqueueJob()` is limited to 50 per transaction** — A batch of failing records all trying to enqueue retry jobs in the same transaction will hit this limit. Design retry logic so each job re-enqueues itself (1 per transaction), not so a parent job enqueues N children.
5. **Native platform retries are separate from Apex retries** — Outbound Messages retry automatically for up to 24 hours at platform-managed intervals. Platform Events can be replayed for up to 3 days. Do not add Apex retry logic on top of these — it results in double-processing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `RetryCalloutJob.cls` | Queueable Apex class implementing exponential backoff + jitter + dead-letter path |
| `Circuit_Breaker_Config__mdt` | Custom Metadata type for per-integration circuit breaker state |
| `Retry_Config__mdt` | Custom Metadata type for maxRetries, baseDelay, maxDelay per integration |
| `Failed_Integration_Log__c` | Custom object for dead-letter records with payload, error, and retry metadata |
| `RetryCalloutJobTest.cls` | Apex test class covering happy path, max retries, and circuit open scenarios |

---

## Related Skills

- `callout-limits-and-async-patterns` — governor limits on callouts (100 per transaction, daily async limits); complements retry design
- `apex-queueable-patterns` — Queueable chaining patterns without callouts; prerequisite for understanding the async execution model
- `named-credentials-setup` — configuring Named Credentials for the endpoint used in retried callouts
- `integration-framework-design` — higher-level integration architecture decisions where retry strategy is one component
