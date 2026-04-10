# Gotchas — FSL Mobile Workflow Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SA Status Does Not Cascade to Work Order Status

**What happens:** When a technician marks a Service Appointment as "Completed" (or any other status) in FSL Mobile, the parent Work Order status does not change. The SA and WO have separate status fields with no built-in link.

**When it occurs:** Every deployment where downstream processes (billing, SLA reporting, inventory replenishment) depend on Work Order status. Without explicit automation, the WO remains in its pre-appointment status indefinitely after the technician finishes work.

**How to avoid:** Build a Record-Triggered Flow on ServiceAppointment that updates the related WorkOrder.Status whenever SA.Status changes. For Work Orders with multiple Service Appointments, include a check that all sibling SAs are "Completed" before marking the WO "Completed".

---

## Gotcha 2: Server-Side Logic (Triggers, Validation Rules, Standard Flows) Does Not Execute Offline

**What happens:** Apex triggers, validation rules, and standard Flows on any object (WO, SA, ProductConsumed, etc.) do not fire while the technician's device is offline. They execute server-side only when the device syncs. Data Capture flows (Spring 25 GA) are the exception — they run client-side on device.

**When it occurs:** Any time a technician takes an action offline that would normally trigger server logic. The most dangerous scenario is a validation rule that requires a field the technician cannot see in the mobile layout — the technician completes work, goes offline, returns to base, attempts sync, and receives a validation error that can only be resolved with admin intervention.

**How to avoid:** Audit all triggers, validation rules, and flows on WO, SA, WorkOrderLineItem, and ProductConsumed. Classify each as "must fire at sync" (acceptable) vs. "must fire immediately" (requires connectivity). For validation rules covering mobile-editable fields, ensure those fields are visible and required in the FSL Mobile layout so technicians fill them before going offline.

---

## Gotcha 3: Service Report PDF Renders Blank for Fields Not in Briefcase

**What happens:** A service report PDF is generated after a technician completes work. Any field on the report template that was not included in the Briefcase Builder configuration appears blank — no error, no indication of the gap. The PDF is created successfully with empty merge fields.

**When it occurs:** When custom fields are added to WO or SA after the initial briefcase configuration, or when a service report template references fields that were never added to the briefcase. Also occurs when the Service Report template is updated to include new merge fields without a corresponding briefcase update.

**How to avoid:** Maintain a field mapping document: for every merge field in the service report template, confirm the corresponding field is in the briefcase. After any schema change or template update, re-audit this mapping. Add the field-to-briefcase audit to the deployment checklist.

---

## Gotcha 4: Briefcase Priming Hierarchy Is Strictly Parent-First

**What happens:** Briefcase Builder primes records in a strict hierarchy: ServiceResource → ServiceAppointment → WorkOrder → WorkOrderLineItem. If a level is missing or not fully configured, child records at lower levels are not primed to the device. Technicians see empty lists for line items or work orders, with no clear error message.

**When it occurs:** Most commonly when admins add Work Order Line Items to the briefcase but have not confirmed Work Orders are also included. Also occurs when the resource's ServiceResource record is not linked correctly to the user, preventing the entire priming chain from starting.

**How to avoid:** Walk the hierarchy top-down in Briefcase Builder before testing. Confirm ServiceResource → SA → WO → WOLI at each level. Run a full device prime and visually inspect each level on a test device before user acceptance testing.

---

## Gotcha 5: ProductConsumed QuantityOnHand Updates Only at Sync (Not Offline Real-Time)

**What happens:** When a technician records parts consumption in FSL Mobile while offline, a `ProductConsumed` record is staged on-device. The corresponding `QuantityOnHand` decrement on the inventory object does not happen until the device syncs with the org. During the offline period, warehouse inventory displays the pre-consumption quantity.

**When it occurs:** Any time technicians work offline (no connectivity) and consume parts. In environments with multiple field teams consuming from shared inventory, the lag can be significant — all teams see the same "stale" on-hand quantity until each individually syncs.

**How to avoid:** Document and communicate this behavior to warehouse and inventory management stakeholders at project kick-off — it is expected platform behavior, not a bug. For high-value or low-quantity parts where real-time accuracy is critical, require connectivity at the moment of parts consumption (cannot be deferred offline). Implement a ProductRequired reservation step at dispatch time to lock planned parts before technicians go offline.
