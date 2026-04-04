---
name: event-driven-architecture-patterns
description: "Use when choosing between Salesforce event-driven mechanisms — Platform Events, Change Data Capture (CDC), Streaming API (PushTopic), and Outbound Messages — to determine which pattern fits a given integration requirement. Trigger keywords: platform events vs CDC, choose event pattern, event-driven integration design, streaming API vs platform events, outbound message vs platform event, event architecture comparison. NOT for implementing any single pattern (use platform-events-integration, change-data-capture-integration, or streaming-api-and-pushtopic for that), and NOT for automation tool selection between Flow and Apex."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
tags:
  - platform-events
  - change-data-capture
  - streaming-api
  - outbound-messages
  - event-driven-architecture
  - integration-patterns
triggers:
  - "should I use platform events or change data capture for this integration"
  - "what is the difference between CDC and platform events for external system sync"
  - "deciding between outbound messages and platform events for workflow integration"
  - "which Salesforce streaming mechanism should I pick for real-time notifications"
  - "comparing platform events streaming API CDC outbound messages architecture decision"
inputs:
  - "Direction of event flow (Salesforce-to-external, external-to-Salesforce, or bidirectional)"
  - "Trigger source: DML operation on a record, business process/workflow, or an external system publishing"
  - "Required event payload: record field deltas only, custom domain fields, or arbitrary data"
  - "Subscriber technology: external middleware, browser client, Apex, or Flow"
  - "Throughput requirements (events per day) and retention window needed (24h, 72h, or longer)"
  - "Org edition and whether SOAP endpoint on the receiving side is acceptable"
outputs:
  - "Recommended event mechanism with rationale against the decision matrix"
  - "Identified tradeoffs for the top-2 candidates"
  - "Risk factors and constraints to validate before committing to the pattern"
  - "Pointer to the implementation skill for the chosen mechanism"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Event-Driven Architecture Patterns

Use this skill when the question is *which* Salesforce event-driven mechanism to use for an integration requirement — not *how* to implement the chosen one. This is the selection layer: understanding the structural differences between Platform Events, Change Data Capture, Streaming API (PushTopic), and Outbound Messages, and applying a decision framework to pick the right one before any implementation begins.

Getting this choice right at the design stage avoids expensive re-architecture. Platform Events and CDC share infrastructure (Pub/Sub API) but serve fundamentally different purposes. Streaming API (PushTopic) is a legacy mechanism still suitable for narrow browser-push use cases. Outbound Messages remain the only built-in option when the receiving endpoint speaks SOAP.

---

## Before Starting

Gather this context before applying the decision framework:

- **Who initiates the event?** Platform Events can be published by Apex, Flow, or external REST calls — the event is intentional and explicit. CDC fires only from Salesforce DML; it cannot be triggered manually or by an external system.
- **What payload is required?** CDC always includes the full set of changed fields in the `ChangeEventHeader` automatically. Platform Events carry only the fields you define on the event object. Streaming API (PushTopic) delivers only the fields listed in the SOQL SELECT clause.
- **Who consumes the event and with what technology?** Apex triggers, Flow, CometD clients, and Pub/Sub API gRPC clients each have different channel types and capability surfaces.
- **What are the volume and retention requirements?** Limits differ significantly across mechanisms and editions.
- **Is SOAP acceptable on the receiving end?** Outbound Messages are SOAP-only; if the receiver cannot process a SOAP envelope, this option is eliminated.

---

## Core Concepts

### Platform Events

Platform Events are a custom publish-subscribe mechanism on the Salesforce Event Bus. Publishers push events explicitly — via `EventBus.publish()` in Apex, a Publish action in Flow, or a REST POST to `/services/data/vXX.0/sobjects/MyEvent__e/`. Subscribers can be Apex triggers (using `@isTest` or `after insert` on the event sObject), Flow elements, or external systems via CometD (Streaming API) or the Pub/Sub API (gRPC).

Key characteristics:
- Events are decoupled from any specific sObject; the event schema is fully custom.
- Default retention is **72 hours** with replay via `replayId`.
- Standard event allocation: **250,000 events per 24 hours** on Enterprise and above (lower on lower editions; check the Platform Events Developer Guide for per-edition allocations).
- High-Volume Platform Events bypass the per-org standard allocation and support `RetainUntilDate` for extended retention beyond 72 hours.
- Fire-and-forget from the publisher's perspective — Apex publisher failures surface as `EventBus.publish()` return values, not exceptions.

Use Platform Events when the integration requires a **custom, domain-specific event payload** that is not tied to a specific record's field changes, or when the publisher is an external system or a business process rather than a DML operation.

### Change Data Capture (CDC)

CDC automatically generates `ChangeEvent` messages on the Salesforce Event Bus whenever a record is created, updated, deleted, or undeleted. No publisher code is required — Salesforce generates the event as part of the DML transaction.

Key characteristics:
- The event payload includes a `ChangeEventHeader` with `changeType` (CREATE, UPDATE, DELETE, UNDELETE, or GAP_* variants), `changedFields` (list of fields that changed), and `recordIds`. The body includes all changed field values plus system fields.
- Replay window is **72 hours** using `replayId`.
- Standard allocation: **5 entity selections** per org (e.g., Account, Contact, Opportunity each count as one). Additional entities require a Change Data Capture add-on license.
- CDC is **not available for all standard objects**. Task and Event have partial support (change events for Task are available but with restrictions; Case Feed changes are not in CDC scope). Check the CDC Developer Guide's supported objects list before committing.
- Subscribers use the same Pub/Sub API or CometD transport as Platform Events, but subscribe to `/data/ChangeEvents` or `/data/<ObjectName>ChangeEvent` channels.
- Gap events (`GAP_CREATE`, `GAP_UPDATE`, etc.) indicate missed events — subscribers must handle these by fetching current record state from the REST API.

Use CDC when an **external system needs to mirror Salesforce record changes** (e.g., syncing Accounts to an ERP) and the payload must include field-level deltas without custom publisher code.

### Streaming API (PushTopic)

The Streaming API predates Platform Events. It uses SOQL-based PushTopic records to define which record changes to stream, and delivers events via CometD long-polling to external clients. Generic Streaming channels (`StreamingChannel`) allow arbitrary payload delivery.

Key characteristics:
- Event retention: **24 hours** (not 72 — a common confusion with Platform Events and CDC).
- Standard allocation: approximately **50,000 events per 24 hours** org-wide across all PushTopic channels.
- Only fields in the PushTopic SOQL SELECT clause are included in the payload — there is no automatic field-delta tracking.
- PushTopic SOQL has significant restrictions: no aggregate functions, no relationship traversal in SELECT, no LIMIT or OFFSET.
- Maximum **1,000 concurrent subscribers** org-wide (100 per individual channel).
- PushTopic is considered a **legacy mechanism** as of the Platform Events era. Salesforce recommends migrating to Platform Events or CDC for new integrations.

Use Streaming API (PushTopic) only when: (1) you are maintaining a legacy integration that already uses it and migration cost is prohibitive, or (2) the use case is a lightweight real-time push to a browser client already using CometD and the 24-hour retention and throughput limits are acceptable.

### Outbound Messages (Workflow)

Outbound Messages are a workflow-triggered SOAP notification to an external HTTPS endpoint. When a Workflow Rule fires, Salesforce sends a SOAP envelope containing specified field values to the configured endpoint URL. The external endpoint must acknowledge receipt with a SOAP acknowledgment; Salesforce retries delivery until an ack is received (at-least-once delivery).

Key characteristics:
- **SOAP-only** — no REST or JSON delivery option.
- Triggered only by **Workflow Rules** (legacy automation). Cannot be triggered by Flow, Apex, or Process Builder directly (though a Flow can trigger a Workflow Rule via a record update in some patterns).
- No payload transformation — the payload is fixed to the fields selected at configuration time.
- At-least-once delivery with retry — the external system must be idempotent.
- Workflow Rules and Outbound Messages are a **legacy mechanism** that Salesforce has soft-deprecated in favor of Flow + Platform Events. As of Spring '25, new Workflow Rules cannot be created in new orgs.
- No replay capability — if the endpoint is down and the retry window expires, the event is lost.

Use Outbound Messages only when the external endpoint **requires SOAP** and the triggering event is a Workflow Rule already in production that cannot be migrated.

---

## Decision Matrix

| Requirement | Platform Events | CDC | Streaming API (PushTopic) | Outbound Messages |
|---|---|---|---|---|
| Custom event payload (non-record) | **Best fit** | Not applicable | Generic Streaming only | Not applicable |
| Record field-change stream to external system | Possible (publish on trigger) | **Best fit** | Limited (SOQL select only) | Legacy option |
| Publisher is an external system | **Supported** (REST POST) | Not possible | Not possible | Not possible |
| Publisher is a Workflow Rule | Not directly | Not applicable | Not applicable | **Only option** |
| Payload includes automatic field deltas | No (custom fields only) | **Yes (changedFields)** | No (SELECT only) | No |
| Subscriber is a browser LWC client | Via empApi / CometD | Via CometD | **Native (legacy)** | Not applicable |
| Subscriber is Apex trigger | **Yes** | **Yes** | No | No |
| Subscriber is Flow | **Yes** | No | No | No |
| Subscriber is external via gRPC | Pub/Sub API | Pub/Sub API | No | No |
| Event retention window | 72 hours (HV: configurable) | 72 hours | **24 hours** | No replay |
| Standard throughput (events/day) | 250k (Enterprise+) | 5 entities free | ~50k events | Unlimited retries |
| SOAP endpoint required on receiver | No | No | No | **Only option** |
| Requires object DML to fire | No | **Yes (always)** | Yes | Yes |

---

## Common Patterns

### Pattern 1 — Decoupled Business Event Integration (Platform Events)

**When to use:** An order management system, CPQ tool, or Apex process needs to signal that a business milestone has occurred (e.g., "Order Shipped", "Quote Approved") and one or more downstream systems or Salesforce automation steps need to react. The event is application-level, not a direct record-change notification.

**How it works:**
1. Define a Platform Event (`OrderShipped__e`) with domain-specific fields (`OrderId__c`, `ShippedDate__c`, `CarrierId__c`).
2. Publisher (Apex, Flow, or external REST) fires the event explicitly.
3. Subscribers register independently: an Apex trigger updates related records, a Flow sends a notification, and an external middleware enriches an ERP order record.
4. All subscribers are decoupled — no direct call, no shared transaction.

**Why not CDC:** CDC cannot carry custom fields or fire for non-DML events. If the "Order Shipped" milestone requires enriched context beyond what a standard field update expresses, Platform Events are the correct choice.

### Pattern 2 — Record Synchronization to External System (CDC)

**When to use:** An external ERP, data warehouse, or master data management platform needs to stay in sync with Salesforce Account, Contact, or Opportunity field changes without polling or custom trigger code.

**How it works:**
1. Enable CDC for the relevant entities in Setup (Change Data Capture settings).
2. External subscriber (MuleSoft, Kafka connector, custom gRPC client via Pub/Sub API) subscribes to `/data/AccountChangeEvent`.
3. On each change event, the subscriber reads `ChangeEventHeader.changedFields` to determine which fields changed, then applies the delta to the target system.
4. Gap events (`GAP_UPDATE`, etc.) trigger a full-state fetch from the Salesforce REST API to reconcile missed changes.
5. Subscriber persists the last processed `replayId` durably for restart recovery.

**Why not Platform Events:** Building a Platform Event publishing infrastructure to replicate CDC behavior — Apex triggers on every object to publish events with field deltas — is far more code, has more failure modes, and requires maintaining the field list manually. CDC does this automatically.

### Pattern 3 — Legacy Workflow Notification to SOAP Endpoint (Outbound Messages)

**When to use:** A legacy system integration requires SOAP delivery on a record status change, and the Workflow Rule and Outbound Message are already in production with no migration budget.

**How it works:**
1. Workflow Rule fires on the record condition (e.g., `Status = 'Closed'`).
2. Outbound Message sends selected field values as SOAP to the configured endpoint.
3. Endpoint processes the payload and returns a SOAP acknowledgment.
4. If acknowledgment fails, Salesforce retries up to 24 hours.

**Why not Platform Events:** If the receiving endpoint speaks SOAP and cannot be changed, Platform Events cannot fulfill the delivery requirement without a middleware translation layer. However, if the endpoint can be updated, migrating to a Platform Event subscriber is the strategic path forward.

---

## Recommended Workflow

1. **Identify the trigger source** — Determine whether the event originates from a Salesforce DML operation (CDC is viable), a business process or Apex/Flow action (Platform Events are viable), a Workflow Rule (Outbound Messages are the legacy path), or an external system (only Platform Events via REST).
2. **Identify the subscriber technology and requirements** — Confirm whether the subscriber is Apex, Flow, a browser LWC, external middleware, or a SOAP endpoint. Eliminate options that do not support the subscriber's protocol.
3. **Apply the decision matrix** — Work through the payload, retention, and throughput rows of the decision matrix. Eliminate any mechanism that cannot meet a hard requirement.
4. **Validate against org limits and edition** — Confirm CDC entity allocation (5 entities free), Platform Event daily allocation (250k on Enterprise), and Streaming API concurrent subscriber limits before finalizing.
5. **Select the implementation skill** — Route to `integration/platform-events-integration`, `integration/change-data-capture-integration`, `integration/streaming-api-and-pushtopic`, or the relevant implementation skill for the chosen mechanism.
6. **Document the decision** — Record the chosen mechanism, the key requirements that drove the selection, and the alternatives considered with reasons they were eliminated.

---

## Review Checklist

- [ ] Trigger source identified: DML, business process, Workflow Rule, or external system.
- [ ] Subscriber protocol confirmed: Apex, Flow, CometD, Pub/Sub API, or SOAP.
- [ ] Payload requirements checked: custom fields vs. automatic field deltas vs. SOQL select.
- [ ] Retention window requirement validated against mechanism limits (24h, 72h, configurable).
- [ ] Throughput requirement validated against mechanism limits and org edition.
- [ ] CDC entity allocation checked if CDC is the candidate (5 entities free, add-on for more).
- [ ] Object CDC support confirmed if CDC is the candidate (not all objects supported).
- [ ] Outbound Messages considered only when SOAP is a hard requirement.
- [ ] Decision documented with rationale and alternatives considered.

---

## Salesforce-Specific Gotchas

1. **CDC cannot be triggered manually or by external systems** — CDC fires only from Salesforce DML (create, update, delete, undelete on enabled objects). Teams that want to publish CDC-like events from an external system or from Apex without an actual record change must use Platform Events instead. There is no API to manually fire a CDC event.
2. **Streaming API retention is 24 hours, not 72** — Platform Events and CDC both retain events for 72 hours. The Streaming API (PushTopic) retains for only 24 hours. Teams migrating PushTopic subscriptions to Platform Events sometimes assume the retention is the same, then design recovery logic based on incorrect assumptions.
3. **CDC is not available for all objects** — The CDC Developer Guide lists supported standard objects. Task and Event have limited CDC support (Task change events exist but have restrictions; activity-related objects are partially excluded). Before committing CDC for a use case involving Activities, confirm support in the official list.
4. **Outbound Messages are tied to Workflow Rules, which cannot be created in new orgs as of Spring '25** — Outbound Messages depend on Workflow Rules. New orgs created after Spring '25 do not support creating new Workflow Rules. Any net-new integration that previously would have used Outbound Messages must be implemented using Platform Events + Apex/Flow subscriber instead.
5. **Platform Events are fire-and-forget from the publisher — there is no delivery confirmation to the publisher** — Unlike Outbound Messages (which retry until the endpoint acks), Platform Event publishers receive a `replayId` in the publish response but have no built-in mechanism to confirm that all subscribers received and processed the event. Subscriber reliability is the subscriber's responsibility.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Mechanism recommendation | Named event mechanism with the key requirements that drove the selection |
| Decision matrix summary | Completed matrix showing which mechanisms were eliminated and why |
| Tradeoff notes | Top-2 candidate comparison with risk factors for the chosen option |
| Implementation skill pointer | Reference to the specific implementation skill (platform-events-integration, change-data-capture-integration, etc.) |

---

## Related Skills

- `integration/platform-events-integration` — External publishers and subscribers via CometD or Pub/Sub API for Platform Events.
- `apex/platform-events-apex` — Apex-side publishing and subscribing to Platform Events via triggers and `EventBus.publish()`.
- `integration/change-data-capture-integration` — Implementing external CDC subscriptions with replay, gap handling, and Pub/Sub API.
- `integration/streaming-api-and-pushtopic` — Setting up and troubleshooting PushTopic and Generic Streaming channels via CometD.
- `architect/platform-selection-guidance` — Broader platform feature selection including CDC vs Platform Events vs Outbound Messaging alongside other platform-level decisions.
