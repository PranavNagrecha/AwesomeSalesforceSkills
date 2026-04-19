---
name: apex-batch-chaining
description: "Use this skill when you need to run one Batch Apex job immediately after another completes — chaining via finish(), managing Flex Queue capacity, or choosing between batch-to-batch chaining and a Queueable bridge. NOT for async job technology selection — use the async-selection decision tree. NOT for single-job batch patterns, scope sizing, or Database.Stateful design — use batch-apex-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance Efficiency
triggers:
  - "chain batch jobs apex finish"
  - "run batch after batch completes"
  - "flex queue capacity check before executeBatch"
  - "database executeBatch from finish method"
  - "schedule next batch after current batch finishes"
  - "queueable alternative to batch chaining"
tags:
  - batch-apex
  - batch-chaining
  - flex-queue
  - async
inputs:
  - "The batch class(es) to be chained in sequence"
  - "Any state that must be passed between chained jobs (record IDs, counters, error lists)"
  - "Expected volume of jobs to be enqueued — needed to assess Flex Queue risk"
outputs:
  - "Apex finish() implementation with FlexQueue capacity guard"
  - "Optional Queueable bridge for unlimited-depth or conditional chaining"
  - "Review checklist for test-class coverage and governor limit exposure"
dependencies:
  - batch-apex-patterns
  - apex-queueable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex Batch Chaining

This skill activates when a practitioner needs to trigger one or more Batch Apex jobs in a controlled sequence — using `finish()` callbacks, Flex Queue guards, or a Queueable bridge — and must avoid silent job-queue saturation or loss of intermediate state.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm you actually need chaining: if you only have one large job, use `batch-apex-patterns` instead.
- Know how many concurrent and queued batch jobs already exist in the org — the Flex Queue holds a maximum of 100 jobs and only 5 can execute concurrently. A chain that submits blindly can silently fail or delay.
- Identify whether intermediate state must pass between jobs. `Database.Stateful` keeps state inside a single job; you need a different mechanism (Custom Settings, Custom Metadata, a temporary SObject, or a constructor parameter) to pass state between chained jobs.
- Confirm the API version is 26.0 or later — `Database.executeBatch` from `finish()` was introduced at API v26.0.

---

## Core Concepts

### finish() as the Chain Trigger

Every Batch Apex class implements three interface methods: `start()`, `execute()`, and `finish()`. The `finish(Database.BatchableContext bc)` method is called exactly once after all `execute()` scope chunks complete. Calling `Database.executeBatch(new NextBatch())` inside `finish()` is the standard, platform-supported mechanism for chaining. The returned `Id` is the `AsyncApexJob` Id of the newly enqueued job — capture it if you need to monitor downstream status.

Chaining from `finish()` is synchronous from the perspective of your code but fully asynchronous from the platform's perspective. The new job enters the **Flex Queue** and waits for an execution slot.

### The Flex Queue and the 5-Concurrent-Job Ceiling

Before the Flex Queue was introduced, Salesforce enforced a hard 5-concurrent-batch limit that caused `Database.executeBatch` to throw a `LimitException` when the ceiling was hit. The Flex Queue removed that hard throw: jobs now queue silently behind the 5 active slots. The Flex Queue can hold up to **100 jobs** (holding + active combined in a single org).

The risk is that silent queuing makes it easy to saturate the queue in high-volume orgs. A chain that checks `System.FlexQueue.getJobIds().size()` before each `Database.executeBatch` call catches saturation before it becomes a production incident.

### Queueable as an Unlimited-Depth Alternative

A Queueable class can enqueue a new Queueable from inside its own `execute()` method — this is the standard recursive Queueable pattern. The depth limit per transaction is **1 child Queueable** per `execute()` call, but there is no enforced total chain depth at the platform level. Queueable chains are therefore preferred when:
- The number of chain steps is not known at design time.
- You need to pass complex typed state between steps (Queueable constructors accept any serializable type).
- Each step must conditionally decide whether to enqueue the next step.

Queueable chains have their own governor context per `execute()` invocation, just like batch. The trade-off is that Queueable does not chunk records the way Batch does — if a step processes large data sets you still need a batch class for that step, with a Queueable acting only as the coordinator.

### Test Limitations

`Test.startTest()` / `Test.stopTest()` forces **one synchronous chain level**: the first batch job runs synchronously at `stopTest()`, but any job enqueued from within `finish()` does not run synchronously in the same test. This means full multi-step chains **cannot be unit-tested end-to-end** in a single test method. The correct approach is to test each link in isolation with its own test method, verifying that `finish()` calls `Database.executeBatch` (or `System.enqueueJob`) with the expected arguments. Use `Test.getStandardPricebookId()` / `Test.isRunningTest()` guards where needed.

---

## Common Patterns

### Pattern 1: Two-Step Chain with Flex Queue Guard

**When to use:** You have exactly two batch jobs that must run in sequence and you want the simplest possible implementation.

**How it works:**

```apex
public class StepOneBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account WHERE ...]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // process scope
    }

    public void finish(Database.BatchableContext bc) {
        // Guard: Flex Queue must have room before chaining
        Integer queuedJobs = [
            SELECT COUNT() FROM AsyncApexJob
            WHERE JobType = 'BatchApex'
            AND Status IN ('Holding', 'Queued', 'Processing', 'Preparing')
        ];
        if (queuedJobs >= 95) {
            // Log and alert — do not chain into a saturated queue
            System.debug(LoggingLevel.ERROR,
                'StepOneBatch: Flex Queue near capacity (' + queuedJobs +
                '). StepTwoBatch NOT enqueued.');
            return;
        }
        Database.executeBatch(new StepTwoBatch(), 200);
    }
}
```

**Why not blindly call executeBatch:** Without the guard, a saturated queue accepts the job silently but the job sits in `Holding` status indefinitely. Monitoring alerts will not fire until a human reviews the queue.

### Pattern 2: Queueable Coordinator for Multi-Step Chains

**When to use:** Three or more steps, or when each step must decide conditionally whether to proceed.

**How it works:**

```apex
public class BatchChainCoordinator implements Queueable {
    private Integer step;
    private Id contextId; // pass state between steps

    public BatchChainCoordinator(Integer step, Id contextId) {
        this.step = step;
        this.contextId = contextId;
    }

    public void execute(QueueableContext ctx) {
        if (step == 1) {
            Database.executeBatch(new StepOneBatch(contextId), 200);
        } else if (step == 2) {
            Database.executeBatch(new StepTwoBatch(contextId), 200);
        } else if (step == 3) {
            Database.executeBatch(new StepThreeBatch(contextId), 200);
        }
        // Queueable does NOT chain itself here — the batch finish() calls:
        // System.enqueueJob(new BatchChainCoordinator(step + 1, contextId));
    }
}
```

Each batch's `finish()` method calls:

```apex
public void finish(Database.BatchableContext bc) {
    System.enqueueJob(new BatchChainCoordinator(2, this.contextId));
}
```

**Why this works better than pure batch-to-batch chaining:** The coordinator owns all routing logic in one place. Adding a step means editing one class, not modifying every batch's `finish()`. Conditional skipping (e.g., skip step 3 if no records were processed) is easy to add.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two sequential batch jobs, simple state passing via constructor | Direct `finish()` chain with Flex Queue guard | Simplest; no extra class needed |
| Three or more sequential batch jobs | Queueable coordinator + batch `finish()` → `enqueueJob()` | Centralizes routing; avoids modifying every finish() when chain grows |
| Chain steps unknown at design time (dynamic depth) | Queueable chain — each step decides whether to enqueue next | Only Queueable supports fully open-ended depth without design-time limit |
| Need to pass complex typed objects between steps | Queueable constructor parameters | Batch constructor accepts typed args but Queueable makes this the primary state-passing mechanism |
| Chain must survive test coverage requirements with full path coverage | Separate unit tests per batch class | Test.stopTest() only runs one synchronous level — end-to-end integration testing requires a sandbox run |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner implementing batch chaining:

1. **Confirm chaining is the right choice** — check `standards/decision-trees/async-selection.md`. If the job is a single large dataset, `batch-apex-patterns` is sufficient. If real-time triggering is needed, consider Platform Events.
2. **Assess Flex Queue headroom** — query `AsyncApexJob` for `Status IN ('Holding','Queued','Processing','Preparing')` in the target org. If count is near 90, implement a hard guard before any `Database.executeBatch` call in `finish()`.
3. **Choose chain architecture** — two steps and simple state: direct `finish()` chain. Three or more steps, conditional logic, or unknown depth: Queueable coordinator pattern.
4. **Implement state transfer** — do NOT rely on `Database.Stateful` across jobs. Pass state via constructor parameters (primitive types or serializable classes). For large state, persist to a staging SObject or Custom Setting and query it in the next job's `start()`.
5. **Write unit tests per batch class** — test each class independently. Assert that `finish()` calls `Database.executeBatch` (or `System.enqueueJob`) with correct arguments using a test flag or mock. Do not attempt to run the full chain in a single test method.
6. **Add AsyncApexJob monitoring** — query `AsyncApexJob` by the returned `Id` from `Database.executeBatch` to confirm each job reaches `Completed` status. Log `NumberOfErrors` and `ExtendedStatus` fields to your custom logging framework.
7. **Review with the checklist below** before deploying to production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every `Database.executeBatch` call in `finish()` is guarded by a Flex Queue size check
- [ ] State passed between chained jobs uses constructor parameters or a staging SObject — NOT `Database.Stateful` across job boundaries
- [ ] Each batch class in the chain has its own unit test; no test attempts to assert the full multi-step chain in one `Test.startTest()/stopTest()` block
- [ ] The `Id` returned by `Database.executeBatch` is captured and logged so downstream job status can be monitored
- [ ] There is an alerting/abort path when the Flex Queue guard fires (not a silent no-op)
- [ ] Chain does not have the potential to recurse infinitely — a step counter or terminal condition is present

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent Flex Queue saturation** — `Database.executeBatch` no longer throws a `LimitException` when the org has many queued jobs. If the Flex Queue already holds 100 jobs, the call silently returns null (or throws `AsyncException` depending on context). Without a guard, the chain step is lost with no error surfaced to the calling code.
2. **Test.stopTest() only runs one synchronous batch level** — calling `Test.stopTest()` inside a test method forces the first batch job to run synchronously, but any `Database.executeBatch` or `System.enqueueJob` call made from within that job's `finish()` is NOT executed synchronously. Tests that assert on a downstream job's effects will always fail.
3. **5-concurrent-job limit still governs execution slots** — even with the Flex Queue, only 5 batch jobs can run concurrently per org. A chain that submits many small jobs rapidly fills the execution slots and leaves later jobs in `Holding` status. Size scope appropriately to keep each job's wall-clock time reasonable.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `finish()` implementation | Guarded chain trigger using `Database.executeBatch` with Flex Queue size check |
| `BatchChainCoordinator` Queueable | Optional coordinator class for multi-step or conditional chains |
| Unit test per batch class | Isolated test asserting correct chaining behavior without full end-to-end execution |

---

## Related Skills

- `batch-apex-patterns` — scope sizing, `Database.Stateful`, `QueryLocator` vs `Iterable`, and single-job batch design; read this first before chaining
- `apex-queueable-patterns` — Queueable interface, `System.enqueueJob`, and child-job limits; used when building the Queueable coordinator
- `apex-transaction-finalizers` — for cleanup logic after Queueable step failures inside a chain
- `async-apex` — high-level comparison of all async mechanisms; useful for initial technology selection
