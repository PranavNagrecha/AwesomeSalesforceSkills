# LLM Anti-Patterns — Apex Batch Chaining

Common mistakes AI coding assistants make when generating or advising on Apex Batch Chaining.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: A Bare `executeBatch` in `finish()` With No Exception Handling

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**Why it happens:** Training data is dominated by minimum-viable `finish()`
examples. The failure mode is invisible in tutorial code because tutorial orgs
have an empty flex queue.

**Why it is wrong:** a full flex queue makes this call throw a `LimitException`
(`apexdev` L17238–17239), and *"an unhandled exception within the job's finish
method… prevents the next job from being enqueued and breaks the sequence"*
(`apexdev` L17823–17825). The job still reports `Completed`. The chain ends with
no failure record anywhere in the data.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    try {
        Id next = Database.executeBatch(new StepTwoBatch(), 200);
        ApplicationLogger.info('StepOneBatch', 'Chained StepTwoBatch as ' + next);
    } catch (Exception e) {
        // finish() must never throw — log and let the watchdog restart the chain
        ApplicationLogger.error('StepOneBatch', e);
    } finally {
        ApplicationLogger.flush();
    }
}
```

**Detection hint:** any `finish()` whose body contains `Database.executeBatch`
or `System.enqueueJob` outside a `try` block.

---

## Anti-Pattern 2: Testing the Full Chain End-to-End in a Single Test Method

**What the LLM generates:**

```apex
@IsTest
static void testFullChain() {
    Test.startTest();
    Database.executeBatch(new StepOneBatch(), 200);
    Test.stopTest();
    // Asserts on StepTwoBatch effects
    List<Account> updated = [SELECT Id, Is_Archived__c FROM Account];
    Assert.areEqual(true, updated[0].Is_Archived__c); // set by StepTwoBatch
}
```

**Why it happens:** LLMs generalize from single-batch test patterns where
`Test.stopTest()` synchronously drives execution, and apply the same shape to a
chain.

**Why it is wrong:** even setting aside how many levels `stopTest` drives, the
test is bounded — *"you can test only one execution of the execute method"*
(`apexdev` L17739–17740) and *"In a running test, you can submit a maximum of 5
batch jobs"* (`apexdev` L17683). A chain test written this way passes or fails
for reasons unrelated to the logic under test.

**Correct pattern:** route every hand-off through one orchestrator that records
the request and does not start it under test, then assert on the request:

```apex
@IsTest
static void linkA_requests_linkB() {
    ChainOrchestrator.lastRequest = null;
    Test.startTest();
    Database.executeBatch(new AccountArchiveBatch(), 200);
    Test.stopTest();

    Assert.areEqual('ArchiveIndex', ChainOrchestrator.getLastRequest().stepName);
    Assert.areEqual(0, [SELECT COUNT() FROM AsyncApexJob
                        WHERE ApexClass.Name = 'ArchiveIndexBatch'
                          AND JobType != 'BatchApexWorker'],
        'link B must not run inside the test');
}
```

**Detection hint:** a test method that asserts on data effects of a class other
than the one passed to `executeBatch`/`enqueueJob` inside the
`startTest`/`stopTest` block.

---

## Anti-Pattern 3: Calling `System.scheduleBatch` Without Deciding About Latency

**What the LLM generates:** either extreme — `System.scheduleBatch` reflexively
in every `finish()`, or a blanket rule that it is never valid there.

```apex
public void finish(Database.BatchableContext bc) {
    System.scheduleBatch(new StepTwoBatch(), 'Step Two', 1);  // always? never?
}
```

**Why it happens:** the two methods sit in the same documentation section, so
the model picks one and generalizes.

**Why both extremes are wrong:** the guide names both as chaining methods —
*"You can chain a batch job by calling `Database.executeBatch` or
`System.scheduleBatch` from the finish method"* (`apexdev` L17817–17818) — and
recommends the scheduled form specifically when the next link may have nothing
to do: *"use System.scheduleBatch to add a delay before the execution of next
chained batch job. This delay optimizes the usage of available batch jobs and
the flex queue by preventing jobs that don't have any work from repeatedly
starting"* (`apexdev` L17831–17835).

**Correct pattern:** pick on latency, and say why in the code.

```apex
public void finish(Database.BatchableContext bc) {
    Integer remaining = [SELECT COUNT() FROM Staging__c WHERE Status__c = 'Pending'];
    if (remaining == 0) {
        return;                                            // terminate
    }
    if (remaining < 200) {
        // trickle: back off a minute rather than spin the flex queue
        System.scheduleBatch(new StepTwoBatch(), 'Chain step two', 5);
    } else {
        Database.executeBatch(new StepTwoBatch(), 200);     // immediate
    }
}
```

**Detection hint:** `System.scheduleBatch` in a `finish()` with no accompanying
comment or condition explaining the delay, **or** a code review comment claiming
`scheduleBatch` is invalid in `finish()`.

---

## Anti-Pattern 4: Assuming `Database.Stateful` State Is Available in the Next Chained Job

**What the LLM generates:**

```apex
public class StepOneBatch implements Database.Batchable<SObject>, Database.Stateful {
    public List<Id> processedIds = new List<Id>();

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        for (SObject s : scope) { processedIds.add(s.Id); }
    }

    public void finish(Database.BatchableContext bc) {
        // WRONG assumption: StepTwoBatch will somehow see processedIds
        Database.executeBatch(new StepTwoBatch(), 200);
    }
}
```

**Why it happens:** `Database.Stateful` is introduced alongside batch chaining in
the documentation, and the model conflates the two features.

**Why it is wrong twice over:** `Stateful` retains *"only instance member
variables… between transactions"* of the same job (`apexdev` L17519–17521), so
the next job gets a fresh instance — and the growing `List<Id>` is re-serialized
before every remaining chunk, so it is also a heap risk in its own right
(gotcha 5).

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    // Pass a scalar summary; keep per-record detail in a staging object
    Database.executeBatch(new StepTwoBatch(this.processedCount), 200);
}
```

**Detection hint:** a `Database.Stateful` class with a `List<`/`Map<`/`Set<`
instance field that is `.add(`-ed inside `execute` — flagged as an advisory by
`scripts/check_apex_batch_chaining.py` (rule C003).

---

## Anti-Pattern 5: Recursive Self-Chaining Without a Terminal Condition

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    // Re-enqueue self to process remaining records
    Database.executeBatch(new SelfChainingBatch(), 200);
}
```

**Why it happens:** LLMs model this from "process all records" use cases and
assume the batch's own query returns 0 records when done — which fails whenever
the query predicate is not updated by the batch itself.

**Why it is wrong:** no platform limit stops a batch-to-batch chain. What stops
it is the shared 24-hour async cap, and that stops it by *rejecting the whole
job*: *"The batch won't start unless there is sufficient capacity for the entire
job available"* (`apexdev` L17694–17697).

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    if (!Chain_Step__mdt.getInstance('SelfChain').Enabled__c) { return; }  // kill-switch
    Integer remaining = [SELECT COUNT() FROM MyObject__c WHERE Status__c = 'Pending'];
    if (remaining > 0 && this.pass < MAX_PASSES) {
        Database.executeBatch(new SelfChainingBatch(this.pass + 1), 200);
    }
}
```

**Detection hint:** any `finish()` that calls
`Database.executeBatch(new [SameClassName]())` without a preceding count check,
pass counter, or kill-switch read.

---

## Anti-Pattern 6: Chaining Past an Upstream Failure

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new StepTwoBatch(), 200); // proceeds even if StepOne had errors
}
```

**Why it happens:** LLMs follow the happy path. `BatchableContext.getJobId()`
gives access to the completed job's error count, but that pattern rarely appears
in tutorial code.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    AsyncApexJob job = [
        SELECT NumberOfErrors, ExtendedStatus
        FROM AsyncApexJob WHERE Id = :bc.getJobId() WITH USER_MODE
    ];
    if (job.NumberOfErrors > 0) {
        ApplicationLogger.error('StepOneBatch',
            'Halting chain: ' + job.NumberOfErrors + ' failed batches — ' + job.ExtendedStatus);
        return;
    }
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

`NumberOfErrors` is the *"Total number of batches with a failure"* and
`ExtendedStatus` *"contains a short description of the first error"*
(`object_reference`, `AsyncApexJob`) — so this is a chunk-level signal, not a
record-level one. For record-level detail, subscribe to `BatchApexErrorEvent`
(`references/code-examples.md` § 6).

**Detection hint:** a `finish()` that calls `Database.executeBatch` with no
preceding read of `AsyncApexJob.NumberOfErrors` and no `Stateful` error counter.

---

## Anti-Pattern 7: Fanning Out From `finish()` With Two Enqueues

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    System.enqueueJob(new IndexQueueable());
    System.enqueueJob(new NotifyQueueable());   // fails
}
```

**Why it happens:** the model knows the synchronous limit — *"You can add up to
50 jobs to the queue with System.enqueueJob in a single transaction"* — and
misses the very next clause: *"In asynchronous transactions (for example, from a
batch Apex job), you can add only one job to the queue with System.enqueueJob"*
(`apexdev` L16175–16177). The same one-job rule binds a Finalizer (`apexdev`
L16355–16356) and a Queueable chaining to a child (`apexdev` L16187–16189).

**Correct pattern:** one enqueue, then either serialize the work in a single
coordinator, or publish a Platform Event and let independent subscribers fan out
(subscriber design belongs to `apex/platform-events-apex`):

```apex
public void finish(Database.BatchableContext bc) {
    System.enqueueJob(new PostArchiveCoordinator(bc.getJobId()));  // exactly one
}
```

**Detection hint:** more than one `System.enqueueJob` in a `finish()` or in a
Queueable `execute()` — flagged as a WARN by
`scripts/check_apex_batch_chaining.py` (rule C002).

---

## Anti-Pattern 8: Reconstructing the Chain From `AsyncApexJob.ParentJobId`

**What the LLM generates:**

```apex
// "Walk the chain" monitoring query
List<AsyncApexJob> chain = [
    SELECT Id, ApexClass.Name, Status, ParentJobId
    FROM AsyncApexJob
    WHERE ParentJobId = :firstJobId
];
```

**Why it happens:** the field name reads like chain lineage, and the model has
never needed to check.

**Why it is wrong:** `ParentJobId` links a batch job to its own internal
`BatchApexWorker` records — *"For batch Apex jobs that run using chunking
implementation, multiple child jobs of type BatchApexWorker are created. Each of
these child job records contains the job Id of the parent Apex job that started
their execution"* (`object_reference`, `AsyncApexJob.ParentJobId`). It records
nothing about the job that `finish()` started. There is no such platform field.

**Correct pattern:** carry a correlation Id through the constructors, and filter
the internal workers out of any count:

```soql
SELECT Id, ApexClass.Name, JobType, Status, CreatedDate, NumberOfErrors
FROM AsyncApexJob
WHERE ApexClass.Name IN ('AccountArchiveBatch','ArchiveIndexBatch')
  AND JobType != 'BatchApexWorker'
  AND CreatedDate = TODAY
ORDER BY CreatedDate ASC
```

**Detection hint:** `ParentJobId` in a filter or a join in any chain-monitoring
query, or an `AsyncApexJob` aggregate with no `JobType` predicate.
