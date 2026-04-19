# Gotchas — Apex Transaction Finalizers

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Finalizer Does Not Run on Aborted Jobs

**What happens:** If a parent Queueable is terminated by calling `System.abortJob(jobId)`, the platform skips the Finalizer entirely. No callback fires, no error is raised — the Finalizer registration is silently discarded.

**When it occurs:** Any time an admin or another Apex class calls `System.abortJob()` on the parent Queueable's `AsyncApexJob` ID while the job is still queued or running. This is common during deployments or emergency queue drains.

**How to avoid:** Do not rely on a Finalizer for abort-path cleanup. If abort-path behavior is required (e.g., releasing a lock, marking a record as "needs reprocessing"), implement a separate monitoring Schedulable that queries `AsyncApexJob WHERE Status = 'Aborted'` and handles cleanup explicitly.

---

## Gotcha 2: Cannot Attach Another Finalizer from Within a Finalizer

**What happens:** Calling `System.attachFinalizer()` inside a Finalizer's own `execute()` method throws `System.AsyncException: Finalizer cannot attach another finalizer`. The exception is swallowed by the platform — no second callback fires, and the failure may be invisible unless you check `ApexLog`.

**When it occurs:** Any attempt to nest Finalizer callbacks, chain guaranteed cleanups, or create a "Finalizer for the Finalizer" pattern.

**How to avoid:** To chain guaranteed behavior, use the single allowed `System.enqueueJob()` slot to enqueue a new Queueable, and attach a new Finalizer inside *that* Queueable's `execute()` method. The chain is: `Queueable A → Finalizer A → enqueues Queueable B → Finalizer B → ...`.

---

## Gotcha 3: Finalizer Runs in a Separate Transaction — Parent State Is Inaccessible

**What happens:** The Finalizer's `execute()` starts with a completely clean Apex transaction. Instance variables set in the parent Queueable's `execute()` method are not available. If the parent threw an exception, all of its DML is rolled back and those records do not exist in the database when the Finalizer runs.

**When it occurs:** Practitioners assume the Finalizer can access the parent's local variables or partially-committed records, then encounter `NullPointerException` or stale query results.

**How to avoid:** Pass all context the Finalizer will need (record IDs, payload snapshots, retry count) through the Finalizer's constructor at the time of `System.attachFinalizer()`. Query for records from the database in the Finalizer if needed, but remember the parent's DML was rolled back — query the pre-failure state.

---

## Gotcha 4: Only One `System.enqueueJob()` Call Is Allowed

**What happens:** A Finalizer that calls `System.enqueueJob()` more than once throws `System.AsyncException` on the second call. This terminates the Finalizer with an unhandled exception (swallowed silently), potentially leaving neither the retry job nor the logging job enqueued.

**When it occurs:** When a Finalizer tries to both log a failure (by enqueuing a logging job) and retry the original work (by enqueuing the retry job) as two separate enqueue calls.

**How to avoid:** Perform logging directly via DML inside the Finalizer (it has a full DML budget), and use the single enqueue slot only for the retry or compensation job. If you need the logging to be async, combine retry and logging into a single Queueable class and enqueue that one combined job.
