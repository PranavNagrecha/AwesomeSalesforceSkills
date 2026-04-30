---
name: platform-event-schema-evolution
description: "Use when modifying the schema of a Platform Event that already has live publishers and subscribers — adding fields, deprecating fields, or splitting events. Triggers: 'add field to platform event without breaking subscribers', 'platform event versioning', 'evolve event schema safely', 'rename a field on a published event'. NOT for initial event design (use integration/platform-events-integration) or for Change Data Capture event schemas."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "add field to platform event with live subscribers"
  - "rename platform event field without breaking publishers"
  - "platform event v2 alongside v1"
  - "deprecate field on published platform event"
  - "platform event subscriber crashing after schema change"
tags:
  - platform-events
  - schema-evolution
  - versioning
  - integration
inputs:
  - "current event definition (event name, fields, publishers, subscribers)"
  - "proposed change (add / remove / rename / type-change)"
  - "list of subscribers (Apex triggers, Flow, external CometD/Pub-Sub clients)"
outputs:
  - "compatibility classification (safe / risky / breaking)"
  - "rollout plan covering subscriber update order"
  - "fallback / dual-publish strategy when needed"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Platform Event Schema Evolution

Activate when an engineer needs to change the field shape of a Platform Event that already has live publishers and subscribers. The skill classifies the proposed change against Salesforce's compatibility rules, sequences the rollout (publisher-first or subscriber-first), and produces a fallback path when a breaking change is unavoidable.

---

## Before Starting

Gather this context before working on anything in this domain:

- The event API name and its current fields (with types). Use Setup → Platform Events → \[Event\] → Custom Fields & Relationships, or `sf project retrieve start -m PlatformEventChannel:<Name>`.
- All subscribers: Apex triggers (`<EventName>__e` triggers), Flows (Platform-Event-Triggered flows), Pub/Sub API clients, CometD clients, Empirical/Apex Streaming consumers, MuleSoft/3rd-party integration listeners.
- All publishers: Apex `EventBus.publish`, Flow Create-Records on the event object, REST `/services/data/vXX.X/sobjects/<Event>__e/`, MuleSoft event-publish, Outbound Messages routed through events.
- Whether subscribers run inside the same Salesforce org (Apex/Flow) or external (Pub/Sub gRPC, CometD). External subscribers cannot be redeployed atomically with the schema change.

---

## Core Concepts

### Compatibility classes

| Change | Compatibility | Notes |
|---|---|---|
| Add a new field | **Safe** | Existing subscribers ignore unknown fields by default in Apex / Pub-Sub gRPC; CometD JSON consumers must tolerate extra keys |
| Remove a field | **Breaking** | Any subscriber that reads the field fails with null or compile error |
| Rename a field | **Breaking** | Salesforce rename = delete + create; old name vanishes |
| Change a field's type | **Breaking** | Schema fingerprint change; subscribers reject deserialization |
| Mark a field required | **Breaking** for publishers | Existing publishers without the field fail to publish |
| Add a required field | **Breaking** for publishers | Same as above |
| Increase string length / precision | **Safe** | Subscribers accept the wider type |
| Decrease string length | **Risky** | Existing in-flight events may exceed the new length |

### High-volume vs. standard-volume events

Standard-volume events were retired for new orgs years ago; almost all modern events are high-volume. High-volume events are stored in the event bus for 72 hours and replayable by Replay ID. Schema evolution must consider in-flight events: a subscriber may be offline during the change and replay events with the *old* schema after the publisher has switched to the new one.

### The Pub/Sub schema fingerprint

The Pub/Sub API issues a schema ID per event version. External clients fetch the schema by ID and cache it. After a *non-breaking* additive change, both the old and new schema IDs are valid; the bus tags each event with the schema ID it was published under. External subscribers **must** call `GetSchema` for any unknown schema ID instead of hardcoding the ID at deploy time.

---

## Common Patterns

### Pattern: additive change ("safe")

**When to use:** Adding a new optional field to capture more context.

**How it works:** Deploy the field. Old subscribers continue to work — they don't know the field exists. New subscribers read it. No version bump needed.

**Why not the alternative:** Versioning the event (creating `Order_Created_v2__e`) for an additive change creates needless dual-publish complexity.

### Pattern: dual-publish for a breaking change

**When to use:** Renaming a field or changing its type.

**How it works:** Create a new event (`Order_Created_v2__e`) with the new shape. Modify all publishers to publish to **both** v1 and v2. Subscribers migrate from v1 to v2 one at a time, on their own cadence. After the last v1 subscriber deactivates, retire v1.

**Why not the alternative:** A direct rename instantly breaks every subscriber that wasn't redeployed in the same maintenance window — usually impossible across external integrations.

### Pattern: subscriber-tolerant migration

**When to use:** A field is being deprecated. You control all subscribers in-org.

**How it works:** (1) Mark the field deprecated and stop reading it in code. (2) Wait one full event-replay window (≥72h). (3) Stop publishing the field — set it to null but leave the field defined. (4) Wait again. (5) Delete the field.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Adding optional field, all subscribers Apex/Flow | Direct add | Apex tolerates unknown fields automatically |
| Adding required field | Add as optional, backfill, then make required | Required-on-publish breaks existing publishers |
| Renaming a field | New event v2 + dual-publish + phased subscriber migration | Atomic rename across publishers/subscribers is impossible |
| Removing a field, all subscribers in-org and you control deploy | Stop reading → drain replay window → stop publishing → delete | Sequenced over time |
| Removing a field, external subscribers exist | Treat as breaking; dual-publish or version bump | No way to coordinate external subscriber redeploy |

---

## Recommended Workflow

1. Inventory: list every publisher and subscriber. Without this, classifying the change is guessing.
2. Classify against the compatibility table. Safe changes deploy normally; risky and breaking go to step 3.
3. Pick the strategy: additive, dual-publish, or subscriber-tolerant migration. State which one in the change request.
4. For dual-publish, design the v2 event, deploy it, and update publishers to publish to both. Verify subscriber count on v1 starts to decline as subscribers migrate.
5. For subscriber-tolerant migration, gate the change on at least 72 hours between each step (the high-volume event replay window).
6. For external subscribers consuming via Pub/Sub gRPC, confirm they invoke `GetSchema` for unknown schema IDs. If not, schedule the schema change inside their next deploy window.
7. After the migration, retire v1 (delete fields or the event) only after monitoring confirms zero subscribers and zero publishers remain.

---

## Review Checklist

- [ ] Publisher and subscriber inventory complete and dated
- [ ] Change classified against the compatibility table
- [ ] Replay-window timing (≥72h between steps) honored for all in-flight tolerance
- [ ] External subscribers' schema-cache behavior verified
- [ ] Rollback plan: dual-publish makes v1 the rollback target; document the cutover trigger
- [ ] Monitoring in place for failed subscribers (Apex `__e` trigger errors, Flow Platform-Event flow run history)

---

## Salesforce-Specific Gotchas

1. **Rename = delete + create** — Renaming a field on a Platform Event is not metadata-aware; the old name is gone, and Apex referencing it fails at compile.
2. **Required field on publish breaks Flow publishers silently** — Flows publishing to events without the new required field will fail at runtime with no compile-time signal.
3. **Replay catches events across schema changes** — A subscriber offline during a rename can replay 72 hours of pre-rename events after coming back. Subscriber code must tolerate the older schema for the full window.
4. **Field history is not retained** — There is no field-level audit on event metadata. Track schema history in source control / change requests, not in the org.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Compatibility classification | One-line label for the proposed change (safe / risky / breaking) |
| Rollout plan | Ordered steps with timing constraints (replay-window waits) |
| Dual-publish manifest | If used, the v2 event definition + publisher update plan |
| Subscriber inventory | Source-of-truth list with owner contact for each subscriber |

---

## Related Skills

- integration/platform-events-integration — for the foundational event-bus mechanics
- integration/event-relay-configuration — when external bus relays must coordinate the change
- integration/idempotent-integration-patterns — when dual-publish creates near-duplicate events
- apex/change-data-capture-apex — for CDC events, which use a related but distinct schema-evolution model
