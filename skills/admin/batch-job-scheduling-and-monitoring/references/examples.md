# Examples — Batch Job Scheduling And Monitoring

## Example 1: Diagnosing a Stuck Batch Job in Queued Status

**Context:** A nightly data sync batch Apex class scheduled to run at 2 AM was stuck in "Queued" status at 6 AM with no progress. The admin needed to determine if it was a limit issue or a failure.

**Problem:** The batch job appeared healthy in Setup > Apex Jobs (Status=Queued) but had been queued for 4 hours. The admin was unsure if it was waiting for resources or stuck in an error state.

**Solution:**
```soql
// Check how many Batch Apex jobs are currently in Processing state
SELECT ApexClass.Name, Status, CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
  AND Status = 'Processing'
ORDER BY CreatedDate ASC
```

Result showed 5 jobs already in Processing state. The org was at the 5-concurrent-job limit. The queued job was waiting for a slot.

The admin identified two long-running batch jobs from a different team that were processing large volumes. After they completed, the queued job automatically started.

**Why it works:** `AsyncApexJob` with `Status = 'Processing'` and `JobType = 'BatchApex'` shows exactly how many concurrent slots are occupied. The default limit of 5 is a common bottleneck. The fix was to coordinate batch timing across teams rather than escalating to Salesforce support.

---

## Example 2: Implementing Failure Notification in a Batch Class

**Context:** A batch Apex job processed nightly Account data enrichment. When it failed due to an external API being down, nobody was alerted. Admins discovered the failure the next morning when checking dashboards.

**Problem:** No failure notification was implemented in the batch class. Salesforce does not send email or create records when a batch job fails — only the status in Apex Jobs changes.

**Solution:**
```apex
global class AccountEnrichmentBatch implements Database.Batchable<sObject> {
    private static final String NOTIFY_EMAIL = 'ops-team@example.com';

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, Name FROM Account WHERE LastModifiedDate = TODAY');
    }

    global void execute(Database.BatchableContext bc, List<Account> scope) {
        // enrichment logic — may throw exceptions if external API is down
    }

    global void finish(Database.BatchableContext bc) {
        AsyncApexJob job = [
            SELECT NumberOfErrors, TotalJobItems, ExtendedStatus, CompletedDate
            FROM AsyncApexJob
            WHERE Id = :bc.getJobId()
        ];

        if (job.NumberOfErrors > 0) {
            Messaging.SingleEmailMessage alert = new Messaging.SingleEmailMessage();
            alert.setToAddresses(new List<String>{NOTIFY_EMAIL});
            alert.setSubject('[ALERT] AccountEnrichmentBatch failed: ' + job.NumberOfErrors + ' chunk errors');
            alert.setPlainTextBody(
                'Job completed with errors.\n' +
                'Chunks failed: ' + job.NumberOfErrors + ' / ' + job.TotalJobItems + '\n' +
                'Error detail: ' + (job.ExtendedStatus != null ? job.ExtendedStatus : 'See debug logs') + '\n' +
                'Completed: ' + String.valueOf(job.CompletedDate)
            );
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{alert});
        }
    }
}
```

**Why it works:** The `finish()` method is the only Salesforce-provided hook that runs after all `execute()` chunks complete. Querying `AsyncApexJob` by `bc.getJobId()` retrieves the final job state including `NumberOfErrors`. Sending an email here is the standard pattern for failure alerting when no centralized monitoring system is connected.

---

## Example 3: The Nightly Job That "Ran Fine" and Processed Nothing

**Context:** An hourly integration sync had grown from ~20 minutes to ~70 minutes as record volume
climbed. The ops dashboard, filtered on `Status = 'Failed'`, stayed green for three weeks. Downstream
reports were stale by roughly half a day.

**Problem:** Two failures were stacked and each hid the other. The schedule was firing while the
previous instance was still running, so most windows produced no job at all; and the runs that did
happen were completing with per-record errors, which do not set `Status = 'Failed'`.

**Solution:** Query the *schedule* and the *runs* separately — they answer different questions.

```soql
-- 1. The schedule. BLOCKED means a fire was attempted while an instance was still running.
SELECT CronJobDetail.Name, State, CronExpression, NextFireTime, PreviousFireTime, TimesTriggered
FROM CronTrigger
WHERE CronJobDetail.Name = 'Hourly Integration Sync'
```

```soql
-- 2. The runs. Note the failure predicate: Status alone is not enough.
SELECT ApexClass.Name, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems,
       CreatedDate, CompletedDate, ExtendedStatus
FROM AsyncApexJob
WHERE ApexClass.Name = 'IntegrationSyncBatch'
  AND JobType != 'BatchApexWorker'
  AND CreatedDate = LAST_N_DAYS:3
ORDER BY CreatedDate DESC
```

What came back, and what each column proved:

| Signal | Value observed | Reading |
|---|---|---|
| `CronTrigger.State` | `BLOCKED` | A second instance was attempted while the first was running |
| `TimesTriggered` vs elapsed hours | 31 over 72 hours | Roughly 40 of 72 windows produced no job at all |
| `AsyncApexJob.Status` | `Completed` | Which is why the `Status = 'Failed'` dashboard was green |
| `NumberOfErrors` | 4–11 per run | Ordinary record-level failures, invisible to that dashboard |
| `JobItemsProcessed` vs `TotalJobItems` | equal | Every batch was attempted; the errors were within batches |

**Why it works:** `BLOCKED` is documented as *"Execution of a second instance of the job is attempted
while one instance is running"* (Object Reference, CronTrigger → State), and the Apex Developer
Guide's batch status table defines `Completed` as *"Job completed with or without failure"*. Neither
condition raises anything. The fix was two changes and one artefact: move the schedule to every two
hours to fit the observed runtime, add a `NumberOfErrors` branch to `finish()`, and record
`max_runtime_minutes: 70` plus a two-hour `window` in the scheduling registry so the checker warns
the next time someone tightens the interval. See `references/gotchas.md` gotchas 7 and 9.

---

## Anti-Pattern: Looking for Flow Scheduled Jobs in Apex Jobs

**What practitioners do:** Navigate to Setup > Apex Jobs to find a scheduled Flow that is not running, expecting to see "Schedule-Triggered Flow" entries there alongside Batch Apex jobs.

**What goes wrong:** Flow scheduled jobs (Schedule-Triggered Flow) do NOT appear in Setup > Apex Jobs. Looking here finds nothing, leading the admin to incorrectly conclude the flow was never scheduled or has no execution history.

**Correct approach:** Navigate to Setup > Scheduled Jobs to view Schedule-Triggered Flow Interviews. This view shows Flow scheduled jobs, their next fire time, and allows deletion of the schedule. For execution history of a scheduled flow, check the Flow Error Email (if error email is configured on the flow) or the custom logging if the flow writes to a custom log object.

The programmatic equivalent — one query that answers "is *anything* scheduled, Apex or Flow", which is the question the admin actually had:

```soql
SELECT CronJobDetail.Name,
       CASE WHEN CronJobDetail.JobType = '6' THEN 'Scheduled Flow' ELSE 'Scheduled Apex' END,
       State, NextFireTime, PreviousFireTime, TimesTriggered
FROM CronTrigger
WHERE CronJobDetail.JobType IN ('6', '7')
ORDER BY CronJobDetail.JobType, NextFireTime
```

`TimesTriggered = 0` on a schedule created weeks ago is the actual smoking gun — the schedule exists
and has never fired. Route by what the row shows:

| What the query returns | What it means | Next move |
|---|---|---|
| No row at all | The flow is genuinely not scheduled | Activate the flow with a `<schedule>`, or set the schedule in Flow Builder |
| Row, `State = WAITING`, `TimesTriggered = 0`, future `NextFireTime` | Scheduled, just hasn't reached the first fire | Wait; confirm the time zone against `TimeZoneSidKey` |
| Row, `State = ERROR` | The trigger definition is broken; it will never fire | Abort it and re-create the schedule |
| Row, `NextFireTime` null | It ran and will not run again | Re-create; a one-off `Once` frequency was probably used |
| Row firing normally, but no business effect | The interviews are erroring, not the schedule | Query `FlowInterview` where `InterviewStatus = 'Error'` and read `Error` |

`CronJobDetail.JobType` code `6` is Scheduled Flow and `7` is Scheduled Apex (Object Reference,
CronJobDetail → JobType). Note that this is the *schedule*, not the run: interview-level history
lives on `FlowInterview`, and `flow/scheduled-flow-not-running-debug` covers that side.
