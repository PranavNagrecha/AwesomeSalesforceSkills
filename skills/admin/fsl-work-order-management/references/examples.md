# Examples — FSL Work Order Management

## Example 1: Preventive Maintenance Work Order with Auto-Created Service Appointment via WorkType

**Context:** A utilities company runs monthly transformer inspections. Each inspection is a standard 90-minute job. They want every Work Order for transformer inspections to automatically generate a Service Appointment so the dispatcher queue is populated without manual steps.

**Problem:** Without WorkType configuration, admins must manually create a ServiceAppointment after each Work Order is saved. At scale (hundreds of WOs per day), this creates dispatch delays and increases the chance of jobs being missed in the queue.

**Solution:**

Step 1 — Create the WorkType:

```
WorkType:
  Name: Transformer Inspection
  Estimated Duration: 90
  DurationType: Minutes
  AutoCreateSvcAppt: true
```

Step 2 — Set up the Maintenance Plan:

```
MaintenancePlan:
  WorkTypeId: [Transformer Inspection WorkType ID]
  StartDate: 2025-01-01
  EndDate: 2026-12-31
  Frequency: 1
  FrequencyType: Monthly
  GenerationHorizon: 30  (days ahead to generate WOs)
```

Step 3 — Verify SA auto-creation after WO is generated:

When the Maintenance Plan batch runs (up to 3x daily), it creates WorkOrders with `WorkTypeId` set to Transformer Inspection. Because `AutoCreateSvcAppt = true`, Salesforce automatically creates a child ServiceAppointment in `None` status for each WO.

Step 4 — Dispatcher action:

The dispatcher opens the Dispatcher Console, sees SAs in the unscheduled queue, and assigns them to available technicians in the relevant service territory.

**Why it works:** WorkType's `AutoCreateSvcAppt` field triggers SA creation at WO save time. Salesforce copies the Estimated Duration onto the SA, giving the Gantt accurate time blocks. The SA starts in `None` status — it is not scheduled or dispatched until a dispatcher acts. This separation of "creation" from "scheduling" is intentional FSL architecture.

---

## Example 2: Emergency Work Order with Manual Service Appointment and Direct Resource Assignment

**Context:** A field operations manager receives an urgent call — a customer's HVAC unit has failed during a heat wave. The job must be assigned to a specific senior technician within the next 2 hours, bypassing the normal scheduling queue.

**Problem:** Using AutoCreateSvcAppt would create an SA in `None` status with no time constraint and no assigned resource. The dispatcher would need to find the SA in the queue, set urgency, and manually assign — adding friction during an emergency.

**Solution:**

Step 1 — Create the Work Order with the correct WorkType:

```
WorkOrder:
  Subject: Emergency HVAC Repair - Customer XYZ
  AccountId: [Customer Account]
  WorkTypeId: [HVAC Corrective Repair WorkType]
  Priority: High
  Status: New
```

Step 2 — Manually create the ServiceAppointment with urgency window:

```
ServiceAppointment:
  ParentRecordId: [WorkOrder ID]
  Subject: Emergency HVAC Repair - Customer XYZ
  EarliestStartTime: 2025-07-15T14:00:00Z
  DueDate: 2025-07-15T16:00:00Z
  Duration: 90
  Status: Scheduled
```

Step 3 — Create an AssignedResource record to link the specific technician:

```
AssignedResource:
  ServiceAppointmentId: [SA ID]
  ServiceResourceId: [Senior Technician Resource ID]
  IsRequiredResource: true
```

Step 4 — Update SA status to Dispatched to notify the technician:

```
ServiceAppointment.Status: Dispatched
```

This triggers the FSL mobile app notification to the technician if push notifications are configured.

**Why it works:** Bypassing AutoCreateSvcAppt gives the operations manager full control over timing and resource assignment. Setting `EarliestStartTime` and `DueDate` signals urgency to both the dispatcher UI and any scheduling optimization runs. Moving status directly to `Dispatched` bypasses the dispatcher queue and immediately notifies the field technician.

---

## Anti-Pattern: Assuming SA Completion Closes the Work Order

**What practitioners do:** They complete all Service Appointments on a Work Order, then expect the WO status to automatically update to Completed or Closed.

**What goes wrong:** Nothing happens. The WO remains in its current status (e.g., In Progress or New) regardless of SA status. Support teams then see open Work Orders with all-completed SAs, breaking SLA reporting and operations dashboards.

**Correct approach:** Build a Record-Triggered Flow on ServiceAppointment that fires after status is updated to `Completed`. The Flow queries all sibling SAs on the same WO and checks if all are `Completed`. If so, it updates the parent WorkOrder status to `Completed`.

```
Trigger: ServiceAppointment — After Update — Status Changed to Completed
Decision: COUNT(child SAs where Status != Completed) = 0
Action: Update WorkOrder.Status = Completed
```

This must be built explicitly — it does not exist out of the box.
