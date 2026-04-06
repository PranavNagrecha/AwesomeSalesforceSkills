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
