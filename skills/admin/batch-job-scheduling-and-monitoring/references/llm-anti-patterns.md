# LLM Anti-Patterns — Batch Job Scheduling And Monitoring

Common mistakes AI coding assistants make when generating or advising on Batch Job Scheduling And Monitoring.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating NumberOfErrors as a Record Count

**What the LLM generates:** Statements like "your batch failed because 1 record errored" when `NumberOfErrors = 1` is observed in AsyncApexJob.

**Why it happens:** LLMs interpret `NumberOfErrors` as a record-level counter by analogy with error counts in other systems. In Batch Apex, `NumberOfErrors` is a count of failed execute() CHUNKS, not records. One chunk can contain up to 200 records.

**Correct pattern:**
```
NumberOfErrors in AsyncApexJob = number of execute() method calls that threw an unhandled exception.
Each execute() processes up to [batchSize] records (default 200).
NumberOfErrors = 1 could mean up to 200 records failed in one chunk.
For record-level error tracking, log Database.SaveResult[] in execute() to a custom object.
```

**Detection hint:** Any statement mapping `NumberOfErrors` directly to a count of affected records.

---

## Anti-Pattern 2: Looking for Flow Scheduled Jobs in Apex Jobs

**What the LLM generates:** Instructions to navigate to Setup > Apex Jobs to find or diagnose a scheduled Flow's execution history.

**Why it happens:** LLMs generalize "scheduled jobs in Salesforce are in Apex Jobs" without distinguishing that Flow scheduled jobs are a different execution model that appears in a different Setup location.

**Correct pattern:**
```
Schedule-Triggered Flows appear in Setup > Scheduled Jobs, not Setup > Apex Jobs.
To find Flow scheduled job history:
1. Navigate to Setup > Scheduled Jobs
2. Look for entries with type "Schedule-Triggered Flow Interview"
For Apex-based jobs: Setup > Apex Jobs shows Batch, Scheduled Apex, Queueable, and @future.
```

**Detection hint:** Instructions directing users to "Setup > Apex Jobs" when investigating a Flow scheduled job issue.

---

## Anti-Pattern 3: Using System.abortJob() Expecting Only the Current Run to Stop

**What the LLM generates:** Instructions to call `System.abortJob(jobId)` on a Scheduled Apex job to "pause" or "stop the current run" while keeping the schedule intact.

**Why it happens:** LLMs generalize from concepts in other job schedulers (e.g., Quartz, cron) where aborting a running instance does not affect the schedule. In Salesforce, aborting a Scheduled Apex job removes the schedule definition entirely.

**Correct pattern:**
```apex
// System.abortJob() on a Scheduled Apex removes the schedule — NOT just the current run
// To abort and reschedule:
System.abortJob(jobId);
// Re-register the schedule immediately after
Id newJobId = System.schedule('MyBatch Daily', '0 0 2 * * ?', new MySchedulable());
```

**Detection hint:** Instructions that say "abort the job to stop it temporarily" without immediately following with a `System.schedule()` call to re-register.

---

## Anti-Pattern 4: Generating Batch Class Without Failure Notification

**What the LLM generates:** A complete Batch Apex class with `start()` and `execute()` methods but no `finish()` method, or a `finish()` method that is empty or only calls another batch job.

**Why it happens:** LLMs generate the minimal Batch Apex interface required by the compiler. The `finish()` method is not required for compilation and is frequently omitted or left empty, causing silent failures in production.

**Correct pattern:**
```apex
global void finish(Database.BatchableContext bc) {
    AsyncApexJob job = [SELECT NumberOfErrors, TotalJobItems, ExtendedStatus
                        FROM AsyncApexJob WHERE Id = :bc.getJobId()];
    if (job.NumberOfErrors > 0) {
        // Send alert email or write to monitoring object
        Messaging.SingleEmailMessage alert = new Messaging.SingleEmailMessage();
        alert.setToAddresses(new List<String>{'admin@example.com'});
        alert.setSubject('Batch failed: ' + job.NumberOfErrors + ' errors');
        alert.setPlainTextBody('ExtendedStatus: ' + job.ExtendedStatus);
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{alert});
    }
}
```

**Detection hint:** Any generated Batch Apex class with an empty `finish()` or a `finish()` method that does not check `NumberOfErrors`.

---

## Anti-Pattern 5: Swallowing Exceptions in execute() Without Logging

**What the LLM generates:** A Batch Apex `execute()` method with a try/catch that catches `Exception` and either silently continues or logs to `System.debug()`.

**Why it happens:** LLMs generate defensive code patterns from general programming best practices where try/catch prevents crashes. In Batch Apex, swallowing exceptions in `execute()` causes the chunk to report as "completed" with `NumberOfErrors = 0` even when records failed, making failures invisible in monitoring.

**Correct pattern:**
```apex
global void execute(Database.BatchableContext bc, List<Account> scope) {
    try {
        // processing logic
    } catch (Exception e) {
        // Write to a custom error log object — do NOT just System.debug
        insert new Batch_Error_Log__c(
            Batch_Class__c = 'MyBatch',
            Error_Message__c = e.getMessage(),
            Stack_Trace__c = e.getStackTraceString(),
            Record_Count__c = scope.size()
        );
        throw e; // Re-throw so NumberOfErrors increments correctly
    }
}
```

**Detection hint:** A try/catch in `execute()` that catches `Exception` and does not re-throw and does not write to a persistent log.
