---
name: fsl-integration-patterns
description: "Use this skill when designing FSL integrations: ERP parts/inventory sync, GPS/fleet management integration, IoT-triggered work order creation, and customer notification workflows. Trigger keywords: FSL ERP integration, ProductConsumed ERP sync, GPS fleet integration FSL, IoT work order trigger, customer notification FSL integration. NOT for generic Salesforce integration patterns, FSC integration (covered by architect/fsc-integration-patterns-dev), or Health Cloud integration."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
  - Operational Excellence
triggers:
  - "How to sync ProductConsumed parts usage back to ERP inventory system"
  - "IoT device triggers work order creation — how to design the integration pattern"
  - "GPS fleet management integration with FSL service appointments"
  - "ERP inventory sync with FSL ProductRequired and ProductConsumed"
  - "Customer notification integration when field technician is en route"
tags:
  - fsl
  - field-service
  - integration
  - erp
  - iot
  - gps
  - fsl-integration-patterns
inputs:
  - "Source system type (ERP, fleet GPS, IoT, notification platform)"
  - "Integration direction (inbound to FSL, outbound from FSL, or bidirectional)"
  - "Volume and frequency of data exchange"
outputs:
  - "FSL-specific integration pattern recommendation for each integration type"
  - "ProductConsumed ERP round-trip pattern with External IDs"
  - "IoT-to-work-order async pattern using Platform Events"
  - "GPS polling frequency guidance to avoid API limit exhaustion"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Integration Patterns

This skill activates when an architect designs integrations between FSL and external systems: ERP inventory platforms, GPS/fleet management systems, IoT platforms, and customer notification services. FSL's integration patterns have FSL-specific object constraints and anti-patterns that generic Salesforce integration guidance doesn't cover.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether the ERP integration needs to be bidirectional (FSL parts usage back to ERP warehouse stock) or inbound-only (ERP catalog to FSL). The bidirectional pattern requires ProductConsumed → ERP upsert to prevent phantom van stock.
- Confirm whether IoT work order creation needs to be synchronous (immediate on event) or can be async (Platform Event consumed by a Flow or Apex). Synchronous IoT-to-scheduling-trigger integration violates Apex callout limits.
- For GPS integration, confirm the update frequency. Real-time REST polling from Salesforce to the fleet system at high frequency exhausts the Daily API Call limit. The correct pattern is inbound batch updates from the fleet system on a scheduled cadence.
- Identify the customer notification platform (SMS, email, push notification) and whether it requires real-time status triggers or can be driven by FSL Mobile status transitions.

---

## Core Concepts

### ERP Parts Sync — ProductRequired and ProductConsumed

FSL uses two objects to track parts for a job:
- `ProductRequired`: Expected parts listed on a WorkOrderLineItem before the job
- `ProductConsumed`: Actual parts used (consumes from van stock `ProductItem`)

**The bidirectional sync pattern:**
1. ERP → FSL: Sync product catalog and warehouse stock to `Product2` and `ProductItem` (van stock per location)
2. FSL → ERP: After technician records `ProductConsumed`, upsert that consumption back to ERP to decrement warehouse ledger

**Critical gotcha:** If `ProductConsumed` is not upserted back to ERP, the van stock is decremented in Salesforce (from `ProductItem`) but the ERP warehouse ledger still shows the parts as available — creating phantom stock. The technician arrives at the next job expecting parts that were already used.

Both `ProductRequired` and `ProductConsumed` should have External ID fields for upsert-safe ERP round-tripping.

### IoT-Triggered Work Orders

IoT devices (connected assets, sensors) that detect anomalies should trigger work order creation asynchronously:

**Correct pattern:**
1. IoT platform publishes event to Salesforce Platform Event channel
2. Platform Event trigger (Apex or Flow) creates WorkOrder + ServiceAppointment
3. Optional: Call FSL scheduling API via Queueable (never synchronously in the Platform Event handler)

**Anti-pattern:** Calling `FSL.ScheduleService.schedule()` synchronously inside the Platform Event Apex handler. Platform Events fire in an Apex context — scheduling callouts require a fresh async context (Queueable). Synchronous scheduling in the event handler throws `CalloutException`.

### GPS/Fleet Integration

Fleet management systems provide real-time vehicle location data. The common mistake is polling Salesforce as the GPS source, with Salesforce making outbound calls to the fleet API in real-time.

**Correct pattern:** Fleet system pushes batch location updates to Salesforce on a defined schedule (every 5–15 minutes). The fleet system is the source of truth for vehicle location; Salesforce consumes updates, not the reverse.

**Anti-pattern:** Using a Scheduled Apex or Flow on a tight interval (every 1–5 minutes) to poll the fleet API for GPS data. This approach exhausts the Daily API Request limit for high-volume fleets.

### Customer Notifications

Customer notifications (SMS "technician en route", email ETA update) should be triggered by FSL Mobile status transitions:
- Technician taps "En Route" → Platform Event → notification to customer
- ServiceAppointment Status change → Salesforce Flow → notification to customer

The notification platform (Twilio, SendGrid, AWS SNS) is called via Salesforce's external service or named credential integration, triggered by the status change event.

---

## Common Patterns

### ProductConsumed ERP Round-Trip

**When to use:** ERP is the warehouse ledger for parts; FSL Mobile records actual parts usage.

**How it works:**
1. ERP → Salesforce: Nightly batch upsert of Product2 and ProductItem (van stock) with External IDs
2. Technician records ProductConsumed in FSL Mobile: `ProductConsumed.QuantityConsumed` decrements `ProductItem.QuantityOnHand`
3. Salesforce → ERP: Near-real-time Platform Event or scheduled batch upsert of ProductConsumed records back to ERP using External ID
4. ERP processes ProductConsumed records as parts consumption events, decrementing warehouse stock

### IoT Work Order Creation

**When to use:** Connected assets trigger field service dispatch automatically.

**How it works:**
```apex
// Platform Event handler — creates WO and queues scheduling
public class IoTWorkOrderTrigger implements Database.Batchable<SObject> {
    // Trigger creates WorkOrder + ServiceAppointment via DML
    // Then enqueues FslScheduleQueueable (from apex/fsl-scheduling-api skill)
    // Never calls FSL.ScheduleService.schedule() here
}
```

---

## Decision Guidance

| Integration Type | Pattern | Avoid |
|---|---|---|
| ERP parts catalog | Nightly inbound batch upsert with External IDs | Real-time per-product REST calls |
| ERP parts consumption | ProductConsumed Platform Event or scheduled batch → ERP | Ignoring the ERP feedback loop (causes phantom stock) |
| IoT work order creation | Platform Event → Flow/Apex → WO creation → Queueable for scheduling | Synchronous scheduling inside event handler |
| GPS fleet location | Inbound batch from fleet system on cadence | Outbound polling from Salesforce to fleet API at high frequency |
| Customer notifications | Status change trigger → named credential → notification platform | Direct SMS/email from triggers (synchronous callout risk) |

---

## Recommended Workflow

1. **Map integration directions** — For each external system, document whether data flows into FSL, out of FSL, or both. Identify the authoritative system for each data domain.
2. **Design ERP parts feedback loop** — Confirm ProductConsumed → ERP upsert is included. Missing this creates phantom stock.
3. **Use Platform Events for IoT** — Design IoT event ingestion via Platform Events. Keep Work Order creation in the event handler; defer scheduling to a Queueable.
4. **Define GPS update cadence** — Agree on a batch update frequency with the fleet team. Document the Daily API limit implications at each frequency.
5. **Implement notification triggers** — Configure FSL Mobile status transitions as notification triggers via Platform Events or record-triggered Flows.
6. **Add External IDs to all integration objects** — ProductRequired, ProductConsumed, WorkOrder, ServiceAppointment should all have External IDs for idempotent integration operations.
7. **Test integration failure modes** — Test ERP unavailability, GPS feed delays, and IoT event storms. Define retry and dead-letter queue patterns.

---

## Review Checklist

- [ ] ProductConsumed ERP feedback loop designed (not just inbound product sync)
- [ ] IoT scheduling uses async Queueable — not synchronous in event handler
- [ ] GPS integration uses inbound batch push — not outbound polling
- [ ] External IDs on all integration objects for upsert safety
- [ ] API limit analysis done for GPS update frequency
- [ ] Customer notification triggers from FSL Mobile status transitions
- [ ] Integration failure and retry patterns documented

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing ProductConsumed → ERP feedback loop creates phantom stock** — The most common FSL ERP integration gap. Van stock decrements in Salesforce but ERP still shows parts as available, causing technicians to arrive at jobs without the parts they expected.
2. **FSL scheduling callouts cannot be made synchronously inside Platform Event handlers** — Platform Event handlers run in an Apex transaction. Schedule() and GetSlots() are callouts that require no uncommitted DML. Use Queueable for any scheduling that follows a Platform Event.
3. **Daily API limit exhaustion from GPS polling** — Polling the fleet GPS API every 1 minute for 200 vehicles = 288,000 API calls/day. At typical FSL org limits, this exhausts the daily limit by midday. Fleet systems should push to Salesforce, not be polled.
4. **FSL Mobile offline status transitions fire integration triggers at sync — not in real-time** — Customer notifications triggered by status changes will be delayed until the technician syncs. Design notification logic to tolerate sync latency.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSL integration architecture diagram | Data flow diagram for ERP, GPS, IoT, and notification integrations |
| ProductConsumed round-trip design | ERP bidirectional sync pattern with External ID and event trigger |

---

## Related Skills

- architect/fsl-offline-architecture — Offline sync behavior that affects when integration triggers fire
- apex/fsl-scheduling-api — FSL scheduling API patterns for IoT-triggered work order scheduling
- data/fsl-work-order-migration — Work order and ProductConsumed data model context
