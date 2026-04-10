---
name: fsl-sla-configuration-requirements
description: "Use this skill to configure SLA enforcement for Salesforce Field Service (FSL) using Work Order entitlement processes: designing entitlement processes of type Work Order, defining FSL milestones (response time, on-site arrival, resolution), wiring milestone actions, and aligning Business Hours with service territory Operating Hours. NOT for Service Cloud Case SLAs, case escalation rules, or omni-channel routing — Case entitlement processes are a separate skill."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
tags:
  - field-service
  - FSL
  - SLA
  - entitlements
  - milestones
  - work-orders
  - operating-hours
  - business-hours
  - service-territories
triggers:
  - "how do I configure SLA response time commitments on field service work orders"
  - "milestones are not tracking on work orders even though entitlements are enabled"
  - "how do I differentiate response times by region or service territory in FSL"
  - "field service SLA clock is not pausing outside business hours on work orders"
  - "milestone timers on work orders are never auto-completing — what automation is required"
  - "what is the difference between a Work Order entitlement process and a Case entitlement process"
inputs:
  - "FSL enabled org with Work Orders and Service Territories already configured"
  - "SLA commitments per service tier or region (e.g., 4-hour on-site response, 8-hour resolution)"
  - "Business Hours schedules and Operating Hours objects already defined for each territory"
  - "Whether SLA differentiation is needed by geography, customer tier, or both"
outputs:
  - "Configured Work Order entitlement process with milestone definitions and action timers"
  - "Decision guidance on process type selection, Operating Hours alignment, and milestone completion automation"
  - "Checklist for validating live milestone timer behavior on work orders"
  - "Flow design guidance for auto-completing milestones on work order status transitions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL SLA Configuration Requirements

This skill activates when an org using Salesforce Field Service needs to configure and enforce time-based SLA commitments on Work Orders using Salesforce Entitlement Management. It covers the correct Work Order entitlement process type, milestone design for field service scenarios (response time, on-site arrival, resolution), Operating Hours alignment with service territories, and the custom automation required to mark milestones complete — which Salesforce does not do automatically for Work Orders.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Salesforce Field Service is enabled and Work Orders are in use. Entitlement processes of type "Work Order" only apply to Work Order records — not Cases.
- Confirm Entitlement Management is enabled: Setup > Entitlement Settings. Even for FSL, this must be turned on explicitly.
- Know the service territories and their Operating Hours. Geographic response time differentiation requires separate territories, each with its own Operating Hours object — a single Operating Hours object cannot vary by region.
- Clarify the SLA commitments: what are the time targets for initial response, on-site arrival, and resolution? Are these measured in business hours or calendar hours?
- Determine whether milestone completion should be triggered by Work Order status changes (most common), Work Order Line Item completion, or technician check-in (requires custom automation in all cases — there is no native auto-completion).

---

## Core Concepts

### Work Order Entitlement Processes vs. Case Entitlement Processes

Salesforce Entitlement Management supports two process types: **Case** and **Work Order**. These are entirely separate and cannot be mixed. A single entitlement process cannot span both Case and Work Order records. When configuring FSL SLAs, practitioners must create processes of type **Work Order** — applying a Case entitlement process to a Work Order will not trigger any milestone tracking.

Key differences from Case processes:
- The Work Order milestone **related list** on Work Order records shows fewer fields by default than the Case milestone related list. The `CompletionDate`, `IsViolated`, and `TargetDate` fields exist on the `WorkOrderMilestone` object but may not appear in the default page layout — add them explicitly.
- The `WorkOrder` object's entitlement lookup field is `EntitlementId`. This must be populated for any process to activate.
- Work Order entitlement processes respect the same Business Hours and recurrence logic as Case processes, but the UI for viewing milestone progress on Work Orders is less feature-rich than on Cases.

### Milestone Design for Field Service Scenarios

FSL SLA milestones typically model three distinct time targets:

1. **Initial Response** (No Recurrence) — time from work order creation to first technician acknowledgment or scheduling action.
2. **On-Site Arrival** (No Recurrence) — time from work order creation (or scheduling confirmation) to technician check-in at the service location.
3. **Resolution** (No Recurrence) — time from work order creation to work order completion.

Choosing **No Recurrence** for all three is appropriate for most field service scenarios because each commitment is a one-time obligation per dispatch, not a repeating cycle. If a business requires follow-up visits with their own SLA windows, Sequential or Independent recurrence may apply — but that is uncommon in standard FSL deployments.

### Business Hours and Operating Hours Alignment

In FSL, two distinct time-window objects interact:

- **Business Hours** (Salesforce core) — controls when entitlement milestone timers tick. Assigned at the entitlement process level or milestone level. Milestone countdowns **pause** outside the configured Business Hours window and resume when business hours begin again.
- **Operating Hours** (FSL-specific) — controls when service territories are staffable and when technicians can be scheduled. Assigned to Service Territory records.

These two objects are not automatically synchronized. If Business Hours on the entitlement process say 8am–5pm Monday–Friday and Operating Hours on a territory say 24/7, the milestone timer pauses at 5pm even if a technician could be dispatched overnight. Misalignment creates situations where customers expect 24/7 response but the SLA clock has paused.

For geographic SLA differentiation (e.g., a 2-hour response in a metro territory versus a 4-hour response in a rural territory), the required approach is:
1. Create a separate Service Territory per region.
2. Assign Operating Hours per territory.
3. Create a separate entitlement process (or separate milestones with different time limits) per tier/region.
4. Assign the correct entitlement to each Work Order based on the Service Territory it is dispatched to.

### Milestone Completion Is Never Automatic

Unlike some SLA platforms, Salesforce does **not** auto-mark Work Order milestones as Completed. The `CompletionDate` field on a `WorkOrderMilestone` record must be set by custom automation. If this is not built, milestone records remain open indefinitely and success actions never fire.

The standard automation pattern is a Record-Triggered Flow on the `WorkOrder` object that fires when status changes to a value that represents completion (e.g., "Completed" or "Cannot Complete"). The Flow queries the related `WorkOrderMilestone` records in an `Incomplete` state and updates their `CompletionDate` to the current timestamp. This must be designed carefully to avoid over-completing milestones that were already violated.

---

## Common Patterns

### Pattern: Multi-Territory FSL SLA With Operating Hours Alignment

**When to use:** The org operates in multiple regions with different response time commitments and staffing windows.

**How it works:**
1. Create one Service Territory per region (e.g., Metro East, Rural West). Assign region-appropriate Operating Hours to each territory.
2. Create a Business Hours record per coverage window (e.g., "Metro 24/7", "Rural M–F 8–5"). These drive the milestone clock.
3. Create one entitlement process of type Work Order per SLA tier. Set the process-level Business Hours to match the region's coverage window.
4. Add milestones: Initial Response (e.g., 2 hours for Metro, 4 hours for Rural), On-Site Arrival, Resolution. All with No Recurrence.
5. Wire warning actions at 50% and 75% elapsed. Wire violation actions at 100%.
6. Create entitlement records that reference the correct process. Populate the `EntitlementId` on Work Orders via a Record-Triggered Flow that reads the Work Order's Service Territory and selects the matching entitlement.

**Why not a single process with milestone overrides:** Milestone-level business hours overrides do not change time limits — only the Business Hours object used for clock calculation. To vary the time limit (e.g., 2 hours vs. 4 hours) by region, separate processes or separate milestone definitions are required.

### Pattern: Milestone Auto-Completion Flow on Work Order Status Change

**When to use:** All FSL deployments that use Work Order entitlement processes. Without this, milestones never complete.

**How it works:**
1. Create a Record-Triggered Flow on the `WorkOrder` object.
2. Trigger: When a Record is Updated. Entry condition: `Status` changes to a completion value (e.g., "Completed").
3. Get Related Records: query `WorkOrderMilestone` records where `WorkOrderId = {WorkOrder.Id}` AND `CompletionDate = null`.
4. For each returned milestone: update `CompletionDate` to `{!$Flow.CurrentDateTime}`.
5. Deploy and test in sandbox by creating a Work Order, associating it with an entitlement, advancing the status to "Completed," and verifying the milestone record shows a `CompletionDate`.

**Why this is always required:** Salesforce's Entitlement Management engine evaluates milestone actions (warning, violation, success) on a timer. Success actions fire when `CompletionDate` is set before the `TargetDate`. If `CompletionDate` is never set, success actions never fire and the milestone stays in a permanent open state that obscures reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SLA commitments are on Work Orders (field service) | Create entitlement processes of type Work Order | Case processes do not apply to Work Order records — milestone tracking will not activate |
| Different response times by region | Separate Service Territory + separate entitlement process per region | A single process cannot vary its time limits by territory; milestone-level overrides only change Business Hours used, not the time limit |
| SLA clock must pause outside technician hours | Assign a Business Hours object matching the territory's Operating Hours | Without matching Business Hours, the milestone clock runs 24/7 even when no technician is staffed |
| Milestones are never showing as complete | Build a Record-Triggered Flow to set CompletionDate on WorkOrderMilestone | Salesforce never auto-completes Work Order milestones — custom automation is always required |
| Need to see milestone fields on Work Order layout | Add WorkOrderMilestone related list with CompletionDate, IsViolated, TargetDate columns | The default related list omits key fields; add them explicitly in the page layout editor |
| Entitlement must be assigned based on territory | Build a Flow on Work Order creation that reads Territory and sets EntitlementId | Manual assignment at scale is error-prone; EntitlementId must be set for any process to activate |
| Single nationwide SLA tier | One entitlement process with one Business Hours record | Simpler to maintain; use this unless territory-based differentiation is confirmed as a requirement |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm FSL is enabled, Entitlement Management is on, and Business Hours records exist per coverage window. Confirm Operating Hours objects are assigned to each Service Territory. Add the Entitlements related list to the Work Order page layout and the WorkOrderMilestone related list with key fields (TargetDate, CompletionDate, IsViolated).
2. **Design the process model** — Map SLA tiers to entitlement processes: one Work Order entitlement process per unique combination of time limits and Business Hours. List the milestones per process (Initial Response, On-Site Arrival, Resolution) with their time limits and recurrence types (No Recurrence for most FSL milestones).
3. **Create entitlement processes** — In Setup > Entitlements > Entitlement Processes, create each process of type Work Order. Set the process-level Business Hours. Do not add milestones yet.
4. **Add milestones and wire actions** — For each process, add the defined milestones with the correct time limits. Add warning actions at 50% and 75% elapsed (email alert to dispatcher and assigned tech). Add a violation action at 100% (escalation email + field update on Work Order to flag breach). Add a success action if reporting stamps are needed.
5. **Create entitlement records and automate assignment** — Create entitlement records referencing each process. Build a Record-Triggered Flow on Work Order creation that reads the Work Order's Service Territory and sets `EntitlementId` to the matching entitlement record.
6. **Build milestone completion automation** — Build a Record-Triggered Flow on Work Order that fires on status change to completion values and sets `CompletionDate` on all open `WorkOrderMilestone` records. Test in sandbox with a short milestone time limit (1 minute) to verify all three action types fire correctly.
7. **Validate and document** — Confirm Business Hours and Operating Hours are aligned per territory. Run the check script against the metadata export to detect missing entitlement process type, missing completion flows, or misaligned Business Hours. Document each process, its tier mapping, and territory assignments before go-live.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Entitlement processes are of type Work Order (not Case)
- [ ] Business Hours records are configured and assigned at the process level for each SLA tier
- [ ] Business Hours and Operating Hours are aligned per service territory
- [ ] Each Work Order entitlement process has at least one warning action before violation
- [ ] A Flow populates `EntitlementId` on Work Orders at creation based on Service Territory
- [ ] A Flow sets `CompletionDate` on `WorkOrderMilestone` records when Work Order status reaches completion
- [ ] WorkOrderMilestone related list on Work Order layout includes TargetDate, CompletionDate, and IsViolated columns
- [ ] Milestone timer behavior was tested in sandbox with a shortened time limit before go-live
- [ ] No Case entitlement processes were accidentally applied to Work Order records

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Work Order entitlement processes are completely separate from Case processes** — A Case entitlement process applied to a Work Order does nothing. The process type must be set to Work Order at creation time and cannot be changed afterward. Orgs that copy a Case process and try to reuse it for FSL will see no milestone tracking on Work Orders.
2. **Salesforce never auto-completes Work Order milestones** — Unlike some help-desk platforms, Salesforce does not mark a WorkOrderMilestone as complete when the Work Order closes. CompletionDate must be set by a Flow or Apex trigger. Without this, success actions never fire and all milestones stay open in perpetuity.
3. **Milestone countdowns pause outside Business Hours — and this interacts with Operating Hours in non-obvious ways** — The Business Hours object on the entitlement process controls when the SLA clock ticks. The Operating Hours object on the Service Territory controls when technicians can be dispatched. These are independent objects and are not automatically synchronized. A mismatch means the SLA timer may pause even when technicians are available (or tick when no one is staffed).
4. **Geographic response time differentiation requires separate territories with their own Operating Hours** — There is no way to configure a single entitlement process or Operating Hours object to vary time limits or staffing windows by sub-region. Each distinct SLA window requires a separate Service Territory with its own Operating Hours, paired with a separate entitlement process.
5. **Work Order milestone related list shows fewer fields than Case milestones by default** — The WorkOrderMilestone related list does not display TargetDate, CompletionDate, or IsViolated out of the box. These fields exist on the object but must be added to the related list columns in the page layout editor. Without them, dispatchers have no visible way to see whether an SLA is at risk.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Work Order entitlement process | Named process of type Work Order with Business Hours, milestones, and action timers |
| Milestone definitions | Time limits, recurrence types (No Recurrence), and Business Hours overrides per milestone |
| Milestone action rules | Warning (50%/75%) and violation (100%) email alerts and field updates |
| Entitlement records | One per SLA tier, referencing the correct process and assigned to accounts or territories |
| Entitlement assignment Flow | Record-Triggered Flow that sets EntitlementId on Work Order creation from Service Territory |
| Milestone completion Flow | Record-Triggered Flow that sets CompletionDate on WorkOrderMilestone on Work Order status change |
| Check script output | Validation report from `scripts/check_fsl_sla_configuration_requirements.py` |

---

## Related Skills

- admin/entitlements-and-milestones — Case-based SLA configuration; use when SLA commitments are on Cases rather than Work Orders
- admin/field-service-scheduling-setup — Service Territory and Operating Hours configuration; must be complete before FSL SLA processes are designed
- apex/entitlement-apex-hooks — Apex-based milestone completion and action hooks for complex scenarios not solvable with Flow alone

## Official Sources Used

- Salesforce Help: Set Up Entitlements for Work Orders — https://help.salesforce.com/s/articleView?id=sf.entitlements_work_orders.htm
- Salesforce Help: Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm
- Salesforce Help: Business Hours in Entitlement Management — https://help.salesforce.com/s/articleView?id=sf.entitlements_biz_hours.htm
- Trailhead: Use Entitlements with Work Orders — https://trailhead.salesforce.com/content/learn/modules/field-service-lightning-quick-look/use-entitlements-with-work-orders
- Salesforce Well-Architected: Reliable — https://architect.salesforce.com/docs/architect/well-architected/guide/reliable.html
