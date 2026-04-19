# Examples — Apex Transaction Finalizers

## Example 1: Retry Queueable on Failure with Retry Count Limit

**Context:** A Queueable performs an outbound HTTP callout to an external inventory system. Transient network errors cause occasional `CalloutException`. Without a Finalizer the job fails silently and the order is never fulfilled.

**Problem:** A `try/catch` inside `execute()` can recover some exceptions but not all (e.g. governor-limit violations, certain system exceptions). The Queueable needs a guaranteed out-of-band retry mechanism that works even for unhandled exceptions.

**Solution:**

```apex
// Parent Queueable — InventoryCalloutJob.cls
public class InventoryCalloutJob implements Queueable, Database.AllowsCallouts {

    private final Id orderId;
    private final Integer retryCount;
    private static final Integer MAX_RETRIES = 3;

    public InventoryCalloutJob(Id orderId, Integer retryCount) {
        this.orderId = orderId;
        this.retryCount = retryCount;
    }

    public void execute(QueueableContext ctx) {
        // Attach Finalizer before any code that might throw
        System.attachFinalizer(new InventoryCalloutFinalizer(orderId, retryCount));

        // ... perform callout and DML ...
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Inventory_API/orders/' + orderId);
        req.setMethod('POST');
        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            throw new CalloutException('Unexpected status: ' + res.getStatusCode());
        }
    }
}

// Finalizer — InventoryCalloutFinalizer.cls
public class InventoryCalloutFinalizer implements System.Finalizer {

    private final Id orderId;
    private final Integer retryCount;
    private static final Integer MAX_RETRIES = 3;

    public InventoryCalloutFinalizer(Id orderId, Integer retryCount) {
        this.orderId = orderId;
        this.retryCount = retryCount;
    }

    public void execute(FinalizerContext ctx) {
        // Only act if parent failed
        if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
            Exception ex = ctx.getException();

            if (retryCount < MAX_RETRIES) {
                // Re-enqueue — this is the ONE allowed enqueue from a Finalizer
                System.enqueueJob(new InventoryCalloutJob(orderId, retryCount + 1));
            } else {
                // Max retries exhausted — write a permanent failure record
                insert new Async_Job_Error__c(
                    Job_Id__c        = ctx.getJobId(),
                    Record_Id__c     = orderId,
                    Error_Message__c = ex.getMessage(),
                    Stack_Trace__c   = ex.getStackTraceString(),
                    Retry_Count__c   = retryCount
                );
            }
        }
        // On SUCCESS, nothing to do
    }
}
```

**Why it works:** `System.attachFinalizer()` is registered before the callout, so even if the callout throws an unhandled exception the platform calls `InventoryCalloutFinalizer.execute()` in a fresh transaction. The retry counter prevents an infinite loop. After `MAX_RETRIES`, a durable failure record is written for operations visibility.

---

## Example 2: Finalizer that Logs Failure to a Custom Object

**Context:** A nightly Queueable processes commission calculations. Finance needs an audit trail of every failure — job ID, error message, and which batch of records was being processed — so they can manually reprocess or escalate.

**Problem:** `System.debug()` logs are ephemeral and invisible to non-admins. The parent transaction is rolled back on failure, so any `insert` inside the Queueable itself is also rolled back.

**Solution:**

```apex
// Parent Queueable — CommissionCalcJob.cls
public class CommissionCalcJob implements Queueable {

    private final List<Id> repIds;

    public CommissionCalcJob(List<Id> repIds) {
        this.repIds = repIds;
    }

    public void execute(QueueableContext ctx) {
        // Register Finalizer FIRST — before any logic that might throw
        System.attachFinalizer(new CommissionCalcFinalizer(repIds));

        // ... expensive commission DML ...
        List<Commission__c> commissions = calculateCommissions(repIds);
        insert commissions; // might throw on validation rule, etc.
    }

    private List<Commission__c> calculateCommissions(List<Id> repIds) {
        // ... business logic ...
        return new List<Commission__c>();
    }
}

// Finalizer — CommissionCalcFinalizer.cls
public class CommissionCalcFinalizer implements System.Finalizer {

    private final List<Id> repIds;

    public CommissionCalcFinalizer(List<Id> repIds) {
        this.repIds = repIds;
    }

    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() != System.ParentJobResult.UNHANDLED_EXCEPTION) {
            return; // SUCCESS — nothing to log
        }

        Exception ex = ctx.getException();

        // Finalizer runs in a SEPARATE transaction — this insert is not rolled back
        // even though the parent's DML was.
        Async_Job_Error__c errRecord = new Async_Job_Error__c(
            Job_Id__c        = ctx.getJobId(),
            Job_Type__c      = 'CommissionCalcJob',
            Error_Message__c = ex.getMessage(),
            Stack_Trace__c   = ex.getStackTraceString(),
            Payload_JSON__c  = JSON.serialize(repIds),
            Occurred_At__c   = System.now()
        );

        try {
            insert errRecord;
        } catch (Exception insertEx) {
            // If logging itself fails, fall back to System.debug so the error
            // is at least visible in debug logs.
            System.debug(LoggingLevel.ERROR,
                'CommissionCalcFinalizer: failed to insert error record. '
                + insertEx.getMessage());
        }
    }
}
```

**Why it works:** The Finalizer executes in its own Apex transaction. The parent's rolled-back DML has no effect on this transaction's DML budget or record state. The `try/catch` around the `insert` guards against the Finalizer itself failing silently — if the insert throws, the `System.debug` ensures the error still appears in platform logs.

---

## Anti-Pattern: Attaching a Finalizer from Within a Finalizer

**What practitioners do:** They try to chain guaranteed callbacks by calling `System.attachFinalizer()` inside the Finalizer's own `execute()` method.

**What goes wrong:** The platform throws `System.AsyncException: Finalizer cannot attach another finalizer` immediately. The Finalizer execution terminates with an unhandled exception which is swallowed silently — no secondary callback fires.

**Correct approach:** If you need chained guaranteed behavior, have the Finalizer enqueue a new Queueable (using the one allowed `System.enqueueJob()` slot), and attach a new Finalizer inside *that* Queueable's `execute()` method.

```apex
// WRONG — throws AsyncException
public void execute(FinalizerContext ctx) {
    System.attachFinalizer(new AnotherFinalizer()); // throws!
}

// CORRECT — enqueue a new Queueable; it attaches its own Finalizer
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        System.enqueueJob(new CompensationJob(payload)); // CompensationJob attaches its own Finalizer inside execute()
    }
}
```
