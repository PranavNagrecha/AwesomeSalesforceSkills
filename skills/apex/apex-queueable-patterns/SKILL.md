---
name: apex-queueable-patterns
description: "Use when designing, implementing, reviewing, or debugging Queueable Apex jobs that chain, use the Finalizer interface, pass state across transactions, or need controlled async depth. Trigger keywords: 'Queueable', 'System.enqueueJob', 'Finalizer', 'QueueableContext', 'AsyncOptions', 'stack depth', 'chained queueable', 'DuplicateMessageException', 'QueueableDuplicateSignature', 'AsyncInfo', 'MinimumQueueableDelayInMinutes', 'attachFinalizer', 'AsyncApexJob'. NOT for choosing Queueable vs Batch — use apex/async-apex. NOT for large-volume chunked record processing — use apex/batch-apex-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - queueable
  - async-apex
  - finalizer
  - job-chaining
  - stack-depth
  - transaction-control
inputs:
  - "Apex class implementing Queueable (or the design intent for one)"
  - "Whether chaining, callouts, Finalizer, or state passing are required"
  - "Operational requirements: retry behavior, failure handling, monitoring needs"
outputs:
  - "Queueable implementation design or review findings"
  - "Chaining pattern scaffold with Finalizer for error handling"
  - "State-passing strategy and governor limit guidance"
triggers:
  - "how do I chain queueable jobs in Apex without hitting stack depth limits"
  - "my queueable job is failing silently with no error in logs"
  - "how do I use the Finalizer interface to handle queueable failures"
  - "queueable job not making callouts as expected"
  - "how do I pass state between chained queueable jobs"
  - "stop the same queueable job being enqueued twice from different transactions"
  - "write a queueable class that processes a set of record ids in chunks"
  - "too many queueable jobs added to the queue error from a trigger"
  - "test a queueable job and assert it actually ran"
  - "enqueue a queueable from an apex trigger without breaking a data load"
  - "delay a queueable job retry instead of scheduling apex"
  - "queueable job shows completed in Apex Jobs but nothing changed"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-09-16
---

# Apex Queueable Patterns

Use this skill when designing or reviewing Apex jobs that use the Queueable interface for controlled async execution, multi-step chaining, outbound callouts, or error recovery through the Finalizer interface. The skill covers implementation patterns, stack depth management, state passing, and production-safe failure handling.

---

## Before Starting

- Is the use case a single deferred operation, a multi-step chain, or a fan-out? Each has a different pattern.
- Does the job require callouts? If so, `Database.AllowsCallouts` must also be implemented.
- How deep can the chain realistically grow? Only Developer Edition and Trial orgs cap it for you — "the maximum stack depth for chained jobs is 5, which means that you can chain jobs four times" (`apexdev` L16182-16185). Production editions enforce no depth limit, so the cap must come from `AsyncOptions.MaximumQueueableStackDepth` plus a counter carried in the constructor.
- Does the job need to recover from failure or enqueue a follow-up regardless of success or failure? That is what the Finalizer interface is for.
- How is state passed between chained jobs? Serialized fields or record IDs are the safe options.

---

## Questions to Ask Before Configuring

Ask these before the first `implements Queueable` is written. Each traces to a
gotcha in `references/gotchas.md`; an agent that skips them ships a job that
deploys, passes its tests, and shows `Completed` in Apex Jobs while the data sits
untouched.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Where is this enqueued from — a trigger, a Lightning controller, a batch `finish()`, or a finalizer?" | The ceiling differs by context: 50 enqueues per synchronous transaction, exactly 1 per asynchronous transaction (`apexdev` L16179-16181, L19573). A per-record loop in a trigger fails on the 51st record, not the 2nd | The one call site that owns the enqueue, and whether the code path is ever reached from inside another job |
| "What is the largest number of records one enqueue can be asked to cover?" | It decides the chunk size and therefore the chain length. One async transaction gets 200 SOQL queries, 150 DML statements and 12 MB heap (`apexdev` L19546, L19553, L19576) | A chunk size, the resulting link count, and whether that count is still under the depth cap |
| "Can the same logical work be enqueued twice from two different transactions?" | A static guard resets at the transaction boundary (`apexdev` L3738-3740). Cross-transaction suppression needs `AsyncOptions.DuplicateSignature`, and a suppressed enqueue *throws* `DuplicateMessageException` rather than returning quietly | The stable business key the signature is built from, and the `catch` that turns the exception into a no-op instead of failed DML |
| "Does anything in this job call an external system, and does it also write records?" | The marker interface grants permission, not ordering: callouts are impossible after DML in the same transaction (`apexdev` L35860-35862) | The order inside `execute()`, and whether the callout and the DML need to be split across two jobs |
| "When this job throws, what must still happen?" | `try/catch` cannot survive a limit exception that terminates the transaction. A Finalizer runs either way, and its budget is five consecutive re-enqueues (`apexdev` L16291-16294) | Whether a Finalizer is needed at all, and what it does on `SUCCESS` versus `UNHANDLED_EXCEPTION` |
| "Who runs this, and are they in system mode?" | Outside system mode the running user needs View Setup and Configuration to enqueue asynchronous Apex at all (`object_reference` L42269-42271); and from API 67.0 an undeclared class runs `with sharing` where it used to run without (`apexdev` L4961-4967) | The explicit sharing declaration, the permission set that carries the enqueue, and the persona the test matrix must cover |
| "How will anyone prove tomorrow that this ran, and how far it got?" | `AsyncApexJob` records that a job ended, not what it decided. `JobItemsProcessed` and `TotalJobItems` are always zero for Queueable (`apexdev` L16012-16013) and `Status = 'Holding'` never appears (`object_reference` L42423-42429) | The log row each terminal path writes, and the `AsyncApexJob` query the runbook will actually paste |

What a proper configuration adds over just calling `System.enqueueJob`: the depth
cap and the duplicate signature exist at one call site instead of N, so no future
caller can omit them; a guard that stops the chain leaves a durable row instead
of a silent `return`; and the tests assert on the decision the job recorded
rather than on how many chain levels the test runtime happened to drive.

---

## Core Concepts

### The Queueable Interface

A Queueable class implements `Queueable` and defines a single `execute(QueueableContext ctx)` method. The job is enqueued with `System.enqueueJob(new MyJob())` and runs asynchronously in a separate transaction under the *asynchronous* limit column — 200 SOQL queries (not the synchronous 100), 150 DML statements, 12 MB heap, and 60,000 ms CPU time (`apexdev` L19546, L19553, L19576-19578). The job Id returned by `enqueueJob` "corresponds to the ID of the AsyncApexJob record" (`apexdev` L15965-15967), which is what makes a Queueable monitorable where a `@future` method is not.

Adding `Database.AllowsCallouts` to the `implements` clause is required for any Queueable that makes HTTP or web service callouts: "Apex allows HTTP and web service callouts from queueable jobs, if they implement the Database.AllowsCallouts marker interface. In queueable jobs that implement this interface, callouts are also allowed in chained queueable jobs." (`apexdev` L16164-16165). The interface grants permission only — it does not reorder the transaction, so a callout still cannot follow DML inside the same `execute()` (`apexdev` L35860-35862).

UNVERIFIED (2026-09-05): the exact runtime failure when the interface is missing — commonly reported as `System.CalloutException: Callout not allowed from this future method` — is not stated in either extracted guide. The requirement is grounded; the message text is not.

### Chaining And Stack Depth

A Queueable can enqueue exactly one child job from within its `execute()` method: "When chaining jobs with System.enqueueJob, you can add only one job from an executing job. Only one child job can exist for each parent queueable job. Starting multiple child jobs from the same queueable job is not supported." (`apexdev` L16186-16188). The synchronous ceiling is different and much higher — 50 enqueues in one synchronous transaction (`apexdev` L16179-16181) — which is why a per-record enqueue in a trigger passes every small test and fails on the first bulk load.

UNVERIFIED (2026-09-05): the exception text `System.LimitException: Too many queueable jobs added to the queue: 2` is widely reported but appears in neither extracted guide, and neither guide states whether the single-child rule is enforced during `Test.stopTest()` execution. Do not treat a passing chained-job test as evidence either way.

"Because no limit is enforced on the depth of chained jobs, you can chain one job to another" — in every edition except Developer and Trial, where the ceiling is a stack depth of 5. That asymmetry is the trap: a runaway chain is *caught* in a scratch org or Developer Edition sandbox and *not caught* in production. The `AsyncOptions` class supplies the cap the production org will not:

```apex
AsyncOptions opts = new AsyncOptions();
opts.MaximumQueueableStackDepth = 5;
System.enqueueJob(new MyJob(nextPayload), opts);
```

`System.AsyncInfo.getCurrentQueueableStackDepth()` returns the current depth so the job can stop or branch safely. Together these two APIs are the canonical pattern for bounded chaining in production code (Apex Developer Guide — Queueable Apex).

### Delayed Enqueue And Cross-Transaction Deduplication

`AsyncOptions` carries two properties beyond `MaximumQueueableStackDepth`, and both are hard rules.

**`MinimumQueueableDelayInMinutes`** is the supported back-off primitive: "Use the System.enqueueJob(queueable, delay) method to add queueable jobs to the asynchronous execution queue with a specified minimum delay (0–10 minutes)." An org-wide floor is set at **Setup → Apex Settings → "Default minimum enqueue delay (in seconds) for queueable jobs that do not have a delay parameter"** (1–600 seconds). An explicit delay **"ignores any org-wide enqueue delay setting"** — the two never compose, so passing `0` runs as fast as the platform allows even under a 600-second org floor. Read the effective value with `System.AsyncInfo.getMinimumQueueableDelayInMinutes()`.

**`DuplicateSignature`** suppresses duplicate enqueues *across transactions*, which a static guard cannot. Build it with `new System.QueueableDuplicateSignature.Builder()` plus `addId()` / `addString()` / `addInteger()`, then `build()` (`apexrefguide` L227456-227461; the Developer Guide sample at `apexdev` L16243-16248 omits the `new` — prefer the Reference Guide form). A second enqueue with the same signature throws `DuplicateMessageException`: `Attempt to enqueue job with duplicate queueable signature`. See `references/gotchas.md` for the release-at-dequeue semantics.

Two ceilings bound any retry loop built on these: the delay caps at 10 minutes, and a job failing on an unhandled exception "can be successively re-enqueued five times by a transaction finalizer." Anything longer or deeper needs Scheduled Apex or a staging record.

### The Finalizer Interface

The Finalizer interface (`System.Finalizer`) runs after the parent Queueable completes, whether it succeeded or threw. "The Queueable job and the Finalizer run in separate Apex and Database transactions" (`apexdev` L16296-16297) — but not under async limits: "Synchronous governor limits apply for the Finalizer transaction, except in these cases where asynchronous limits apply: Total heap size; Maximum number of Apex jobs added to the queue with System.enqueueJob; Maximum number of methods with the future annotation" (`apexdev` L16297-16303). Attach it with `System.attachFinalizer(new MyFinalizer())` as the first statement of `execute()`, so that code failing later still reaches it.

`FinalizerContext` has exactly four methods (`apexdev` L16311-16344) — and `getJobId()` is **not** one of them:

| Method | Returns |
|---|---|
| `ctx.getAsyncApexJobId()` | The `AsyncApexJob` Id of the parent Queueable |
| `ctx.getRequestId()` | The request Id, shared with the parent job, correlatable with Event Monitoring |
| `ctx.getResult()` | `ParentJobResult.SUCCESS` or `ParentJobResult.UNHANDLED_EXCEPTION` |
| `ctx.getException()` | The exception that terminated the parent; `null` otherwise |

`getJobId()` belongs to `QueueableContext`, which has that one method and nothing else (`apexrefguide` L227365-227392). A Finalizer may enqueue one asynchronous job — "Queueable, Future, or Batch" (`apexdev` L16354-16356) — and only one Finalizer may be attached per job (`apexdev` L16353). Anything deeper than that, including the five-consecutive-retry budget, belongs to `apex/apex-transaction-finalizers`; keep the Finalizer here thin.

### State Passing Between Chained Jobs

Each Queueable runs in a separate transaction, so state must travel through constructor fields. Non-primitive members are permitted — "Your queueable class can contain member variables of non-primitive data types, such as sObjects or custom Apex types" (`apexdev` L15968-15970) — which is the one advantage over `@future`, whose parameters "must be primitive data types, arrays of primitive data types, or collections of primitive data types" (`apexdev` L17968-17970). Permission is not recommendation: a `List<SObject>` is re-serialized on every link, carries a snapshot that may already be stale, and breaks deserialization if the field set changes between deployments. Pass a `Set<Id>` and re-query.

Two hard rules bound the state you can carry. `transient` members "are ignored by serialization and deserialization and the value is set to null in Queueable Apex" (`apexdev` L15975-15976). And statics do not bridge anything: "A static variable is static only within the scope of the Apex transaction... reset across transaction boundaries" (`apexdev` L3738-3740).

### Mode Selection

This skill operates in three modes based on the practitioner's need:

- **Mode 1 — Implement:** Design a new Queueable or chain from scratch.
- **Mode 2 — Review/Audit:** Evaluate existing Queueable classes for anti-patterns, depth risk, missing callout declaration, or lack of Finalizer-based error handling.
- **Mode 3 — Troubleshoot:** Diagnose a failing, stuck, or looping Queueable job in production.

---

## Common Patterns

### Bounded Chained Processing With Stack Guard

**When to use:** A multi-step async workflow requires sequential jobs, each processing a slice of work, and the depth must be capped to prevent runaway chains.

**How it works:**
1. Each Queueable receives a payload (list of IDs to process, a cursor, or a batch number).
2. Before chaining, the job checks `System.AsyncInfo.getCurrentQueueableStackDepth()` against the configured max.
3. If depth is within limit, it enqueues the next job with `AsyncOptions.MaximumQueueableStackDepth` set.
4. If the depth cap is reached, the job logs the state and exits cleanly or triggers a Platform Event for external pickup.

**Why not the alternative:** Without the stack guard, an off-by-one error in termination logic or an unexpected data condition can produce an infinite chain that floods the async queue and degrades the org.

### Finalizer-Based Error Recovery

**When to use:** The Queueable performs irreversible side effects (callouts, record updates) and the team needs guaranteed error notification or compensating action even when the job throws an uncaught exception.

**How it works:**
1. Call `System.attachFinalizer(new MyFinalizer())` as the first line of `execute()` before any code that could throw.
2. In `MyFinalizer.execute(FinalizerContext ctx)`, check `ctx.getResult()`.
3. On `ParentJobResult.UNHANDLED_EXCEPTION`, log or create a failure record, send a Platform Event, or enqueue a compensating job.
4. On `ParentJobResult.SUCCESS`, optionally enqueue the next stage or record completion.

**Why not the alternative:** Without a Finalizer, an uncaught exception in a Queueable leaves no guaranteed cleanup path. `try/catch` alone cannot handle out-of-memory or system limit exceptions that terminate the transaction externally.

### Callout Queueable With Retry

**When to use:** The job makes an outbound HTTP or web service call that can fail transiently, and the team wants automatic retry up to a bounded count.

**How it works:**
1. The class implements `Queueable, Database.AllowsCallouts`.
2. The constructor carries a `retryCount` integer and a payload.
3. The Finalizer checks for `UNHANDLED_EXCEPTION`. If `retryCount < maxRetries`, it enqueues the same job class with `retryCount + 1`.
4. After `maxRetries`, the Finalizer writes a failure record or fires an alert.

**Why not the alternative:** Re-enqueueing from inside `catch` inside `execute()` works only for caught exceptions. The Finalizer handles all failure modes including platform-level termination.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single deferred async operation, no chaining needed | Plain Queueable, no Finalizer | Simplest correct tool |
| Multi-step chain with bounded depth | Queueable + `AsyncOptions.MaximumQueueableStackDepth` + stack depth check | Prevents runaway chain |
| Job makes outbound callouts | `implements Queueable, Database.AllowsCallouts` | Required by platform; omitting causes runtime exception |
| Error recovery or compensating action after failure | Queueable + `System.attachFinalizer()` | Finalizer runs regardless of parent success or failure |
| Need retry after transient callout failure | Finalizer re-enqueues with an incremented counter and `MinimumQueueableDelayInMinutes` | Handles all failure modes; delay is the supported back-off |
| Back-off > 10 min, or > 5 attempts | Scheduled Apex or a staging record | Past both ceilings of the delay + Finalizer pattern |
| Same job enqueued from several transactions (Data Loader batches, retried API calls) | `AsyncOptions.DuplicateSignature` + catch `DuplicateMessageException` | Static guards reset per transaction |
| Need fan-out to multiple parallel jobs | Reconsider: use Batch or Platform Events | Queueable allows only one child per execution |
| Very large record volume (tens of thousands+) | Batch Apex, not Queueable | Batch provides fresh limits per scope and query locator support |

---


## Recommended Workflow

1. **Confirm Queueable is the answer before writing one.** Read the
   `standards/decision-trees/async-selection.md` branch that applies — Q1 for
   volume and duration, Q5 for state between invocations, Q7 for work that must
   resume after failure — and cite it. Above roughly 50k records or 5 minutes the
   tree routes to Batch Apex; multi-link pipelines and flex-queue ceilings belong
   to `apex/apex-batch-chaining`.
2. **Answer the seven questions above.** They fix the chunk size, the enqueue call
   site, the signature key, the callout/DML ordering and the sharing declaration.
   Any of these decided later is decided by accident.
3. **Write the job from `references/code-examples.md` § 2.** Constructor takes a
   `Set<Id>`; `enqueueOnce` is the only public door and owns both the
   `AsyncOptions` depth cap and the `DuplicateSignature`; `execute()` contains
   exactly one `System.enqueueJob` on a terminal path; the Finalizer is thin and
   logs through `templates/apex/ApplicationLogger.cls`.
4. **Wire the enqueue at one seam.** Extend `templates/apex/TriggerHandler.cls`,
   collect Ids across the whole `Trigger.new`, and call `enqueueOnce` once — see
   `references/code-examples.md` § 3.
5. **Write the tests against recorded decisions, not chain levels.** Enqueue
   inside `Test.startTest()` / `Test.stopTest()`; assert the single-chunk case
   requests no child and the 201-record case requests exactly one; assert
   `enqueueOnce` swallows `DuplicateMessageException`. Never annotate the class
   `@IsTest(IsParallel=true)`.
6. **Run the checker over the source tree**, then fix every ERROR:
   `python3 scripts/check_apex_queueable_patterns.py --manifest-dir force-app/main/default/classes --strict`
7. **Deploy in the order in `references/code-examples.md` § 6, then verify in the
   org** with the `AsyncApexJob` query in § 7 — one row per chain link, `JobType`
   `Queueable`, `NumberOfErrors` zero — and confirm the Finalizer wrote its
   `Application_Log__c` row.

---

## Review Checklist

- [ ] Class implements `Queueable` (and `Database.AllowsCallouts` if callouts are made).
- [ ] `System.attachFinalizer()` is called for any job where failure handling matters.
- [ ] `execute()` enqueues at most one child Queueable.
- [ ] Chained jobs use `AsyncOptions.MaximumQueueableStackDepth` to cap depth.
- [ ] Stack depth is checked with `System.AsyncInfo.getCurrentQueueableStackDepth()` before re-enqueueing.
- [ ] State is passed through serializable constructor fields, not static variables.
- [ ] Tests use `Test.startTest()` / `Test.stopTest()` boundaries.
- [ ] `AsyncApexJob` is used for operational visibility (job status, failure count).
- [ ] Callout errors and limit exceptions are handled in the Finalizer, not only in `catch` blocks.
- [ ] Retry back-off uses `AsyncOptions.MinimumQueueableDelayInMinutes` (0–10), not a Schedulable dispatcher or a CRON string.
- [ ] Any dedup requirement that spans transactions uses `AsyncOptions.DuplicateSignature`, not a static Boolean or Set.
- [ ] `enqueueJob` is never inside a `for` loop; a trigger collects Ids and enqueues once.
- [ ] No `transient` member on the Queueable or the Finalizer.
- [ ] Sharing is declared explicitly (`with` / `without` / `inherited sharing`), not inherited by default.
- [ ] Any callout precedes every DML statement in the same `execute()`.
- [ ] The Finalizer uses `ctx.getAsyncApexJobId()`, never `ctx.getJobId()`.
- [ ] No test class that enqueues carries `@IsTest(IsParallel=true)`.
- [ ] Every terminal guard path writes a log row rather than returning silently.

---

## Salesforce-Specific Gotchas

1. **Single-child chaining is enforced at runtime, not compile time** — a second `enqueueJob` inside `execute()` compiles, then throws `System.LimitException: Too many queueable jobs added to the queue: 2`. Tests run async jobs synchronously and do not enforce it.
2. **The Finalizer has fresh limits but is still subject to them** — expensive SOQL or DML inside a Finalizer can itself blow governor limits and lose the failure record it was written to create.
3. **`MaximumQueueableStackDepth` does not propagate** — re-set the `AsyncOptions` on every enqueue in the chain, or the guard silently stops applying downstream.
4. **The synchronous enqueue ceiling is 50, not 1** (`apexdev` L16179-16181) — the per-record loop in a trigger dies on record 51, long after every hand test passed.
5. **`Status = 'Holding'` and the batch counters are meaningless here** — `Holding` "applies to batch jobs in the Apex flex queue" (`object_reference` L42423-42429) and `JobItemsProcessed` / `TotalJobItems` are always zero for Queueable (`apexdev` L16012-16013).

See `references/gotchas.md` for the full diagnosis of each — 14 grounded behaviours, including the duplicate-signature release semantics, the `transient` trap, the View Setup permission requirement, and the API 67.0 sharing change.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Queueable design review | Findings on chaining, callout declaration, Finalizer coverage, and state safety |
| Bounded chain scaffold | Pattern for multi-step Queueable chain with stack depth guard and Finalizer |
| Callout retry pattern | Queueable + `AllowsCallouts` + Finalizer-based retry up to a configurable max |
| Deployable package | Job class, trigger handler, trigger, test class, `-meta.xml`, `package.xml`, deploy order and verification SOQL — `references/code-examples.md` |
| Checker report | JSON findings from `scripts/check_apex_queueable_patterns.py` over a source tree |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the code — the full `RecalculateAccountRollupQueueable`, the `enqueueOnce` helper, the trigger seam, the minimal Finalizer, the test class, `-meta.xml`, `package.xml`, deploy order and verification SOQL |
| `references/gotchas.md` | A job failed, chained too far, ran under the wrong sharing mode, or reported `Completed` while changing nothing — 14 grounded platform behaviours |
| `references/examples.md` | You want the narrative walk-through of the bounded chain and the Finalizer retry, plus the diagnostic sequence for a chain that reported success |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated Queueable code, or self-checking your own output — 9 patterns with detection hints |
| `references/well-architected.md` | You are justifying the design in a review, or need the source list with the claim each bullet supports |

---

## Related Skills

- `apex/async-apex` — use when the question is whether Queueable is the right async mechanism at all; it owns the selection, this skill assumes it is settled.
- `apex/apex-batch-chaining` — use for multi-link pipelines, `finish()` hand-offs and flex-queue ceilings.
- `apex/apex-transaction-finalizers` — use for the Finalizer deep dive: retry budgets, buffered logging, the full `FinalizerContext` contract.
- `apex/apex-future-method-patterns` — use when the code in front of you is an existing `@future` method.
- `apex/batch-apex-patterns` — use when the volume or chunking need exceeds what Queueable chaining should handle.
- `apex/callout-and-dml-transaction-boundaries` — use when a job must both call out and write records.
- `apex/exception-handling` — use when the broader error handling and logging strategy is the focus.
- `apex/governor-limits` — use when the job is hitting CPU, heap, or DML limits inside `execute()`.
- `apex/debug-and-logging` — use when diagnosing async job failures through log analysis and correlation IDs.
