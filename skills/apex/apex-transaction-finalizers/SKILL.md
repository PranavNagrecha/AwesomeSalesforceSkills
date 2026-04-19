---
name: apex-transaction-finalizers
description: "Use this skill when you need guaranteed post-Queueable cleanup, retry, or failure-logging logic that must run even when the parent Queueable throws an unhandled exception. Trigger keywords: FinalizerContext, System.attachFinalizer, Queueable cleanup on failure, post-job compensation, guaranteed async cleanup. NOT for batch job completion callbacks — use apex-batch-chaining. NOT for platform event publishing on failure — use platform-events-apex."
category: apex
salesforce-version: "Summer '21+ (API v53.0+)"
well-architected-pillars:
  - Reliability
triggers:
  - "queueable cleanup on failure apex"
  - "transaction finalizer run after exception"
  - "FinalizerContext getResult SUCCESS apex"
tags:
  - apex-finalizer
  - queueable
  - error-handling
  - async-apex
  - cleanup
inputs:
  - "The Queueable class that needs guaranteed post-execution behavior"
  - "The failure scenario: retry, compensate, or log"
  - "Retry count limit if implementing retry logic"
outputs:
  - "A System.Finalizer implementation attached to the parent Queueable"
  - "Retry Queueable enqueue (one job max) or failure record DML"
  - "Review checklist confirming Finalizer constraints are respected"
dependencies:
  - apex-queueable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex Transaction Finalizers

This skill activates when a Queueable job needs guaranteed post-execution behavior — cleanup, retry, or failure logging — that must run even if the parent Queueable throws an unhandled exception. Use `System.attachFinalizer()` to bind a `System.Finalizer` implementation to a Queueable; the Finalizer runs in a **separate Apex transaction** with **full governor limits** after the parent job finishes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the parent job is a `Queueable` (not Batch, Scheduled, or `@future`). Transaction Finalizers are only supported on Queueable jobs.
- Identify the failure scenario: Is this a retry (re-enqueue the same job), a compensation (write a failure record / publish a PE), or silent logging?
- Determine a retry ceiling. Finalizers can enqueue exactly one new Queueable — if that Queueable also has a Finalizer, the chain continues. Without a retry limit you risk infinite loops.
- Check the API version of the Queueable class — `System.attachFinalizer()` requires API v53.0+ (Summer '21).
- The Finalizer does **not** run if the parent job was aborted via `System.abortJob()`. Plan for that case separately.

---

## Core Concepts

### Finalizer Lifecycle

When `System.attachFinalizer(myFinalizer)` is called inside a Queueable's `execute()` method, the platform registers the Finalizer to execute after the parent job's transaction closes — whether it committed successfully or was rolled back due to an unhandled exception. The Finalizer runs in a **completely separate Apex transaction** with fresh governor-limit counters (100 SOQL queries, 150 DML statements, etc.). The parent transaction's state (variable values, uncommitted DML) is not visible to the Finalizer.

### FinalizerContext API

The Finalizer's `execute(FinalizerContext ctx)` method receives a `FinalizerContext` object with three key members:

| Member | Returns | Notes |
|---|---|---|
| `ctx.getJobId()` | `Id` | The `AsyncApexJob` ID of the **parent** Queueable |
| `ctx.getResult()` | `System.ParentJobResult` | `SUCCESS` or `UNHANDLED_EXCEPTION` |
| `ctx.getException()` | `Exception` | Non-null only when `getResult() == UNHANDLED_EXCEPTION` |

Always gate retry / compensation logic on `ctx.getResult()` to avoid double-processing on success.

### Enqueue Constraint

A Finalizer may enqueue **exactly one** new Queueable job via `System.enqueueJob()`. Attempting to enqueue more than one throws a `System.AsyncException`. A Finalizer cannot attach another Finalizer to itself — `System.attachFinalizer()` called from within a Finalizer context throws a `System.AsyncException`.

### Abort Gap

If the parent Queueable is terminated via `System.abortJob()`, the Finalizer is **not invoked**. This is a hard platform constraint with no workaround at the Finalizer layer. If abort-path cleanup is required, model it as a separate Schedulable or monitoring job that polls `AsyncApexJob` for `ABORTED` status.

---

## Common Patterns

### Retry-on-Failure with Backoff Counter

**When to use:** A Queueable makes an external callout or complex DML that can fail transiently. You want automatic retry up to N times without manual re-queuing.

**How it works:**
1. Pass a `retryCount` integer into the Queueable constructor.
2. Inside `execute()`, call `System.attachFinalizer(new MyFinalizer(jobPayload, retryCount))`.
3. In the Finalizer's `execute()`, check `ctx.getResult()`. On `UNHANDLED_EXCEPTION` and `retryCount < MAX_RETRIES`, enqueue a new instance of the Queueable with `retryCount + 1`.
4. On `retryCount >= MAX_RETRIES`, write a failure record instead of re-enqueuing.

**Why not try/catch inside execute():** A `try/catch` inside `execute()` only catches exceptions thrown by code in that block — governor-limit violations and some system exceptions escape it. A Finalizer provides an out-of-band, guaranteed callback even for unhandled exceptions that bypass catch blocks.

### Failure Logging to Custom Object

**When to use:** You need an auditable record of every Queueable failure for operations monitoring, SLA reporting, or manual reprocessing.

**How it works:**
1. Attach a Finalizer that receives the job context (record IDs, batch key, etc.) from the parent Queueable constructor.
2. In `execute(ctx)`, if `ctx.getResult() == UNHANDLED_EXCEPTION`, insert an `Async_Job_Error__c` (or equivalent) record with the job ID, exception message, stack trace, and payload snapshot.
3. Use the single Queueable enqueue slot only if retry is also needed; otherwise leave it unused.

**Why not System.debug:** Debug logs are transient and unavailable to non-admin users. A custom object record survives platform restarts and is queryable by monitoring tools.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Parent Queueable fails transiently (callout timeout, lock contention) | Retry Finalizer with counter | Full governor limits in separate transaction; single enqueue slot used for the retry job |
| Failure needs permanent audit record | Logging Finalizer (DML in separate transaction) | Parent transaction is rolled back; Finalizer gets fresh DML budget |
| Both retry AND logging needed | Single Finalizer handles both; log first, then conditionally enqueue retry | Enqueue limit is 1 — combine both behaviors in one Finalizer |
| Parent job was aborted by admin | Schedulable monitor polling `AsyncApexJob` for ABORTED status | Finalizer does not fire on abort; no workaround |
| Batch job completion callback | `Database.Batchable` `finish()` method or apex-batch-chaining skill | Transaction Finalizers are Queueable-only |
| Publishing a Platform Event on failure | PE publish inside Finalizer OR dedicated PE skill | PE publish counts against Finalizer's DML budget; prefer dedicated skill for complex routing |

---

## Recommended Workflow

1. **Confirm Queueable context** — verify the failing async job is a `Queueable`, API v53+, and that abort-path behavior does not need to be covered by this Finalizer.
2. **Choose Finalizer behavior** — decide between retry, compensation DML, or both. If both, plan the single Finalizer class that handles them sequentially.
3. **Design the retry ceiling** — pick `MAX_RETRIES` (typically 3–5) and pass `retryCount` through the Queueable constructor so the Finalizer can increment and re-enqueue safely.
4. **Implement `System.Finalizer`** — create a class that `implements System.Finalizer`, receives the job payload via constructor, implements `execute(FinalizerContext ctx)`, gates on `ctx.getResult()`, and enqueues at most one retry job.
5. **Attach in `execute()`** — call `System.attachFinalizer(new MyFinalizer(...))` near the top of the parent Queueable's `execute()` method so it is registered before any code that might throw.
6. **Test both SUCCESS and UNHANDLED_EXCEPTION paths** — use `Test.startTest()` / `Test.stopTest()` to flush the queue; mock the failure by having the Queueable throw in test context, and assert the Finalizer's DML/enqueue behavior.
7. **Review checklist** — confirm no second `attachFinalizer` call, retry counter bounded, no `attachFinalizer` inside the Finalizer itself.

---

## Review Checklist

- [ ] `System.attachFinalizer()` is called exactly once per Queueable `execute()` invocation
- [ ] Finalizer gates all compensation logic on `ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION`
- [ ] Retry counter is passed via constructor and incremented before re-enqueuing; `MAX_RETRIES` ceiling is enforced
- [ ] The Finalizer enqueues at most one new Queueable job (throws `AsyncException` if you try more)
- [ ] No call to `System.attachFinalizer()` inside the Finalizer's own `execute()` method
- [ ] Tests cover both SUCCESS and UNHANDLED_EXCEPTION result paths
- [ ] Abort-path (if required) is handled by a separate mechanism — Finalizer does not fire on `System.abortJob()`

---

## Salesforce-Specific Gotchas

1. **Finalizer does not fire on `System.abortJob()`** — If an admin or another job calls `System.abortJob(parentJobId)`, the Finalizer is silently skipped. This is undocumented in some sources but confirmed in the official Apex Developer Guide. Any cleanup that must happen on abort needs a separate polling mechanism.
2. **Parent transaction rollback is total** — When the Queueable throws an unhandled exception, every DML operation in that transaction is rolled back. The Finalizer starts with a clean slate — it cannot read variables set in the parent, and it cannot "see" records that the parent tried but failed to commit.
3. **One enqueue, no exceptions** — Calling `System.enqueueJob()` more than once in a single Finalizer `execute()` call throws `System.AsyncException` immediately. Wrap the retry call in a conditional so it is only reached when retry is actually needed.
4. **Finalizer exception is swallowed** — If the Finalizer itself throws an unhandled exception, the platform logs it to `ApexLog` but does not propagate it anywhere visible. There is no secondary Finalizer. Build explicit logging inside the Finalizer's own `execute()` using a `try/catch` wrapper.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `System.Finalizer` implementation class | Apex class implementing `System.Finalizer` with retry and/or logging logic |
| Updated Queueable class | Parent Queueable with `System.attachFinalizer()` call and `retryCount` constructor param |
| `Async_Job_Error__c` insert (optional) | Custom object record capturing job ID, exception type, message, and stack trace |

---

## Related Skills

- apex-queueable-patterns — foundational Queueable design; use alongside this skill for the parent job structure
- apex-batch-chaining — for batch-to-batch chaining; Finalizers do not apply to Batch jobs
- apex-limits-monitoring — for monitoring Apex governor limits that might cause the Queueable to fail in the first place
