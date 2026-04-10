# Examples — FSL Scheduling API

## Example 1: Two-Transaction Booking Flow with LWC

**Context:** A Lightning Web Component presents available appointment windows to a customer. The dispatcher selects a window and the system hard-assigns a resource. The implementation uses an `@AuraEnabled` method for slot retrieval and a second `@AuraEnabled` method for assignment.

**Problem:** A developer tries to call `GetSlots()`, update the SA's ArrivalWindow fields with DML, then call `schedule()` all within one Apex method. This throws `System.CalloutException: You have uncommitted work pending` because DML before a callout is not allowed when the DML is uncommitted.

**Solution:**

```apex
// Method 1 — called on page load or "Check Availability" button
@AuraEnabled
public static List<Map<String, Object>> getAvailableSlots(Id saId, Id policyId) {
    List<FSL.Scheduling.TimeSlot> slots =
        FSL.AppointmentBookingService.GetSlots(saId, null, policyId);
    // Optionally grade the slots
    List<FSL.Scheduling.TimeSlot> graded =
        FSL.GradeSlotsService.GradeSlots(saId, slots, policyId);
    List<Map<String, Object>> result = new List<Map<String, Object>>();
    for (FSL.Scheduling.TimeSlot ts : graded) {
        result.add(new Map<String, Object>{
            'startTime' => ts.startTime,
            'endTime'   => ts.endTime,
            'grade'     => ts.grade
        });
    }
    return result;
}

// Method 2 — called after user selects a slot
@AuraEnabled
public static void confirmBooking(Id saId, Datetime windowStart, Datetime windowEnd, Id policyId) {
    // DML first — no prior callout in this transaction
    ServiceAppointment sa = [SELECT Id FROM ServiceAppointment WHERE Id = :saId FOR UPDATE];
    sa.ArrivalWindowStart = windowStart;
    sa.ArrivalWindowEnd   = windowEnd;
    update sa;
    // Now schedule — callout after DML is committed
    FSL.ScheduleResult result = FSL.ScheduleService.schedule(saId, policyId);
    if (result == null) {
        throw new AuraHandledException('No available resource found for this window.');
    }
}
```

**Why it works:** Each method executes in its own transaction. `GetSlots` and `GradeSlots` are callout-only (no DML). `confirmBooking` does DML first and calls `schedule()` after — the callout constraint requires no uncommitted DML *preceding* the callout in the same transaction.

---

## Example 2: Bulk Scheduling via Batch Apex

**Context:** After a data migration loading 5,000 new ServiceAppointments with Status = 'None', a post-migration step needs to auto-assign resources to all of them using the Default Scheduling Policy.

**Problem:** A developer loops over the SA list and calls `FSL.ScheduleService.schedule()` inside a single transaction. This immediately hits `System.LimitException: Too many callouts: 101` after the first 100 records and the entire batch fails with no partial commit.

**Solution:**

```apex
global class PostMigrationFslScheduler
    implements Database.Batchable<SObject>, Database.AllowsCallouts {

    private final Id schedulingPolicyId;

    global PostMigrationFslScheduler(Id policyId) {
        this.schedulingPolicyId = policyId;
    }

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id FROM ServiceAppointment WHERE Status = \'None\' AND SchedStartTime = NULL'
        );
    }

    global void execute(Database.BatchableContext bc, List<SObject> scope) {
        ServiceAppointment sa = (ServiceAppointment) scope[0];
        try {
            FSL.ScheduleResult result = FSL.ScheduleService.schedule(sa.Id, schedulingPolicyId);
            if (result == null) {
                // Log unscheduled SA to a custom error object
                insert new FSL_Schedule_Error__c(
                    ServiceAppointment__c = sa.Id,
                    Reason__c = 'No resource available'
                );
            }
        } catch (Exception ex) {
            insert new FSL_Schedule_Error__c(
                ServiceAppointment__c = sa.Id,
                Reason__c = ex.getMessage()
            );
        }
    }

    global void finish(Database.BatchableContext bc) {
        // Notify dispatcher team via custom notification
    }
}

// Invoke: Database.executeBatch(new PostMigrationFslScheduler(POLICY_ID), 1);
```

**Why it works:** `Database.executeBatch` with size 1 ensures each SA is scheduled in its own transaction. `Database.AllowsCallouts` marks the class as callout-eligible. Errors are isolated per SA — one unschedulable appointment does not abort the others.

---

## Anti-Pattern: Calling schedule() Inside a Trigger

**What practitioners do:** A developer adds an after-insert trigger on ServiceAppointment that calls `FSL.ScheduleService.schedule(sa.Id, policyId)` to auto-schedule every newly created SA.

**What goes wrong:** Apex triggers run inside the same transaction as the DML that fired them. Calling a callout inside a trigger that was fired by DML throws `System.CalloutException: You have uncommitted work pending`. Even if the DML was committed before the trigger (after-insert), Salesforce's transaction model still treats the trigger as part of the same uncommitted unit of work.

**Correct approach:** In the after-insert trigger, enqueue a Queueable:

```apex
trigger ServiceAppointmentTrigger on ServiceAppointment (after insert) {
    Set<Id> newSaIds = new Map<Id, ServiceAppointment>(
        (List<ServiceAppointment>) Trigger.new
    ).keySet();
    System.enqueueJob(new FslScheduleQueueable(newSaIds));
}

public class FslScheduleQueueable implements Queueable, Database.AllowsCallouts {
    private final Set<Id> saIds;
    public FslScheduleQueueable(Set<Id> ids) { this.saIds = ids; }
    public void execute(QueueableContext ctx) {
        for (Id saId : saIds) {
            FSL.ScheduleService.schedule(saId, POLICY_ID);
        }
    }
}
```

Note: This Queueable pattern works for small volumes. For bulk post-insert auto-scheduling, use Batch Apex with size 1.
