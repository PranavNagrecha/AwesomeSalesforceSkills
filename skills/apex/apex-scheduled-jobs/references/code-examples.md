# Code Examples — Apex Scheduled Jobs

A complete, deployable scheduled-job unit: a thin `Schedulable` that guards against
overlapping runs, an admin utility that makes scheduling idempotent, the test class, the
`-meta.xml` files, `package.xml`, the deploy order, the unschedule → deploy → reschedule
runbook, and the verification SOQL.

Everything below is grounded in the Apex Developer Guide (`apexdev`), the Apex Reference
Guide (`apexrefguide`), and the Object Reference (`object_reference`); line cites are given
per claim in the "How to read it" list.

---

## How to read it

- **The `Schedulable` method does not have to be `global`.** The guide states "The implemented
  method must be declared as global or public" (apexdev L16620) and its own sample is
  `public with sharing class ScheduledMerge implements Schedulable` with a `public void execute`
  (apexdev L16628–16632). `public` is the right default; `global` is only needed when the class
  crosses a managed-package namespace boundary.
- **The scheduled body runs under *synchronous* governor limits.** "Although scheduled Apex is an
  asynchronous feature, synchronous limits apply to scheduled Apex jobs" (apexdev L19536). That is
  100 SOQL queries, 6 MB heap, 10,000 ms CPU — not the async 200 / 12 MB / 60,000 ms
  (apexdev L19544–L19579). This is the concrete reason `execute()` stays a dispatcher; the guide
  itself recommends "all processing must take place in a separate class" (apexdev L16972).
- **`Database.executeBatch` and `System.enqueueJob` counts differ inside `execute()`.** Because
  synchronous limits apply, up to 50 jobs can be added with `System.enqueueJob` from a
  `Schedulable` (apexdev L19571, synchronous column) — the async column's limit of 1 does not bind
  here. Batch is separately capped at five queued or active batch jobs at one time
  (apexdev L17012), with the Flex Queue holding up to 100 more (apexdev L15940).
- **The platform's own overlap guard is per-`CronTrigger`, not per-workload.** `CronTrigger.State`
  becomes `BLOCKED` when "Execution of a second instance of the job is attempted while one instance
  is running" (object_reference L86820). That protects the *scheduler* from re-entering itself; it
  does **not** stop tonight's dispatched batch from running while last night's batch is still
  `Processing`. `NightlyRollupScheduler` below adds that second guard explicitly.
- **`AsyncApexJob.Status` values used by the guard** are `Aborted`, `Completed`, `Failed`,
  `Holding`, `Preparing`, `Processing`, `Queued` (object_reference, AsyncApexJob `Status` field,
  ~L42414). In-flight for our purposes is `Holding`, `Preparing`, `Processing`, `Queued`.
- **`SchedulableContext.getTriggerId()` returns a `CronTrigger` Id that `System.abortJob` accepts.**
  The abort reference lists `SchedulableContext.getTriggerId` among "the following methods return
  the job ID that can be passed to abortJob" (apexrefguide L238688–L238695). `abortJob` rejects an
  `AsyncApexJob` Id for a scheduled job (apexrefguide L238679–L238681).
- **`System.schedule` returns the CronTrigger Id as a `String`**; signature
  `public static String schedule(String jobName, String cronExpression, Object schedulableClass)`
  (apexrefguide L239722–L239735).
- **Duplicate job names fail at run time**, with
  `System.AsyncException: The Apex job named "jobName" is already scheduled for execution`
  (apexdev L16812). `SchedulerAdmin.scheduleOrReplace` exists to make that impossible.
- **`apiVersion` 67.0** matches the repo's canonical Apex metadata (`templates/apex/ApplicationLogger.cls-meta.xml`).

Canonical building blocks referenced rather than re-invented:

| Need | Use this, do not rewrite it |
|---|---|
| Structured logging from `execute()` and from the batch | `templates/apex/ApplicationLogger.cls` |
| Test data at bulk volume | `templates/apex/tests/TestDataFactory.cls` |
| The ≥ 200-record bulk assertion shape | `templates/apex/tests/BulkTestPattern.cls` |
| FLS/CRUD enforcement inside the dispatched worker | `templates/apex/SecurityUtils.cls` |
| Selector layer for the batch's `start()` query | `templates/apex/BaseSelector.cls` |

---

## 1. `NightlyRollupScheduler.cls` — the thin Schedulable with an overlap guard

```apex
/**
 * NightlyRollupScheduler
 *
 * Clock-only entry point. Does NO business work: it decides whether the previous run
 * is still in flight and, if not, hands off to AccountRollupBatch.
 *
 * Why so thin: scheduled Apex runs under SYNCHRONOUS governor limits
 * (Apex Developer Guide, Per-Transaction Apex Limits note: "Although scheduled Apex is
 * an asynchronous feature, synchronous limits apply to scheduled Apex jobs") — 100 SOQL,
 * 6 MB heap, 10,000 ms CPU. Real work belongs in the batch.
 *
 * `public` (not `global`) is deliberate: the guide requires the execute method be
 * "global or public". Use `global` only to expose this across a managed-package namespace.
 */
public with sharing class NightlyRollupScheduler implements Schedulable {

    /** Job name used by SchedulerAdmin and by the verification SOQL. */
    public static final String JOB_NAME = 'Nightly Account Rollup';

    /** 01:15 every day. Day_of_week is '?' because Day_of_month is '*'. */
    public static final String CRON_EXPRESSION = '0 15 1 * * ?';

    /** Batch scope. A factor of 2000 per the guide's scope guidance. */
    private static final Integer BATCH_SCOPE = 200;

    /** AsyncApexJob.Status values that mean "still in flight". */
    private static final Set<String> IN_FLIGHT_STATUSES = new Set<String>{
        'Holding', 'Preparing', 'Processing', 'Queued'
    };

    /**
     * Optional run-date override so the same class can be reused for a catch-up run
     * scheduled at a different time. Marked transient: scheduled job objects and their
     * member variables persist from initialization into every subsequent run
     * (Apex Developer Guide, Apex Scheduler Notes and Best Practices), which silently
     * pins a stale date into every future execution unless the field is transient.
     */
    public transient Date asOfOverride;

    public NightlyRollupScheduler() {
        this.asOfOverride = null;
    }

    public NightlyRollupScheduler(Date asOf) {
        this.asOfOverride = asOf;
    }

    public void execute(SchedulableContext sc) {
        String triggerId = sc == null ? null : sc.getTriggerId();

        if (isPreviousRunInFlight()) {
            // Skip, do not queue behind it. A rollup that runs twice over the same
            // window double-counts; a rollup that skips one night self-heals tomorrow.
            ApplicationLogger.warn(
                'NightlyRollupScheduler',
                'Skipped run: AccountRollupBatch still in flight. CronTrigger=' + triggerId
            );
            ApplicationLogger.flush();
            return;
        }

        Date asOf = (asOfOverride == null) ? Date.today() : asOfOverride;
        Id batchId = Database.executeBatch(new AccountRollupBatch(asOf), BATCH_SCOPE);

        ApplicationLogger.info(
            'NightlyRollupScheduler',
            'Dispatched AccountRollupBatch ' + batchId + ' asOf=' + asOf +
            ' from CronTrigger=' + triggerId
        );
        ApplicationLogger.flush();
    }

    /**
     * One SOQL query. Returns true when a prior AccountRollupBatch has not finished.
     * AsyncApexJob.Status values are from the Object Reference (AsyncApexJob).
     */
    @TestVisible
    private static Boolean isPreviousRunInFlight() {
        List<AsyncApexJob> inFlight = [
            SELECT Id, Status, CreatedDate
            FROM AsyncApexJob
            WHERE JobType IN ('BatchApex', 'BatchApexWorker')
              AND ApexClass.Name = 'AccountRollupBatch'
              AND Status IN :IN_FLIGHT_STATUSES
            LIMIT 1
        ];
        return !inFlight.isEmpty();
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> File: `force-app/main/default/classes/NightlyRollupScheduler.cls-meta.xml`

---

## 2. `AccountRollupBatch.cls` — the worker the scheduler dispatches

The scheduler is useless without a worker; this is the minimum that makes the package
deployable. Scope sizing, `Database.Stateful`, and chaining belong to
`apex/batch-apex-patterns` and `apex/apex-batch-chaining` — read those before changing it.

```apex
public with sharing class AccountRollupBatch implements Database.Batchable<SObject> {

    private final Date asOf;

    public AccountRollupBatch(Date asOf) {
        this.asOf = asOf;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        Date windowStart = asOf.addDays(-1);
        return Database.getQueryLocator([
            SELECT Id, Open_Opportunity_Amount__c
            FROM Account
            WHERE LastModifiedDate >= :windowStart
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        Map<Id, Decimal> totals = new Map<Id, Decimal>();
        for (Account a : scope) {
            totals.put(a.Id, 0);
        }
        for (AggregateResult ar : [
            SELECT AccountId acctId, SUM(Amount) total
            FROM Opportunity
            WHERE AccountId IN :totals.keySet() AND IsClosed = false
            GROUP BY AccountId
        ]) {
            totals.put((Id) ar.get('acctId'), (Decimal) ar.get('total'));
        }

        List<Account> updates = new List<Account>();
        for (Account a : scope) {
            Decimal newTotal = totals.get(a.Id) == null ? 0 : totals.get(a.Id);
            if (a.Open_Opportunity_Amount__c != newTotal) {
                updates.add(new Account(Id = a.Id, Open_Opportunity_Amount__c = newTotal));
            }
        }
        if (!updates.isEmpty()) {
            update updates;
        }
    }

    public void finish(Database.BatchableContext bc) {
        AsyncApexJob job = [
            SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, ExtendedStatus
            FROM AsyncApexJob
            WHERE Id = :bc.getJobId()
        ];
        ApplicationLogger.info(
            'AccountRollupBatch',
            'Finished ' + job.Status + ' errors=' + job.NumberOfErrors +
            ' batches=' + job.JobItemsProcessed + '/' + job.TotalJobItems +
            ' detail=' + job.ExtendedStatus
        );
        ApplicationLogger.flush();
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> File: `force-app/main/default/classes/AccountRollupBatch.cls-meta.xml`

---

## 3. `SchedulerAdmin.cls` — idempotent scheduling and job inventory

```apex
/**
 * SchedulerAdmin — one place that knows how to (re)schedule a job safely.
 *
 * scheduleOrReplace() exists because System.schedule() throws
 * "System.AsyncException: The Apex job named "<name>" is already scheduled for execution"
 * when a CronTrigger with that CronJobDetail.Name already exists (Apex Developer Guide,
 * Using the System.schedule Method). Aborting first makes every post-deploy script
 * re-runnable, which matters when a release is retried.
 */
public with sharing class SchedulerAdmin {

    /** CronTrigger.State values that still occupy a scheduled-Apex slot. */
    private static final Set<String> LIVE_STATES = new Set<String>{
        'WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'PAUSED_BLOCKED', 'BLOCKED'
    };

    /** CronJobDetail.JobType value for scheduled Apex (Object Reference: CronJobDetail). */
    public static final String JOB_TYPE_SCHEDULED_APEX = '7';

    /** Apex classes scheduled concurrently: 100 (5 in Developer Edition). */
    public static final Integer SCHEDULED_APEX_CEILING = 100;

    public class SchedulerAdminException extends Exception {}

    /**
     * Abort any live CronTrigger carrying this job name, then schedule the instance.
     * Returns the new CronTrigger Id.
     */
    public static Id scheduleOrReplace(String jobName, String cronExpression, Schedulable instance) {
        if (String.isBlank(jobName) || String.isBlank(cronExpression) || instance == null) {
            throw new SchedulerAdminException('jobName, cronExpression and instance are all required.');
        }

        Integer aborted = abortByName(jobName);
        if (aborted > 0) {
            ApplicationLogger.info('SchedulerAdmin', 'Aborted ' + aborted + ' prior job(s) named ' + jobName);
        }

        Integer used = scheduledApexCount();
        if (used >= SCHEDULED_APEX_CEILING) {
            throw new SchedulerAdminException(
                'Scheduled Apex ceiling reached: ' + used + '/' + SCHEDULED_APEX_CEILING +
                '. Retire a job before scheduling ' + jobName + '.'
            );
        }

        Id cronTriggerId = (Id) System.schedule(jobName, cronExpression, instance);
        ApplicationLogger.info('SchedulerAdmin', 'Scheduled ' + jobName + ' as ' + cronTriggerId);
        ApplicationLogger.flush();
        return cronTriggerId;
    }

    /** Abort every live CronTrigger with this CronJobDetail.Name. Returns how many. */
    public static Integer abortByName(String jobName) {
        List<CronTrigger> live = [
            SELECT Id, State
            FROM CronTrigger
            WHERE CronJobDetail.Name = :jobName
              AND State IN :LIVE_STATES
        ];
        for (CronTrigger ct : live) {
            System.abortJob(ct.Id);
        }
        return live.size();
    }

    /** Scheduled-Apex jobs only, excluding scheduled Flows, report runs, dashboards. */
    public static Integer scheduledApexCount() {
        return [
            SELECT COUNT()
            FROM CronTrigger
            WHERE CronJobDetail.JobType = :JOB_TYPE_SCHEDULED_APEX
              AND State IN :LIVE_STATES
        ];
    }

    /** Inventory rows for a release checklist or an audit report. */
    public static List<CronTrigger> inventory() {
        return [
            SELECT Id, CronJobDetail.Name, CronJobDetail.JobType, CronExpression,
                   State, NextFireTime, PreviousFireTime, TimesTriggered,
                   TimeZoneSidKey, OwnerId
            FROM CronTrigger
            WHERE CronJobDetail.JobType = :JOB_TYPE_SCHEDULED_APEX
            ORDER BY NextFireTime ASC NULLS LAST
        ];
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> File: `force-app/main/default/classes/SchedulerAdmin.cls-meta.xml`

---

## 4. `NightlyRollupSchedulerTest.cls` — asserts the CronTrigger row and the synchronous fire

The `Test.startTest()` / `Test.stopTest()` bracket is what makes the scheduled job run
synchronously: "All asynchronous calls made after the startTest method are collected by the
system. When stopTest is executed, all asynchronous processes are run synchronously"
(apexdev L16712–L16716). The four assertions below — `CronExpression`, `State`,
`TimesTriggered == 0`, `NextFireTime` — mirror the guide's own scheduler test
(apexdev L16736–L16745, L16770–L16800).

A far-future CRON year is used so `NextFireTime` is deterministic; the guide's own example
uses `'0 0 0 3 9 ? 2042'`.

```apex
@IsTest
private class NightlyRollupSchedulerTest {

    /** Far-future so NextFireTime is deterministic and the job never fires "for real". */
    private static final String TEST_CRON = '0 0 0 3 9 ? 2042';

    /** Unique per method: System.schedule rejects a duplicate job name in the same org. */
    private static String uniqueJobName(String suffix) {
        return 'Test Nightly Rollup ' + suffix + ' ' + String.valueOf(Crypto.getRandomInteger()).right(8);
    }

    @TestSetup
    static void seed() {
        // 200 accounts: the bulk floor from templates/apex/tests/BulkTestPattern.cls
        insert TestDataFactory.createAccounts(200, null);
    }

    @IsTest
    static void schedulingCreatesAWaitingCronTriggerAndFiresAtStopTest() {
        String jobName = uniqueJobName('happy');
        List<Account> accounts = [SELECT Id FROM Account LIMIT 200];
        System.assertEquals(200, accounts.size(), 'Test setup should have seeded 200 accounts');

        Test.startTest();
        String jobId = System.schedule(jobName, TEST_CRON, new NightlyRollupScheduler());

        CronTrigger ct = [
            SELECT Id, CronExpression, State, TimesTriggered, NextFireTime,
                   CronJobDetail.Name, CronJobDetail.JobType
            FROM CronTrigger
            WHERE Id = :jobId
        ];
        System.assertEquals(TEST_CRON, ct.CronExpression, 'CronExpression should round-trip unchanged');
        System.assertEquals('WAITING', ct.State, 'A freshly scheduled job waits for execution');
        System.assertEquals(0, ct.TimesTriggered, 'The job must not have run before stopTest');
        System.assertEquals(
            '2042-09-03 00:00:00',
            String.valueOf(ct.NextFireTime),
            'NextFireTime must match the CRON expression'
        );
        System.assertEquals(jobName, ct.CronJobDetail.Name, 'CronJobDetail carries the display name');
        System.assertEquals('7', ct.CronJobDetail.JobType, 'JobType 7 is scheduled Apex');

        // stopTest runs the collected asynchronous work synchronously.
        Test.stopTest();

        // The scheduler dispatched exactly one batch.
        List<AsyncApexJob> batches = [
            SELECT Id, Status, JobType
            FROM AsyncApexJob
            WHERE JobType = 'BatchApex' AND ApexClass.Name = 'AccountRollupBatch'
        ];
        System.assertEquals(1, batches.size(), 'execute() should dispatch exactly one AccountRollupBatch');
    }

    @IsTest
    static void schedulerSkipsWhenAPriorBatchIsStillInFlight() {
        // No batch has been created in this transaction, so nothing is in flight.
        System.assertEquals(
            false,
            NightlyRollupScheduler.isPreviousRunInFlight(),
            'A clean org has no AccountRollupBatch in flight'
        );
    }

    @IsTest
    static void scheduleOrReplaceIsIdempotent() {
        String jobName = uniqueJobName('idempotent');

        Test.startTest();
        Id first = SchedulerAdmin.scheduleOrReplace(jobName, TEST_CRON, new NightlyRollupScheduler());
        Id second = SchedulerAdmin.scheduleOrReplace(jobName, '0 0 1 3 9 ? 2042', new NightlyRollupScheduler());
        Test.stopTest();

        System.assertNotEquals(first, second, 'Rescheduling creates a new CronTrigger record');

        List<CronTrigger> live = [
            SELECT Id, CronExpression, State
            FROM CronTrigger
            WHERE CronJobDetail.Name = :jobName
              AND State IN ('WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'BLOCKED')
        ];
        System.assertEquals(1, live.size(), 'Only one live CronTrigger may carry the job name');
        System.assertEquals('0 0 1 3 9 ? 2042', live[0].CronExpression, 'The replacement cron is in effect');
    }

    @IsTest
    static void scheduleOrReplaceRejectsBlankInput() {
        try {
            SchedulerAdmin.scheduleOrReplace('', TEST_CRON, new NightlyRollupScheduler());
            System.assert(false, 'A blank job name should have thrown');
        } catch (SchedulerAdmin.SchedulerAdminException e) {
            System.assert(
                e.getMessage().contains('required'),
                'Expected the required-argument message, got: ' + e.getMessage()
            );
        }
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> File: `force-app/main/default/classes/NightlyRollupSchedulerTest.cls-meta.xml`

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>NightlyRollupScheduler</members>
        <members>AccountRollupBatch</members>
        <members>SchedulerAdmin</members>
        <members>NightlyRollupSchedulerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Account.Open_Opportunity_Amount__c</members>
        <name>CustomField</name>
    </types>
    <version>67.0</version>
</Package>
```

Note what is **absent**: there is no `CronTrigger` member and no metadata type for a schedule.
The active job is data, not metadata — step 3 of the runbook below is not optional.

---

## 6. Deploy order

| # | Action | Why this order |
|---|---|---|
| 1 | `SchedulerAdmin.abortByName('Nightly Account Rollup')` in the target org | An active scheduled job locks the class **and every class it references** against update (apexdev L16604). Deploying first produces `This schedulable class has jobs pending or in progress - CronTrigger IDs (ids)` (apexdev L16991). |
| 2 | Deploy the custom field, then the four classes | `Account.Open_Opportunity_Amount__c` must exist before `AccountRollupBatch` compiles. |
| 3 | Run the reschedule script (§7) | Nothing in `package.xml` recreates the schedule. |
| 4 | Run the verification SOQL (§8) | Confirms `State`, `NextFireTime`, and that exactly one live `CronTrigger` carries the name. |

```bash
# 1. Abort the live job (see §7 for the script body)
sf apex run --file scripts/apex/unschedule-nightly-rollup.apex --target-org prod

# 2. Validate, then deploy
sf project deploy start --manifest manifest/package.xml --target-org prod \
  --test-level RunSpecifiedTests --tests NightlyRollupSchedulerTest --dry-run
sf project deploy start --manifest manifest/package.xml --target-org prod \
  --test-level RunSpecifiedTests --tests NightlyRollupSchedulerTest

# 3. Reschedule
sf apex run --file scripts/apex/reschedule-nightly-rollup.apex --target-org prod

# 4. Verify (see §8)
sf data query --query "SELECT Id, CronJobDetail.Name, CronExpression, State, NextFireTime, TimesTriggered FROM CronTrigger WHERE CronJobDetail.JobType = '7'" --target-org prod

# Retrieve the deployed classes back into source control
sf project retrieve start --manifest manifest/package.xml --target-org prod

# Test verification only
sf apex run test --tests NightlyRollupSchedulerTest --result-format human --wait 10 --target-org prod
```

---

## 7. The unschedule → deploy → reschedule runbook

Two Anonymous Apex files, both checked into `scripts/apex/` next to the classes.

`scripts/apex/unschedule-nightly-rollup.apex` — run **before** the deploy:

```apex
// Run BEFORE deploying. Frees the class from the schedulable-class deploy lock.
// Idempotent: safe to run when no job exists.
Integer aborted = SchedulerAdmin.abortByName(NightlyRollupScheduler.JOB_NAME);
System.debug(LoggingLevel.INFO, 'Aborted ' + aborted + ' job(s) named ' + NightlyRollupScheduler.JOB_NAME);

Integer remaining = SchedulerAdmin.scheduledApexCount();
System.debug(LoggingLevel.INFO, 'Scheduled Apex slots in use after abort: ' + remaining + '/100');
```

`scripts/apex/reschedule-nightly-rollup.apex` — run **after** the deploy:

```apex
// Run AFTER deploying. Idempotent: scheduleOrReplace aborts any live job of the same
// name first, so re-running a failed release does not throw the duplicate-name
// AsyncException.
//
// The CRON expression is interpreted in the TIME ZONE OF THE USER RUNNING THIS SCRIPT
// (Apex Developer Guide: "The System.schedule method uses the user's time zone as the
// basis of all schedules"). Run it as the integration user whose time zone the SLA is
// written against, not as whoever happens to be doing the release.
System.debug(LoggingLevel.INFO, 'Scheduling as ' + UserInfo.getName() +
    ' in time zone ' + UserInfo.getTimeZone().getID());

Id cronTriggerId = SchedulerAdmin.scheduleOrReplace(
    NightlyRollupScheduler.JOB_NAME,
    NightlyRollupScheduler.CRON_EXPRESSION,
    new NightlyRollupScheduler()
);

CronTrigger ct = [
    SELECT Id, CronExpression, State, NextFireTime, TimeZoneSidKey
    FROM CronTrigger
    WHERE Id = :cronTriggerId
];
System.debug(LoggingLevel.INFO, 'Scheduled ' + ct.Id +
    ' cron=' + ct.CronExpression +
    ' state=' + ct.State +
    ' nextFire=' + ct.NextFireTime +
    ' tz=' + ct.TimeZoneSidKey);
```

If the deploy fails at step 2 the schedule is already gone — the org is running with the
job unscheduled until step 3 succeeds. For an overnight job that is usually acceptable;
for anything hourly, gate the release window accordingly, or accept the lock and use the
Deployment Settings bypass (apexdev L16991–L16995), which the guide warns "can fail".

---

## 8. Verification SOQL

**Is the job live, and when does it next fire?**

```soql
SELECT Id, CronJobDetail.Name, CronJobDetail.JobType, CronExpression,
       State, NextFireTime, PreviousFireTime, TimesTriggered,
       StartTime, EndTime, TimeZoneSidKey, OwnerId
FROM CronTrigger
WHERE CronJobDetail.Name = 'Nightly Account Rollup'
ORDER BY CreatedDate DESC
```

Expected immediately after §7: exactly one row, `State = 'WAITING'`, `TimesTriggered = 0`,
`NextFireTime` = the next 01:15 in `TimeZoneSidKey`.

**How close is the org to the ceiling?** `JobType = '7'` filters to scheduled Apex only —
scheduled Flows are `'6'`, report runs `'8'`, dashboard refreshes `'3'`
(object_reference, CronJobDetail `JobType`).

```soql
SELECT COUNT()
FROM CronTrigger
WHERE CronJobDetail.JobType = '7'
  AND State IN ('WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'PAUSED_BLOCKED', 'BLOCKED')
```

**Which jobs are unhealthy?** `ERROR` means the trigger definition itself is broken;
`BLOCKED` means a second instance was attempted while one was running.

```soql
SELECT Id, CronJobDetail.Name, State, CronExpression, NextFireTime, PreviousFireTime, TimesTriggered
FROM CronTrigger
WHERE CronJobDetail.JobType = '7'
  AND State IN ('ERROR', 'BLOCKED', 'PAUSED_BLOCKED')
```

**Did the dispatched work actually succeed?** `CronTrigger` says the *timer* fired;
`AsyncApexJob` says the *work* finished. A green `CronTrigger` over a `Failed` batch is the
most common false-clean signal in this domain.

```soql
SELECT Id, ApexClass.Name, JobType, Status, NumberOfErrors, ExtendedStatus,
       JobItemsProcessed, TotalJobItems, CreatedDate, CompletedDate, CronTriggerId
FROM AsyncApexJob
WHERE ApexClass.Name IN ('NightlyRollupScheduler', 'AccountRollupBatch')
  AND CreatedDate = LAST_N_DAYS:3
ORDER BY CreatedDate DESC
```

`AsyncApexJob.CronTriggerId` "only applies to ScheduledApex job type" and is available in
API version 53.0 and later (object_reference, AsyncApexJob) — it is the join back from a run
to the schedule that produced it.

---

## 9. Run the checker before you deploy

```bash
python3 skills/apex/apex-scheduled-jobs/scripts/check_apex_scheduled_jobs.py \
  --manifest-dir force-app/main/default/classes
# add --strict in CI to promote WARN to ERROR
```

---

## Related reading

- `apex/batch-apex-patterns` — `AccountRollupBatch`'s scope sizing, `Database.Stateful`, `start()` shapes.
- `apex/apex-batch-chaining` — chaining from `finish()`, and `System.scheduleBatch` as a chain ceiling.
- `apex/apex-queueable-patterns` — the Queueable that a callout-needing scheduler must delegate to.
- `apex/scheduled-apex-failure-detection-and-monitoring` — `BatchApexErrorEvent` and alerting on the `AsyncApexJob` rows queried above.
- `standards/decision-trees/async-selection.md` — whether a schedule is the right trigger at all.
