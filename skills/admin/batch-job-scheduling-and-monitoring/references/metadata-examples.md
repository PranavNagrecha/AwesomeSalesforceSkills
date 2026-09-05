# Metadata & Operations Examples — Batch Job Scheduling And Monitoring

This skill's deployable surface is deliberately small. **A schedule is data, not metadata.** The
class or Flow that runs is deployable; the *fact that it is scheduled at 02:00* is not. Everything
below is split accordingly: XML you deploy, SOQL you run, anonymous Apex you execute, and a
registry file you keep in source control because the platform will not keep it for you.

---

## 1. What is deployable and what is not

| Surface | Deployable via Metadata API? | Where it actually lives |
|---|---|---|
| `ApexClass` implementing `Schedulable` / `Database.Batchable` | Yes | `force-app/main/default/classes/` |
| `Flow` with `<triggerType>Scheduled</triggerType>` | Yes — `FlowSchedule` is a Flow subtype (api_meta.txt L71335–71382) | `force-app/main/default/flows/` |
| `PermissionSet` granting monitoring access | Yes (api_meta.txt L95370–95395) | `force-app/main/default/permissionsets/` |
| `CronTrigger` / `CronJobDetail` (the schedule itself) | **No** | Org data — created by `System.schedule()` or Setup > Schedule Apex |
| `AsyncApexJob` (execution history) | **No** | Org data — read-only, `query()` / `retrieve()` only |

Grounding for the two "No" rows: `CronTrigger`, `CronJobDetail` and `AsyncApexJob` appear nowhere in
the Metadata API Developer Guide (`grep -c "CronTrigger" api_meta.txt` → 0), and the Object Reference
lists their Supported Calls as `describeSObjects(), query(), retrieve()` only — no `create()`
(Object Reference: AsyncApexJob L42267–42268; CronJobDetail L86669–86670; CronTrigger L86715–86716).

**The consequence you must plan for:** a deploy moves the class; it does not move the schedule.
After every deploy to a new org — and after every sandbox refresh — someone has to re-run
`System.schedule()`. That is why section 5 exists.

---

## 2. Deployable XML

### 2a. `permissionsets/Async_Job_Operations.permissionset-meta.xml`

The Object Reference states, for `AsyncApexJob`: *"If Apex isn't running in system mode, users must
have the View Setup and Configuration permission to access this object and to enqueue asynchronous
Apex jobs."* (object_reference.txt L42272–42273). So the ops team that runs the monitoring queries
needs `ViewSetup` — not a profile change, a permission set.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Async Job Operations</label>
    <description>Read-only access to Apex Jobs, Scheduled Jobs and the Apex Flex Queue for the batch-operations on-call rota. Does not grant Author Apex.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <userPermissions>
        <enabled>true</enabled>
        <name>ViewSetup</name>
    </userPermissions>
</PermissionSet>
```

Shape and the `<userPermissions><enabled>/<name>` pair are taken from the PermissionSet sample in
the Metadata API Developer Guide (api_meta.txt L95370–95395).

### 2b. `flows/Batch_Failure_Sweep.flow-meta.xml`

A once-daily sweep that calls an Apex invocable action to read `AsyncApexJob` and raise the alert.
The Flow owns the *schedule*; the Apex owns the *query*, because `AsyncApexJob` is a setup object
that Apex can query in system mode without the running user holding View Setup (object_reference.txt
L42272–42273). See `apex/scheduled-apex-failure-detection-and-monitoring` for the invocable class.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <actionCalls>
        <name>Sweep_Failed_Async_Jobs</name>
        <label>Sweep Failed Async Jobs</label>
        <locationX>176</locationX>
        <locationY>134</locationY>
        <actionName>AsyncJobFailureSweep</actionName>
        <actionType>apex</actionType>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>lookbackHours</name>
            <value>
                <numberValue>24.0</numberValue>
            </value>
        </inputParameters>
    </actionCalls>
    <interviewLabel>Batch Failure Sweep {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Batch Failure Sweep</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Sweep_Failed_Async_Jobs</targetReference>
        </connector>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2026-09-07</startDate>
            <startTime>07:30:00.000Z</startTime>
        </schedule>
        <triggerType>Scheduled</triggerType>
    </start>
    <status>Active</status>
</Flow>
```

### How to read it

- `<triggerType>Scheduled</triggerType>` is the only value that makes `<schedule>` legal —
  `schedule` is *"Required when triggerType is Scheduled"* (api_meta.txt L72462).
- `<frequency>` accepts `Once`, `Daily`, `Weekly` for an ordinary scheduled flow; the other values
  (`Hourly`, `Monthly`, `Weekdays`, `Yearly`, `OnActivate`) are **segment-triggered flows only**
  (api_meta.txt L71352–71366). Deploying `Hourly` on a plain scheduled flow is a design error, not
  a shortcut to hourly runs — chain from Apex instead (`apex/apex-batch-chaining`).
- `<startTime>` is *"based on the org's default time zone"* (api_meta.txt L71378–71379). This is
  **not** the same basis as `System.schedule()`, which *"uses the user's timezone for the basis of
  all schedules"* (apexrefguide.txt L239764). Two jobs written to run "at 2 AM" can be two hours
  apart. See gotcha 8.
- The `<start>` element carries no `<object>`, so the flow runs **once per schedule**, not once per
  record. Adding `<object>` turns it into a per-record batch — a different runtime shape entirely.
- `<status>Active</status>` on deploy means the schedule is live the moment the deploy finishes.
  Deploy `Draft` first if the org is not ready for the first fire.

### Deploy and retrieve

```bash
# Retrieve what the org already has
sf project retrieve start \
  --metadata "PermissionSet:Async_Job_Operations" \
  --metadata "Flow:Batch_Failure_Sweep" \
  --target-org prod

# Validate before you deploy (never deploy a schedulable class blind — see gotcha 6)
sf project deploy validate --manifest manifest/package.xml --target-org prod

sf project deploy start --manifest manifest/package.xml --target-org prod
```

### `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Async_Job_Operations</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Batch_Failure_Sweep</members>
        <name>Flow</name>
    </types>
    <types>
        <members>AsyncJobFailureSweep</members>
        <members>AccountEnrichmentSchedule</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

There is no `<name>CronTrigger</name>` entry to add, and never will be. Re-establishing the schedule
after this deploy is a manual or scripted step (section 4b).

### Verification step

After deploying, prove the flow is actually scheduled — the deploy succeeding is not the proof:

```soql
SELECT CronJobDetail.Name, CronJobDetail.JobType, State, NextFireTime, TimeZoneSidKey
FROM CronTrigger
WHERE CronJobDetail.JobType = '6'
ORDER BY NextFireTime
```

`JobType = '6'` is Scheduled Flow (object_reference.txt L86680–86689). If this returns nothing, the
flow deployed but did not schedule. Setup equivalent: **Setup > Scheduled Jobs**, filter Type =
"Scheduled Flow".

---

## 3. The monitoring SOQL set

### 3a. Running and recently failed Apex jobs, last 24 hours

```soql
SELECT Id, ApexClass.Name, MethodName, JobType, Status,
       JobItemsProcessed, TotalJobItems, NumberOfErrors,
       CreatedDate, CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE CreatedDate = LAST_N_HOURS:24
  AND Status IN ('Holding', 'Queued', 'Preparing', 'Processing', 'Failed', 'Aborted')
  AND JobType != 'BatchApexWorker'
ORDER BY CreatedDate DESC
```

`JobType != 'BatchApexWorker'` is not cosmetic. Chunked batch jobs create *child* jobs of type
`BatchApexWorker`, each carrying the parent's Id in `ParentJobId` (object_reference.txt
L42401–42405). Leave them in and a single batch run looks like dozens of jobs.

Status values are a restricted picklist: `Aborted`, `Completed`, `Failed`, `Holding`, `Preparing`,
`Processing`, `Queued` (object_reference.txt L42419–42429).

### 3b. Jobs by class with error counts — the weekly health roll-up

```soql
SELECT ApexClass.Name, Status, COUNT(Id) jobCount, SUM(NumberOfErrors) failedBatches
FROM AsyncApexJob
WHERE CreatedDate = LAST_N_DAYS:7
  AND JobType IN ('BatchApex', 'ScheduledApex', 'Queueable')
GROUP BY ApexClass.Name, Status
ORDER BY SUM(NumberOfErrors) DESC
```

Read `failedBatches` as **batches**, not records: *"Total number of batches with a failure. A batch
is considered transactional, so any unhandled exceptions constitute an entire failure of the
batch."* (object_reference.txt L42393–42394).

### 3c. The error text you can actually see

```soql
SELECT ApexClass.Name, Status, NumberOfErrors, ExtendedStatus, CompletedDate
FROM AsyncApexJob
WHERE CreatedDate = LAST_N_DAYS:2
  AND (Status = 'Failed' OR NumberOfErrors > 0)
ORDER BY CompletedDate DESC
```

`ExtendedStatus` holds *"a short description of the first error"* only. The full detail *"along with
any subsequent errors, is emailed to the last user who modified the batch class"* (object_reference.txt
L42325–42333). If that user has left the company, that email is going nowhere — see gotcha 5.

### 3d. Scheduled jobs with next fire time and state

```soql
SELECT CronJobDetail.Name, CronJobDetail.JobType, CronExpression, State,
       NextFireTime, PreviousFireTime, TimesTriggered, TimeZoneSidKey, OwnerId
FROM CronTrigger
ORDER BY NextFireTime NULLS LAST
```

`CronJobDetail.JobType` codes: `1` Data Export, `3` Dashboard Refresh, `4` Reporting Snapshot,
`6` Scheduled Flow, `7` Scheduled Apex, `8` Report Run, `9` Batch Job, `A` Reporting Notification
(object_reference.txt L86680–86689). `State` values: `WAITING`, `ACQUIRED`, `EXECUTING`, `COMPLETE`,
`ERROR`, `DELETED`, `PAUSED`, `BLOCKED`, `PAUSED_BLOCKED` (object_reference.txt L86812–86823).

Count against the cap the same way the Apex Developer Guide tells you to — *"You can also
programmatically query the CronTrigger and CronJobDetail objects to get the count of Apex scheduled
jobs"* (apexdev.txt L16597–16600):

```soql
SELECT COUNT(Id)
FROM CronTrigger
WHERE CronJobDetail.JobType = '7'
```

100 is the cap for Apex classes scheduled concurrently; 5 in Developer Edition orgs
(salesforce_app_limits_cheatsheet.txt L313–314).

### 3e. Orphaned schedules — the class or flow is gone, the trigger is not

```soql
SELECT Id, CronJobDetail.Name, CronJobDetail.JobType, State, NextFireTime, TimesTriggered
FROM CronTrigger
WHERE State IN ('ERROR', 'DELETED', 'BLOCKED', 'PAUSED_BLOCKED')
   OR NextFireTime = NULL
ORDER BY CronJobDetail.Name
```

`ERROR` means *"The trigger definition has an error"* and `NextFireTime` is *"null if the job is not
scheduled to run again"* (object_reference.txt L86816, L86770–86771). These rows are the ones that
consume a slot against the 100-job cap while doing nothing. There is no cascade delete from class to
CronTrigger — you abort them by Id (section 4a).

### 3f. Flex queue order

```soql
SELECT Id, ApexClass.Name, Status, CreatedDate
FROM AsyncApexJob
WHERE Status = 'Holding'
  AND JobType = 'BatchApex'
ORDER BY CreatedDate ASC
```

`Holding` *"applies to batch jobs in the Apex flex queue"* (object_reference.txt L42423–42429). The
queue is FIFO — *"jobs are processed 'first-in, first-out' — in the order in which they're
submitted"* (apexdev.txt L17262–17264) — so `CreatedDate ASC` is the queue order unless someone has
reordered it. Up to 100 jobs can hold here; up to five queued or active jobs run at once
(salesforce_app_limits_cheatsheet.txt L316–319).

### 3g. Paused and errored Flow interviews

```soql
SELECT Id, InterviewLabel, InterviewStatus, CurrentElement, Error, CreatedDate
FROM FlowInterview
WHERE InterviewStatus IN ('Paused', 'Error', 'VersionPaused')
ORDER BY CreatedDate
```

`InterviewStatus` values are `Completed`, `Error`, `Paused`, `Running`, `VersionPaused`
(object_reference.txt L139956–139970). `Error` is *"The error message that explains why the flow
interview failed"* and is available in API version 62.0 and later (object_reference.txt L139907–139913).
Deleting an interview requires the **Manage Flow** user permission (object_reference.txt L139867–139868).

---

## 4. Operational Apex — anonymous window

Run these from Developer Console > Execute Anonymous, or
`sf apex run --file scripts/apex/<name>.apex --target-org <org>`.

### 4a. Abort by Id — and pick the right kind of Id

```apex
// Batch / Queueable / @future: abort by the AsyncApexJob Id.
System.abortJob('707xx0000000001');

// Scheduled Apex: abort by the CRONTRIGGER Id. An AsyncApexJob Id will not work.
System.abortJob('08exx0000000001');
```

The Apex Reference Guide is explicit: *"The jobId is the ID associated with an AsyncApexJob ID for
batch or future Apex jobs, or a CronTrigger ID for scheduled Apex jobs. You can't abort a scheduled
Apex job using an AsyncApexJob ID."* (apexrefguide.txt L238676–238680). It is equally explicit that
abort is not instant: *"If the job is currently executing, the stopped job is still visible in the
job queue... any code that is in progress will continue to execute until it completes."*
(apexrefguide.txt L238662–238664).

Bulk-abort every orphaned schedule found by query 3e:

```apex
List<CronTrigger> orphans = [
    SELECT Id, CronJobDetail.Name
    FROM CronTrigger
    WHERE State = 'ERROR' OR NextFireTime = NULL
];
for (CronTrigger ct : orphans) {
    System.debug('Aborting ' + ct.CronJobDetail.Name + ' (' + ct.Id + ')');
    System.abortJob(ct.Id);
}
```

Log before you abort. Aborting removes the row you were reading.

### 4b. Reschedule — the post-deploy, post-refresh step

```apex
// Signature: public static String schedule(String jobName, String cronExpression, Object schedulableClass)
// Returns the scheduled job ID (CronTrigger ID).   apexrefguide.txt L239722-239737
String jobId = System.schedule(
    'Nightly Account Enrichment',        // jobName  -> CronJobDetail.Name
    '0 0 2 * * ?',                       // 02:00:00 every day
    new AccountEnrichmentSchedule()
);
System.debug('CronTrigger Id = ' + jobId);
```

The expression is **six or seven fields**:

```
Seconds Minutes Hours Day_of_month Month Day_of_week Optional_year
```

(apexrefguide.txt L239760). Field values and legal special characters, verbatim from the guide's
table (apexrefguide.txt L239768–239800):

| Field | Values | Special characters |
|---|---|---|
| Seconds | 0–59 | none |
| Minutes | 0–59 | none |
| Hours | 0–23 | `, - * /` |
| Day_of_month | 1–31 | `, - * ? / L W` |
| Month | 1–12 or `JAN`…`DEC` | `, - * /` |
| Day_of_week | 1–7 or `SUN`…`SAT` | `, - * ? / L #` |
| Optional_year | null or 1970–2099 | `, - * /` |

Worked expressions from the guide (apexrefguide.txt L239863–239870):

| Expression | Runs |
|---|---|
| `0 0 13 * * ?` | Every day at 1 PM |
| `0 0 22 ? * 6L` | Last Friday of every month at 10 PM |
| `0 0 10 ? * MON-FRI` | Monday through Friday at 10 AM |
| `0 0 20 * * ? 2010` | Every day at 8 PM during 2010 |

`?` means "no specific value" and is legal only in `Day_of_month` and `Day_of_week` — you set one
and `?` the other. Putting `*` in both is the single most common malformed expression.

### 4c. One-off run in N minutes — `scheduleBatch`

```apex
// public static String scheduleBatch(Database.Batchable batchable, String jobName, Integer minutesFromNow)
// minutesFromNow must be greater than zero.       apexrefguide.txt L239892-239906
String cronId = System.scheduleBatch(new AccountEnrichmentBatch(), 'Enrichment catch-up run', 30, 200);
```

Two behaviours worth knowing before you use it (apexrefguide.txt L239914–239925):
- the job lands *at the end of the flex queue* when the schedule fires, not at the front;
- *"All scheduled Apex limits apply for batch jobs scheduled using System.scheduleBatch. After the
  batch job is queued (with a status of Holding or Queued), all batch job limits apply and the job no
  longer counts toward scheduled Apex limits."* — so it borrows one of the 100 scheduled-Apex slots
  only until it starts.

### 4d. Jump the flex queue for one urgent job

```apex
Id urgentJobId = Database.executeBatch(new HighPriorityBatchClass(), 200);
Boolean moved = System.FlexQueue.moveJobToFront(urgentJobId);
System.debug('Moved to front: ' + moved);
```

Pattern taken from the FlexQueue class example (apexrefguide.txt L215723–215727). The other three
methods are `moveAfterJob(jobToMoveId, jobInQueueId)`, `moveBeforeJob(jobToMoveId, jobInQueueId)` and
`moveJobToEnd(jobId)`; each returns `false` when the job is already in that position and throws an
element-not-found exception when either job is not in the queue (apexrefguide.txt L215744–215762).

> *"As best practice and for safe usage, a FlexQueue reorder method must be the final statement in a
> transaction."* (apexrefguide.txt L215711–215712)

Setup equivalent: **Setup > Apex Flex Queue** (apexdev.txt L17255–17256).

### 4e. How much daily async budget is left

```apex
System.OrgLimits.Limit async = OrgLimits.getMap().get('DailyAsyncApexExecutions');
System.debug(async.getValue() + ' used of ' + async.getLimit());
```

The cheat sheet names this limit and this exact check: the cap is *"250,000 or the number of
applicable user licenses in your org multiplied by 200, whichever is greater"*, it is the
`DailyAsyncApexExecutions` org limit, and *"To check how many asynchronous Apex executions are
available, make a request to REST API limits resource or use Apex methods OrgLimits.getAll() or
OrgLimits.getMap()"* (salesforce_app_limits_cheatsheet.txt L261–265, L363–366).

---

## 5. The scheduling registry

The platform stores schedules as data and gives you no owner, no runtime budget, no dependency and no
alert routing. Keep them in the repo. `scripts/check_batch_job_scheduling_and_monitoring.py` lints
this file.

Save as `config/scheduled-jobs-registry.yaml` (any `*scheduled-jobs-registry.y*ml` path under the
manifest dir is found by the checker):

```yaml
# Every recurring job in this org. One entry per CronTrigger you expect to exist.
# The checker enforces: unique name, 6- or 7-field cron, owner, window, alert_channel.
jobs:
  - name: Nightly Account Enrichment
    apex_class: AccountEnrichmentSchedule
    cron: "0 0 2 * * ?"
    owner: integration-ops@example.com
    window: "02:00-03:30"
    depends_on: none
    max_runtime_minutes: 90
    alert_channel: "#sfdc-batch-alerts"

  - name: Nightly Territory Recalculation
    apex_class: TerritoryRecalcSchedule
    cron: "0 45 3 * * ?"
    owner: sales-ops@example.com
    window: "03:45-05:00"
    depends_on: Nightly Account Enrichment
    max_runtime_minutes: 75
    alert_channel: "#sfdc-batch-alerts"

  - name: Monthly Entitlement Sweep
    apex_class: EntitlementSweepSchedule
    cron: "0 0 22 ? * 6L"
    owner: service-ops@example.com
    window: "22:00-23:30"
    depends_on: none
    max_runtime_minutes: 60
    alert_channel: "#sfdc-service-ops"

  - name: Batch Failure Sweep
    apex_class: AsyncJobFailureSweep
    cron: "0 30 7 * * ?"
    owner: integration-ops@example.com
    window: "07:30-07:45"
    depends_on: none
    max_runtime_minutes: 5
    alert_channel: "#sfdc-batch-alerts"
```

Field meanings the platform will not infer for you:

| Key | Why it is in the file |
|---|---|
| `name` | Must match `CronJobDetail.Name` exactly, or query 3d cannot reconcile registry to org |
| `apex_class` | The `Schedulable` class; lets the checker flag classes with no schedule and schedules with no class |
| `cron` | The argument you pass to `System.schedule()` when rebuilding the org |
| `owner` | Who is paged. `CronTrigger.OwnerId` records who *created* the schedule, which is rarely the same person |
| `window` | The agreed runtime envelope; overlapping windows on the same class produce `BLOCKED` (gotcha 7) |
| `depends_on` | Encodes ordering the cron expressions only imply |
| `max_runtime_minutes` | The threshold that turns "still Processing" into an alert |
| `alert_channel` | Where the failure goes when nobody is reading the batch-owner's inbox (gotcha 5) |

Run the linter:

```bash
python3 scripts/check_batch_job_scheduling_and_monitoring.py --manifest-dir ../../../
```

---

## 6. The alerting recipe

Nothing on the platform emails you when a batch job completes with `NumberOfErrors > 0`. Wire one of
these, and pick based on who has to act.

| Recipe | Build it when | Cross-reference |
|---|---|---|
| `finish()` sends the email | The batch class is yours to change and one team owns it | SKILL.md "Failure Notification via finish()" |
| Scheduled Flow → Apex invocable sweep (section 2b) | Many classes, some owned by managed packages you cannot edit | `flow/scheduled-flows` for the Flow shape; `apex/scheduled-apex-failure-detection-and-monitoring` for the invocable |
| `BatchApexErrorEvent` subscriber | You need per-chunk failure detail, not a completion summary | `apex/scheduled-apex-failure-detection-and-monitoring` — out of scope for this admin skill |

The sweep is the one recipe that catches the case the other two miss: a job that **never started**.
A `finish()` handler cannot fire for a run that did not happen, and no platform event is published
for a schedule that silently stopped existing. Query 3d plus the registry from section 5 is the only
thing that notices the absence.

<!-- UNVERIFIED (2026-09-04): whether AsyncApexJob can be used as a report type / support a report
     subscription is not stated in any of the extracted guides consulted here (object_reference.txt,
     api_meta.txt, apexdev.txt, apexrefguide.txt). The scheduled-Flow-plus-invocable recipe is
     recommended instead precisely because it rests only on grounded behaviour. Do not promise the
     user a report subscription on AsyncApexJob without confirming it in the target org. -->

**Report-subscription alternative — UNVERIFIED (2026-09-04):** the extracted guides do not state
whether `AsyncApexJob` is available as a report type, so a report subscription on failed jobs cannot
be confirmed from source here. Verify in the target org before promising it; use the sweep otherwise.

---

## 7. Deploy-order note

Order matters in one direction only:

1. Deploy the `ApexClass` / `Flow`.
2. **Then** create the schedule (`System.schedule`, Setup > Schedule Apex, or the Flow's own
   `<schedule>` element).

Reversing it is not possible, and updating a class that already has a live schedule is blocked:
*"If you attempt to deploy changes to a class or its dependent code when the class is scheduled for
execution, you see the error `This schedulable class has jobs pending or in progress - CronTrigger IDs
(ids)`"* (apexdev.txt L16990–16991). The guide's own recommendation is to *"first delete the scheduled
job, and then deploy your changes. After deployment, create a new scheduled job with the updated
class."* (apexdev.txt L16993–16995) — which is exactly the abort (4a) → deploy (2) → reschedule (4b)
sequence, driven off the registry in section 5. The bypass exists (Setup > Deployment Settings,
"allowing deployments with Apex jobs") but the guide warns *"be aware that the job can fail"*
(apexdev.txt L16992–16993).
