# Examples — Apex Scheduled Jobs

## Example 1: Nightly Record Cleanup Dispatched to Batch Apex

**Context:** An org needs to archive or delete stale `Lead` records older than 90 days, running every night at 2:00 AM. The volume can reach tens of thousands of records.

**Problem:** A developer puts the SOQL query and DML directly inside `execute()`. When the Lead volume grows, the job hits the 50,000-record SOQL row limit or 10,000-DML-row limit and silently fails, leaving no automatic retry.

**Solution:**

```apex
// Step 1: Schedulable dispatcher — keeps execute() lightweight
public with sharing class StaleLeadCleanupScheduler implements Schedulable {
    public void execute(SchedulableContext SC) {
        Database.executeBatch(new StaleLeadCleanupBatch(), 200);
    }
}

// Step 2: Batch class carries the governor-intensive work
public class StaleLeadCleanupBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext BC) {
        Date cutoff = Date.today().addDays(-90);
        return Database.getQueryLocator(
            'SELECT Id FROM Lead WHERE CreatedDate < :cutoff AND IsConverted = false'
        );
    }

    public void execute(Database.BatchableContext BC, List<Lead> scope) {
        delete scope;
    }

    public void finish(Database.BatchableContext BC) {
        // Optional: send notification or log completion
    }
}

// Step 3: Schedule via Anonymous Apex post-deployment
// '0 0 2 * * ?' = every day at 2:00 AM
System.schedule('Nightly Stale Lead Cleanup', '0 0 2 * * ?', new StaleLeadCleanupScheduler());
```

**Test class:**

```apex
@IsTest
private class StaleLeadCleanupSchedulerTest {
    @IsTest
    static void testScheduling() {
        Test.startTest();
        String jobId = System.schedule(
            'Test Stale Lead Cleanup',
            '0 0 2 * * ?',
            new StaleLeadCleanupScheduler()
        );
        Test.stopTest();

        CronTrigger ct = [
            SELECT State, CronExpression
            FROM CronTrigger
            WHERE Id = :jobId
        ];
        System.assertEquals('WAITING', ct.State);
        System.assertEquals('0 0 2 * * ?', ct.CronExpression);
    }
}
```

**Why it works:** The Schedulable acts purely as the timer and hands off to Batch Apex, which resets governor limits for each chunk of 200 records. That matters more than it first appears: the Schedulable body runs under *synchronous* limits (apexdev L19536), so it has 100 SOQL / 6 MB heap / 10,000 ms CPU to spend — less headroom than the Batch it dispatches, not more.

---

## Example 2: Abort-and-Reschedule Pattern for Schedule Changes

**Context:** An existing scheduled job runs at 2:00 AM nightly but the ops team wants to shift it to 3:30 AM to avoid contention with a new nightly ETL process. The job is live in production.

**Problem:** There is no API to modify a `CronTrigger` record in place. Attempting to change `CronExpression` via DML throws a `System.SObjectException`. Teams sometimes delete and recreate the class, causing downtime or confusion about the active job.

**Solution:**

```apex
// Run from Anonymous Apex or a post-deployment script
// Step 1: Find the active job by name
List<CronTrigger> existing = [
    SELECT Id, State
    FROM CronTrigger
    WHERE CronJobDetail.Name = 'Nightly Stale Lead Cleanup'
    AND State = 'WAITING'
    LIMIT 1
];

// Step 2: Abort the existing job if found
if (!existing.isEmpty()) {
    System.abortJob(existing[0].Id);
    System.debug('Aborted job: ' + existing[0].Id);
}

// Step 3: Reschedule with the new cron expression
// '0 30 3 * * ?' = every day at 3:30 AM
String newJobId = System.schedule(
    'Nightly Stale Lead Cleanup',
    '0 30 3 * * ?',
    new StaleLeadCleanupScheduler()
);
System.debug('Rescheduled job ID: ' + newJobId);
```

**Verification SOQL after running:**

```soql
SELECT Id, CronJobDetail.Name, CronExpression, State, NextFireTime
FROM CronTrigger
WHERE CronJobDetail.Name = 'Nightly Stale Lead Cleanup'
```

**Why it works:** `System.abortJob()` stops the job and frees the slot; the Object Reference lists `DELETED` — "The job has been deleted" — among the `CronTrigger.State` values. Abort does not stop work already running: "any code that is in progress will continue to execute until it completes" (apexrefguide L238663). The subsequent `System.schedule()` creates a new `CronTrigger` with the updated expression under the same display name. Reusing the same display name makes it easy to identify the job consistently in audit queries.

---

## Example 3: Master Scheduler Consolidating Multiple Jobs

**Context:** An org is approaching the 100-scheduled-job limit. Multiple teams have independently scheduled their own Apex jobs throughout the day, and adding more jobs is blocked.

**Problem:** Each team's job occupies a separate `CronTrigger` slot. The ceiling is 100 Apex classes scheduled concurrently — 5 in Developer Edition (salesforce_app_limits_cheatsheet L313) — and once it is reached, `System.schedule` fails. UNVERIFIED (2026-09-05): the exact exception text at the ceiling; neither apexdev.txt nor apexrefguide.txt quotes it, so do not match on a string.

**Solution:**

```apex
// Single master scheduler replaces many individual jobs
public with sharing class MasterNightlyScheduler implements Schedulable {
    public void execute(SchedulableContext SC) {
        // Dispatch each logical operation as separate Batch or Queueable
        Database.executeBatch(new StaleLeadCleanupBatch(), 200);
        Database.executeBatch(new ExpiredOpportunityBatch(), 200);
        System.enqueueJob(new MetricsRollupQueueable());
    }
}

// One scheduled job covers all three operations
// '0 0 2 * * ?' = 2:00 AM daily
System.schedule('Master Nightly Operations', '0 0 2 * * ?', new MasterNightlyScheduler());
```

**Why it works:** Three logical operations now consume one `CronTrigger` slot instead of three. Each dispatched Batch or Queueable runs in its own transaction with its own governor limits, and the fan-out is legal at this width because synchronous limits apply to scheduled Apex — up to 50 jobs may be added with `System.enqueueJob` (apexdev L19571), where the same code inside a Queueable would be capped at 1.

**What it costs:** consolidation trades granularity for slots. All three operations now share one fire time, one `CronTrigger.State`, and one row in Setup, so a partial failure is invisible from the schedule alone — `AsyncApexJob` becomes the only place the truth lives. Before consolidating, confirm the org is genuinely near the ceiling; this is the audit query:

```soql
SELECT CronJobDetail.Name, CronExpression, State, NextFireTime, TimesTriggered
FROM CronTrigger
WHERE CronJobDetail.JobType = '7'
  AND State IN ('WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'PAUSED_BLOCKED', 'BLOCKED')
ORDER BY NextFireTime ASC NULLS LAST
```

Rows whose owning feature was retired are the cheapest slots to reclaim — abort those before consolidating anything that still works. `JobType = '7'` is essential: an unfiltered count mixes in scheduled Flows (`'6'`), report runs (`'8'`) and dashboard refreshes (`'3'`), which do not compete for this ceiling.

---

## Anti-Pattern: Heavy Logic Inline in execute()

**What practitioners do:** Write SOQL queries, loops, and DML directly inside `execute()` because it seems simpler than creating a separate Batch class for a "small" job.

```apex
// ANTI-PATTERN — do not do this for significant data volumes
public with sharing class InlineCleanupScheduler implements Schedulable {
    public void execute(SchedulableContext SC) {
        List<Lead> staleLeads = [SELECT Id FROM Lead WHERE CreatedDate < LAST_N_DAYS:90];
        delete staleLeads; // Fails silently at 10,000 records
    }
}
```

**What goes wrong:** When record volume grows beyond governor limits (50,000 query rows, 10,000 DML rows), the job throws an unhandled exception, transitions to `ERROR` state on `CronTrigger`, and does not automatically retry. The job stays in `ERROR` state until someone notices and manually aborts and reschedules it.

**Correct approach:** Keep `execute()` to dispatch calls only. Delegate all data processing to Batch Apex (for large volumes) or a Queueable (for smaller async work). This keeps the Schedulable's governor footprint near zero regardless of data size.
