---
name: fsl-scheduling-optimization-design
description: "Use this skill to design, configure, and troubleshoot the Field Service Lightning (FSL) Optimizer — including selecting optimization type (Global, In-Day, Resource Schedule), understanding the priority-score model, configuring travel mode (Aerial vs Street-Level Routing), and tuning optimizer behavior for specific scheduling objectives. NOT for configuring scheduling policies, work rules, service objectives weights, or the Dispatcher Console dispatch settings."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
  - Reliability
triggers:
  - "field service optimizer is not scheduling all appointments and some are staying unscheduled"
  - "how to run global optimization to reschedule the entire week of field service appointments"
  - "in-day optimization is not responding fast enough to same-day cancellations and disruptions"
  - "appointment priority is not being respected by the FSL optimizer when ranking candidates"
  - "should I use aerial travel mode or street-level routing for field service optimization"
  - "optimizer is treating high-priority work orders the same as low-priority appointments"
  - "how to configure the FSL optimizer to minimize travel time across all scheduled appointments"
tags:
  - field-service
  - fsl
  - optimizer
  - scheduling-optimization
  - global-optimization
  - in-day-optimization
  - travel-mode
  - appointment-priority
  - street-level-routing
inputs:
  - "Current optimization type in use (Global, In-Day, Resource Schedule, or none)"
  - "Appointment volume and geographic distribution of service territories"
  - "Priority distribution of appointments (how many are high vs. low priority)"
  - "Travel mode currently configured (Aerial or Street-Level Routing add-on)"
  - "Whether predictive traffic data is required for route accuracy"
  - "Time horizon for optimization (same-day, multi-day, or weekly)"
  - "Whether the optimizer is run manually by dispatchers or on an automated schedule"
outputs:
  - "Recommended optimization type (Global, In-Day, or Resource Schedule) with justification"
  - "Optimizer configuration checklist covering scheduling policy, horizon, and travel mode"
  - "Priority scoring guidance ensuring appointment DueDate and priority field are populated correctly"
  - "Travel mode selection decision with cost/accuracy tradeoff documented"
  - "Runbook for triggering and monitoring optimization jobs in the Field Service Dispatcher Console"
dependencies:
  - fsl-scheduling-policies
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Scheduling Optimization Design

This skill activates when a practitioner needs to design or troubleshoot the Field Service Lightning Optimizer — the engine that automatically assigns and sequences service appointments across a workforce. It covers optimization type selection, appointment priority scoring mechanics, travel mode configuration, and optimizer job execution. Use the related `fsl-scheduling-policies` skill for work rule and service objective configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Field Service managed package is installed at version 3.x or higher and that the FSL Optimizer is licensed for the org. The Optimizer is a separate licensed component from the base Field Service package; not all Field Service implementations have it.
- Identify the geographic scale of the operation: the number of service territories being optimized, the average appointment density per technician per day, and whether technicians are concentrated or dispersed across a region.
- Determine the scheduling horizon: same-day disruption management requires In-Day optimization, while full-week planning requires Global optimization. The correct type is driven by when decisions are made, not by appointment volume alone.
- Check the org's travel mode configuration in Setup > Field Service Settings > Routing. The default is Aerial (straight-line distance, free). Street-Level Routing is a paid add-on that uses actual road networks and supports predictive traffic data.
- Confirm that service appointments have both `DueDate` and `Priority` fields populated. Appointments with a null `DueDate` are treated as lowest priority by the optimizer and may never be scheduled in a constrained run.

---

## Core Concepts

### The Three Optimization Types

FSL provides three distinct optimizer modes. Each is designed for a different decision context and should not be substituted for one another:

**Global Optimization** processes a batch of unscheduled appointments across a 1–7 day horizon. It is the full-workforce rescheduling engine. Global runs are typically triggered at the start of a day or week to fill the schedule and minimize total travel across the territory. Global optimization can move existing scheduled appointments if re-sequencing improves the overall score. It is the most resource-intensive optimization type and should not be triggered multiple times per hour.

**In-Day Optimization** runs during an active workday to respond to disruptions — cancellations, emergency insertions, or technician delays. It reschedules appointments within the current day only and does so within a tighter time window than Global. In-Day optimization is designed to be triggered automatically by platform events (e.g., a service appointment is cancelled) or manually by a dispatcher who needs to rebalance the schedule after a disruption. It does not reschedule across days.

**Resource Schedule Optimization** is a single-resource variant that optimizes the schedule for one technician at a time. Use it when a dispatcher needs to resequence one technician's day without affecting the rest of the territory. It is faster than In-Day for single-resource operations and appropriate for targeted adjustments.

### Appointment Priority Scoring

The optimizer uses a numeric priority score — not the scheduling policy's service objectives — to determine which appointments take precedence when it cannot schedule everything. This is a separate mechanism from service objective weighting.

Priority score is calculated from the appointment's `Priority` field (a picklist with numeric values 1–10) combined with due date urgency. Priority 1 (highest urgency) generates approximately **25,500 points** on the optimizer's internal score. Lower priorities generate proportionally fewer points. The relationship between priority number and score is not linear: the gap between priority 1 and priority 2 is larger than the gap between priority 5 and priority 6.

Appointments with a null `DueDate` are assigned the lowest possible priority score. In a constrained optimization run where not all appointments can fit, null-DueDate appointments will be left unscheduled first.

Practitioners should treat the `Priority` field and `DueDate` as required fields operationally, even if the platform does not enforce them at the data model level.

### Travel Mode: Aerial vs. Street-Level Routing

**Aerial (default, free):** The optimizer calculates travel time and distance using straight-line (as-the-crow-flies) distance between appointment locations. This is computationally cheap and requires no third-party integration. It is the correct choice for sparse rural territories where roads do not significantly deviate from straight-line paths, or for organizations that do not need high travel accuracy.

**Street-Level Routing (add-on, paid):** The optimizer uses actual road network data to calculate realistic drive times and distances. This add-on also supports **predictive traffic** data, which adjusts travel time estimates based on historical traffic patterns at the time of day. Street-Level Routing produces meaningfully more accurate schedules in dense urban areas and reduces the gap between planned and actual travel times. It requires a separate license and must be enabled in Setup > Field Service Settings > Routing.

Switching from Aerial to Street-Level Routing after go-live will change optimization outputs: schedules that were previously efficient under aerial calculations may be less efficient under street-level data, and vice versa. Test in a sandbox before enabling in production.

---

## Common Patterns

### Pattern: Weekly Global Optimization at Start of Day

**When to use:** The business prefers a fully loaded schedule at the beginning of each day or week. Dispatchers review and approve the optimized schedule rather than building it manually. Appointment volume exceeds what a dispatcher can sequence manually.

**How it works:**
1. Configure a scheduling policy with the appropriate work rules for the territory (Service Resource Availability, Match Skills, Match Territory as a baseline).
2. In Setup > Field Service > Optimization, create a Global Optimization run configuration. Set the horizon to the desired planning window (1–7 days). Select the scheduling policy.
3. Set the optimization run to trigger automatically via a scheduled job, or allow dispatchers to trigger it manually from the Dispatcher Console using the "Optimize" button.
4. After the run completes, dispatchers review the Gantt. Any appointments the optimizer could not schedule are flagged in the unscheduled appointments list. Dispatchers handle exceptions manually.
5. Monitor the optimizer log to confirm the run completed without errors and that the percentage of scheduled appointments meets the target SLA.

**Why not the alternative:** Manual dispatcher sequencing at scale produces inconsistent travel routing and wastes technician time on inefficient drive sequences. The optimizer evaluates combinations across the entire territory simultaneously, which a dispatcher cannot replicate.

### Pattern: In-Day Optimization Triggered by Cancellation Event

**When to use:** Same-day cancellations leave gaps in technician schedules. The business wants those gaps filled automatically by pulling forward other unscheduled or later appointments, without requiring dispatcher intervention for every disruption.

**How it works:**
1. Create a platform event or process (Flow) that fires when a service appointment status changes to "Cancelled" during business hours.
2. The Flow triggers an In-Day optimization job via the FSL API or the Field Service managed package's optimization invocable action.
3. In-Day optimization evaluates remaining unscheduled appointments for that day and fills the gap using the configured scheduling policy's work rules and objectives.
4. The dispatcher receives a notification that the schedule has been updated. They review and confirm, or override if needed.

**Why not the alternative:** Relying on dispatchers to manually respond to every same-day disruption introduces delay and inconsistency. In-Day optimization runs in minutes and produces a globally optimal adjustment for the day, whereas a dispatcher typically fills gaps by pulling the nearest appointment without evaluating the full-day sequence impact.

### Pattern: Resource Schedule Optimization for Single Technician Resequencing

**When to use:** A specific technician's schedule becomes disordered mid-day (new appointment inserted, one job runs long). The dispatcher wants to resequence only that technician without running a territory-wide optimization that would disrupt other resources.

**How it works:**
1. From the Dispatcher Console Gantt, select the specific service resource.
2. Use the "Optimize Resource" action to trigger Resource Schedule Optimization for that resource only.
3. The optimizer resequences the remaining appointments for that resource's day based on the scheduling policy and travel mode in use.
4. Review the updated sequence in the Gantt before confirming.

**Why not the alternative:** Triggering In-Day optimization for a single-resource adjustment runs across all resources in the territory unnecessarily. Resource Schedule Optimization is scoped and faster for targeted corrections.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Planning the full week's schedule before workdays begin | Global Optimization with 5–7 day horizon | Optimizes across the full appointment backlog and territory workforce simultaneously |
| Responding to a same-day cancellation or emergency insertion | In-Day Optimization | Scoped to current day only; faster and safer than re-running Global mid-day |
| Resequencing a single technician whose route is disordered | Resource Schedule Optimization | Faster than territory-wide In-Day; does not disturb other resources |
| Appointments with null DueDate are never getting scheduled | Populate DueDate on all service appointments operationally | Null DueDate means lowest optimizer score; these appointments are deferred indefinitely in constrained runs |
| Optimizer ignores high-priority appointments | Set Priority field to 1–3 for critical work and ensure DueDate is near-term | Priority 1 generates ~25,500 pts; without Priority and DueDate, all appointments appear equal to the optimizer |
| Territory is rural/sparse with minimal road deviation | Aerial travel mode (default) | Straight-line estimates acceptable; no additional license cost |
| Dense urban territory with significant traffic variation | Street-Level Routing add-on with predictive traffic | Road-network accuracy dramatically improves schedule fidelity in cities |
| Optimizer runs taking too long or timing out | Reduce optimization horizon, split into smaller territories, or schedule runs during off-peak hours | Global runs across large territories with long horizons are the most compute-intensive operations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm licensing and feature enablement** — Verify the FSL Optimizer is licensed for the org. Navigate to Setup > Field Service Settings and confirm optimization is enabled. Confirm the managed package version supports the optimization type being configured. Without the Optimizer license, the optimization controls will not appear in the Dispatcher Console.

2. **Assess the scheduling decision context** — Determine whether the primary need is pre-day bulk scheduling (Global), same-day disruption response (In-Day), or single-resource resequencing (Resource Schedule). Each optimization type solves a different problem; using the wrong type produces suboptimal results regardless of policy configuration.

3. **Audit appointment data quality** — Run a report on service appointments to identify records with null `DueDate` or null `Priority`. These records receive the lowest optimizer score and will be consistently skipped when the schedule is full. Establish a data quality rule or validation rule to require these fields before an appointment enters the scheduling queue.

4. **Select and configure travel mode** — Evaluate whether Aerial or Street-Level Routing is appropriate for the territory's geography and the business's travel accuracy requirements. If Street-Level Routing is selected, confirm the add-on license is active and enable it in Setup > Field Service Settings > Routing. Document the travel mode decision and its impact on optimization outputs.

5. **Configure the optimization run** — Create the optimization job configuration in Setup > Field Service > Optimization. Assign the appropriate scheduling policy. Set the correct time horizon. Define whether the job runs on a schedule or is triggered manually or by automation.

6. **Test in a sandbox with representative data** — Run the optimization against a representative sample of appointments and technicians in a sandbox environment. Validate that high-priority appointments are scheduled first, that travel sequences are logical, and that unscheduled appointments match expectations based on data quality.

7. **Monitor and tune post-go-live** — After production go-live, monitor the optimizer job logs for completion rate, appointment scheduling percentage, and any errors. If a high proportion of appointments remain unscheduled after a Global run, investigate DueDate/Priority data quality, scheduling policy restrictiveness, and resource availability configuration.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] FSL Optimizer license is confirmed active for the org
- [ ] Correct optimization type selected (Global, In-Day, or Resource Schedule) for the use case
- [ ] All service appointments have non-null `DueDate` and `Priority` fields
- [ ] Travel mode (Aerial or Street-Level Routing) selected and documented with business justification
- [ ] Scheduling policy assigned to the optimization run has Service Resource Availability work rule present
- [ ] Optimizer time horizon set appropriately (1–7 days for Global; current day only for In-Day)
- [ ] Optimization job tested in sandbox with representative appointment and resource data
- [ ] Post-optimization unscheduled appointment rate reviewed and acceptable
- [ ] Optimizer job logs checked for errors after first production run

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Null DueDate causes permanent deferral in constrained runs** — Service appointments with a null `DueDate` are treated as lowest priority by the optimizer. In any run where the schedule cannot accommodate all appointments, null-DueDate records are the first to be left unscheduled. Because this is silent behavior — the optimizer does not log a specific warning per appointment — practitioners often interpret the result as a policy misconfiguration rather than a data quality issue.

2. **Work Rules and Service Objectives are policy concerns, not optimizer concerns** — The optimizer uses the scheduling policy to filter and rank candidates, but the priority score (Priority field + DueDate) is a separate mechanism that operates above policy-level service objectives. Setting objective weights in the scheduling policy does not directly control which appointments are scheduled first when the optimizer cannot schedule all of them. Mixing these two mechanisms in troubleshooting leads to incorrect tuning.

3. **Priority score is not linear: priority 1 generates approximately 25,500 points** — The priority scoring scale is not a simple 10x multiplier. Priority 1 generates approximately 25,500 optimizer points. The drop from priority 1 to priority 2 is larger than the drop from priority 5 to priority 6. Organizations that assign priority 1 to all "important" appointments negate the differentiation: if everything is priority 1, the optimizer cannot distinguish between them and falls back to DueDate proximity for ordering.

4. **Street-Level Routing is a paid add-on and is not enabled by default** — Aerial is the default travel mode because it is free and computationally cheap. Street-Level Routing requires a separate license. Practitioners sometimes assume road-network routing is included because the Field Service product implies real-world travel. Enabling Street-Level Routing after go-live will change optimization outputs and travel time estimates, which can disrupt existing schedule patterns and dispatcher expectations.

5. **Global Optimization can reschedule already-scheduled appointments** — Unless explicitly configured otherwise, a Global optimization run may move appointments that are already scheduled if resequencing them improves the overall territory score. Dispatchers who have manually arranged specific appointments may find them rescheduled by a subsequent Global run. This is expected optimizer behavior, but it surprises teams who expect Global optimization to only fill empty slots.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Optimization type recommendation | Documented decision (Global / In-Day / Resource Schedule) with use-case justification |
| Travel mode decision record | Aerial vs. Street-Level Routing selection with licensing status and accuracy tradeoff documented |
| Priority scoring audit report | Report of service appointments with null DueDate or null Priority, with remediation guidance |
| Optimizer run configuration | Named optimization job in Setup > Field Service > Optimization with policy, horizon, and trigger configured |
| Post-run monitoring runbook | Step-by-step guide for reviewing optimizer job logs and unscheduled appointment lists after each run |

---

## Related Skills

- `fsl-scheduling-policies` — work rule and service objective configuration that the optimizer uses as its filtering and scoring input; configure the scheduling policy before configuring the optimizer
- `fsl-service-territory-setup` — service territory and resource membership configuration that the optimizer's territory-based work rules depend on
- `fsl-work-order-management` — work order priority and DueDate configuration that feeds into the optimizer's appointment priority scoring

---

## Official Sources Used

- Understanding Optimization in Field Service Scheduling (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-lightning-quick-look/understand-optimization
- Global Optimization Planning (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-scheduling/global-optimization
- Set Up Routing for Travel Time Calculations — https://help.salesforce.com/s/articleView?id=sf.fs_routing.htm
- Optimize Appointments Using Priorities — https://help.salesforce.com/s/articleView?id=sf.fs_optimizer_priorities.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
