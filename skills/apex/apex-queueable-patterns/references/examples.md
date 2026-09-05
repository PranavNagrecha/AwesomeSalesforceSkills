# Examples — Apex Queueable Patterns

## Example 1: Bounded Multi-Step Chain With Stack Depth Guard

**Context:** An integration must push a large set of Account records to an external system in sequential batches of 50. Sending all records in one async job risks heap limits. A chained Queueable solution is chosen, but the team needs to prevent an unbounded chain if the termination condition is never met.

**Problem:** Without a stack depth guard, a bug in the termination check (or unexpected data) causes perpetual re-enqueueing that floods the org's async queue and saturates job limits.

**Solution:**

```apex
public class AccountSyncJob implements Queueable, Database.AllowsCallouts {

    private final List<Id> accountIds;
    private final Integer batchStart;
    private static final Integer BATCH_SIZE = 50;
    private static final Integer MAX_DEPTH = 10;

    public AccountSyncJob(List<Id> accountIds, Integer batchStart) {
        this.accountIds = accountIds;
        this.batchStart = batchStart;
    }

    public void execute(QueueableContext ctx) {
        // Attach Finalizer before any code that could fail
        System.attachFinalizer(new AccountSyncFinalizer(accountIds, batchStart));

        Integer end = Math.min(batchStart + BATCH_SIZE, accountIds.size());
        List<Id> slice = new List<Id>();
        for (Integer i = batchStart; i < end; i++) {
            slice.add(accountIds[i]);
        }

        // Do the callout work for this slice
        pushToExternalSystem(slice);

        // Chain only if more records remain and depth is safe
        if (end < accountIds.size()) {
            Integer depth = System.AsyncInfo.getCurrentQueueableStackDepth();
            if (depth < MAX_DEPTH) {
                AsyncOptions opts = new AsyncOptions();
                opts.MaximumQueueableStackDepth = MAX_DEPTH;
                System.enqueueJob(new AccountSyncJob(accountIds, end), opts);
            } else {
                // Log or fire a Platform Event — human intervention needed
                insert new Error_Log__c(
                    Message__c = 'AccountSyncJob reached max depth at index ' + end,
                    Job_Id__c = ctx.getJobId()
                );
            }
        }
    }

    private void pushToExternalSystem(List<Id> ids) {
        // HttpRequest / callout logic here
    }
}
```

**Why it works:** `System.AsyncInfo.getCurrentQueueableStackDepth()` returns the live depth within the chain. `AsyncOptions.MaximumQueueableStackDepth` enforces the cap at the platform level. The Finalizer is attached first so failure handling is guaranteed even if `pushToExternalSystem` throws. These three constructs together make the chain safe for production use. (Apex Developer Guide — Queueable Apex; Apex Reference Guide — AsyncInfo Class)

---

## Example 2: Finalizer-Based Retry For Transient Callout Failures

**Context:** An order fulfillment job calls a third-party shipping API. The API is occasionally unavailable for 30–60 seconds. The team wants automatic retry up to 3 times before writing a failure record for manual intervention.

**Problem:** Wrapping the callout in a `try/catch` and re-enqueueing from inside `catch` only handles caught exceptions. Platform-level limit exceptions or system terminations bypass the `catch` block entirely and leave no cleanup.

**Solution:**

```apex
public class FulfillmentCalloutJob implements Queueable, Database.AllowsCallouts {

    private final Id orderId;
    private final Integer retryCount;
    private static final Integer MAX_RETRIES = 3;

    public FulfillmentCalloutJob(Id orderId, Integer retryCount) {
        this.orderId = orderId;
        this.retryCount = retryCount;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new FulfillmentFinalizer(orderId, retryCount));

        // Perform the callout — any exception here is caught by the Finalizer
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ShippingAPI/fulfill');
        req.setMethod('POST');
        req.setBody('{"orderId":"' + orderId + '"}');
        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200) {
            throw new CalloutException('Unexpected status: ' + res.getStatusCode());
        }

        // Update order on success
        update new Order__c(Id = orderId, Status__c = 'Submitted');
    }
}

public class FulfillmentFinalizer implements System.Finalizer {

    private final Id orderId;
    private final Integer retryCount;
    private static final Integer MAX_RETRIES = 3;

    public FulfillmentFinalizer(Id orderId, Integer retryCount) {
        this.orderId = orderId;
        this.retryCount = retryCount;
    }

    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() == ParentJobResult.SUCCESS) {
            return; // Nothing to do — parent succeeded
        }

        // Parent failed — decide whether to retry
        if (retryCount < MAX_RETRIES) {
            System.enqueueJob(new FulfillmentCalloutJob(orderId, retryCount + 1));
        } else {
            // Max retries exhausted — write failure record
            insert new Order_Failure__c(
                Order__c = orderId,
                Failure_Reason__c = ctx.getException()?.getMessage(),
                Retry_Count__c = retryCount
            );
        }
    }
}
```

**Why it works:** The Finalizer runs in its own transaction regardless of how the parent ended — caught exception, uncaught exception, or platform termination. `ctx.getResult()` and `ctx.getException()` give the Finalizer full context about what happened. The retry counter is passed through constructor fields, which survive serialization across async transactions. (Apex Developer Guide — Transaction Finalizers)

---

## Anti-Pattern: Enqueuing Two Children From One Execute

**What practitioners do:** A Queueable finishes a processing step and tries to kick off two parallel follow-up jobs by calling `System.enqueueJob()` twice inside `execute()`.

```apex
public void execute(QueueableContext ctx) {
    processRecords();
    System.enqueueJob(new NotificationJob(recordIds));   // succeeds
    System.enqueueJob(new ArchiveJob(recordIds));        // throws LimitException!
}
```

**What goes wrong:** The second `System.enqueueJob()` call throws `System.LimitException: Too many queueable jobs added to the queue: 2`. This exception propagates up and the entire `execute()` transaction is rolled back, meaning neither child is enqueued and any DML from `processRecords()` is also rolled back.

**Correct approach:** A Queueable may enqueue exactly one child. For fan-out, use a Platform Event published from the Queueable and handle each branch in separate trigger-based Queueables, or use Batch Apex with `finish()` dispatching. (Apex Developer Guide — Queueable Apex — Limits)

---

## Example 3: Diagnosing A Chain That Reports `Completed` And Changed Nothing

**Context:** An overnight Queueable chain shows every link `Completed` with
`NumberOfErrors = 0`, and the target field is still stale on most records. The
on-call engineer has a job Id and nothing else.

**Problem:** `Completed` means the transaction ended without an unhandled
exception. It does not mean the work was done — a `return` on a guard path, an
`update` on an empty list, or a chain that stopped one link early all produce
exactly this signature.

**The diagnostic sequence.** Run these in order; the first one that disagrees
with expectation is the answer.

```soql
-- 1. How many links actually ran, and did the chain reach its terminal link?
--    Four rows at CHUNK_SIZE 200 means 800 records were in scope.
SELECT Id, ApexClass.Name, Status, NumberOfErrors, ExtendedStatus,
       CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE JobType = 'Queueable'
  AND ApexClass.Name = 'RecalculateAccountRollupQueueable'
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate ASC

-- 2. Did a link hit the depth cap? The job logs this itself; the platform does not.
SELECT Id, Severity__c, Message__c, Request_Id__c, CreatedDate
FROM Application_Log__c
WHERE Source__c = 'RecalculateAccountRollupQueueable'
  AND Severity__c IN ('WARN', 'ERROR')
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate ASC

-- 3. How much async headroom was left? A chain that ran out of 24-hour async
--    capacity stops without an error on the last successful link.
SELECT Id, Status, JobType, CreatedDate
FROM AsyncApexJob
WHERE CreatedDate = LAST_N_DAYS:1
  AND Status IN ('Queued', 'Processing')
```

Do not add `Status = 'Holding'` to any of these. That status *"applies to batch
jobs in the Apex flex queue"* (`object_reference` L42423-42429) and a Queueable
never occupies the flex queue. Likewise `JobItemsProcessed` and `TotalJobItems`
are always zero for this job type (`apexdev` L16012-16013), so neither can tell
you how far a link got.

**The instrumentation that makes step 2 possible** — a terminal path that says so
rather than returning quietly:

```apex
if (!hasDepthHeadroom()) {
    ApplicationLogger.warn(
        'RecalculateAccountRollupQueueable',
        'Depth cap ' + MAX_DEPTH + ' reached at depth ' + depth
            + ' with ' + remaining.size() + ' Account Ids unprocessed. '
            + 'First unprocessed Id: ' + remaining[0]
    );
    ApplicationLogger.flush();
    return;
}
```

**Why it works:** the platform records that a job ended, not what it decided. The
only durable evidence of a guard firing is the row the guard writes, and
`FinalizerContext.getRequestId()` — shared by the Queueable and its Finalizer
(`apexdev` L16330-16334) — is the column that joins that row back to the job and
to Event Monitoring. A chain without this instrumentation cannot be diagnosed
after the debug logs have rolled off; it can only be re-run and watched.
