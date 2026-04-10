---
name: fsl-mobile-workflow-design
description: "Use this skill when designing, troubleshooting, or reviewing FSL Mobile worker workflows — including job lifecycle management, offline data capture, customer signature collection, parts consumption, and geolocation-triggered status transitions. Trigger keywords: FSL mobile, field service mobile workflow, offline job lifecycle, technician mobile, service appointment status, briefcase priming, parts consumption mobile, signature capture FSL. NOT for mobile app installation/configuration, FSL scheduling optimization, Dispatcher Console setup, or Work Capacity management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "How do I capture a customer signature on the FSL mobile app and attach it to the service report?"
  - "Technician marks the service appointment complete but the work order status does not update automatically"
  - "Fields are showing blank on the service report PDF after the technician fills them in offline"
  - "Parts consumed offline are not updating inventory until after the technician syncs — is that expected?"
  - "How do I configure an offline-capable data capture flow for field technicians?"
  - "What is the correct job status progression in FSL Mobile from dispatched to completed?"
tags:
  - fsl-mobile
  - field-service
  - offline-workflow
  - job-lifecycle
  - briefcase-priming
  - signature-capture
  - parts-consumption
  - data-capture-flow
inputs:
  - FSL Mobile license type (FSL Field Technician or FSL Dispatcher)
  - Whether offline mode is enabled and which objects are in the briefcase
  - Current service appointment and work order status flows
  - Whether Data Capture (Spring 25 GA) is in use or classic quick actions
  - Inventory / product catalog configuration (ProductRequired, ProductConsumed)
outputs:
  - Job lifecycle design with correct status transitions and required automation
  - Briefcase priming plan ensuring all referenced fields reach the device
  - Offline workflow guidance for signature, parts consumption, and data capture
  - Review checklist confirming server-side logic is not assumed to run offline
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Mobile Workflow Design

This skill activates when a practitioner is designing or debugging the end-to-end workflow a field technician follows in the FSL Mobile app — from receiving a dispatched appointment through completing work, capturing data, consuming parts, and syncing results back to the org. It focuses on offline-first behavioral constraints, job status lifecycle, and the automation required to bridge mobile actions to record updates.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether offline mode is enabled and which objects are included in the Briefcase Builder configuration. Any field not primed to the device will render blank in service reports and will not be editable offline.
- Identify how status updates on Service Appointment (SA) and Work Order (WO) are managed. SA status changes made in FSL Mobile do NOT automatically cascade to the parent Work Order — a separate automation (Flow, Process Builder, Apex trigger) must handle this.
- Identify whether the org uses classic FSL quick actions or the Spring 25 GA Data Capture feature for structured offline form collection. Data Capture flows execute client-side and sync results at reconnect; regular server-side Flows do not execute offline.

---

## Core Concepts

### 1. Offline-First Architecture and Briefcase Priming

FSL Mobile is designed to operate without network connectivity. The Briefcase Builder determines which records and fields are downloaded to the device before a technician goes into the field. Priming follows a strict hierarchy:

1. Resource (ServiceResource)
2. Service Appointments assigned to that resource
3. Work Orders linked to those appointments
4. Work Order Line Items linked to those Work Orders

If any level in the hierarchy is missing from the briefcase configuration, records at lower levels will not be primed. A technician attempting to view work order line items when WOs are not in the briefcase will see empty lists or encounter sync errors.

Fields must also be explicitly included in the briefcase. A field that exists on the Work Order object but is not in the briefcase configuration will appear blank in the FSL Mobile UI and blank in any service report generated from that appointment — even if the field has a value in the org.

### 2. Job Lifecycle: Service Appointment Status Transitions

The canonical FSL Mobile job lifecycle for a technician is:

| Status | Who Sets It | Trigger |
|---|---|---|
| None / New | System | Appointment created |
| Scheduled | Dispatcher | Assigned to a resource |
| Dispatched | Dispatcher | Pushed to technician's queue |
| In Progress | Technician | En route or check-in via mobile |
| Completed | Technician | Work complete action in mobile |
| Cannot Complete | Technician | Blocking issue encountered |

**Critical constraint:** Changing the Service Appointment status in FSL Mobile does NOT cascade to the parent Work Order status. If the org expects the Work Order to move to "In Progress" when a technician checks in, or to "Completed" when all appointments are done, that logic must be implemented as an automation — typically a Record-Triggered Flow on ServiceAppointment that updates the related WorkOrder.

### 3. Server-Side Logic Blackout During Offline Operation

Apex triggers, validation rules, and standard Flows (other than Data Capture flows) do NOT execute while the device is offline. They fire at the moment of sync when the device reconnects. This means:

- Required field validation rules will block sync if the technician did not fill those fields in the mobile app — even if the field was not shown in the mobile layout.
- Apex triggers that auto-populate fields will not run until sync, which can cause interim blank values visible in reports generated before sync.
- Any workflow that depends on immediate trigger execution (e.g., inventory reservation on parts consumption) will have a sync delay.

This is the single most common source of production surprises in FSL Mobile deployments.

### 4. Data Capture Flows (Spring 25 GA)

Data Capture is the Spring 25 GA replacement for classic FSL quick actions for structured offline data collection. Data Capture flows:

- Execute entirely on-device (client-side)
- Support conditional logic, required fields, and signature collection natively
- Sync collected data to the org as a batch when connectivity is restored
- Do NOT support Apex callouts or external service calls (those would require connectivity)

Data Capture is the recommended pattern for pre-flight checklists, safety inspections, and structured work completion forms in Spring 25+ orgs.

---

## Common Patterns

### Pattern 1: Customer Signature Capture

**When to use:** The business requires a customer to sign off on completed work, and the signature must appear on the service report PDF.

**How it works:**
1. Use a Data Capture flow (Spring 25+) or FSL quick action (pre-Spring 25) that includes a Signature capture component.
2. The signature is stored as a ContentDocument linked to the Service Appointment or Work Order.
3. The Service Report template must reference the signature field via a merge field. If the signature field is not in the briefcase configuration AND not on the service report template, the PDF will render blank.
4. Confirm the ContentDocument / ContentDocumentLink objects are included in the briefcase so the signature is available offline for display after capture.

**Why not the alternative:** Storing signatures as a text-encoded Base64 field on the WO and referencing it in a report works but bypasses the native Content Document approach, loses file management capabilities, and can hit field-length limits for complex signatures.

### Pattern 2: Parts Consumption (ProductConsumed)

**When to use:** Technicians consume parts from their van stock or a warehouse location during a job.

**How it works:**
1. Technician selects consumed products via the FSL Mobile "Products Consumed" action on the Work Order.
2. A `ProductConsumed` record is created on-device and staged for sync.
3. At sync, Salesforce processes the ProductConsumed record and decrements `QuantityOnHand` on the linked `Product2` / inventory location record.
4. Inventory levels are not updated in real time while the technician is offline — the decrement happens server-side at sync.
5. If the org uses `ProductRequired` records for planned parts, confirm those are in the briefcase so technicians see expected parts pre-loaded.

**Why not the alternative:** Manually keying consumed quantities via a custom text field on the WO bypasses the native FSL inventory chain, loses traceability to inventory locations, and prevents automated replenishment workflows.

### Pattern 3: Automating WO Status from SA Status

**When to use:** Business process requires the Work Order to automatically reflect the field status of the appointment being worked.

**How it works:**
1. Create a Record-Triggered Flow on `ServiceAppointment`, triggered on update when `Status` changes.
2. In the flow, find the parent `WorkOrder` via the `WorkOrderId` lookup.
3. Update `WorkOrder.Status` using a mapped value (e.g., SA "In Progress" → WO "In Progress", SA "Completed" → check all sibling SAs before setting WO "Completed").
4. For multi-appointment work orders, add a decision element that checks whether all linked ServiceAppointments are in "Completed" status before updating the WO to "Completed".

**Why not the alternative:** Using a Process Builder or Workflow Rule for this will be deprecated in future releases. Record-Triggered Flows are the supported path.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Structured offline form (inspection, checklist) | Data Capture Flow (Spring 25+) | Native offline execution, sync on reconnect, no Apex needed |
| Customer signature on service report | Data Capture signature component + briefcase ContentDocument | Native PDF merge field support |
| Status cascade SA → WO | Record-Triggered Flow on ServiceAppointment | Supported automation, handles multi-SA WOs |
| Parts tracking | Native ProductConsumed action | Maintains FSL inventory chain; QuantityOnHand updates at sync |
| Server-side validation on offline data | Move validation to mobile layout required fields + sync-time validation rule | Validation rules fire at sync; surface errors pre-sync via mobile required fields |
| Service report blank fields | Add missing fields to briefcase AND service report template | Fields must be primed to device AND referenced in template |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map the job lifecycle.** Document the required SA status transitions (Dispatched → In Progress → Completed / Cannot Complete). Identify any WO status that must track SA status. For each required cascade, verify a Record-Triggered Flow or equivalent automation exists — do not assume platform auto-cascade.
2. **Audit the briefcase configuration.** Open Briefcase Builder (Field Service Settings → Briefcase Builder). Confirm the hierarchy is complete: ServiceResource → ServiceAppointment → WorkOrder → WorkOrderLineItem. List all fields required by the mobile UI and service report template and verify each field is included in the briefcase.
3. **Identify server-side dependencies that will break offline.** List all Apex triggers, validation rules, and Flows on WO / SA / ProductConsumed. For each, determine whether it must fire immediately (connectivity required) or can fire at sync. Validation rules that block sync must have the fields shown and required in the mobile layout so technicians fill them before going offline.
4. **Design data capture and signature workflows.** For Spring 25+ orgs, use Data Capture flows for structured offline forms and signature collection. For pre-Spring 25 orgs, use FSL quick actions with an FSL Signature action. Ensure the ContentDocument/ContentDocumentLink is in the briefcase.
5. **Configure parts consumption.** Verify ProductRequired records for planned parts are in the briefcase. Confirm the "Products Consumed" quick action is on the Work Order mobile layout. Communicate to stakeholders that QuantityOnHand updates are not real-time — they occur at sync.
6. **Test offline behavior end-to-end.** Enable airplane mode on a test device after priming. Execute each workflow step (status change, data capture, signature, parts consumption). Reconnect and verify sync results, including trigger execution outcomes and service report PDF rendering.
7. **Review the service report template.** Open the Service Report template and verify every data field that must appear on the printed report is (a) in the briefcase and (b) referenced by the correct merge field in the template. Generate a test report in both online and offline+sync scenarios.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] SA status lifecycle documented and all required WO status cascades covered by automation
- [ ] Briefcase hierarchy is complete: Resource → SA → WO → WOLI, all required fields included
- [ ] No automation assumes server-side execution while technician is offline; sync-time firing is acceptable for all server logic
- [ ] Data Capture flows (Spring 25+) or FSL quick actions configured for all structured offline forms
- [ ] Signature capture linked to ContentDocument and included in service report template merge fields
- [ ] ProductConsumed action on WO mobile layout; stakeholders informed of sync-delay inventory updates
- [ ] End-to-end airplane mode test completed; service report PDF validated after sync

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SA Status Does Not Cascade to Work Order** — FSL Mobile updates the Service Appointment status. The parent Work Order status does not change automatically. Without explicit automation, WO status will lag behind or never update, breaking downstream reporting and billing workflows.
2. **Service Report Blanks for Non-Briefcased Fields** — Fields not included in the Briefcase Builder configuration render as blank in the service report PDF, even if the field has a value in the org. This is a silent failure — the PDF is generated without error, just with empty merge fields.
3. **Validation Rules Fire at Sync, Not Offline** — Required field validation rules and other validation logic executes server-side when the device syncs. If a required field was not surfaced in the mobile layout, the technician cannot fill it offline. Sync will fail with a validation error, and the technician must reconnect to resolve — potentially after leaving the customer site.
4. **Priming Hierarchy Is Strictly Parent-First** — Skipping a level in the Briefcase Builder (e.g., including WOs but not SAs) means child records at lower levels will not prime. Practitioners sometimes add WOLIs without adding WOs, resulting in empty line item lists on device.
5. **ProductConsumed QuantityOnHand Updates on Reconnect Only** — Inventory levels are not decremented in real time during offline jobs. A dispatcher or warehouse team looking at inventory levels while a technician is offline will see stale quantities. This is expected platform behavior, not a bug, but must be communicated to inventory management stakeholders.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Job lifecycle diagram | SA and WO status transition map with automation triggers identified |
| Briefcase audit spreadsheet | Field-by-field list of what is and is not primed, mapped to mobile UI sections and report merge fields |
| Automation inventory | List of all triggers, validation rules, and flows with offline vs. sync-time classification |
| Data Capture flow configuration | Offline form design with required fields, conditional logic, and signature step |
| Service report template review | Merge field–to–briefcase field mapping confirming no blank fields |

---

## Related Skills

- admin/fsl-mobile-app-setup — Installation, permission sets, connected app, and initial device configuration; prerequisite to workflow design
- apex/fsl-mobile-app-extensions — Custom Apex for FSL Mobile actions and deep links; use when built-in actions are insufficient
- apex/fsl-service-report-templates — Visualforce/PDF template design for service reports; required when customizing report layout

---

## Official Sources Used

- Field Service Mobile App (Offline Considerations) — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_offline.htm
- Configure Offline Mode — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_mobile_offline.htm
- Track Field Service Jobs — Trailhead — https://trailhead.salesforce.com/content/learn/modules/field-service-mobile-app/track-field-service-jobs
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
