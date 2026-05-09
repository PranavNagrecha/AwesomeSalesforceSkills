# Gotchas — Scheduled Apex Failure Detection And Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Uncaught exceptions in async `execute()` do not email anyone

**What happens:** When a Schedulable, Batchable, Queueable, or `@future` method throws an uncaught exception, Salesforce records the exception on the corresponding `AsyncApexJob` row's `ExtendedStatus` field and writes it to the debug log — but it does *not* send an unhandled-exception email to the user who scheduled the job, nor to addresses in Setup → Apex Exception Email. That email mechanism is for *synchronous* Apex only.

**When it occurs:** Every silent batch failure traces back to this. Teams who learned Apex from synchronous patterns assume the email path covers async; it does not.

**How to avoid:** Either (a) wrap the body in try-catch and explicitly write to a log + send your own notification, or (b) implement `Database.RaisesPlatformEvents` on Batch classes and subscribe to `BatchApexErrorEvent`, or (c) ship an `AsyncApexJob` watcher schedule. In practice, ship all three layers — they cover different failure modes.

---

## Gotcha 2: `Database.RaisesPlatformEvents` only applies to Batch Apex

**What happens:** `Database.RaisesPlatformEvents` is a marker interface on `Database.Batchable` classes only. Implementing it (or trying to) on a `Schedulable`, `Queueable`, or `@future` class has no effect — the platform does not publish `BatchApexErrorEvent` for those job types regardless of annotation. Queueable / Future / Schedulable failures must be caught manually or detected via `AsyncApexJob` polling.

**When it occurs:** Engineers see "Salesforce publishes a platform event on async failures" in a blog post and assume it covers all async work. They convert their Queueables to use `Database.RaisesPlatformEvents` and find no events arriving.

**How to avoid:** Use `BatchApexErrorEvent` only for batch classes. For other async work, rely on in-job try-catch + log and the watcher schedule.

---

## Gotcha 3: A Batch can `Complete` with `NumberOfErrors > 0`

**What happens:** `Database.Batchable.execute(BatchableContext bc, List<SObject> scope)` can catch its own exceptions per record (or the `Database.update(records, false)` partial-success form can drop bad records). The platform increments `AsyncApexJob.NumberOfErrors` for each failed record, but the overall job ends with `Status = 'Completed'`. A SOQL filter of `WHERE Status = 'Failed'` misses these entirely.

**When it occurs:** Most production Batch Apex uses `Database.update(records, false)` (allOrNone = false) to keep one bad record from failing the whole chunk — a good practice for throughput, but it means `Status = 'Completed'` no longer implies success.

**How to avoid:** Watcher SOQL must include `OR (Status = 'Completed' AND NumberOfErrors > 0)`. The watcher in `references/examples.md` Example 3 has this branch.

---

## Gotcha 4: `Database.executeBatch` from a Schedulable can fail to enqueue

**What happens:** When a Schedulable's `execute()` calls `Database.executeBatch(...)`, that call itself can throw. The most common cause is the Apex Flex Queue concurrency cap (5 batch jobs in `Holding`/`Queued`) plus the asynchronous request limit. The schedule fires, the call throws, no `AsyncApexJob` row is ever created for the batch — so nothing to find with `AsyncApexJob` SOQL alone.

**When it occurs:** Quarter-end batch storms, where multiple scheduled launchers fire close together and saturate the queue. The first few succeed; the later ones fail to enqueue.

**How to avoid:** Log a "schedule fired" entry *before* `Database.executeBatch` — see Example 1. The absence of a corresponding "batch enqueued" log entry is the signal that the launch failed. Watchers should also reconcile expected schedules against actual `AsyncApexJob` rows in the same window.

---

## Gotcha 5: A schedule whose Apex class was deleted leaves a dead `CronTrigger`

**What happens:** Deleting (or refactoring with rename) a class that was scheduled does not automatically drop the `CronTrigger` row in some upgrade paths. The schedule appears in Setup → Scheduled Jobs but produces zero `AsyncApexJob` rows. Setup may show error states inconsistently — sometimes the schedule looks healthy.

**When it occurs:** Long-lived orgs with multiple deployment lineages. Especially after package upgrades that rename or remove a previously scheduled class.

**How to avoid:** Watcher should query `CronTrigger` and reconcile `CronJobDetail.Name` against the set of expected schedule names from configuration (Custom Metadata or a hardcoded set in code). Mismatches → log + notify. Note: dropping then re-adding the schedule via System Scheduler is the standard remediation.

---

## Gotcha 6: `BatchApexErrorEvent` subscriber trigger can re-publish or fire multiple times

**What happens:** Platform events with `RaisesPlatformEvents` are published asynchronously and the subscriber trigger may receive duplicate events (the platform's at-least-once delivery model) or fire across multiple replays in some recovery scenarios. A naive subscriber that emails on every event will page operators multiple times for the same failure.

**When it occurs:** Generally low-frequency, but observable when an org goes through a maintenance window or when a batch hits a transient platform error and is retried internally.

**How to avoid:** Always dedupe by `AsyncApexJobId`. Either upsert a log row with `External_Id__c = AsyncApexJobId` and check existence before notifying, or track the event by `EventUuid` + `AsyncApexJobId` in a small custom-object cache. Idempotency is non-optional for any subscriber that sends external notifications.

---

## Gotcha 7: Governor limits in the Schedulable context

**What happens:** A Schedulable's `execute(SchedulableContext sc)` runs in a *synchronous* governor context, not async. Limits are tighter than they are inside a Batch `execute()`: 100 SOQL queries, 150 DML statements, 6 MB heap. A Schedulable that does inventory queries before deciding what to enqueue can OOM unexpectedly.

**When it occurs:** Watcher schedules that try to do too much in their own `execute()` body — querying `AsyncApexJob`, `CronTrigger`, log objects, then publishing notifications and writing to a log object can hit limits in a busy org with thousands of recent async jobs.

**How to avoid:** Keep the watcher's `execute()` body lean. Use `LIMIT N` clauses on every SOQL. Push heavy work (notification publishing across many channels) into a Queueable enqueued from `execute()` so the heavy code runs in async governor context. The watcher schedule itself should query, log, and enqueue — not loop over hundreds of records inline.

---

## Gotcha 8: `ExtendedStatus` is truncated and may be empty

**What happens:** `AsyncApexJob.ExtendedStatus` is limited to about 255 characters and may be empty for some failure types (e.g. when the platform itself aborts the job for governor reasons rather than an Apex throw). Notifications that *only* surface `ExtendedStatus` will sometimes show "First error: Update failed." with no actionable context.

**When it occurs:** Long Apex stack traces, or when failures originate outside Apex (e.g. Salesforce platform internals, governor enforcement before user code runs).

**How to avoid:** When `BatchApexErrorEvent` fires, prefer `evt.Message` and `evt.StackTrace` from the event itself — they are not truncated to 255. For non-batch jobs, the only durable record of the full exception is what your in-job try-catch wrote to the log. This is the strongest argument for try-catch + log even when `BatchApexErrorEvent` is in play.
