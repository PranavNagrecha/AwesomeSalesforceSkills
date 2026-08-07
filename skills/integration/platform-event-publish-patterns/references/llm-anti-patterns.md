# LLM Anti-Patterns — Platform Event Publish Patterns

Common mistakes AI coding assistants make when publishing Platform Events.

## Anti-Pattern 1: Ignoring `SaveResult` from `EventBus.publish`

**What the LLM generates:**

```
EventBus.publish(new Order_Created__e(Order_Id__c = o.Id));
```

**Why it happens:** Model treats publish as fire-and-forget like `System.debug`.

**Correct pattern:**

```
Database.SaveResult sr = EventBus.publish(evt);
if (!sr.isSuccess()) {
    for (Database.Error err : sr.getErrors()) {
        Logger.error('Event publish failed: ' + err.getMessage());
    }
}

A publish can fail silently — monthly allocation exhausted, storage
limit, serialization error. Without inspecting SaveResult, the event
vanishes and subscribers never fire.
```

**Detection hint:** `EventBus.publish(...)` call whose return value is discarded.

---

## Anti-Pattern 2: Wrong `PublishBehavior` for business-critical events

**What the LLM generates:** Publishes with default metadata without considering rollback semantics, or sets `PublishImmediately` on an Order_Created event.

**Why it happens:** Model doesn't distinguish telemetry from business logic.

**Correct pattern:**

```
Business-logic events (Order_Created, Payment_Completed) MUST be
PublishAfterCommit. If the transaction rolls back after publish,
an Immediately-published event fires regardless — downstream systems
act on an order that doesn't exist.

Only use PublishImmediately for telemetry/audit events where over-
firing is acceptable.
```

**Detection hint:** Event metadata with `PublishImmediately` on an event whose name implies business state (Created, Completed, Approved).

---

## Anti-Pattern 3: Publishing inside a try/catch that swallows DML rollback

**What the LLM generates:**

```
try {
    insert orders;
    EventBus.publish(evts);  // PublishImmediately event
} catch (Exception e) {
    // log and swallow
}
```

**Why it happens:** Model pairs publish with insert without reasoning about rollback timing.

**Correct pattern:**

```
With PublishImmediately, the event fires even if `insert orders`
partially succeeded and the catch rolled back via savepoint. Use
PublishAfterCommit OR gate the publish on successful DML:

List<Database.SaveResult> srs = Database.insert(orders, false);
List<Order_Created__e> evts = new List<Order_Created__e>();
for (Integer i = 0; i < srs.size(); i++) {
    if (srs[i].isSuccess()) evts.add(new Order_Created__e(Order_Id__c = orders[i].Id));
}
EventBus.publish(evts);
```

**Detection hint:** `EventBus.publish` inside a try block preceded by DML, without guarding on DML success.

---

## Anti-Pattern 4: Test without `Test.getEventBus().deliver()`

**What the LLM generates:**

```
@IsTest static void testFlow() {
    Test.startTest();
    myService.doWork();   // publishes Order_Created__e
    Test.stopTest();
    // assertions on subscriber side effects
}
```

**Why it happens:** Model assumes events deliver synchronously in tests like DML.

**Correct pattern:**

```
PublishAfterCommit events do NOT fire in tests without explicit delivery:

Test.startTest();
myService.doWork();
Test.getEventBus().deliver();  // force synchronous delivery
Test.stopTest();

Without deliver(), subscriber triggers/flows never run. Tests silently
pass while real deployment breaks.
```

**Detection hint:** Apex test that publishes Platform Events and asserts on subscriber side effects without calling `Test.getEventBus().deliver()`.

---

## Anti-Pattern 5: Single-event publish in a loop

**What the LLM generates:**

```
for (Order__c o : orders) {
    EventBus.publish(new Order_Created__e(Order_Id__c = o.Id));
}
```

**Why it happens:** Model mirrors the DML-in-loop shape without bulkifying.

**Correct pattern:**

```
Build a list and publish once:

List<Order_Created__e> evts = new List<Order_Created__e>();
for (Order__c o : orders) evts.add(new Order_Created__e(Order_Id__c = o.Id));
List<Database.SaveResult> srs = EventBus.publish(evts);

Single-event publishes in a loop still consume one allocation each
but also trigger more internal overhead. Bulk publish is idiomatic
and gives a SaveResult per event for granular failure handling.
```

**Detection hint:** `EventBus.publish(...)` inside a `for`/`while` loop with a single-event argument.

---

## Anti-Pattern: Platform Event Allocation and Retention Stated From Memory

**What the LLM generates:** Three recurring shapes, all built from real Salesforce numbers pinned to the wrong dimension:

1. "Standard event allocation: 250,000 events per **24 hours**." — right number, wrong period. 250,000 is an **hourly** allocation.
2. "High-Volume Platform Events bypass the standard allocation" / "high-volume events are unlimited." — no event type publishes without an allocation.
3. "High-Volume Platform Events support `RetainUntilDate` for retention beyond 72 hours." — there is no retention field on any Platform Event.

**Why it happens:** Platform Events genuinely have several allocations metered over different periods — publishing per hour, delivery to CometD/empApi subscribers per 24 hours — so a period gets attached to the wrong figure with no loss of plausibility. "High-volume" as a product name invites the reading that it is the uncapped tier. And every neighbouring event bus (SQS, EventBridge, Kafka) exposes per-message or per-topic retention, so a retention knob is the strong prior for anything that stores events.

**Correct version:**

```text
Publishing (org-wide, PER HOUR):
  high-volume     250,000  (Enterprise, Performance, Unlimited)
                   50,000  (Developer)
                  +25,000/hour per add-on
  standard-volume 100,000  (EE / Perf / Unlimited)  [legacy]

Retention (fixed, NOT configurable, no field sets it):
  high-volume      72 hours
  standard-volume  24 hours

Tier: after Spring '19 you cannot define a standard-volume event.
      Publish and subscribe for standard-volume retire in Winter '27.
      So "standard vs high-volume" is a migration question, not a design choice.

Replay window > 72 hours: publisher writes a durable copy (Big Object /
      external queue) alongside the publish; subscriber backfills from it.
```

**Detection hint:** `grep -rniE 'RetainUntilDate|250,?000 (events )?per (24|day)|high.?volume.*unlimited'` — all three shapes are wrong. Positively: any platform-event allocation quoted without both an edition and a period ("per hour" vs "per 24 hours") is under-specified and probably relabelled.
