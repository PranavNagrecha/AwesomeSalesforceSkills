# Gotchas — FSL Work Order Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Work Order Status and Service Appointment Status Are Completely Independent

**What happens:** Changing a Work Order's status to Completed, Canceled, or any other value has zero automatic effect on child Service Appointments. Likewise, completing or canceling all SAs on a WO does not change the WO status. The two status fields are managed by entirely separate picklists with no built-in cascade logic.

**When it occurs:** Every time practitioners assume the statuses are linked. This surfaces as open WOs with all-completed SAs, or completed WOs with open SAs that continue to appear in dispatch queues and SLA reports. It is particularly damaging in reporting because KPIs built on WO status and SA status diverge silently.

**How to avoid:** Treat WO status and SA status as independent lifecycles. If the business requires cascading behavior (e.g., all SAs Completed → WO Completed), implement it explicitly with a Record-Triggered Flow on ServiceAppointment. Document the cascade rules in a decision record so future admins do not remove the flow thinking it is redundant.

---

## Gotcha 2: AutoCreateSvcAppt on WorkType Creates a Service Appointment, Not a Scheduled One

**What happens:** When `AutoCreateSvcAppt = true` on a WorkType, Salesforce creates one ServiceAppointment in `None` status when the parent WorkOrder or WorkOrderLineItem is saved. The SA has no assigned resource, no scheduled start time, and does not appear on the Gantt until a dispatcher acts on it. It goes into the unscheduled queue.

**When it occurs:** Practitioners configure AutoCreateSvcAppt expecting the system to schedule the appointment automatically — especially when combined with a Maintenance Plan. The WO is generated, the SA is created, but nothing is dispatched and the Gantt shows no upcoming job. Technicians receive no notification.

**How to avoid:** Clearly distinguish "auto-create" from "auto-schedule." If automated scheduling is needed, use Einstein Scheduling (requires additional configuration) or build a Flow that sets SA fields and triggers the scheduling engine. For manual dispatch workflows, train dispatchers to look for SAs in the unscheduled queue after Maintenance Plan batch runs.

---

## Gotcha 3: Maintenance Plans Run ~3 Times Per Day — Not On Demand or in Real Time

**What happens:** Maintenance Plans are processed by a Salesforce batch job that runs approximately three times per day (roughly every 8 hours). There is no configurable trigger time, no on-demand execution button available in standard configuration, and no guarantee of an exact run window.

**When it occurs:** Admins create a Maintenance Plan expecting WOs to appear within minutes. When WOs are not generated for hours, they assume the plan is misconfigured and make redundant changes. It also causes SLA timing issues when WOs need to be generated at a specific time relative to a scheduled maintenance window.

**How to avoid:** Communicate the ~3x daily batch cadence to operations teams at project kickoff. Do not build SLA commitments that depend on real-time WO generation from Maintenance Plans. If near-real-time WO creation is required, use an external trigger (Scheduled Flow, external scheduler) to create WOs via API instead of relying on Maintenance Plan processing.

---

## Gotcha 4: 10,000 Child Record Limit per Work Order and 500 WOLI Gantt Visibility Limit

**What happens:** A single WorkOrder record supports a maximum of 10,000 child records (WorkOrderLineItems and ServiceAppointments combined). Attempting to create records beyond this limit results in an error. Separately, the Dispatcher Console Gantt view only renders up to 500 WorkOrderLineItems per Work Order — WOLIs beyond this threshold are silently omitted from the Gantt with no warning to dispatchers.

**When it occurs:** Large manufacturing, utilities, or construction jobs that break down a single WO into many granular tasks hit the 10,000 limit. High-WOLI jobs where dispatchers rely on the Gantt for full visibility hit the 500-WOLI Gantt limit — dispatchers see an incomplete picture and may miss WOLIs that require scheduling.

**How to avoid:** For high-task jobs, use a parent-child Work Order hierarchy rather than one WO with hundreds of WOLIs. Distribute tasks across child WOs (each with fewer WOLIs) to stay within the Gantt limit. Monitor WOLI counts during design; flag any WO design that exceeds 400 WOLIs as a risk for Gantt visibility.

---

## Gotcha 5: WorkType Field Values Are Copied at Creation Time — Retroactive Changes Do Not Apply

**What happens:** When a WorkType is assigned to a WorkOrder or WOLI, the field values (Estimated Duration, DurationType) are copied onto the record at save time. If the WorkType record is later updated — for example, duration changed from 90 to 120 minutes — existing WOs and WOLIs are not updated. They retain the values from when they were created.

**When it occurs:** Admins update a WorkType assuming the change propagates to all open Work Orders using that type. Dispatchers then see incorrect estimated durations on existing WOs, causing Gantt scheduling gaps.

**How to avoid:** Treat WorkType changes as additive going forward — new WOs will pick up the updated values. If existing open WOs must reflect the new duration, run a batch update (via Apex or Data Loader) to update the affected WOs and WOLIs explicitly. Communicate the non-retroactive behavior to admins during training.
