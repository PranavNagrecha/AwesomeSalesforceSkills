# Gotchas — Apex Scheduled Jobs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Scheduled Jobs Are Not Deployed by the Metadata API

**What happens:** Deploying the Schedulable Apex class via a change set, the Metadata API, or Salesforce CLI succeeds, but no active scheduled job exists in the target org afterward. The class is deployed; the `CronTrigger` record that represents the active schedule is not.

**When it occurs:** Every time a new scheduled job is introduced in a release, or when an existing job's schedule changes. Teams that treat Salesforce deployments like a traditional "deploy and done" workflow are caught off-guard when the job never runs in production.

**How to avoid:** Include a post-deployment step in every release plan that involves scheduled jobs. The standard approach is an Anonymous Apex script checked into the repository alongside the Apex class:

```apex
// deploy-scheduled-jobs.apex — run after deployment
List<CronTrigger> existing = [
    SELECT Id FROM CronTrigger
    WHERE CronJobDetail.Name = 'Nightly Lead Cleanup' AND State = 'WAITING'
    LIMIT 1
];
if (!existing.isEmpty()) {
    System.abortJob(existing[0].Id);
}
System.schedule('Nightly Lead Cleanup', '0 0 2 * * ?', new NightlyLeadCleanupScheduler());
```

For managed packages, a post-install script implementing `InstallHandler` can call `System.schedule()` automatically.

---

## Gotcha 2: The 100-Job Ceiling Counts Scheduled *Apex* Only — and Is 5 in Developer Edition

**What happens:** `System.schedule()` fails once the org already has 100 Apex classes scheduled concurrently. The Apex Developer Guide states the limit plainly: "You can only have 100 scheduled Apex jobs at one time" (apexdev L16597, restated under Apex Scheduler Limits at L16947). The App Limits cheat sheet gives the row its precise name and the edition exception: "Maximum number of Apex classes scheduled concurrently — 100. In Developer Edition orgs, the limit is 5" (salesforce_app_limits_cheatsheet L313).

**When it occurs:** In orgs that accumulate scheduled Apex over years without an inventory practice, and — far sooner than anyone expects — in Developer Edition scratch work and Trailhead orgs, where the fifth job is the last one. It also occurs when a trigger schedules a class: the guide warns to "use extreme care if you're planning to schedule a class from a trigger. You must be able to guarantee that the trigger won't add more scheduled classes than the limit" (apexdev L16601–L16603), because a 200-record bulk update can attempt 200 `System.schedule` calls in one transaction.

**How to avoid:** Count scheduled Apex *specifically*, using `CronJobDetail.JobType = '7'`. Scheduled Flows (`'6'`), report runs (`'8'`), dashboard refreshes (`'3'`), and data exports (`'1'`) are separate job types on the same `CronTrigger` table (object_reference, CronJobDetail `JobType`), so an unfiltered `SELECT COUNT() FROM CronTrigger` overstates Apex consumption and can send an audit chasing the wrong jobs:

```soql
SELECT COUNT() FROM CronTrigger
WHERE CronJobDetail.JobType = '7'
  AND State IN ('WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'PAUSED_BLOCKED', 'BLOCKED')
```

The guide names the equivalent Setup path: the Scheduled Jobs page "creating a custom view with a type filter equal to 'Scheduled Apex'" (apexdev L16598–L16600). `SchedulerAdmin.scheduledApexCount()` in `references/code-examples.md` wraps this query and throws before the platform does, with the job name in the message.

UNVERIFIED (2026-09-05): the exact exception thrown when the ceiling is hit. The guide documents the ceiling and the duplicate-name exception text but not the over-limit exception text; earlier revisions of this skill asserted `System.AsyncException: Too many jobs in the queue`, which appears in neither apexdev.txt nor apexrefguide.txt. Treat the failure as "scheduling throws", not as a specific string to match on.

---

## Gotcha 3: Synchronous Callouts From Scheduled Apex Are Unsupported, but the Batch It Dispatches May Call Out

**What happens:** A `Schedulable.execute()` that sends an HTTP request fails at run time. The class compiles and deploys cleanly, so nothing surfaces until the cron actually fires — often days after the release, in an overnight window nobody is watching. The Apex Developer Guide states the rule directly: "Synchronous Web service callouts aren't supported from scheduled Apex" (apexdev L16975).

UNVERIFIED (2026-09-05): the exact exception text. Earlier revisions of this skill asserted `System.CalloutException: Callout from scheduled Apex not supported`; that string appears in neither apexdev.txt nor apexrefguide.txt. The unsupported-ness is documented; the message is not.

**When it occurs:** When callout logic is lifted from a trigger, controller, or invocable into a scheduled job without inserting an async hop. It also occurs on the second hop: a `Schedulable` that enqueues a `Queueable` which *forgets* `Database.AllowsCallouts` fails the same way one transaction later.

**How to avoid:** The guide names two supported routes and one important exemption (apexdev L16975–L16977):

1. "To make asynchronous callouts, use Queueable Apex, implementing the `Database.AllowsCallouts` marker interface."
2. "If your scheduled Apex executes a batch job using the `Database.AllowsCallouts` marker interface, callouts are supported from the batch class."

Route 2 is the one teams miss. A `Schedulable` that dispatches `Database.executeBatch(new SyncBatch())` where `SyncBatch implements Database.Batchable<SObject>, Database.AllowsCallouts` may call out from `execute()` — no Queueable bridge is required.

```apex
public with sharing class IntegrationSyncScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        // Either of these is supported; the callout permission lives on the dispatched class.
        Database.executeBatch(new ExternalSyncBatch(), 50);   // Batch + Database.AllowsCallouts
        // System.enqueueJob(new ExternalSyncQueueable());     // Queueable + Database.AllowsCallouts
    }
}
```

Note that `Database.AllowsCallouts` on the `Schedulable` itself is not a supported route — the guide attaches the marker to the Queueable or the Batchable, never to the Schedulable.

---

## Gotcha 4: `getTriggerId()` Can Abort the Running Job — but Self-Rescheduling Inside `execute()` Is Undocumented

**What happens:** Two opposite mistakes are common here, and the guides settle only one of them.

Settled: `SchedulableContext.getTriggerId()` returns a `CronTrigger` Id that `System.abortJob` accepts. The Apex Reference Guide lists it explicitly among "the following methods return the job ID that can be passed to `abortJob`" (apexrefguide L238688–L238695), and the Developer Guide repeats it: "To stop execution of a job that was scheduled, use the `System.abortJob` method with the ID returned by the `getTriggerID` method" (apexdev L16660–L16661). A job *can* therefore retire itself — a legitimate pattern for a one-shot backfill that should disappear after it succeeds. Note that `abortJob` "stops the specified job… but any code that is in progress will continue to execute until it completes" (apexrefguide L238661–L238664), so aborting from inside `execute()` does not abort the current run.

Unsettled: whether `System.schedule()` may be called from within `execute()` to reschedule the same class. UNVERIFIED (2026-09-05): neither apexdev.txt nor apexrefguide.txt documents a restriction, and the exception text earlier revisions of this skill asserted — `System.AsyncException: Already running scheduled Apex.` — appears in neither file. Do not state it as a platform rule.

**When it occurs:** When a team wants a variable cadence — run hourly while a backlog exists, nightly otherwise — and reaches for self-rescheduling as the mechanism.

**How to avoid:** Prefer the pattern that needs no undocumented behaviour. Schedule at the *finest* cadence the requirement allows and make `execute()` decide whether there is work to do; a fixed `'0 0 * * * ?'` hourly job that returns after one cheap SOQL query costs one scheduled-Apex slot and no governor headroom, and is trivially auditable from `CronTrigger.CronExpression`. Reserve abort-and-reschedule for one-shot jobs, and run it from a Queueable dispatched by `execute()` — a separate transaction — rather than inline.

---

## Gotcha 5: Sandbox Refreshes Delete All Scheduled Jobs

**What happens:** After a sandbox refresh from production, all scheduled Apex jobs that existed in the sandbox are gone. The `CronTrigger` records are not carried over from the production snapshot. Developers who depend on scheduled jobs running in sandboxes for testing integration points or background processing are surprised when nothing runs after a refresh.

**When it occurs:** Every sandbox refresh. This affects full sandbox refreshes as well as partial and developer sandbox refreshes.

**How to avoid:** Maintain a sandbox initialization Anonymous Apex script (or a Custom Setting-driven auto-scheduler pattern) that is run immediately after each sandbox refresh. Document this step in the team's sandbox management runbook. Do not assume sandbox scheduled jobs persist; treat them as ephemeral.

---

## Gotcha 6: Duplicate Job Names Throw at Runtime, Not at Compile Time

**What happens:** Calling `System.schedule('My Job Name', cron, instance)` when a `CronTrigger` record with `CronJobDetail.Name = 'My Job Name'` already exists in `WAITING` state throws the exception the Apex Developer Guide quotes verbatim: `System.AsyncException: The Apex job named "jobName" is already scheduled for execution` (apexdev L16810–L16813). It is enforced at run time per org, not at the class level — the guide's wording is "The name for the job must be unique among the jobs scheduled for execution."

**When it occurs:** Post-deployment scripts that call `System.schedule()` without first aborting any existing job with the same name. Commonly happens when a release is run twice (e.g., a failed deployment is retried) or when multiple environments share the same deployment script without environment-specific job naming.

**How to avoid:** Always follow the abort-before-schedule pattern in deployment scripts: query for an existing job by name, abort it if found, then schedule. This is idempotent and safe to run multiple times.

Use `SchedulerAdmin.scheduleOrReplace()` from `references/code-examples.md` rather than hand-rolling the abort each time; it also refuses to schedule when the org is already at the ceiling.

---

## Gotcha 7: Scheduled Apex Runs Under *Synchronous* Governor Limits, Not Asynchronous Ones

**What happens:** Developers size `execute()` against the asynchronous column — 200 SOQL queries, 12 MB heap, 60,000 ms CPU — and get half of each. The Apex Developer Guide puts the exception in a note directly above the limits table: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (apexdev L19536; repeated in salesforce_app_limits_cheatsheet L36). So `Schedulable.execute()` gets 100 SOQL queries, 6 MB heap, and 10,000 ms CPU (apexdev L19544, L19577, L19579), the same as a Visualforce controller action.

**When it occurs:** Whenever the "it's async, so I have room" assumption is applied to a scheduler. The failure is delayed and asymmetric: a scheduler that computes a small result set in a dev sandbox at 300 ms CPU crosses 10,000 ms in production at 30× the volume, and the run dies inside an unattended overnight window with `CronTrigger.State` still reading `WAITING` for the *next* fire.

**How to avoid:** Treat 10,000 ms CPU as the budget for the dispatcher, not the work. One inexpensive guard query plus a `Database.executeBatch` or `System.enqueueJob` call is the shape that stays inside it at any data volume, because the dispatched job opens a fresh transaction with its own limits. One consolation runs the other way: because synchronous limits apply, a `Schedulable` may add up to 50 jobs with `System.enqueueJob` — the synchronous figure (apexdev L19571) — where a Queueable or Batch context is capped at 1. A master scheduler fanning out to several Queueables is therefore legal; the same code inside a Queueable is not.

---

## Gotcha 8: Member Variables Persist Across Every Future Run Unless They Are `transient`

**What happens:** A `Schedulable` instance is serialized at `System.schedule()` time and that snapshot — not a fresh object — is what runs each night. The guide is explicit: "Scheduled job objects, along with their member variables and properties, persist from initialization to subsequent scheduled runs. The object state at the time of invocation of `System.schedule()` persists in subsequent job executions" (apexdev L16984–L16986). A constructor that captures `Date.today()` therefore pins the *scheduling* date into every run for as long as the job lives.

**When it occurs:** With any parameterised scheduler — `new NightlyRollupScheduler(Date.today())`, a cached `List<Id>` of records to process, a `Map` primed in the constructor. It is invisible on day one because the snapshot is correct on day one, and it drifts silently thereafter.

**How to avoid:** The guide names the remedy: "With Scheduled Apex, use the `transient` keyword so that member variables and properties aren't persisted" (apexdev L16987–L16989). Mark every field that must be recomputed per run as `transient` and derive it inside `execute()`:

```apex
public with sharing class WindowedScheduler implements Schedulable {
    public transient Date asOfOverride;          // not serialized into the schedule

    public void execute(SchedulableContext sc) {
        Date asOf = (asOfOverride == null) ? Date.today() : asOfOverride;
        Database.executeBatch(new WindowedBatch(asOf), 200);
    }
}
```

Note the contrast with Batch Apex, where state is *opt-in* via `Database.Stateful` (apexdev L16987). Scheduled Apex inverts the default: state is kept unless you say otherwise.

---

## Gotcha 9: An Active Schedule Locks the Class *and Everything It References* Against Deployment

**What happens:** The deploy fails with `This schedulable class has jobs pending or in progress - CronTrigger IDs (ids)` (apexdev L16990–L16992). The blast radius is wider than the scheduled class: "If there are one or more active scheduled jobs for an Apex class, you can't update the class **or any classes referenced by this class** through the Salesforce user interface" (apexdev L16604–L16606). A one-line change to a shared utility class that a scheduler happens to call transitively is enough to block an unrelated release.

**When it occurs:** On any deployment touching the dependency closure of a scheduled class — which, in an org with a service/selector layer, is most of the codebase.

**How to avoid:** Abort first, deploy, reschedule — the runbook in `references/code-examples.md` §7, driven by two checked-in Anonymous Apex files so it is repeatable rather than remembered. The platform does offer a bypass: "You can bypass this error by allowing deployments with Apex jobs in the Deployment Settings page in Setup. If you enable this setting, be aware that the job can fail. Instead, we recommend that you first delete the scheduled job, and then deploy your changes. After deployment, create a new scheduled job with the updated class" (apexdev L16992–L16995). Note that the Setup-UI lock and the Metadata API lock differ: the guide states you *can* "enable deployments to update the class with active scheduled jobs by using the Metadata API" (apexdev L16606–L16608). UNVERIFIED (2026-09-05): the Deployment Settings toggle's exact label and location live on help.salesforce.com, which cannot be fetched here.

---

## Gotcha 10: Resuming a Paused Job Fires It Once Immediately, and Missed Fires Never Run

**What happens:** Scheduled Apex has no catch-up semantics. The guide states both halves: "If you resume a paused scheduled job, the job immediately runs one time. Subsequent executions of the job run according to the established schedule. Any scheduled executions that were missed while the job was paused don't run" (apexdev L16996–L16998). So a job paused across three nights does not run three times on resume — it runs once, right then, possibly in the middle of the business day it was designed to avoid.

**When it occurs:** `CronTrigger.State = 'PAUSED'` is not primarily an operator action: the Object Reference describes it as a state "a job can have… during patch and major releases. After the release has finished, the job state is automatically set to `WAITING` or another state" (object_reference, CronTrigger `State`). Seasonal release weekends are therefore the usual trigger, and the resume lands whenever the release completes.

**How to avoid:** Design every scheduled workload to be idempotent over a *window*, not over a *fire*. A rollup that recomputes "the last 24 hours" from source data is safe under both a missed fire and an unexpected midday fire; a job that increments a counter or appends to a ledger is not. Where the work genuinely cannot be re-run, gate on a high-water-mark record and have `execute()` compare the platform's own `CronTrigger.PreviousFireTime` against it rather than assuming last night's run happened.

---

## Gotcha 11: `BLOCKED` Protects the Scheduler From Itself, Not the Work It Dispatched

**What happens:** Teams read `CronTrigger.State = 'BLOCKED'` — "Execution of a second instance of the job is attempted while one instance is running. This state lasts until the first job instance is completed" (object_reference, CronTrigger `State`) — as an overlap guarantee for the whole workload. It is not. It guards re-entry of the `Schedulable` itself, which for a correctly thin dispatcher finishes in milliseconds. The batch or Queueable it launched runs in a *different* job with a *different* record; nothing stops tonight's dispatch from starting while last night's `AccountRollupBatch` is still `Processing`.

**When it occurs:** Whenever the dispatched job's runtime can exceed the schedule interval — a nightly batch that grows past 24 hours, or an hourly job over a backlog. It also occurs after a maintenance window: "Apex jobs scheduled to run during a Salesforce service maintenance downtime will be scheduled to run after the service comes back up… If a scheduled Apex job was running when downtime occurred, the job is rolled back and scheduled again after the service comes back up. After major service upgrades, there can be longer delays than usual for starting scheduled Apex jobs because of system usage spikes" (apexdev L16978–L16981) — so the delayed run and the next scheduled run can bunch together.

**How to avoid:** Write the guard yourself, in `execute()`, before dispatching. One SOQL against `AsyncApexJob` for in-flight jobs of the target class — `Status IN ('Holding','Preparing','Processing','Queued')` (object_reference, AsyncApexJob `Status`) — and return without dispatching if any row comes back. `NightlyRollupScheduler.isPreviousRunInFlight()` in `references/code-examples.md` is that guard. Skipping is almost always the right response: the next fire self-heals, whereas queueing a duplicate double-processes the window.

---

## Gotcha 12: The CRON Expression Is Evaluated in the *Scheduling* User's Time Zone, but the Job Runs as System

**What happens:** Two different identities are at play, and conflating them produces jobs that run at the wrong hour with the wrong data visibility.

The clock belongs to whoever ran `System.schedule()`: "The `System.schedule` method uses the user's time zone as the basis of all schedules" (apexdev L16820; apexrefguide L239773). The resulting `CronTrigger` records that decision in `TimeZoneSidKey`, "the timezone ID. For example, `America/Los_Angeles`" (object_reference, CronTrigger). A release engineer in Sydney running the post-deploy script produces a job that fires at 01:15 *Sydney* time forever, regardless of where the business is.

The permissions do not: "The scheduler runs as system — all classes are executed, whether the user has permission to execute the class or not" (apexdev L16613, restated at L16819 and for `System.scheduleBatch` at L17336). Object and field permissions of the scheduling user are not applied. Sharing is governed by the class's own declaration, and note the async-specific rule that "asynchronous Apex classes defined with `inherited sharing` always run in `with sharing` mode for asynchronous operations. Each asynchronous operation is a new entry point and the sharing mode isn't serialized" (apexdev L4935–L4936).

**When it occurs:** Every time the reschedule script is run ad hoc by whoever is doing the release, rather than by a designated identity, and every DST transition thereafter.

**How to avoid:** Name the scheduling identity in the runbook and log it — the reschedule script in `references/code-examples.md` §7 prints `UserInfo.getName()` and `UserInfo.getTimeZone().getID()` before scheduling, and the verification SOQL selects `CronTrigger.TimeZoneSidKey` so a wrong-time-zone schedule is caught at deploy time rather than at 3 a.m. Because the body runs as system with no user permissions applied, enforce CRUD/FLS explicitly in the dispatched worker — see `templates/apex/SecurityUtils.cls` — instead of relying on the running user's profile.

---

## Gotcha 13: `System.scheduleBatch` Runs Once and Then Stops Counting Against the Scheduled-Apex Ceiling

**What happens:** `System.scheduleBatch(batchable, jobName, minutesFromNow)` looks like a scheduling API but is a one-shot delay: it "schedule[s] a batch job to run once at a future time" and "doesn't require the implementation of the `Schedulable` interface" (apexdev L17293–L17296, L16939–L16943). It returns "the scheduled job ID (CronTrigger ID)" (apexdev L17314), so it produces a real `CronTrigger` row — which is why teams mistake it for a recurring schedule and then cannot find why the job never ran a second time. The interval is in **minutes from now**, not a CRON expression.

**When it occurs:** When someone wants "run this batch in an hour" and reaches for a `Schedulable` wrapper plus a computed CRON string, or conversely when someone uses `scheduleBatch` expecting recurrence.

**How to avoid:** Use `scheduleBatch` for exactly its case — a delayed single run, typically from a `finish()` method to resume work in an off-peak window (apexdev L17833–L17835; the chaining ceilings belong to `apex/apex-batch-chaining`). Know its two limit transitions, which the guide states as a note: "All scheduled Apex limits apply for batch jobs scheduled using `System.scheduleBatch`. After the batch job is queued (with a status of `Holding` or `Queued`), all batch job limits apply and the job no longer counts toward scheduled Apex limits" (apexdev L17339–L17342). It therefore occupies a scheduled-Apex slot only during the delay window. Until it starts, "you can use the returned scheduled job ID to abort the scheduled job using the `System.abortJob` method" (apexdev L17343–L17344).

```apex
// One run, 60 minutes from now. Not a recurring schedule.
String cronId = System.scheduleBatch(new AccountRollupBatch(Date.today()), 'Rollup catch-up', 60);
```
