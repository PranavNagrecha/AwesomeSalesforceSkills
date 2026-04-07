---
name: fsl-work-order-management
description: "Configure and manage Field Service Lightning work orders: work types, work order line items, service appointments, status flow, and auto-creation via maintenance plans. NOT for case management, resource scheduling optimization, or dispatcher console configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "configure work order status flow in FSL"
  - "set up work types in Field Service Lightning"
  - "auto-create service appointments from work orders"
  - "work order line items not showing in Gantt"
  - "maintenance plan not generating work orders automatically"
tags:
  - field-service
  - fsl
  - work-orders
  - service-appointments
  - work-types
  - maintenance-plans
inputs:
  - FSL package installed and Field Service enabled in org
  - Confirmation of which WorkTypes apply (preventive, corrective, emergency)
  - Desired status values for Work Order and Service Appointment status fields
  - Whether AutoCreateSvcAppt should be enabled on WorkType
  - Maintenance Plan cadence if recurring work orders are required
outputs:
  - Configured WorkType records with correct Estimated Duration and AutoCreateSvcAppt settings
  - Work Order status picklist aligned to operational lifecycle
  - Service Appointment status picklist independent of Work Order status
  - Work Order Line Items mapped to products or tasks
  - Maintenance Plan generating Work Orders at defined frequency
  - Configuration checklist confirming all FSL work order components are wired correctly
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# FSL Work Order Management

This skill activates when a practitioner needs to configure the Field Service Lightning work order object model — including work types, work order line items, service appointments, status picklists, and maintenance plan auto-generation. It does NOT cover dispatcher console layout, resource scheduling optimization, or case management.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Field Service managed package is installed and Field Service is enabled under Setup > Field Service Settings. Without the package, FSL objects (WorkType, ServiceAppointment, AssignedResource) do not exist.
- Confirm whether the org uses the standard Work Order status picklist or has extended it with custom values. Custom statuses must be managed carefully — SA statuses are entirely independent and require separate picklist management.
- Identify the 10,000 child record limit per Work Order and the 500 Work Order Line Item Gantt visibility limit before designing any bulk work order patterns.

---

## Core Concepts

### The FSL Data Model

The canonical FSL work order hierarchy is:

```
WorkOrder
  └── WorkOrderLineItem (WOLI)
        └── ServiceAppointment
              └── AssignedResource
```

A **WorkOrder** is the top-level container for a field service job. It holds the customer, location, account, and overall status. A **WorkOrderLineItem** (WOLI) represents a discrete task or product line within the job — for example, "Replace compressor unit" or "Install firmware update". A **ServiceAppointment** (SA) is the scheduled event for a resource to perform the work; it has its own subject, scheduled start/end, and status lifecycle. An **AssignedResource** links a ServiceResource (technician) to a specific SA.

WorkOrders can also be created as children of other WorkOrders to model parent-child job hierarchies for complex projects.

### WorkType: The Reusable Template

A **WorkType** record is a reusable template that pre-populates fields on a new WorkOrder or WOLI. Key fields include:

- **Estimated Duration** — pre-fills the duration on the WorkOrder or WOLI when the WorkType is selected, which feeds directly into Gantt scheduling.
- **AutoCreateSvcAppt** — when set to `true`, saving a WorkOrder or WOLI with this WorkType automatically creates one ServiceAppointment. The SA is created in `None` status and must still be explicitly scheduled; auto-creation does not schedule or dispatch.
- **DurationType** — Minutes or Hours, paired with Estimated Duration.

A single WorkType can be reused across many WorkOrders and WOLIs. Changes to a WorkType do not retroactively update existing WOs or WOLIs — the template values are copied at creation time.

### Status Independence: Work Order vs. Service Appointment

This is the most critical FSL concept and the most common source of production bugs:

**Work Order status and Service Appointment status are completely independent.** There is no built-in cascade. Completing, cancelling, or moving a WO to any status has zero automatic effect on its SAs, and vice versa. Practitioners who assume completing all SAs marks the WO complete will be wrong. Organizations must build explicit automation (Flow, Apex trigger) to cascade status if that behavior is needed.

The WO status picklist and SA status picklist are also separate picklists with separate values. Standard SA statuses include: None, Scheduled, Dispatched, In Progress, Cannot Complete, Completed, Canceled.

### Maintenance Plans and Auto-Generation

A **Maintenance Plan** defines a recurring schedule for generating Work Orders automatically. Salesforce processes active Maintenance Plans and generates WOs approximately three times per day (roughly every 8 hours) — not in real time, not on demand, and not at an exact configurable time. Practitioners who expect Maintenance Plans to fire immediately after creation or at a precise hour will be surprised. The generated WO is linked back to the Maintenance Plan via the `MaintenancePlanId` lookup.

---

## Common Patterns

### Pattern 1: WorkType-Driven Service Appointment Auto-Creation

**When to use:** Preventive maintenance or any scenario where every WorkOrder of a given type should automatically have a ServiceAppointment created so dispatchers can schedule immediately.

**How it works:**
1. Create a WorkType record with `AutoCreateSvcAppt = true` and `Estimated Duration` set (e.g., 120 minutes).
2. When a new WorkOrder is saved with this WorkType, Salesforce creates one SA in `None` status automatically.
3. The SA inherits the Subject and Location from the WO.
4. A dispatcher then opens the Dispatcher Console, finds the SA in the unscheduled queue, and schedules it to a resource.

**Why not the alternative:** Manually creating SAs after every WO is error-prone and creates dispatcher backlogs. AutoCreateSvcAppt ensures the SA exists immediately and can be picked up in the dispatch queue without extra steps.

### Pattern 2: Manual Service Appointment for Emergency Work

**When to use:** Emergency or reactive work where the WorkType may not have AutoCreateSvcAppt, or where the SA needs to be created with specific overridden details (different location, narrower time window).

**How it works:**
1. Create the WorkOrder with the relevant WorkType.
2. Manually create a ServiceAppointment via the SA related list on the WO, or via Quick Action.
3. Set `EarliestStartTime` and `DueDate` to reflect urgency window.
4. Assign a resource directly via the AssignedResource related list, bypassing the Gantt optimizer.
5. Move SA status to Dispatched manually or via Flow.

**Why not the alternative:** Using AutoCreateSvcAppt for emergency scenarios still creates an SA in `None` status with no time constraint, requiring a dispatcher to find and update it — slower for emergency response.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Preventive maintenance that recurs on a schedule | Maintenance Plan + WorkType with AutoCreateSvcAppt | Automates WO generation and SA creation; reduces manual ops |
| Emergency job with specific resource requirement | Manual WO + manual SA + manual AssignedResource | Full control over timing, resource, and urgency window |
| Completing all SAs should close the WO | Build a Record-Triggered Flow on SA update | No built-in cascade; must be explicit automation |
| Job requires multiple tasks with separate scheduling | Use WOLIs — one per task, each with its own SA | Allows independent scheduling and resource assignment per task |
| WorkType changes should apply to existing WOs | Not possible natively — WorkType values are copied at WO creation | Re-create WOs or build batch update logic if needed |

---

## Recommended Workflow

Step-by-step instructions for configuring FSL work order management:

1. Verify FSL package is installed and Field Service is enabled under Setup > Field Service Settings. Confirm the FSL permission sets (Field Service Standard/Admin) are assigned to relevant users.
2. Define and create **WorkType** records for each category of work (e.g., Preventive Maintenance, Corrective Repair, Emergency Response). Set `Estimated Duration`, `DurationType`, and `AutoCreateSvcAppt` on each.
3. Customize the **Work Order status picklist** and **Service Appointment status picklist** separately under Setup > Object Manager. Map each status to business lifecycle stages. Do not assume these two picklists share values or cascade automatically.
4. Configure any **Maintenance Plans** for recurring work by linking them to the appropriate WorkType and setting recurrence frequency and generation horizon.
5. Build automation (Record-Triggered Flow recommended) to cascade status between WO and SA if the business requires it — for example, closing the WO when all child SAs reach `Completed`.
6. Validate that WO → WOLI → SA relationships display correctly in the related lists and that the Dispatcher Console shows SAs in the unscheduled queue.
7. Test auto-creation: save a WO with a WorkType where `AutoCreateSvcAppt = true` and confirm the SA is created in `None` status with correct subject and location.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All WorkTypes have Estimated Duration and DurationType set
- [ ] AutoCreateSvcAppt is explicitly set (true or false) on each WorkType — not left at default
- [ ] Work Order status picklist and Service Appointment status picklist are managed independently
- [ ] Any status cascade logic between WO and SA is implemented in automation (Flow or Apex) — not assumed to be built-in
- [ ] Maintenance Plans are verified to generate WOs within the 3x-daily batch window — not expected to fire on demand
- [ ] Work Order child record counts will not exceed 10,000 per WO; Gantt display accounts for 500 WOLI limit
- [ ] FSL permission sets are assigned so field technicians can update SA status from the FSL mobile app

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **WO and SA Status Do Not Cascade** — Setting a Work Order to Completed has no effect on its Service Appointments, and vice versa. Organizations routinely ship with this assumption unvalidated, then find open SAs attached to closed WOs. Build explicit Flow automation if cascading is needed.
2. **AutoCreateSvcAppt Creates, Not Schedules** — Enabling `AutoCreateSvcAppt` on a WorkType causes one SA to be created in `None` status when the WO is saved. It is not dispatched, not assigned, and not on the Gantt. Dispatchers must still schedule it. Conflating "auto-create" with "auto-schedule" is a common implementation error.
3. **Maintenance Plans Fire ~3x Daily, Not in Real Time** — Salesforce processes Maintenance Plans in a batch job that runs approximately three times per day. There is no exact time, no on-demand trigger, and no way to force immediate generation through configuration alone.
4. **10,000 Child Records per Work Order / 500 WOLI in Gantt** — A single WorkOrder supports up to 10,000 child records. Additionally, only 500 WOLIs are visible in the Gantt view at one time — beyond that the UI silently omits them.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| WorkType records | Templates pre-populating duration and SA auto-creation on WorkOrders and WOLIs |
| Work Order status picklist | Extended lifecycle statuses for the WO object |
| Service Appointment status picklist | Independent SA lifecycle statuses |
| Maintenance Plan configuration | Recurring schedule driving automatic WO generation |
| Status cascade Flow | Record-Triggered Flow implementing WO ↔ SA status sync |
| Configuration checklist | Completed template confirming all FSL work order components are validated |

---

## Related Skills

- `fsl-integration-patterns` — when integrating external systems that create or update WOs via API
- `fsl-multi-region-architecture` — when work orders must be scoped to service territories across regions
- `case-management-setup` — NOT for work order config; use when the starting point is a Case, not a WorkOrder
