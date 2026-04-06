---
name: governor-limit-recovery-patterns
description: "Recovering from and preventing Apex governor limit errors: proactive Limits class checkpoints, savepoint-based partial recovery, BatchApexErrorEvent scope recovery, CPU timeout analysis, limit-safe coding patterns. Use when diagnosing LimitException failures or designing limit-safe Apex. NOT for general limits overview (use limits-and-scalability-planning). NOT for bulkification patterns (use governor-limits)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "Apex transaction is throwing System.LimitException and I need to prevent or recover from it"
  - "How do I use savepoints to roll back part of a transaction when a limit is about to be hit"
  - "How to check how many SOQL queries or DML statements have been used so far in a transaction"
  - "BatchApexErrorEvent not firing or scope recovery not working after a batch scope failure"
  - "CPU time limit exceeded in Apex and I need to budget or diagnose the bottleneck"
tags:
  - governor-limits
  - LimitException
  - savepoints
  - bulkification
  - limits-class
  - BatchApexErrorEvent
  - apex
  - reliability
inputs:
  - Apex class or trigger exhibiting LimitException failures in production or sandbox
  - Batch Apex job scope size and current error behavior
  - Transaction context (synchronous, async, batch, queueable) where limits are being hit
outputs:
  - Instrumented Apex code using Limits class checkpoints for proactive limit detection
  - Savepoint-based partial-recovery code pattern with documented rollback constraints
  - BatchApexErrorEvent handler for post-scope-failure recovery
  - Decision table for choosing the right recovery strategy per execution context
dependencies:
  - governor-limits
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Governor Limit Recovery Patterns

This skill activates when an Apex transaction is at risk of or has already hit a governor limit, and the goal is to detect headroom, recover partially, or reroute work before or after the limit terminates the transaction. It covers in-flight recovery mechanics and limit budgeting — not general bulkification design (see `governor-limits`) and not infrastructure-level limits planning.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the execution context: synchronous (trigger/VF controller), asynchronous (future/queueable), batch (Database.Batchable), or scheduled. Each context has different limit ceilings and recovery options.
- The most common wrong assumption is that `try/catch` can intercept a `LimitException`. It cannot. `System.LimitException` is uncatchable — the transaction terminates immediately with a full rollback the moment the limit is exceeded. Recovery must happen proactively, before the limit is breached.
- Know which limits are in play for the context: SOQL queries (100 sync / 200 async), DML statements (150), heap size (6 MB sync / 12 MB async), CPU time (10 000 ms sync / 60 000 ms async), callouts (100), future calls (50).

---

## Core Concepts

### The Limits Class: Proactive Headroom Checks

The `System.Limits` class exposes the current consumed count and the ceiling for each governor limit within the running transaction. Every method comes in a pair:

- `Limits.getQueries()` — queries consumed so far
- `Limits.getLimitQueries()` — ceiling (100 sync, 200 async)

The same pattern applies to DML (`getDMLStatements` / `getLimitDMLStatements`), CPU time (`getCpuTime` / `getLimitCpuTime`), heap (`getHeapSize` / `getLimitHeapSize`), callouts (`getCallouts` / `getLimitCallouts`), and others.

The canonical safety idiom is to compute remaining headroom before performing work:

```apex
Integer remaining = Limits.getLimitQueries() - Limits.getQueries();
if (remaining < 5) {
    // defer work or throw a controlled exception
}
```

This check must happen inside the loop or batch-processing block, not just at the entry point of the method, because limit consumption is cumulative and linear.

### Database.Savepoint and Partial Transaction Recovery

`Database.setSavepoint()` captures a named rollback target within the transaction. `Database.rollback(sp)` reverts all DML that occurred after that savepoint, including inserted record IDs — but with critical caveats:

- The platform allows a maximum of **5 savepoints per transaction**. Each call to `setSavepoint()` counts as one DML statement itself, consuming both the DML and savepoint quotas.
- After `rollback()`, the sObject variables in Apex memory still carry the IDs that were assigned by the failed DML. The ID field is NOT cleared. Code that inspects `record.Id != null` as a "was this inserted?" check will produce a false positive after rollback.
- Static variables are not reset on rollback. Any state cached in static maps or counters before the rollback point remains in memory, which can cause logic errors if those caches are not explicitly cleared.
- Savepoints cannot cross async boundaries. A savepoint set in a synchronous context is invalid in a future method or queueable spawned from that context.

Typical use: wrap a risky bulk DML block in a savepoint, check limit headroom inside the block, and roll back if the threshold is crossed.

### BatchApexErrorEvent for Scope-Level Recovery

When a batch scope (execute method) throws an uncaught exception, the platform fires a `BatchApexErrorEvent` platform event. A separate trigger or process subscribed to this event can perform compensating logic — alerting, requeuing the failed records, or logging the partial state.

Key implementation detail: the event payload includes `JobScope` (a CSV of record IDs in the failed scope) and `DoesExceedJobScopeMaxLength` (a boolean). When `DoesExceedJobScopeMaxLength` is `true`, `JobScope` is truncated and cannot be used for record-level recovery — the handler must fall back to a re-query strategy using the job ID and a status field.

This pattern decouples error observation from error recovery: the batch job remains simple, and the compensation logic lives in an event-driven subscriber.

---

## Common Patterns

### Pattern 1: Limit Budget Checkpoint Inside a Loop

**When to use:** Processing a list of records where each iteration may issue SOQL, DML, or callouts, and the total record count could push total consumption near the ceiling.

**How it works:**

```apex
public void processRecords(List<SObject> records) {
    for (SObject rec : records) {
        // Check headroom before each expensive operation
        if (Limits.getLimitQueries() - Limits.getQueries() < 3) {
            // Log what is being skipped; enqueue remaining records
            System.debug(LoggingLevel.WARN, 'SOQL headroom exhausted at record ' + rec.Id);
            break;
        }
        // perform queries and DML
        doWork(rec);
    }
}
```

**Why not the alternative:** Letting the loop run until `LimitException` fires means a full rollback with zero partial results and no opportunity to log what was processed. Checking headroom lets the code preserve the progress already committed and enqueue only the remaining work.

### Pattern 2: Savepoint-Guarded DML Block

**When to use:** A multi-step DML sequence (insert parent, then insert children) where child insertion might fail due to limit pressure, and you want to atomically undo the parent insert rather than leave orphaned records.

**How it works:**

```apex
Savepoint sp = Database.setSavepoint();
try {
    insert parentRecord;
    // Check DML headroom before child insert
    if (Limits.getLimitDMLStatements() - Limits.getDMLStatements() < 2) {
        Database.rollback(sp);
        // Enqueue for retry; parentRecord.Id is still set in memory — do not trust it
        parentRecord.Id = null; // manually clear to avoid false-positive ID check
        AsyncRetryQueueable.enqueue(parentRecord);
        return;
    }
    insert childRecords;
} catch (DmlException e) {
    Database.rollback(sp);
    throw e; // re-throw after cleanup
}
```

**Why not the alternative:** Without the savepoint, a DML limit hit on child insert leaves the parent record committed but orphaned. Without manually clearing `parentRecord.Id`, downstream code may incorrectly believe the record was successfully inserted.

### Pattern 3: BatchApexErrorEvent Subscriber for Scope Recovery

**When to use:** A batch job processes large volumes and scope-level failures must be logged and retried without manual intervention.

**How it works:**

```apex
trigger BatchApexErrorEventHandler on BatchApexErrorEvent (after insert) {
    for (BatchApexErrorEvent evt : Trigger.new) {
        if (evt.DoesExceedJobScopeMaxLength) {
            // JobScope is truncated — fall back to status field query
            List<MyObject__c> failed = [
                SELECT Id FROM MyObject__c
                WHERE BatchJobId__c = :evt.AsyncApexJobId
                AND Status__c = 'Pending'
            ];
            // requeue failed
        } else {
            List<Id> failedIds = evt.JobScope.split(',');
            // process by ID
        }
    }
}
```

**Why not the alternative:** Relying solely on batch `finish()` to detect failures means you cannot distinguish which scope chunks failed or retry at record granularity. `BatchApexErrorEvent` gives scope-level fidelity.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Synchronous trigger at risk of hitting SOQL limit inside loop | Limits class checkpoint + break + queueable enqueue | Can't catch LimitException; must detect before breach |
| Multi-step DML that must be atomic on limit hit | Database.setSavepoint() before first DML, rollback on limit check failure | Prevents orphaned parent records without relying on catchable exception |
| Batch scope fails unpredictably and records need retry | BatchApexErrorEvent trigger subscriber | Decouples recovery from batch job logic; handles scope truncation |
| CPU time approaching limit in complex computation | Limits.getCpuTime() checkpoint + early exit | CPU LimitException is uncatchable; proactive exit preserves partial results |
| Async (queueable/future) hitting SOQL limit | Limits checkpoint before each query, chain to next queueable if headroom low | Async contexts have higher ceilings but still hit LimitException on breach |
| Savepoint limit (5 per transaction) about to be reached | Redesign to a single savepoint per logical unit; avoid nested savepoints | Exceeding 5 savepoints throws LimitException like any other limit |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the execution context (synchronous, async, batch, scheduled) and look up the exact limit ceilings for that context from the Apex Developer Guide limits reference table.
2. Instrument the failing code with `Limits.*` calls at the entry point and before each loop iteration to capture headroom values in debug logs; identify which limit is actually being exhausted and at which record index.
3. Determine the appropriate recovery strategy: Limits checkpoint with early exit and queueable enqueue (for loops), savepoint-guarded DML block (for multi-step atomic DML), or BatchApexErrorEvent subscriber (for batch scope failures).
4. If using savepoints, verify the total savepoint count in the transaction is below 5 and explicitly null out sObject Id fields after rollback to prevent false-positive ID checks.
5. If using BatchApexErrorEvent, handle the `DoesExceedJobScopeMaxLength` flag — do not attempt to parse `JobScope` when this is true.
6. Write unit tests that assert the recovery path is taken when limits are artificially constrained using Test.setMock patterns or by constructing a dataset large enough to trigger the checkpoint.
7. Run the Apex debug log with log level FINEST on the Apex category and verify that limit checkpoint messages appear and no `LimitException` is thrown.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No bare `try/catch(Exception e)` block is relied upon to intercept `LimitException` — recovery logic is proactive
- [ ] All `Limits.*` checkpoints are inside loops or just before expensive operations, not only at method entry
- [ ] Savepoint count in the transaction does not exceed 5; each `setSavepoint()` is counted against the DML statement limit
- [ ] After every `Database.rollback()`, sObject Id fields that were set by the rolled-back DML are explicitly cleared
- [ ] Static variable caches that may have been updated before a rollback are reset alongside the rollback
- [ ] BatchApexErrorEvent handler checks `DoesExceedJobScopeMaxLength` before parsing `JobScope`
- [ ] Unit tests exercise the headroom-exceeded branch, not just the happy path

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LimitException is uncatchable** — Unlike `DmlException` or `CalloutException`, `System.LimitException` cannot be caught with any `try/catch` block. The transaction is immediately terminated and fully rolled back. Any code relying on catching this exception to "handle" a limit breach will silently miss the exception and leave no trace. Recovery must be designed to never reach the limit.
2. **Savepoint rollback does not clear sObject Id fields** — After `Database.rollback(sp)`, the in-memory sObject variable retains the ID assigned by the pre-rollback insert. Checking `record.Id != null` as a "was this persisted?" guard produces a false positive, causing downstream code to treat rolled-back records as successfully inserted.
3. **Static variables survive rollback** — The Limits class and DML/SOQL state reset on rollback, but static variables in Apex classes do not. Any accumulator, ID set, or cache built in a static context before the rollback point persists. This causes logic errors where rolled-back records reappear in caches used by subsequent processing.
4. **Each setSavepoint() consumes a DML statement** — The savepoint quota (5 per transaction) is separate from DML, but every `setSavepoint()` call also counts as one DML statement. In a tight DML budget scenario, savepoint use accelerates DML statement consumption.
5. **BatchApexErrorEvent JobScope is truncated silently** — When a batch scope contains enough record IDs to overflow the field length, `DoesExceedJobScopeMaxLength` is set to `true` and `JobScope` is cut off mid-string. Handlers that split on comma without checking this flag will process an incomplete and potentially malformed ID list.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Instrumented Apex with Limits checkpoints | Code with `Limits.*` calls placed inside processing loops, logging headroom and exiting gracefully before limit breach |
| Savepoint recovery block | Apex snippet using `Database.setSavepoint()` and `Database.rollback()` with explicit Id field cleanup and static cache reset |
| BatchApexErrorEvent trigger | Apex trigger on `BatchApexErrorEvent` that handles both normal and truncated-scope cases for scope-level retry |
| Limit budget decision table | Per-context (sync/async/batch) table of limit ceilings and recommended checkpoint thresholds |

---

## Related Skills

- `governor-limits` — Bulkification and general limit-avoidance design patterns; use when the problem is architectural (looping DML, SOQL in loops) rather than in-flight recovery
- `batch-apex-patterns` — Batch job structure, chunking strategy, and state management; use alongside this skill when designing batch retry flows
- `error-handling-framework` — Platform-wide exception handling and logging; use for the logging layer that supports limit checkpoint alerting
- `async-apex` — Queueable and future method patterns; use when the recovery strategy involves deferring work to an async context
