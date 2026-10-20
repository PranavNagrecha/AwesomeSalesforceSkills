# Flow Platform Events Integration — Gotchas

## 1. Publish-Immediately Delivers Events That Should Have Been Rolled Back

A flow that publishes an event via `Create Records` with immediate semantics has already pushed the event to the bus by the time a later element throws. If the transaction rolls back, the DML is reversed but the event is NOT recalled. Downstream systems receive a notification for work that never committed.

Avoid it:
- Use publish-after-commit semantics on record-triggered flows whenever the event semantically represents a record change.
- For publish-immediately use cases (telemetry, instrumentation), accept that events can be "ahead of" DML state.

## 2. Standard-Volume Publish Limit Is Org-Wide And Shared

The Standard-Volume hourly publish allocation is ONE shared bucket across all Standard-Volume events in the org — and so is the High-Volume one. Splitting a workload across two event types buys no extra headroom: on a Developer org (1,000 Standard-Volume publishes/hour) two event types each publishing 600/hour together exceed the allocation even though each looks safe alone. Size against the org's actual edition allocation (Enterprise / Performance / Unlimited: 100,000/hour Standard-Volume, 250,000/hour High-Volume), not against a remembered number.

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

## 6. Platform-Event-Triggered Flow Runs As The Publisher, Not Automated Process

Debug logs for a platform event–triggered flow appear under the Automated Process user, but each interview "runs in the context of the user who published the event message", and records it creates or updates show that publisher in `CreatedById` and `LastModifiedById` (`platform_events.txt` 264 L2190–2192). A design that assumes Automated Process access — because that is whose log it reads — sees different rows depending on who published.

Avoid it:
- Test the subscriber as each publishing persona (integration user, internal user, site user).
- Document the publishing users in the design doc.
- Do not reach for `PlatformEventSubscriberConfig`: it sets the running user of a platform event Apex trigger (`api_meta.txt` 264 L99118). UNVERIFIED (2026-10-19): the corpus documents no equivalent for a flow. If the subscriber needs one fixed least-privilege identity, subscribe with an Apex trigger configured that way.

## 7. High-Volume Events Do Not Support Publish-After-Commit In The Same Way

High-Volume platform events are delivered to the durable bus quickly; they do not hold for a current DML's commit in the same way Standard-Volume events do for classic publish-after-commit semantics. UNVERIFIED (2026-10-20): the corpus sets publish behavior per event definition with no volume restriction (`api_meta.txt` 264 L44509–44519; `platform_events.txt` 264 L270–272), and new custom events have been high volume by default since API 45.0 (L237–238). If publish-after-commit is critical, confirm the event's `publishBehavior` in the definition.

Avoid it:
- Read the event definition's `PublishBehavior` setting and the Salesforce release notes for the current behavior.
- When in doubt, test explicitly: publish, force a rollback, and see whether the subscriber ran.

## 8. Bulk Subscriber Delivery Batches Up To 200 Events

A platform event–triggered flow can receive "a batch of event messages at once, up to a maximum of 200 event messages" (`platform_events.txt` 264 L2185). 2,000 is the batch size of a platform event Apex trigger (`apexdev.txt` 264 L20065), not of a flow. A flow that does one Create Records per event in a 200-event batch issues 200 DML statements against the 150 ceiling (`apexdev.txt` 264 L19757).
UNVERIFIED (2026-10-19): the corpus says a flow receives a batch but not whether `$Record` exposes it as a collection or as one event per interview.

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
