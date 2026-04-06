# LLM Anti-Patterns — Apex Queueable Patterns

Common mistakes AI coding assistants make when generating or advising on Queueable Apex jobs.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Chaining queueable jobs without a depth guard

**What the LLM generates:**

```apex
public void execute(QueueableContext ctx) {
    // process current batch
    processRecords(this.records);
    // Always chain the next job
    if (!remainingRecords.isEmpty()) {
        System.enqueueJob(new MyQueueable(remainingRecords));
    }
}
```

**Why it happens:** LLMs generate infinite chaining patterns without considering the platform stack depth limit (default 5 for `AsyncOptions.MaximumQueueableStackDepth`). In production, the chain silently stops when the depth limit is reached, leaving unprocessed records.

**Correct pattern:**

```apex
public void execute(QueueableContext ctx) {
    processRecords(this.records);
    if (!remainingRecords.isEmpty()) {
        if (this.currentDepth < MAX_CHAIN_DEPTH) {
            System.enqueueJob(new MyQueueable(remainingRecords, this.currentDepth + 1));
        } else {
            // Fallback: log, persist remaining work to a staging object, or use Batch
            StagingService.persistRemainingWork(remainingRecords);
        }
    }
}
```

**Detection hint:** `System\.enqueueJob` inside an `execute` method with no depth counter or `Limits.getQueueableJobs()` check.

---

## Anti-Pattern 2: Forgetting Database.AllowsCallouts for queueable jobs that make HTTP calls

**What the LLM generates:**

```apex
public class MyCalloutJob implements Queueable {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:MyNamedCredential/api/data');
        req.setMethod('GET');
        new Http().send(req); // Throws: Callout not allowed from this future method
    }
}
```

**Why it happens:** LLMs know Queueable supports callouts but forget that the class must also implement `Database.AllowsCallouts`. Without it, the callout throws a runtime exception.

**Correct pattern:**

```apex
public class MyCalloutJob implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:MyNamedCredential/api/data');
        req.setMethod('GET');
        HttpResponse res = new Http().send(req);
        // process response
    }
}
```

**Detection hint:** Class implements `Queueable` and contains `Http\(\)\.send` but does not implement `Database.AllowsCallouts`.

---

## Anti-Pattern 3: Passing non-serializable state to a chained queueable

**What the LLM generates:**

```apex
public class MyQueueable implements Queueable {
    private HttpResponse lastResponse; // Not serializable
    private transient Database.QueryLocator locator; // Not serializable

    public MyQueueable(HttpResponse resp) {
        this.lastResponse = resp;
    }
}
```

**Why it happens:** LLMs treat Queueable like a regular class and assign any object to its fields. Queueable instances are serialized between transactions. Non-serializable types like `HttpResponse`, `Database.QueryLocator`, or `Savepoint` cause a runtime `SerializationException` when the job is enqueued.

**Correct pattern:**

```apex
public class MyQueueable implements Queueable {
    private String responseBody; // Serialize the data, not the transport object
    private Integer statusCode;

    public MyQueueable(String body, Integer statusCode) {
        this.responseBody = body;
        this.statusCode = statusCode;
    }
}
```

**Detection hint:** Queueable class with member fields of type `HttpResponse`, `HttpRequest`, `Database.QueryLocator`, `Savepoint`, or `PageReference`.

---

## Anti-Pattern 4: Not using the Finalizer interface for error recovery

**What the LLM generates:**

```apex
public class MyQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        try {
            riskyOperation();
        } catch (Exception e) {
            System.debug('Job failed: ' + e.getMessage());
            // No recovery, no retry, no notification
        }
    }
}
```

**Why it happens:** LLMs wrap the body in try/catch and call it done. But if the job fails with an unhandled exception (or the catch itself fails), there is no recovery path. The Finalizer interface provides a guaranteed callback after a queueable completes, whether it succeeded or failed.

**Correct pattern:**

```apex
public class MyQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new MyFinalizer(this.jobConfig));
        riskyOperation();
    }
}

public class MyFinalizer implements Finalizer {
    private JobConfig config;

    public MyFinalizer(JobConfig config) {
        this.config = config;
    }

    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
            String error = ctx.getException().getMessage();
            LogService.logJobFailure('MyQueueable', error);
            if (config.retryCount < 3) {
                config.retryCount++;
                System.enqueueJob(new MyQueueable(config));
            }
        }
    }
}
```

**Detection hint:** Queueable class with no `System.attachFinalizer` call and a bare `try/catch` with only `System.debug` in the catch block.

---

## Anti-Pattern 5: Enqueuing a queueable from a trigger without checking limits

**What the LLM generates:**

```apex
// In trigger handler
for (Account a : Trigger.new) {
    if (a.Status__c == 'Active') {
        System.enqueueJob(new AccountProcessorJob(a.Id));
    }
}
```

**Why it happens:** LLMs generate per-record async dispatch. In a trigger context, you can only enqueue 1 queueable job per synchronous transaction (or 1 per `execute` in async). Enqueuing inside a loop with more than 1 qualifying record throws `System.LimitException: Too many queueable jobs added to the queue: 2`.

**Correct pattern:**

```apex
// Collect all IDs, enqueue a single job for the batch
List<Id> activeIds = new List<Id>();
for (Account a : Trigger.new) {
    if (a.Status__c == 'Active') {
        activeIds.add(a.Id);
    }
}
if (!activeIds.isEmpty()) {
    System.enqueueJob(new AccountProcessorJob(activeIds));
}
```

**Detection hint:** `System\.enqueueJob` inside a `for` loop in trigger or handler context.

---

## Anti-Pattern 6: Using System.enqueueJob in a test without Test.startTest/stopTest

**What the LLM generates:**

```apex
@IsTest
static void testQueueable() {
    System.enqueueJob(new MyQueueable(testData));
    // Assertions immediately — job has not executed yet
    System.assertEquals(1, [SELECT COUNT() FROM Log__c]);
}
```

**Why it happens:** LLMs forget that queueable jobs in tests only execute synchronously when enqueued between `Test.startTest()` and `Test.stopTest()`. Without that boundary, the job never runs and assertions fail or pass vacuously.

**Correct pattern:**

```apex
@IsTest
static void testQueueable() {
    // Setup test data
    Test.startTest();
    System.enqueueJob(new MyQueueable(testData));
    Test.stopTest();
    // Now the job has executed synchronously
    System.assertEquals(1, [SELECT COUNT() FROM Log__c]);
}
```

**Detection hint:** `System\.enqueueJob` in a test method without `Test\.startTest` and `Test\.stopTest` bracketing it.
