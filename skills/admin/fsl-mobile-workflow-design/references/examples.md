# Examples — FSL Mobile Workflow Design

## Example 1: Service Appointment Completion Does Not Update Work Order Status

**Context:** A utility company uses FSL Mobile for field technicians. Each Work Order has a single Service Appointment. When technicians mark the appointment "Completed" in the mobile app, the Work Order remains in "In Progress" status, breaking the billing workflow that triggers on WO status = "Completed".

**Problem:** The team assumed FSL Mobile would cascade SA status changes to the parent Work Order automatically. No automation was built. The WO status only updates if someone manually changes it in the org desktop UI.

**Solution:**

Build a Record-Triggered Flow on `ServiceAppointment`:

```
Object: ServiceAppointment
Trigger: A record is updated
Condition: Status CHANGES TO "Completed"

Action: Update Records
  - Related Record: WorkOrder (via WorkOrderId)
  - Field: Status → "Completed"
```

For orgs with multiple Service Appointments per Work Order, add a Get Records element to count sibling SAs not in "Completed" status before updating the WO:

```
Get Records: ServiceAppointment
  - Filter: WorkOrderId = {$Record.WorkOrderId}
            Status != "Completed"
            Id != {$Record.Id}

Decision: If count > 0 → do NOT update WO
          If count = 0 → update WO Status to "Completed"
```

**Why it matters:** Without this automation, billing, inventory replenishment, and SLA tracking workflows never fire. The gap is invisible in testing if testers manually update the WO after each appointment.

---

## Example 2: Service Report PDF Shows Blank Signature and Blank Custom Fields

**Context:** A facilities management company configured FSL Mobile with customer signature capture on work completion. After go-live, service report PDFs consistently show blank signature lines and blank readings from the technician's inspection — even though the technician confirmed they filled in the fields and obtained the signature.

**Problem:** Two separate briefcase gaps exist:
1. The custom inspection fields (e.g., `Equipment_Reading__c`, `Technician_Notes__c`) on Work Order were added after the initial briefcase configuration and never added to the Briefcase Builder.
2. The ContentDocument / ContentDocumentLink objects holding the signature were not included in the briefcase, so the signature file was captured and staged for sync but not accessible for report generation during the offline session.

**Solution:**

Step 1 — Open Briefcase Builder (Field Service Settings → Briefcase Builder → select the relevant briefcase). Add the missing custom fields to the Work Order object configuration.

Step 2 — Add `ContentDocument` and `ContentDocumentLink` to the briefcase to ensure signature files are primed to the device and available for report rendering.

Step 3 — Open the Service Report template (Reports tab → Service Reports). Verify each custom field has a corresponding merge field, e.g.:

```
{!WorkOrder.Equipment_Reading__c}
{!WorkOrder.Technician_Notes__c}
```

Step 4 — Re-prime the device (log out of FSL Mobile, log back in) and run a full offline test: disable airplane mode after priming, complete work, capture signature, generate report, re-enable connectivity, sync, and verify the PDF.

**Why it matters:** Service report gaps are a legal and billing issue in many field service verticals. The failure is silent — no error is thrown, the PDF simply renders blanks. Catching this requires an explicit field-by-field audit against the briefcase and template merge fields.

---

## Example 3: Parts Consumption Inventory Appears Wrong Until Sync

**Context:** A telecom company's warehouse team reports that inventory levels shown in the org do not match what technicians have consumed during the day. A technician consumed 3 splitters on a job, but the warehouse still shows the original quantity.

**Problem:** The team expected `QuantityOnHand` to update in real time as technicians consume parts. In FSL Mobile, `ProductConsumed` records are created on-device and synced at reconnect — `QuantityOnHand` is decremented server-side during sync, not immediately when the technician records consumption offline.

**Solution:**

This is expected platform behavior, not a bug. The correct response is operational communication:

1. Train warehouse staff that on-hand quantities are "end-of-shift accurate" for technicians working offline, not real-time.
2. If real-time inventory accuracy is required, require technicians to maintain connectivity during parts consumption (Wi-Fi or LTE) and sync immediately after each job.
3. For high-value parts, use a pre-job ProductRequired reservation flow that locks inventory at dispatch time rather than relying on consumption sync for accuracy.

**Why it matters:** Misunderstanding this behavior leads to duplicate orders, stocking errors, and stakeholder trust issues. Documenting the sync-delay characteristic explicitly in the deployment runbook prevents post-go-live escalations.

---

## Anti-Pattern: Placing Required Validation Rules on Fields Not in the Mobile Layout

**What practitioners do:** Admins add a validation rule requiring a field (e.g., `Failure_Code__c`) to be populated when WO Status = "Completed". The field is not added to the FSL Mobile WO layout.

**What goes wrong:** The technician marks the appointment complete in the app. The WO record is queued for sync. At sync, the validation rule fires server-side and blocks the update. The technician receives a cryptic sync error after leaving the customer site. The WO remains in "In Progress" status in the org until an admin manually resolves the validation error.

**Correct approach:** For any field covered by a validation rule that fires on WO or SA status change, ensure the field is (a) in the briefcase configuration and (b) visible and editable in the FSL Mobile layout. If the field must be conditionally required based on work type, implement that conditional logic in the Data Capture flow so the technician is prompted before sync occurs.
