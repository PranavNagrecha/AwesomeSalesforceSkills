# LLM Anti-Patterns — FSL Mobile Workflow Design

Common mistakes AI coding assistants make when generating or advising on FSL Mobile workflow design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising That SA Status Automatically Updates Work Order Status

**What the LLM generates:** "When a technician marks a Service Appointment as Completed in FSL Mobile, the Work Order status will automatically update to Completed as well."

**Why it happens:** LLMs conflate the logical relationship between SA and WO with automatic data cascade. The objects are related by lookup but have independent status fields with no built-in cascade. Training data may include Salesforce community posts that describe the desired behavior without noting the missing automation.

**Correct pattern:**

```
SA status does NOT cascade to WO status automatically.
A Record-Triggered Flow (or Apex trigger) on ServiceAppointment must explicitly
update WorkOrder.Status when ServiceAppointment.Status changes.
For multi-SA Work Orders, the flow must check all sibling SAs before
setting WO status to "Completed".
```

**Detection hint:** Any response that says "automatically updates," "cascades," or "syncs" WO status from SA status without mentioning a Flow, trigger, or Process Builder is incorrect.

---

## Anti-Pattern 2: Claiming Standard Flows or Apex Execute in Real Time While Offline

**What the LLM generates:** "Your Flow will run when the technician taps the button in FSL Mobile, even if they are offline, because Salesforce handles the execution."

**Why it happens:** LLMs confuse client-side execution (Data Capture flows, Spring 25 GA) with server-side execution (standard Flows, Apex). Standard Flows and Apex triggers are server-side and do not execute while the device is offline — they fire at sync. Data Capture flows are a specific offline-capable feature distinct from standard Flow automation.

**Correct pattern:**

```
Standard Flows (Record-Triggered, Screen Flows launched from quick actions) and
Apex triggers execute SERVER-SIDE. They do not run while the device is offline.
They fire at the moment of sync when the device reconnects.

Data Capture flows (Spring '25 GA) are a separate feature that executes
CLIENT-SIDE on-device and supports offline execution. Do not conflate the two.
```

**Detection hint:** Any claim that a "Flow" will execute immediately offline without specifying "Data Capture flow" is incorrect. Look for "Flow runs offline" without the "Data Capture" qualifier.

---

## Anti-Pattern 3: Assuming Service Report Will Show All Fields Filled In by the Technician

**What the LLM generates:** "Once the technician fills in the fields in FSL Mobile, the service report PDF will include those values when generated."

**Why it happens:** LLMs reason about form-fill to PDF as a straightforward data binding. They do not model the briefcase priming requirement: a field that is not in the briefcase is not available to the device and therefore cannot be merged into the report, even if it has a value in the org.

**Correct pattern:**

```
A field appears in the service report PDF only if ALL of the following are true:
1. The field is included in the Briefcase Builder configuration for the relevant object.
2. The field is referenced by a merge field in the Service Report template.
3. The technician populated the field before the report was generated.

Fields not in the briefcase render as blank on the PDF — no error is thrown.
```

**Detection hint:** Any service report guidance that does not mention "briefcase" or "Briefcase Builder" in the context of field visibility is incomplete.

---

## Anti-Pattern 4: Treating ProductConsumed as a Real-Time Inventory Update

**What the LLM generates:** "When the technician records parts consumed in FSL Mobile, the inventory quantity on hand is updated immediately so the warehouse can see the correct stock level."

**Why it happens:** LLMs model the user action (technician records consumption) as immediately producing the downstream effect (inventory decrement). They do not model the offline sync delay in the FSL Mobile data pipeline.

**Correct pattern:**

```
ProductConsumed records are created on-device and queued for sync.
QuantityOnHand on the inventory object is decremented SERVER-SIDE during sync —
not at the moment the technician records consumption offline.

During the technician's offline session, warehouse inventory displays
pre-consumption quantities. The decrement appears after the device syncs.
This is expected platform behavior, not a bug.
```

**Detection hint:** Any claim that inventory is updated "in real time" or "immediately" when parts are consumed in FSL Mobile is incorrect for offline sessions.

---

## Anti-Pattern 5: Recommending Briefcase Inclusion of All Fields "To Be Safe"

**What the LLM generates:** "To avoid any gaps, include all fields from WorkOrder, ServiceAppointment, and WorkOrderLineItem in your briefcase configuration. It's better to have too much data than too little."

**Why it happens:** LLMs default to maximalist coverage to avoid gaps. They do not model the performance, storage, and security tradeoffs of oversized briefcase configurations.

**Correct pattern:**

```
Briefcase configuration should be scoped to:
- Fields displayed in the FSL Mobile UI layouts
- Fields referenced as merge fields in Service Report templates
- Fields required by offline Data Capture flows
- A rolling window of appointments (typically 24–48 hours)

Overly broad briefcase configurations:
- Increase priming time (slow device startup)
- Consume device storage
- Expose more customer data on lost/stolen devices
- Can hit briefcase record/field limits

Audit field-by-field against mobile layout and report template.
```

**Detection hint:** Any briefcase recommendation that includes all fields or all objects without justification per mobile layout and report template usage is an anti-pattern.

---

## Anti-Pattern 6: Recommending Validation Rules as the Primary Mobile Data Quality Mechanism

**What the LLM generates:** "Add a validation rule on WorkOrder to require Failure_Code__c when Status = 'Completed'. This will ensure technicians fill in the field before the record can be saved."

**Why it happens:** LLMs apply standard Salesforce data quality patterns (validation rules) without accounting for the sync-time execution model. In desktop/online use, validation rules prevent save immediately. In FSL Mobile offline use, they prevent sync after the technician has left the site.

**Correct pattern:**

```
Validation rules are a necessary data quality backstop but are NOT a substitute
for mobile-side required field configuration.

For any field that must be filled during a field job:
1. Add the field to the FSL Mobile layout (WO or SA layout)
2. Mark the field as required in the mobile layout
3. For conditional requirements, use a Data Capture flow with conditional logic

The validation rule provides sync-time enforcement as a safety net.
The mobile layout required field provides in-session enforcement.

If a validation rule blocks sync for a field not in the mobile layout,
the technician cannot self-resolve — admin intervention is required.
```

**Detection hint:** Any response that recommends validation rules for mobile data quality without also requiring the field to be visible and required in the FSL Mobile layout is incomplete.
