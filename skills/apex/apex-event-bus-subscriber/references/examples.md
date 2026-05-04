# Examples — Apex Event Bus Subscriber

## Example 1 — Default trigger that silently re-processes on every retry

**Context.** A team writes their first Platform Event subscriber trigger.
It works in the happy path. In production, an upstream callout fails
intermittently and the team notices their downstream system is creating
duplicate records — the same OrderEvent is being processed multiple
times.

**Wrong code.**

```apex
trigger OrderEventSubscriber on OrderEvent__e (after insert) {
    for (OrderEvent__e e : Trigger.new) {
        new OrderProcessor().process(e);
    }
}
```

**Why it's wrong.** No `setResumeCheckpoint`. Any uncaught exception
re-fires the trigger from the START of the batch — events 0..N that
already succeeded run again. With the default 2,000-event batch and a
flaky callout in the middle, this is a duplicate-record machine.

**Right code.**

```apex
trigger OrderEventSubscriber on OrderEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (OrderEvent__e e : Trigger.new) {
        try {
            new OrderProcessor().process(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (CalloutException ex) {
            // Transient — let it propagate. Trigger re-fires from event AFTER
            // the last successful checkpoint.
            throw ex;
        }
    }
}
```

**Why it works.** After each successfully processed event, the
checkpoint advances. On the next retry the trigger resumes from the
event AFTER the checkpoint. Already-processed events are skipped
without idempotency tricks.

---

## Example 2 — RetryableException re-firing the entire batch

**Context.** A ledger system needs all-or-nothing batch semantics — if
any event in the batch fails, the whole batch must be retried or
flagged for review. The trigger uses `EventBus.RetryableException`
without realizing it implies idempotency.

**Wrong code.**

```apex
trigger LedgerEventSubscriber on LedgerEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (LedgerEvent__e e : Trigger.new) {
        try {
            applyToLedger(e);  // not idempotent — appends to ledger
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (Exception ex) {
            throw new EventBus.RetryableException('Ledger error', ex);
        }
    }
}
```

**Why it's wrong-ish.** Mixing checkpoint with `RetryableException`
contradicts itself. RetryableException re-fires the WHOLE batch —
checkpoints don't apply. So on retry, events 0..N that already
succeeded *and were checkpointed* are re-processed by the
non-idempotent `applyToLedger` — double-entry bookkeeping with
duplicates.

**Right code (Pattern B — true all-or-nothing).**

```apex
trigger LedgerEventSubscriber on LedgerEvent__e (after insert) {
    try {
        // applyBatch is itself transactional and idempotent on retry
        // (uses each event's ReplayId as a dedup key).
        Ledger.applyBatch(Trigger.new);
    } catch (TransientException ex) {
        throw new EventBus.RetryableException('Re-fire ledger batch', ex);
    }
}
```

No per-event checkpoint. The whole batch is the unit. `applyBatch` is
idempotent (deduplicating by ReplayId), so retries are safe.

---

## Example 3 — Permanent failures that burn the retry budget

**Context.** A trigger processes events that occasionally have
malformed payloads (upstream system bug). The trigger throws on bad
payloads. The events get retried 9 times, fail every time, then are
dropped. Meanwhile valid events behind them in the batch never get
processed because the bad event blocks the slice.

**Wrong code.**

```apex
trigger PaymentEventSubscriber on PaymentEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (PaymentEvent__e e : Trigger.new) {
        validatePayload(e);   // throws on bad payload
        applyPayment(e);
        ctx.setResumeCheckpoint(e.ReplayId);
    }
}
```

**Why it's wrong.** `validatePayload` throws an uncaught exception →
trigger re-fires from the checkpoint. The bad event is the first
unprocessed event, so the next retry hits it again immediately. After
9 retries the whole slice (including valid events behind the bad one)
is dropped.

**Right code.**

```apex
trigger PaymentEventSubscriber on PaymentEvent__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (PaymentEvent__e e : Trigger.new) {
        try {
            validatePayload(e);
            applyPayment(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (PayloadException ex) {
            // Permanent — bad payload, retrying won't help. Log to a
            // dead-letter table and skip.
            DeadLetter__c dl = new DeadLetter__c(
                Replay_Id__c = e.ReplayId,
                Reason__c = ex.getMessage(),
                Payload__c = JSON.serialize(e)
            );
            insert dl;
            ctx.setResumeCheckpoint(e.ReplayId);
        }
    }
}
```

The bad event is logged + skipped, retry budget is preserved for
genuinely transient failures, valid events behind the bad one are
processed.

---

## Example 4 — Tuning the batch size for CPU-heavy work

**Context.** A trigger processes events containing rich-text payloads
that need regex parsing and sanitization. With the default 2,000-event
batch, the trigger blows the 10-second sync CPU governor on payloads
> 50 KB.

**Right answer.** Add a `PlatformEventSubscriberConfig` to source
control:

```xml
<!-- platformEventSubscriberConfigs/RichTextEventSubscriber.platformEventSubscriberConfig-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventSubscriberConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <batchSize>200</batchSize>
    <masterLabel>RichTextEventSubscriber</masterLabel>
    <platformEventConsumer>RichTextEventSubscriber</platformEventConsumer>
    <user>integration.user@acme.com</user>
</PlatformEventSubscriberConfig>
```

`batchSize: 200` brings the per-batch work back inside the CPU
governor. `<user>` fixes the running user to a dedicated integration
user with the right permissions for the downstream operations.

---

## Example 5 — Test class using `Test.EventBus.deliver()`

**Context.** Testing the OrderEventSubscriber trigger from Example 1.

```apex
@IsTest
private class OrderEventSubscriberTest {
    @IsTest
    static void processedEventsAdvanceCheckpoint() {
        // Arrange — publish two events synchronously inside Test context.
        OrderEvent__e e1 = new OrderEvent__e(OrderId__c = 'A1');
        OrderEvent__e e2 = new OrderEvent__e(OrderId__c = 'A2');
        Test.startTest();
        EventBus.publish(e1);
        EventBus.publish(e2);
        Test.stopTest();

        // Act — drive the trigger synchronously.
        Test.EventBus.deliver();

        // Assert — both orders processed.
        List<Order__c> orders = [SELECT Id FROM Order__c WHERE OrderId__c IN ('A1', 'A2')];
        System.assertEquals(2, orders.size(), 'Both events should produce orders');
    }
}
```

Without `Test.EventBus.deliver()` the trigger doesn't fire in the test
context — `EventBus.publish` queues the events, the test ends, the
trigger never runs, and the test passes for the wrong reason.

---

## Anti-Pattern: Looking for `EventBus.subscribe()`

```apex
// This API does not exist.
EventBus.subscribe('/event/MyEvent__e', new MyHandler());
```

**Why it doesn't work.** Apex has no programmatic subscribe API. The
ONLY supported in-org subscriber mechanism is an `after insert`
trigger on the Platform Event SObject.

**Where the confusion comes from.** External clients (Node, Python)
subscribe via the Pub/Sub API — those clients DO use a programmatic
subscribe call. Inside Apex, the equivalent is the trigger.
