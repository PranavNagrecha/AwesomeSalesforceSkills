# LLM Anti-Patterns — FSL Apex Extensions

Common mistakes AI coding assistants make when generating or advising on FSL Apex Extensions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Calling GetSlots Immediately After DML in the Same Method

**What the LLM generates:**

```apex
ServiceAppointment sa = new ServiceAppointment(...);
insert sa;
// Then immediately:
List<FSL.AppointmentBookingSlot> slots =
    FSL.AppointmentBookingService.GetSlots(sa.Id, policyId, ohId);
```

**Why it happens:** LLMs trained on standard Salesforce Apex patterns treat `GetSlots()` as a database query (like a SOQL call), which is safe after DML. The distinction that FSL methods make internal HTTP callouts is not well-represented in training data, and the pattern "insert record, then use its ID" is extremely common.

**Correct pattern:**

```apex
// Transaction 1: insert the SA
insert sa;
// Enqueue — runs in a new transaction with no prior DML
System.enqueueJob(new FSLBookingQueueable(sa.Id, policyId, ohId));
// In the Queueable's execute(): call GetSlots() safely
```

**Detection hint:** Any code where `FSL.AppointmentBookingService.GetSlots(` or `FSL.ScheduleService.schedule(` appears in the same method body as `insert`, `update`, `upsert`, or `delete` without an intervening transaction boundary.

---

## Anti-Pattern 2: Batch Class Without batchSize=1

**What the LLM generates:**

```apex
Database.executeBatch(new FSLScheduleBatch(policyId));
// or
Database.executeBatch(new FSLScheduleBatch(policyId), 200);
```

**Why it happens:** LLMs know that larger batch sizes are more efficient for standard Apex DML and SOQL operations. The FSL-specific constraint that batchSize must be 1 to avoid the uncommitted-work-callout conflict is a domain-specific nuance not present in general Apex training data.

**Correct pattern:**

```apex
// batchSize=1 is mandatory for FSL scheduling API calls
Database.executeBatch(new FSLScheduleBatch(policyId), 1);
```

**Detection hint:** Any `Database.executeBatch(` call invoking a batch class that contains `FSL.` method calls, where the second argument is absent (defaults to 200) or is greater than 1.

---

## Anti-Pattern 3: Missing `Database.AllowsCallouts` on the Queueable or Batch

**What the LLM generates:**

```apex
public class FSLBookingQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        List<FSL.AppointmentBookingSlot> slots =
            FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);
    }
}
```

**Why it happens:** LLMs often scaffold the minimum interface declaration for Queueable without adding `Database.AllowsCallouts`. Since FSL methods make internal callouts, the `Database.AllowsCallouts` interface must be explicitly declared; omitting it causes `System.CalloutException: Callout not allowed from this future method` or `Queueable does not allow callouts`.

**Correct pattern:**

```apex
public class FSLBookingQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        List<FSL.AppointmentBookingSlot> slots =
            FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);
    }
}
```

**Detection hint:** A class that `implements Queueable` (or `implements Database.Batchable`) and calls any `FSL.` method, where `Database.AllowsCallouts` is not in the implements clause.

---

## Anti-Pattern 4: Using @future Instead of Queueable in Batch Context

**What the LLM generates:**

```apex
public class FSLScheduleBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {
    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        ServiceAppointment sa = (ServiceAppointment) scope[0];
        // Tries to use @future for the FSL call
        FSLHelper.scheduleAsync(sa.Id, policyId);
    }
}

public class FSLHelper {
    @future(callout=true)
    public static void scheduleAsync(Id saId, Id policyId) { ... }
}
```

**Why it happens:** LLMs know `@future(callout=true)` is valid for separating callouts from synchronous DML, and they correctly apply it in trigger contexts. However, the constraint that `@future` cannot be called from batch Apex is often missed — LLMs apply the `@future` pattern uniformly across contexts.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<SObject> scope) {
    ServiceAppointment sa = (ServiceAppointment) scope[0];
    // Call FSL directly — batchSize=1 ensures clean transaction
    FSL.ScheduleService.schedule(sa.Id, policyId, resourceId, startDt, endDt);
    // OR: enqueue a Queueable (max 1 per execute() in batch context)
    System.enqueueJob(new FSLBookingQueueable(sa.Id, policyId, ohId));
}
```

**Detection hint:** A `@future` method call inside a `Database.Batchable` `execute()` method, or a class that both `implements Database.Batchable` and contains `@future` annotated helper method calls.

---

## Anti-Pattern 5: Assuming GetSlots Returns a Non-Empty List Without Checking

**What the LLM generates:**

```apex
List<FSL.AppointmentBookingSlot> slots =
    FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);

FSL.AppointmentBookingSlot best = slots[0]; // ListException if empty
FSL.ScheduleService.schedule(
    saId, policyId, best.Resource.Id, best.Interval_Start__c, best.Interval_End__c
);
```

**Why it happens:** LLMs often generate the "happy path" without defensive null/empty checks, particularly for method calls whose return semantics (empty list vs. null) are not always made explicit in training examples.

**Correct pattern:**

```apex
List<FSL.AppointmentBookingSlot> slots =
    FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);

if (slots == null || slots.isEmpty()) {
    // Handle no-availability gracefully
    System.debug(LoggingLevel.WARN, 'No slots available for SA: ' + saId);
    return;
}

FSL.AppointmentBookingSlot best = slots[0];
FSL.ScheduleService.schedule(
    saId, policyId, best.Resource.Id, best.Interval_Start__c, best.Interval_End__c
);
```

**Detection hint:** Any code that accesses `slots[0]` or iterates `slots` without a preceding `isEmpty()` or size check after a `GetSlots()` call.

---

## Anti-Pattern 6: Calling OAAS Without License or Feature Guard

**What the LLM generates:**

```apex
public static void triggerOptimization(Id territoryId, Id policyId) {
    String jobId = FSL.OAAS.inDay(territoryId, policyId, startDt, endDt, false);
    // No license check
}
```

**Why it happens:** LLMs generate direct API calls without considering that OAAS requires a separately licensed add-on (Enhanced Scheduling and Optimization). The constraint is a business/licensing rule rather than an API signature rule, so LLMs do not infer it from the method signature.

**Correct pattern:**

```apex
public static void triggerOptimization(Id territoryId, Id policyId) {
    // Gate on a custom permission or custom metadata flag that tracks add-on availability
    if (!FeatureManagement.checkPermission('FSL_Enhanced_Optimization_Enabled')) {
        throw new UnsupportedOperationException(
            'Enhanced Scheduling and Optimization add-on is required for OAAS.');
    }
    String jobId = FSL.OAAS.inDay(territoryId, policyId, startDt, endDt, false);
}
```

**Detection hint:** Any `FSL.OAAS.` method call that is not preceded by a permission check, feature flag check, or try/catch that handles the managed-package license exception.
