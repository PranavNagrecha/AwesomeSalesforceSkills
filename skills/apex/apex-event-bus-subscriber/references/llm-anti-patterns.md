# LLM Anti-Patterns — Apex Event Bus Subscriber

Mistakes AI coding assistants commonly make when generating Apex
Platform Event subscriber code. The consuming agent should self-check
before finalizing output.

---

## Anti-Pattern 1: Inventing `EventBus.subscribe(...)` API

**What the LLM generates.**

```apex
EventBus.subscribe('/event/MyEvent__e', new MyHandler());
// or:
EventBus.SubscriberContext ctx = EventBus.subscribe(MyEvent__e.class);
```

**Why it happens.** The LLM generalizes from `EventBus.publish(...)`
expecting a symmetric `subscribe`. External Pub/Sub API clients
(Node, Python) DO have a programmatic subscribe — the LLM bleeds
that into Apex.

**Correct pattern.** In Apex, the only subscriber is an `after insert`
trigger on the Platform Event SObject:

```apex
trigger MyEventSubscriber on MyEvent__e (after insert) {
    for (MyEvent__e e : Trigger.new) { ... }
}
```

**Detection hint.** Any Apex code that calls `EventBus.subscribe(...)`
or any method on `EventBus` other than `publish` is wrong. The
trigger IS the subscribe mechanism.

---

## Anti-Pattern 2: Default trigger with no checkpointing

**What the LLM generates.**

```apex
trigger MyEventSubscriber on MyEvent__e (after insert) {
    for (MyEvent__e e : Trigger.new) {
        process(e);
    }
}
```

**Why it happens.** Looks like a normal DML trigger. The LLM doesn't
surface that without `setResumeCheckpoint` an uncaught exception
re-processes already-handled events on retry.

**Correct pattern.**

```apex
trigger MyEventSubscriber on MyEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (MyEvent__e e : Trigger.new) {
        process(e);
        ctx.setResumeCheckpoint(e.ReplayId);
    }
}
```

**Detection hint.** Any Platform Event trigger body that doesn't
mention `setResumeCheckpoint` or `EventBus.TriggerContext` is missing
the central retry-correctness mechanism.

---

## Anti-Pattern 3: Assuming 200-record batch size

**What the LLM generates.** Comments / governor budgets sized against
200-record batches; SOQL queries inside loops that would be safe at
200 but blow at 2,000.

**Why it happens.** "Apex trigger" → "200-record batch" is rote
training-data association. Platform Event triggers are 10× that.

**Correct pattern.** Plan governor budgets against 2,000 (or whatever
`PlatformEventSubscriberConfig.batchSize` is set to). Use
`Limits.getQueries()`, `Limits.getDmlStatements()`, etc. to track,
and `EventBus.TriggerContext.getEventsRemaining()` to bail out
cleanly when budget runs low.

**Detection hint.** Any "we have 200 records max" comment in a
Platform Event trigger is wrong.

---

## Anti-Pattern 4: Mixing checkpoint and `RetryableException`

**What the LLM generates.**

```apex
trigger MyEventSubscriber on MyEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (MyEvent__e e : Trigger.new) {
        try {
            process(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (Exception ex) {
            throw new EventBus.RetryableException('failed', ex);
        }
    }
}
```

**Why it happens.** Both APIs exist; the LLM combines them assuming
"more retry mechanisms = more resilient". They contradict.

**Correct pattern.** Pick ONE:

- Per-event resilience → checkpoint + propagate uncaught exception:
  ```apex
  } catch (TransientException ex) { throw ex; }
  ```
- Whole-batch atomicity → no checkpoint + RetryableException, with
  idempotent processing.

**Detection hint.** A trigger body that calls *both* `setResumeCheckpoint`
*and* throws `RetryableException` is contradicting itself. Refactor
to one strategy.

---

## Anti-Pattern 5: Catching bare `Exception` and re-throwing

**What the LLM generates.**

```apex
} catch (Exception ex) {
    throw new EventBus.RetryableException('error', ex);
}
```

**Why it happens.** Bare `catch (Exception)` is the default Java
muscle-memory. The LLM doesn't surface that this loses the
transient-vs-permanent distinction critical to retry budget management.

**Correct pattern.** Catch typed exceptions individually; decide per
type whether to retry (transient) or skip (permanent):

```apex
} catch (CalloutException ex) {
    throw ex;  // transient — let trigger retry
} catch (DmlException ex) {
    // permanent — log and skip
    ApplicationLogger.error('Bad event', ex);
    ctx.setResumeCheckpoint(e.ReplayId);
}
```

**Detection hint.** Any `catch (Exception ex)` in a Platform Event
trigger that re-throws as `RetryableException` is mistreating
permanent failures as transient.

---

## Anti-Pattern 6: Tests that publish without `Test.EventBus.deliver()`

**What the LLM generates.**

```apex
@IsTest
static void testTrigger() {
    EventBus.publish(new MyEvent__e(...));
    Test.stopTest();
    System.assertEquals(1, [SELECT COUNT() FROM Result__c]);  // 0 — trigger never fired
}
```

**Why it happens.** DML-trigger test pattern: insert → trigger fires
synchronously → assert. Platform Event triggers are async.

**Correct pattern.**

```apex
@IsTest
static void testTrigger() {
    Test.startTest();
    EventBus.publish(new MyEvent__e(...));
    Test.stopTest();
    Test.EventBus.deliver();   // drives the trigger synchronously
    System.assertEquals(1, [SELECT COUNT() FROM Result__c]);
}
```

**Detection hint.** Any test that publishes a Platform Event without
calling `Test.EventBus.deliver()` is testing nothing.

---

## Anti-Pattern 7: "Save the ReplayId for replay later"

**What the LLM generates.**

```apex
// Save position for resumption
CustomSetting__c.put('last_processed', e.ReplayId);
// ... later ...
ctx.setResumeCheckpoint(savedReplayId);  // doesn't work
```

**Why it happens.** "ReplayId is a position; save it like Kafka
offsets" is a transferable mental model from external event systems.
But Apex's `setResumeCheckpoint` only accepts a ReplayId from the
*current* `Trigger.new` batch.

**Correct pattern.** Cross-batch / cross-session replay is a
Pub/Sub API feature, not an Apex API feature. From Apex you can only
checkpoint within the current batch. For external replay, use the
Pub/Sub API client and its replay parameter.

**Detection hint.** Any code that stores a ReplayId in a custom
setting / object and tries to use it in `setResumeCheckpoint` later
is mixing Apex semantics with external-client semantics.
