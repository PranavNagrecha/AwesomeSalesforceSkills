# Gotchas — FSL Apex Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Uncommitted DML Before FSL Callout

**What happens:** `FSL.AppointmentBookingService.GetSlots()` and `FSL.ScheduleService.schedule()` both make internal HTTP callouts to the FSL routing engine (SLR or P2P) to calculate travel time. The platform enforces that no callout can be made after uncommitted DML in the same transaction. Calling either method after any `insert`, `update`, `upsert`, or `delete` statement that has not been committed throws:

> `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out`

**When it occurs:** Any time GetSlots or schedule() is invoked in the same transaction as a preceding DML operation — including trigger contexts (before/after insert/update), invocable actions that insert records, or Apex called from Flow with DML earlier in the transaction.

**How to avoid:** Always split the DML and the FSL API call into separate Apex transactions. Use a Queueable (implement `Database.AllowsCallouts`) for single-record scenarios or a Batch with `batchSize=1` for bulk scenarios. The FSL method must be the first — and ideally only — significant operation in its transaction.

---

## Gotcha 2: Missing ServiceTerritory on ServiceAppointment

**What happens:** `FSL.ScheduleService.schedule()` requires the ServiceAppointment to have a `ServiceTerritoryId` populated. If the field is null, the call throws a managed-package runtime exception. The error message from the FSL package is not always transparent; it may surface as a generic `FSL.ScheduleService.InvalidParameterException` or a non-descriptive exception from the managed package internals, making the root cause hard to identify without knowing this requirement.

**When it occurs:** Whenever a ServiceAppointment is created without explicitly setting `ServiceTerritoryId`, or when it is set to null by an automation rule, or when a Work Order's territory is not inherited by the SA.

**How to avoid:** Before calling `schedule()`, always assert that the ServiceAppointment's `ServiceTerritoryId` is non-null. Fail fast with a meaningful error rather than letting the FSL exception propagate. Also confirm that the ServiceTerritory is active and that the referenced ServiceResource belongs to that territory.

---

## Gotcha 3: Batch Size Must Be Exactly 1 for FSL Scheduling

**What happens:** When using `Database.Batchable` to call `FSL.ScheduleService.schedule()` or `GetSlots()`, setting `batchSize` to any value greater than 1 causes the second record's FSL call to fail with the uncommitted work exception. The first record's routing callout completes and leaves uncommitted state in the transaction; the second record's call is then blocked.

**When it occurs:** Any bulk FSL scheduling batch where the developer uses the default batch size (200) or any value > 1. This is a common oversight because most Apex batch jobs perform better with larger chunk sizes.

**How to avoid:** Always invoke the batch with an explicit size of 1: `Database.executeBatch(new MyScheduleBatch(), 1)`. Document this requirement as a comment in the batch class itself so future maintainers do not "optimize" the batch size and break it.

---

## Gotcha 4: OAAS Throws at Runtime Without the Enhanced Scheduling Add-On

**What happens:** Calling any `FSL.OAAS` method (`FSL.OAAS.optimizeBySchedulingPolicy()`, `FSL.OAAS.inDay()`, etc.) in an org without the Enhanced Scheduling and Optimization add-on license throws a managed-package exception at runtime. This is not a compile-time error and will not surface in a sandbox that has the add-on but a production org that does not — or vice versa.

**When it occurs:** Whenever OAAS methods are called in an org where the add-on is not activated, or where the FSL managed package version predates OAAS availability.

**How to avoid:** Gate OAAS calls with an explicit check against org license or a custom permission/feature flag. For cross-environment deployment safety, use dynamic Apex (`Type.forName('FSL.OAAS')`) or a custom metadata flag rather than hard-coding OAAS calls in always-executed paths.

---

## Gotcha 5: GetSlots Returns Empty List When No Resources Available

**What happens:** `FSL.AppointmentBookingService.GetSlots()` returns an empty `List<FSL.AppointmentBookingSlot>` — not null — when no available time slots are found. Code that does not check for an empty list before accessing `slots[0]` throws `System.ListException: List index out of bounds: 0`.

**When it occurs:** When no service resources are available in the ServiceTerritory during the scheduling window, when the scheduling policy's work rules block all candidate slots, or when the appointment's earliest start and due date window is too narrow.

**How to avoid:** Always check `if (slots != null && !slots.isEmpty())` before accessing any slot element. Log or surface a meaningful business message (e.g., "No available technicians in the next 7 days") rather than allowing the exception to propagate. Consider notifying dispatchers via Platform Events or a status field update when no slots are returned.

---

## Gotcha 6: @future Cannot Be Called From Batch Context

**What happens:** Using a `@future(callout=true)` method as the transaction-splitting mechanism fails when the calling code is itself inside a `Database.Batchable` execute method. Salesforce does not permit `@future` calls from batch Apex. The error is `System.AsyncException: Future method cannot be called from a batch class`.

**When it occurs:** When a developer tries to use `@future` for FSL scheduling inside a batch, thinking it follows the same pattern as in trigger contexts.

**How to avoid:** Use `System.enqueueJob(new FSLBookingQueueable(...))` inside batch `execute()` instead of `@future`. Queueables can be enqueued from batch context (with the restriction that only one Queueable can be enqueued per batch execute invocation). Alternatively, restructure so the batch itself calls the FSL methods directly with batchSize=1.
