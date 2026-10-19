# Examples — Batch Data Cleanup Patterns

## Example 1: Nightly Job Deleting Debug Log Records Older Than 30 Days

**Context:** An org uses a custom object `Integration_Debug_Log__c` to capture raw payloads from inbound REST integrations. Logs must be retained for 30 days for troubleshooting but must be purged after that to control data storage. Volume reaches approximately 50,000 records per day.

**Problem:** Without a scheduled cleanup, the object accumulates millions of records over months, using data storage and slowing SOQL queries against the object. A manual Data Loader delete leaves records restorable in the Recycle Bin for 15 days, where queries still have to skip them.

**Solution:**

```apex
// Batch class — delete logs older than 30 days and immediately empty recycle bin
public class DebugLogCleanupBatch implements Database.Batchable<SObject>, Database.Stateful {

    private Integer deletedCount = 0;
    private Integer failureCount = 0;

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Rolling 30-day cutoff, bound as a Date rather than a date literal
        Date cutoff = Date.today().addDays(-30);
        return Database.getQueryLocator(
            [SELECT Id FROM Integration_Debug_Log__c WHERE CreatedDate < :cutoff]
        );
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // allOrNone = false: a bad record does not roll back the whole chunk
        Database.DeleteResult[] results = Database.delete(scope, false);
        List<Id> purge = new List<Id>();
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                purge.add(scope[i].Id);
                deletedCount++;
            } else {
                failureCount++;
            }
        }
        // Purge per chunk: emptyRecycleBin accepts at most 10,000 records per call,
        // and 50,000 logs a day would exceed that in finish().
        if (!purge.isEmpty()) {
            Database.emptyRecycleBin(purge);
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug(LoggingLevel.INFO, 'Deleted ' + deletedCount + ', failed ' + failureCount);
    }
}

// Schedulable wrapper — dispatches the batch at 2:00 AM every night
public class DebugLogCleanupScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {
        Database.executeBatch(new DebugLogCleanupBatch(), 200);
    }
}

// Register the schedule via Anonymous Apex (run once in production setup)
// Cron: seconds minutes hours day-of-month month day-of-week
// '0 0 2 * * ?' = every day at 2:00 AM
System.schedule('Nightly Debug Log Cleanup', '0 0 2 * * ?', new DebugLogCleanupScheduler());
```

**Why it works:** Each 200-record chunk is its own transaction, so millions of rows can be deleted across a run. `Database.delete(scope, false)` keeps one bad record from blocking the chunk. Purging per chunk keeps every `emptyRecycleBin` call far under its 10,000-record limit and leaves nothing restorable after the run.

---

## Example 2: Monthly Retention Job Purging Custom Object Records Older Than 7 Years

**Context:** A financial services org stores loan application records in a custom object `Loan_Application__c`. Regulatory policy requires retention for 7 years and mandates permanent deletion after that period. The object holds approximately 2 million total records; roughly 300,000 are eligible for deletion each month.

**Problem:** A manual deletion process is error-prone and not auditable. Standard delete leaves records in the Recycle Bin, which violates the "permanently deleted" requirement of the retention policy. The volume exceeds what a single Apex transaction can handle.

**Solution:**

```apex
// Batch class — purge loan applications older than 7 years with hard delete
public class LoanApplicationRetentionBatch implements Database.Batchable<SObject>, Database.Stateful {

    private Integer totalDeleted = 0;
    private Integer totalFailed = 0;
    private List<Id> failedIds = new List<Id>();

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // LAST_N_YEARS:7 is calendar-aligned (it ends Dec 31 of last year), so bind
        // an exact rolling cutoff instead.
        Date cutoff = Date.today().addYears(-7);
        return Database.getQueryLocator(
            [SELECT Id, Name FROM Loan_Application__c WHERE CreatedDate < :cutoff]
        );
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        Database.DeleteResult[] results = Database.delete(scope, false);
        List<SObject> successfulDeletes = new List<SObject>();

        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                totalDeleted++;
                successfulDeletes.add(scope[i]);
            } else {
                totalFailed++;
                failedIds.add(scope[i].Id);
                // Write failure detail to Cleanup_Error_Log__c for audit
                // (insert logic omitted for brevity)
            }
        }

        // Hard-delete each chunk immediately — permanently removes from Recycle Bin
        if (!successfulDeletes.isEmpty()) {
            Database.emptyRecycleBin(successfulDeletes);
        }
    }

    public void finish(Database.BatchableContext bc) {
        // Send compliance notification with summary
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        mail.setToAddresses(new List<String>{ 'compliance@example.com' });
        mail.setSubject('Monthly Loan Retention Job Complete');
        mail.setPlainTextBody(
            'Records deleted: ' + totalDeleted + '\n' +
            'Records failed: ' + totalFailed + '\n' +
            (totalFailed > 0 ? 'Failed IDs logged to Cleanup_Error_Log__c.' : '')
        );
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ mail });
    }
}

// Schedulable — first day of each month at 1:00 AM
public class LoanRetentionScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {
        // Batch size 200 is the default safe choice; reduce to 50-100 if cascade children are numerous
        Database.executeBatch(new LoanApplicationRetentionBatch(), 200);
    }
}

// Register via Anonymous Apex
// '0 0 1 1 * ?' = 1:00 AM on the 1st of every month
System.schedule('Monthly Loan Retention Purge', '0 0 1 1 * ?', new LoanRetentionScheduler());
```

**Why it works:** `Database.Stateful` allows `totalDeleted` and `totalFailed` counters to accumulate across all `execute()` chunks so the `finish()` summary is accurate. Calling `Database.emptyRecycleBin()` per chunk, rather than collecting all IDs until `finish()`, stays within the method's 10,000-record limit on a 300,000-record run. The compliance email in `finish()` provides an auditable notification trail.

---

## Anti-Pattern: Running Bulk Deletion Inside an Apex Trigger

**What practitioners do:** Add a `before delete` or `after insert` trigger that queries and deletes related records inline, intending to enforce a rolling retention window on every save operation.

**What goes wrong:** Triggers run in the same transaction as the originating DML. Deleting records inside a trigger immediately consumes DML row limit (10,000 rows per transaction) and CPU time from the caller's governor budget. If a user saves a record and the trigger tries to delete 10,000 aged records, the save fails with a governor limit exception. Launching a batch from the trigger instead is allowed, but the Apex guide warns to use extreme caution: bulk updates fire the trigger repeatedly, and only five batch jobs can be queued or active at once.

**Correct approach:** Move bulk deletion to a Batch Apex class scheduled via a `Schedulable` wrapper. The trigger, if needed, should only enqueue a Platform Event or set a flag — never perform bulk DML directly.
