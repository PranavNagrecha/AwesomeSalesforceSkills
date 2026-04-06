# LLM Anti-Patterns — Platform Events Apex

Common mistakes AI coding assistants make when generating or advising on Platform Events in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not checking EventBus.publish results for failures

**What the LLM generates:**

```apex
List<MyEvent__e> events = new List<MyEvent__e>();
for (Account a : accounts) {
    events.add(new MyEvent__e(AccountId__c = a.Id, Action__c = 'Updated'));
}
EventBus.publish(events); // Return value ignored — no error detection
```

**Why it happens:** LLMs treat `EventBus.publish` like standard DML and ignore the return value. Unlike standard DML, `publish` does not throw an exception on partial failure — it returns `Database.SaveResult` objects where individual events may have failed.

**Correct pattern:**

```apex
List<MyEvent__e> events = new List<MyEvent__e>();
for (Account a : accounts) {
    events.add(new MyEvent__e(AccountId__c = a.Id, Action__c = 'Updated'));
}
List<Database.SaveResult> results = EventBus.publish(events);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        for (Database.Error err : results[i].getErrors()) {
            LogService.logError('EventPublish', events[i].AccountId__c + ': ' + err.getMessage());
        }
    }
}
```

**Detection hint:** `EventBus\.publish\(` without capturing the return value in a `List<Database.SaveResult>`.

---

## Anti-Pattern 2: Confusing Platform Events with Change Data Capture

**What the LLM generates:**

```apex
// "Use Platform Events to track field changes on Account"
trigger AccountChangeTrigger on MyEvent__e (after insert) {
    // Re-implementing change tracking that CDC already provides
    for (MyEvent__e evt : Trigger.new) {
        // Compare old and new values...
    }
}
```

**Why it happens:** LLMs suggest custom Platform Events for record change notifications when Change Data Capture (CDC) already provides this natively. CDC captures all field changes, old values, and change metadata automatically — no custom event schema needed.

**Correct pattern:**

```apex
// For record change tracking, use Change Data Capture
trigger AccountCDCTrigger on AccountChangeEvent (after insert) {
    for (AccountChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        List<String> changedFields = header.getChangedFields();
        // React to specific field changes
    }
}

// Platform Events are for custom business events NOT tied to specific record changes
// Examples: "Order Fulfilled", "Payment Received", "Approval Requested"
```

**Detection hint:** Platform Event trigger that manually tracks field value changes — should likely be CDC instead.

---

## Anti-Pattern 3: Publishing events inside a trigger loop

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (after update) {
    for (Account a : Trigger.new) {
        MyEvent__e evt = new MyEvent__e(AccountId__c = a.Id);
        EventBus.publish(evt); // Publish per record — hits limits
    }
}
```

**Why it happens:** LLMs generate per-record publish calls. `EventBus.publish` counts against the DML statement limit. With 200 records in a trigger batch, this is 200 DML operations.

**Correct pattern:**

```apex
trigger AccountTrigger on Account (after update) {
    List<MyEvent__e> events = new List<MyEvent__e>();
    for (Account a : Trigger.new) {
        events.add(new MyEvent__e(AccountId__c = a.Id));
    }
    if (!events.isEmpty()) {
        EventBus.publish(events); // Single publish call for all events
    }
}
```

**Detection hint:** `EventBus\.publish\(` inside a `for` loop.

---

## Anti-Pattern 4: Assuming platform event triggers run in the same transaction as the publisher

**What the LLM generates:**

```apex
// Publisher:
insert new Account(Name = 'Test');
EventBus.publish(new MyEvent__e(Action__c = 'AccountCreated'));
// Subscriber trigger assumes it can see the Account immediately

// Subscriber:
trigger MyEventTrigger on MyEvent__e (after insert) {
    // This runs in a SEPARATE transaction
    Account a = [SELECT Id FROM Account WHERE Name = 'Test' ORDER BY CreatedDate DESC LIMIT 1];
    // May not find it if publisher transaction hasn't committed yet
}
```

**Why it happens:** LLMs treat event publication and subscription as synchronous. Platform event triggers run in a separate transaction from the publisher. If the publisher's transaction rolls back, the event is still delivered (publish-after-commit events are the exception when using `EventBus.publish` behavior, but standard behavior delivers immediately).

**Correct pattern:**

```apex
// Pass the record ID in the event payload so the subscriber can query by ID
EventBus.publish(new MyEvent__e(RecordId__c = account.Id, Action__c = 'AccountCreated'));

// Subscriber:
trigger MyEventTrigger on MyEvent__e (after insert) {
    Set<Id> recordIds = new Set<Id>();
    for (MyEvent__e evt : Trigger.new) {
        recordIds.add(evt.RecordId__c);
    }
    // Query by ID, and handle the case where the record may not exist yet
    List<Account> accounts = [SELECT Id FROM Account WHERE Id IN :recordIds];
}
```

**Detection hint:** Platform event subscriber that queries records without using an ID from the event payload, relying on timing assumptions.

---

## Anti-Pattern 5: Not implementing EventBus.RetryableException for transient subscriber failures

**What the LLM generates:**

```apex
trigger MyEventTrigger on MyEvent__e (after insert) {
    try {
        processEvents(Trigger.new);
    } catch (Exception e) {
        System.debug('Event processing failed: ' + e.getMessage());
        // Event is marked as consumed — lost forever
    }
}
```

**Why it happens:** LLMs swallow exceptions in event triggers, which marks the events as successfully consumed. For transient failures (callout timeout, lock contention), the events should be retried. The platform provides `EventBus.RetryableException` for exactly this purpose.

**Correct pattern:**

```apex
trigger MyEventTrigger on MyEvent__e (after insert) {
    try {
        processEvents(Trigger.new);
    } catch (CalloutException e) {
        // Transient failure — throw RetryableException to retry delivery
        throw new EventBus.RetryableException('Callout failed, retrying: ' + e.getMessage());
    } catch (Exception e) {
        // Permanent failure — log and consume
        LogService.logError('MyEventTrigger', e);
    }
}
```

**Detection hint:** Platform event trigger with a generic `catch (Exception e)` that does not use `EventBus.RetryableException` for transient failures.

---

## Anti-Pattern 6: Setting replay ID incorrectly for CometD/Pub/Sub API subscribers

**What the LLM generates:**

```
// Subscribe to platform events with replay ID = -1 to get all historical events
```

**Why it happens:** LLMs confuse replay ID values. `-1` means "subscribe to new events only" (from the tip). `-2` means "replay from the earliest available event in the retention window" (24 hours for standard, 72 hours for high-volume). Getting these backwards means either missing historical events or getting a flood of old events on reconnect.

**Correct pattern:**

```
Replay ID values:
- -1: New events only (tip of the stream) — use for real-time consumers
- -2: All retained events (up to 24h/72h) — use for recovery after downtime
- Specific ID: Resume from a specific event — use for reliable gap-free processing

Best practice: Store the last successfully processed ReplayId and resume from there.
```

**Detection hint:** Replay ID set to `-2` in production code (could cause event flood), or `-1` for a consumer that must not miss events during downtime.
