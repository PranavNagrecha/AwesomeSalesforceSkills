---
name: apex-queueable-patterns
description: "Use when designing, implementing, reviewing, or debugging Queueable Apex jobs that chain, use the Finalizer interface, pass state across transactions, or need controlled async depth. Trigger keywords: 'Queueable', 'System.enqueueJob', 'Finalizer', 'QueueableContext', 'AsyncOptions', 'stack depth', 'chained queueable'. NOT for basic async Apex mechanism selection (use async-apex), NOT for large-volume record processing where Batch Apex is the right tool (use batch-apex-patterns)."
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
  - how do I chain queueable jobs in Apex without hitting stack depth limits
  - my queueable job is failing silently with no error in logs
  - how do I use the Finalizer interface to handle queueable failures
  - queueable job not making callouts as expected
  - how do I pass state between chained queueable jobs
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Apex Queueable Patterns

Use this skill when designing or reviewing Apex jobs that use the Queueable interface for controlled async execution, multi-step chaining, outbound callouts, or error recovery through the Finalizer interface. The skill covers implementation patterns, stack depth management, state passing, and production-safe failure handling.

---

## Before Starting

- Is the use case a single deferred operation, a multi-step chain, or a fan-out? Each has a different pattern.
- Does the job require callouts? If so, `Database.AllowsCallouts` must also be implemented.
- How deep can the chain realistically grow? The platform enforces a default maximum stack depth of 5 when using `AsyncOptions.MaximumQueueableStackDepth`.
- Does the job need to recover from failure or enqueue a follow-up regardless of success or failure? That is what the Finalizer interface is for.
- How is state passed between chained jobs? Serialized fields or record IDs are the safe options.

---

## Core Concepts

### The Queueable Interface

A Queueable class implements `Queueable` and defines a single `execute(QueueableContext ctx)` method. The job is enqueued with `System.enqueueJob(new MyJob())` and runs asynchronously in a separate transaction with full governor limits — 100 SOQL queries, 150 DML statements, 12 MB heap, and 60 000 ms CPU time (per the Apex Developer Guide). The job ID returned by `enqueueJob` maps to an `AsyncApexJob` record that can be monitored.

Adding `Database.AllowsCallouts` to the `implements` clause is required for any Queueable that makes HTTP or web service callouts. Without it, a runtime exception is thrown even though the code compiles cleanly.

### Chaining And Stack Depth

A Queueable can enqueue exactly one child job from within its `execute()` method. Attempting to enqueue a second child in the same execution throws a `System.LimitException`. This is the single-child chaining rule and it applies in production — in sandbox and scratch orgs the same rule holds, but tests run synchronously and skip the queue, so the limit is not exercised in unit tests.

Chaining can continue indefinitely by default, but uncontrolled infinite chains are a production risk. The `AsyncOptions` class lets you cap depth explicitly:

```apex
AsyncOptions opts = new AsyncOptions();
opts.MaximumQueueableStackDepth = 5;
System.enqueueJob(new MyJob(nextPayload), opts);
```

`System.AsyncInfo.getCurrentQueueableStackDepth()` returns the current depth so the job can stop or branch safely. Together these two APIs are the canonical pattern for bounded chaining in production code (Apex Developer Guide — Queueable Apex).

### The Finalizer Interface

The Finalizer interface (`System.Finalizer`) runs after the parent Queueable completes — regardless of whether that Queueable succeeded or threw an uncaught exception. The Finalizer runs in its own separate Apex transaction with its own full governor limits. It is attached with `System.attachFinalizer(new MyFinalizer())` inside the Queueable's `execute()` method, before any code that might fail.

The `FinalizerContext` passed to `execute(FinalizerContext ctx)` provides:
- `ctx.getJobId()` — the parent job's `AsyncApexJob` ID
- `ctx.getResult()` — `ParentJobResult.SUCCESS` or `ParentJobResult.UNHANDLED_EXCEPTION`
- `ctx.getException()` — the exception that terminated the parent, if any

A Finalizer can enqueue one additional Queueable. This is the safe mechanism for retry, dead-letter notification, or compensating transactions after Queueable failure. Only one Finalizer may be attached per Queueable (Apex Developer Guide — Transaction Finalizers).

### State Passing Between Chained Jobs

Each Queueable runs in a separate transaction, so state must be serialized through job constructor fields. Collections of IDs, simple primitives, and serializable wrapper classes are all safe. Large SObject collections should be avoided in favor of passing a Set of IDs and re-querying in the next job. Do not rely on static variables to bridge jobs — static state does not survive across async transactions.

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
| Need retry after transient callout failure | Finalizer re-enqueues same job with incremented retry counter | Only safe retry path that handles all failure modes |
| Need fan-out to multiple parallel jobs | Reconsider: use Batch or Platform Events | Queueable allows only one child per execution |
| Very large record volume (tens of thousands+) | Batch Apex, not Queueable | Batch provides fresh limits per scope and query locator support |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

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

---

## Salesforce-Specific Gotchas

1. **Single-child chaining rule is enforced at runtime, not compile time** — code that enqueues two children inside `execute()` compiles cleanly but throws `System.LimitException` in the second enqueue call. Tests may not catch this because async jobs run synchronously in test context.
2. **Finalizer runs in a separate transaction with fresh limits, but it is still subject to its own limits** — a Finalizer that performs expensive SOQL or DML can itself hit governor limits and fail silently unless the Finalizer is also guarded.
3. **`AsyncOptions.MaximumQueueableStackDepth` must be set on every `enqueueJob` call in the chain** — setting it once on the first job does not propagate; each chained job must re-set the option or the guard does not apply downstream.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Queueable design review | Findings on chaining, callout declaration, Finalizer coverage, and state safety |
| Bounded chain scaffold | Pattern for multi-step Queueable chain with stack depth guard and Finalizer |
| Callout retry pattern | Queueable + `AllowsCallouts` + Finalizer-based retry up to a configurable max |

---

## Related Skills

- `apex/async-apex` — use when the question is whether Queueable is the right async mechanism at all.
- `apex/batch-apex-patterns` — use when the volume or chunking need exceeds what Queueable chaining should handle.
- `apex/exception-handling` — use when the broader error handling and logging strategy is the focus.
- `apex/governor-limits` — use when the job is hitting CPU, heap, or DML limits inside `execute()`.
- `apex/debug-and-logging` — use when diagnosing async job failures through log analysis and correlation IDs.
