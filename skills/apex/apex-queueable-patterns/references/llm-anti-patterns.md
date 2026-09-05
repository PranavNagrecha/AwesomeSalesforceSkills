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

**Why it happens:** LLMs generate infinite chaining patterns and assume the platform caps them. It does not: "Because no limit is enforced on the depth of chained jobs, you can chain one job to another." The 5-deep ceiling exists only in Developer Edition and Trial orgs — so the runaway chain is caught in a scratch org and runs forever in production.

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

**Why it happens:** LLMs generate per-record async dispatch. The ceiling is real but it is not the one usually quoted: *"You can add up to 50 jobs to the queue with System.enqueueJob in a single transaction. In asynchronous transactions (for example, from a batch Apex job), you can add only one job to the queue"* (`apexdev` L16179-16181; limits table L19573 reads 50 synchronous / 1 asynchronous). So the loop fails on the 51st qualifying record in a trigger, and on the 2nd inside another job — which is why a hand test with ten records never catches it.

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

---

## Anti-Pattern 7: Asserting Apex cannot delay a job, then building a Schedulable dispatcher

**What the LLM generates:**

```apex
// "Apex has no Thread.sleep() and no way to delay a queueable, so schedule it."
public class RetryDispatcher implements Schedulable {
    public void execute(SchedulableContext sc) {
        for (Retry_Queue__c r : [SELECT Id, Payload__c FROM Retry_Queue__c
                                 WHERE Next_Attempt__c <= :System.now()]) {
            System.enqueueJob(new CalloutJob(r.Payload__c));
        }
    }
}
```

**Why it happens:** the absence of `Thread.sleep()` is heavily represented in training data, and model exposure to `AsyncOptions` rarely extends past `MaximumQueueableStackDepth`. The model reasons from "no sleep" to "no delay at all."

**Correct pattern:**

```apex
AsyncOptions opts = new AsyncOptions();
opts.MinimumQueueableDelayInMinutes = Math.min(attempt * 2, 10); // platform ceiling is 10
System.enqueueJob(new CalloutJob(payload, attempt + 1), opts);
```

The generated fix is worse, not merely unnecessary: the dispatcher consumes a slot in the 100-scheduled-Apex-jobs-per-org limit, needs its own staging object and reaper, and polls on an interval that no longer matches the requested back-off. Respect the two ceilings: the delay maxes at 10 minutes, and a job that failed on an unhandled exception "can be successively re-enqueued five times by a transaction finalizer." Only back-off beyond one of those justifies Scheduled Apex.

**Detection hint:** `System.schedule(`, `System.scheduleBatch(`, or a CRON literal (`'0 0 * * * ?'`) in a file whose class name or comments mention retry, backoff, or re-attempt — or any `Next_Attempt__c`-style datetime field on a staging object.

---

## Anti-Pattern 8: Calling `ctx.getJobId()` on a `FinalizerContext`

**What the LLM generates:**

```apex
public void execute(FinalizerContext ctx) {
    Id parentJob = ctx.getJobId();          // does not compile
    if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
        insert new Job_Failure__c(Job__c = parentJob);
    }
}
```

**Why it happens:** both context interfaces are passed to a method called
`execute`, both concern the same job, and `QueueableContext.getJobId()` is far
more common in training data. They are different interfaces.
`QueueableContext` has exactly one method, `getJobId()` (`apexrefguide`
L227365-227392). `FinalizerContext` has four — `getAsyncApexJobId()`,
`getRequestId()`, `getResult()`, `getException()` (`apexdev` L16311-16344) — and
`getJobId()` is not among them.

**Correct pattern:**

```apex
public void execute(FinalizerContext ctx) {
    Id parentJob = ctx.getAsyncApexJobId();     // correlates with AsyncApexJob
    String requestId = ctx.getRequestId();      // correlates with Event Monitoring
    if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
        ApplicationLogger.error('MyJob', ctx.getException());
        ApplicationLogger.flush();
    }
}
```

**Detection hint:** `getJobId\s*\(` inside a method whose parameter type is
`FinalizerContext`.

---

## Anti-Pattern 9: Querying records in the constructor and carrying them as job state

**What the LLM generates:**

```apex
public class AccountSyncJob implements Queueable {
    private List<Account> accounts;

    public AccountSyncJob(Set<Id> accountIds) {
        this.accounts = [SELECT Id, Name, Industry, AnnualRevenue, Description
                         FROM Account WHERE Id IN :accountIds];
    }
}
```

**Why it happens:** the guide does say a queueable class *"can contain member
variables of non-primitive data types, such as sObjects or custom Apex types"*
(`apexdev` L15968-15970), and the model reads permission as recommendation. Three
costs follow. The whole record graph is serialized on enqueue and deserialized on
execute, on every link of a chain. The data is a snapshot taken in the enqueuing
transaction, so the job acts on values that may already be stale by the time it
runs — the same reasoning the guide gives for banning sObjects as `@future`
parameters (`apexdev` L17971-17974). And a field removed from the object between
enqueue and execute breaks deserialization of a job already sitting in the queue.

**Correct pattern:**

```apex
public class AccountSyncJob implements Queueable {
    private final List<Id> accountIds;

    public AccountSyncJob(Set<Id> accountIds) {
        this.accountIds = new List<Id>(accountIds);
    }

    public void execute(QueueableContext ctx) {
        List<Account> accounts = [SELECT Id, Name, Industry FROM Account
                                  WHERE Id IN :accountIds WITH USER_MODE];
        // fresh values, minimal serialized state
    }
}
```

**Detection hint:** a Queueable member field of type `List<SObject>` or a
concrete `List<Account>` assigned from a `[SELECT ...]` inside the constructor.
The checker in this skill reports this as ADVISORY.
