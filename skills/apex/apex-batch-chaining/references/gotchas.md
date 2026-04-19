# Gotchas — Apex Batch Chaining

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Silent Flex Queue Saturation — No Exception, No Alert

**What happens:** When the Flex Queue reaches its 100-job limit, `Database.executeBatch` called from inside `finish()` does not throw a catchable exception in all API versions and contexts. The call either returns null silently or (in some cases) raises a non-catchable `AsyncException`. Either way, the chained job is never enqueued, and there is no platform-generated alert.

**When it occurs:** High-volume orgs running multiple batch processes concurrently (e.g., scheduled nightly jobs, integration callbacks, and chained pipelines all running at the same time) can hit the 100-job ceiling without realizing it.

**How to avoid:** Add a guard query before every `Database.executeBatch` call in `finish()`:

```apex
Integer depth = [
    SELECT COUNT() FROM AsyncApexJob
    WHERE JobType = 'BatchApex'
    AND Status IN ('Holding', 'Queued', 'Processing', 'Preparing')
];
if (depth >= 95) { /* log and abort */ return; }
Database.executeBatch(new NextBatch(), 200);
```

---

## Gotcha 2: Test.stopTest() Only Executes One Synchronous Chain Level

**What happens:** Inside a `@isTest` method, `Test.stopTest()` forces the first enqueued batch job to run synchronously. However, any `Database.executeBatch` or `System.enqueueJob` call made from inside that job's `finish()` method is NOT driven synchronously by `stopTest()`. The downstream job is queued but never executed within the test transaction.

**When it occurs:** Any test that tries to assert on the state produced by the second or later link in a chain. The assertions fail because the downstream batch never ran — not because the logic is wrong.

**How to avoid:** Test each batch class in isolation with its own test method. Do not write a single test that tries to verify the full end-to-end chain. For the `finish()` method, use a test flag (`Test.isRunningTest()`) or a constructor-injected mock to verify that `Database.executeBatch` was called with the correct arguments without actually executing the downstream job.

---

## Gotcha 3: Confusing Database.Stateful Scope with Cross-Job State

**What happens:** `Database.Stateful` preserves instance variable values between `execute()` scope chunks **within a single batch job**. It does NOT persist state to the next job in a chain. Developers sometimes assume that making a batch class `Database.Stateful` means its fields will be available to the job chained from `finish()`.

**When it occurs:** When a batch class accumulates counts or error records using `Database.Stateful` and the developer tries to pass that accumulated data to the next job by referencing `this.someField` inside `finish()` — which actually does work correctly since `finish()` is part of the same job's context. The gotcha is the opposite assumption: that the *next* job will somehow inherit the previous job's stateful instance. It will not — each `Database.executeBatch` creates a fresh instance.

**How to avoid:** Pass state forward explicitly via the constructor of the chained job:

```apex
public void finish(Database.BatchableContext bc) {
    // CORRECT: pass accumulated state via constructor
    Database.executeBatch(new StepTwoBatch(this.processedCount, this.errorIds), 200);
    // WRONG: next job will not have access to this.processedCount otherwise
}
```

For larger state objects, persist to a staging SObject and let the next job query it in `start()`.

---

## Gotcha 4: Calling System.scheduleBatch() Instead of Database.executeBatch() for Immediate Chaining

**What happens:** `System.scheduleBatch()` schedules a batch to run at a minimum delay of 1 minute (the minimum interval is ~1 minute by platform contract). Using it inside `finish()` as a "chain" means the next job is not immediate — it is scheduled. This delays pipelines and adds an unnecessary CronTrigger entry.

**When it occurs:** Developers who discovered `System.scheduleBatch()` and use it everywhere without understanding the distinction. Also common when copy-pasting from scheduled-batch examples that predate the `finish()` chaining pattern.

**How to avoid:** Use `Database.executeBatch()` inside `finish()` for immediate chaining. Reserve `System.scheduleBatch()` for cases where a genuine time-delay between steps is required (e.g., wait for external system synchronization).

---

## Gotcha 5: Infinite Chain Due to Missing Terminal Condition

**What happens:** A batch class whose `finish()` unconditionally re-enqueues itself (or re-enqueues a job that eventually calls back to the same class) creates an infinite loop of batch jobs. Each job consumes Flex Queue capacity, execution slots, and governor resources. Because the chain grows without a terminal condition, the org's Flex Queue saturates within hours.

**When it occurs:** "Self-healing" or "poll until done" patterns implemented as a batch that re-enqueues itself with the same query. Also occurs with copy-paste errors where a developer chains Job A → B → A again.

**How to avoid:** Every chain implementation must have an explicit terminal condition checked before enqueuing. Common patterns:
- A step counter passed through the constructor: stop when `step > MAX_STEPS`.
- A query result count: stop when the start query returns 0 records.
- A Custom Setting flag: stop when `Chain_Config__c.Enabled__c == false`.
