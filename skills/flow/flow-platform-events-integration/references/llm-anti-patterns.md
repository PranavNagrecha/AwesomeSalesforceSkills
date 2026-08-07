# Flow Platform Events Integration — LLM Anti-Patterns

AI assistants misjudge Platform Event integration in predictable ways. Each item below has been observed in generated designs and reviews.

## 1. Recommending Platform Events as a Generic "Make It Async" Tool

Platform Events are specifically for publish/subscribe topology with multiple independent consumers. For single-consumer async work, a Scheduled Path or Queueable is simpler, cheaper (no publish-limit tax), and easier to monitor. An assistant that proposes PEs for a single-destination enrichment is over-engineering.

Correct approach:
- Recommend PEs only when multiple independent subscribers exist OR external consumption via Pub/Sub API is required.
- For single-consumer async, prefer Scheduled Path or Queueable.

## 2. Claiming the Publisher and Subscriber Share a Transaction

An assistant writing "after publishing the event, the subscriber runs and updates Y" as if they are in one sequence is wrong. The subscriber runs in a separate, asynchronous transaction. The publisher's caller has already moved on.

Correct approach:
- Explicitly state the transaction boundary between publish and subscribe.
- Design subscriber idempotency and error handling independently of the publisher.

## 3. Omitting Fault Paths on Subscribers "Because Delivery Is Guaranteed"

Delivery is at-least-once, but subscriber EXECUTION is not guaranteed to succeed. An unhandled fault in a subscriber flow is silently swallowed by the platform. An assistant that skips fault handling on subscribers guarantees silent data loss.

Correct approach:
- Every subscriber design includes a fault path to a durable error log.
- The reviewer asserts the presence of the fault path as a gate.

## 4. Proposing Strict Ordering Between Flow and Apex Subscribers

When asked "how do I make sure the Apex trigger runs before the Flow subscriber", the correct answer is: you can't. Subscribers run independently. An assistant that proposes sleep loops, invocable chaining, or subflow tricks to enforce order is incorrect.

Correct approach:
- Explain that ordering across heterogeneous subscribers is undefined.
- If ordering is required, chain via a secondary event.

## 5. Publishing Inside a Flow Loop With Per-Iteration Create Records

A naive implementation publishes one event per loop iteration. This is a bulkification anti-pattern: 200 iterations = 200 DML = over limit.

Correct approach:
- Build a collection of event objects in the loop.
- Use a single Create Records element against the collection at the end.

## 6. Ignoring the Org-Wide Publish Limit on Standard-Volume Events

Assistants propose a Standard-Volume PE for a high-rate use case without checking the org's edition. On Developer or Professional-with-API-Add-On the Standard-Volume publish allocation is only 1,000/hour, so a 10k/hour design fails there while passing on Enterprise (100,000/hour). The first symptom is `LIMIT_EXCEEDED: Event publishing rate limit reached`.

Correct approach:
- Ask the expected publish rate explicitly.
- Route rates > 1,000/hour toward High-Volume and confirm against the org's allocated allowance.

## 7. Treating Publish-After-Commit as a Reliability Feature

Publish-after-commit is a CORRECTNESS feature for record-change events — it prevents phantom deliveries on rolled-back saves. It is NOT a reliability feature in the sense of retries or durability. An assistant that sells publish-after-commit as "reliable delivery" confuses two orthogonal concerns.

Correct approach:
- Explain publish-after-commit as "don't deliver if the save rolled back."
- Durability / replay is a High-Volume property; publish-after-commit is a timing property. They are independent.

## 8. Assuming Subscriber Runs Synchronously After Publish

An assistant writes: "after you publish, query the target record and you'll see the subscriber's update." You will NOT. The subscriber is async and may not have run yet. The publisher should never query for the subscriber's output.

Correct approach:
- Use a separate sync step or an explicit wait/event-driven confirmation if the publisher needs to see subscriber output.
- Better: restructure so the caller doesn't need the output at all.

## 9. Omitting Idempotency Design

An assistant generates a subscriber that always creates a child record per event. Duplicates create duplicate children. The bug shows up under load, not in sandbox single-record tests.

Correct approach:
- State the idempotency key (fields in the payload that identify the logical message).
- Implement a "check-then-create" or a unique index with duplicate-catch fault path.

## 10. Recommending Platform Events For Intra-Transaction Coordination

Two flows that need to coordinate on the SAME record save should not use Platform Events. The subscriber runs in a future transaction; the data in question is in the current transaction. An assistant that proposes PEs for "communicating between flows in one save" is misdirecting.

Correct approach:
- For intra-transaction coordination, use subflows, invocable Apex, or order the flows by trigger order.
- Reserve PEs for cross-transaction, cross-component, or cross-org coordination.

## 11. Forgetting That Subscriber Batches Are Bulked

A subscriber designed as if it receives exactly one event per invocation will fail under High-Volume. The assistant should always design the subscriber for a batch of up to 2,000 events.

Correct approach:
- Subscriber flow starts with Assignment elements that collect ids from the `$Record` collection.
- SOQL and DML inside the subscriber operate on collections, not individual events.

## 12. Neglecting Running-User Context on Subscribers

An assistant might write a subscriber flow that queries `ContactAccess__c` records assuming the flow runs as the event publisher. It runs as the Automated Process user. Sharing may yield empty results.

Correct approach:
- Explicitly set Run-As or assign a dedicated integration user.
- Document expected sharing behavior at the subscriber boundary.

## 13. Suggesting External Publish via Flow Instead of Via Apex

To publish to an external system, you do NOT publish a Salesforce Platform Event — you make an outbound callout. An assistant that proposes "publish a Platform Event, then an external system picks it up" without confirming the external system is a Pub/Sub API consumer is wasting effort.

Correct approach:
- Confirm whether the external system subscribes via Pub/Sub API.
- If not, use outbound callout (REST via Named Credential + invocable Apex) directly.


---

## Anti-Pattern: The fabricated "6,000 platform events per hour" allocation

**What the LLM generates:**

> "Standard-Volume platform events share a 6,000/hour org-wide publish limit. A 100,000-record bulk import would exceed it by 17x — switch to High-Volume, which has a separate per-event-type allocation."

**Why it happens:** No 6,000/hour figure appears anywhere in the Platform Event Allocations table. The number is a plausible-looking invention that then *propagates into arithmetic*: "exceed the limit by 17x" is exactly 100,000 ÷ 6,000, so a downstream worked example silently inherits the fabricated base and looks rigorous. That is the signature to watch for — a fabricated constant becomes much harder to spot once a calculation has been derived from it. The paired "separate per-event-type allocation" claim is a second, independent error: it is the intuitive mental model (more event types = more headroom) rather than the documented one.

**Correct version** (Platform Event Allocations):

| | Enterprise / Performance / Unlimited | Developer / Professional w/ API Add-On |
|---|---|---|
| Standard-volume publishes per hour | 100,000 | 1,000 |
| High-volume publishes per hour | 250,000 | 50,000 (Developer) |
| High-volume event **deliveries** per 24 h | 50,000 (Perf/Unl) / 25,000 (Ent) | 10,000 (Developer) |

Every one of these is **org-wide**. Adding a second event type buys no additional headroom in either tier. The 24-hour delivery allocation is shared with Change Data Capture and is usually the binding constraint, not the publish rate.

**Detection hint:** grep Flow/integration guidance for `6,000` or `6000` near `event` — it is not a platform-event allocation figure. Two structural hints that generalise: (1) an allocation quoted **without an edition** is suspect, because every platform-event allocation is edition-scoped; (2) a limit claim immediately followed by an "exceeds by Nx" calculation — verify the base before trusting the arithmetic, because the calculation is evidence the author committed to the number, not evidence the number is right. Third hint: any claim that an allocation is "per event type."
