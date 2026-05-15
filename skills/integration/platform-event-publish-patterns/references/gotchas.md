# Gotchas — Platform Event Publish Patterns

Edge cases that surface only after a Platform Event publisher is
running in production. These compound the SKILL.md gotchas with the
second-order issues found by ops teams chasing real outages.

## Gotcha 1: `EventBus.publish` consumes a DML statement per call, not per event

**What happens:** Code does
`for (Order__c o : orders) { EventBus.publish(new MyEvent__e(...)); }`
and hits `LimitException: Too many DML statements: 151` at the 151st
iteration. Practitioners read the docs, see "EventBus.publish counts
as DML," and assume it's "1 DML per event" — but the consumed unit
is per `publish()` *call*, not per event. Bulk-publishing a list
of 200 events is 1 DML; publishing individually in a loop is 200.

**When it occurs:** Per-record publishes in loops, often introduced
"to make the code more readable" by extracting the publish into a
helper method that's then called per-iteration.

**How to avoid:** Always batch into a `List<Event__e>` and call
`EventBus.publish(list)` once. The DML budget is preserved and the
underlying network traffic is identical (the platform batches the
list internally). Code-review rule: if you see `EventBus.publish`
inside a `for` loop, flag it.

---

## Gotcha 2: `PublishAfterCommit` events queued in a Savepoint scope are dropped on rollback

**What happens:** Code does
`Savepoint sp = Database.setSavepoint();` then queues several
`Order_Submitted__e` events (with `PublishBehavior:
PublishAfterCommit`) via `EventBus.publish`. A later DML fails;
the catch block calls `Database.rollback(sp)`. The events are
silently dropped — neither the original transaction's DML *nor*
the queued events reach subscribers.

This is usually the desired behavior, but it's frequently a
surprise: practitioners assume "the event was already published,
so it's gone." The opposite is true for `PublishAfterCommit`.

**When it occurs:** Any code path that wraps publishes in a
savepoint scope. Especially: service-layer code that uses
savepoint for atomicity and emits events at the end of the
happy path — the rollback path drops both the DML and the
events, which is correct but not always documented.

**How to avoid:** Document the contract explicitly. If your
service emits events as part of its happy-path return, callers
know that a thrown exception means the events also didn't fire.
For events that MUST fire regardless of rollback (audit trails,
telemetry), set the event metadata to `PublishBehavior:
PublishImmediately` and accept that subscribers may see "event
fired for transaction that didn't commit" — handle that on the
subscriber side.

---

## Gotcha 3: Events from `PublishImmediately` may fire BEFORE the publishing transaction's DML is visible

**What happens:** Code does:

```apex
insert order;                                           // line 1
EventBus.publish(new Order_Created__e(                  // line 2
    Order_Id__c = order.Id));                           // line 3
```

The event has `PublishBehavior: PublishImmediately`. A subscriber
on the event queries `Order__c WHERE Id = :Order_Id__c` and gets
zero results — the order doesn't exist yet from the subscriber's
perspective.

The issue: `PublishImmediately` releases the event to the bus
immediately, but the `insert order` on line 1 isn't visible to
other transactions until *this* transaction commits. The subscriber
is a different transaction; it sees the pre-insert state.

**When it occurs:** `PublishImmediately` events that carry record
IDs that subscribers will look up. The race window is short
(milliseconds) but real.

**How to avoid:** Either (a) use `PublishAfterCommit` (the default,
correct for almost all business-event scenarios), or (b) include
all the data the subscriber needs in the event payload itself
(don't make the subscriber do a lookup). The latter is more code
but is the right pattern for fan-out scenarios where many
subscribers each do the same lookup.

---

## Gotcha 4: Event allocation is consumed even by events that subscribers never receive

**What happens:** A team builds a new Platform Event and rolls it
out as `PublishImmediately`. No subscribers are configured yet —
the rollout sequence has the publisher going live first, then
subscribers being deployed a week later. During that week, the
publisher fires ~50,000 events that no one consumes. The next
monthly billing cycle shows allocation usage spike; finance asks
why.

The platform charges per event *published*, not per event
*received*. Events without subscribers still count.

**When it occurs:** Rollout sequences that put the publisher
before the subscriber. Also: debugging sessions where the
developer publishes test events repeatedly to verify "the
publish works" without realizing each test consumes allocation.

**How to avoid:** Defer publisher rollout until at least one
subscriber is ready, or wrap the publish in a feature flag
that defaults to off until subscribers are wired. During
development, use a dev sandbox with a separate allocation pool
— production allocation should not be burned by dev testing.
For very high-volume events, consider using `High Volume`
event type (different allocation pricing) and review the
`Setup → Platform Events → Event Delivery Usage` panel weekly.

---

## Gotcha 5: Tests with `PublishAfterCommit` events require BOTH `Test.startTest()` AND `Test.getEventBus().deliver()`

**What happens:** A unit test inserts a record, asserts that an
event was published (by checking subscriber side-effects), and
fails. The trigger does fire `EventBus.publish`, but
`PublishAfterCommit` semantics defer delivery until the
*transaction* commits — which never happens in a unit test
because every test runs in a single transaction that rolls back.

`Test.startTest()` / `Test.stopTest()` don't help directly —
they don't commit the test transaction, they just provide a fresh
governor-limit scope. The subscriber's side-effect doesn't
appear.

**When it occurs:** Every Apex test that asserts a downstream
side-effect of a Platform Event. Surprisingly common — tests
"pass" by accident when the assertion is too lenient
(`System.assertNotEquals(0, [SELECT COUNT() FROM AsyncApexJob])`
which happens to be non-zero for other reasons).

**How to avoid:** Use `Test.getEventBus().deliver()` between
`Test.startTest()` and the assertion. This forces immediate
delivery to subscribers within the test transaction. Pair with
`Test.startTest()` so async subscribers (Apex triggers on the
event) run with a clean governor budget. The full pattern:

```apex
Test.startTest();
insert account;
Test.getEventBus().deliver();   // ← essential
Test.stopTest();
System.assertEquals(1, [SELECT COUNT() FROM Notification_Log__c]);
```

Without `deliver()`, the assertion would fail even though the
trigger code is correct.
