---
name: apex-scheduled-jobs
description: "Scheduling Apex classes using the Schedulable interface: implementing execute(), cron expressions, System.schedule(), monitoring CronTrigger records, job limits, and job chaining patterns. Triggers: 'run this code every night', 'schedule a class to run daily', 'nightly Apex job', 'run at 2am', 'cron expression for a daily job', 'how do I schedule Apex'. NOT for writing the Batch Apex class a schedule invokes — use apex/batch-apex-patterns. NOT for org-wide job monitoring and failure alerting in Setup — use admin/batch-job-scheduling-and-monitoring. NOT for alerting when a scheduled job fails silently — use apex/scheduled-apex-failure-detection-and-monitoring. Also covers: SchedulableContext.getTriggerId, System.abortJob, System.scheduleBatch, CronTrigger.State, CronJobDetail.JobType, TimesTriggered, NextFireTime, the 100-scheduled-Apex ceiling, the schedulable-class deploy lock, and the unschedule-deploy-reschedule runbook."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how to run an Apex class on a schedule"
  - "schedule a daily batch job in Apex using Schedulable"
  - "cron expression for weekly Apex job"
  - "how do I abort or reschedule a scheduled Apex job"
  - "scheduled Apex job not running or failing silently"
  - "query active scheduled jobs in Salesforce org"
  - "we're having issues with scheduled apex"
  - "write a Schedulable class that kicks off a batch every night"
  - "deploy blocked by this schedulable class has jobs pending or in progress"
  - "unschedule a job before deploying and reschedule it afterwards"
  - "count how many scheduled Apex jobs the org has left before 100"
  - "stop a nightly job from overlapping with the previous run"
  - "scheduled job ran at the wrong time after the release"
  - "make a scheduled Apex job run every hour on weekdays only"
  - "check whether a scheduled job actually did its work or just fired"
tags:
  - schedulable
  - scheduled-apex
  - cron
  - system-schedule
  - async-apex
  - job-management
inputs:
  - "Apex class that needs to run on a time-based schedule (or the business requirement for one)"
  - "Desired schedule frequency, time of day, and day-of-week or day-of-month targeting"
  - "Whether the job will dispatch Batch Apex, Queueable, or perform work inline"
  - "Current org scheduled job count if approaching the 100-job limit"
outputs:
  - "Schedulable Apex class implementation with correct interface and execute() signature"
  - "Valid cron expression for the target schedule"
  - "System.schedule() call for initial deployment or post-deployment manual scheduling"
  - "CronTrigger SOQL query for monitoring and audit"
  - "Guidance on abort-and-reschedule pattern, deployment considerations, and testing approach"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-09-12
---

# Apex Scheduled Jobs

Use this skill when designing, implementing, reviewing, or troubleshooting Apex classes that run on a time-based schedule using the `Schedulable` interface. The skill covers the full lifecycle: authoring, scheduling via cron expression, monitoring via `CronTrigger`, aborting, rescheduling, testing, and deployment considerations.

---

## Before Starting

Gather this context before working in this domain:

- **What is the scheduling target?** Schedulable should act as the timer and dispatcher, not the data processor. Large-volume work belongs in Batch Apex or a Queueable dispatched from `execute()`.
- **What is the org's current scheduled *Apex* count?** The ceiling is 100 Apex classes scheduled concurrently, and 5 in Developer Edition (salesforce_app_limits_cheatsheet L313; apexdev L16597). Count `CronJobDetail.JobType = '7'` only — scheduled Flows, report runs and dashboard refreshes are separate job types sharing the `CronTrigger` table.
- **Does the job need callouts?** "Synchronous Web service callouts aren't supported from scheduled Apex" (apexdev L16975). The documented routes are a `Queueable` implementing `Database.AllowsCallouts`, or — the one teams miss — a Batch class carrying the same marker, from which "callouts are supported" (apexdev L16976–L16977).
- **Who will own the schedule post-deployment, and in which time zone will they run the script?** The active job is data, not metadata, and `System.schedule` "uses the user's time zone as the basis of all schedules" (apexdev L16820). Both answers belong in the release plan, not in someone's memory.
- **Is this a sandbox refresh scenario?** "When you refresh a sandbox, scheduled jobs from the source org aren't copied. You must reschedule any jobs that you need in the refreshed sandbox" (apexdev L16982–L16983).
- **What does the class reference?** An active schedule locks the class "or any classes referenced by this class" against update (apexdev L16604) — the unschedule step has to be sequenced before the deploy of anything in that closure.

---

## Questions to Ask Before Configuring

Ask these before writing the class. Each maps to a documented platform behaviour that a plausible-looking Schedulable gets wrong; the gotcha each one defends against is named in the last column.

| Ask | Why it matters | What a good answer adds | Defends |
|---|---|---|---|
| "How long does one run take today, and what happens if run N+1 starts while run N is still going?" | `CronTrigger.State = 'BLOCKED'` guards the *scheduler* re-entering itself, not the batch it dispatched | The in-flight guard query, and a decision to skip vs. queue | Gotcha 11 |
| "If a night is missed entirely — release weekend, maintenance window — must it be made up?" | Resuming a paused job "immediately runs one time"; missed executions never run | A window-based, idempotent workload instead of a per-fire one, or an explicit high-water mark | Gotcha 10 |
| "Does the work call an external system, and from which class?" | Synchronous callouts are unsupported from scheduled Apex, but *are* supported from a dispatched Batch or Queueable carrying `Database.AllowsCallouts` | The marker interface's correct home — one hop down, not on the Schedulable | Gotcha 3 |
| "Which identity runs the reschedule script, and in which time zone?" | The CRON expression is read in the scheduling user's time zone; the job body runs as system with no user permissions applied | A named service identity in the runbook, and explicit CRUD/FLS in the worker | Gotcha 12 |
| "How many scheduled Apex jobs does this org already have, and what edition is it?" | The ceiling is 100 concurrent scheduled Apex classes — 5 in Developer Edition — and it counts `JobType = '7'` only | A pre-flight count, and a consolidation plan if the answer is near the ceiling | Gotcha 2 |
| "What does the class reference, and who else deploys those classes?" | An active schedule locks the class *and every class it references* against update | The unschedule step sequenced into the release plan, not discovered at deploy time | Gotcha 9 |
| "Does anything need to be computed per-run — a date, a record scope, a cutoff?" | Member variables are serialized at `System.schedule()` time and persist into every future run | A `transient` declaration, or the value derived inside `execute()` instead of in the constructor | Gotcha 8 |

What a proper configuration adds over just writing a Schedulable and calling `System.schedule`: the job is re-runnable after a failed release, it refuses to stack on top of itself, its schedule survives a deploy of any class in its dependency closure, and a single SOQL query tells an operator whether last night's *work* succeeded rather than only that the *timer* fired.

---

## Core Concepts

### The Schedulable Interface

A class becomes schedulable by implementing the `Schedulable` interface and defining a single `execute(SchedulableContext sc)` method. The Apex Developer Guide requires only that "The implemented method must be declared as global or public" (apexdev L16620) — `public` is the correct default, and the guide's own sample is `public with sharing class ScheduledMerge implements Schedulable` (apexdev L16628). Reserve `global` for classes that must be visible across a managed-package namespace boundary. Always declare a sharing mode explicitly, because the body runs as system with no user permissions applied.

```apex
public with sharing class MyScheduledJob implements Schedulable {
    public void execute(SchedulableContext sc) {
        // Dispatch work here — avoid heavy logic inline
        Database.executeBatch(new MyWorkBatch(), 200);
    }
}
```

`execute()` runs under **synchronous** governor limits — 100 SOQL, 6 MB heap, 10,000 ms CPU — because "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (apexdev L19536). That single sentence is the whole justification for the dispatcher pattern below.

`SchedulableContext.getTriggerId()` returns the `CronTrigger` Id for the running job. It is a valid argument to `System.abortJob` — the reference lists it among the methods returning an abortable job ID (apexrefguide L238688–L238695) — so a one-shot job can retire its own schedule. Aborting does not stop the current run: "any code that is in progress will continue to execute until it completes" (apexrefguide L238663).

### Cron Expressions

Salesforce uses six required fields plus an optional year (apexdev L16815-L16817) — so a legal expression has 6 or 7 fields, never the 5 of Unix cron:

```
Seconds  Minutes  Hours  Day_of_month  Month  Day_of_week  [Year]
```

Field ranges and legal special characters, from the Apex Developer Guide's own table (apexdev L16826–L16866):

| Field | Values | Special characters |
|---|---|---|
| Seconds | 0–59 | none |
| Minutes | 0–59 | none |
| Hours | 0–23 | `, - * /` |
| Day_of_month | 1–31 | `, - * ? / L W` |
| Month | 1–12 or `JAN`–`DEC` | `, - * /` |
| Day_of_week | 1–7 or `SUN`–`SAT` | `, - * ? / L #` |
| optional_year | null or 1970–2099 | `, - * /` |

Key rules, and where each actually comes from:
- **`?` is only legal in the two day fields.** The guide defines it as "Specifies no specific value. This option is only available for Day_of_month and Day_of_week. It's typically used when specifying a value for one and not the other" (apexdev L16879–L16881). Every example in the guide puts `?` in exactly one of them. The guide says "typically", not "must" — but a schedule with a concrete value in both day fields has no documented meaning, so treat one-`?` as the authoring rule and flag the alternative.
- **Seconds is not forced to `0`.** The range is 0–59 and the guide's own example is `'20 30 8 10 2 ?'` — 08:30:20 (apexdev L16637). What *is* capped is frequency: "Apex doesn't allow for a job to be scheduled more than once an hour" (apexdev L16923).
- **Three special characters have no Unix-cron equivalent.** `L` = last (last day of month, or last such weekday: `6L` is the last Friday); `W` = nearest weekday to a given day-of-month (`20W` on a Saturday runs the 19th; `1W` on a Saturday runs the 3rd, never the previous month); `#` = the nth weekday, written `weekday#nth`, so `2#1` is the first Monday. Definitions at apexdev L16893–L16913.
- **The expression is read in the scheduling user's time zone** (apexdev L16820), and that decision is frozen into `CronTrigger.TimeZoneSidKey`.

Common patterns:

| Schedule | Cron Expression | Source |
|---|---|---|
| Every day at 1 PM | `'0 0 13 * * ?'` | guide example, apexdev L16919 |
| Every hour at 5 past | `'0 5 * * * ?'` | guide example, apexdev L16921 — the maximum legal frequency |
| Last Friday of every month, 10 PM | `'0 0 22 ? * 6L'` | guide example, apexdev L16925 |
| Monday–Friday at 10 AM | `'0 0 10 ? * MON-FRI'` | guide example, apexdev L16927 |
| Every day at 8 PM during 2010 only | `'0 0 20 * * ? 2010'` | guide example, apexdev L16929 |
| Daily at 2:00 AM | `'0 0 2 * * ?'` | derived from the field table |
| First day of each month at midnight | `'0 0 0 1 * ?'` | derived; Day_of_week is `?` |
| Every fifth day of the month | `'0 0 2 1/5 * ?'` | derived from the `/` definition, apexdev L16887–L16891 |

Schedule during off-peak hours: the platform reserves the right to slip the start — "Salesforce schedules the class for execution at the specified time. Actual execution can be delayed based on service availability" (apexdev L16594–L16595) — and contention makes that slip larger.

### System.schedule() and the CronTrigger Object

A scheduled job is created with:

```apex
String jobId = System.schedule('Job Display Name', cronExpression, new MyScheduledJob());
```

- The first argument is the display name, stored on `CronJobDetail.Name`. It must be unique among jobs scheduled for execution; a duplicate throws `System.AsyncException: The Apex job named "jobName" is already scheduled for execution` (apexdev L16810–L16813).
- The method returns "the scheduled job ID (CronTrigger ID)" as a `String` (apexrefguide L239731–L239735) — not an `AsyncApexJob` ID. `System.abortJob` rejects an `AsyncApexJob` Id for a scheduled job (apexrefguide L238679–L238681).
- Jobs can be scheduled from Anonymous Apex, a controller, or another Apex class. Scheduling **from a trigger** carries an explicit warning: "Use extreme care… You must be able to guarantee that the trigger won't add more scheduled classes than the limit. In particular, consider API bulk updates, import wizards, mass record changes through the user interface" (apexdev L16601–L16603) — a 200-record update can attempt 200 `System.schedule` calls in one transaction.
- Whether a job may reschedule *itself* from inside `execute()` is not documented either way. See `references/gotchas.md` Gotcha 4.

Monitor active jobs with:

```soql
SELECT Id, CronJobDetail.Name, CronExpression, State, NextFireTime, PreviousFireTime
FROM CronTrigger
WHERE State = 'WAITING'
ORDER BY NextFireTime ASC
```

`CronTrigger.State` values, from the Object Reference (CronTrigger `State`): `WAITING` (awaiting execution), `ACQUIRED` (picked up, about to execute), `EXECUTING`, `COMPLETE` (fired and not scheduled again), `ERROR` (the trigger *definition* is broken), `DELETED`, `PAUSED` (set by the platform during patch and major releases, then restored automatically), `BLOCKED` (a second instance was attempted while one was running), `PAUSED_BLOCKED` (paused by a release while an instance was running).

`CronJobDetail.JobType` distinguishes what kind of job a `CronTrigger` row represents: `'7'` scheduled Apex, `'6'` scheduled Flow, `'8'` report run, `'3'` dashboard refresh, `'4'` reporting snapshot, `'9'` batch job, `'1'` data export, `'A'` reporting notification (object_reference, CronJobDetail). Filter on `'7'` or the count is wrong.

Abort a scheduled job with:

```apex
System.abortJob('CronTrigger_Id_Here');
```

### Mode Selection

This skill operates in three modes based on the practitioner's need:

- **Mode 1 — Implement:** Design and create a new scheduled job from scratch. Follow the Schedulable-as-dispatcher pattern and produce both the class and the scheduling call.
- **Mode 2 — Review/Audit:** Evaluate existing scheduled jobs in an org — query `CronTrigger`, check proximity to the 100-job limit, verify off-peak scheduling, and confirm that heavy work is delegated rather than inlined.
- **Mode 3 — Troubleshoot:** Diagnose a job that is not running, stuck in `BLOCKED` or `ERROR` state, or failing silently. Start with `CronTrigger.State`, then check `AsyncApexJob` for the most recent execution record.

---

## Common Patterns

### Schedulable as Dispatcher (Preferred Pattern)

**When to use:** Any case where the scheduled job processes records, performs DML, or does anything beyond trivial computation. This is the default pattern.

**How it works:**
1. The `Schedulable` class holds minimal state — typically a constructor parameter for scoping (e.g., record type, org-specific flag).
2. `execute()` instantiates and dispatches a Batch Apex class or enqueues a Queueable. It does not perform DML or SOQL at scale itself.
3. The Batch or Queueable carries all governor-intensive work within its own transaction limits.

```apex
public with sharing class NightlyLeadCleanupScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        Database.executeBatch(new LeadCleanupBatch(), 200);
    }
}
```

The guide gives the same shape and the same advice: "Though it's possible to do additional processing in the execute method, we recommend that all processing must take place in a separate class" (apexdev L16972–L16973). See `references/code-examples.md` §1 for the production version, which adds the in-flight guard and structured logging.

**Why not the alternative:** inline work spends *synchronous* limits — 100 SOQL, 6 MB heap, 10,000 ms CPU (apexdev L19536, L19544, L19577, L19579), which is less headroom than the Batch or Queueable you were avoiding writing. The dispatched job opens a fresh transaction and gets its own budget, so the dispatcher's footprint stays flat at any data volume.

### Self-Identifying Job for Conditional Logic

**When to use:** A single Schedulable class is reused for multiple schedules with different parameters, and the job needs to know which schedule triggered it.

**How it works:**
1. The `SchedulableContext.getTriggerId()` returns the `CronTrigger.Id`.
2. Query `CronJobDetail` from `CronTrigger` to retrieve the job name and branch logic accordingly.

```apex
public with sharing class MultiPurposeScheduler implements Schedulable {
    public void execute(SchedulableContext SC) {
        CronTrigger ct = [
            SELECT CronJobDetail.Name
            FROM CronTrigger
            WHERE Id = :SC.getTriggerId()
        ];
        if (ct.CronJobDetail.Name.contains('Nightly')) {
            Database.executeBatch(new NightlyBatch(), 200);
        } else {
            System.enqueueJob(new WeeklyReportQueueable());
        }
    }
}
```

**Why not the alternative:** Creating one Schedulable class per variation leads to class sprawl. A parameterized or self-identifying class reduces maintenance surface.

### Abort-and-Reschedule for Schedule Changes

**When to use:** The cron schedule for a live job needs to change. There is no in-place modification API.

**How it works:**
1. Query `CronTrigger` to find the job ID by name.
2. Call `System.abortJob(jobId)`.
3. Call `System.schedule(sameName, newCronExpression, new MyScheduledJob())`.

```apex
// Run from Anonymous Apex or a deployment script
List<CronTrigger> jobs = [
    SELECT Id FROM CronTrigger
    WHERE CronJobDetail.Name = 'Nightly Lead Cleanup'
    AND State = 'WAITING'
];
if (!jobs.isEmpty()) {
    System.abortJob(jobs[0].Id);
}
System.schedule('Nightly Lead Cleanup', '0 0 3 * * ?', new NightlyLeadCleanupScheduler());
```

**Why not the alternative:** Attempting to update `CronExpression` directly on the `CronTrigger` record via DML is not supported. The only path to change a schedule is abort and reschedule.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to run Apex on a fixed time-based schedule | `Schedulable` + `System.schedule()` | Purpose-built platform feature for time-based Apex |
| Job processes large record volumes | Schedulable dispatches Batch Apex | Batch provides chunked limits and automatic retry |
| Job needs to make outbound callouts | Schedulable dispatches a `Queueable` **or a Batch class** carrying `Database.AllowsCallouts` | Synchronous callouts are unsupported from scheduled Apex, but supported from either dispatched class (apexdev L16975–L16977) |
| Job schedule needs to change post-deployment | Abort existing job, schedule new one with updated cron | No in-place schedule modification API exists |
| Org is near the ceiling (100, or 5 in Developer Edition) | Consolidate into a master scheduler class | Synchronous limits apply, so one `execute()` may add up to 50 jobs with `System.enqueueJob` (apexdev L19571) |
| Job runs in multiple sandboxes or prod | Plan post-deployment Anonymous Apex script | Scheduled jobs are not Metadata API-deployable |
| Need sub-hourly firing | Re-evaluate: Platform Events, CDC, or a record-triggered path | "Apex doesn't allow for a job to be scheduled more than once an hour" (apexdev L16923) |
| Need one delayed run, not a recurrence | `System.scheduleBatch(batchable, name, minutesFromNow)` | Runs once at a future time and needs no `Schedulable` implementation (apexdev L17293–L17296) |
| Previous run may still be executing when the next fires | Guard in `execute()` on in-flight `AsyncApexJob` rows | `CronTrigger` `BLOCKED` guards the scheduler's re-entry, not the dispatched worker |
| Job errors silently and stops | Query `CronTrigger.State = 'ERROR'`, check `AsyncApexJob` | State field and job history show failure details |

---


## Recommended Workflow

1. **Confirm a schedule is the right trigger at all.** Read `standards/decision-trees/async-selection.md` — Q9 and the "Clock (cron)" branch — before writing anything. A schedule that exists only to poll for changed records is usually a record-triggered Flow or a Platform Event; a schedule that exists to run at a fixed clock time is this skill. If the work is purely declarative, `flow/scheduled-flows` and `admin/scheduled-path-patterns` own it and this skill does not apply.
2. **Answer the seven questions above, then run the pre-flight count.** `SELECT COUNT() FROM CronTrigger WHERE CronJobDetail.JobType = '7' AND State IN ('WAITING','ACQUIRED','EXECUTING','PAUSED','PAUSED_BLOCKED','BLOCKED')`. Record the number against 100 (5 in Developer Edition) in the release notes; if it is above 80, plan the consolidation before writing the class.
3. **Write the dispatcher and its worker from `references/code-examples.md`.** Copy `NightlyRollupScheduler` (thin `execute()`, `transient` per-run fields, in-flight guard against `AsyncApexJob`) and `SchedulerAdmin` (`scheduleOrReplace`, `abortByName`, `scheduledApexCount`). Reference `templates/apex/ApplicationLogger.cls` for logging and `templates/apex/SecurityUtils.cls` for CRUD/FLS in the worker — the body runs as system. Hand the worker's design to `apex/batch-apex-patterns` or `apex/apex-queueable-patterns`.
4. **Author and validate the CRON expression against the field table in Core Concepts.** Seven fields, `?` in exactly one day field, no more than once an hour. Confirm the time zone the script will run under, not the one you are sitting in.
5. **Write the test class from `references/code-examples.md` §4.** `System.schedule` inside `Test.startTest()`/`Test.stopTest()`; assert `CronExpression`, `State`, `TimesTriggered == 0`, and `NextFireTime` before `stopTest`, and the dispatched `AsyncApexJob` after it. Use a far-future CRON year and a unique job name per method.
6. **Run the checker, then the tests.** `python3 skills/apex/apex-scheduled-jobs/scripts/check_apex_scheduled_jobs.py --manifest-dir force-app/main/default/classes --strict`, then `sf apex run test --tests <YourSchedulerTest>`. The checker flags callouts in `execute()`, malformed CRON literals, unguarded `System.schedule`, and `System.schedule` outside the test bracket.
7. **Execute the runbook in order: unschedule → deploy → reschedule → verify.** `references/code-examples.md` §6–§8. Both Anonymous Apex files belong in source control next to the classes; the verification SOQL over `CronTrigger` *and* `AsyncApexJob` is the acceptance step, because a green `CronTrigger` over a failed batch is the domain's characteristic false-clean signal.

---

## Review Checklist

Run through these before marking scheduled job work complete:

- [ ] Class declares an explicit sharing mode and implements `Schedulable`; `execute` is `public` (or `global` only if it must cross a package namespace).
- [ ] `execute(SchedulableContext)` is sized for **synchronous** limits — 100 SOQL, 6 MB heap, 10,000 ms CPU.
- [ ] Any field that must be recomputed per run is `transient`, or is derived inside `execute()`.
- [ ] `execute()` refuses to dispatch when a prior run of the same worker is still in flight.
- [ ] Heavy work (SOQL at scale, DML at scale) is delegated to Batch or Queueable, not done inline.
- [ ] Cron expression has seven fields, `?` in exactly one day field, and fires no more than hourly.
- [ ] The time zone the reschedule script runs under is named in the runbook and verified on `CronTrigger.TimeZoneSidKey`.
- [ ] Job name is unique in the org — duplicate names cause a runtime `AsyncException`.
- [ ] Job is scheduled during off-peak hours.
- [ ] Scheduled-Apex count (`CronJobDetail.JobType = '7'`) is below 100 — 5 in Developer Edition — with a consolidation plan if close.
- [ ] The unschedule step is sequenced before the deploy, covering the class's whole dependency closure.
- [ ] No direct callouts in `execute()` — callouts are delegated to async contexts.
- [ ] Post-deployment scheduling script (Anonymous Apex) is prepared and documented.
- [ ] Test class brackets `System.schedule` with `Test.startTest()` / `Test.stopTest()`, uses a unique job name, and asserts `CronExpression`, `State`, `TimesTriggered`, and `NextFireTime`.
- [ ] `python3 scripts/check_apex_scheduled_jobs.py --manifest-dir <src> --strict` exits 0.
- [ ] Sandbox refresh impact is understood and post-refresh scheduling is scripted.

---

## Salesforce-Specific Gotchas

Full write-ups, with guide line cites, are in `references/gotchas.md` (13 entries). The five that most often survive review:

1. **The active job is data, not metadata.** `package.xml` deploys the class; nothing in it recreates the `CronTrigger`. Every release touching a schedule needs a post-deploy script (`references/code-examples.md` §7).
2. **The ceiling counts scheduled Apex only.** `CronJobDetail.JobType = '7'`; Developer Edition stops at 5, not 100.
3. **Synchronous limits, not asynchronous ones.** Half the SOQL, half the heap, a sixth of the CPU you would get in a Batch `execute()`.
4. **The schedule locks the class *and its references*** against deployment until the job is aborted.
5. **State is sticky.** Constructor-captured values persist into every future run unless declared `transient`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Schedulable class implementation | Correctly structured class with `global` modifier and `execute(SchedulableContext SC)` |
| Cron expression | Validated expression matching the target schedule with Day_of_month / Day_of_week handling |
| System.schedule() call | Ready-to-run statement for Anonymous Apex or post-deployment script |
| CronTrigger monitoring query | SOQL to surface active jobs, state, and next fire time |
| Abort-and-reschedule script | Anonymous Apex pattern to change an existing job's schedule |
| Test class scaffold | Unit test with `Test.startTest()` / `Test.stopTest()` and CronTrigger assertion |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building or changing a scheduled job — the complete deployable unit: `NightlyRollupScheduler`, `AccountRollupBatch`, `SchedulerAdmin`, the test class, `-meta.xml`, `package.xml`, deploy order, the unschedule → reschedule runbook, and the verification SOQL |
| `references/gotchas.md` | Something behaves unexpectedly — 13 documented platform behaviours with Apex Developer Guide / Object Reference line cites, including the deploy lock, state persistence, `BLOCKED` semantics, paused-job resume, and time-zone binding |
| `references/examples.md` | You want worked scenarios end to end — nightly cleanup dispatched to Batch, the abort-and-reschedule change, master-scheduler consolidation, and the inline-logic anti-pattern |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated Schedulable code, or self-checking your own output before proposing it |
| `references/well-architected.md` | You need the Reliability / Operational Excellence framing, the architectural trade-offs, or the official source list with the claim each supports |
| `templates/apex-scheduled-jobs-template.md` | You are running the skill as a structured engagement — context capture, CRON builder, review record |
| `scripts/check_apex_scheduled_jobs.py` | Before deploying — static checks over `.cls` files for callouts in `execute()`, malformed CRON literals, unguarded `System.schedule`, and untested schedule calls |

`scripts/check_apex_scheduled_jobs.py` is the canonical checker; `scripts/check_apex_scheduled.py` alongside it is a backward-compatible alias that delegates every argument to the canonical script and returns the same exit code — invoke either name, but cite the canonical one in new plans and tests.

---

## Related Skills

- `apex/async-apex` — use when the question is which async mechanism to choose (Schedulable vs Queueable vs Batch vs future).
- `apex/batch-apex-patterns` — use when the scheduled job needs to process large data volumes with chunked limits.
- `apex/apex-queueable-patterns` — use when the scheduled job needs to make callouts or chain async steps.
- `apex/governor-limits` — use when the scheduled job is hitting CPU, SOQL, or DML limits during execution.
- `apex/debug-and-logging` — use when diagnosing why a scheduled job failed or produced unexpected results.
- `apex/apex-batch-chaining` — use when the dispatched batch must trigger the next one from `finish()`, or when `System.scheduleBatch` is being used as a chain link rather than as a schedule.
- `apex/scheduled-apex-failure-detection-and-monitoring` — use when the job runs but nobody finds out that it failed: `BatchApexErrorEvent`, `AsyncApexJob` alerting, silent-failure modes.
- `flow/scheduled-flows` — use when the recurring work is declarative and no Apex is involved.
- `admin/scheduled-path-patterns` — use when the timing is relative to a record's own field value rather than to a wall clock.
- `admin/batch-job-scheduling-and-monitoring` — use for the Setup-side operational view of scheduled jobs across the org.
