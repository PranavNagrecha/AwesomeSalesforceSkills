# Examples — Apex Transaction Finalizers

## Example 1: Retry Queueable on Failure with Retry Count Limit

**Context:** A Queueable performs an outbound HTTP callout to an external inventory system. Transient network errors cause occasional `CalloutException`. Without a Finalizer the job fails silently and the order is never fulfilled.

**Problem:** A `try/catch` inside `execute()` can recover some exceptions but not all (e.g. governor-limit violations, certain system exceptions). The Queueable needs a guaranteed out-of-band retry mechanism that works even for unhandled exceptions.

**Solution:**

```apex
// Parent Queueable — InventoryCalloutJob.cls
public with sharing class InventoryCalloutJob implements Queueable, Database.AllowsCallouts {

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
public with sharing class InventoryCalloutFinalizer implements System.Finalizer {

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
                // Re-enqueue — the ONE async job a Finalizer may enqueue (guide L16355-16356).
                // MAX_RETRIES must stay below the platform's five consecutive
                // re-enqueues (guide L16293-16295), or the platform fails the call
                // before this class ever writes its failure record.
                System.enqueueJob(new InventoryCalloutJob(orderId, retryCount + 1));
            } else {
                // Max retries exhausted — write a permanent failure record.
                // Guarded: a Finalizer that throws has no second Finalizer, and the
                // failure appears only in the debug log (guide L16578-16587).
                try {
                    insert new Async_Job_Error__c(
                        Async_Apex_Job_Id__c = String.valueOf(ctx.getAsyncApexJobId()),
                        Record_Id__c         = orderId,
                        Error_Message__c     = ex.getMessage(),
                        Stack_Trace__c       = ex.getStackTraceString(),
                        Retry_Count__c       = retryCount
                    );
                } catch (Exception logEx) {
                    System.debug(LoggingLevel.ERROR,
                        'InventoryCalloutFinalizer: dead-letter insert failed — ' + logEx.getMessage());
                }
            }
        }
        // On SUCCESS, nothing to do
    }
}
```

**Why it works:** `System.attachFinalizer()` is registered before the callout, so even if the callout throws an unhandled exception the platform calls `InventoryCalloutFinalizer.execute()` in a transaction of its own (guide L16297). `MAX_RETRIES = 3` stops the chain on our terms rather than at the platform's fifth consecutive failure, which fails the enqueue call itself (guide L16523) and would leave no failure record at all.

---

## Example 2: Finalizer that Logs Failure to a Custom Object

**Context:** A nightly Queueable processes commission calculations. Finance needs an audit trail of every failure — job ID, error message, and which batch of records was being processed — so they can manually reprocess or escalate.

**Problem:** `System.debug()` logs are ephemeral and invisible to non-admins. The parent transaction is rolled back on failure, so any `insert` inside the Queueable itself is also rolled back.

**Solution:**

```apex
// Parent Queueable — CommissionCalcJob.cls
public with sharing class CommissionCalcJob implements Queueable {

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
public with sharing class CommissionCalcFinalizer implements System.Finalizer {

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
            Async_Apex_Job_Id__c = String.valueOf(ctx.getAsyncApexJobId()),
            Request_Id__c    = ctx.getRequestId(),
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

**What goes wrong:** a Finalizer's `execute()` is not a Queueable execution context, so the platform logs `System.attachFinalizer(Finalizer) is not allowed in this context` (Apex Developer Guide v67.0 L16543-16567) and the Finalizer terminates. UNVERIFIED (2026-09-05): the guide names the error message but not the exception type, so do not tell users to catch `System.AsyncException` here.

**Correct approach:** If you need chained guaranteed behavior, have the Finalizer enqueue a new Queueable (using the one allowed `System.enqueueJob()` slot), and attach a new Finalizer inside *that* Queueable's `execute()` method.

```apex
// WRONG — logs "System.attachFinalizer(Finalizer) is not allowed in this context"
public void execute(FinalizerContext ctx) {
    System.attachFinalizer(new AnotherFinalizer()); // fails at runtime
}

// CORRECT — enqueue a new Queueable; it attaches its own Finalizer
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        System.enqueueJob(new CompensationJob(payload)); // CompensationJob attaches its own Finalizer inside execute()
    }
}
```

---

## Example 3: One Class, Both Interfaces — Buffered Log Committed on Failure

**Context:** A nightly reconciliation Queueable walks several steps. When it dies at step 4, operations need to know that steps 1–3 succeeded. Nothing the Queueable wrote survives, because the transaction rolled back.

**Problem:** A separate logging Finalizer cannot see what the Queueable did. Passing the log through the constructor is impossible — the log does not exist yet when `attachFinalizer` runs.

**Solution:** fuse the two interfaces and mutate the Finalizer instance while the job runs. The guide's own `LoggingFinalizer` (Apex Developer Guide v67.0 L16373) is this shape, and the behaviour it depends on is stated outright: "The Finalizer framework uses the state of the Finalizer object (if attached) at the end of Queueable execution. Mutation of the Finalizer state, after it's attached, is therefore supported" (guide L16358-16359).

```apex
public with sharing class ReconciliationJob implements Queueable, Finalizer {

    // Deliberately NOT transient — transient fields "don't persist in the
    // Transaction Finalizer" (guide L16360-16362).
    private final List<Reconciliation_Step__c> steps = new List<Reconciliation_Step__c>();

    // ---- Queueable half -------------------------------------------------
    public void execute(QueueableContext ctx) {
        System.attachFinalizer(this);        // guide L16393 uses exactly this form

        step('fetch-ledger',  fetchLedger());
        step('match-payments', matchPayments());
        step('post-journal',   postJournal());   // may throw; the log above still lands
    }

    private void step(String name, Integer rowsTouched) {
        steps.add(new Reconciliation_Step__c(
            Step_Name__c   = name,
            Rows_Touched__c = rowsTouched,
            Started_At__c   = System.now()
        ));
    }

    // ---- Finalizer half -------------------------------------------------
    public void execute(FinalizerContext ctx) {
        Id parentJobId = ctx.getAsyncApexJobId();   // NOT ctx.getJobId()
        String outcome = ctx.getResult() == System.ParentJobResult.SUCCESS
            ? 'Complete'
            : 'Failed: ' + ctx.getException().getTypeName();

        for (Reconciliation_Step__c s : steps) {
            s.Async_Apex_Job_Id__c = String.valueOf(parentJobId);
            s.Request_Id__c        = ctx.getRequestId();
            s.Job_Outcome__c       = outcome;
        }
        // Partial-success insert, as the guide's logging example does (guide L16435):
        // one bad row must not take the whole audit trail with it.
        Database.insert(steps, false);
    }

    private Integer fetchLedger()   { return 0; }
    private Integer matchPayments() { return 0; }
    private Integer postJournal()   { return 0; }
}
```

**Why it works:** the two `execute` overloads are distinguished by parameter type, so one class can serve both roles. The `steps` list is populated during the Queueable transaction and read during the Finalizer transaction — legal only because the framework snapshots the Finalizer object rather than re-constructing it. The rows carry `Async_Apex_Job_Id__c`, so they join to the platform's own job record:

```soql
-- 1. the failed jobs the platform recorded
SELECT Id, Status, ExtendedStatus, CompletedDate
FROM AsyncApexJob
WHERE ApexClass.Name = 'ReconciliationJob'
  AND Status = 'Failed'
  AND CreatedDate = LAST_N_DAYS:7
ORDER BY CompletedDate DESC

-- 2. the step trail the Finalizer committed, keyed by the same job ID
SELECT Async_Apex_Job_Id__c, Step_Name__c, Rows_Touched__c,
       Job_Outcome__c, Started_At__c
FROM Reconciliation_Step__c
WHERE Async_Apex_Job_Id__c IN ('<ids from query 1>')
ORDER BY Async_Apex_Job_Id__c, Started_At__c
```

`Async_Apex_Job_Id__c` is a plain Text field, not a lookup — `AsyncApexJob` cannot be the target of a custom relationship, so the join is done by ID value in the reporting layer.

**The trap in this shape:** `getJobId()` (from `QueueableContext`) and `getAsyncApexJobId()` (from `FinalizerContext`) are both in scope in this file, twenty lines apart. The guide's own sample uses one in each half (L16380 and L16424). Reviewing this class means checking that each `execute` overload reaches for the right one.
