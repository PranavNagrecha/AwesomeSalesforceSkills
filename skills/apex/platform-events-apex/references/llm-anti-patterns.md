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

**Why it happens:** LLMs generate per-record publish calls and then justify them with the wrong limit. Which meter a publish spends depends on the event's
`publishBehavior`, not on `EventBus.publish` itself: an event configured `PublishAfterCommit` costs one DML statement per call (`apexdev` L19635,
`apexrefguide` L214525-214527), while an event configured `PublishImmediately` — **the default when `publishBehavior` is omitted** (`api_meta` L42228-42229) —
spends a separate meter of 150 `EventBus.publish` calls per transaction (`apexdev` L19598). So 200 per-record publishes on a default event do not exhaust DML;
they hit the 150-call ceiling at record 151 and the remaining events are never published.

**Correct pattern:**

```apex
trigger AccountTrigger on Account (after update) {
    List<MyEvent__e> events = new List<MyEvent__e>();
    for (Account a : Trigger.new) {
        events.add(new MyEvent__e(AccountId__c = a.Id));
    }
    if (!events.isEmpty()) {
        EventBus.publish(events); // Single publish call — one meter unit for the whole batch
    }
}
```

**Detection hint:** `EventBus\.publish\(` inside a `for` loop. Also flag any limit claim about publishing that does not name the event's `publishBehavior`.

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

**Why it happens:** LLMs treat event publication and subscription as synchronous. Platform event triggers run in a separate transaction from the publisher, and whether a rolled-back publisher still delivers is decided by the event definition, not by the Apex. `PublishAfterCommit`: *"The event message is published only after a transaction commits successfully. If the transaction fails, the event message isn't published."* `PublishImmediately`: *"The event message is published when the publish call executes, regardless of whether the transaction succeeds."* — and *"If you don't specify this field, the default value used is `PublishImmediately`"* (`api_meta` L42206-42230). An LLM that writes a subscriber assuming the publisher's records are committed has silently assumed `PublishAfterCommit` on an event whose definition it never read.

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
    // Query by ID. Under PublishAfterCommit a missing record is a permanent data
    // problem, not a timing race — do NOT retry it. Under PublishImmediately it may
    // genuinely not be committed yet.
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
        // Transient failure — but CAP the retries. Exceeding the budget puts the
        // subscription into Status = Error, where it stops receiving events
        // entirely and later resumes "from the tip", skipping the backlog
        // (object_reference L131382-131390).
        Integer retries = EventBus.TriggerContext.currentContext().retries;
        if (retries >= 8) {
            LogService.logError('MyEventTrigger',
                'Retry budget exhausted after ' + retries + ': ' + e.getMessage());
        } else {
            throw new EventBus.RetryableException('Callout failed, retrying: ' + e.getMessage());
        }
    } catch (Exception e) {
        // Permanent failure — log and consume
        LogService.logError('MyEventTrigger', e);
    }
}
```

The Object Reference recommends *"limiting the retries to fewer than nine times"* to stay out of the `Error` state (`object_reference` L131385-131387), and `EventBus.TriggerContext.retries` is *"The number of times the trigger was retried due to throwing the `EventBus.RetryableException`"* (`apexrefguide` L157805-157810).

**Detection hint:** Platform event trigger with a generic `catch (Exception e)` that does not use `EventBus.RetryableException` for transient failures — or, worse, one that throws `EventBus.RetryableException` with no read of `EventBus.TriggerContext.currentContext().retries` anywhere in the file.

---

## Anti-Pattern 7: Test class that publishes an event and asserts nothing ran

**What the LLM generates:**

```apex
@IsTest
static void testEventPublish() {
    Test.startTest();
    EventBus.publish(new MyEvent__e(RecordId__c = acct.Id));
    Test.stopTest();
    // Asserts the subscriber's side effect... which never happened
    Assert.areEqual(1, [SELECT COUNT() FROM Task]);
}
```

**Why it happens:** LLMs assume `Test.stopTest()` flushes the event bus the way it flushes `@future` and Queueable jobs. It does not. The event bus in a test context is driven explicitly: *"Delivers platform event messages to the test event bus. Use this method to deliver test event messages multiple times and verify that event subscribers have processed the test events each step of the way."* and *"Enclose `Test.getEventBus().deliver()` within the `Test.startTest()` and `Test.stopTest()` statement block."* (`apexrefguide` L157686-157712). The Apex Developer Guide adds that each downstream hop needs its own call: *"If further platform events are published by downstream processes, add `Test.getEventBus().deliver();` to deliver the event messages for each process."* (`apexdev` L17938-17941).

**Correct pattern:**

```apex
@IsTest
static void subscriberCreatesTask() {
    Test.startTest();
    List<Database.SaveResult> results = EventBus.publish(new MyEvent__e(RecordId__c = acct.Id));
    Assert.isTrue(results[0].isSuccess(), 'publish should be queued');
    Test.getEventBus().deliver();          // drives the __e trigger
    Test.stopTest();

    Assert.areEqual(1, [SELECT COUNT() FROM Task]);
}
```

To test the publish-failure path instead, use the other broker method: *"Causes the publishing of platform event messages to fail in the test event bus. Use this method to test Apex publish callbacks."* — `Test.getEventBus().fail()` (`apexrefguide` L157718-157742).

**Detection hint:** a test method containing `EventBus.publish(` and no `Test.getEventBus().deliver()` or `Test.getEventBus().fail()`. Also flag the invented spelling `Test.EventBus.deliver()` — the documented call is `Test.getEventBus()`, which returns an `EventBus.TestBroker` (`apexrefguide` L240472-240480).

---

## Anti-Pattern 8: Writing the `__e` object file without `publishBehavior`

**What the LLM generates:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <label>Order Approved</label>
    <pluralLabel>Order Approved Events</pluralLabel>
    <eventType>HighVolume</eventType>
</CustomObject>
```

**Why it happens:** LLMs reproduce the minimum that deploys. The prose they generate alongside it almost always describes after-commit semantics ("the event fires once the order is saved"), but the file they wrote gets the opposite behaviour by default: *"If you don't specify this field, the default value used is `PublishImmediately`"* (`api_meta` L42228-42229). Nothing fails at deploy time; the mismatch only shows up as a phantom downstream record after the first rollback.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Business event: an order cleared approval.</description>
    <eventType>HighVolume</eventType>
    <label>Order Approved</label>
    <pluralLabel>Order Approved Events</pluralLabel>
    <publishBehavior>PublishAfterCommit</publishBehavior>
</CustomObject>
```

**Detection hint:** a `*.object-meta.xml` whose file name ends in `__e` and whose body has no `<publishBehavior>` element.

---

## Anti-Pattern 6: Setting replay ID incorrectly for CometD/Pub/Sub API subscribers

**What the LLM generates:**

```
// Subscribe to platform events with replay ID = -1 to get all historical events
```

**Why it happens:** LLMs confuse replay ID values, and they invent retention numbers to go with them. The Metadata API's own wording for the equivalent `EventSubscriptionReplayPreset` settings is the grounded version: `LATEST` — *"(Default) The subscription starts from the latest events received. This option skips sending events that were published when the client was disconnected."*; `EARLIEST` — *"The subscription starts from the earliest events stored in the event bus. This option sends new events and any other events less than 72 hours old ... Use this option sparingly. Subscribing with the `EARLIEST` option when a large number of event messages are stored can slow performance and exhaust the event delivery allocation."* (`api_meta` L86606-86632).

UNVERIFIED (2026-09-05): the frequently repeated "24 hours for standard volume, 72 hours for high volume" split is not in the offline corpus. The only retention figure the corpus states is the 72 hours above, and `StandardVolume` is in any case documented as deprecated (`api_meta` L42091-42097). Confirm against the Platform Events Developer Guide allocations page before quoting a per-type number.

**Correct pattern:**

```
Replay ID values:
- -1: New events only (tip of the stream) — use for real-time consumers
- -2: All retained events still in the retention window — use for recovery after downtime
- Specific ID: Resume from a specific event — use for reliable gap-free processing

Best practice: Store the last successfully processed ReplayId and resume from there.
```

**Detection hint:** Replay ID set to `-2` in production code (could cause event flood), or `-1` for a consumer that must not miss events during downtime.
