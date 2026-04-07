# LLM Anti-Patterns — FSL Work Order Management

Common mistakes AI coding assistants make when generating or advising on FSL Work Order Management. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Work Order Status and Service Appointment Status Cascade Automatically

**What the LLM generates:** Guidance like "when all Service Appointments are completed, the Work Order will automatically move to Completed status" — or automation designs that skip building cascade logic because they assume Salesforce handles it.

**Why it happens:** LLMs conflate FSL with other case/ticket systems (ServiceNow, Zendesk, standard Case-with-Milestone) where parent record status does cascade from child resolution. Salesforce FSL explicitly does not do this, but training data mixes descriptions of those systems with FSL documentation.

**Correct pattern:**

```
WO status and SA status are completely independent picklists with no built-in link.
To cascade SA Completed → WO Completed, build a Record-Triggered Flow:
  Trigger: ServiceAppointment After Update (Status = Completed)
  Logic: Count sibling SAs where Status != Completed
  If count = 0: Update parent WorkOrder.Status = Completed
```

**Detection hint:** Look for phrases like "automatically updates," "cascades," or "propagates" between WO and SA status without referencing an explicit Flow or Apex trigger.

---

## Anti-Pattern 2: Confusing WorkType with WorkOrderLineItem

**What the LLM generates:** Statements like "add a WorkType to the Work Order to record each task or product line" — or designs that create multiple WorkType records per job to represent individual tasks.

**Why it happens:** The name "WorkType" sounds like it could mean "a type of work item on a job." LLMs conflate it with WorkOrderLineItem, which is the record that actually captures individual tasks or product lines. WorkType is a reusable template record that defines defaults (duration, auto-create SA) — not a per-task line item.

**Correct pattern:**

```
WorkType: A reusable template record (e.g., "HVAC Inspection") that stores
  Estimated Duration, DurationType, and AutoCreateSvcAppt defaults.
  One WorkType can be applied to many WOs.

WorkOrderLineItem: The per-job record representing a discrete task or product
  within a specific Work Order. Each WOLI can itself reference a WorkType
  to inherit duration defaults.
```

**Detection hint:** Any suggestion to "create multiple WorkType records for each task on the job" — or to "view WorkTypes in the related list to see what work was done."

---

## Anti-Pattern 3: Assuming AutoCreateSvcAppt Schedules the Appointment

**What the LLM generates:** Instructions like "set AutoCreateSvcAppt = true on the WorkType to automatically schedule and dispatch the service appointment when the work order is created."

**Why it happens:** The field name strongly implies full automation. LLMs interpret "auto-create service appointment" as including scheduling, dispatching, or assigning a resource — none of which occur. The field only creates the SA record in `None` status.

**Correct pattern:**

```
AutoCreateSvcAppt = true:
  - Creates one SA record in None status when WO/WOLI is saved
  - SA has no assigned resource
  - SA has no scheduled start time
  - SA appears in the unscheduled queue in Dispatcher Console
  - Dispatcher must still manually schedule or trigger Einstein Scheduling

Scheduling is a separate step that occurs AFTER SA creation.
```

**Detection hint:** Any phrase combining "AutoCreateSvcAppt" with "schedule," "dispatch," "assign," or "notify technician" without mentioning a separate dispatch step.

---

## Anti-Pattern 4: Treating Maintenance Plan Generation as Real-Time or On-Demand

**What the LLM generates:** Instructions like "save the Maintenance Plan and the Work Orders will be generated immediately" — or runbooks that say "after creating the Maintenance Plan, verify the WO in the related list."

**Why it happens:** Most Salesforce automation (Flows, triggers, Apex) runs synchronously or near-synchronously. LLMs default to assuming the same behavior for Maintenance Plans without knowing they rely on a background batch job that runs ~3 times per day.

**Correct pattern:**

```
Maintenance Plans are processed by a Salesforce background batch job.
Generation runs approximately 3 times per day (every ~8 hours).
There is no on-demand trigger in standard configuration.
Work Orders will NOT appear in the related list immediately after saving a plan.
For time-sensitive WO generation, use Scheduled Flow or API-based WO creation instead.
```

**Detection hint:** Instructions that tell the user to check for generated WOs immediately after Maintenance Plan creation, or SLA commitments built on Maintenance Plan timing.

---

## Anti-Pattern 5: Ignoring the 500 WOLI Gantt Visibility Limit When Designing Data Models

**What the LLM generates:** Data model designs that use a single Work Order with hundreds or thousands of Work Order Line Items, without flagging that the Dispatcher Console Gantt only renders up to 500 WOLIs per Work Order.

**Why it happens:** LLMs design based on functional correctness (a WO can technically have up to 10,000 child records) without surfacing operational UX limits. The 500-WOLI Gantt limit is documented in FSL release notes and limits documentation but is not a code-level enforcement — it is a UI rendering constraint that LLMs do not model.

**Correct pattern:**

```
Gantt Console limit: 500 WOLIs visible per Work Order
Record limit: 10,000 child records per Work Order

For large jobs (>400 WOLIs), use a parent-child Work Order hierarchy:
  ParentWorkOrder (container)
    └── ChildWorkOrder A (50 WOLIs)
    └── ChildWorkOrder B (50 WOLIs)
    └── ChildWorkOrder C (50 WOLIs)

Each child WO stays within Gantt visibility limits.
```

**Detection hint:** Any WO data model that assigns more than 400 WOLIs to a single Work Order without flagging Gantt limits or recommending a WO hierarchy.

---

## Anti-Pattern 6: Using WorkType as a Status-Filtering Mechanism

**What the LLM generates:** Queries or reports that filter active vs. inactive WorkTypes to understand which jobs are "in progress" — or automation that updates WorkType records to track job state.

**Why it happens:** LLMs sometimes conflate WorkType (a configuration template) with WorkOrder (the transactional record). WorkType records are static configuration; job state is tracked on WorkOrder and ServiceAppointment. Updating WorkTypes dynamically would corrupt templates shared across many WOs.

**Correct pattern:**

```
WorkType = configuration template (do not write job state here)
WorkOrder.Status = where job lifecycle state is tracked
ServiceAppointment.Status = where scheduling/dispatch state is tracked

SOQL for open jobs:
  SELECT Id, Subject, Status FROM WorkOrder WHERE Status != 'Completed'
  (NOT: SELECT Id FROM WorkType WHERE ...)
```

**Detection hint:** Any SOQL, Flow, or report that reads or writes WorkType records to determine or track current job status.
