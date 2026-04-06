# Examples — Governor Limit Recovery Patterns

## Example 1: SOQL Headroom Checkpoint in a Trigger Handler Loop

**Context:** A trigger on `Opportunity` fires on bulk inserts of 200 records. Each record requires a related SOQL query to fetch account data. Without checkpoints the 101st record's query throws `LimitException` in a synchronous context.

**Problem:** The trigger processes records in a loop and issues one SOQL query per record. At 101 records the cumulative query count exceeds the 100-query synchronous limit and `System.LimitException: Too many SOQL queries: 101` is thrown. The entire transaction rolls back — all 100 previously processed records are lost and the user sees a generic error.

**Solution:**

```apex
public class OpportunityTriggerHandler {
    public void handleAfterInsert(List<Opportunity> newRecords) {
        List<Id> deferredIds = new List<Id>();

        for (Opportunity opp : newRecords) {
            // Check headroom before each per-record query
            Integer remaining = Limits.getLimitQueries() - Limits.getQueries();
            if (remaining < 3) {
                // Not enough headroom — defer this record
                deferredIds.add(opp.Id);
                continue;
            }
            // Safe to query
            Account acc = [SELECT Id, AnnualRevenue FROM Account WHERE Id = :opp.AccountId LIMIT 1];
            processWithAccount(opp, acc);
        }

        if (!deferredIds.isEmpty() && !System.isBatch() && !System.isFuture()) {
            OpportunityDeferredQueueable.enqueue(deferredIds);
        }
    }
}
```

**Why it works:** The Limits class check runs before the expensive operation. When headroom drops to 2 remaining queries, the loop stops issuing SOQL and enqueues the remaining IDs as a separate async unit of work. The 100 successfully processed records are committed. The async job runs with a fresh limit budget.

---

## Example 2: Savepoint-Guarded Parent-Child Insert

**Context:** A service class inserts a `Contract__c` parent record followed by multiple `ContractLineItem__c` child records. If the child insert fails due to DML pressure, the parent must be rolled back atomically to avoid an orphaned Contract.

**Problem:** Without a savepoint, a DML statement limit hit on the child insert leaves the parent `Contract__c` committed but with no line items. The orphaned record violates business rules and requires manual cleanup. The Id field on the in-memory parent object makes it look like the insert succeeded.

**Solution:**

```apex
public static void createContractWithLines(Contract__c contract, List<ContractLineItem__c> lines) {
    // savepoint before any DML; counts as 1 DML statement
    Savepoint sp = Database.setSavepoint();
    try {
        insert contract;

        // Check remaining DML headroom before child insert
        Integer remainingDml = Limits.getLimitDMLStatements() - Limits.getDMLStatements();
        if (remainingDml < 2) {
            Database.rollback(sp);
            // Rollback does NOT clear the Id field — must null it manually
            contract.Id = null;
            System.debug(LoggingLevel.ERROR,
                'DML budget exhausted before child insert; contract rolled back. Enqueuing for retry.');
            ContractRetryQueueable.enqueue(contract, lines);
            return;
        }

        for (ContractLineItem__c line : lines) {
            line.Contract__c = contract.Id;
        }
        insert lines;

    } catch (DmlException e) {
        Database.rollback(sp);
        contract.Id = null; // clear rolled-back Id
        throw new ContractServiceException('Contract insert rolled back: ' + e.getMessage(), e);
    }
}
```

**Why it works:** The savepoint captures the state before any DML. If the DML budget is exhausted before child insert, `Database.rollback(sp)` reverts the parent insert and the `contract.Id` is explicitly nulled to prevent downstream code from treating the record as persisted. The async retry job runs with a fresh limit context.

---

## Example 3: BatchApexErrorEvent Subscriber for Scope Retry

**Context:** A nightly batch job processes `Invoice__c` records in scopes of 200. Occasionally a scope hits an unhandled exception (external callout timeout, data integrity issue) and the scope rolls back. Operations needs automatic retry for failed scopes without manual re-runs.

**Problem:** Without `BatchApexErrorEvent` handling, failed scopes are silently dropped. The batch job's `finish()` method receives the total scope count but not the failed record IDs. Identifying and reprocessing the specific records requires manual log analysis.

**Solution:**

```apex
trigger BatchApexErrorEventHandler on BatchApexErrorEvent (after insert) {
    List<Invoice__c> toRequeue = new List<Invoice__c>();

    for (BatchApexErrorEvent evt : Trigger.new) {
        System.debug('Batch scope failure on job ' + evt.AsyncApexJobId
            + ' | ExceptionType: ' + evt.ExceptionType
            + ' | Phase: ' + evt.Phase);

        if (evt.DoesExceedJobScopeMaxLength) {
            // JobScope is truncated — cannot parse reliably
            // Fall back: re-query by job tracking field
            for (Invoice__c inv : [
                SELECT Id FROM Invoice__c
                WHERE BatchJobId__c = :evt.AsyncApexJobId
                  AND ProcessingStatus__c = 'InProgress'
            ]) {
                inv.ProcessingStatus__c = 'PendingRetry';
                toRequeue.add(inv);
            }
        } else {
            // Parse the CSV of record IDs from the event payload
            List<String> rawIds = evt.JobScope.split(',');
            for (String rawId : rawIds) {
                Id recId = (Id) rawId.trim();
                toRequeue.add(new Invoice__c(
                    Id = recId,
                    ProcessingStatus__c = 'PendingRetry'
                ));
            }
        }
    }

    if (!toRequeue.isEmpty()) {
        update toRequeue;
        // A scheduled job or the next batch run picks up PendingRetry records
    }
}
```

**Why it works:** The trigger subscribes to the platform-emitted `BatchApexErrorEvent`, which fires after a scope exception even though the scope transaction rolled back. The `DoesExceedJobScopeMaxLength` guard prevents parsing a truncated ID string that would produce invalid Ids. Records are marked for retry via a status field, and the next scheduled run picks them up automatically.

---

## Anti-Pattern: Relying on try/catch to Catch LimitException

**What practitioners do:** Wrap the entire processing loop in a `try/catch(Exception e)` block, assuming the catch block will fire when `System.LimitException` is thrown and allow graceful cleanup.

**What goes wrong:** `System.LimitException` is not catchable. When the limit is exceeded, Apex terminates the transaction immediately. The catch block is never reached. The partial work is rolled back, no cleanup runs, and the user sees a system-generated error page. Worse: if the try/catch wraps callout code, the developer assumes the callout results are safely guarded, but they are not.

**Correct approach:** Use `Limits.*` checks before the operation that would exceed the limit. Design the code so the limit is never reached — exit the loop early, enqueue remaining work, or partition the work into smaller units before hitting the limit.
