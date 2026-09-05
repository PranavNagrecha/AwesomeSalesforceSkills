# Examples — Apex Batch Chaining

## Example 1: Simple Two-Step Chain in finish() with Flex Queue Capacity Check

**Context:** An ETL pipeline must first archive old Account records (Step 1) and then re-index a related search cache (Step 2). Both are large-volume operations that require full Batch Apex chunking.

**Problem:** Without exception handling, calling `Database.executeBatch` inside `finish()` throws a `LimitException` when the flex queue already holds its maximum of 100 jobs (`apexdev` L17238-17239) — and an unhandled exception in `finish()` "prevents the next job from being enqueued and breaks the sequence" (`apexdev` L17823-17825). The first job still reports `Completed`, so the chain reads as healthy up to the link that never started.

**Solution:**

```apex
public class ArchiveAccountsBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Name FROM Account WHERE LastModifiedDate < LAST_N_YEARS:3'
        );
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        // archive logic
        for (Account a : scope) {
            a.IsArchived__c = true;
        }
        update scope;
    }

    public void finish(Database.BatchableContext bc) {
        // Headroom check. The two ceilings are separate and must be compared
        // separately: 100 is the Holding cap (apexdev L17687), 5 is the
        // queued-or-active cap (apexdev L17686).
        Integer holding = [
            SELECT COUNT() FROM AsyncApexJob
            WHERE JobType = 'BatchApex' AND Status = 'Holding'
        ];
        if (holding >= 95) {
            ApplicationLogger.error('ArchiveAccountsBatch',
                'Flex queue Holding at ' + holding + '/100. RebuildCacheBatch not started.');
            ApplicationLogger.flush();
            return;
        }

        // The guard narrows the window; it does not close it. Between the count
        // and the call, another transaction can fill the queue — and the queue
        // "sometimes exceeds the maximum limit, resulting from parallel requests"
        // (apexdev L17251-17253). So the try/catch is the real protection.
        try {
            Id nextJobId = Database.executeBatch(new RebuildCacheBatch(), 200);
            ApplicationLogger.info('ArchiveAccountsBatch',
                'RebuildCacheBatch started as ' + nextJobId);
        } catch (Exception e) {
            ApplicationLogger.error('ArchiveAccountsBatch', e);
        } finally {
            ApplicationLogger.flush();
        }
    }
}
```

**Why it works:** The count gives the on-call team a warning before saturation; the try/catch is what actually keeps a full queue from ending the chain invisibly. The logged `nextJobId` is the only durable record that link two was requested — the platform stores no link between the two `AsyncApexJob` rows (see `gotchas.md` gotcha 9).

---

## Example 2: Queueable Coordinator for a Three-Step Chain

**Context:** A data migration pipeline has three sequential batch steps: (1) extract records from a legacy object, (2) transform and upsert to the new schema, (3) clean up the legacy staging table. Conditional logic determines whether Step 3 runs based on Step 2's error count.

**Problem:** Wiring Step 3 directly into Step 2's `finish()` and Step 2 into Step 1's `finish()` scatters all routing logic across three classes. Adding a Step 4 later requires modifying Step 3's `finish()`. Conditional skipping requires passing a boolean through constructors at every level.

**Solution — Queueable coordinator:**

```apex
public class MigrationChainCoordinator implements Queueable {

    private Integer step;
    private Integer errorCount;

    public MigrationChainCoordinator(Integer step, Integer errorCount) {
        this.step       = step;
        this.errorCount = errorCount;
    }

    public void execute(QueueableContext ctx) {
        if (step == 1) {
            Database.executeBatch(new ExtractLegacyBatch(this), 200);
        } else if (step == 2) {
            Database.executeBatch(new TransformUpsertBatch(this), 200);
        } else if (step == 3 && errorCount == 0) {
            Database.executeBatch(new CleanupLegacyBatch(), 200);
        } else {
            System.debug('MigrationChain complete. errorCount=' + errorCount);
        }
    }
}
```

Each batch class holds a reference to the coordinator and calls back from `finish()`:

```apex
public class ExtractLegacyBatch implements Database.Batchable<SObject>,
                                           Database.Stateful {
    private MigrationChainCoordinator coordinator;
    private Integer errorCount = 0;

    public ExtractLegacyBatch(MigrationChainCoordinator coord) {
        this.coordinator = coord;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Legacy_Record__c]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // extraction logic — increment errorCount on partial failures
    }

    public void finish(Database.BatchableContext bc) {
        // Hand off to coordinator for next step
        System.enqueueJob(new MigrationChainCoordinator(2, errorCount));
    }
}
```

**Why it works:** All routing lives in one coordinator class. The error count flows forward through the constructor without requiring each batch to know about the next one. Adding Step 4 means editing only `MigrationChainCoordinator.execute()`.

---

## Example 3: Reading a Broken Chain Back Out of the Org

**Context:** The nightly pipeline `ArchiveAccountsBatch → RebuildCacheBatch → NotifyIndexQueueable` reported success in the Apex Jobs UI, but the search index is a day stale. Nothing failed visibly.

**Problem:** There is no platform field that records which job started which. `AsyncApexJob.ParentJobId` links a batch job to its own internal `BatchApexWorker` rows, not to the next link (Object Reference, `AsyncApexJob.ParentJobId`). So "did link two ever start?" cannot be answered by walking a relationship — it has to be reconstructed from class name and time.

**Diagnostic sequence — run these three in order:**

```soql
-- 1. Did each link produce a job at all, and in what order?
SELECT ApexClass.Name, JobType, Status, CreatedDate, CompletedDate,
       JobItemsProcessed, TotalJobItems, NumberOfErrors, ExtendedStatus
FROM AsyncApexJob
WHERE ApexClass.Name IN ('ArchiveAccountsBatch','RebuildCacheBatch','NotifyIndexQueueable')
  AND JobType != 'BatchApexWorker'
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate ASC

-- 2. If link two is absent: was the org's flex queue full at the time?
--    Holding is measured against 100; queued/active against 5.
SELECT Status, COUNT(Id) jobs
FROM AsyncApexJob
WHERE JobType = 'BatchApex' AND CreatedDate = LAST_N_DAYS:1
GROUP BY Status

-- 3. Did any link raise an uncatchable failure? Requires the batch classes to
--    declare Database.RaisesPlatformEvents, and a subscriber that persists it.
SELECT Source__c, Severity__c, Message__c, Exception_Type__c, Request_Id__c, CreatedDate
FROM Application_Log__c
WHERE Source__c IN ('ArchiveAccountsBatch','RebuildCacheBatch','MarkChainFailure')
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate ASC
```

**How to read the result:**

| What query 1 shows | What it means | Next move |
|---|---|---|
| Link 1 `Completed`, link 2 absent | `finish()` threw before the hand-off — the job still reports `Completed` (`apexdev` L17823–17825) | Query 3 for the logged exception; add the try/catch from Example 1 |
| Link 2 present, `Status = 'Holding'` for hours | The queue is full ahead of it, not broken | Query 2; `System.FlexQueue.moveJobToFront(jobId)` to prioritise |
| Link 2 `Completed`, `NumberOfErrors > 0` | Chunks failed; the chain advanced over dirty data | `ExtendedStatus` for the first error; add the upstream-error gate (`llm-anti-patterns.md` #6) |
| Nothing at all for any link | The scheduler never fired, or the kill-switch is off | Check `CronTrigger` and `Chain_Step__mdt.Enabled__c` |

**Why the `JobType != 'BatchApexWorker'` filter is mandatory:** "For each 10,000 AsyncApexJob records, Apex creates an AsyncApexJob record of type BatchApexWorker for internal use" (`apexdev` L17755–17758). Without the filter, query 2's counts are inflated and query 1 returns rows that look like phantom extra links.
