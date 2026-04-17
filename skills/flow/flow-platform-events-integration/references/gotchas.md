# Flow Platform Events Integration — Gotchas

## 1. Publish-Immediately Delivers Events That Should Have Been Rolled Back

A flow that publishes an event via `Create Records` with immediate semantics has already pushed the event to the bus by the time a later element throws. If the transaction rolls back, the DML is reversed but the event is NOT recalled. Downstream systems receive a notification for work that never committed.

Avoid it:
- Use publish-after-commit semantics on record-triggered flows whenever the event semantically represents a record change.
- For publish-immediately use cases (telemetry, instrumentation), accept that events can be "ahead of" DML state.

## 2. Standard-Volume Publish Limit Is Org-Wide And Shared

The 6,000/hour Standard-Volume publish limit is ONE shared bucket across all Standard-Volume events in the org. Two separate event types each publishing 4,000 events/hour together exceed the limit, even if individually each looks safe.

Avoid it:
- Move higher-rate events to High-Volume.
- Centralize publish accounting — track which teams publish which events and at what rate.
- Set monitoring alerts on the Platform Event Usage page.

## 3. Subscriber Failure Is Silent

If a Platform-Event-Triggered flow faults and the fault is unhandled, the platform marks the delivery as complete. The event is NOT redelivered. The business message is effectively lost.

Avoid it:
- Every subscriber flow has a fault path connecting to a durable error log object.
- An admin notification or dashboard watches that error log.
- A scheduled retry sweeper is considered for high-value events.

## 4. Duplicate Delivery Creates Duplicate Writes Without Idempotency

At-least-once delivery means the same event may trigger a subscriber multiple times: during platform retry, during redeployment, or during subscriber concurrency. A subscriber that does a naive `Create Records` for every event will create duplicates.

Avoid it:
- Derive a unique natural key from the event payload (e.g., `caseId + changedAt`).
- Check for existing records before creating, OR use a unique external-id index on the target object and catch DUPLICATE_VALUE in the fault path.

## 5. Ordering Between Flow And Apex Subscribers Is Undefined

Two subscribers on the same event — one Flow and one Apex trigger — run independently and in an undefined order. A design that assumes "the Flow runs first to prepare state, then the Apex runs" will fail under concurrency.

Avoid it:
- Do not build inter-subscriber sequences on shared events. Each subscriber is independent.
- If sequence is required, chain via a second event: Subscriber A publishes `Stage_1_Complete__e`, Subscriber B listens for that.

## 6. Platform-Event-Triggered Flow Runs As Automated Process User

By default the subscriber flow runs as the Automated Process user, which has different sharing visibility from the publishing user. A subscriber that queries records may see fewer (or more) rows than expected.

Avoid it:
- Set explicit Run-As context on the PE-triggered flow when sharing matters.
- Document the running user in the design doc.
- Prefer dedicated integration users with scoped permission sets for sensitive subscribers.

## 7. High-Volume Events Do Not Support Publish-After-Commit In The Same Way

High-Volume platform events are delivered to the durable bus quickly; they do not hold for a current DML's commit in the same way Standard-Volume events do for classic publish-after-commit semantics. If publish-after-commit is critical, confirm the event's volume type and publish mode in the definition.

Avoid it:
- Read the event definition's `PublishBehavior` setting and the Salesforce release notes for the current behavior.
- When in doubt, test explicitly: publish, force a rollback, and see whether the subscriber ran.

## 8. Bulk Subscriber Delivery Batches Up To 2,000 Events

A High-Volume Platform-Event-Triggered flow can receive up to 2,000 events in one invocation. A flow that loops and does per-event DML will exhaust limits.

Avoid it:
- Treat the subscriber's `$Record` as a COLLECTION.
- Use the bulkification patterns from `flow/flow-bulkification`: one SOQL against the batch, one DML at the end.

## 9. Events Published In A Loop Can Exceed Per-Transaction DML

Create Records on a Platform Event object inside a Flow Loop counts as DML per iteration. A loop publishing 200 events is 200 DML statements — over the 150-statement limit.

Avoid it:
- Build a collection of event objects and `Create Records` on the collection in one element (one DML).
- Flow's element natively handles a collection of event objects.

## 10. Publishing From Apex And Flow On The Same Object Double-Counts

If both a Flow and an Apex trigger publish events on the same business action (because the Flow was added later), the org now emits 2x events per action. Subscribers see duplicates.

Avoid it:
- Choose ONE publisher per business event.
- When migrating a publisher between Apex and Flow, decommission the old publisher in the same release.

## 11. Screen Flow Publishing In A Pause/Resume Pattern Has Surprising Ordering

A Screen Flow that publishes an event, pauses, then publishes again after resumption creates two events in two different transactions. Publish-after-commit applies per transaction, so the two publishes commit independently. External subscribers may see them in unexpected order if network latency varies.

Avoid it:
- Document the publishing sequence with transaction labels.
- If strict ordering is required, include a sequence field in the event payload.

## 12. Deleting A Platform Event Definition Does Not Retroactively Clear The Bus

For High-Volume events, the 72-hour durable bus retains events even after the definition is deleted. Subscribers may continue to process old events until the retention window passes.

Avoid it:
- When decommissioning an event, deactivate all subscribers FIRST, wait 72 hours, then delete the definition.
- Alternatively, deploy a new version of subscribers that no-op on legacy events.
