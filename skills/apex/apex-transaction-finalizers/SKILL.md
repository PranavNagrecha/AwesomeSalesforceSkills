---
name: apex-transaction-finalizers
description: "Use this skill when you need guaranteed post-Queueable cleanup, retry, or failure-logging logic that must run even when the parent Queueable throws an unhandled exception. Trigger keywords: FinalizerContext, System.attachFinalizer, getAsyncApexJobId, ParentJobResult, Queueable cleanup on failure, post-job compensation, guaranteed async cleanup, five-retry chaining limit. NOT for Queueable design or chaining — use apex/apex-queueable-patterns. NOT for the same need in Flow — use flow/flow-transaction-finalizer-patterns."
category: apex
salesforce-version: "Summer '21+ (API v53.0+); verified against Apex Developer Guide v67.0, Summer '26"
well-architected-pillars:
  - Reliability
triggers:
  - "queueable cleanup on failure apex"
  - "transaction finalizer run after exception"
  - "FinalizerContext getResult SUCCESS apex"
  - "queueable finalizer handle failure retry apex async"
  - "retry a failed queueable job automatically from a finalizer"
  - "log queueable failures to a custom object after the transaction rolled back"
  - "fix System.attachFinalizer(Finalizer) is not allowed in this context"
  - "debug More than one Finalizer cannot be attached to same Async Apex Job"
  - "how many times can a finalizer re-enqueue a failed queueable job"
  - "test a transaction finalizer with Test.startTest and Test.stopTest"
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
  - "Retry enqueue (one async job max) or failure record DML"
  - "Review checklist confirming Finalizer constraints are respected"
dependencies:
  - apex-queueable-patterns
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Apex Transaction Finalizers

This skill activates when a Queueable job needs guaranteed post-execution behavior — cleanup, retry, or failure logging — that must run even if the parent Queueable throws an unhandled exception. `System.attachFinalizer()` binds a `System.Finalizer` implementation to a Queueable; the Queueable job and the Finalizer "run in separate Apex and Database transactions" (Apex Developer Guide v67.0 L16297).

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the parent job is a `Queueable` (not Batch, Scheduled, or `@future`). Transaction Finalizers attach only to "asynchronous Apex jobs that use the Queueable framework" (guide L16285); calling `attachFinalizer` anywhere else produces `System.attachFinalizer(Finalizer) is not allowed in this context` (guide L16543–16567).
- Identify the failure scenario: retry (re-enqueue), compensation (write a failure record / publish a Platform Event), or buffered logging.
- Decide the retry ceiling *below* the platform's own cap. "A Queueable job that failed due to an unhandled exception can be successively re-enqueued five times by a transaction finalizer… The counter is reset when the Queueable job completes without an unhandled exception" (guide L16293–16295).
- Check the API version of the Queueable class — `System.attachFinalizer()` requires API v53.0+. UNVERIFIED (2026-09-05): the v67.0 Apex Developer Guide does not state the introducing API version; v53.0/Summer '21 comes from the release-note history, not from `apexdev.txt`.
- Decide what the Finalizer must carry. The framework "uses the state of the Finalizer object (if attached) at the end of Queueable execution. Mutation of the Finalizer state, after it's attached, is therefore supported" (guide L16358–16359) — but `transient` fields are dropped (guide L16360–16362).

---

## Questions to Ask Before Configuring

Ask these before writing the class; the answers decide the design, and an LLM that skips them ships a Finalizer that compiles, deploys, and silently retries forever or silently retries never.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "When this job fails, what must still happen — a retry, a durable failure record, or a released lock?" | Retry and compensation have different enqueue budgets: the Finalizer may enqueue exactly one async job (guide L16355), so retry and async logging cannot both use it | The single Finalizer class's responsibility list, and which behaviour claims the one enqueue slot |
| "Is the failure transient (callout timeout, row lock) or deterministic (bad payload, validation rule)?" | Retrying a deterministic failure burns all five platform-allowed re-enqueues and still fails (gotcha 5) | An exception-type allowlist for retry vs. an immediate route to the dead-letter record |
| "How many retries before we stop, and where does the counter live?" | The counter must be carried on the Finalizer/Queueable state — the Finalizer runs in a separate transaction and cannot read the parent's locals (gotcha 3) | The constructor parameter and the `MAX_RETRIES` constant, both below the platform cap of 5 |
| "What context does the Finalizer need in order to be useful — record IDs, a payload snapshot, a correlation key?" | The parent's DML is rolled back on failure, so the Finalizer cannot query for what the parent tried to write (gotcha 3) | The exact fields to buffer on the Finalizer instance before the risky code runs |
| "Does the Finalizer need to call out, and to what?" | "Callouts are allowed in finalizer implementations" (guide L16357), so a webhook/dead-letter POST is legal here even though the parent was mid-DML | A decision to notify externally in the Finalizer instead of chaining another Queueable |
| "Who reads the failure signal, and with what permissions?" | Debug logs are transient and admin-only; the Finalizer's own runtime errors surface only as `Error processing finalizer for queueable job id: {0}` in the log (guide L16580) | The custom object (or Platform Event) plus the report or monitoring query that consumes it |
| "Can this job be aborted or killed mid-flight, and does the abort path need cleanup too?" | Finalizer execution is not guaranteed under unexpected termination: "If a job request is terminated unexpectedly, such as a database shutdown during system upgrade, the transaction finalizer can fail to execute" (guide L16533–16534) | An explicit decision to add (or consciously skip) an `AsyncApexJob` polling monitor for the abort path |

What a proper configuration adds over just attaching a Finalizer: the retry stops at a number you chose rather than at the platform's fifth failure, the failure record survives the parent rollback and names the `AsyncApexJob` row it came from, and the abort path is either covered by a separate monitor or documented as knowingly uncovered.

---

## Core Concepts

### Finalizer Lifecycle

`System.attachFinalizer(myFinalizer)` inside a Queueable's `execute()` registers the Finalizer to run after the parent job's transaction closes, whether it committed or rolled back. The Finalizer then runs in its own Apex and Database transaction (guide L16297). Two consequences follow, and they pull in opposite directions:

- The parent's **database work** is gone on failure — a rolled-back insert is not queryable from the Finalizer.
- The parent's **Finalizer-object state** is not gone — the framework snapshots the Finalizer instance at the end of Queueable execution, so anything the Queueable pushed onto the Finalizer (log lines, a retry count, IDs) is still there (guide L16358–16359, L16369–16370).

### FinalizerContext API

`System.FinalizerContext` "contains four methods" (guide L16317; Apex Reference Guide L215612–215614):

| Method | Signature | Returns | Notes |
|---|---|---|---|
| `ctx.getAsyncApexJobId()` | `public Id getAsyncApexJobId()` | `Id` | "the ID of the Queueable job for which this finalizer is defined" — use this to join to `AsyncApexJob` (ref guide L215642–215649) |
| `ctx.getRequestId()` | `public String getRequestId()` | `String` | Correlates with Event Monitoring logs; "The Queueable job and the Finalizer execution share the same request ID" (ref guide L215674) |
| `ctx.getResult()` | `public System.ParentJobResult getResult()` | `System.ParentJobResult` | "The enum takes these values: SUCCESS, UNHANDLED_EXCEPTION" (ref guide L215685, L227217–227226) |
| `ctx.getException()` | `public Exception getException()` | `Exception` | "Returns the exception with which the Queueable job failed when getResult is UNHANDLED_EXCEPTION, null otherwise" (ref guide L215654) |

There is **no** `getJobId()` on `FinalizerContext`. `getJobId()` belongs to `QueueableContext` (guide L16380) — a class that implements both interfaces has both methods in scope, which is exactly how the confusion survives code review.

`System.attachFinalizer` is declared `public static void attachFinalizer(Object finalizer)` (Apex Reference Guide L238804), so a wrong-typed argument is a *runtime* failure — `Class {0} must implement the Finalizer interface` (guide L16543–16567) — not a compile error.

### Enqueue and Retry Budget

| Constraint | Grounded statement |
|---|---|
| One Finalizer per job | "Only one finalizer instance can be attached to any Queueable job" (guide L16354) |
| One async job per Finalizer | "You can enqueue a single asynchronous Apex job (Queueable, Future, or Batch) in the finalizer's implementation of the execute method" (guide L16355–16356) |
| Five consecutive retries | "can be successively re-enqueued five times by a transaction finalizer. This limit applies to a series of consecutive Queueable job failures. The counter is reset when the Queueable job completes without an unhandled exception" (guide L16293–16295) |
| Callouts permitted | "Callouts are allowed in finalizer implementations" (guide L16357) |
| No extra daily async execution | "Using a finalizer doesn't count as an extra execution against your daily Async Apex limit" (guide L16298) |
| Governor limits | "Synchronous governor limits apply for the Finalizer transaction, except in these cases where asynchronous limits apply: • Total heap size • Maximum number of Apex jobs added to the queue with System.enqueueJob • Maximum number of methods with the future annotation allowed per Apex invocation" (guide L16298–16303) |

The retry example in the guide re-enqueues unconditionally and annotates the call `// This call fails after 5 times when it hits the chaining limit` (guide L16523). The platform therefore stops the loop for you — but it stops it by *failing*, at the fifth retry, with no failure record written. A bounded counter is how you stop it on your own terms.

### Same Class, Both Interfaces

Both worked examples in the guide use one class for both roles: `public class LoggingFinalizer implements Finalizer, Queueable` (guide L16373) and `public class RetryLimitDemo implements Finalizer, Queueable` (guide L16477). "Finalizers can be implemented as an inner class. Also, you can implement both Queueable and Finalizer interfaces with the same class" (guide L16296). Fusing them makes the buffered-state pattern trivial (`System.attachFinalizer(this)`, guide L16393) at the cost of two `execute` overloads in one file.

---

## Common Patterns

### Retry-on-Failure with a Bounded Counter

**When to use:** A Queueable makes an external callout or complex DML that can fail transiently and you want automatic retry that stops short of the platform's fifth failure.

**How it works:**
1. Carry `retryCount` on the class that implements `Finalizer`.
2. Call `System.attachFinalizer(...)` as the first statement of the Queueable's `execute()`.
3. In `execute(FinalizerContext ctx)`, act only when `ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION`.
4. Re-enqueue with `retryCount + 1` while `retryCount < MAX_RETRIES` (keep `MAX_RETRIES` at 3 or 4 so the dead-letter DML runs before the platform's fifth-failure cap hits).
5. Otherwise write the dead-letter record — the Finalizer's own transaction is not rolled back with the parent's.

**Why not try/catch inside execute():** a `try/catch` cannot catch a `LimitException` — the guide's own examples deliberately run `while (true)` inside a `try` to "result in limit error" and still reach the Finalizer (guide L16404–16409 and L16488–16495).

### Buffered Logging Committed by the Finalizer

**When to use:** You need an auditable record of what the job did *and* why it failed, including work logged before the exception.

**How it works:** the Queueable pushes log rows onto the Finalizer instance while it runs (`f.addLog(...)`, guide L16401), and the Finalizer commits them with `Database.insert(logRecords, false)` (guide L16435). This is legal precisely because "Mutation of the Finalizer state, after it's attached, is therefore supported" (guide L16358–16359) and "The finalizer state is preserved even if the Queueable job fails" (guide L16369–16370). Stamp each row with `ctx.getAsyncApexJobId()` or `ctx.getRequestId()` — the guide's example does exactly that (guide L16424–16430).

**Why not System.debug:** debug logs are transient and admin-gated. A custom object row is queryable, reportable, and survives the log window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Parent Queueable fails transiently (callout timeout, lock contention) | Retry Finalizer with a counter below 5 | Platform allows five consecutive re-enqueues and then fails the call (guide L16293, L16523) |
| Failure needs a permanent audit record | Log via DML inside the Finalizer | Separate Apex and Database transaction, so the parent's rollback does not take the log with it (guide L16297) |
| Both retry AND logging needed | One Finalizer: DML the log synchronously, then use the single enqueue slot for the retry | Only one async job may be enqueued from a Finalizer (guide L16355) |
| Need to notify an external system on failure | Callout from the Finalizer | "Callouts are allowed in finalizer implementations" (guide L16357) |
| Failure must be correlated with Event Monitoring | Store `ctx.getRequestId()` alongside `ctx.getAsyncApexJobId()` | Request ID correlates with Event Monitoring; job ID correlates with `AsyncApexJob` (ref guide L215674) |
| Log lines produced before the exception must survive | Buffer on the Finalizer instance, commit in `execute(FinalizerContext)` | Finalizer state is snapshotted at the end of Queueable execution and preserved on failure (guide L16358, L16369) |
| Batch job completion callback | `Database.Batchable.finish()` or apex/apex-batch-chaining | Finalizers attach to the Queueable framework only (guide L16285) |
| Job aborted or killed mid-flight | Separate Schedulable polling `AsyncApexJob` | Finalizer execution is not guaranteed under unexpected termination (guide L16533–16534); the abort case specifically is UNVERIFIED (2026-09-05) — see gotcha 1 |
| Publishing a Platform Event on failure | `EventBus.publish` inside the Finalizer | Runs in the Finalizer's own transaction. UNVERIFIED (2026-09-05): the guide does not state how a Platform Event publish counts against the Finalizer's DML budget |

---

## Recommended Workflow

1. **Answer the questions above and fix the shape.** Decide retry vs. compensate vs. buffered log, the `MAX_RETRIES` value, and whether one class implements both `Queueable` and `Finalizer` (guide L16296) or two classes do.
2. **Write the pair from `references/code-examples.md`.** Copy `OrderSyncQueueable.cls` / `OrderSyncFinalizer.cls`, keep `System.attachFinalizer(...)` as the first statement of `execute(QueueableContext)`, and route failure logging through `templates/apex/ApplicationLogger.cls` rather than a hand-rolled insert.
3. **Wire the deployment artifacts.** Take the `*.cls-meta.xml` (`<apiVersion>67.0</apiVersion>`) and the `package.xml` from `references/code-examples.md`; the class list must include the Queueable, the Finalizer, and the test class.
4. **Write the test from the same file.** `Test.startTest()` / `System.enqueueJob(...)` / `Test.stopTest()` runs the async work synchronously (guide L16121–16126); assert on the dead-letter rows and on the retry counter that the Finalizer wrote.
5. **Run the checker.** `python3 scripts/check_apex_transaction_finalizers.py --manifest-dir force-app` — it flags `Finalizer` implementations with no `execute(FinalizerContext)`, `attachFinalizer` outside a Queueable `execute`, unbounded re-enqueue, `transient` state on a Finalizer, unguarded DML, `ctx.getJobId()` on a `FinalizerContext`, and a Finalizer with no test class naming it.
6. **Deploy and verify.** `sf project deploy start -x manifest/package.xml` then `sf apex run test -n OrderSyncFinalizerTest -r human -w 10 -c`, and confirm the run with the `AsyncApexJob` SOQL in `references/code-examples.md`.
7. **Walk the Review Checklist below** before handing the change to a reviewer.

---

## Review Checklist

- [ ] `System.attachFinalizer()` is called exactly once per Queueable `execute()` invocation, as the first statement
- [ ] The Finalizer's method is `execute(FinalizerContext ctx)`, and it reads `ctx.getAsyncApexJobId()` — never `ctx.getJobId()`
- [ ] All compensation logic is gated on `ctx.getResult() == System.ParentJobResult.UNHANDLED_EXCEPTION`
- [ ] `retryCount` is carried on the Finalizer state, incremented before re-enqueue, and capped by a `MAX_RETRIES` constant strictly below the platform's five consecutive retries
- [ ] At most one `System.enqueueJob` / `Database.executeBatch` / `@future` call is reachable in the Finalizer's `execute()`
- [ ] No `System.attachFinalizer()` call inside the Finalizer's own `execute()` method
- [ ] No field the Finalizer needs is declared `transient`
- [ ] Every DML statement in the Finalizer is inside a `try/catch` (or uses `Database.insert(list, false)`), because a Finalizer failure surfaces only in the debug log
- [ ] Tests cover both the `SUCCESS` and `UNHANDLED_EXCEPTION` result paths and assert on the dead-letter record
- [ ] Abort / unexpected-termination path is either handled by a separate `AsyncApexJob` monitor or documented as uncovered

---

## Salesforce-Specific Gotchas

The full list with **What happens / When it occurs / How to avoid** is in `references/gotchas.md`. The three that most often survive review:

1. **`FinalizerContext` has no `getJobId()`.** The four methods are `getAsyncApexJobId`, `getRequestId`, `getResult`, `getException` (guide L16317). Code that compiles with `getJobId()` is a class implementing both interfaces, where the `QueueableContext` method is in scope.
2. **The retry cap is five consecutive failures, and it fails loudly at the sixth attempt** — the guide's own example annotates the call `// This call fails after 5 times when it hits the chaining limit` (guide L16523). An "unbounded" retry is not an infinite loop; it is a loop that dies without writing anything down.
3. **Finalizer state survives, parent DML does not.** The framework snapshots the Finalizer instance at the end of Queueable execution (guide L16358–16359), so buffered state is available — but any record the parent tried to insert was rolled back with the parent's transaction.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `System.Finalizer` implementation class | Apex class implementing `System.Finalizer` with bounded retry and/or dead-letter logging |
| Updated Queueable class | Parent Queueable with `System.attachFinalizer()` as the first statement of `execute()` |
| `*.cls-meta.xml` + `package.xml` | Deployment metadata at `<apiVersion>67.0</apiVersion>` |
| Test class | `Test.startTest()`/`Test.stopTest()` coverage of the SUCCESS and UNHANDLED_EXCEPTION paths |
| `Async_Job_Error__c` rows (or `Application_Log__c` via `templates/apex/ApplicationLogger.cls`) | Durable failure record carrying job ID, request ID, exception type, message, retry count |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the classes — full Queueable + Finalizer + test class, `-meta.xml`, `package.xml`, deploy and `sf apex run test` verification |
| `references/gotchas.md` | A Finalizer deployed but did nothing, retried forever, or lost its state — 10 grounded platform behaviours |
| `references/examples.md` | You want the narrative walk-through of the retry and logging scenarios before writing code |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated Finalizer code, or self-checking your own output |
| `references/well-architected.md` | You are justifying Finalizer retry vs. a polling monitor, or need the source list |

---

## Related Skills

- apex/apex-queueable-patterns — foundational Queueable design, chaining, and stack depth; use alongside this skill for the parent job structure
- apex/apex-batch-chaining — batch-to-batch chaining; Finalizers do not attach to Batch jobs
- apex/apex-limits-monitoring — monitoring the governor limits that make the parent Queueable fail in the first place
- apex/async-apex — choosing Queueable vs Batch vs `@future` vs Schedulable before a Finalizer is relevant
- apex/scheduled-apex-failure-detection-and-monitoring — the `AsyncApexJob` polling monitor that covers the abort path a Finalizer cannot
