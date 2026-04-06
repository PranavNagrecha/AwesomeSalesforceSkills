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

## Anti-Pattern: Looking for Flow Scheduled Jobs in Apex Jobs

**What practitioners do:** Navigate to Setup > Apex Jobs to find a scheduled Flow that is not running, expecting to see "Schedule-Triggered Flow" entries there alongside Batch Apex jobs.

**What goes wrong:** Flow scheduled jobs (Schedule-Triggered Flow) do NOT appear in Setup > Apex Jobs. Looking here finds nothing, leading the admin to incorrectly conclude the flow was never scheduled or has no execution history.

**Correct approach:** Navigate to Setup > Scheduled Jobs to view Schedule-Triggered Flow Interviews. This view shows Flow scheduled jobs, their next fire time, and allows deletion of the schedule. For execution history of a scheduled flow, check the Flow Error Email (if error email is configured on the flow) or the custom logging if the flow writes to a custom log object.
