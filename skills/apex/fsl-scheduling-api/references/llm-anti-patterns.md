# LLM Anti-Patterns — FSL Scheduling API

Common mistakes AI coding assistants make when generating or advising on FSL Scheduling API.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Single-Transaction GetSlots + DML + schedule()

**What the LLM generates:**
```apex
@AuraEnabled
public static void bookAppointment(Id saId, Id policyId) {
    List<FSL.Scheduling.TimeSlot> slots = FSL.AppointmentBookingService.GetSlots(saId, null, policyId);
    ServiceAppointment sa = [SELECT Id FROM ServiceAppointment WHERE Id = :saId];
    sa.ArrivalWindowStart = slots[0].startTime;
    sa.ArrivalWindowEnd = slots[0].endTime;
    update sa;  // DML before second callout — will throw!
    FSL.ScheduleService.schedule(saId, policyId);
}
```

**Why it happens:** LLMs pattern-match to "sequential steps" and don't model Apex's callout-DML transaction constraint. The sequence looks logically correct but violates platform rules.

**Correct pattern:** Split into two @AuraEnabled methods. Transaction 1: GetSlots only. Transaction 2: DML on ArrivalWindow, then schedule().

**Detection hint:** Any method containing both `FSL.AppointmentBookingService.GetSlots` and `update sa` (or any DML) followed by `FSL.ScheduleService.schedule` in the same method body is wrong.

---

## Anti-Pattern 2: Calling schedule() Inside a Trigger

**What the LLM generates:**
```apex
trigger ServiceAppointmentTrigger on ServiceAppointment (after insert) {
    for (ServiceAppointment sa : Trigger.new) {
        FSL.ScheduleService.schedule(sa.Id, POLICY_ID); // throws CalloutException
    }
}
```

**Why it happens:** LLMs know "after insert triggers can make async-style calls" but don't model the specific Apex callout constraint that prohibits callouts when DML is uncommitted — and trigger execution is always inside an uncommitted transaction.

**Correct pattern:**
```apex
trigger ServiceAppointmentTrigger on ServiceAppointment (after insert) {
    Set<Id> ids = Trigger.newMap.keySet();
    System.enqueueJob(new FslScheduleQueueable(ids));
}
```

**Detection hint:** Any `FSL.ScheduleService.schedule` or `FSL.AppointmentBookingService.GetSlots` call inside a trigger handler class or trigger body is wrong.

---

## Anti-Pattern 3: Batch Apex with Default Size for FSL Scheduling

**What the LLM generates:**
```apex
Database.executeBatch(new BulkFslScheduler()); // uses default size 200
```
or
```apex
Database.executeBatch(new BulkFslScheduler(), 50); // still too large
```

**Why it happens:** LLMs know batch size controls chunk size but don't know FSL scheduling callouts require exactly size 1 due to callout limits and transaction isolation requirements.

**Correct pattern:**
```apex
Database.executeBatch(new BulkFslScheduler(), 1);
```

**Detection hint:** Any `Database.executeBatch` call on an FSL scheduling class without `, 1` as the second argument is likely wrong.

---

## Anti-Pattern 4: Not Checking schedule() for Null Return

**What the LLM generates:**
```apex
FSL.ScheduleResult result = FSL.ScheduleService.schedule(saId, policyId);
// proceeds assuming scheduling succeeded
system.debug('Assigned to: ' + result.serviceResource.Name);
```

**Why it happens:** LLMs pattern-match to exception-based error handling. They assume a method either succeeds or throws. FSL's schedule() returns null on failure instead of throwing, which LLMs miss because it's non-standard.

**Correct pattern:**
```apex
FSL.ScheduleResult result = FSL.ScheduleService.schedule(saId, policyId);
if (result == null) {
    // log error, flag SA for manual dispatch
    return;
}
System.debug('Assigned to: ' + result.serviceResource.Name);
```

**Detection hint:** Code that uses `result.` immediately after `FSL.ScheduleService.schedule()` without a null check is wrong.

---

## Anti-Pattern 5: Assuming OAAS Is Available Without Add-On

**What the LLM generates:** OAAS invocation code presented as a standard FSL feature available in all orgs, or code that calls `FSL.OAAS` methods without noting the Enhanced Scheduling and Optimization add-on requirement.

**Why it happens:** LLMs conflate the FSL base license with all FSL features. OAAS (and ESO) are add-ons with separate licensing and operation limits that training data does not reliably distinguish.

**Correct pattern:** Always include a prerequisite check comment and note in implementation docs that OAAS requires the Field Service Scheduling optimization add-on license. For ESO-specific operations, note per-territory ESO enrollment in Setup.

**Detection hint:** Any OAAS implementation without a comment or check confirming the add-on license is potentially misleading.

---

## Anti-Pattern 6: Constructing Custom TimeSlot Objects for GradeSlots

**What the LLM generates:**
```apex
FSL.Scheduling.TimeSlot ts = new FSL.Scheduling.TimeSlot();
ts.startTime = someDateTime;
ts.endTime = someOtherDateTime;
List<FSL.Scheduling.TimeSlot> slotList = new List<FSL.Scheduling.TimeSlot>{ ts };
FSL.GradeSlotsService.GradeSlots(saId, slotList, policyId); // undefined behavior
```

**Why it happens:** LLMs see `GradeSlotsService.GradeSlots` accepts a `List<FSL.Scheduling.TimeSlot>` and construct objects manually, not knowing that TimeSlots from GetSlots contain internal state required by GradeSlots.

**Correct pattern:** Always pipe GetSlots output directly into GradeSlots:
```apex
List<FSL.Scheduling.TimeSlot> slots = FSL.AppointmentBookingService.GetSlots(saId, null, policyId);
List<FSL.Scheduling.TimeSlot> graded = FSL.GradeSlotsService.GradeSlots(saId, slots, policyId);
```

**Detection hint:** Any `new FSL.Scheduling.TimeSlot()` construction followed by use in GradeSlots is wrong.
