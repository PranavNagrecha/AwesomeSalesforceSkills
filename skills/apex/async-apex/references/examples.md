# Examples: Async Apex

## Example 1: Queueable for a post-save callout

**Context:** An `Order__c` trigger must notify an external order system after commit; a trigger chunk can hold 200 records.

**Approach:** Collect changed IDs, enqueue one `Database.AllowsCallouts` Queueable per chunk, re-query inside `execute`, and throw a custom exception on a failed response so the `AsyncApexJob` shows the failure. Worker, trigger, and test class are in `code-examples.md`.

---

## Example 2: Scheduler that dispatches a batch

**Context:** Stale Leads must be closed nightly and the volume can exceed one transaction.

**Approach:** A thin `Schedulable` that calls `Database.executeBatch`, because synchronous limits apply to scheduled Apex (Apex Developer Guide 262, L19536). The batch uses partial-success DML and `Database.Stateful` for a failure count. Batch, scheduler, tests, metadata, and package.xml are in `code-examples.md`.

---

## Anti-Pattern: Async fan-out inside a loop

**What practitioners do:** Call `System.enqueueJob()` once for each record in `Trigger.new`.

```apex
for (Order__c record : Trigger.new) {
    System.enqueueJob(new OrderDispatchQueueable(new Set<Id>{record.Id}));
}
```

**What goes wrong:** A 200-record chunk passes the 50-enqueue synchronous limit, each job consumes a daily async execution, and monitoring becomes noisy.

**Correct approach:** Aggregate IDs and enqueue one job per transaction, or deliberately chunk into a controlled series of jobs.
