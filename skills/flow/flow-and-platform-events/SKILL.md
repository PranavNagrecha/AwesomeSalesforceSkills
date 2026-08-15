---
name: flow-and-platform-events
description: "Publish and subscribe to Platform Events from Flow for async decoupling, high-volume triggers, and cross-org signaling. NOT for publish-after-commit semantics, subscriber idempotency, or fan-out failure design — use flow/flow-platform-events-integration. NOT for a flow that just fires on record save — use flow/record-triggered-flow-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
triggers:
  - "flow publish platform event"
  - "platform event triggered flow"
  - "async flow notification"
  - "flow publish high volume event"
tags:
  - platform-events
  - flow
  - async
inputs:
  - "use case (decouple / fan-out / cross-org)"
  - "event payload"
outputs:
  - "PE definition + publish flow + subscribe flow"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow and Platform Events

Platform Events are the platform's async bus, and Flow sits on both ends of it:
a flow publishes by creating a record on the event object, and a
platform-event-triggered flow consumes. Neither operation has a dedicated
element, which is why both are routinely built wrong.

This skill covers the Flow-side mechanics — the publish element and its governor
cost, the subscriber's trigger type and running user, batch size, the
allocations that actually bind, and what a failure looks like from Flow. The
semantics layer above it — publish-after-commit guarantees, idempotency design,
fan-out failure domains — belongs to `flow/flow-platform-events-integration`.

Before building either side, use
[`templates/flow/PlatformEvent_Publisher_Flow.md`](../../../templates/flow/PlatformEvent_Publisher_Flow.md)
as the publisher skeleton rather than starting from a blank canvas. It already
carries the event field design, the `eventId__c` correlation key, and the fault
path.

## Adoption Signals

Reach for an event when the publisher should not wait for, and is not
responsible for, the downstream work: decoupling a slow side effect from a
user-facing save, fanning one business fact out to several independent
consumers, or signalling across orgs.

Do not reach for one when you need the result before the next element runs. That
is a subflow or invocable Apex, in the same transaction. If you catch yourself
designing compensating logic in the publisher to recover from a subscriber
failure, the event was the wrong choice — re-run
`standards/decision-trees/async-selection.md`.

## Recommended Workflow

1. **Define the event with typed fields and a correlation key.** One event per
   business fact, not one envelope with a `type__c` discriminator. Include a
   deterministic id field that subscribers can check-then-act against.
2. **Read the event definition's Publish Behavior before designing the
   publisher.** Publish After Commit spends the shared 150-DML budget; Publish
   Immediately has its own 150-call allocation and fires even on rollback. This
   setting lives on the event, not on the flow.
3. **Publish from an after-save flow with a Create Records element.** Before-save
   flows cannot perform DML, so they cannot publish. Build the collection inside
   any loop and publish once after it. Set `storeOutputAutomatically` to `false`.
4. **Build the subscriber as a platform-event-triggered flow** —
   `<triggerType>PlatformEvent</triggerType>` with the event as `<object>`.
   Remember `$Record` is the event message, not a record: get the real record by
   the Id field the event carried.
5. **Bulkify the subscriber against a 200-message batch.** Collect Ids across the
   batch, one Get Records with an `In` filter, one Update against the collection.
   Lower the flow's maximum batch size only when the per-event work is
   irreducibly expensive.
6. **Size against the peak hour, not the daily total,** using the publishing
   allocation. The delivery allocation does not apply to flows.
7. **Instrument the subscriber as if nobody is watching, because nobody is.**
   Route flow error emails to a monitored alias, fault-connector every DML and
   Action element, and put the event's correlation key on the log row.

## Key Considerations

**The subscriber is batched and shares one governor budget.** Up to 200 event
messages per interview batch. One Get Records per event is 200 SOQL queries
against a synchronous limit of 100 — the most common way a subscriber that
passed testing fails in production.

**Apex and Flow batch differently by 10×.** A platform-event Apex trigger
defaults to 2,000 messages (configurable through `PlatformEventSubscriberConfig`)
against Flow's maximum of 200. Porting a subscriber in either direction changes
its per-transaction cost by an order of magnitude with no change in logic.

**The volume-type decision no longer exists for new events.** Definitions created
at API 45.0 and later are high-volume; standard-volume events can no longer be
defined and the legacy ones are being retired. The live consequence is retention
— 72 hours for high-volume, 24 hours for legacy standard-volume.

**The delivery allocation excludes flows.** Flows, Apex triggers, and Process
Builder consume the *publishing* allocation (250,000 per hour on Enterprise,
Performance, and Unlimited; 50,000 on Developer). The 24-hour delivery allocation
applies to Pub/Sub API, CometD, empApi, and event relays. Reading this backwards
has killed workable internal designs.

**A subscriber runs as Automated Process by default.** No profile, no permission
set assignments, so `$Permission.X` is false for every X and `$User` is not the
human who triggered the publish. Since Spring '24 event-triggered flows can be
configured to run as the Workflow User when they need real record access.

**Subscriber failure is invisible from the publisher.** No rollback, no error on
the triggering record, no notification to the publishing user. The subscriber's
own error email goes to whoever last modified the subscriber flow.

**Replay is not a Flow feature.** Messages are retained in the bus for 72 hours,
and replaying from a Replay Id needs a Pub/Sub API or CometD client. For a
Flow-only design, "we can replay it later" is false.

## Worked Examples (see `references/examples.md`)

- *The publish element, and what it costs* — the XML and the Publish Behavior
  accounting table.
- *The subscriber* — a complete platform-event-triggered flow, and the three ways
  it differs from a record-triggered one.
- *Batch size, wrong vs right* — why a working subscriber breaks at volume.
- *Sizing against the allocations before you build* — the arithmetic, and the two
  conclusions people invert.
- *The failure you will not see* — instrumenting a subscriber nobody is watching.

## Common Gotchas (see `references/gotchas.md`)

- **Subscribers are batched** — up to 200 messages sharing one governor budget.
- **Publish Behavior decides which budget you spend** — and it is set on the
  event, not the flow.
- **Before-save flows cannot publish** — a publish is DML.
- **`$Record` is the event, not the record** — no relationships to traverse.
- **The delivery allocation does not apply to flows** — size against publishing.
- **An Apex subscriber that exhausts its retries stops consuming entirely.**

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Treating the event as transactional with the publisher.
- Publishing inside a loop.
- "Choose high-volume if you expect more than 250,000 a day."
- Assuming one event equals one interview.
- Inventing a "Publish Platform Event" element.

## Related

- `templates/flow/PlatformEvent_Publisher_Flow.md` — canonical publisher shape.
- `flow/flow-platform-events-integration` — semantics, idempotency, fan-out
  failure design.
- `flow/flow-bulkification` — the collection patterns a batched subscriber needs.
- `flow/flow-interview-debugging` — instrumenting the invisible subscriber.
- `standards/decision-trees/async-selection.md` — events vs Queueable vs Batch vs
  Scheduled Flow.
- `standards/decision-trees/integration-pattern-selection.md` — whether the event
  bus is the right integration surface.

## Official Sources Used

- Platform Event Allocations — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Publish Platform Event Messages Using Apex — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- Configure the User and Batch Size for Your Platform Event Trigger — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_trigger_config.htm
- Message Durability (Streaming API) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_durability.htm
- Platform Events Maximum Batch Size Is 200 — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_platform_events_max_batch_size.htm&release=234&type=5

The full annotated list is in `references/well-architected.md`.
