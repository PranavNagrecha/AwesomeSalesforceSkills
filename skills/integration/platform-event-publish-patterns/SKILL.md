---
name: platform-event-publish-patterns
description: "Publishing Platform Events: EventBus.publish, PublishBehavior (PublishImmediately vs PublishAfterCommit), high-volume events, event allocation, publish failures, Change Data Capture comparison. NOT for subscribing/consuming (use platform-event-subscribe-patterns). NOT for CDC architecture (use cdc-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - platform-events
  - eventbus
  - publish
  - publishbehavior
  - async
triggers:
  - "eventbus.publish platform event apex how to"
  - "platform event publish immediately vs after commit"
  - "high volume platform event allocation monthly"
  - "platform event publish error handling and retry"
  - "platform event publish from trigger rollback"
  - "publish behavior publish after commit vs immediate"
inputs:
  - Event name and payload shape
  - Publish context (trigger, service, async)
  - Rollback semantics desired
  - Expected event volume per day
outputs:
  - Publish code with correct PublishBehavior
  - Event allocation estimate
  - Error-handling and retry plan
  - Monitoring approach
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-05-15
---

# Platform Event Publish Patterns

Activate when emitting Platform Events from Apex, Flow, or external callers. Publish semantics have subtle implications: `PublishAfterCommit` vs `PublishImmediately` determines whether rollback erases the event, high-volume events consume monthly allocation, and publish failures surface differently from synchronous DML errors.

## Before Starting

- **Decide publish behavior.** `PublishAfterCommit` is the default and safest — event fires only if the surrounding transaction commits. `PublishImmediately` fires even if the transaction rolls back.
- **Check event allocation.** High-Volume events have daily + monthly caps per license.
- **Plan monitoring.** Publish failures return `SaveResult` errors; check every result.

## Core Concepts

### EventBus.publish

```
MyEvent__e evt = new MyEvent__e(Order_Id__c = oid, Amount__c = amt);
Database.SaveResult sr = EventBus.publish(evt);
if (!sr.isSuccess()) {
    for (Database.Error err : sr.getErrors()) {
        System.debug(err.getMessage());
    }
}
```

Returns a `Database.SaveResult` per event, or `List<SaveResult>` for bulk.

### PublishBehavior

Set on event metadata (`PublishBehavior: PublishAfterCommit` | `PublishImmediately`):

- **PublishAfterCommit** (default): event fires only if the transaction commits. Safer; survives rollback.
- **PublishImmediately**: event fires regardless of transaction outcome. Use for telemetry where fire-and-forget is acceptable even on rollback.

### ReplayId and durability

Every published event is stored with a `ReplayId`; a subscriber can resume from a stored `ReplayId`, or use `-1` (default — new events only) or `-2` (replay everything still retained). Retention is **72 hours** for high-volume events — which is every event definable since Spring '19 — and **24 hours** for legacy standard-volume events, retiring in Winter '27. Retention is fixed: no field or setting extends it, so a replay window longer than 72 hours must be served by a durable copy the publisher writes alongside the event.

### Event allocation

Publishing is metered **per hour, org-wide**: 250,000/hour for high-volume events on Enterprise, Performance, and Unlimited; 50,000/hour on Developer; add-on capacity in +25,000/hour increments. Bulk publishes consume one unit per event published, so a 10,000-record batch that publishes one event per record spends 10,000 of the hourly allocation — batching domain changes into coarser events is the lever when a design approaches the ceiling. (Event *delivery* to CometD/empApi subscribers is metered separately on a 24-hour basis; do not conflate the two.)

### Publishing from async contexts

Triggers, Queueables, Batch, Scheduled — all can publish. Publishing from a future method works but adds complexity; prefer publishing in the originating transaction.

## Common Patterns

### Pattern: Publish after DML commit

```
insert orders;
List<Order_Created__e> evts = new List<Order_Created__e>();
for (Order__c o : orders) evts.add(new Order_Created__e(Order_Id__c = o.Id));
EventBus.publish(evts);  // fires after commit
```

### Pattern: Bulk publish with result check

```
List<SaveResult> results = EventBus.publish(events);
List<Id> failed = new List<Id>();
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) failed.add(events[i].someId__c);
}
```

### Pattern: Retry via Queueable

If `SaveResult` failure includes "STORAGE_LIMIT_EXCEEDED" or similar transient error, re-enqueue via Queueable with exponential backoff.

## Decision Guidance

| Scenario | PublishBehavior |
|---|---|
| Business-logic event — must not fire on rollback | PublishAfterCommit |
| Fire-and-forget telemetry | PublishImmediately |
| Chain to external system, must commit first | PublishAfterCommit |
| Alert/audit event, okay if tx rolled back | PublishImmediately |

## Recommended Workflow

1. Decide PublishBehavior on the event metadata.
2. Publish via `EventBus.publish(event)` or bulk list.
3. Always inspect `SaveResult` — publish is not guaranteed.
4. For business-critical events, pair with an outbox pattern (write to a custom object, async publisher retries on failure).
5. Monitor monthly allocation via Setup → Platform Events.
6. Test with `Test.startTest()` / `Test.getEventBus().deliver()` to drive subscribers.
7. Document event schema, versioning strategy, and retry guarantees.

## Review Checklist

- [ ] PublishBehavior set intentionally on metadata
- [ ] SaveResult inspected; failures logged or retried
- [ ] Event volume estimated vs allocation
- [ ] Bulk publish used for multi-event scenarios
- [ ] No silent ignore of failures
- [ ] Test uses `Test.getEventBus().deliver()` where needed
- [ ] Outbox pattern considered for business-critical events
- [ ] Event schema versioning plan documented

## Salesforce-Specific Gotchas

1. **`PublishAfterCommit` events do NOT fire in test context without `Test.getEventBus().deliver()`.** Tests silently pass while real subscribers wouldn't be invoked.
2. **Platform Events cannot be published from a transaction that's rolled back via `Database.rollback`** when behavior is PublishAfterCommit — no event fires. When PublishImmediately, the event fires even on rollback.
3. **Bulk publish allocates one event per record.** 200 events = 200 allocation units.

## Output Artifacts

| Artifact | Description |
|---|---|
| Event metadata spec | PublishBehavior + field list |
| Publisher Apex class | Bulk publish + SaveResult handling |
| Outbox pattern (optional) | Custom object + retry publisher |
| Monitoring dashboard | Allocation + failure metrics |

## Related Skills

- `integration/platform-event-subscribe-patterns` — consuming
- `integration/outbox-pattern` — durable publish
- `integration/cdc-patterns` — alternative for record changes
