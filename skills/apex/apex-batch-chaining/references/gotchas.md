# Gotchas — Apex Batch Chaining

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line cites are into the *Apex Developer Guide* Version 67.0 Summer '26
(`apexdev`), the *Apex Reference Guide* (`apexrefguide`), and the *Object
Reference for Salesforce* (`object_reference`), as extracted 2026-09-05.

## Gotcha 1: A Full Flex Queue Throws — It Does Not Queue Silently

**What happens:** When the Apex flex queue already holds its maximum of 100
jobs, `Database.executeBatch` **throws a `LimitException` and does not add the
job to the queue** (`apexdev` L17238–17239). Called from `finish()`, that
exception is unhandled by default — and an unhandled exception in `finish()`
*"prevents the next job from being enqueued and breaks the sequence"* (`apexdev`
L17823–17825). So the failure is loud in the debug log and invisible in your
data: the chain simply stops, one link short.

A second, different failure mode looks like the "silent" behaviour and is often
confused with it. If the call fails to acquire an *Apex flex queue lock*:
*"In API version 52.0 and later, the call throws a System.AsyncException. In API
version 51.0 and earlier, the call returns an empty ID, `000000000000000`,
instead of throwing an exception"* (`apexrefguide` L207068–207070). Only a class
running at API 51.0 or earlier gets the empty-Id return.

**When it occurs:** Any org where nightly scheduled jobs, integration callbacks
and chained pipelines overlap. The guide notes the ceiling is not even hard:
*"It is possible that the number of jobs in the Apex flex queue sometimes
exceeds the maximum limit, resulting from parallel requests to enqueue batch
Apex jobs. Further attempts to enqueue batch jobs will encounter a
LimitException until the queue size drops below the maximum limit"* (`apexdev`
L17251–17253).

**How to avoid:** Wrap every hand-off in `finish()` in try/catch so the
exception is recorded rather than silently ending the chain, check the API
version of the *batch class* (not the helper) is ≥ 52.0, and treat a returned
`000000000000000` as a failure if you are stuck on an older version:

```apex
public void finish(Database.BatchableContext bc) {
    try {
        Id next = Database.executeBatch(new StepTwoBatch(), 200);
        if (next == null || String.valueOf(next).startsWith('000000000000000')) {
            ApplicationLogger.error('StepOneBatch', 'Flex queue lock refused the hand-off.');
            return;
        }
        ApplicationLogger.info('StepOneBatch', 'Chained StepTwoBatch as ' + next);
    } catch (Exception e) {
        ApplicationLogger.error('StepOneBatch', e);   // never let finish() throw
    } finally {
        ApplicationLogger.flush();
    }
}
```

---

## Gotcha 2: `System.FlexQueue.getJobIds()` Does Not Exist

**What happens:** Code that guards a chain with `System.FlexQueue.getJobIds()`
fails to compile. The `FlexQueue` class has exactly four methods —
`moveAfterJob`, `moveBeforeJob`, `moveJobToEnd`, `moveJobToFront`
(`apexrefguide` L215739–215762). There is no read accessor. The only method that
returns queue order is `Test.getFlexQueueOrder()`, which the guide pairs with
`Test.enqueueBatchJobs` for *"no-operation jobs within the context of tests"*
(`apexdev` L17680–17682) — test context only.

**When it occurs:** Whenever an assistant or a blog post reaches for a
"check the queue first" API by analogy with `Limits.getQueueableJobs()`.

**How to avoid:** Read the queue through SOQL on `AsyncApexJob`, and use
`FlexQueue` only to *reorder*. To make a chain link jump the holding queue,
`System.FlexQueue.moveJobToFront(highPriorityJobId)` (`apexrefguide`
L215723–215727) — it returns `false` (not an error) if the job is already at the
front, and throws an element-not-found exception if the job is not in the queue
at all (`apexrefguide` L215758–215762).

---

## Gotcha 3: The 100 and the 5 Are Two Different Ceilings, Counted Differently

**What happens:** A guard query that counts `Holding + Queued + Preparing +
Processing` and compares the total to 100 is comparing the wrong number to the
wrong ceiling. The two limits are:

- *"Up to 5 batch jobs can be queued or active concurrently"* (`apexdev` L17686)
- *"Up to 100 **Holding** batch jobs can be held in the Apex flex queue"*
  (`apexdev` L17687); the limits table reads *"Maximum number of batch Apex jobs
  in the Apex flex queue that are in Holding status — 100"* (`apexdev` L19779)

The flex queue is *additional* capacity: *"only five active Batch Apex jobs are
allowed at one time in your org. Jobs beyond this limit are placed in the Flex
Queue, which is limited to 100 additional jobs"* (`apexdev` L15939–15940). The
practical ceiling is 105 in-flight batch jobs, not 100.

**When it occurs:** Any guard copied from a tutorial. A combined count of 96
looks like "near capacity" but may be 5 running and 91 holding — nine slots of
real headroom.

**How to avoid:** Group by `Status` and compare each group to its own limit. The
verification query in `references/code-examples.md` § 11 does this.

---

## Gotcha 4: `System.scheduleBatch` Is a Sanctioned Chaining Method, Not a Mistake

**What happens:** Teams rip `System.scheduleBatch` out of `finish()` believing
it is always the wrong tool. The guide names both: *"You can chain a batch job by
calling `Database.executeBatch` or `System.scheduleBatch` from the finish method
of the current batch class"* (`apexdev` L17817–17818), and then actively
recommends the scheduled form for one case: *"If there's currently no further
work to perform either in the current job's finish method or because your
business is entering an off-peak period, use System.scheduleBatch to add a delay
before the execution of next chained batch job. This delay optimizes the usage
of available batch jobs and the flex queue by preventing jobs that don't have
any work from repeatedly starting"* (`apexdev` L17831–17835).

**When it occurs:** In poll-until-done chains, where a no-delay
`Database.executeBatch` loop burns async executions on empty passes.

**How to avoid:** Choose on latency, not on habit. `Database.executeBatch` for
an immediate next link. `System.scheduleBatch(batchable, jobName,
minutesFromNow)` when you want a gap — `minutesFromNow` *"must be greater than
zero"* (`apexrefguide` L239905), so the floor is one minute, and the call
consumes a scheduled-Apex slot against the org's cap of 100 scheduled jobs
(`apexdev` L16617). The slot is released once the job queues: *"After the batch
job is queued (with a status of Holding or Queued), all batch job limits apply
and the job no longer counts toward scheduled Apex limits"* (`apexrefguide`
L239920–239923).

---

## Gotcha 5: A `Database.Stateful` Collection That Grows Per Scope Is Serialized Every Chunk

**What happens:** `Database.Stateful` preserves state by serializing the batch
instance between transactions — *"only instance member variables retain their
values between transactions. Static member variables don't"* (`apexdev`
L17519–17521). A `List<Id>` or `Map<Id, String>` that gains 200 entries per
`execute()` therefore carries the whole accumulated collection into the
serialization for every remaining chunk. On a job with hundreds of chunks that
ends as a heap failure late in the run, long after the code that "worked in the
sandbox".

**When it occurs:** In exactly the chaining scenario — collecting failed record
Ids across a job so `finish()` can hand them to the next link.

**How to avoid:** Keep `Stateful` members to counters and scalars. Persist
per-record detail to a staging sObject (or emit a `BatchApexErrorEvent`
subscriber record) inside `execute()`, and let the next link query it in
`start()`. The checker in `scripts/` flags a `Stateful` class with a collection
instance field that is `.add(`-ed inside `execute` as an advisory.

---

## Gotcha 6: State Does Not Travel With the Chain

**What happens:** `Database.Stateful` preserves instance members between the
`execute()` transactions of *one job*. It does not persist into the job started
from `finish()`. Each `Database.executeBatch` constructs a fresh instance of the
next class, whose members are at their declared defaults.

**When it occurs:** When a batch accumulates counts or error records and the
developer assumes the next job "inherits" them.

**How to avoid:** Pass state forward explicitly via the constructor of the
chained job:

```apex
public void finish(Database.BatchableContext bc) {
    // CORRECT: pass accumulated state via constructor
    Database.executeBatch(new StepTwoBatch(this.processedCount, this.errorIds), 200);
}
```

For larger state, persist to a staging sObject and let the next job query it in
`start()`. Note the asymmetry that makes this confusing: reading `this.someField`
inside `finish()` *does* work, because `finish()` is part of the same job's
context — it is only the *next* job that cannot see it.

---

## Gotcha 7: One `enqueueJob` Per Async Transaction — a Fan-Out From `finish()` Is Impossible

**What happens:** A `finish()` that enqueues two Queueables fails on the second.
*"You can add up to 50 jobs to the queue with System.enqueueJob in a single
transaction. In asynchronous transactions (for example, from a batch Apex job),
you can add only one job to the queue with System.enqueueJob"* (`apexdev`
L16175–16177). The same one-job rule binds the Finalizer: *"You can enqueue a
single asynchronous Apex job (Queueable, Future, or Batch) in the finalizer's
implementation of the execute method"* (`apexdev` L16355–16356). And Queueable
chaining itself: *"you can add only one job from an executing job. Only one child
job can exist for each parent queueable job. Starting multiple child jobs from
the same queueable job isn't supported"* (`apexdev` L16187–16189).

**When it occurs:** Fan-out designs — "after archiving, kick off the indexer AND
the notifier" — written as two enqueues in one `finish()`.

**How to avoid:** Fan out through a single coordinator Queueable that fans back
in serially, or publish a Platform Event and let independent subscribers do the
parallel work (`apex/platform-events-apex` owns that subscriber design).
`Limits.getQueueableJobs()` reports how many have already been added in the
current transaction (`apexdev` L16177–16178).

---

## Gotcha 8: The 24-Hour Async Cap Is Checked Up Front and Rejects the Whole Job

**What happens:** The chain does not degrade gracefully near the daily async
limit — it refuses to start. *"Batch Apex preemptively checks the required
asynchronous job capacity when Database.executeBatch is called and the start
method has returned the workload. The batch won't start unless there is
sufficient capacity for the entire job available. For example, if the batch
requires 10,000 executions and the remaining asynchronous limit is 9,500
executions, an `AsyncApexExecutions Limit exceeded` exception is thrown, and the
remaining executions are left unchanged"* (`apexdev` L17694–17699).

The cap is *"250,000, or the number of user licenses in your org multiplied by
200 — whichever is greater"* and it is shared: *"This limit is for your entire
org and is shared with all asynchronous Apex: Batch Apex, Queueable Apex,
scheduled Apex, and future methods"* (`apexdev` L17689–17693). Method executions
count `start`, `execute` **and** `finish` — so an N-link chain over the same
data costs roughly N × (chunks + 2).

**When it occurs:** Long chains over large objects, and self-chaining
poll-until-done loops with a zero delay.

**How to avoid:** Budget the chain before building it: total executions ≈
Σ(rows ÷ scope + 2) per link. Query remaining headroom through the REST API
`limits` resource (`apexdev` L17693–17694). If your org has the beta enabled,
note that elastic limits do **not** rescue a batch chain: *"Elastic limits for
asynchronous Apex jobs (beta) applies to only Queueable Apex and future methods
in production and demo orgs. Batch Apex and scheduled jobs currently remain
capped at the rolling 24-hour asynchronous job limit"* (`apexdev` L20020–20021).

---

## Gotcha 9: `AsyncApexJob.ParentJobId` Is Not the Chain Link

**What happens:** A monitoring query that walks `ParentJobId` to reconstruct
"which job started which" returns nothing useful. Per the Object Reference's
`AsyncApexJob.ParentJobId` description: *"For batch Apex jobs that run using
chunking implementation, multiple child jobs of type `BatchApexWorker` are
created. Each of these child job records contains the job Id of the parent Apex
job that started their execution. For batch Apex jobs that run using a
non-chunking implementation, child jobs aren't created."* It is internal
worker lineage, not chain lineage. The platform records no link between job A
and the job A's `finish()` started.

Counting is affected too: *"For each 10,000 AsyncApexJob records, Apex creates an
AsyncApexJob record of type BatchApexWorker for internal use. When querying for
all AsyncApexJob records, we recommend that you filter out records of type
BatchApexWorker using the JobType field"* (`apexdev` L17755–17758) — an
unfiltered capacity guard over-counts.

**When it occurs:** Building a chain dashboard, or a `finish()` guard that
counts jobs.

**How to avoid:** Carry your own correlation Id through the links (a constructor
parameter, or `ApplicationLogger`'s `Request_Id__c`), filter every
`AsyncApexJob` query with `JobType != 'BatchApexWorker'`, and order by
`CreatedDate` to read the sequence.

---

## Gotcha 10: An Unhandled Exception in `finish()` Silently Ends the Chain

**What happens:** *"A potential failure point in chained batch jobs is an
unhandled exception within the job's finish method. The unhandled exception
prevents the next job from being enqueued and breaks the sequence"* (`apexdev`
L17823–17825). The job that threw still shows `Completed` in the Apex Jobs UI —
the exception was in `finish`, after all chunks succeeded — so the chain reads
as healthy right up to the link that never started.

**When it occurs:** A query in `finish()` that hits a row limit, a null
dereference on a `Stateful` member, a `LimitException` from a capacity check —
and, per Gotcha 1, the `LimitException` from a full flex queue.

**How to avoid:** Two layers, both named by the guide.

1. Never let `finish()` throw: try/catch around every hand-off, logging through
   `templates/apex/ApplicationLogger.cls`.
2. Run the guide's own watchdog: *"consider implementing a separate scheduled
   Apex job that periodically checks the status of the chain. The scheduled job
   queries the AsyncApexJob object for records where the JobType is 'BatchApex'
   and the ApexClass.Name matches the class expected to be currently running or
   queued within the chain. If this query returns no results, the expected job is
   neither running nor queued, which signifies that the chain has been
   unexpectedly interrupted. The scheduled job then restarts the entire batch
   chain"* (`apexdev` L17825–17830). The query is in
   `references/code-examples.md` § 11.

For the class of failures that happen *inside* `execute()` rather than
`finish()`, declare `Database.RaisesPlatformEvents` so a `BatchApexErrorEvent`
fires — *"Events are also fired for Salesforce Platform internal errors and
other uncatchable Apex exceptions such as LimitExceptions"* (`apexdev`
L17845–17847), which is the only signal you get for an uncatchable failure.

---

## Gotcha 11: Test Behaviour Is Bounded in Ways That Make Chain Tests Lie

**What happens:** Three separate limits collide in a chain test.

- *"When testing your batch Apex, you can test only one execution of the execute
  method"* (`apexdev` L17739–17740) — so a test over 500 records with scope 200
  covers 200 records, not 500, and a bug in chunk 2 is invisible.
- *"In a running test, you can submit a maximum of 5 batch jobs"* (`apexdev`
  L17683) — a 6-link chain cannot be exercised in one test method even if the
  platform ran it.
- Async calls inside the block don't consume org limits: *"Asynchronous calls,
  such as @future or executeBatch, called in a startTest, stopTest block, don't
  count against your limits"* (`apexdev` L17614–17615) — so a test never
  reproduces the capacity failures in Gotchas 1, 3 and 8.

UNVERIFIED (2026-09-05): the widely-held rule that `Test.stopTest()` runs only
*one* level of a chain is not stated in the extracted guides. What they state is
narrower — *"The system executes all asynchronous processes started in a test
method synchronously after the Test.stopTest statement"* (`apexdev`
L16123–16125, L17604–17607) — which is silent on a job started by another job's
`finish()`. For Queueables the guide points the other way: *"You can test chained
queueable jobs by using appropriate stack depths"* (`apexdev` L16166).

**When it occurs:** Any test that asserts on the data effects of link 2 or later.

**How to avoid:** Do not make the test depend on which levels run. Route every
hand-off through one orchestrator that records the request and skips the start
under `Test.isRunningTest()`, then assert on the recorded request. That
assertion is deterministic regardless of the platform's test-mode chaining
behaviour. See `ChainOrchestratorTest` in `references/code-examples.md` § 7.

---

## Gotcha 12: Infinite Chain Due to Missing Terminal Condition

**What happens:** A batch class whose `finish()` unconditionally re-enqueues
itself (or re-enqueues a job that eventually calls back to the same class)
creates an unbounded sequence of jobs. Each consumes flex-queue capacity, an
execution slot, and — the one that actually bites — async executions against the
shared 24-hour cap (Gotcha 8). Because batch chains have no platform-enforced
depth limit, nothing stops it.

Queueable chains have the same shape with one asymmetry worth knowing: *"Because
no limit is enforced on the depth of chained jobs, you can chain one job to
another… For Developer Edition and Trial organizations, the maximum stack depth
for chained jobs is 5, which means that you can chain jobs four times"*
(`apexdev` L16182–16186). A runaway Queueable chain therefore stops itself in a
Developer Edition sandbox and does not stop itself in production — the reverse
of the failure order you want.

**When it occurs:** "Self-healing" or "poll until done" patterns implemented as a
batch that re-enqueues itself with the same query. Also with copy-paste errors
where a developer chains Job A → B → A again.

**How to avoid:** Every chain implementation must have an explicit terminal
condition checked before enqueuing:

- A step counter passed through the constructor: stop when `step > MAX_STEPS`.
- A query result count: stop when the start query returns 0 records.
- A Custom Metadata kill-switch: stop when `Chain_Step__mdt.Enabled__c == false`.

For the Queueable links, set the cap explicitly rather than relying on the
edition default: `AsyncOptions.MaximumQueueableStackDepth`, read back at runtime
through `AsyncInfo.hasMaxStackDepth()`,
`AsyncInfo.getCurrentQueueableStackDepth()` and
`AsyncInfo.getMaximumQueueableStackDepth()` (`apexdev` L16044–16062). The guide's
`FibonacciDepthQueueable` example (`apexdev` L16066–16110) is the canonical
shape.
