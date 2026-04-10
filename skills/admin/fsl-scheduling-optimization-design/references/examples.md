# Examples — FSL Scheduling Optimization Design

## Example 1: Configuring Global Optimization for a Multi-Territory Field Service Operation

**Context:** A utilities company operates 12 service territories with 80 technicians. Dispatchers were manually building each technician's daily route in the Dispatcher Console Gantt. Scheduling 400+ appointments per day was taking 2–3 hours of dispatcher time each morning, and travel sequences were inconsistent because dispatchers optimized locally without seeing cross-technician conflicts.

**Problem:** Without Global Optimization, every dispatcher is solving a subset of the routing problem in isolation. Technician A's route might pass through a cluster of appointments that would be more efficient for Technician B, but no single dispatcher sees both schedules simultaneously. The result is predictable: excess travel, late arrivals, and appointment backlogs that grow through the week.

**Solution:**

```
Optimization Configuration (Setup > Field Service > Optimization):
  Name: Morning Global Run — All Territories
  Scheduling Policy: High Intensity (custom clone with Match Skills + Service Resource Availability)
  Time Horizon: 5 days (Mon–Fri)
  Optimization Type: Global
  Trigger: Scheduled — weekdays at 06:00 local time, 30 minutes before dispatchers log in

Appointment Data Requirements:
  - ServiceAppointment.DueDate: populated for all records (required field via validation rule)
  - ServiceAppointment.Priority: 1–5 range; maintenance = 4, inspections = 5, emergency = 1
  - ServiceAppointment.Duration: accurate duration from Work Type (not default 60 min)

Post-Run Dispatcher Workflow:
  1. Review Dispatcher Console Gantt at 06:30 — optimizer has pre-loaded the day
  2. Check Unscheduled Appointments list — handle exceptions manually (typically <5% of volume)
  3. Confirm flagged appointments (yellow triangles) before start of shift
```

**Why it matters:** Global Optimization evaluates every territory's full appointment backlog simultaneously and produces a schedule that minimizes total travel across all technicians in the run. The dispatcher role shifts from manual route-building to exception handling — a more scalable and consistent workflow. Scheduling time dropped from 2–3 hours to 20 minutes of exception review.

---

## Example 2: In-Day Optimization Triggered Automatically on Cancellation

**Context:** A telecom field service team handles 200 appointments per day. Approximately 8% of appointments are cancelled on the day of service (customer not home, access issues). Each cancellation left a gap in a technician's schedule that dispatchers had to fill manually, often leaving technicians with 60–90 minute idle windows.

**Problem:** Dispatchers were too busy with new call intake to consistently backfill cancelled appointments. Idle gaps accumulated across the territory, reducing appointment throughput by 12–15 appointments per day.

**Solution:**

```
Flow: Auto-trigger In-Day Optimization on Cancellation

Trigger: Record-Triggered Flow on ServiceAppointment
  - Trigger Condition: Status changes to "Cannot Complete" or "Customer No Show"
  - Condition: SchedStartTime is today (within current business day)
  - Time: Only during business hours (08:00–17:00)

Flow Action:
  - Invocable Action: "Optimize In Day" (from FSL managed package)
  - Input: Territory = ServiceAppointment.ServiceTerritoryId
  - Input: Policy = In-Day Scheduling Policy (custom clone of Customer First, ASAP weighted 70%)
  - Input: Horizon = current day only

Notification:
  - Custom notification to dispatcher: "In-Day optimization ran after cancellation at [Address]. 
    Review schedule updates in Gantt."

Data Requirements:
  - All same-day unscheduled appointments must have DueDate = today or within 3 days
  - Priority must be set (no nulls) to allow optimizer to rank backfill candidates
```

**Why it matters:** Automating In-Day optimization on cancellation events removes the dependency on dispatcher availability to backfill gaps. The optimizer evaluates all same-day unscheduled appointments and finds the best candidate for the newly available slot — factoring in travel from the technician's current location, skills match, and customer time windows. The team recovered 10–12 appointments per day that previously went unscheduled due to manual backfill delay.

---

## Example 3: Priority Score Misconfiguration — All Appointments at Priority 1

**Context:** A home services company configured all service appointments with `Priority = 1` based on the reasoning that "all customer appointments are equally important." During optimizer runs, they observed no meaningful differentiation in scheduling order and blamed service objective weighting for the problem.

**Problem:** When every appointment has `Priority = 1`, all records generate the same optimizer score (~25,500 points each). The optimizer cannot use priority to differentiate scheduling order and falls back entirely to DueDate proximity. Appointments with identical DueDates are ordered arbitrarily. The intended effect of "all appointments matter equally" produced an optimizer that behaved as if no priority configuration existed at all.

**Solution:**

```
Priority Tier Assignment (recommended mapping):
  Priority 1 (~25,500 pts): Emergency / safety-critical / SLA breach in <4 hours
  Priority 2: Urgent — customer-impacting, same-day response required
  Priority 3: High — next-business-day SLA commitment
  Priority 4: Standard — routine maintenance, scheduled within 3–5 days
  Priority 5–7: Low urgency — planned preventive maintenance, flexible window
  Priority 8–10: Lowest — bulk recertification, non-customer-facing work

Implementation:
  - Set Priority automatically via Flow based on Work Type or Case escalation level
  - Never default all records to Priority 1
  - DueDate should align with the SLA tier (Priority 1 due today, Priority 4 due in 5 days)
```

**Why it matters:** The optimizer's priority scoring model is only useful when the Priority field carries real differentiation. Collapsing all appointments to a single priority tier eliminates the optimizer's ability to protect high-value work during constrained scheduling runs. Introducing a 4–5 tier priority model, aligned to business SLA categories, allows the optimizer to reliably protect emergency and urgent appointments from being deferred.

---

## Anti-Pattern: Using Global Optimization to Handle Same-Day Disruptions

**What practitioners do:** A dispatcher notices a gap caused by a morning cancellation and triggers a Global Optimization run to fill it, using a 5-day horizon.

**What goes wrong:** A Global run with a 5-day horizon re-evaluates the entire territory schedule across all days and may reschedule appointments that were confirmed for later in the week. Customers may receive new appointment confirmations that conflict with prior commitments. Additionally, Global runs are compute-intensive and can take 10–30 minutes to complete, which is far too slow for a same-day gap that needs filling in minutes.

**Correct approach:** Use In-Day Optimization for same-day disruptions. In-Day is scoped to the current day, runs faster, and does not touch appointments scheduled on future days. Reserve Global Optimization for pre-day bulk scheduling with explicit dispatcher review before schedule delivery.
