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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
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

Standard Platform Events are stored with a ReplayId; subscribers can replay from a specific Id (up to 72 hours). High-Volume events have different durability.

### Event allocation

Events are counted against an org's monthly Platform Event allocation (license-dependent). Bulk publishes consume one allocation unit per event published.

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
