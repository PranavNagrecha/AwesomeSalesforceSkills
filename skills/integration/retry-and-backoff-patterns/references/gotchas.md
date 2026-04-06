# Gotchas — Retry and Backoff Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when implementing retry logic for Apex callouts.

## Gotcha 1: DML Before Callout Causes "Callout After Uncommitted Work" Exception

**What happens:** If you update a status field or insert a log record before issuing `Http.send()` in the same transaction, Apex throws `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out.` This silently prevents any retry logic from executing.

**When it occurs:** Any time a developer adds logging, status updates, or retry counter increments before the `Http.send()` call inside an `execute()` method. Common pattern: updating `Retry_Count__c` on the driving record before the callout attempt.

**How to avoid:** Always perform DML after the callout block completes (success or failure). The Queueable `execute()` method allows callouts AND DML, but callouts must come first in the execution flow. Move all `insert`/`update` operations to after the `try/catch` block that wraps the callout.

---

## Gotcha 2: Re-Enqueue Does Not Guarantee Any Specific Delay

**What happens:** `System.enqueueJob()` places the job on the async Apex queue. The platform schedules it for the next available worker thread — this may be seconds or several minutes later depending on org load. There is no guarantee that a job enqueued with a "2-second backoff" will actually wait 2 seconds.

**When it occurs:** Any time a developer communicates retry timing to stakeholders as precise ("it will retry in 10 seconds") or writes tests that assume deterministic retry intervals.

**How to avoid:** Document the retry delay as approximate and log the calculated delay value for observability, but do not design dependent systems that require precise retry timing. If exact timing is critical, consider Scheduled Apex (which has a 1-minute minimum interval, not suitable for short retries) or a native Outbound Messaging retry approach.

---

## Gotcha 3: Daily Async Apex Limit Is Shared Across All Queueable Jobs

**What happens:** Salesforce allows 250,000 Queueable executions per 24-hour rolling window for most orgs (the exact limit scales with user licenses). A broken external endpoint with no circuit breaker can exhaust this budget within hours, blocking all other background Queueable processing (data sync, nightly jobs, notifications).

**When it occurs:** When a high-volume integration fails (e.g., hundreds of orders failing per minute) and the retry chain re-enqueues up to `maxRetries` times for each record without a circuit breaker halting new attempts.

**How to avoid:** The `maxRetries` cap is a mandatory guard. The circuit breaker pattern using Custom Metadata provides a secondary protection layer. Monitor the async limit using the `AsyncApexJob` object and set up a threshold alert before the limit is approached.

---

## Gotcha 4: 50-Enqueue-Per-Transaction Limit Blocks Bulk Retry Scenarios

**What happens:** `System.enqueueJob()` can be called at most 50 times per transaction. A Batch Apex `execute()` method or a trigger processing 200 records that all fail and each try to enqueue a retry job will hit `System.LimitException: Too many queueable jobs added to the queue: 50`.

**When it occurs:** When retry logic is triggered from Batch Apex `execute()`, or when a trigger tries to enqueue one retry job per failing record in a bulk DML operation.

**How to avoid:** Design retry jobs to re-enqueue themselves (1 enqueue per job execution), not to fan out from a parent. In Batch Apex, collect failed record Ids and enqueue a single retry coordinator job that processes them sequentially.

---

## Gotcha 5: Outbound Messages and Platform Events Have Native Retry — Don't Double-Retry

**What happens:** Developers add Apex retry logic on top of Outbound Messages or Platform Event subscribers, resulting in double-processing when the native platform retry also fires. Outbound Messages automatically retry for up to 24 hours at increasing intervals if the endpoint returns a non-200 response. Platform Events can be replayed for up to 3 days via the `ReplayId` mechanism.

**When it occurs:** When a team migrates from Apex callouts to Outbound Messages but copies existing Apex retry scaffolding without removing it, or when a Platform Event trigger fires from a subscriber that has its own retry queue.

**How to avoid:** If using Outbound Messages or Platform Events as the delivery mechanism, do not add Apex retry logic. Document which retry mechanism owns each integration path. Apex callout retry is only for direct `Http.send()` callouts from Queueable or Batch context.
