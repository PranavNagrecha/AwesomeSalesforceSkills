# Examples — Apex Batch Chaining

## Example 1: Simple Two-Step Chain in finish() with Flex Queue Capacity Check

**Context:** An ETL pipeline must first archive old Account records (Step 1) and then re-index a related search cache (Step 2). Both are large-volume operations that require full Batch Apex chunking.

**Problem:** Without a capacity check, calling `Database.executeBatch` inside `finish()` silently enqueues the job even when the Flex Queue is near its 100-job ceiling. The second batch job sits in `Holding` status indefinitely with no alert.

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
        // Flex Queue guard: count all non-terminal batch jobs
        Integer activeAndQueued = [
            SELECT COUNT() FROM AsyncApexJob
            WHERE JobType = 'BatchApex'
            AND Status IN ('Holding', 'Queued', 'Processing', 'Preparing')
        ];

        if (activeAndQueued >= 95) {
            // Surface a visible alert — do not silently swallow the chain
            insert new Error_Log__c(
                Message__c = 'ArchiveAccountsBatch.finish(): Flex Queue at ' +
                             activeAndQueued + ' jobs. RebuildCacheBatch NOT enqueued.',
                Severity__c = 'ERROR',
                Context__c   = 'BatchChaining'
            );
            return;
        }

        // Safe to chain
        Id nextJobId = Database.executeBatch(new RebuildCacheBatch(), 200);
        System.debug('RebuildCacheBatch enqueued: ' + nextJobId);
    }
}
```

**Why it works:** The SOQL guard checks real-time Flex Queue depth before every chain call. If the queue is near saturation the chain aborts with a logged alert instead of silently dropping work. The returned `nextJobId` can be stored or monitored downstream.

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

## Anti-Pattern: Chaining Without FlexQueue Check

**What practitioners do:**

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**What goes wrong:** When the Flex Queue already holds many jobs (e.g., in a busy production org during peak load), this call enqueues the job in `Holding` status. There is no exception, no log entry, and no alert. The downstream batch step simply never runs — or runs hours later — without any notification to the owning team.

**Correct approach:** Always query `AsyncApexJob` for active and queued batch jobs before calling `Database.executeBatch` in `finish()`. If the count is above a safe threshold (typically 90–95 out of 100), log an error and abort the chain rather than proceeding silently.
