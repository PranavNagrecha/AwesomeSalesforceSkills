# Gotchas — FSL Scheduling API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: GetSlots + ArrivalWindow DML + schedule() Must Span Two Transactions

**What happens:** Calling `FSL.AppointmentBookingService.GetSlots()`, then updating `ArrivalWindowStart`/`ArrivalWindowEnd` with DML, then calling `FSL.ScheduleService.schedule()` in a single Apex transaction throws `System.CalloutException: You have uncommitted work pending`.

**When it occurs:** Any time a developer implements the full booking flow (retrieve slots → update arrival window → hard assign) in a single @AuraEnabled method, Queueable, or trigger execution.

**How to avoid:** Split into two transactions. Transaction 1: GetSlots (callout only, no DML). Transaction 2: DML on ArrivalWindow fields, then schedule(). Pass slot data between transactions via a custom object, platform cache, or back through the calling component.

---

## Gotcha 2: schedule() Returns Null When No Resource is Available

**What happens:** `FSL.ScheduleService.schedule()` returns `null` — not a thrown exception — when the scheduling policy finds no available resource matching the SA's requirements. Code that only uses try/catch will treat null as success and silently leave the SA unscheduled.

**When it occurs:** Any scheduling call where resource availability is limited, work type requirements are restrictive, or territory coverage gaps exist.

**How to avoid:** Always check `if (result == null)` immediately after `schedule()`. Log or store the failure state in a custom object. Do not assume a non-exception return means success.

---

## Gotcha 3: Batch Apex Size > 1 Causes Callout Limit Failures

**What happens:** Using `Database.executeBatch(job, N)` where N > 1 causes `System.LimitException: Too many callouts` if more than 100 FSL scheduling calls are attempted, or produces partial transaction failures with data inconsistency between Apex state and the FSL microservice.

**When it occurs:** Bulk scheduling implementations that use a default batch size (200) or any size > 1 without testing at full volume.

**How to avoid:** Always use `Database.executeBatch(new BulkScheduler(), 1)`. One record per execute() ensures callout isolation and clean failure handling.

---

## Gotcha 4: ESO Enabled Per Territory — Not a Global Switch

**What happens:** Enhanced Scheduling and Optimization (ESO) must be adopted territory-by-territory in Setup. Once enabled for a territory, it uses ESO exclusively with no fallback to the legacy engine. OAAS operation limits for ESO differ from legacy limits.

**When it occurs:** Orgs that partially adopted ESO will have different scheduling behavior and limits depending on which territory a SA belongs to. Developers who test with one territory and deploy to another may see unexpected failures.

**How to avoid:** Before any OAAS implementation, query which territories have ESO enabled. Check current ESO operation limits in the Spring '26 release notes. Plan for territory-aware error handling.

---

## Gotcha 5: GradeSlotsService Requires Unmodified Slots from GetSlots

**What happens:** Passing custom-constructed or modified `FSL.Scheduling.TimeSlot` objects to `FSL.GradeSlotsService.GradeSlots()` produces null scores or a `NullPointerException` because the TimeSlot objects contain internal state set by GetSlots that GradeSlots depends on.

**When it occurs:** Developers try to filter or sort slots before grading, or construct synthetic slots from stored data.

**How to avoid:** Pass GetSlots output directly to GradeSlots without modification. If filtering is needed, filter after grading, not before.

---

## Gotcha 6: OAAS Global Optimization Has a 2-Hour Hard Timeout

**What happens:** Global optimization jobs that run longer than 2 hours are silently cancelled by the server. No exception is thrown. The FSL optimization job record shows a cancelled status, but the submitting Apex code has already completed normally.

**When it occurs:** Large territory optimization runs with more than 50 resources or more than 1,000 SAs per day horizon.

**How to avoid:** Keep territories under the recommended 50 resource / 1,000 SA limit. Monitor FSL optimization job records with a scheduled report or Flow. Run territory-by-territory rather than submitting concurrent global jobs.
