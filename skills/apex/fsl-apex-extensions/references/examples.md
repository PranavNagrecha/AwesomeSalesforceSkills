# Examples — FSL Apex Extensions

## Example 1: Interactive Appointment Booking via Queueable (GetSlots then Schedule)

**Context:** A custom LWC "Book Appointment" button triggers an Apex invocable action. The action creates a ServiceAppointment record and immediately needs to find available slots and book the first one. The ServiceAppointment insert and the FSL API call cannot share a transaction.

**Problem:** Calling `FSL.AppointmentBookingService.GetSlots()` immediately after `insert sa` in the same method throws `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out`. The FSL booking API internally makes an HTTP callout for travel routing, which Salesforce blocks after uncommitted DML.

**Solution:**

Step 1 — Invocable action inserts the ServiceAppointment and enqueues the booking job:

```apex
public class BookAppointmentAction {

    @InvocableMethod(label='Book FSL Appointment')
    public static void bookAppointment(List<BookingRequest> requests) {
        BookingRequest req = requests[0];

        // Insert SA — this DML must commit before FSL API can be called
        ServiceAppointment sa = new ServiceAppointment(
            ParentRecordId   = req.workOrderId,
            ServiceTerritoryId = req.serviceTerritoryId,
            EarliestStartTime  = req.earliestStart,
            DueDate            = req.dueDate
        );
        insert sa;

        // Enqueue booking — runs in a fresh transaction with no prior DML
        System.enqueueJob(new FSLBookingQueueable(
            sa.Id,
            req.schedulingPolicyId,
            req.operatingHoursId
        ));
    }

    public class BookingRequest {
        @InvocableVariable public Id workOrderId;
        @InvocableVariable public Id serviceTerritoryId;
        @InvocableVariable public Id schedulingPolicyId;
        @InvocableVariable public Id operatingHoursId;
        @InvocableVariable public DateTime earliestStart;
        @InvocableVariable public DateTime dueDate;
    }
}
```

Step 2 — Queueable calls GetSlots and schedules the highest-graded slot:

```apex
public class FSLBookingQueueable implements Queueable, Database.AllowsCallouts {

    private final Id saId;
    private final Id policyId;
    private final Id ohId;

    public FSLBookingQueueable(Id saId, Id policyId, Id ohId) {
        this.saId     = saId;
        this.policyId = policyId;
        this.ohId     = ohId;
    }

    public void execute(QueueableContext ctx) {
        // No prior DML in this transaction — callout is safe
        List<FSL.AppointmentBookingSlot> slots =
            FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);

        if (slots == null || slots.isEmpty()) {
            // Log and exit gracefully — no available slots
            System.debug(LoggingLevel.WARN, 'No available slots for SA: ' + saId);
            return;
        }

        // Pick the slot with the highest grade (first in returned list is highest-graded)
        FSL.AppointmentBookingSlot best = slots[0];

        FSL.ScheduleService.schedule(
            saId,
            policyId,
            best.Resource.Id,
            best.Interval_Start__c,
            best.Interval_End__c
        );
    }
}
```

**Why it works:** The `insert sa` statement in the action method commits when that transaction ends. The Queueable runs in a completely new Apex transaction where no DML has occurred, satisfying the platform's callout-after-DML restriction. `Database.AllowsCallouts` must be declared on the Queueable class for the internal FSL HTTP callout to be permitted.

---

## Example 2: Bulk Scheduling Batch Job (batchSize=1)

**Context:** A nightly scheduled job needs to schedule all ServiceAppointments with status "None" (unscheduled) against the FSL engine without human intervention. There may be 200–500 appointments to process.

**Problem:** A standard batch class with batchSize=200 fails: the first appointment's `schedule()` call leaves uncommitted routing state, and the second appointment's call in the same batch chunk triggers the uncommitted work exception. Setting batchSize > 1 is not safe with FSL scheduling APIs.

**Solution:**

```apex
public class FSLBulkScheduleBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {

    private final Id policyId;

    public FSLBulkScheduleBatch(Id schedulingPolicyId) {
        this.policyId = schedulingPolicyId;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Query unscheduled appointments with a ServiceTerritory assigned
        return Database.getQueryLocator([
            SELECT Id
            FROM   ServiceAppointment
            WHERE  Status = 'None'
            AND    ServiceTerritoryId != null
        ]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // scope contains exactly 1 record when batchSize=1
        ServiceAppointment sa = (ServiceAppointment) scope[0];

        try {
            // No prior DML in this execute() call — callout is safe
            List<FSL.AppointmentBookingSlot> slots =
                FSL.AppointmentBookingService.GetSlots(
                    sa.Id,
                    policyId,
                    null  // null = use territory operating hours
                );

            if (slots != null && !slots.isEmpty()) {
                FSL.AppointmentBookingSlot best = slots[0];
                FSL.ScheduleService.schedule(
                    sa.Id,
                    policyId,
                    best.Resource.Id,
                    best.Interval_Start__c,
                    best.Interval_End__c
                );
            } else {
                System.debug(LoggingLevel.WARN, 'No slots for SA: ' + sa.Id);
            }
        } catch (Exception e) {
            // Log but do not re-throw — batch continues for remaining appointments
            System.debug(LoggingLevel.ERROR,
                'Failed to schedule SA ' + sa.Id + ': ' + e.getMessage());
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('FSL bulk scheduling batch complete.');
    }
}
```

Invoke with:

```apex
Database.executeBatch(new FSLBulkScheduleBatch(policyId), 1);
```

**Why it works:** `Database.executeBatch(..., 1)` ensures each `execute()` call processes one ServiceAppointment in a fresh transaction. No DML has occurred in that transaction before the `GetSlots()` call, so the internal HTTP callout succeeds. The `try/catch` block prevents a single appointment failure from aborting the entire batch run.

---

## Example 3: OAAS Optimization Trigger

**Context:** After a field technician calls in sick, a dispatcher needs to re-optimize the day's schedule for a ServiceTerritory to redistribute appointments to available resources. This must be triggered from an Apex action rather than manually in the Dispatcher Console.

**Problem:** Manually triggering optimization from the console is not scriptable. The `FSL.OAAS` API provides a programmatic entry point, but it requires the Enhanced Scheduling and Optimization add-on and its methods are unfamiliar to developers used to standard Apex.

**Solution:**

```apex
public class TriggerFSLOptimization {

    @InvocableMethod(label='Trigger FSL In-Day Optimization')
    public static List<String> triggerInDay(List<OptimizationRequest> requests) {
        OptimizationRequest req = requests[0];
        List<String> jobIds = new List<String>();

        // FSL.OAAS.inDay(serviceTerritoryId, policyId, startTime, endTime, allTasksMode)
        String jobId = FSL.OAAS.inDay(
            req.serviceTerritoryId,
            req.policyId,
            req.optimizationStart,
            req.optimizationEnd,
            false  // false = optimize only unscheduled; true = reschedule all
        );

        jobIds.add(jobId);
        return jobIds;
    }

    public class OptimizationRequest {
        @InvocableVariable public Id serviceTerritoryId;
        @InvocableVariable public Id policyId;
        @InvocableVariable public DateTime optimizationStart;
        @InvocableVariable public DateTime optimizationEnd;
    }
}
```

**Why it works:** `FSL.OAAS.inDay()` submits the optimization job asynchronously and returns a String job ID. The job runs on Salesforce infrastructure. The returned job ID can be stored on a custom field for audit or used to poll optimization status via FSL APIs. This call does not itself make a synchronous callout in the way GetSlots/schedule do, so it is safe to call after DML — though placing it in a Queueable is still a good practice for clean separation.

---

## Anti-Pattern: Calling GetSlots Directly After Insert in the Same Transaction

**What practitioners do:** Insert a ServiceAppointment and immediately call `FSL.AppointmentBookingService.GetSlots()` in the same Apex method, assuming the FSL call is a database lookup rather than a callout.

**What goes wrong:** `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out` — the platform blocks the FSL HTTP callout because the insert is uncommitted. The appointment is created but never scheduled, and the exception may swallow the operation silently if caught by a broad exception handler.

**Correct approach:** Always separate the DML and the FSL API call into distinct transactions using a Queueable (single record) or Batch with batchSize=1 (bulk). Pass the record IDs across the transaction boundary via Queueable constructor parameters or via the batch query locator.
