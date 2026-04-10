# Gotchas — FSL Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing ProductConsumed → ERP Feedback Causes Phantom Stock

**What happens:** FSL's `ProductConsumed` record decrements `ProductItem.QuantityOnHand` in Salesforce. If this consumption is not upserted back to the ERP warehouse ledger, the ERP still shows the parts as available. Future dispatch decisions based on ERP inventory data lead technicians to jobs without the parts they need.

**When it occurs:** Any FSL-ERP integration that has an inbound product sync (ERP → Salesforce) but no outbound consumption feedback (Salesforce → ERP).

**How to avoid:** Explicitly design and implement the ProductConsumed → ERP feedback loop as part of the inventory integration. Use Platform Events or scheduled batch to push consumption records to ERP.

---

## Gotcha 2: Scheduling Callouts Cannot Run Inside Platform Event Handlers

**What happens:** Calling `FSL.ScheduleService.schedule()` or `FSL.AppointmentBookingService.GetSlots()` directly inside a Platform Event Apex handler throws `CalloutException: You have uncommitted work pending`. Platform Event handlers run in a transaction; DML that creates WorkOrder or ServiceAppointment records precedes the callout in the same transaction.

**When it occurs:** IoT or event-driven work order creation patterns that try to auto-schedule the appointment in the same event handler that creates the records.

**How to avoid:** Create Work Order and ServiceAppointment records in the Platform Event handler. Enqueue a `Queueable` (that implements `Database.AllowsCallouts`) for the scheduling call. The Queueable runs in a fresh transaction without the DML constraint.

---

## Gotcha 3: Outbound GPS Polling Exhausts Daily API Limits

**What happens:** A Scheduled Apex job that polls a fleet GPS API on a short interval (1–5 minutes) for many vehicles quickly exhausts the Salesforce Daily API Request limit, blocking other integrations, deployments, and Apex code.

**When it occurs:** Any GPS/fleet integration where Salesforce is designed as the poller rather than the recipient.

**How to avoid:** Design fleet GPS as an inbound push from the fleet system to Salesforce. The fleet system updates Salesforce on a scheduled cadence (every 10–15 minutes). Salesforce never makes outbound calls to retrieve GPS data.

---

## Gotcha 4: FSL Mobile Status Changes During Offline Fire Integration Triggers at Sync

**What happens:** Customer notification integrations triggered by FSL Mobile status changes (e.g., "En Route" triggers an SMS to the customer) don't fire in real-time for offline technicians. The trigger fires when the device syncs — which may be 1–4 hours after the technician actually went en route.

**When it occurs:** Deployments where technicians work in areas with intermittent connectivity and a customer notification integration fires on status change events.

**How to avoid:** Design customer notification integrations with FSL Mobile offline behavior in mind. Consider adding a "delayed notification" disclosure to customer communication, or implement a notification at the scheduled appointment time (independent of status change) as a fallback.

---

## Gotcha 5: ERP Upsert Requires Both External IDs and Idempotent Processing

**What happens:** ERP integration that uses plain insert (not upsert) for ProductConsumed creates duplicate consumption records if the integration runs twice due to a retry after network failure. Duplicate ProductConsumed records double-decrement `ProductItem.QuantityOnHand`, causing negative van stock.

**When it occurs:** Integration without External IDs or without idempotency controls on the ERP receiving side.

**How to avoid:** Add External IDs to ProductConsumed (and ProductRequired) for upsert-safe ERP operations. Implement idempotency checks on the ERP side using the External ID as the deduplication key.
