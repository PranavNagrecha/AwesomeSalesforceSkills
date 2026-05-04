---
name: apex-event-bus-subscriber
description: "Apex Platform Event subscriber runtime semantics — checkpoint-and-resume via `EventBus.TriggerContext.setResumeCheckpoint`, `EventBus.RetryableException` semantics, the 2,000-event-per-trigger default batch (10× standard DML trigger size), and `PlatformEventSubscriberConfig` for batch-size + running-user tuning. Covers the checkpoint-vs-RetryableException decision (the most common subscriber bug). NOT for declaring Platform Events themselves (use platform_events_definition skill), NOT for publishing them (apex/platform-event-publish), NOT for the basic `trigger Foo on MyEvent__e (after insert)` syntax."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "platform event apex trigger checkpoint resume replayid"
  - "eventbus retryableexception batch retry limit"
  - "platform event subscriber 2000 events governor limit"
  - "platformeventsubscriberconfig batch size running user"
  - "apex event bus subscribe programmatic api"
  - "platform event trigger 9 retries gives up"
tags:
  - platform-events
  - eventbus
  - subscriber
  - trigger
  - retry
  - replay
  - checkpoint
inputs:
  - "Platform Event SObject (e.g. `MyEvent__e`) the trigger subscribes to"
  - "Failure modes the subscriber must handle (transient infra, permanent bad payload, partial-batch failures)"
  - "Whether the event volume justifies tuning the batch size away from the 2,000 default"
  - "Whether a non-default running user is needed (e.g. an integration user with broader access)"
outputs:
  - "Idiomatic Platform Event trigger with `setResumeCheckpoint` after each successful event"
  - "Decision: when to throw `RetryableException` vs let an uncaught exception resume from checkpoint"
  - "`PlatformEventSubscriberConfig` metadata XML when default batch / user is wrong"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Apex Event Bus Subscriber

Subscribing to Platform Events from Apex looks deceptively like writing a
DML trigger. It isn't. The runtime semantics — batch size, error handling,
position tracking, retry budget — are all different from `before insert` /
`after insert` triggers, and getting them wrong is the most common
production bug in Platform Event subscribers.

This skill is the runtime-semantics layer. The basic `trigger Foo on
MyEvent__e (after insert) { ... }` syntax is plain Apex; go to the Apex
Developer Guide. Publishing events (`EventBus.publish`) lives in
`apex/platform-event-publish`. Defining the event SObject itself lives
in admin / metadata. This skill assumes you already have a trigger and
you need to make it production-grade.

---

## Before Starting

- **There is no programmatic `EventBus.subscribe()` API.** The only
  supported Apex subscriber mechanism is an `after insert` trigger on
  the Platform Event SObject. If you've seen `EventBus.subscribe(...)`
  in pseudocode, that pattern doesn't compile. (For programmatic
  subscribe-from-outside, use the Pub/Sub API from a non-Apex
  client.)
- **The default batch size is 2,000 events per trigger invocation,
  not 200.** This is 10× a standard DML trigger's batch. Every
  governor budget your code touches (CPU time, SOQL queries, DML
  rows) needs to size against 2,000.
- **Decide your retry strategy before writing the trigger body.** The
  three options interact: checkpoint + uncaught-exception resume, vs
  `RetryableException` re-fire, vs do-nothing (drop the event on
  error). Mixing them carelessly is the #1 production bug.

---

## Core Concepts

### The trigger contract

```apex
trigger MyEventSubscriber on MyEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (MyEvent__e e : Trigger.new) {
        try {
            handleEvent(e);
            // Mark this event processed. If we throw later, we resume AFTER this one.
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (TransientException ex) {
            throw new EventBus.RetryableException(
                'Transient failure on ' + e.ReplayId + '; re-fire batch', ex
            );
        } catch (PermanentException ex) {
            // Log + skip; the rest of the batch should proceed.
            ApplicationLogger.error('Bad event ' + e.ReplayId, ex);
            ctx.setResumeCheckpoint(e.ReplayId);
        }
    }
}
```

Three things are happening here that don't happen in a DML trigger:

1. `EventBus.TriggerContext.currentContext()` — gives you the per-batch state object, including `getEventsRemaining()` (count) and `setResumeCheckpoint(replayId)` (position marker).
2. `setResumeCheckpoint(e.ReplayId)` — *after* each successfully-processed event, set the checkpoint. On uncaught exception, the trigger re-fires from the event AFTER this checkpoint (skipping already-processed events).
3. `EventBus.RetryableException` — explicit retry signal. Throws the **whole batch** back to be re-fired, up to 9 times (10 attempts total). After 10 attempts the trigger gives up and the events are lost.

### Three retry strategies and when to use each

| Strategy | Mechanism | Behavior on failure |
|---|---|---|
| **Checkpoint + uncaught exception** | `setResumeCheckpoint` after each success; let other exceptions propagate | Trigger re-fires from event AFTER the checkpoint (already-processed events are skipped). Up to 9 retries on the *unprocessed* slice. |
| **Explicit RetryableException** | `throw new EventBus.RetryableException(...)` | Whole batch re-fires (including already-processed events). Idempotency required. Up to 9 retries on the *whole* batch. |
| **Drop on error** | catch + log + `setResumeCheckpoint` | Move past the bad event, do not re-fire. Right for permanent / poison-pill events. |

The most common bug is using `RetryableException` *without*
`setResumeCheckpoint` first. Result: every uncaught failure re-fires
the whole 2,000-event batch, processed events are reprocessed, and
governor budget is multiplied by 10.

### `PlatformEventSubscriberConfig` for tuning

The default 2,000 batch is too large for many real workloads. Tune via
metadata:

```xml
<!-- MyEventSubscriber.platformEventSubscriberConfig-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventSubscriberConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <batchSize>200</batchSize>
    <masterLabel>MyEventSubscriber</masterLabel>
    <platformEventConsumer>MyEventSubscriber</platformEventConsumer>
    <user>integration.user@example.com</user>
</PlatformEventSubscriberConfig>
```

Two knobs that matter:

- **`batchSize`** — 1 to 2,000. Drop below 2,000 if your trigger body's CPU / SOQL / DML budget can't handle a full batch.
- **`user`** — the running user for the trigger. Default is the user who created the configured event; usually the wrong user for production. Set explicitly to a dedicated integration user with the right permissions.

---

## Common Patterns

### Pattern A — Checkpointed forward processing

**When to use.** Mostly-independent events; failure on one shouldn't
block others; transient infra issues should be retried automatically.

```apex
trigger OrderEventSubscriber on OrderEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (OrderEvent__e e : Trigger.new) {
        try {
            new OrderProcessor().handle(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (DmlException dml) {
            // Permanent: bad event payload. Log and skip.
            ApplicationLogger.error('Bad OrderEvent', dml);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (CalloutException callout) {
            // Transient: external system unreachable. Bail and let the
            // platform retry from this checkpoint.
            throw callout;  // uncaught — checkpoint advances are preserved
        }
    }
}
```

The trigger re-fires on the unprocessed slice if a `CalloutException`
fires. Permanent failures are logged + skipped. Transient failures get
9 retries on shrinking slices.

### Pattern B — All-or-nothing with explicit retry

**When to use.** Events must be processed as a transactional batch
(e.g. accounting balance updates). Idempotent or guarded by an
external dedup key.

```apex
trigger LedgerEventSubscriber on LedgerEvent__e (after insert) {
    try {
        Ledger.applyBatch(Trigger.new);  // all-or-nothing
    } catch (TransientException ex) {
        throw new EventBus.RetryableException('Re-fire ledger batch', ex);
    }
}
```

No checkpoint — the batch is the unit of work. RetryableException
fires the whole batch up to 9 more times. After 10 total attempts the
events are lost; an idempotency key on each event lets you reprocess
from a dead-letter store.

### Pattern C — Tuned batch size for heavy work

**When to use.** Trigger body does substantial CPU work (rich text
parsing, regex on large payloads) and a 2,000-event batch blows the
CPU governor.

Step 1 — measure. Run a representative batch and confirm the CPU
budget hit.

Step 2 — tune via `PlatformEventSubscriberConfig` (see XML above).
A common starting point is 200 (matching DML-trigger intuition);
optimize from there.

Step 3 — re-measure. Don't tune below what one event's worth of work
would handle; below ~50 events per batch, per-batch overhead
dominates.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Default trigger written, no checkpoint, no try/catch | **Add `setResumeCheckpoint(e.ReplayId)` after each success** | Without it, an uncaught exception re-fires from the START of the batch every retry — repeated processing of already-handled events |
| Transient failure mode (callout timeout, lock contention) | Either **let exception propagate (with checkpoint)** OR **throw RetryableException (no checkpoint)** | Both retry; with-checkpoint retries the unprocessed slice, RetryableException retries the whole batch |
| Permanent failure (bad payload, validation rejection) | **catch + log + setResumeCheckpoint** | Drop the bad event; don't burn the 9-retry budget on something that will never succeed |
| Trigger body does heavy CPU work | **Tune `batchSize` down via PlatformEventSubscriberConfig** | Default 2,000 is 10× DML; CPU governor will blow on rich payloads |
| Trigger needs broader permissions than the publishing user | **Set `<user>` in PlatformEventSubscriberConfig** | Default running user is often wrong; integration user is the typical right answer |
| All-or-nothing semantics with idempotency | **No checkpoint + RetryableException on transient** | Whole batch is the unit of work |
| Events must NEVER be lost | **Checkpoint + dead-letter on the 10th attempt failure** | After 10 attempts the platform stops retrying; a custom dead-letter table catches the residue |
| You see "EventBus.subscribe()" in someone's code | **Stop and rewrite** | That API does not exist in Apex; the only subscriber is a trigger |

---

## Recommended Workflow

1. **Pick the retry strategy first.** Checkpoint + propagate, RetryableException + no-checkpoint, or drop-on-error. Different strategies for transient vs permanent failures inside the same trigger are fine and common.
2. **Always call `setResumeCheckpoint(e.ReplayId)` after each successful event** unless you've explicitly chosen Pattern B (all-or-nothing).
3. **Catch the right exception types.** Don't catch `Exception` — catch `DmlException`, `CalloutException`, `QueryException` etc. and decide per type whether it's transient (re-throw) or permanent (log + checkpoint).
4. **Test with `Test.EventBus.deliver()`.** Triggers are async; in a test class, publish the event, then call `Test.EventBus.deliver()` to drive the trigger synchronously.
5. **Tune via `PlatformEventSubscriberConfig` only after measurement.** Default batch size is fine for most workloads; only tune when you have profile evidence.

---

## Review Checklist

- [ ] `EventBus.TriggerContext.currentContext()` is captured once at the top of the trigger, not per-event.
- [ ] `setResumeCheckpoint(e.ReplayId)` is called after each successfully-processed event (unless deliberately Pattern B).
- [ ] No bare `catch (Exception ex)` — exception types are caught individually.
- [ ] Permanent-failure branch logs + checkpoints (does not re-throw).
- [ ] Transient-failure branch either re-throws (with checkpoint set) or throws `RetryableException`.
- [ ] No use of a fictional `EventBus.subscribe(...)` API.
- [ ] `PlatformEventSubscriberConfig` is in source control if non-default batch size or running user is required.
- [ ] Test class uses `Test.EventBus.deliver()` to drive the trigger, with assertions on the eventual side effects.
- [ ] Trigger's per-event work, multiplied by 2,000 (or the configured batch size), stays inside SOQL / DML / CPU governors.

---

## Salesforce-Specific Gotchas

1. **Default batch size is 2,000, not 200.** Plan governor budgets accordingly. (See `references/gotchas.md` § 1.)
2. **`EventBus.subscribe(...)` does not exist.** Only triggers are supported subscribers. (See `references/gotchas.md` § 2.)
3. **`RetryableException` without `setResumeCheckpoint` reprocesses already-processed events.** Idempotency required. (See `references/gotchas.md` § 3.)
4. **9 retries (10 total) then the events are lost.** Plan a dead-letter strategy for must-not-lose flows. (See `references/gotchas.md` § 4.)
5. **The trigger's running user defaults to the publisher's context, not always what you want.** Set explicitly via `PlatformEventSubscriberConfig`. (See `references/gotchas.md` § 5.)
6. **`Test.EventBus.deliver()` is required to drive triggers in tests** — publishing alone doesn't fire the trigger synchronously. (See `references/gotchas.md` § 6.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Production-grade subscriber trigger | With per-event checkpointing, typed exception handling, retry-strategy decision documented inline |
| `PlatformEventSubscriberConfig` XML (when needed) | Batch size + running user tuning |
| Test class | Uses `Test.EventBus.deliver()`; covers success path, transient retry, permanent-skip, and 10-attempt give-up |
| Dead-letter handler (if must-not-lose) | Stores residue from the 10th failed retry for human review or async retry |

---

## Related Skills

- `apex/platform-event-publish` — the publisher side; pair with this skill for end-to-end Platform Event flow.
- `apex/trigger-framework` — when this trigger lives inside a generic trigger framework; the framework dispatch must respect the EventBus.TriggerContext API rather than treating the trigger like a DML trigger.
- `apex/apex-mocking-and-stubs` — for the test class that uses `Test.EventBus.deliver()`.
- `integration/event-relay-configuration` — when the same Platform Event channel that this trigger subscribes to is also relayed to AWS EventBridge; the two subscribers are independent (Apex + AWS-side rule).
