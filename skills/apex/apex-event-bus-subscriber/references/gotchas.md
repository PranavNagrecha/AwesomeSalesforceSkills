# Gotchas — Apex Event Bus Subscriber

Non-obvious behaviors of Apex Platform Event triggers that bite real
production subscribers.

---

## Gotcha 1: Default batch size is 2,000 events, not 200

**What happens.** A trigger written with DML-trigger intuition (200
records per batch) runs into governor limit failures in production.
SOQL query count, DML row count, and CPU all hit harder than expected.

**When it occurs.** First production load with realistic event volume.
Tests with `Test.EventBus.deliver()` and small event lists pass; the
wall hits when 2,000 events arrive in a batch.

**How to avoid.** Two-pronged:
- Plan governor budgets against 2,000 (or whatever you tune via
  `PlatformEventSubscriberConfig`).
- Use `EventBus.TriggerContext.getEventsRemaining()` to short-circuit
  cleanly when you know the batch can't be finished within budget,
  letting the platform retry the unprocessed slice.

---

## Gotcha 2: `EventBus.subscribe(...)` does not exist in Apex

**What happens.** Code that calls `EventBus.subscribe(channel,
handler)` doesn't compile. Or it compiles because someone wrote a
wrapper class named `EventBus.subscribe` and the team thinks it's the
real API.

**When it occurs.** Patterns ported from external Pub/Sub API clients
(Node, Python), or LLM-generated code that hallucinates the API
based on `EventBus.publish` symmetry.

**How to avoid.** Apex's only supported subscriber is an `after insert`
trigger on the Platform Event SObject. For genuine programmatic
subscribe-from-outside-Apex, the Pub/Sub API is the answer, but it's
called from a non-Apex client (Heroku, AWS Lambda, custom service).

---

## Gotcha 3: `RetryableException` reprocesses already-checkpointed events

**What happens.** The trigger sets `setResumeCheckpoint` on every
success AND throws `EventBus.RetryableException` on failure. On
retry, the WHOLE batch re-fires (including events that already
succeeded and were checkpointed). The non-idempotent processor runs
duplicates.

**When it occurs.** Mixing the two retry strategies thinking they
combine. They don't — checkpoints are honored only on
*uncaught-exception* retry, not on `RetryableException` retry.

**How to avoid.** Pick ONE strategy:
- Checkpoint + propagate uncaught exception → trigger retries the
  unprocessed slice only.
- No checkpoint + `RetryableException` → whole batch retries; require
  idempotency (dedup key).

---

## Gotcha 4: After 9 retries (10 attempts) the events are gone

**What happens.** A trigger that keeps throwing `RetryableException`
or letting transient exceptions propagate eventually exhausts the
retry budget. The platform stops retrying and the events are dropped
silently. No alert.

**When it occurs.** A persistent infra failure that doesn't recover
within the retry window. Or a logic bug that always fails (bad regex,
wrong type cast).

**How to avoid.** For must-not-lose flows, plan a dead-letter
strategy: catch the exception just before re-throw and write the
event payload to a custom object. A separate batch / scheduled job
processes the dead-letter table. The 9-retry budget is for transient
infra; permanent failures should hit dead-letter immediately.

---

## Gotcha 5: Default running user is often the wrong user

**What happens.** Without a `PlatformEventSubscriberConfig`, the
trigger runs as the user whose context published the event (or as
the Automated Process user for replay flows). FLS / sharing /
Apex-enabled-permissions are evaluated against THAT user — often
without the broad access the integration code assumes.

**When it occurs.** Trigger does cross-object DML or queries records
the publishing user can't see; works in dev, fails in production
where the publishing context is a low-permission user.

**How to avoid.** Set `<user>` in `PlatformEventSubscriberConfig` to
a dedicated integration user with the necessary permissions. Document
the user's permission set in the config-meta.xml comment.

---

## Gotcha 6: `Test.EventBus.deliver()` is required to drive triggers in tests

**What happens.** Test publishes an event with `EventBus.publish`,
the test ends, the trigger never fires, the test passes — but the
trigger isn't actually exercised. Coverage is fake.

**When it occurs.** Tests written with DML-trigger intuition where
`insert` immediately fires triggers. Platform Event triggers run
asynchronously; in tests you must explicitly drive them.

**How to avoid.**

```apex
EventBus.publish(myEvent);  // queues
Test.stopTest();
Test.EventBus.deliver();    // drives the trigger synchronously
// then assert side effects
```

Multiple `Test.EventBus.deliver()` calls drive multiple batches if
you want to test the retry path.

---

## Gotcha 7: `setResumeCheckpoint` accepts only a ReplayId from the current batch

**What happens.** Code calls `setResumeCheckpoint(someArbitraryString)`
or `setResumeCheckpoint(e.ReplayId)` from a previous batch. The call
silently no-ops or throws — neither does what was intended.

**When it occurs.** Code that "saves" a ReplayId across batch
boundaries (e.g. in a custom setting) and tries to resume from it.

**How to avoid.** `setResumeCheckpoint` only accepts a ReplayId from
the current `Trigger.new` batch. For cross-batch resumption (replay),
use the Pub/Sub API replay feature from outside Apex — this is not
in Apex's API surface.

---

## Gotcha 8: `EventBus.TriggerContext` is per-trigger-invocation, not per-batch

**What happens.** Code captures `currentContext()` once at class scope,
reuses it across triggers. The TriggerContext is stale; checkpoint
calls go nowhere.

**When it occurs.** Trying to "cache" the context for performance.

**How to avoid.** Capture `currentContext()` at the top of EVERY
trigger invocation. It's cheap; don't optimize.
