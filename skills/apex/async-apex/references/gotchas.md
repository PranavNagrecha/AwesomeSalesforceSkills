# Gotchas — Async Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## One Child Queueable Per Executing Queueable

**What happens:** A Queueable attempts to enqueue two follow-up jobs and the second enqueue throws a limit exception.

**When it occurs:** Developers treat Queueable chaining like a free fan-out mechanism inside `execute()`.

**How to avoid:** Chain only one next job from a Queueable. If you need broader fan-out, redesign with Batch, Platform Events, or an external queue/orchestrator.

---

## `@future` Parameters Are Narrower Than Queueable State

**What happens:** A team migrates logic mentally from Queueable to `@future` and tries to pass SObjects or complex DTOs.

**When it occurs:** Legacy code paths are extended instead of modernized.

**How to avoid:** Pass only IDs or primitive collections to `@future`. Prefer Queueable when non-primitive state or better observability is needed.

---

## Async Tests Pass Only After `Test.stopTest()`

**What happens:** A test enqueues a Queueable or runs a Batch and immediately asserts that records changed. The assertions fail even though the code is correct.

**When it occurs:** Async jobs are scheduled inside tests without a `Test.stopTest()` boundary.

**How to avoid:** Put the enqueue or `Database.executeBatch()` call between `Test.startTest()` and `Test.stopTest()`, then assert afterward.

---

## Schedulers That Do Real Work Become A Maintenance Trap

**What happens:** The cron class contains queries, business logic, and DML directly. Over time it becomes harder to test and impossible to reuse outside the schedule.

**When it occurs:** Teams treat `Schedulable` as a worker instead of a dispatcher.

**How to avoid:** Keep the scheduler thin. Have it launch a Queueable or Batch and let the worker class own the actual processing logic.
