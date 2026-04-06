---
name: batch-job-scheduling-and-monitoring
description: "Use when monitoring, diagnosing, or managing Batch Apex, Scheduled Apex, Queueable, and Flow scheduled jobs: Setup > Apex Jobs, AsyncApexJob queries, concurrent limits, failure detection, and notification patterns. NOT for writing batch Apex code (use batch-apex-patterns) or writing Schedulable implementations (use apex-scheduled-jobs)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Batch Job Scheduling And Monitoring

This skill activates when a Salesforce admin, developer, or operator needs to monitor, diagnose, or manage async job execution in an org. It covers the Setup > Apex Jobs and Scheduled Jobs views, direct SOQL queries against `AsyncApexJob`, concurrent job limits, failure notification patterns, and the difference between how Batch Apex and Flow scheduled jobs surface in monitoring.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the job type: Batch Apex (`JobType='BatchApex'`), Scheduled Apex (`JobType='ScheduledApex'`), Queueable (`JobType='Queueable'`), Future (`JobType='Future'`), or Flow scheduled interview (`JobType='ScheduledFlow'`).
- Determine whether the issue is a job that is stuck/running, a job that failed silently, or a job that never fired.
- Note the org's concurrent Batch Apex limit — the default is 5 concurrent jobs. This is the most common cause of jobs staying in "Queued" status without progressing.

---

## Core Concepts

### Apex Jobs UI vs Scheduled Jobs UI

Salesforce provides two distinct monitoring views:
1. **Setup > Apex Jobs** — shows `AsyncApexJob` records for Batch Apex, Queueable, @future, and Scheduled Apex invocations. Displays status, number of records processed, errors, and completion time.
2. **Setup > Scheduled Jobs** — shows Scheduled Apex definitions (the cron-based schedule) and their next fire time. Also shows Schedule-Triggered Flow Interviews. This view does NOT show the individual Batch Apex executions triggered by a scheduled job — those appear in Apex Jobs.

Flow scheduled jobs (Schedule-Triggered Flow) appear only in Setup > Scheduled Jobs as "Schedule-Triggered Flow Interview". They do NOT appear in Apex Jobs.

### AsyncApexJob as the Query Surface

All Apex async jobs are queryable via SOQL against `AsyncApexJob`. This is the programmatic equivalent of the Apex Jobs UI and is the only way to retrieve historical job data programmatically.

Key fields:
- `Status` — Holding, Queued, Processing, Completed, Failed, Aborted
- `JobType` — BatchApex, ScheduledApex, Queueable, Future, BatchApexWorker
- `NumberOfErrors` — count of batch chunks that failed (for Batch Apex)
- `TotalJobItems` — total batch chunks
- `CompletedDate` — when the job finished (null if still running)
- `ExtendedStatus` — error message for failed jobs (up to 255 chars)

```soql
SELECT Id, ApexClass.Name, Status, NumberOfErrors, TotalJobItems,
       CreatedDate, CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
ORDER BY CreatedDate DESC
LIMIT 20
```

### Concurrent Batch Apex Limit

The org-wide limit is **5 concurrent Batch Apex jobs** in the Processing state. Jobs beyond 5 wait in Queued or Holding status. This limit is independent of the 100 scheduled Apex job limit.

- **Queued** — waiting for an executor slot. Normal if fewer than 5 jobs are in Processing.
- **Holding** — system backpressure — the job is waiting to be queued. Common in shared environments.

The concurrent limit can be increased above 5 via a Salesforce support case for Enterprise+ orgs.

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
| Job shows Status=Failed in Apex Jobs | Query `ExtendedStatus` on AsyncApexJob for error detail | Up to 255 chars of error in ExtendedStatus |
| Need to abort a running batch job | `Database.executeBatch()` returns the job ID; use `System.abortJob(jobId)` | Only works if job is in Queued/Holding/Processing |
| Flow scheduled job not appearing in Apex Jobs | Check Setup > Scheduled Jobs for "Schedule-Triggered Flow Interview" | Flow jobs do not appear in Apex Jobs |
| Need email notification on batch failure | Implement failure check in `finish()` method using AsyncApexJob query | No native platform notification on batch failure |
| Concurrent limit exceeded repeatedly | Open Salesforce support case to request limit increase | Default is 5; can be increased for Enterprise+ |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the job type (Batch Apex, Scheduled Apex, Flow scheduled, Queueable) — this determines which Setup view and query to use.
2. Navigate to Setup > Apex Jobs for Batch/Scheduled/Queueable. For Flow scheduled jobs, navigate to Setup > Scheduled Jobs.
3. Run a targeted SOQL query against `AsyncApexJob` filtered by `JobType` and `CreatedDate` to retrieve job history programmatically.
4. For failed jobs: read `ExtendedStatus` for the error message. If truncated, check debug logs or the Apex class's `finish()` method for more detail.
5. For stuck Queued jobs: count concurrent Batch Apex jobs in `Processing` state — if 5 or more, the queue is at capacity.
6. Implement a `finish()` notification if the batch class does not already send one on failure.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Verified job type maps to correct monitoring location (Apex Jobs vs Scheduled Jobs)
- [ ] SOQL query against AsyncApexJob is scoped to the correct JobType and time range
- [ ] ExtendedStatus checked for failed jobs — not just the Status field
- [ ] Concurrent Batch Apex job count confirmed against 5-job limit
- [ ] Batch class finish() method sends notification when NumberOfErrors > 0
- [ ] Scheduled Apex schedule definition confirmed in Scheduled Jobs UI (separate from execution records)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Flow scheduled jobs do NOT appear in Setup > Apex Jobs** — Admins looking for a scheduled flow that isn't running check Apex Jobs and see nothing. Flow schedule-triggered interviews only appear in Setup > Scheduled Jobs as "Schedule-Triggered Flow Interview". This is a common source of confusion.
2. **Batch Apex failure does not delete the Scheduled Apex schedule** — If a batch class is invoked by a scheduled Apex and fails, the batch fails but the schedule continues. The next cron window fires another instance. If the failure is caused by a data issue that isn't fixed, the job will keep failing on every scheduled run without any notification (unless `finish()` sends one).
3. **NumberOfErrors counts failed CHUNKS, not failed RECORDS** — For Batch Apex with a scope of 200, a `NumberOfErrors` of 1 means one chunk of up to 200 records failed — not necessarily one record. The actual record-level failure requires reading the exception in `Database.SaveResult[]` in the `execute()` method.
4. **Aborting a job removes it from Apex Jobs immediately** — Calling `System.abortJob(jobId)` removes the job from the queue. If you need a record of the abort for audit purposes, log it before aborting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AsyncApexJob SOQL query | Parameterized query for job history by type and time range |
| Batch finish() notification snippet | Apex code for failure detection and email notification in finish() |
| Concurrent job count query | SOQL to count currently Processing batch jobs against the 5-job limit |

---

## Related Skills

- batch-apex-patterns — writing and designing Batch Apex classes
- apex-scheduled-jobs — implementing the Schedulable interface and cron expressions
- custom-logging-and-monitoring — centralized logging patterns for Apex automation
