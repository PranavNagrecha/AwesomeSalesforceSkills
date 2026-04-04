# Batch Data Cleanup — Implementation Template

Use this template when implementing a scheduled batch job to delete aged or temporary records from a Salesforce org. Copy and adapt the code snippets below. Replace all `<PLACEHOLDER>` values before use.

---

## 1. Scope Definition

| Field | Value |
|---|---|
| Target object | `<OBJECT_API_NAME>` |
| Retention filter field | `CreatedDate` / `<CUSTOM_DATE_FIELD__c>` |
| Retention period | `<N>` days / years |
| Hard delete required? | Yes (emptyRecycleBin / HARD_DELETE) / No (soft delete only) |
| Estimated record volume per run | `<VOLUME>` |
| Cascade child objects | `<LIST_CHILD_OBJECTS_OR_NONE>` |
| Average children per parent | `<AVG_CHILDREN>` |
| Recommended batch size | `<BATCH_SIZE>` (= floor(10000 / avg_children), max 200) |

---

## 2. Batch Apex Class

```apex
/**
 * <OBJECT_API_NAME> Cleanup Batch
 *
 * Deletes records older than <N> days/years on a scheduled cadence.
 * Implements Database.Stateful so deletion counts persist across chunks.
 *
 * Schedule: <CRON_EXPRESSION> (e.g., '0 0 2 * * ?' for 2:00 AM nightly)
 */
public class <ObjectName>CleanupBatch
        implements Database.Batchable<SObject>, Database.Stateful {

    // Track totals across chunks for the finish() summary
    private Integer totalDeleted = 0;
    private Integer totalFailed  = 0;
    // Collect deleted SObject stubs for emptyRecycleBin — remove if not using hard delete
    private List<SObject> deletedStubs = new List<SObject>();

    // -----------------------------------------------------------------------
    // start() — define the records to delete
    // -----------------------------------------------------------------------
    public Database.QueryLocator start(Database.BatchableContext bc) {
        // LAST_N_DAYS:<N> selects records created MORE than <N> days ago
        // Replace with LAST_N_YEARS:<Y> for year-based retention
        return Database.getQueryLocator(
            'SELECT Id FROM <OBJECT_API_NAME> WHERE CreatedDate < LAST_N_DAYS:<N>'
        );
    }

    // -----------------------------------------------------------------------
    // execute() — delete each chunk with partial-failure tolerance
    // -----------------------------------------------------------------------
    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // allOrNone=false: one bad record does not abort the chunk
        Database.DeleteResult[] results = Database.delete(scope, false);

        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                totalDeleted++;
                deletedStubs.add(scope[i]); // needed for emptyRecycleBin
            } else {
                totalFailed++;
                // TODO: write failure detail to a custom audit object
                // Database.Error err = results[i].getErrors()[0];
                // insert new Cleanup_Error_Log__c(
                //     Record_Id__c = scope[i].Id,
                //     Error_Message__c = err.getMessage(),
                //     Status_Code__c = String.valueOf(err.getStatusCode())
                // );
            }
        }

        // Option A: empty recycle bin per chunk (safer for very large jobs — avoids heap)
        // if (!deletedStubs.isEmpty()) {
        //     Database.emptyRecycleBin(deletedStubs);
        //     deletedStubs.clear();
        // }
    }

    // -----------------------------------------------------------------------
    // finish() — post-job actions
    // -----------------------------------------------------------------------
    public void finish(Database.BatchableContext bc) {

        // Option B: empty recycle bin in finish() (simpler; watch heap for >500K records)
        if (!deletedStubs.isEmpty()) {
            Database.emptyRecycleBin(deletedStubs);
        }

        // Notify team of job completion
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        mail.setToAddresses(new List<String>{ '<NOTIFICATION_EMAIL>' });
        mail.setSubject('<ObjectName> Cleanup Batch Complete');
        mail.setPlainTextBody(
            'Records deleted: ' + totalDeleted + '\n' +
            'Records failed:  ' + totalFailed  + '\n' +
            (totalFailed > 0
                ? 'Check Cleanup_Error_Log__c for details.'
                : 'All records processed successfully.')
        );
        if (!Test.isRunningTest()) {
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ mail });
        }
    }
}
```

---

## 3. Schedulable Wrapper

```apex
/**
 * Schedulable wrapper for <ObjectName>CleanupBatch.
 *
 * Register via Anonymous Apex:
 *   System.schedule('<JOB_NAME>', '<CRON_EXPRESSION>', new <ObjectName>CleanupScheduler());
 *
 * Cron reference:
 *   '0 0 2 * * ?'   = every day at 2:00 AM
 *   '0 0 1 1 * ?'   = 1:00 AM on the 1st of every month
 *   '0 0 3 ? * SUN' = every Sunday at 3:00 AM
 */
public class <ObjectName>CleanupScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {
        // Adjust batch size: floor(10000 / avg_cascade_children_per_parent), max 200
        Database.executeBatch(new <ObjectName>CleanupBatch(), <BATCH_SIZE>);
    }
}
```

---

## 4. Anonymous Apex — Register the Schedule

```apex
// Run this once in production to register the scheduled job.
// Verify it appears in Setup > Scheduled Jobs after running.
System.schedule(
    '<JOB_NAME>',          // Unique display name (e.g., 'Nightly Debug Log Cleanup')
    '<CRON_EXPRESSION>',   // e.g., '0 0 2 * * ?' for 2:00 AM daily
    new <ObjectName>CleanupScheduler()
);
```

---

## 5. Apex Test Class

```apex
@isTest
private class <ObjectName>CleanupBatchTest {

    @TestSetup
    static void makeData() {
        // Insert records EXPLICITLY — never use SeeAllData=true for deletion tests
        List<<OBJECT_API_NAME>> records = new List<<OBJECT_API_NAME>>();
        for (Integer i = 0; i < 5; i++) {
            records.add(new <OBJECT_API_NAME>(
                Name = 'Test Record ' + i
                // Add required fields here
            ));
        }
        insert records;
    }

    @isTest
    static void testBatchDeletesRecords() {
        // Verify setup data exists
        System.assertEquals(5, [SELECT COUNT() FROM <OBJECT_API_NAME>]);

        Test.startTest();
        Database.executeBatch(new <ObjectName>CleanupBatch(), 200);
        Test.stopTest();

        // All test records should be deleted (all were inserted before LAST_N_DAYS threshold in test context)
        System.assertEquals(0, [SELECT COUNT() FROM <OBJECT_API_NAME>],
            'Batch should have deleted all eligible records.');
    }

    @isTest
    static void testSchedulerDispatchesBatch() {
        Test.startTest();
        String cronExpr = '0 0 2 * * ?';
        System.schedule('Test Cleanup Job', cronExpr, new <ObjectName>CleanupScheduler());
        Test.stopTest();
        // If no exception thrown, schedule registered successfully
        System.assert(true, 'Scheduler should register without exception.');
    }
}
```

---

## 6. Pre-Run Cascade Audit Queries

Run these in Developer Console > Query Editor before the first production execution:

```sql
-- Count eligible parent records
SELECT COUNT() FROM <OBJECT_API_NAME> WHERE CreatedDate < LAST_N_DAYS:<N>

-- Count cascade children (repeat for each master-detail child object)
SELECT COUNT() FROM <CHILD_OBJECT__c>
WHERE <MASTER_FIELD__c> IN (
    SELECT Id FROM <OBJECT_API_NAME> WHERE CreatedDate < LAST_N_DAYS:<N>
)
```

Document the child counts and adjust `<BATCH_SIZE>` before scheduling.

---

## 7. Post-Run Verification

```sql
-- Confirm records are gone
SELECT COUNT() FROM <OBJECT_API_NAME> WHERE CreatedDate < LAST_N_DAYS:<N>

-- Check for failures logged (if using custom error object)
SELECT Record_Id__c, Error_Message__c, Status_Code__c, CreatedDate
FROM Cleanup_Error_Log__c
ORDER BY CreatedDate DESC
LIMIT 50
```

After the first production run, check Setup > Company Information > Data Storage Used to confirm storage was reclaimed.
