---
name: flow-platform-events-integration
description: "Use when Flow is a Platform Event publisher, subscriber, or both. Triggers: 'publish platform event from flow', 'platform-event-triggered flow', 'high-volume platform event', 'publish after commit vs immediate', 'PE subscriber error handling', 'integration fan-out from save'. NOT for Change Data Capture (see integration skills) or for generic async work that does not need pub/sub (see flow/scheduled-flows)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - flow
  - platform-events
  - pub-sub
  - integration
  - decoupling
  - high-volume-events
  - publish-after-commit
triggers:
  - "publish platform event from flow"
  - "platform-event-triggered flow"
  - "high-volume platform event"
  - "publish after commit vs publish immediately"
  - "pe subscriber error handling"
  - "integration fan-out from flow save"
  - "platform event subscriber running user"
inputs:
  - Platform Event object definition (Standard-Volume or High-Volume)
  - Publisher context (Flow type, caller transaction)
  - Subscriber list (Flow, Apex, external via Pub/Sub API)
outputs:
  - Publisher Flow design with publish semantics selected
  - Subscriber Flow design with idempotency and error handling
  - Fan-out topology and failure-compensation plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

Use this skill when Platform Events are the coordination mechanism between Flow and another component — another Flow, Apex, or an external system. Flow can BOTH publish (by creating records on the event sObject) AND subscribe (via a Platform-Event-Triggered Flow). Both sides have transaction-context, delivery-semantics, and error-handling rules that teams commonly get wrong, producing three recurring defect classes: lost events (publisher succeeded, subscriber never ran), replayed events (subscriber ran twice for one logical message), and out-of-order events (two events delivered in the opposite order from publish).

The objective of this skill is to design loosely-coupled, bulk-safe, fault-tolerant Flow-based pub/sub. If the team cannot answer "what happens if the subscriber fails?" and "what happens if the publisher retries?", the design is incomplete.

## When to use this skill

- Publishing a Platform Event from a record-triggered flow, screen flow, or autolaunched flow.
- Designing a Platform-Event-Triggered flow that subscribes to a specific event definition.
- Choosing between Standard-Volume and High-Volume Platform Events.
- Choosing `Publish After Commit` vs `Publish Immediately` semantics.
- Debugging a subscriber flow that "ran but didn't do anything" or "didn't run at all".
- Coordinating Flow subscribers with Apex subscribers (`@Triggered` on `__e`).
- Designing integration fan-out from a save event to multiple downstream systems.

NOT for: Change Data Capture (use the CDC skills), or basic async work that does not need pub/sub topology (use `flow/scheduled-flows` or `flow/flow-transactional-boundaries`).

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- The Platform Event object name and whether it is Standard-Volume or High-Volume.
- The expected publish rate per hour (org-wide and per-event-type).
- Who else subscribes to the event (Apex triggers on `__e`, external Pub/Sub API consumers, other flows).
- Whether the publisher needs publish-after-commit semantics (most record-triggered publishers do).
- The replay / idempotency requirement: can the business tolerate a duplicate subscriber execution?

## Recommended Workflow

1. **Classify the event type.** Decide whether the use case fits Standard-Volume (low-rate, transactional publish-after-commit ordering) or High-Volume (high-rate, Pub/Sub API replay-enabled, no transactional publish-after-commit semantics). Most Flow publishers use Standard-Volume unless the integration target requires high-throughput external consumption.
2. **Design the publisher Flow.** Choose the Flow type (record-triggered after-save is the default for "publish on record change"), and choose the publish mode. For record-change events, `Publish After Commit` prevents phantom events for rolled-back saves.
3. **Design the subscriber Flow.** Create a Platform-Event-Triggered flow, define the entry condition, and plan for idempotency: the same event may be delivered more than once under failure, especially for High-Volume.
4. **Document fan-out.** If multiple subscribers consume the event (Flow + Apex trigger + external), list all of them. Each has independent failure semantics.
5. **Plan error handling.** Publisher failures (publish-limit exhaustion, field validation) must route to a fault log. Subscriber failures do NOT roll back the publisher. Plan compensation.
6. **Compute budget.** Publish counts against per-transaction DML. Subscriber flows consume their own async budget per delivery batch.
7. **Validate.** Run `python3 scripts/skill_sync.py --skill skills/flow/flow-platform-events-integration` and the repo-level validator.

## Core Concepts

### Standard-Volume vs High-Volume Platform Events

| Attribute | Standard-Volume | High-Volume |
|---|---|---|
| Publish rate (per hour) | ~6,000 org-wide default shared with other PE | Much higher; separate per-event-type allocation |
| Publish-after-commit semantics | Yes — only delivers on successful commit | Event is delivered on publish, not tied to DML commit ordering in the same way |
| Replay / durability | Short-lived buffer | Durable 72-hour event bus with replay via replayId |
| External consumption | Limited | Designed for Pub/Sub API external consumers |
| Best for | Internal Flow-to-Flow or Flow-to-Apex coordination | Integration fan-out, external systems, high-throughput telemetry |

All NEW Platform Event object definitions default to High-Volume; only legacy events are Standard-Volume. Check the object definition's `isStandardVolume` attribute / Setup page.

### Publish Immediately vs Publish After Commit

A record-triggered flow that creates a `Price_Change__e` event can choose:

- **Publish Immediately:** the event is published as soon as the Create Records element runs. If the transaction later rolls back due to a fault, the event has ALREADY been delivered — downstream subscribers act on a change that never happened. This is the source of "phantom event" bugs.
- **Publish After Commit:** the event is buffered and delivered only if the current DML successfully commits. If the transaction rolls back, the event is discarded. This is the safer default for record-change events.

In Flow Builder, the `Create Records` element on a Platform Event object exposes a "How to Run the Flow After Save" option that controls publish semantics at the flow level (for record-triggered flows). For autolaunched publishers, you set the immediate/after-commit intent at event definition time (some event types only support one mode).

### Subscribing With Platform-Event-Triggered Flows

A Platform-Event-Triggered flow activates when a message is delivered on its event channel. Key properties:

- Runs asynchronously in a NEW transaction. Not part of the publisher's transaction.
- Receives the event payload as `$Record` with the event's fields.
- Runs as the Automated Process user by default (configurable to a specific user).
- Has async governor limits (200 SOQL, 12 MB heap).
- Cannot "reject" the delivery — if the subscriber fails, the platform logs the failure; it does not propagate back to the publisher.
- Batches multiple events into a single flow run (up to 2,000 per batch for High-Volume).

### Delivery Semantics

| Event type | Delivery guarantee | Replay |
|---|---|---|
| Standard-Volume PE | At-least-once within a short window | Not available |
| High-Volume PE | At-least-once, durable 72h | Yes via replayId in Pub/Sub API |

"At-least-once" means a subscriber MAY be invoked more than once per logical event. Idempotency is the subscriber's responsibility.

### Coordinating Flow and Apex Subscribers

Both a Platform-Event-Triggered flow AND an `apex trigger ... on Event__e (after insert)` can coexist on the same event. They are independent subscribers. Each has its own transaction, governor budget, and failure handling. Running order between Flow and Apex subscribers is NOT guaranteed. Do not design a sequence where the Flow subscriber must run before the Apex subscriber.

## Key Patterns

### Pattern 1: Publish an Event from a Record-Triggered Flow With After-Commit Safety

**When to use:** On a Case save, notify downstream systems that a case status changed. You do NOT want to notify if the save rolls back.

**Pseudo-flow (After-Save on Case):**
```text
[Start: Record-Triggered, After-Save, Create/Update on Case]
  Entry condition: ISCHANGED([Case].Status)
  └── [Create Records: new Case_Status_Changed__e]
         caseId__c  = {!$Record.Id}
         oldStatus__c = {!$Record__Prior.Status}
         newStatus__c = {!$Record.Status}
         changedAt__c = {!$Flow.CurrentDateTime}
  └── [End]
```

**Metadata (publisher):**
```xml
<triggerType>RecordAfterSave</triggerType>
<recordCreates>
  <name>Publish_Status_Change</name>
  <object>Case_Status_Changed__e</object>
  <inputAssignments>
    <field>caseId__c</field>
    <value><elementReference>$Record.Id</elementReference></value>
  </inputAssignments>
  <inputAssignments>
    <field>newStatus__c</field>
    <value><elementReference>$Record.Status</elementReference></value>
  </inputAssignments>
</recordCreates>
```

**Why it works:** The Create Records on the event object is the publish action. Because the flow is After-Save and the event supports publish-after-commit, the event is buffered until the current DML commits. If the save rolls back, the event is discarded. No phantom notifications.

**Caveat:** Standard-Volume events count against the 6,000/hour org-wide publish limit. A 100,000-record bulk import that triggers this flow on each record would exceed the limit by 17x. For that cardinality, switch to High-Volume or batch the publish.

### Pattern 2: Subscribe to an Event With a Platform-Event-Triggered Flow

**When to use:** On `Case_Status_Changed__e`, create an `Audit_Entry__c` row and update a summary on `Account`.

**Pseudo-flow (Platform-Event-Triggered):**
```text
[Start: Platform-Event-Triggered on Case_Status_Changed__e]
  └── [Get Records: Case WHERE Id = {!$Record.caseId__c}]
  └── [Decision: Case found?]
        ├── Yes → [Create Records: new Audit_Entry__c ...]
        │        [Get Records: Account WHERE Id = {!Case.AccountId}]
        │        [Update Records: Account.LastCaseChange__c = {!$Record.changedAt__c}]
        └── No  → [Create Records: Integration_Error_Log__c (case not found)]
[End]
```

**Metadata (subscriber):**
```xml
<triggerType>PlatformEvent</triggerType>
<start>
  <object>Case_Status_Changed__e</object>
</start>
<recordLookups>
  <name>Lookup_Case</name>
  <object>Case</object>
  <filters>
    <field>Id</field>
    <operator>EqualTo</operator>
    <value><elementReference>$Record.caseId__c</elementReference></value>
  </filters>
</recordLookups>
```

**Why it works:** The subscriber runs in its own async transaction. It does not block or interact with the publisher. It has async governor limits and isolated failure.

**Idempotency note:** At-least-once delivery means this flow may run twice for the same event. Before writing the Audit_Entry__c, check for an existing entry with the same `(caseId, changedAt)` tuple. The Audit_Entry__c should have a unique index on `(Case__c, ChangedAt__c)` to enforce this.

### Pattern 3: Fan-Out With High-Volume Events

**When to use:** An order is placed; downstream fulfillment, billing, and analytics must each receive the event. The rate is > 10,000 events/hour.

**Topology:**
```
[Order After-Save] --> publishes [Order_Placed__e (High-Volume)]
                                    |
               +--------------------+---------------------+
               |                    |                     |
  [Flow subscriber]     [Apex @Triggered trigger]   [External Pub/Sub API consumer]
  (creates ShipRequest  (posts to internal          (MuleSoft/Kafka bridge for
   record)               billing queue)              data lake)
```

**Design rules:**
- Use High-Volume to get replay durability and higher throughput.
- Each subscriber is independent. The failure of one does NOT affect the others.
- The external consumer uses replayId to recover from its own outages within 72 hours.
- Publisher (Flow on Order after-save) emits ONE event per order save, not one per downstream subscriber.

### Pattern 4: Publisher Budget Guard

**When to use:** A bulk-save path may publish hundreds of events in one transaction.

**Risk:** Publishing too many events in one transaction hits the per-transaction DML limit (the Create Records on the event object counts as DML). Additionally, the org-wide publish-per-hour limit can be exhausted for Standard-Volume events.

**Mitigation:**
```text
[After-Save Flow]
  └── [Get Records: count $Record collection size]
  └── [Decision: collection size > 100]
        ├── Yes → [Create Records: Batch_Publish_Request__c row per 100]
        │          (a Scheduled Path sweeps Batch_Publish_Request__c rows in smaller batches)
        └── No  → [Create Records: inline PE publish]
```

Alternative: switch the event to High-Volume if the workload demands steady-state high rates.

### Pattern 5: Deliberate Failure Handling in Subscriber

**When to use:** Every subscriber. Not optional.

**Pseudo-flow:**
```text
[Platform-Event-Triggered on Case_Status_Changed__e]
  └── [Get Records: Case] (with Fault Path)
        ├── Happy → continue
        └── Fault → [Create Records: PE_Subscriber_Error_Log__c
                        event_type__c = 'Case_Status_Changed__e'
                        payload_json__c = <serialized $Record>
                        error__c = {!$Flow.FaultMessage}]
                    [Send Custom Notification to Admin Queue]
                    [End] (swallow; platform does not re-deliver on Flow fault)
```

**Key insight:** A Flow subscriber fault does NOT cause redelivery. The platform considers the delivery complete. If you swallow the error silently, the business message is lost. Always log to a durable store and notify.

## Bulk safety

Both publish and subscribe have bulk semantics.

- **Publisher bulk:** when a bulk save invokes the publisher flow, the flow is invoked ONCE with a batched `$Record` collection (up to 200 records per batch). A Create Records on the event object inside a Loop — publishing one event per iteration — is safe IF each iteration is a single Create Records call (Salesforce groups them into one DML operation internally in Flow). But a mis-bulkified publisher can still exceed the per-transaction DML statement count and the org-wide publish-per-hour limit.
- **Subscriber bulk:** the platform batches up to 2,000 events per Flow invocation for High-Volume PEs. Your subscriber flow must be bulk-safe. Specifically:
  - The trigger-entry collection ($Record collection) may contain many events.
  - Any Get Records should filter on a Set of input Ids extracted from the event batch, not one event at a time.
  - DML at the end should be against a collection, not per-event.
- **Combined publisher + subscriber math:** if Publisher A publishes 200 events in one transaction and Subscriber B processes them in one async batch with 3 DML each, that's 600 async DML — within the 10,000-DML-row limit but against the 150-statement limit at 3 DML/event * 200 events if not collection-batched. Always collection-batch the subscriber.

## Error handling

- **Publisher fault (publish-after-commit):** if the DML that was supposed to commit the event rolls back, the event is discarded. This is the correct outcome for record-change events. Log the rollback on the primary save's fault path.
- **Publisher fault (publish immediately):** the event already delivered. Compensate by publishing a corrective event (`Order_Placed_Reversed__e`) on the originating save's fault path.
- **Publish limit exhaustion:** the Create Records on the event throws. Fault path should log and notify admin; do NOT retry in the same transaction (will throw again).
- **Subscriber fault:** platform does NOT redeliver. Log to a durable error-log object. Add a scheduled retry flow that scans the error log and republishes events where appropriate (being careful with idempotency).
- **External (Pub/Sub API) subscriber fault:** the external consumer is responsible for replay using replayId. For High-Volume PEs, the 72-hour durable bus supports this.
- **Duplicate delivery:** design every subscriber to be idempotent. Use a unique key derived from event fields (e.g., `caseId + changedAt`) to detect duplicates.

## Well-Architected mapping

- **Reliability:** Publish-after-commit prevents phantom events. Durable High-Volume events enable external replay. Fault logs on subscribers make at-least-once semantics safe.
- **Performance:** PEs decouple the save transaction from downstream work, improving user-visible save latency. High-Volume PEs scale horizontally with external consumers.
- **Security:** Subscriber flows run as Automated Process user by default; set explicit run-as on Platform-Event-Triggered flows if sharing visibility differs from Automated Process.

## Review Checklist

- [ ] The event definition's volume type (Standard vs High) matches the expected publish rate.
- [ ] The publisher uses publish-after-commit semantics for record-change use cases.
- [ ] The publisher guards against per-transaction and per-hour publish limits.
- [ ] Every subscriber flow is designed for idempotency (duplicate delivery handling).
- [ ] Every subscriber flow has a fault path that writes to a durable error log.
- [ ] Multiple subscribers (Flow + Apex + external) are enumerated; ordering dependencies (if any) are documented and known to be unreliable.
- [ ] The subscriber flow is bulk-safe (handles up to 2,000 events per invocation for High-Volume).
- [ ] The Platform-Event-Triggered flow's run-as context is explicitly chosen.
- [ ] A compensation or replay strategy exists for subscriber failures.

## Salesforce-Specific Gotchas (short list)

1. Standard-Volume events share the 6,000/hour publish limit ORG-WIDE, not per-event-type.
2. `Publish Immediately` can deliver events that should have rolled back; always prefer after-commit for record-change triggers.
3. Subscriber flows run as Automated Process user unless explicitly configured.
4. At-least-once delivery means idempotency is mandatory.

See `references/gotchas.md` for the full set.

## Related Skills

- `flow/flow-transactional-boundaries` — publish-after-commit vs publish-immediately is fundamentally a boundary choice.
- `flow/flow-bulkification` — subscriber flows must be bulk-safe.
- `flow/fault-handling` — fault connectors and fault paths in publisher and subscriber.
- `apex/trigger-and-flow-coexistence` — Apex and Flow subscribers on the same event.
- `integration/platform-events` — deeper integration patterns including Pub/Sub API and CometD.
- `standards/decision-trees/integration-pattern-selection.md` — routing between PE, CDC, REST, Bulk API.

## Official Sources Used

- Salesforce Developer Documentation — "Platform Events Developer Guide": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Salesforce Help — "Publish Events from a Flow": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_platform_event_publish.htm
- Salesforce Help — "Platform Event–Triggered Flow": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_platform_event.htm
- Salesforce Developer Documentation — "High-Volume Platform Events Allocations": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Salesforce Developer Documentation — "Pub/Sub API": https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Salesforce Architects — "Well-Architected: Resilient" integration patterns: https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Help — "Set the Run Context for a Platform Event–Triggered Flow": https://help.salesforce.com/s/articleView?id=sf.flow_build_config_trigger_pe_runcontext.htm
