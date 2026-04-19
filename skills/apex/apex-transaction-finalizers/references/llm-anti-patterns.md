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
// WRONG — throws AsyncException at runtime
public void execute(FinalizerContext ctx) {
    System.attachFinalizer(new AnotherFinalizer()); // throws!
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
    insert new Async_Job_Error__c(Job_Id__c = ctx.getJobId()); // inserts on every run
}

// CORRECT — gate on result
public void execute(FinalizerContext ctx) {
    if (ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION) {
        insert new Async_Job_Error__c(
            Job_Id__c        = ctx.getJobId(),
            Error_Message__c = ctx.getException().getMessage()
        );
    }
}
```

**Detection hint:** Any Finalizer `execute()` method that does not contain `ctx.getResult()` in a conditional is suspicious.

---

## Anti-Pattern 4: Infinite Retry Without a Counter

**What the LLM generates:** A Finalizer that unconditionally calls `System.enqueueJob(new OriginalJob(payload))` on failure with no retry limit, creating an infinite loop.

**Why it happens:** LLMs generate "retry on failure" as a simple pattern without modeling the termination condition. In a language runtime that would stack-overflow, but in async Salesforce it will just keep filling the flex queue.

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
            insert new Async_Job_Error__c(Job_Id__c = ctx.getJobId(),
                                          Error_Message__c = ctx.getException().getMessage());
        }
    }
}
```

**Detection hint:** A Finalizer `execute()` method that enqueues without checking a `retryCount` or similar ceiling variable.

---

## Anti-Pattern 5: Expecting Finalizer to Run After System.abortJob()

**What the LLM generates:** Documentation or code comments claiming the Finalizer "always runs" or will fire even if the job is aborted, leading practitioners to rely on Finalizer cleanup for the abort path.

**Why it happens:** The documentation says Finalizers run "regardless of whether the job succeeds or fails," and LLMs over-generalize this to mean "in all termination scenarios," missing the abort exception.

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
