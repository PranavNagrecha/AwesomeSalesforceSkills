---
name: flow-platform-events-integration
description: "Use when Flow is a Platform Event publisher, subscriber, or both. Triggers: 'publish platform event from flow', 'platform-event-triggered flow', 'high-volume platform event', 'publish after commit vs immediate', 'PE subscriber error handling', 'integration fan-out from save'. NOT for Change Data Capture — use integration/change-data-capture-integration. NOT for async work that needs no pub/sub — use flow/scheduled-flows."
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
  - "I want to Flow is a Platform Event publisher"
inputs:
  - Platform Event object definition (Standard-Volume or High-Volume)
  - Publisher context (Flow type, caller transaction)
  - Subscriber list (Flow, Apex, external via Pub/Sub API)
outputs:
  - Publisher Flow design with publish semantics selected
  - Subscriber Flow design with idempotency and error handling
  - Fan-out topology and failure-compensation plan
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-19
---

Use this skill when Platform Events are the coordination mechanism between Flow and another component — another Flow, Apex, or an external system. Flow can BOTH publish (by creating records on the event sObject) AND subscribe (via a Platform-Event-Triggered Flow). Both sides have transaction-context, delivery-semantics, and error-handling rules that teams commonly get wrong, producing three recurring defect classes: lost events (publisher succeeded, subscriber never ran), replayed events (subscriber ran twice for one logical message), and out-of-order events (two events delivered in the opposite order from publish).

The objective of this skill is to design loosely-coupled, bulk-safe, fault-tolerant Flow-based pub/sub. If the team cannot answer "what happens if the subscriber fails?" and "what happens if the publisher retries?", the design is incomplete.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- The Platform Event object name and whether it is Standard-Volume or High-Volume.
- The expected publish rate per hour (org-wide and per-event-type).
- Who else subscribes to the event (Apex triggers on `__e`, external Pub/Sub API consumers, other flows).
- Whether the publisher needs publish-after-commit semantics (most record-triggered publishers do).
- The replay / idempotency requirement: can the business tolerate a duplicate subscriber execution?

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Should subscribers hear about a change that later rolls back?" | Publish Immediately has already put the event on the bus when the transaction rolls back (gotcha 1) | Publish After Commit on record-change events |
| "What is the peak publish rate per hour, across every event type in the org?" | The publish allocation is one shared bucket per volume class (gotcha 2) | A rate budget against the edition's allocation |
| "Who is told when a subscriber faults?" | An unhandled subscriber fault completes the delivery and the event is not redelivered (gotcha 3) | A fault path to a durable error log that someone watches |
| "What natural key makes a repeated delivery harmless?" | At-least-once delivery runs a subscriber more than once (gotcha 4) | An idempotency key or unique external ID on the target |
| "Do Apex triggers also subscribe, and does anything depend on their order?" | Flow and Apex subscribers run in an undefined order (gotcha 5) | Independent subscribers, or an explicit second event to chain them |
| "How many events can one transaction publish?" | Create Records on an event inside a loop is one DML per iteration (gotcha 9) | One collection publish per transaction |
| "Does Apex already publish this business event?" | Two publishers emit twice per action (gotcha 10) | One named publisher per business event |

A proper configuration names the publisher, the delivery guarantee and the failure owner before the first event ships, instead of discovering them from duplicate records.

## Recommended Workflow

1. **Classify the event type.** New custom event definitions are high volume by default from API 45.0, and standard-volume custom platform events "will be retired in Summer '27" (`platform_events.txt` 264 L237–239) — design new events as High-Volume and treat a Standard-Volume event as a migration item. Publish timing is a separate, per-event `publishBehavior` choice (step 2).
2. **Design the publisher Flow.** Choose the Flow type (record-triggered after-save is the default for "publish on record change"), and choose the publish mode. For record-change events, `Publish After Commit` prevents phantom events for rolled-back saves.
3. **Design the subscriber Flow.** Create a Platform-Event-Triggered flow, define the entry condition, and plan for idempotency: the same event may be delivered more than once under failure, especially for High-Volume.
4. **Document fan-out.** If multiple subscribers consume the event (Flow + Apex trigger + external), list all of them. Each has independent failure semantics.
5. **Plan error handling.** Publisher failures (publish-limit exhaustion, field validation) must route to a fault log. Subscriber failures do NOT roll back the publisher. Plan compensation.
6. **Compute budget.** Publish counts against per-transaction DML. Subscriber flows consume their own governor budget per delivery batch of up to 200 event messages (`platform_events.txt` 264 L2185).
7. **Validate.** Run `python3 scripts/skill_sync.py --skill skills/flow/flow-platform-events-integration` and the repo-level validator.

## Core Concepts

### Standard-Volume vs High-Volume Platform Events

| Attribute | Standard-Volume | High-Volume |
|---|---|---|
| Publish rate (per hour) | 100,000 org-wide (Enterprise / Performance / Unlimited); 1,000 (Developer, and Professional with API Add-On) | 250,000 org-wide (Enterprise / Performance / Unlimited / Professional with API Add-On); 50,000 (Developer) |
| Publish-after-commit semantics | Set per event by `publishBehavior` | Set per event by `publishBehavior` (`api_meta.txt` 264 L44509–44519); UNVERIFIED (2026-10-20): the corpus states no volume-specific difference |
| Replay / durability | Short-lived buffer | Durable 72-hour event bus with replay via replayId |
| External consumption | Limited | Designed for Pub/Sub API external consumers |
| Best for | Internal Flow-to-Flow or Flow-to-Apex coordination | Integration fan-out, external systems, high-throughput telemetry |

All NEW Platform Event object definitions default to High-Volume; only legacy events are Standard-Volume. Check the object definition's `isStandardVolume` attribute / Setup page.

### Publish Immediately vs Publish After Commit

A record-triggered flow that creates a `Price_Change__e` event can choose:

- **Publish Immediately:** the event is published as soon as the Create Records element runs. If the transaction later rolls back due to a fault, the event has ALREADY been delivered — downstream subscribers act on a change that never happened. This is the source of "phantom event" bugs.
- **Publish After Commit:** the event is buffered and delivered only if the current DML successfully commits. If the transaction rolls back, the event is discarded. This is the safer default for record-change events.

Publish behavior is set on the platform event definition, not on the flow: the event object's `publishBehavior` field takes `PublishAfterCommit` or `PublishImmediately`, applies to messages published from Flow Builder, Apex and Process Builder, and defaults to `PublishImmediately` when unspecified (`api_meta.txt` 264 L44509–44519; `platform_events.txt` 264 L270–272). Every flow that publishes the event inherits that one setting.

### Subscribing With Platform-Event-Triggered Flows

A Platform-Event-Triggered flow activates when a message is delivered on its event channel. Key properties:

- Runs asynchronously in a NEW transaction. Not part of the publisher's transaction.
- Receives the event payload as `$Record` with the event's fields.
- Runs in the context of the user who published the event message — records it creates or updates carry that user in `CreatedById` / `LastModifiedById` — while its debug logs appear under the Automated Process user (`platform_events.txt` 264 L2190–2192). The running-user override `PlatformEventSubscriberConfig` configures a platform event *Apex trigger*, not a flow (`api_meta.txt` 264 L99118; `platform_events.txt` 264 L2366–2368). UNVERIFIED (2026-10-19): the corpus documents no run-as setting for a platform event–triggered flow.
- Gets its own, freshly reset governor limits. Which column (sync or async) a platform event–triggered flow draws from is UNVERIFIED (2026-10-19): `platform_events.txt` 264 says only that each interview runs asynchronously in a separate transaction (L2187–2188), while for platform event *triggers* "the synchronous limits apply" (L2338–2339). Budget against the synchronous column — 100 SOQL, 10 MB heap (`apexdev.txt` 264 L19747, L19780). The heap figure is a Winter '27 release-level change for every org, not an API-version gate; Summer '26 was 6 MB sync / 12 MB async.
- Cannot "reject" the delivery — if the subscriber fails, the platform logs the failure; it does not propagate back to the publisher.
- Batches multiple events into a single flow run — "up to a maximum of 200 event messages", order preserved within the batch, possibly from several publishers (`platform_events.txt` 264 L2185–2186). 2,000 is the platform event *Apex trigger* batch size (`apexdev.txt` 264 L20065), not the flow's.

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
<!-- excerpt: Flow root added so the fragment parses; triggerType is a FlowStart field (api_meta.txt 264 L75233, L75261) -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
<start>
  <triggerType>RecordAfterSave</triggerType>
</start>
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
</Flow>
```

**Why it works:** The Create Records on the event object is the publish action. Because the event definition sets `publishBehavior` to `PublishAfterCommit` (`api_meta.txt` 264 L44509–44517), the event is published only after the transaction commits. If the save rolls back, the event is discarded. No phantom notifications.

**Caveat:** Standard-Volume publishing is allocated 100,000 events per hour org-wide on Enterprise / Performance / Unlimited (1,000 on Developer and Professional-with-API-Add-On), and that bucket is shared across every Standard-Volume event type in the org. A 100,000-record bulk import that publishes one event per record consumes the entire hourly allocation on its own, leaving nothing for any other Standard-Volume publisher — and on Developer or Professional it fails almost immediately. For that cardinality, switch to High-Volume (250,000/hour) or batch the publish. Note that High-Volume publishing is also **org-wide**, not a fresh allocation per event type.

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
<!-- excerpt: Flow root added so the fragment parses; PlatformEvent is a FlowStart triggerType value (api_meta.txt 264 L75233, L75258) -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
<start>
  <object>Case_Status_Changed__e</object>
  <triggerType>PlatformEvent</triggerType>
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
</Flow>
```

**Why it works:** The subscriber runs in its own async transaction. It does not block or interact with the publisher. It has its own governor limits (column UNVERIFIED — see the subscriber bullets above) and isolated failure.

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
- **Subscriber bulk:** the platform batches up to 200 event messages per flow invocation (`platform_events.txt` 264 L2185; 2,000 is the Apex trigger batch, `apexdev.txt` 264 L20065). Your subscriber flow must be bulk-safe. Specifically:
  - The trigger-entry collection ($Record collection) may contain many events.
  - Any Get Records should filter on a Set of input Ids extracted from the event batch, not one event at a time.
  - DML at the end should be against a collection, not per-event.
- **Combined publisher + subscriber math:** if Publisher A publishes 200 events in one transaction and Subscriber B processes them in one batch (200 is the flow's batch ceiling) with 3 DML each, that's 600 DML statements — within the 10,000-DML-row limit but against the 150-statement limit at 3 DML/event * 200 events if not collection-batched. Always collection-batch the subscriber.

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
- **Security:** Each subscriber interview runs in the context of the user who published the event, not the Automated Process user that owns its debug logs (`platform_events.txt` 264 L2190–2192), so test the subscriber as every publishing persona. UNVERIFIED (2026-10-19): how the flow's `runInMode` combines with the publisher's context is not stated.

## Review Checklist

- [ ] The event definition's volume type (Standard vs High) matches the expected publish rate.
- [ ] The publisher uses publish-after-commit semantics for record-change use cases.
- [ ] The publisher guards against per-transaction and per-hour publish limits.
- [ ] Every subscriber flow is designed for idempotency (duplicate delivery handling).
- [ ] Every subscriber flow has a fault path that writes to a durable error log.
- [ ] Multiple subscribers (Flow + Apex + external) are enumerated; ordering dependencies (if any) are documented and known to be unreliable.
- [ ] The subscriber flow is bulk-safe (handles up to 200 event messages per invocation, `platform_events.txt` 264 L2185).
- [ ] The subscriber is tested as each user who publishes the event, since every interview runs in the publisher's context.
- [ ] A compensation or replay strategy exists for subscriber failures.

## Salesforce-Specific Gotchas (short list)

1. Both Standard-Volume and High-Volume publish allocations are ORG-WIDE, not per-event-type — adding a new event type buys no fresh headroom. Standard-Volume: 100,000/hour (Enterprise / Performance / Unlimited), 1,000/hour (Developer, Professional with API Add-On). High-Volume: 250,000/hour (50,000 on Developer).
2. `Publish Immediately` can deliver events that should have rolled back; always prefer after-commit for record-change triggers.
3. Subscriber interviews run in the context of the user who published the event; only their debug logs appear under Automated Process (`platform_events.txt` 264 L2190–2192).
4. At-least-once delivery means idempotency is mandatory.

See `references/gotchas.md` for the full set.

## Related Skills

- `flow/flow-transactional-boundaries` — publish-after-commit vs publish-immediately is fundamentally a boundary choice.
- `flow/flow-bulkification` — subscriber flows must be bulk-safe.
- `flow/fault-handling` — fault connectors and fault paths in publisher and subscriber.
- `apex/trigger-and-flow-coexistence` — Apex and Flow subscribers on the same event.
- `integration/platform-events-integration` — deeper integration patterns including Pub/Sub API and CometD.
- `standards/decision-trees/integration-pattern-selection.md` — routing between PE, CDC, REST, Bulk API.

## Official Sources Used

- Salesforce Developer Documentation — "Platform Events Developer Guide": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Salesforce Help — "Publish Events from a Flow": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_platform_event_publish.htm
- Salesforce Help — "Platform Event–Triggered Flow": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_platform_event.htm
- Salesforce Developer Documentation — "High-Volume Platform Events Allocations": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Salesforce Developer Documentation — "Pub/Sub API": https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Salesforce Architects — "Well-Architected: Resilient" integration patterns: https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Help — "Set the Run Context for a Platform Event–Triggered Flow": https://help.salesforce.com/s/articleView?id=sf.flow_build_config_trigger_pe_runcontext.htm
