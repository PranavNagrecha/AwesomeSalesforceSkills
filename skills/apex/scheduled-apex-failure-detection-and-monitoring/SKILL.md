---
name: scheduled-apex-failure-detection-and-monitoring
description: "Use when nightly batch / scheduled Apex jobs are failing without anyone noticing — covers why uncaught exceptions in `execute()` go to the debug log instead of email, how to query `AsyncApexJob` for `Status`, `NumberOfErrors`, and `ExtendedStatus`, when to implement `Database.RaisesPlatformEvents` so the platform publishes `BatchApexErrorEvent` on uncaught failures, how to subscribe to that event with an Apex trigger and notify operators, and how to layer a custom watcher schedule on top so silent-failure modes (job that never started, scheduled class deleted, queue stuck on `Queued`) still surface. Triggers: 'nightly batch failed at 2am with no notification', 'how do we know if a scheduled apex job is failing', 'BatchApexErrorEvent vs custom retry logic', 'Setup Apex Jobs only shows last 7 days, where else can I look', 'job is stuck in queued status nobody noticed for a week'. NOT for general Apex exception handling patterns (use apex/apex-exception-handling-and-logging), NOT for Batch Apex authoring or chunking strategy (use apex/batch-apex-design), NOT for Setup → Apex Jobs UI walkthrough as an admin task (use admin/batch-job-scheduling-and-monitoring), NOT for retry logic itself (use apex/scheduled-apex-retry-patterns once authored)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "nightly batch job failed at 2am and nobody got notified"
  - "how do I know if my scheduled apex is silently failing"
  - "Setup Apex Jobs UI only shows the last 7 days, what else is available"
  - "job has been stuck in Queued for hours, why didn't anyone notice"
  - "do we need BatchApexErrorEvent or is try-catch enough"
  - "scheduled class was deleted but the schedule keeps firing somehow"
  - "where do I see the ExtendedStatus for a failed AsyncApexJob"
  - "how to send an email or Slack alert when a batch fails"
tags:
  - scheduled-apex-failure-detection-and-monitoring
  - asyncapexjob
  - batchapexerrorevent
  - raisesplatformevents
  - operational-excellence
  - reliability
  - monitoring
inputs:
  - "Symptom: silent failure, stuck job, missed batch run, or all of the above"
  - "Inventory of scheduled jobs (Apex classes implementing Schedulable / Batchable)"
  - "Whether the org has Event Monitoring (controls whether ApexExecution log files are available)"
  - "Notification channel target (email, Custom Notification, Slack via outbound HTTP, platform event subscriber)"
outputs:
  - "Failure detection design: which mechanism (`BatchApexErrorEvent`, `AsyncApexJob` watcher, try-catch + logger) covers which failure mode"
  - "BatchApexErrorEvent subscriber Apex trigger pattern (with idempotent recipient resolution)"
  - "Watcher schedule that polls AsyncApexJob and publishes failure notifications"
  - "Operator notification recipe (email + Custom Notification fallback)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Scheduled Apex Failure Detection And Monitoring

Activate this skill when a Salesforce team needs to *know* their scheduled and batch Apex jobs failed — not just hope they did. The default platform behavior swallows uncaught exceptions in async execution into the debug log, with no email, no record, and no signal to the system of record. This skill closes that gap with three layered mechanisms: in-job try-catch logging, the `BatchApexErrorEvent` platform event for batch-class crashes, and a custom `AsyncApexJob` watcher schedule for everything else (stuck jobs, never-fired schedules, deleted classes).

---

## Before Starting

Gather this context before designing failure detection:

- **What kind of async work is failing.** Three different things commonly get called "scheduled Apex" and each has a different failure surface:
  - A `Schedulable` class invoked by `System.schedule(...)` directly. Uncaught exception in `execute(SchedulableContext)` is logged to the debug log only.
  - A `Schedulable` whose `execute()` calls `Database.executeBatch(new MyBatch(), N)` to enqueue a batch. The schedule fires fine, but the call to `executeBatch` itself can fail (e.g. concurrency limit, governor in the scheduler context), and the batch never runs.
  - A `Database.Batchable` job in flight. Uncaught exception in `start()`, `execute()`, or `finish()` aborts the *current chunk* and is recorded on `AsyncApexJob` — but only if the platform sees the exception. With `Database.RaisesPlatformEvents` it also publishes `BatchApexErrorEvent`.
- **Who owns "the system noticed."** Most orgs assume Setup → Apex Jobs is the source of truth. It only shows the last 7 days, only shows what made it onto the queue, and is rarely checked. If the failure path depends on a human opening that page, the failure path is broken.
- **Whether Event Monitoring is licensed.** With Event Monitoring, the `ApexExecution` event log file (`EVENT_TYPE = ApexExecution`) records every Apex execution including async, with `STATUS` and `MESSAGE` fields useful for reconciliation. Without it, `AsyncApexJob` SOQL is the primary signal.
- **Existing logging substrate.** If the org already has a custom log object (commonly `Application_Log__c` or similar) populated by an `ApplicationLogger`, the failure notifications should write there too. If not, decide *now* whether you're shipping a logger as part of this work or piggybacking on Custom Notifications + email.

---

## Core Concepts

### Concept 1 — Why scheduled Apex fails silently by default

Three behaviors compound into the silent-failure mode:

1. **Uncaught exceptions in async `execute()` do not email the user who scheduled the job.** Synchronous Apex sends an unhandled-exception email to the user and to addresses configured in Setup → Apex Exception Email. *Async* Apex (Schedulable, Batch, Queueable, `@future`) does not — the exception is recorded on the `AsyncApexJob` row (in `ExtendedStatus`) and written to the debug log, but no email is sent unless you handle the exception yourself or subscribe to `BatchApexErrorEvent`. This is the single biggest gap teams discover after a quarter-end batch fails on a Sunday.
2. **Setup → Apex Jobs is a 7-day rolling window.** The page renders from `AsyncApexJob`, which is retained for 7 days for completed entries, longer for failed/aborted, but the UI filter typically defaults to recent entries and does not surface "schedule fired but enqueue failed" cleanly.
3. **A scheduled job whose underlying Apex class is deleted continues to occupy a `CronTrigger` slot but cannot fire.** No email, no warning. The job appears in `CronTrigger` but produces no `AsyncApexJob` rows. The first symptom is almost always "we noticed last quarter's data wasn't being refreshed."

The design implication: any failure-detection design must cover (a) caught and logged exceptions, (b) uncaught exceptions during batch execution, and (c) jobs that should have run but didn't.

### Concept 2 — `AsyncApexJob` is the queryable record for every async execution

Every async Apex execution (Future, Queueable, Batch, Scheduled) creates an `AsyncApexJob` row. The relevant fields for monitoring are:

- **`Status`** — values are `Queued`, `Preparing`, `Processing`, `Aborted`, `Completed`, `Failed`, `Holding`. `Failed` is what you check; `Aborted` is operator-initiated; `Holding` indicates Flex Queue throttling.
- **`NumberOfErrors`** — count of chunks that errored within a Batch job. A Batch can `Complete` with `NumberOfErrors > 0` — completion does not imply success.
- **`ExtendedStatus`** — short description of the most recent error (truncated to ~255 chars). This is what surfaces in Setup → Apex Jobs.
- **`JobType`** — `BatchApex`, `BatchApexWorker`, `Queueable`, `Future`, `ScheduledApex`, `ApexToken`, `SharingRecalculation`, etc. Filter the watcher to job types you care about.
- **`ApexClassId`** — FK to `ApexClass.Id`. Resolve via `[SELECT Name FROM ApexClass WHERE Id = :id]` to get the class name in the alert.
- **`MethodName`**, **`CompletedDate`**, **`CreatedDate`** — timing context for "stuck job" detection (e.g. `Status = 'Queued' AND CreatedDate < :Datetime.now().addHours(-2)`).

A baseline failure-detection SOQL is therefore:

```apex
SELECT Id, JobType, ApexClassId, ApexClass.Name, Status, NumberOfErrors,
       ExtendedStatus, CompletedDate, CreatedDate
FROM AsyncApexJob
WHERE Status IN ('Failed', 'Aborted')
  AND CompletedDate >= :Datetime.now().addHours(-25)
ORDER BY CompletedDate DESC
```

The 25-hour window covers a daily cadence with overlap for clock skew; tighten or widen based on cadence.

### Concept 3 — `BatchApexErrorEvent` is the platform's signal for uncaught batch failures

`BatchApexErrorEvent` is a standard Platform Event that the platform publishes automatically whenever a Batch Apex execution throws an uncaught exception — but only if the batch class is annotated with `Database.RaisesPlatformEvents`. The event carries the failing job's `AsyncApexJobId`, the exception type and message, the stack trace, the JSON-serialized job scope (so a subscriber can re-enqueue the failed batch on a smaller scope), and `Phase` (which lifecycle method threw — `START`, `EXECUTE`, or `FINISH`).

To activate it:

1. Implement `Database.RaisesPlatformEvents` on your batch class:
   ```apex
   public class NightlyAccountRollup
     implements Database.Batchable<SObject>, Database.RaisesPlatformEvents {
       // start, execute, finish
   }
   ```
2. Subscribe with an Apex trigger on `BatchApexErrorEvent`:
   ```apex
   trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
     for (BatchApexErrorEvent evt : Trigger.new) {
       // log, notify, optionally re-enqueue
     }
   }
   ```

Two important constraints:
- The event covers **uncaught** exceptions only. Anything you `try { ... } catch(Exception e) { }` away never publishes.
- It covers **Batch Apex only**. Queueable, Schedulable, `@future` failures do not produce `BatchApexErrorEvent`. Those need either in-job try-catch logging or the `AsyncApexJob` watcher.

### Concept 4 — The watcher schedule pattern fills the gaps

A *watcher* is a separate scheduled Apex class — typically running every 15 minutes or hourly — whose only job is to query `AsyncApexJob` and `CronTrigger` for failure or stuck conditions and notify operators. This catches the failure modes neither try-catch nor `BatchApexErrorEvent` cover:

- **Job that never enqueued.** A `Schedulable` whose `execute()` threw before `Database.executeBatch` was called. The schedule fires (`CronTrigger.PreviousFireTime` advances), but no Batch `AsyncApexJob` row appears for that window.
- **Job stuck in `Queued`.** Concurrency limits or Flex Queue saturation can leave a job in `Status = 'Queued'` for hours. With no `Failed` status, neither try-catch nor `BatchApexErrorEvent` triggers.
- **Job that completed with errors but didn't throw.** A Batch Apex `execute()` that catches its own exceptions and increments a counter — `Status` ends as `Completed` but `NumberOfErrors > 0`. Watchers should treat these as failures.
- **Schedule that no longer maps to a class.** `CronTrigger` row exists, but the underlying class was deleted. The watcher reads `CronTrigger.CronJobDetail.Name` and reconciles against expected schedules.

The watcher is itself scheduled Apex, so the same considerations apply: it must `try-catch` its own execution, write to a log, and ideally have a *second*, lighter-weight watcher (e.g. an external uptime ping) confirming the watcher itself ran. This is the limit of in-org monitoring — at the boundary you need an external observer.

---

## Recommended Workflow

1. **Inventory existing scheduled jobs and classify them.** Query `CronTrigger` for active schedules, cross-reference against `ApexClass`, and bucket each into Schedulable-only, Schedulable-launching-Batch, or pure Batch invoked elsewhere. Run `scripts/check_scheduled_apex_failure_detection_and_monitoring.py` against the SFDX project to flag classes that schedule themselves without exception handling.
2. **Add try-catch + structured logging to every `execute()` body.** Whether `Schedulable` or `Batchable`, wrap the body in try-catch and write to a log object on exception. The catch must re-throw only if you *want* the platform to mark the job `Failed` (and, for batch classes implementing `Database.RaisesPlatformEvents`, publish `BatchApexErrorEvent`). For Schedulable classes that launch batches, log a "schedule fired" entry before `executeBatch` so a missing entry signals a pre-enqueue failure.
3. **Add `Database.RaisesPlatformEvents` to every business-critical batch class.** Audit each `Database.Batchable` class. For ones whose failure has user impact, add the marker interface and ship a `BatchApexErrorEventTrigger` that logs + notifies. See `references/examples.md` Example 2.
4. **Build the `AsyncApexJob` watcher schedule.** A separate Schedulable class that queries `AsyncApexJob` for `Status IN ('Failed','Aborted')` in the last hour, plus stuck `Queued`/`Holding` jobs older than your SLA, plus `Completed` jobs with `NumberOfErrors > 0`. For each finding, log + notify. See Example 3.
5. **Pick a notification channel and make it idempotent.** Email Alerts work for low volume but are easy to ignore. Custom Notifications (bell icon) are durable but have no Slack/external surface. For ops, a Platform Event subscribed by a middleware bridge to Slack/Pagerduty is the most reliable. Whichever you pick, deduplicate by `AsyncApexJobId` so a watcher running every 15 minutes does not page operators five times for the same failure.
6. **Document the failure runbook alongside the alert.** Each alert payload should include the `AsyncApexJob.Id`, class name, `ExtendedStatus`, and a link to a runbook describing how to re-run, what side effects to expect, and who to escalate to. Notifications without runbooks become noise within two weeks.
7. **Verify by injecting a controlled failure.** In a sandbox, deploy a batch that throws on a known input, schedule it, and confirm the alert fires through every channel (log, `BatchApexErrorEvent` subscriber, watcher) within the expected window. Fail open — assume the watcher itself can fail and have at least one external check.

---

## Related Skills

- `apex/apex-exception-handling-and-logging` — general Apex exception patterns; the structured logger you call from `execute()` lives there
- `apex/batch-apex-design` — chunking, scope size, and stateful design for Batch Apex
- `admin/batch-job-scheduling-and-monitoring` — admin-facing monitoring via Setup → Apex Jobs and Scheduled Jobs UI
- `architect/org-limits-monitoring` — broader org-level limits monitoring (Flex Queue saturation, async limits) which also surfaces in this domain
- `apex/apex-custom-notifications-from-apex` — how to publish a Custom Notification from an Apex trigger or class, for the bell-icon alert path
