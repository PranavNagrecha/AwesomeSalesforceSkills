---
name: batch-job-scheduling-and-monitoring
description: "Use when monitoring, diagnosing, or managing Batch Apex, Scheduled Apex, Queueable, and Flow scheduled jobs: Setup > Apex Jobs, AsyncApexJob queries, concurrent limits, failure detection, and notification patterns. NOT for writing the Batch or Schedulable class itself — use apex/batch-apex-patterns or apex/apex-scheduled-jobs. NOT for BatchApexErrorEvent alerting in code — use apex/scheduled-apex-failure-detection-and-monitoring. Trigger keywords: Setup > Scheduled Jobs, Apex Flex Queue, CronTrigger, CronJobDetail, FlowInterview, System.abortJob, System.schedule, CRON expression, Holding status, BLOCKED state, reschedule after sandbox refresh, scheduled job runbook."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I check if my batch Apex job is still running"
  - "batch job failed and I need to see the error in Salesforce"
  - "how many batch jobs can run at the same time in a Salesforce org"
  - "scheduled Apex job is not firing at the expected time"
  - "how to get notified when a batch job fails"
  - "how do I check if my batch Apex job is stuck or failed"
  - "abort a scheduled Apex job in Salesforce"
  - "batch job stuck in Holding status in the Apex flex queue"
  - "deploy fails with this schedulable class has jobs pending or in progress"
  - "find scheduled jobs whose Apex class no longer exists"
  - "scheduled jobs missing after a sandbox refresh"
  - "query CronTrigger for the next fire time of a scheduled job"
tags:
  - batch-apex
  - scheduled-jobs
  - apex-jobs
  - monitoring
  - operational-excellence
inputs:
  - "Job type to monitor: Batch Apex, Scheduled Apex, Queueable, or Flow scheduled job"
  - "Whether the issue is a failed job, a delayed job, or a missing notification"
outputs:
  - "SOQL query to retrieve AsyncApexJob status for the target job"
  - "Explanation of the job's current status and relevant limits"
  - "Failure notification pattern if not already implemented"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Batch Job Scheduling And Monitoring

This skill activates when a Salesforce admin, developer, or operator needs to monitor, diagnose, or manage async job execution in an org. It covers the Setup > Apex Jobs and Scheduled Jobs views, direct SOQL queries against `AsyncApexJob`, concurrent job limits, failure notification patterns, and the difference between how Batch Apex and Flow scheduled jobs surface in monitoring.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the job type. `AsyncApexJob.JobType` is a restricted picklist: `ApexToken`, `BatchApex`, `BatchApexWorker`, `Future`, `Queueable`, `ScheduledApex`, `SharingRecalculation`, `TestRequest`, `TestWorker` (Object Reference, AsyncApexJob → JobType). **There is no `ScheduledFlow` value on `AsyncApexJob`** — a scheduled Flow surfaces on `CronJobDetail` as `JobType = '6'` instead.
- Determine whether the issue is a job that is stuck/running, a job that failed silently, or a job that never fired. The third is the hardest, because a job that never fired leaves no `AsyncApexJob` row at all — only `CronTrigger` can prove the absence.
- Note the org's concurrent Batch Apex limit: 5 jobs queued or active concurrently, with up to 100 more held in the Apex flex queue in `Holding` status (App Limits cheat sheet L316–319). This is the most common cause of jobs staying in "Queued" status without progressing.
- Confirm the person running the diagnosis can actually read the data. `AsyncApexJob` requires **View Setup and Configuration** when Apex is not running in system mode (Object Reference, AsyncApexJob → Special Access Rules).

---

## Questions to Ask Before Configuring

Ask these before scheduling anything or before declaring a job "fine"; the answers decide the runbook, and an agent that skips them ships a schedule that survives exactly until the next deploy.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who gets paged when this job fails, and is that a mailbox we control?" | The platform emails full error detail to the last user who *modified the batch class*, not to an ops rota (gotcha 5) | A named owner and an alert channel, recorded in the scheduling registry |
| "How long does this job take today, and what is the interval between runs?" | Runtime creeping past the interval puts the CronTrigger in `BLOCKED` and the window is silently missed (gotcha 7) | A `max_runtime_minutes` and a runtime `window` per job |
| "Which time zone is the schedule anchored to — the scheduling user's or the org's?" | `System.schedule()` uses the running user's timezone; a scheduled Flow's `startTime` uses the org default (gotcha 8) | The intended wall-clock time, and a `CronTrigger.TimeZoneSidKey` check after scheduling |
| "How does this schedule get rebuilt in a refreshed sandbox or a new org?" | Schedules are org data — a refresh copies none of them, and no deploy carries them (gotcha 10) | A registry entry with the exact CRON expression, and a reschedule step in the refresh runbook |
| "Does anything else depend on this job finishing first?" | Cron expressions only imply ordering; two jobs 45 minutes apart are not a dependency | A `depends_on` value and a real decision about whether to chain instead |
| "When we next deploy this class, who aborts and re-creates the schedule?" | A live schedule blocks the deploy of its own class and everything that class references (gotcha 6) | A named abort → deploy → reschedule sequence, not a production surprise |
| "Are we filtering on `Status = 'Failed'`?" | `Completed` covers "completed with failures"; `Failed` means a system-level failure only (gotcha 9) | A failure predicate of `Status = 'Failed' OR NumberOfErrors > 0` |

What a proper configuration adds over just scheduling it: the job can be rebuilt from source after a refresh, the person who has to fix it finds out before the business does, and the deploy that changes the class does not fail on the schedule the deploy itself cannot see.

---

## Core Concepts

### Apex Jobs UI vs Scheduled Jobs UI

Salesforce provides two distinct monitoring views:
1. **Setup > Apex Jobs** — shows `AsyncApexJob` records for Batch Apex, Queueable, @future, and Scheduled Apex invocations. Displays status, number of records processed, errors, and completion time.
2. **Setup > Scheduled Jobs** — shows Scheduled Apex definitions (the cron-based schedule) and their next fire time. Also shows Schedule-Triggered Flow Interviews. This view does NOT show the individual Batch Apex executions triggered by a scheduled job — those appear in Apex Jobs.

Flow scheduled jobs (Schedule-Triggered Flow) appear only in Setup > Scheduled Jobs as "Schedule-Triggered Flow Interview". They do NOT appear in Apex Jobs.

### AsyncApexJob as the Query Surface

All Apex async jobs are queryable via SOQL against `AsyncApexJob`. This is the programmatic equivalent of the Apex Jobs UI and is the only way to retrieve historical job data programmatically.

Key fields (Object Reference, AsyncApexJob → Fields):
- `Status` — `Aborted`, `Completed`, `Failed`, `Holding`, `Preparing`, `Processing`, `Queued`. `Holding` applies only to batch jobs in the Apex flex queue.
- `JobType` — restricted picklist; the ones you monitor are `BatchApex`, `BatchApexWorker`, `Future`, `Queueable`, `ScheduledApex`.
- `NumberOfErrors` — "Total number of batches with a failure. A batch is considered transactional." Label is **Failures**.
- `TotalJobItems` / `JobItemsProcessed` — batches in the job and batches done so far. Labels **Total Batches** and **Batches Processed**.
- `CompletedDate` — when the job finished (null if still running)
- `ExtendedStatus` — "a short description of the **first** error". The full detail and any subsequent errors are emailed to the last user who modified the batch class, not to you.
- `ParentJobId` — set on `BatchApexWorker` children of a chunked batch job; the reason job counts inflate.
- `CronTriggerId` — populated for `ScheduledApex` only, API v53.0 and later.

```soql
SELECT Id, ApexClass.Name, Status, NumberOfErrors, TotalJobItems,
       CreatedDate, CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
ORDER BY CreatedDate DESC
LIMIT 20
```

### CronTrigger and CronJobDetail — the Schedule Itself

`AsyncApexJob` records what *ran*. `CronTrigger` records what is *supposed to run*, and it is the only object that can prove a job never fired. `CronJobDetail` carries the job's name and type.

| Field | Object | Why you query it |
|---|---|---|
| `CronExpression` | CronTrigger | The exact expression to re-run `System.schedule()` with after a refresh |
| `State` | CronTrigger | `WAITING`, `ACQUIRED`, `EXECUTING`, `COMPLETE`, `ERROR`, `DELETED`, `PAUSED`, `BLOCKED`, `PAUSED_BLOCKED` |
| `NextFireTime` / `PreviousFireTime` | CronTrigger | Null `NextFireTime` means "not scheduled to run again" — an orphan holding a slot |
| `TimesTriggered` | CronTrigger | Zero on a job that has existed for weeks is the tell |
| `TimeZoneSidKey` | CronTrigger | The timezone actually recorded, which is the scheduling user's, not the org's |
| `OwnerId` | CronTrigger | Who *created* the schedule — rarely the same person as who should be paged |
| `CronJobDetail.Name` | CronJobDetail | The `jobName` passed to `System.schedule()`; your reconciliation key |
| `CronJobDetail.JobType` | CronJobDetail | `1` Data Export, `3` Dashboard Refresh, `4` Reporting Snapshot, `6` Scheduled Flow, `7` Scheduled Apex, `8` Report Run, `9` Batch Job, `A` Reporting Notification |

Neither object is deployable metadata. A schedule is org data; see `references/metadata-examples.md` section 1.

### Concurrent Batch Apex Limit and the Flex Queue

Three separate numbers, all from the App Limits cheat sheet (L313–319):

- **5** batch Apex jobs queued or active concurrently.
- **100** batch Apex jobs in the Apex flex queue in `Holding` status.
- **100** Apex classes scheduled concurrently — **5 in Developer Edition orgs**. This is a different cap from the two above.

- **Holding** — in the flex queue, waiting for the system to move it. Reorder it in **Setup > Apex Flex Queue** or with `System.FlexQueue` methods; otherwise the queue is first-in, first-out.
- **Queued** — already promoted out of the flex queue, waiting for an executor slot.

`Database.executeBatch` throws a `LimitException` when the flex queue is already at 100 — the job is not queued at all (Apex Developer Guide, Holding Batch Jobs in the Apex Flex Queue).

### Scheduled Apex Runs Under Synchronous Limits

The App Limits cheat sheet is explicit: *"Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs"* (L36–37). Batch Apex is the opposite — its per-transaction limits *"are reset for each execution of a batch of records in the execute method"* (L29–30).

This is why the standard shape is a thin `Schedulable` that immediately calls `Database.executeBatch` or `System.enqueueJob`: the `Schedulable.execute()` body itself gets synchronous headroom only. See `apex/apex-scheduled-jobs` for the class; `standards/decision-trees/async-selection.md` Q9 covers "runs on a schedule AND re-runnable ad hoc".

### Scheduled Apex Does Not Retry on Failure

When a Scheduled Apex job fails during execution, the schedule definition is NOT deleted. The scheduler will fire the job again at the next scheduled time. The failed execution is recorded in `AsyncApexJob` with `Status='Failed'`. There is no native automatic retry on immediate failure — the org waits until the next cron window.

---

## Common Patterns

### SOQL Monitoring Dashboard Query

**When to use:** Quickly checking the status of all Batch Apex jobs in the last 24 hours without navigating to Setup.

**How it works:**
```soql
SELECT ApexClass.Name, Status, JobType, NumberOfErrors, TotalJobItems,
       CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE JobType IN ('BatchApex', 'ScheduledApex', 'Queueable')
  AND CreatedDate = LAST_N_HOURS:24
ORDER BY CreatedDate DESC
LIMIT 50
```

Filter to `Status = 'Failed'` to find only failures. Check `ExtendedStatus` for the error message.

### Failure Notification via finish() Method

**When to use:** A Batch Apex job needs to send an alert when it completes with errors — Salesforce does not email on batch failure by default.

**How it works:**
```apex
global class MyBatch implements Database.Batchable<sObject> {
    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Account WHERE ...');
    }
    global void execute(Database.BatchableContext bc, List<Account> scope) {
        // processing logic
    }
    global void finish(Database.BatchableContext bc) {
        AsyncApexJob job = [
            SELECT NumberOfErrors, TotalJobItems, ExtendedStatus
            FROM AsyncApexJob
            WHERE Id = :bc.getJobId()
        ];
        if (job.NumberOfErrors > 0) {
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            mail.setToAddresses(new List<String>{'admin@example.com'});
            mail.setSubject('Batch Job Failed: ' + job.NumberOfErrors + ' errors');
            mail.setPlainTextBody(
                'Job: MyBatch\nErrors: ' + job.NumberOfErrors +
                '/' + job.TotalJobItems + '\nDetails: ' + job.ExtendedStatus
            );
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{mail});
        }
    }
}
```

**Why not rely on platform notifications:** Salesforce does not send email or create alerts when a batch job fails. The `finish()` method is the only hook available to the developer for failure notification.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Job is stuck in Queued status | Check concurrent job count via SOQL or Apex Jobs UI | May be waiting for a slot (5 concurrent limit) |
| Job shows Status=Failed, or Completed with `NumberOfErrors > 0` | Query `ExtendedStatus` on AsyncApexJob for error detail | `ExtendedStatus` holds the first error only; the rest is emailed to the last user who edited the class |
| Need to abort a running batch job | `Database.executeBatch()` returns the job ID; use `System.abortJob(jobId)` | Only works if job is in Queued/Holding/Processing |
| Flow scheduled job not appearing in Apex Jobs | Check Setup > Scheduled Jobs for "Schedule-Triggered Flow Interview" | Flow jobs do not appear in Apex Jobs |
| Need email notification on batch failure | Implement failure check in `finish()` method using AsyncApexJob query | No native platform notification on batch failure |
| Need to abort a *scheduled* Apex job | `System.abortJob(cronTriggerId)` — an AsyncApexJob Id will not work | The Apex Reference Guide states you can't abort a scheduled Apex job using an AsyncApexJob ID |
| Jobs pile up in `Holding` and one is urgent | `System.FlexQueue.moveJobToFront(jobId)`, or Setup > Apex Flex Queue | Flex queue is FIFO otherwise; the reorder call must be the last statement in the transaction |
| A job's window keeps being missed with no failure | Query `CronTrigger.State` for `BLOCKED` | Two instances never run concurrently; the second attempt blocks instead |
| Concurrent limit exceeded repeatedly | Stagger schedules and shrink runtime windows before escalating | Raising the 5-job concurrency cap is not documented as self-service in the sources cited here — **UNVERIFIED (2026-09-04): whether Salesforce Support will raise the concurrent Batch Apex limit, and for which editions, is not stated in the App Limits cheat sheet, Apex Developer Guide or Apex Reference Guide. Confirm with Support before promising it.** |

---

## Recommended Workflow

1. **Establish which surface owns the answer.** Ran-or-not → `AsyncApexJob`. Supposed-to-run → `CronTrigger` + `CronJobDetail`. Flow interviews → `FlowInterview` and Setup > Scheduled Jobs. Getting this wrong is why "the flow isn't scheduled" reports are usually false — see `references/gotchas.md` gotcha 1.
2. **Run the matching query from `references/metadata-examples.md` section 3** — 3a running/failed, 3c error text, 3d schedules and next fire time, 3e orphans, 3f flex queue order, 3g paused Flow interviews. Always exclude `JobType = 'BatchApexWorker'` from counts, and never filter failures on `Status` alone.
3. **Reconcile against the scheduling registry** (`references/metadata-examples.md` section 5). Registry entries with no matching `CronJobDetail.Name` are jobs that will not run; `CronTrigger` rows with no registry entry are unowned. Lint the file with `python3 scripts/check_batch_job_scheduling_and_monitoring.py --manifest-dir <project>` — it exits 1 on a malformed CRON expression, a duplicate job name, or a missing owner / window / alert channel, and WARNs on overlapping windows for one class.
4. **Act with the right Id and the right tool.** Abort batch/Queueable/future by `AsyncApexJob` Id, scheduled Apex by `CronTrigger` Id; reschedule with `System.schedule(name, cron, new Class())` using the registry's expression; prioritise with `System.FlexQueue`. Snippets in `references/metadata-examples.md` section 4 — log before aborting, because the abort removes the row.
5. **Close the alerting gap, don't just report it.** Pick a recipe from `references/metadata-examples.md` section 6 and deploy the `Async_Job_Operations` permission set (section 2a) so the on-call rota can actually read `AsyncApexJob`. Verify with the SOQL check in section 2, not with a green deploy.
6. **Write the deploy and refresh sequence down.** Abort → deploy → reschedule, driven off the registry, added to the release and sandbox-refresh runbooks (`devops/sandbox-refresh-and-templates`). This is the step that stops the next release failing on a schedule nobody remembered.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Verified job type maps to correct monitoring location (Apex Jobs vs Scheduled Jobs)
- [ ] SOQL query against AsyncApexJob is scoped to the correct JobType and time range
- [ ] ExtendedStatus checked for failed jobs — not just the Status field
- [ ] Concurrent Batch Apex job count confirmed against 5-job limit
- [ ] Batch class finish() method sends notification when NumberOfErrors > 0
- [ ] Scheduled Apex schedule definition confirmed in Scheduled Jobs UI (separate from execution records)
- [ ] `JobType = 'BatchApexWorker'` excluded from any query that counts jobs
- [ ] Failure predicate is `Status = 'Failed' OR NumberOfErrors > 0`, not `Status` alone
- [ ] Every recurring job has a registry entry with an owner, window and alert channel; `scripts/check_batch_job_scheduling_and_monitoring.py` exits 0
- [ ] `CronTrigger.TimeZoneSidKey` matches the intended wall-clock time
- [ ] The reschedule step exists in the deploy runbook and the sandbox-refresh runbook

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Flow scheduled jobs do NOT appear in Setup > Apex Jobs** — Admins looking for a scheduled flow that isn't running check Apex Jobs and see nothing. Flow schedule-triggered interviews only appear in Setup > Scheduled Jobs as "Schedule-Triggered Flow Interview". This is a common source of confusion.
2. **Batch Apex failure does not delete the Scheduled Apex schedule** — If a batch class is invoked by a scheduled Apex and fails, the batch fails but the schedule continues. The next cron window fires another instance. If the failure is caused by a data issue that isn't fixed, the job will keep failing on every scheduled run without any notification (unless `finish()` sends one).
3. **NumberOfErrors counts failed CHUNKS, not failed RECORDS** — For Batch Apex with a scope of 200, a `NumberOfErrors` of 1 means one chunk of up to 200 records failed — not necessarily one record. The actual record-level failure requires reading the exception in `Database.SaveResult[]` in the `execute()` method.
4. **Abort is not instant, and the Id you pass is not interchangeable** — Per the Apex Reference Guide, a job already executing *"is still visible in the job queue"* after abort and *"any code that is in progress will continue to execute until it completes."* Batch, Queueable and @future are aborted by `AsyncApexJob` Id; scheduled Apex only by `CronTrigger` Id. Log the abort before you issue it — the row you were reading goes away.
5. **`Status = 'Completed'` includes runs that failed** — The Apex Developer Guide's batch status table defines `Completed` as *"Job completed with or without failure"*, reserving `Failed` for a system failure. A dashboard filtering on `Status` alone is blind to the ordinary failure mode.
6. **A live schedule blocks the deploy of its own class** — And of every class that class references. The abort → deploy → reschedule order is the guide's own recommendation, which is why the CRON expression belongs in source control.

Full write-ups, with source line ranges, in `references/gotchas.md` (11 gotchas).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AsyncApexJob SOQL query | Parameterized query for job history by type and time range |
| Batch finish() notification snippet | Apex code for failure detection and email notification in finish() |
| Concurrent job count query | SOQL to count currently Processing batch jobs against the 5-job limit |
| Scheduled-jobs registry | YAML inventory of every recurring job: name, class, CRON, owner, window, dependency, max runtime, alert channel |
| Reschedule script | `System.schedule()` calls generated from the registry, for post-deploy and post-refresh use |
| Orphan report | CronTrigger rows in ERROR / DELETED / null-NextFireTime state, consuming slots against the 100-job cap |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You need the monitoring SOQL, the abort/reschedule/flex-queue Apex, the scheduling registry format, or the deployable permission set and scheduled-Flow XML |
| `references/gotchas.md` | A job "looks fine" but the work did not happen, or a deploy failed on a schedule |
| `references/examples.md` | You want a worked diagnosis to follow end to end |
| `references/well-architected.md` | Justifying the monitoring and registry investment, or citing sources |
| `references/llm-anti-patterns.md` | Reviewing AI-generated batch monitoring or scheduling guidance |
| `templates/batch-job-scheduling-and-monitoring-template.md` | Recording a live investigation as you work it |

---

## Related Skills

- apex/batch-apex-patterns — writing and designing the Batch Apex class this skill only operates
- apex/apex-scheduled-jobs — implementing `Schedulable` and choosing the CRON expression
- apex/async-apex — the async model these jobs sit inside; read with `standards/decision-trees/async-selection.md` (Q9 schedule-plus-ad-hoc, Q12 progress feedback)
- apex/scheduled-apex-failure-detection-and-monitoring — `BatchApexErrorEvent` and the invocable sweep class the alerting recipe calls
- apex/apex-batch-chaining — the alternative when one job's runtime keeps overrunning its window
- apex/custom-logging-and-monitoring — centralized logging when email from `finish()` stops scaling
- flow/scheduled-flows — designing the Schedule-Triggered Flow whose schedule this skill monitors
- flow/scheduled-flow-not-running-debug — when the missing job is a Flow, not Apex
- devops/sandbox-refresh-and-templates — the refresh sequence that drops every schedule
- apex/apex-limits-monitoring — `OrgLimits` and the daily async execution allocation
