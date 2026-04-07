# Examples — FSL Mobile App Setup

## Example 1: LWC Quick Action for Safety Checklist on Work Order

**Context:** A utilities company requires technicians to complete a safety checklist before beginning work on any work order. The checklist captures 10 yes/no fields and a freetext notes field, then saves them to a custom object (`Safety_Checklist__c`) linked to the work order.

**Problem:** The team initially tried to surface a Visualforce page as a custom button inside FSL Mobile. The page never rendered — FSL Mobile does not execute Visualforce. The team then tried building an HTML5 Mobile Extension Toolkit extension, which worked but required a bespoke Apex REST endpoint and could not use standard LDS validation.

**Solution:**

```javascript
// safety-checklist/safety-checklist.js (LWC Quick Action)
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import { createRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

const WORK_ORDER_FIELDS = ['WorkOrder.Id', 'WorkOrder.WorkOrderNumber'];

export default class SafetyChecklist extends LightningElement {
    @api recordId; // injected by the quick action container

    @wire(getRecord, { recordId: '$recordId', fields: WORK_ORDER_FIELDS })
    workOrder;

    hazardsCleared = false;
    ppeVerified = false;
    notes = '';

    handleSave() {
        const fields = {
            Work_Order__c: this.recordId,
            Hazards_Cleared__c: this.hazardsCleared,
            PPE_Verified__c: this.ppeVerified,
            Notes__c: this.notes
        };
        createRecord({ apiName: 'Safety_Checklist__c', fields })
            .then(() => {
                this.dispatchEvent(new ShowToastEvent({ title: 'Saved', variant: 'success' }));
            })
            .catch(err => {
                console.error(err);
            });
    }
}
```

Register this LWC as a Quick Action on the Work Order object (type: Lightning Web Component). In Field Service Mobile Settings → Actions, add this quick action to the Work Order action list.

**Why it works:** LWC quick actions receive `recordId` automatically from the FSL Mobile container, so the component always has context. `createRecord` from `uiRecordApi` works offline via LDS — the record is queued locally and synced to the org when connectivity is restored.

---

## Example 2: Diagnosing Silent Offline Priming Failures

**Context:** A telecom org rolled out FSL Mobile to 200 technicians. After go-live, technicians in busy urban territories consistently reported missing line items when offline. Technicians in rural territories (fewer appointments per day) reported no issues.

**Problem:** The priming configuration looked correct in Setup. Data Sync was enabled for Work Order Line Items. No errors appeared in the app or in Field Service Mobile Settings. The issue was invisible.

**Solution:**

Audit the page reference count for a high-volume technician:

```python
# Rough page reference estimator (run in org context or data export)
# For each resource, sum:
#   1 page ref per Service Appointment
#   1 page ref per Work Order
#   1 page ref per Work Order Line Item
#   1 page ref per each enabled related list record

# Example for a busy urban technician:
appointments_per_day = 8
work_orders_per_appointment = 2          # avg
line_items_per_work_order = 6            # avg
related_list_records_per_wo = 15         # parts, notes, etc.

total_refs = (
    appointments_per_day
    + (appointments_per_day * work_orders_per_appointment)
    + (appointments_per_day * work_orders_per_appointment * line_items_per_work_order)
    + (appointments_per_day * work_orders_per_appointment * related_list_records_per_wo)
)
# 8 + 16 + 96 + 240 = 360 per day window — under limit for this example

# But if scheduling window is 3 days:
total_refs_3_day = total_refs * 3   # = 1,080 — OVER the 1,000 limit
print(f"Estimated page refs (3-day window): {total_refs_3_day}")
```

**Resolution steps:**
1. Reduce the priming window from 3 days to 1 day for high-volume territories.
2. Remove low-priority related lists from the priming config (e.g., internal notes not needed offline).
3. Re-test: verify technicians in high-volume territories can see all line items after a fresh priming sync.

**Why it works:** The 1,000-page-reference limit is per resource per priming run. Narrowing the scheduling window and trimming unnecessary related lists is the standard mitigation. There is no admin console showing the current page reference count — it must be estimated from data.

---

## Example 3: Deep Linking from a Third-Party Mapping App into FSL Mobile

**Context:** Technicians use a third-party navigation app on their device. After arriving at a site, they want a single tap to jump into the relevant Service Appointment record in FSL Mobile without manually searching.

**Problem:** The navigation app can only open a URL/URI. There is no native FSL Mobile intent or scheme documented in standard mobile app documentation — practitioners conflate this with the standard Salesforce Mobile deep link scheme (`salesforce://`), which does not open FSL Mobile.

**Solution:**

FSL Mobile uses a distinct custom URI scheme registered through the Field Service Mobile connected app. The URI structure follows this pattern:

```
fieldservice://<action>?recordId=<recordId>&objectType=<objectType>
```

Configuration steps:
1. In Setup → App Manager, open the Field Service Mobile connected app.
2. Under Mobile App Settings, note or configure the custom URI scheme (e.g., `fieldservice`).
3. Register the scheme in the third-party app's outbound link configuration.
4. Construct the link with `recordId` of the target Service Appointment and `objectType=ServiceAppointment`.
5. Keep the total URI length and encoded payload under 1 MB.

Test by tapping the link on a physical device with FSL Mobile installed. Verify the app opens to the correct record.

**Why it works:** The FSL Mobile connected app registers the custom URI scheme with iOS and Android at install time. The OS routes matching URIs directly to the FSL Mobile app, which parses the parameters and navigates to the specified record.

---

## Anti-Pattern: Configuring FSL Mobile Through Standard Mobile App Builder

**What practitioners do:** Attempt to configure what technicians see in FSL Mobile by editing the Salesforce Mobile App navigation, adding tabs in App Manager → Salesforce app, or building Lightning App pages targeting "Mobile" form factor.

**What goes wrong:** None of these changes affect FSL Mobile. FSL Mobile reads its own configuration from Field Service Mobile Settings and the Field Service Mobile connected app — completely separate from the standard Salesforce Mobile app and App Manager. Practitioners spend hours configuring the wrong surface and see no change in the FSL app.

**Correct approach:** All FSL Mobile configuration lives in Setup → Field Service → Field Service Mobile Settings. App extensions are added as quick actions under object action lists in those settings, not through the standard App Manager or Mobile Navigation UI.
