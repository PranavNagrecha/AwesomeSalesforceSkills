---
name: outbound-webhook-from-salesforce
description: "Use when Salesforce must POST a webhook to a third-party endpoint after a record change — with signed payloads, retries, dead-lettering, rate limits, and idempotency. Covers design choice between Outbound Message, Flow HTTP Callout, Apex Queueable callout, and Event Relay. NOT for receiving a webhook INTO Salesforce from an external system — use integration/webhook-inbound-patterns. NOT for the Workflow-triggered SOAP Outbound Message and its listener contract — use integration/outbound-messages-and-callbacks."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "salesforce send webhook"
  - "outbound http from salesforce"
  - "webhook retry salesforce"
  - "signed webhook hmac salesforce"
  - "flow http callout alternative"
tags:
  - integration
  - webhook
  - callout
  - outbound
  - reliability
inputs:
  - Triggering event (record change, platform event, scheduled)
  - Target endpoint + auth requirement
  - Volume and latency SLA
  - Failure tolerance + compliance requirements
outputs:
  - Webhook design (producer pattern, payload shape, signing, retry)
  - Failure handling + dead-letter
  - Observability plan
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Outbound Webhook From Salesforce

A webhook out of Salesforce is a callout with a delivery guarantee bolted on.
Every design decision here follows from one platform fact and one distributed-
systems fact, and teams that skip either build something that works in the
sandbox and loses events in production.

**The platform fact:** *"You can't make a callout when there are pending
operations in the same transaction. Things that result in pending operations are
DML statements, asynchronous Apex (such as future methods and batch Apex jobs),
scheduled Apex, or sending email."* A record change is a DML statement. So the
callout cannot happen in the transaction that caused it — the only question is
which async mechanism carries it.

**The distributed-systems fact:** the receiver can be slow, down, or lying about
success. At-least-once delivery with idempotency is the only guarantee you can
actually offer, and it has to be designed in, not added after the first incident.

| Concern | Established by | Fails when |
|---|---|---|
| **The event escapes the transaction** | Async boundary (Queueable, Platform Event, Scheduled Path) | The callout is attempted inline after DML |
| **Delivery survives a bad hour** | Retry with backoff + a durable outbox row | Retry is a `for` loop inside one transaction |
| **The receiver can trust it** | HMAC over a timestamped payload, secret in an External Credential | The secret is in Custom Metadata or in code |
| **Nothing is processed twice** | An idempotency key the *receiver* honours | You assume exactly-once because retries look rare |
| **You find out when it breaks** | Outbox status + a DLQ depth alert | Failures are logged and nobody reads logs |

**Scope.** This skill owns the *producer* side: picking the mechanism, shaping
the payload, signing it, retrying it, and knowing when it is dead. Receiving a
webhook into Salesforce is `integration/webhook-inbound-patterns`; verifying an
inbound signature is `integration/webhook-signature-verification`. The
Workflow-triggered SOAP Outbound Message and its listener WSDL contract belong to
`integration/outbound-messages-and-callbacks` — it appears below only as one
option in the mechanism choice.

Read `standards/decision-trees/integration-pattern-selection.md` (Direction 1,
Q1–Q4) before choosing. This skill implements that tree's outcome; it does not
re-derive it.

---

## Before Starting

1. **Establish whether the receiver is idempotent.** Ask, in writing, what
   happens if they receive the same event twice. If the answer is "it would
   duplicate the order", the design needs an idempotency key *they honour* — and
   agreeing that is a contract negotiation, not a code change.

2. **Get the failure budget.** "How many events may be lost, and how stale may a
   delivery be?" A five-minute tolerance and a zero-loss requirement produce
   completely different designs. Nobody volunteers this; you have to ask.

3. **Classify the volume in events per minute at peak**, not per day. A daily
   average hides the mass update that generates 50,000 events in ninety seconds,
   and that burst is what the design has to survive.

4. **Decide who owns the secret and how it rotates.** External Credential, not
   Custom Metadata, not Apex source. Rotation is a Setup change if you get this
   right and a deployment if you do not.

5. **Find out whether ordering matters.** If the receiver applies deltas rather
   than absolute state, out-of-order delivery corrupts them — and every retrying
   design reorders. The cheap fix is to send absolute state plus a version
   number, and it is much cheaper to agree now.

---

## Core Concepts

### Callouts and the transaction boundary

The rule is absolute and it decides the architecture: a callout is illegal once
the transaction has pending work. A trigger has, by definition, pending DML. So
the shapes available are:

```text
Record change ──► Trigger / Flow
                     │
                     ├─► Queueable (Database.AllowsCallouts)   ← the workhorse
                     ├─► Platform Event ──► subscriber ──► callout
                     └─► After-save Flow + Scheduled Path (≥ 1 min) ──► HTTP Callout action
```

The relevant per-transaction ceilings, from the Apex Developer Guide:

| Limit | Value |
|---|---|
| Callouts per transaction | 100 |
| Cumulative callout timeout per transaction | 120 seconds |
| Default timeout per callout | 10 seconds |
| Configurable timeout per callout | 1 ms – 120,000 ms |
| Concurrent callouts outside the org's domain (Developer Edition) | 20 |

The 120-second cumulative budget is the one that bites. Twelve callouts at the
10-second default exhaust it, so a Queueable that loops over deliveries needs a
bounded batch size and a per-callout timeout small enough that the batch fits.

### The outbox is the design

Everything that makes this reliable — retry, backoff, dead-lettering, replay,
observability — hangs off one durable row per delivery attempt. Without it, a
retry is a loop inside a transaction that cannot outlive its own governor limits,
and a failure is a debug log nobody reads.

```text
Webhook_Delivery__c
    Idempotency_Key__c   External Id, Unique   ← the whole idempotency story
    Status__c            Pending | Sent | Failed | Dead
    Attempt_Count__c
    Next_Attempt_At__c                          ← the sweeper's index
    Payload__c           Long Text
    Last_Status_Code__c
    Last_Error__c
```

Write the row in the same transaction as the record change (it is DML, which is
legal there) and deliver it from a Queueable. The record change and the
*intent to deliver* commit or roll back together; the delivery itself is
asynchronous and retryable. That is the whole pattern.

### Retry: a Finalizer, not a loop

`System.Finalizer` is the platform's answer to "the async job failed and I need
to react". Attach one inside a Queueable's `execute`, and it runs afterwards
whether or not the job threw:

- `System.attachFinalizer(Finalizer)` — **"Only one finalizer instance can be
  attached to any Queueable job."**
- `FinalizerContext.getResult()` returns `System.ParentJobResult` — `SUCCESS` or
  `UNHANDLED_EXCEPTION` — and `getException()` returns the exception in the
  second case.
- **"A Queueable job that failed due to an unhandled exception can be
  successively re-enqueued five times by a transaction finalizer."** The counter
  resets on success.

Five is a hard ceiling for finalizer-driven retry, which is exactly why long
backoff schedules belong to a scheduled sweeper reading `Next_Attempt_At__c`
rather than to finalizer chaining.

For the short end of the schedule, `System.enqueueJob` accepts a delay of 0–10
minutes and an `AsyncOptions` overload carrying `MaximumQueueableStackDepth`;
`System.AsyncInfo` exposes `getCurrentQueueableStackDepth()` and
`getMaximumQueueableStackDepth()` at runtime. Note the chaining constraint:
"you can add only one job from an executing job. Only one child job can exist for
each parent queueable job", and Developer Edition and Trial orgs cap the chained
stack depth at 5.

### Signing

HMAC-SHA256 over `"{timestamp}.{body}"` is the de-facto industry shape and the
one receivers already have libraries for. Two Salesforce-specific points:

- The secret belongs in a **Named Credential's External Credential**, referenced
  from the request with the documented merge syntax
  (`{!$Credential.<AuthProviderName>.<ParameterName>}` and
  `{!$Credential.Password}`), so that rotation is a Setup change. "Salesforce
  manages all authentication for Apex callouts that specify a named credential as
  the callout endpoint so that your code doesn't have to."
- Sign the **exact bytes you send**. If you serialize once for the signature and
  again for the body, key order can differ and the receiver rejects everything.
  Serialize to a `String` once; sign that string; send that string.

The mirror-image skill for the receiving end is
`integration/webhook-signature-verification` — read it to know what a competent
receiver will check, because that is what you have to produce.

### Mechanism comparison, with the numbers

| Mechanism | Async? | Retry | Auth | Signing | Verdict |
|---|---|---|---|---|---|
| **Apex Queueable + `HttpClient`** | Yes | Yours: Finalizer + outbox sweeper | Named Credential, all protocols | Full control | Default for anything with a reliability requirement |
| **Flow HTTP Callout** | Only via Scheduled Path or async path | None built in | Named Credential (required) | Not practical declaratively | Low-volume, admin-owned, tolerant receivers |
| **Platform Event + Apex subscriber** | Yes, by construction | Subscriber-side | Named Credential | Full control | When several consumers want the same signal |
| **Event Relay → Amazon EventBridge** | Yes | AWS-side | Named Credential holding AWS account info | AWS-side | AWS-native fleets; not a way to call one HTTPS endpoint |
| **Outbound Message (SOAP)** | Yes | Platform: exponential backoff to 2 h, dropped at 24 h | Session ID / mTLS only | None | Legacy. Its host reached end of support 31 Dec 2025 |

Outbound Messaging's semantics are worth knowing precisely, because they are the
bar the Apex design has to clear: "A single SOAP message can include up to 100
notifications"; "If a message can't be delivered, the interval between retries
increases exponentially, up to a maximum of two hours between retries"; "messages
stay in the queue until sent successfully, or until they're 24 hours old. After
24 hours, messages are dropped from the queue"; and — the one that surprises
people — "Messages are retried independent of their order in the queue. As a
result, messages can be delivered out of order."

Event Relay is a genuinely different shape rather than a webhook alternative.
`EventRelayConfig` (API 56.0+, suffix `.eventRelay`) requires
`destinationResourceName` — "the developer name of the named credential, which
stores the AWS account information" — and an `eventChannel`. It relays platform
events and change data capture events to Amazon EventBridge. If the requirement
is "POST to a partner's HTTPS endpoint", this is the wrong tool; if it is "fan
our events into an AWS estate", it removes a whole layer of your code.

---

## Common Patterns

### Pattern A — outbox + Queueable + Finalizer

The default. Trigger writes a `Webhook_Delivery__c` row and enqueues; the
Queueable delivers a bounded batch; a Finalizer catches unhandled failures and
re-enqueues up to the platform's five; a scheduled sweeper picks up anything with
`Next_Attempt_At__c` in the past. Full implementation in
[`references/examples.md`](references/examples.md), Examples 1–3.

### Pattern B — Platform Event as the fan-out point

When more than one consumer wants "an order closed", publish once and let
subscribers callout independently. Note the limit split: with **Publish After
Commit**, "Each method execution is counted as one DML statement against the Apex
DML statement limit"; with **Publish Immediately**, "Each method execution is
counted against a separate event publishing limit of 150 `EventBus.publish()`
calls". `Limits.getPublishImmediateDML()` reads the second.

### Pattern C — Flow HTTP Callout for the low-volume, admin-owned case

Flow Builder generates an External Service registration and an invocable action
from the API's response shape, and requires an External Credential and a Named
Credential. It is a legitimate choice when volume is low, the receiver is
tolerant, and the integration should be owned by an admin — and it is the wrong
choice the moment a retry or a signature is required, because neither is
expressible declaratively.

### Pattern D — notification-plus-pull

When the payload is large or sensitive, send an event that carries only an
identifier and let the receiver fetch the body over an authenticated API. This
removes payload size from your problem, removes PII from the outbox, and turns
"replay a delivery" into "they call again".

### Pattern E — absolute state plus a version, never a delta

Because every retrying design reorders, `{"status":"Closed","version":47}` is
safe to apply twice and out of order; `{"statusDelta":"+1"}` is not. This is a
payload-design decision that buys you out of an entire class of production
incident, and it costs nothing at build time.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Any receiver with a reliability requirement | Outbox + Queueable + Finalizer + sweeper |
| Low volume, admin-owned, tolerant receiver | Flow HTTP Callout + Named Credential |
| Several internal consumers of the same signal | Platform Event, subscribers call out |
| Destination is an AWS estate | Event Relay → EventBridge |
| Existing Outbound Message | Migrate; its host hit end of support 31 Dec 2025 |
| Receiver cannot deduplicate | Negotiate an idempotency key before writing code |
| Ordering matters to the receiver | Absolute state + version, or a single-threaded chain |
| Payload > a few hundred KB, or contains PII | Notification-plus-pull |
| Burst of 10,000+ events from a mass update | Outbox + sweeper with a bounded batch; never one Queueable per record |
| Receiver returns 429 with `Retry-After` | Honour the header; it overrides your backoff schedule |
| Receiver returns 4xx (not 408/429) | Dead-letter immediately; retrying a rejection wastes the budget |
| Secret rotation required | External Credential; the code never changes |

---

## Recommended Workflow

1. **Route with the decision tree first.** Read
   `standards/decision-trees/integration-pattern-selection.md`, Direction 1,
   Q1–Q4, and cite the branch that resolved the choice. Q4 in particular already
   distinguishes transient-5xx retry, 429 throttling, idempotency keys, and
   ordering sensitivity.
2. **Design the outbox object before the sender**: idempotency key as an External
   Id, Unique field; status; attempt count; next-attempt timestamp; payload;
   last status code and error. Everything else in this design hangs off it.
3. **Write the delivery row in the triggering transaction and nothing else.** No
   callout there — the platform forbids it once DML is pending, and the failure
   mode is a `CalloutException` in a trigger, which rolls back the user's save.
4. **Deliver from a Queueable implementing `Database.AllowsCallouts`**, with a
   bounded batch sized against the 120-second cumulative timeout and an explicit
   per-callout timeout. Use
   [`templates/apex/HttpClient.cls`](../../../templates/apex/HttpClient.cls) —
   it already carries Named Credential enforcement, timeouts, and transient
   classification.
5. **Attach a `Finalizer` for unhandled failures** and keep the long backoff in a
   scheduled sweeper. The finalizer path is capped at five successive
   re-enqueues; the sweeper is not.
6. **Sign the exact serialized string you send**, with the secret in an External
   Credential, and give the receiver the timestamp they need to bound replay.
   Never log the payload or the signature.
7. **Instrument the outbox, not the code path.** Alert on DLQ depth and on
   oldest-pending age. A dashboard of `Status__c` by hour answers "is it working"
   without reading a single log, and a rising oldest-pending age is the earliest
   signal that the receiver is degrading.

---

## Review Checklist

- [ ] No callout in any code path that runs after DML in the same transaction
- [ ] Delivery intent is persisted in the triggering transaction, atomically with the change
- [ ] Idempotency key is an External Id, Unique field, and is sent to the receiver
- [ ] The receiver has confirmed, in writing, that they honour that key
- [ ] Queueable implements `Database.AllowsCallouts`
- [ ] Batch size × per-callout timeout fits inside the 120-second cumulative budget
- [ ] Per-callout timeout is set explicitly, not left at the 10-second default
- [ ] Retry distinguishes transient (5xx, 408, 429) from permanent (other 4xx)
- [ ] `Retry-After` is honoured where the receiver sends it
- [ ] Backoff is scheduled, not slept; no busy-wait inside a transaction
- [ ] Finalizer re-enqueues are bounded, and the design knows the platform cap is five
- [ ] Dead-letter state exists and is distinguishable from "still retrying"
- [ ] Endpoint is `callout:<NamedCredential>/...`; no hostname in code
- [ ] Signing secret is in an External Credential, never in Custom Metadata or source
- [ ] The signed bytes and the sent bytes are the same `String` instance
- [ ] Payload carries a schema version and a correlation id
- [ ] Payload is absolute state with a version, not a delta
- [ ] Nothing logs the payload, the signature, or any credential
- [ ] Alerting exists on DLQ depth **and** on oldest-pending age
- [ ] Tests use `MockHttpResponseGenerator`; no test touches a real endpoint
- [ ] A mass-update burst has been modelled, not assumed

---

## Salesforce-Specific Gotchas

Full detail in [`references/gotchas.md`](references/gotchas.md).

1. **"You can't make a callout when there are pending operations"** — the rule that shapes everything.
2. **120 seconds cumulative per transaction**, so twelve default-timeout callouts exhaust a Queueable.
3. **`Database.AllowsCallouts` is a marker you have to remember**, and forgetting it fails at runtime.
4. **Only one finalizer per Queueable**, and five successive finalizer re-enqueues.
5. **`Test.setMock` plus DML ordering** makes the callout-after-DML rule bite in tests too.
6. **Platform Event publish behaviour changes which limit you consume.**
7. **A retried delivery is a reordered delivery** — always, in every design.
8. **HTTP 200 is not "processed"** unless the receiver's contract says so.
9. **Outbound Messages drop silently at 24 hours** and deliver out of order by design.
10. **Flow HTTP Callout has no retry**, and adding one means leaving Flow.
11. **Serializing twice produces two different strings** and a signature the receiver rejects.
12. **One Queueable per record does not survive a mass update.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Mechanism decision record | The chosen option, the decision-tree branch that produced it, and the volume/SLA/ordering facts behind it |
| Receiver contract note | Endpoint, auth, idempotency key semantics, signature scheme, what their 2xx means, and their documented rate limit |
| Outbox object | `Webhook_Delivery__c` with External Id, Unique idempotency key, status, attempt count, next-attempt time, payload, last error — plus a retention policy |
| Producer | Trigger or Flow writing the delivery row; Queueable with `Database.AllowsCallouts` delivering a bounded batch |
| Retry design | Backoff schedule, which status codes retry, `Retry-After` handling, finalizer role, and the dead-letter threshold |
| Named + External Credential | The endpoint and the signing secret, with a rotation runbook that requires no deployment |
| Payload schema | Versioned, absolute-state, with correlation id and idempotency key; documented for the receiver |
| Observability | Outbox status dashboard, DLQ depth alert, oldest-pending-age alert, and the replay procedure |
| Test suite | `MockHttpResponseGenerator` cases for 2xx, 5xx-then-success, 4xx-permanent, 429 with `Retry-After`, timeout, and a bulk burst |

---

## Related Skills

- `integration/webhook-signature-verification` — the receiving end of the
  signature you are producing; read it to know what a competent receiver checks
- `integration/webhook-inbound-patterns` — the mirror direction, when the partner
  is the one pushing to you
- `integration/outbound-messages-and-callbacks` — the legacy SOAP Outbound
  Message and its listener WSDL contract, if you are migrating one
- `integration/retry-and-backoff-patterns` — the general backoff and
  dead-lettering treatment this skill applies to webhooks specifically
- `integration/event-relay-configuration` — Event Relay to Amazon EventBridge in
  full, when the destination is an AWS estate rather than an HTTPS endpoint
- `apex/callout-limits-and-async-patterns` — the per-transaction callout budget
  and which async shape fits inside it
- `standards/decision-trees/integration-pattern-selection.md` — Direction 1,
  Q1–Q4: the routing this skill implements rather than re-derives

## Related Templates

- `templates/apex/HttpClient.cls` — Named-Credential-aware client with timeout,
  transient classification, and retry already implemented
- `templates/apex/ApplicationLogger.cls` — the queryable log this design's
  observability depends on
- `templates/apex/tests/MockHttpResponseGenerator.cls` — the only acceptable way
  to test a callout
