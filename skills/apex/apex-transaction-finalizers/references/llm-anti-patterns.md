# LLM Anti-Patterns — Apex Transaction Finalizers

Common mistakes AI coding assistants make when generating or advising on Apex Transaction Finalizers.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Finalizer Instead of try/catch for In-Transaction Errors

**What the LLM generates:** Code that implements a Finalizer to catch expected, recoverable exceptions that should be handled inline — for example, a `DmlException` from a duplicate record that can be caught and handled in the same transaction.

**Why it happens:** LLMs conflate "error handling" broadly with Finalizers because they both deal with exceptions. Training data conflates general error-recovery patterns.

**Correct pattern:**

```apex
// WRONG — using Finalizer for a recoverable in-transaction error
public void execute(QueueableContext ctx) {
    System.attachFinalizer(new RecoverableFinalizer(recordId));
    insert myRecord; // DmlException can be caught inline
}

// CORRECT — handle recoverable exceptions inline; use Finalizer only for
//            unhandled exceptions that escape the transaction
public void execute(QueueableContext ctx) {
    System.attachFinalizer(new UnhandledFinalizer(recordId));
    try {
        insert myRecord;
    } catch (DmlException e) {
        // Handle inline — no need for a Finalizer for this case
        myRecord.Name += ' (duplicate)';
        upsert myRecord;
    }
}
```

**Detection hint:** If the Finalizer's only job is to handle an exception that could be caught with a try/catch inside `execute()`, the Finalizer is unnecessary. Look for Finalizers wrapping simple DML or callout errors.

---

## Anti-Pattern 2: Attaching Another Finalizer from Within a Finalizer

**What the LLM generates:** A `System.attachFinalizer(new SecondaryFinalizer())` call inside the `execute(FinalizerContext ctx)` method of an existing Finalizer, attempting to chain callbacks.

**Why it happens:** LLMs model Finalizers like Java's `finally` blocks or JavaScript's `.finally()` chains, where nesting is valid. The platform constraint is not obvious from the interface signature.

**Correct pattern:**

```apex
// WRONG — a Finalizer's execute() is not a Queueable context, so the platform
//         logs "System.attachFinalizer(Finalizer) is not allowed in this context"
//         (Apex Developer Guide v67.0 L16543-16567) and the Finalizer dies here.
public void execute(FinalizerContext ctx) {
    System.attachFinalizer(new AnotherFinalizer()); // fails at runtime
}

// CORRECT — enqueue a new Queueable; it attaches its own Finalizer
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        System.enqueueJob(new NextStepJob(payload)); // NextStepJob registers its own Finalizer
    }
}
```

**Detection hint:** Any `System.attachFinalizer()` call inside a class that also `implements System.Finalizer` is wrong.

---

## Anti-Pattern 3: Not Checking getResult() Before Taking Action

**What the LLM generates:** A Finalizer that unconditionally performs retry or compensation logic regardless of whether the parent succeeded or failed.

**Why it happens:** LLMs pattern-match on "run something after the job" and forget to gate on the result. This causes double-processing: the job succeeds, and then the Finalizer also inserts a duplicate record or enqueues a redundant retry.

**Correct pattern:**

```apex
// WRONG — runs compensation even on SUCCESS
public void execute(FinalizerContext ctx) {
    insert new Async_Job_Error__c(Async_Apex_Job_Id__c = ctx.getAsyncApexJobId()); // inserts on every run
}

// CORRECT — gate on result
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        insert new Async_Job_Error__c(
            Async_Apex_Job_Id__c = ctx.getAsyncApexJobId(),
            Error_Message__c = ctx.getException().getMessage()
        );
    }
}
```

**Detection hint:** Any Finalizer `execute()` method that does not contain `ctx.getResult()` in a conditional is suspicious.

---

## Anti-Pattern 4: Infinite Retry Without a Counter

**What the LLM generates:** A Finalizer that unconditionally calls `System.enqueueJob(new OriginalJob(payload))` on failure with no retry limit, creating an infinite loop.

**Why it happens:** LLMs generate "retry on failure" as a simple pattern without modeling the termination condition, then reassure the reader that "the flex queue will fill up". It will not. The platform allows five consecutive re-enqueues from a finalizer and then fails the enqueue call (Apex Developer Guide v67.0 L16293-16295, and the guide's own sample comment at L16523) — so the unbounded version dies at the fifth failure having written nothing down, which is strictly worse than looping.

**Correct pattern:**

```apex
// WRONG — infinite loop on persistent failure
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        System.enqueueJob(new OriginalJob(payload)); // no limit!
    }
}

// CORRECT — bounded retry with counter
private static final Integer MAX_RETRIES = 3;

public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        if (retryCount < MAX_RETRIES) {
            System.enqueueJob(new OriginalJob(payload, retryCount + 1));
        } else {
            insert new Async_Job_Error__c(Async_Apex_Job_Id__c = ctx.getAsyncApexJobId(),
                                          Error_Message__c = ctx.getException().getMessage());
        }
    }
}
```

**Detection hint:** A Finalizer `execute()` method that enqueues without checking a `retryCount` or similar ceiling variable — or one whose ceiling is >= 5, which the platform reaches first.

---

## Anti-Pattern 5: Expecting Finalizer to Run After System.abortJob()

**What the LLM generates:** Documentation or code comments claiming the Finalizer "always runs" or will fire even if the job is aborted, leading practitioners to rely on Finalizer cleanup for the abort path.

**Why it happens:** The documentation says Finalizers run "regardless of whether the job succeeds or fails," and LLMs over-generalize this to mean "in all termination scenarios." What the guide actually reserves is broader and vaguer: "If a job request is terminated unexpectedly, such as a database shutdown during system upgrade, the transaction finalizer can fail to execute" (Apex Developer Guide v67.0 L16533-16534). UNVERIFIED (2026-09-05): the guide says nothing at all about `System.abortJob()`, so an assistant that asserts either outcome for abort is inventing it.

**Correct pattern:**

```apex
// WRONG — Finalizer-based cleanup for abort path will never fire
// DO NOT document this as a complete cleanup guarantee
public class MyFinalizer implements System.Finalizer {
    public void execute(FinalizerContext ctx) {
        // This will NOT run if System.abortJob() was called on the parent
        releaseLock();
    }
}

// CORRECT — handle abort path with a separate polling Schedulable:
// SELECT Id, Status FROM AsyncApexJob
//   WHERE ApexClass.Name = 'MyQueueable' AND Status = 'Aborted'
//   ORDER BY CompletedDate DESC
// Then compensate in the Schedulable's execute() method.
```

**Detection hint:** Comments or documentation saying a Finalizer fires "always" or "in all cases" — add the qualifier "except when the parent job is aborted via System.abortJob()".

---

## Anti-Pattern 6: Calling `ctx.getJobId()` on a `FinalizerContext`

**What the LLM generates:** `Id parentJobId = ctx.getJobId();` inside `execute(FinalizerContext ctx)`, usually alongside a comment or a table describing `FinalizerContext` as having three methods.

**Why it happens:** `QueueableContext` does have `getJobId()`, and the guide's own worked examples put both interfaces on one class with `ctx.getJobId()` in the Queueable half (Apex Developer Guide v67.0 L16380) and `ctx.getAsyncApexJobId()` in the Finalizer half (L16424), forty lines apart. Training data mixes the two halves. The `System.FinalizerContext` interface "contains four methods: getAsyncApexJobId, getRequestId, getResult, and getException" (Apex Reference Guide v67.0 L215612-215614) — `getJobId` is not among them.

**Correct pattern:**

```apex
// WRONG — no getJobId() on FinalizerContext; in a fused Queueable+Finalizer class
//         this may even compile, and then correlates against the wrong ID.
public void execute(FinalizerContext ctx) {
    logFailure(ctx.getJobId());
}

// CORRECT — getAsyncApexJobId() is the AsyncApexJob join key; getRequestId()
//           is the Event Monitoring correlation key. They are not interchangeable.
public void execute(FinalizerContext ctx) {
    logFailure(ctx.getAsyncApexJobId(), ctx.getRequestId());
}
```

**Detection hint:** grep for `getJobId` in any file containing `FinalizerContext`. Also flag any prose claiming `FinalizerContext` has three members — the count is four.

---

## Anti-Pattern 7: Marking Finalizer State `transient`

**What the LLM generates:** `private transient List<Id> recordIds;` or `private transient List<LogMessage__c> buffer;` on a class implementing `System.Finalizer`, usually introduced as a heap optimisation or copied from a Visualforce controller idiom.

**Why it happens:** `transient` is the standard Apex answer to "this collection is large and I want to keep the view state / serialized payload small", and an assistant optimising for heap reaches for it without knowing that Finalizer state crosses a transaction boundary by serialization. The failure is silent: the field is simply empty in `execute(FinalizerContext)`, so the compensation runs and logs nothing.

**Correct pattern:**

```apex
// WRONG — "Variables that are declared transient are ignored by serialization and
//          deserialization, and therefore don't persist in the Transaction
//          Finalizer" (Apex Developer Guide v67.0 L16360-16362).
public class OrderFinalizer implements Finalizer {
    private transient List<Id> orderIds;      // null when execute() runs
    private transient List<String> trace;     // empty when execute() runs
}

// CORRECT — keep the state serializable and keep it small by storing IDs,
//           not sObjects. Asynchronous heap limits apply to the Finalizer
//           transaction (Apex Developer Guide v67.0 L16298-16303), so IDs are
//           almost never the thing that blows the budget.
public class OrderFinalizer implements Finalizer {
    private final List<Id> orderIds;
    private final List<String> trace = new List<String>();
}
```

**Detection hint:** any `transient` keyword in a class that implements `Finalizer`, or in a class whose instance is passed to `System.attachFinalizer`. The skill's checker (`scripts/check_apex_transaction_finalizers.py`) flags this case directly.
