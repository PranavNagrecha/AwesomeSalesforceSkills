# Gotchas — Batch Job Scheduling And Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Flow Scheduled Jobs Do Not Appear in Apex Jobs

**What happens:** An admin navigates to Setup > Apex Jobs looking for a Schedule-Triggered Flow that appears to not be running. The view shows no entry for the flow. The admin concludes the flow is not scheduled, but it is actually running — just visible in a different location.

**When it occurs:** Any time a Schedule-Triggered Flow's execution history is needed. Schedule-Triggered Flows appear only in Setup > Scheduled Jobs as "Schedule-Triggered Flow Interview" entries, not in Setup > Apex Jobs.

**How to avoid:** Always check Setup > Scheduled Jobs for Flow scheduled jobs. Setup > Apex Jobs only contains Apex-based async jobs (Batch, Scheduled Apex, Queueable, @future). If looking for both types, check both views.

---

## Gotcha 2: NumberOfErrors Counts Failed Chunks, Not Failed Records

**What happens:** A Batch Apex job shows `NumberOfErrors = 1` in Setup > Apex Jobs. The admin reports "one record failed." In reality, one batch chunk failed — which may have contained 1 to 200 records (depending on the batch size) all processed as a group. The actual number of failed records may be much larger.

**When it occurs:** Anyone reading `NumberOfErrors` from AsyncApexJob directly or from the Apex Jobs UI, and interpreting it as a record count.

**How to avoid:** Use `NumberOfErrors` only as an indicator that failures occurred, not as a record count. For accurate record-level failure tracking, implement `Database.SaveResult[]` processing in the `execute()` method and log each failed record explicitly to a custom object or platform event.

---

## Gotcha 3: Aborting a Scheduled Apex Job Deletes the Schedule Definition

**What happens:** Using `System.abortJob(jobId)` on a Scheduled Apex job (not a Batch Apex job) deletes both the scheduled execution AND the schedule definition. After abort, the job will NOT fire at the next scheduled time — the schedule is gone. This is different from aborting a Batch Apex job, which only cancels the current execution.

**When it occurs:** An admin aborts a Scheduled Apex job using `System.abortJob()` expecting to stop the current run and let it fire again tomorrow at the scheduled time.

**How to avoid:** After aborting a Scheduled Apex job, re-schedule it explicitly using `System.schedule()`. Document the cron expression and Schedulable class name so re-scheduling after an abort does not require code deployment. Alternatively, use `Database.executeBatch()` in a Schedulable class — abort the batch run, not the schedule.

---

## Gotcha 4: Scheduled Apex Does Not Auto-Retry on Failure

**What happens:** When a Scheduled Apex job (or the Batch Apex it invokes) fails, the schedule definition remains intact and fires at the next scheduled time. However, there is no automatic retry at the failure time. The failed execution is simply logged in AsyncApexJob with `Status='Failed'` and the next fire happens at the next cron window — which could be 24 hours later.

**When it occurs:** A batch job fails due to a transient error (e.g., external API downtime), and the team assumes it will automatically retry within minutes.

**How to avoid:** Implement failure detection in the `finish()` method. If `NumberOfErrors > 0`, send an alert or enqueue a retry Queueable. Do not rely on the schedule firing again — that may be too delayed for time-sensitive integrations. For immediate retry capability, use Platform Events to trigger a retry flow or a separate Queueable.

---

## Gotcha 5: The Full Error Text Is Emailed to Whoever Last Edited the Class

**What happens:** `ExtendedStatus` on `AsyncApexJob` holds only *"a short description of the first
error"*. The complete detail — *"along with any subsequent errors"* — is **emailed to the last user
who modified the batch class** (Object Reference, AsyncApexJob → ExtendedStatus, object_reference.txt
L42325–42333). Not the job's owner, not the scheduler, not the ops distribution list: the last
person to save the class. When that developer has changed teams or left the company, the only full
copy of the error goes to a mailbox nobody reads, and the on-call admin is left with a truncated
first-error string.

**When it occurs:** Every batch job that completes with `NumberOfErrors > 0`. It is invisible until
an incident, because the truncated `ExtendedStatus` usually looks like enough — right up to the run
where the first error is a generic `System.LimitException` and the useful detail is in error 47.

**How to avoid:** Do not treat the platform email as the alerting channel — it has an owner you do
not control. Route failures through a channel you own: the `finish()` handler, or the scheduled sweep
in `references/metadata-examples.md` section 6, writing to the `alert_channel` recorded in the
scheduling registry. Keep the registry's `owner` field as the human answer to "who is paged", since
`CronTrigger.OwnerId` records who *created* the schedule, which is a different question.

---

## Gotcha 6: A Live Schedule Blocks the Deploy of Its Own Class

**What happens:** A deploy that touches a `Schedulable` class — **or any class that class references**
— fails with `This schedulable class has jobs pending or in progress - CronTrigger IDs (ids)` (Apex
Developer Guide, Apex Scheduler, apexdev.txt L16990–16991). The deploy is rejected in full, so an
unrelated change riding in the same package fails with it. Through the Salesforce user interface the
restriction is broader still: *"If there are one or more active scheduled jobs for an Apex class, you
can't update the class or any classes referenced by this class through the Salesforce user
interface"* (apexdev.txt L16604–16606).

**When it occurs:** On any release into an org where the class is scheduled — which is every
production release after the first, because production is the org where the schedule exists.
Sandboxes usually deploy clean, so this fails first in production, at the worst moment.

**How to avoid:** Sequence it: abort by CronTrigger Id → deploy → re-run `System.schedule()` with the
expression from the registry (`references/metadata-examples.md` sections 4a, 4b, 5). The platform
does offer a bypass — Setup > Deployment Settings, "allowing deployments with Apex jobs" — but the
guide's own caveat is *"be aware that the job can fail"*, and it recommends the delete-deploy-
recreate order instead (apexdev.txt L16992–16995). A registry entry is what makes the recreate step
a 10-second paste rather than an archaeology exercise.

---

## Gotcha 7: A Job Still Running When Its Next Window Opens Goes to BLOCKED, Not to a Second Run

**What happens:** The schedule fires while the previous instance is still executing. Salesforce does
not run two copies and does not skip silently — the trigger moves to state `BLOCKED`, defined as
*"Execution of a second instance of the job is attempted while one instance is running. This state
lasts until the first job instance is completed"* (Object Reference, CronTrigger → State,
object_reference.txt L86812–86823). In Setup > Scheduled Jobs the job looks scheduled and healthy.
`NextFireTime` still shows a time. Nothing has failed. The work simply did not happen on time, and
`AsyncApexJob` has no row to show for the missed window because no job was created.

**When it occurs:** When runtime grows past the schedule interval — an hourly job that creeps to 70
minutes, or a nightly job whose volume doubled after a data load. It is a slow-onset failure: it
starts as an occasional `BLOCKED`, and by the time it is permanent the backlog is days old.

**How to avoid:** Record `max_runtime_minutes` and a `window` per job in the scheduling registry and
alert when `Processing` exceeds it — the runtime envelope is a design decision the platform will not
enforce. Query 3d in `references/metadata-examples.md` surfaces `State` directly; `BLOCKED` and
`PAUSED_BLOCKED` in that column mean overlap, not an error. Two entries in the registry sharing an
`apex_class` with overlapping `window` values is the design smell, and the checker WARNs on it.

---

## Gotcha 8: `System.schedule()` Uses the Running User's Time Zone; a Scheduled Flow Uses the Org's

**What happens:** Two jobs both specified as "2 AM" run at different times. The Apex Reference Guide
states *"The System.Schedule method uses the user's timezone for the basis of all schedules"*
(apexrefguide.txt L239764). The Metadata API Developer Guide states that a scheduled Flow's
`startTime` is *"based on the org's default time zone"* (api_meta.txt L71378–71379). An admin in
London scheduling an Apex class into a US-Pacific org pins it to 02:00 Europe/London — 18:00 the
previous day, org time — while the flow they scheduled in the same sitting runs at 02:00 Pacific.
Neither is wrong; they are answering different questions.

**When it occurs:** Whenever the person running `System.schedule()` is not in the org's default time
zone: offshore delivery teams, consultants, and anyone scheduling from a laptop that has moved. It
also re-appears at daylight-saving transitions, when the two bases shift on different dates.

**How to avoid:** Read `CronTrigger.TimeZoneSidKey` back after scheduling — it returns the timezone
ID actually recorded (for example `America/Los_Angeles`, Object Reference, CronTrigger →
TimeZoneSidKey) — and compare it against the org default before signing off. Query 3d in
`references/metadata-examples.md` includes the column for this reason. Record the intended clock in
the registry `window` field so the check has something to compare against.

---

## Gotcha 9: `Status = 'Completed'` Does Not Mean the Job Succeeded

**What happens:** A batch run finishes and reports `Status = 'Completed'`. A monitoring query
filtering on `Status = 'Failed'` returns nothing, and the dashboard is green. But the Apex Developer
Guide's own status table defines `Completed` as *"Job completed with or without failure"* and reserves
`Failed` for *"Job experienced a system failure"* (apexdev.txt L17287–17289). Ordinary data errors —
validation rules, required fields, locked rows — land as `Completed` with `NumberOfErrors > 0`. Only
a platform-level breakdown produces `Failed`.

**When it occurs:** On essentially every real batch job, because record-level failures are the normal
kind. A monitoring query written against `Status` alone has a blind spot the size of the actual
failure mode.

**How to avoid:** Never filter on `Status` alone. The correct failure predicate is
`Status = 'Failed' OR NumberOfErrors > 0` — query 3c in `references/metadata-examples.md`. Same rule
in the `finish()` handler: branch on `NumberOfErrors`, not on status. And read the count as
*batches*: *"Total number of batches with a failure. A batch is considered transactional, so any
unhandled exceptions constitute an entire failure of the batch"* (object_reference.txt L42393–42394).

---

## Gotcha 10: A Sandbox Refresh Silently Drops Every Schedule

**What happens:** *"When you refresh a sandbox, scheduled jobs from the source org aren't copied. You
must reschedule any jobs that you need in the refreshed sandbox"* (Apex Developer Guide, Apex
Scheduler, apexdev.txt L16982–16983). The classes arrive, the flows arrive, Setup > Scheduled Jobs is
empty. Nothing errors and nothing is logged — the absence of a schedule produces no `CronTrigger`
row, no `AsyncApexJob` row, and no notification. UAT then runs for a fortnight against an org where
none of the nightly automation has ever fired, and the gap is discovered in production.

**When it occurs:** Every sandbox refresh, and every fresh scratch org or new-org deploy — the same
root cause, since a schedule is org data and never travels with metadata (see
`references/metadata-examples.md` section 1).

**How to avoid:** Make rescheduling an explicit, owned step of the refresh runbook, driven from the
scheduling registry: for each entry, run `System.schedule(name, cron, new Class())` (section 4b),
then run verification query 3d and reconcile row-for-row against the registry. Anything in the
registry with no matching `CronJobDetail.Name` is a job that will not run. See
`devops/sandbox-refresh-and-templates` for the wider refresh sequence.

---

## Gotcha 11: `BatchApexWorker` Child Rows Inflate Every Job Count You Take

**What happens:** A count or roll-up over `AsyncApexJob` returns far more rows than there were job
runs. Chunked batch jobs create child records: *"For batch Apex jobs that run using chunking
implementation, multiple child jobs of type `BatchApexWorker` are created. Each of these child job
records contains the job Id of the parent Apex job that started their execution"* (Object Reference,
AsyncApexJob → ParentJobId, object_reference.txt L42401–42405). A single nightly batch can therefore
appear as dozens of rows in Setup > Apex Jobs and in any query that does not exclude the type.

**When it occurs:** On chunked batch implementations only — *"For batch Apex jobs that run using a
non-chunking implementation, child jobs aren't created"* — which is exactly why it looks
intermittent: the same query is accurate for some classes and wildly wrong for others in the same org.

**How to avoid:** Add `AND JobType != 'BatchApexWorker'` to any query that counts jobs, and use
`ParentJobId` when you deliberately want the children (queries 3a and 3b in
`references/metadata-examples.md`). Do not confuse this with `TotalJobItems` / `JobItemsProcessed`,
which count *batches within one job* — labels "Total Batches" and "Batches Processed" respectively
(object_reference.txt L42340, L42436–42438).
