# Gotchas — Long-Running Process Orchestration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `MaximumQueueableStackDepth` Does Not Propagate Through The Chain

**What happens:** A developer sets `AsyncOptions.MaximumQueueableStackDepth = 5` on the first `System.enqueueJob()` call, assumes it applies to all subsequent chained jobs, and does not pass `AsyncOptions` on later calls. The guard is silently absent on jobs 2 through N. If a bug causes runaway chaining — for example, a step counter that fails to increment — the chain continues indefinitely past the intended limit.

**When it occurs:** Any chained Queueable implementation where `AsyncOptions` is not explicitly set on every `enqueueJob` call. The platform does not emit a warning when `AsyncOptions` is omitted on a child enqueue inside a chain.

**How to avoid:** Every `System.enqueueJob()` call in a chain must construct a new `AsyncOptions` instance and set `MaximumQueueableStackDepth`. Treat it as a required argument to your internal `enqueueNextStep()` helper method so omission is a compile-time gap rather than a silent runtime omission.

---

## Gotcha 2: Platform Events Published Before A DML Commit Are Delivered Even If The Transaction Rolls Back

**What happens:** A Queueable publishes a `StepAdvance__e` event to signal the next step, then performs DML that throws an unhandled exception. The transaction rolls back, reversing the DML. However, the Platform Event has already been committed to the event bus as a side effect of the `EventBus.publish()` call, and it is delivered to subscribers. The state machine advances to the next step while the data changes from the current step are gone, causing state inconsistency.

**When it occurs:** Any code that publishes a Platform Event to signal step completion before the DML for that step is committed and confirmed successful. This is particularly common when publication is the last line before a `commit` path, but an exception in a shared utility method earlier in the call stack triggers rollback.

**How to avoid:** Publish step-advance Platform Events only after all DML for the current step has completed without error — either by placing `EventBus.publish()` as the final operation after all DML, or by verifying DML results before publishing. Consider using `System.EventBus.publish()` return value inspection and treating a failed publish as a step failure rather than as an advisory.

---

## Gotcha 3: Finalizer Failures Are Silent Without Explicit Monitoring

**What happens:** A Finalizer is attached to recover from step failures. The Finalizer itself hits a governor limit (for example, it queries 101 records or uses too much CPU on a large retry set) and throws an exception. This failure does not surface in the original job's error context, does not appear in the `AsyncApexJob` record for the parent job, and does not generate a platform-level alert. The process appears to have a Finalizer, but its recovery logic never ran.

**When it occurs:** Finalizers that perform significant SOQL, DML, or callouts without being subject to the same limit scrutiny applied to the parent Queueable. Since Finalizers run in a separate transaction with their own full limits, they can usually tolerate typical work — but a poorly designed Finalizer that queries all records related to a process or performs unbounded DML in a retry loop can hit limits.

**How to avoid:** Keep Finalizer logic minimal: check the result, update a Custom Object checkpoint record (1 DML row), and enqueue one retry job. Do not perform unbounded queries or loop-based DML in the Finalizer. Add monitoring by writing to a `FinalizerLog__c` Custom Object or calling `System.debug()` at the start of every Finalizer `execute()`. Monitor `AsyncApexJob` records filtered by `JobType = 'Queueable'` and `Status = 'Failed'` — these represent Finalizer transaction failures.

---

## Gotcha 4: `System.AsyncInfo.getCurrentQueueableStackDepth()` Returns 0 In Test Context

**What happens:** Unit tests invoke Queueable jobs synchronously via `Test.startTest()` / `Test.stopTest()`. In this context, `System.AsyncInfo.getCurrentQueueableStackDepth()` always returns 0 because the test does not place jobs on the real async queue. Branch logic that checks `if (depth >= maxDepth) { stopChaining(); }` is never exercised in unit tests because the depth never exceeds 0. Chain termination logic is effectively invisible to the test suite.

**When it occurs:** Any test that relies on `Test.stopTest()` to synchronously execute a Queueable chain with depth guards.

**How to avoid:** Test depth-guard logic by injecting a configurable `maxDepth` value into the Queueable constructor and setting it to 1 in tests. This forces the termination branch to execute on the first `execute()` call regardless of actual async depth. Alternatively, mock `System.AsyncInfo` behavior through a testable wrapper interface.

---

## Gotcha 5: A Queueable Cannot Enqueue More Than One Child — Fan-Out Fails At Runtime

**What happens:** A developer implements a step that needs to spawn multiple parallel workers (for example, processing 10 account groups in parallel). The step calls `System.enqueueJob()` in a loop, each iteration enqueuing one of the 10 workers. The first `enqueueJob` succeeds; the second call throws `System.LimitException: Too many queueable jobs added to the queue: 2`. This exception is thrown at runtime and does not appear during compilation or deployment.

**When it occurs:** Any Queueable `execute()` method that calls `System.enqueueJob()` more than once. This limit is enforced in production and full sandbox orgs. In test context, the limit is 1 enqueue per synchronous execution.

**How to avoid:** Fan-out in Apex requires a different mechanism. Options: (1) publish multiple Platform Events and let the subscriber trigger process them concurrently via individual Queueable enqueues (each trigger invocation can enqueue one job); (2) use Batch Apex with a small `scope` size for parallel processing of a set; (3) chain a single Queueable that processes a slice and re-enqueues itself with the next slice (sequential fan-out, not parallel). Choose based on whether true parallelism is required or sequential processing with slice boundaries is sufficient.

---

## Gotcha 6: Continuation Is Not Available Outside LWC/Aura/Visualforce Controller Context

**What happens:** A developer tries to use the `Continuation` class to make a long-running async callout from a Queueable, a trigger, or a `@future` method. The code compiles but throws a runtime exception: `System.CalloutException: Continuation is only supported from Visualforce/Aura/LWC controllers`.

**When it occurs:** Continuation is a UI-layer mechanism. It is valid only when the method is invoked as an action from a Lightning Web Component, Aura component, or Visualforce page controller. Attempting to use it in any server-side async context is always a runtime failure.

**How to avoid:** Use `Continuation` only in `@AuraEnabled` controller methods that return `Object` (not `void`) or Visualforce action methods. For long-running callouts outside the UI layer, use a Queueable implementing `Database.AllowsCallouts` — the callout limit per transaction is 100, and each callout can run up to 10 seconds, for a combined 120-second total callout time, which covers most integration scenarios (Apex Developer Guide — Callout Limits).
