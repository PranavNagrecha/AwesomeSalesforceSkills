---
name: callout-and-dml-transaction-boundaries
description: "Use when diagnosing, preventing, or refactoring the 'You have uncommitted work pending' CalloutException caused by mixing DML and callouts in the same Apex transaction. Triggers: 'uncommitted work pending', 'callout after DML', 'DML between callouts'. NOT for general HTTP callout construction, Named Credential setup, or async Apex design in isolation."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "System.CalloutException You have uncommitted work pending"
  - "why does my callout fail after an insert or update in the same method"
  - "how to do DML and a callout in the same Apex transaction"
  - "can I make a callout between two DML statements"
  - "callout fails in trigger because record was already saved"
tags:
  - callout-dml-boundary
  - uncommitted-work-pending
  - transaction-scope
  - queueable-callout
  - future-callout
inputs:
  - "the Apex transaction context — trigger, controller, Queueable, Batch, or scheduled job"
  - "the order of DML and callout operations in the current execution path"
  - "whether the callout result is needed before the DML or can be deferred"
outputs:
  - "refactored transaction design that separates callout and DML into safe boundaries"
  - "diagnosis of which DML operation is causing the uncommitted-work-pending error"
  - "recommendation for Queueable, @future, or reordering approach"
dependencies:
  - callouts-and-http-integrations
  - apex-queueable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Callout and DML Transaction Boundaries

Use this skill when Apex code that mixes outbound HTTP callouts and DML operations fails with `System.CalloutException: You have uncommitted work pending`, or when you need to architect a transaction that requires both callouts and database writes without hitting this restriction.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the full execution path? The restriction is transaction-scoped, not method-scoped. DML in any helper, trigger, or utility class earlier in the same transaction counts.
- Does the callout result determine what gets saved, or can the callout happen after the DML commits?
- Is this running synchronously (trigger, controller) or asynchronously (Queueable, Batch, @future)?

---

## Core Concepts

### The Uncommitted-Work-Pending Rule Is Transaction-Scoped

Salesforce enforces a hard rule: if any DML statement (insert, update, delete, upsert, or Database methods) has executed in the current Apex transaction, all subsequent callouts in that same transaction throw `System.CalloutException: You have uncommitted work pending`. This applies to the entire transaction, not just the current method. DML performed in a trigger handler, a utility class, or even a managed package that fires earlier in the same execution context will block a callout later.

### Callout-DML-Callout Is Also Prohibited

It is not enough to do the callout first and then DML. If you need a second callout after DML, the same restriction applies. Any pattern like callout -> DML -> callout requires the second callout to move to a separate async boundary, because the DML in the middle creates uncommitted work for the remainder of the transaction.

### Async Boundaries Reset the Transaction

The canonical fix is to split the work across transaction boundaries. A Queueable that implements `Database.AllowsCallouts` runs in its own transaction with a clean DML slate. The original transaction performs DML and enqueues the Queueable; the Queueable then executes callouts in its own fresh context. `@future(callout=true)` is an older alternative that also creates a new transaction boundary but cannot accept sObject parameters or be chained.

### Callout-First Is the Simplest Synchronous Fix

When the callout result is needed before saving, the simplest approach is to reorder the code: perform the callout first, capture the response, and only then execute DML. This works as long as no DML has occurred anywhere earlier in the transaction — including triggers, before-save flows, or validation-rule side effects.

---

## Common Patterns

### Pattern 1: Callout First, DML Second (Synchronous)

**When to use:** The callout response determines what data to save, and no DML has occurred yet in the transaction.

**How it works:**

1. Make the HTTP callout and capture the response.
2. Parse and validate the response.
3. Perform DML with the callout-derived data.

**Why not the alternative:** This avoids async complexity entirely. It fails only if something else in the transaction (a trigger, flow, or managed package) has already performed DML before your code runs.

### Pattern 2: DML First, Queueable Callout After Commit

**When to use:** Business data must be saved first, and the callout can happen after the transaction commits. This is the most common real-world pattern.

**How it works:**

1. Perform all DML in the synchronous transaction.
2. Enqueue a Queueable that implements `Database.AllowsCallouts`, passing record IDs.
3. In the Queueable `execute()`, re-query the records and make the callout.
4. Update integration status fields from within the Queueable's own transaction.

**Why not the alternative:** `@future(callout=true)` also works but cannot accept sObjects, cannot be chained, and cannot be monitored via AsyncApexJob as easily. Queueable is the modern standard.

### Pattern 3: Split Callout-DML-Callout With Chained Queueables

**When to use:** The flow requires callout A, then DML, then callout B.

**How it works:**

1. Make callout A synchronously (before any DML).
2. Perform DML.
3. Enqueue a Queueable for callout B, passing the IDs and any state needed from callout A.

**Why not the alternative:** Attempting all three operations in a single synchronous execution always fails. The second callout hits uncommitted work from the DML.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Callout result needed before DML, no prior DML in transaction | Callout first, then DML (synchronous) | Simplest; no async overhead |
| DML must happen first, callout can be deferred | Enqueue Queueable with `Database.AllowsCallouts` | Clean transaction boundary; chainable |
| Trigger context needs to fire callout | Enqueue Queueable from trigger handler | Triggers always have pending DML from the triggering record |
| Two callouts separated by DML | First callout synchronous, DML, then Queueable for second callout | Only way to satisfy both boundaries |
| Legacy code, cannot refactor to Queueable | `@future(callout=true)` | Works but limited: no sObject params, no chaining |
| Batch job needs callouts and DML per chunk | Implement `Database.AllowsCallouts` on Batch; callout before DML in each `execute()` | Each `execute()` is its own transaction |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map the full transaction path.** Trace every DML and callout in the execution — including triggers, flows, and helper classes — to identify the exact ordering.
2. **Identify which DML blocks the callout.** The culprit is often not in the same class. Check trigger handlers, before-save flows, and utility methods that fire before your callout code.
3. **Decide if the callout can move before all DML.** If yes, reorder synchronously. If no, introduce an async boundary.
4. **Implement the async boundary.** Create a Queueable implementing `Database.AllowsCallouts`. Pass only record IDs, not sObjects. Re-query inside the Queueable.
5. **Add error handling for the async path.** The Queueable runs in a separate transaction. If the callout fails, the original DML is already committed. Design retry or status-tracking logic.
6. **Test both success and failure.** Use `Test.setMock()` and `Test.startTest()`/`Test.stopTest()` to force Queueable execution. Verify that the callout fires and that failures are logged.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No DML occurs before any callout in the same synchronous transaction
- [ ] Queueable classes that make callouts implement `Database.AllowsCallouts`
- [ ] Record IDs (not sObjects) are passed to async boundaries
- [ ] The callout-dependent path has error handling for async failure scenarios
- [ ] Trigger handlers do not attempt direct callouts
- [ ] Test classes use `Test.setMock()` and verify both sync DML and async callout behavior

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **DML in managed packages counts.** If an installed package performs DML in a trigger or subscriber handler before your code runs, your callout will fail even though your code has no DML. The only fix is to move your callout to an async boundary.
2. **Before-save flows can cause hidden DML.** A before-save record-triggered flow that creates or updates a related record introduces DML before your after-save logic runs. This is invisible in the Apex call stack.
3. **System.enqueueJob counts toward the Queueable limit.** In synchronous transactions, you can enqueue up to 50 Queueable jobs. In a Queueable's own execute, you can enqueue exactly 1 (for chaining). Plan your splitting accordingly.
4. **@future cannot call @future.** If your code is already inside an @future method, you cannot call another @future to split the transaction. Use Queueable for chainable async work.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refactored transaction design | Diagram or description showing DML and callout separated into safe boundaries |
| Queueable callout class | Apex class implementing Queueable and Database.AllowsCallouts |
| Integration status field recommendation | Custom field to track whether the async callout succeeded or needs retry |

---

## Related Skills

- callouts-and-http-integrations — use for HTTP callout construction, Named Credentials, and mock testing patterns
- apex-queueable-patterns — use for Queueable design, chaining, error handling, and monitoring
- async-apex — use for choosing between @future, Queueable, Batch, and Scheduled Apex
- trigger-framework — use when the callout boundary problem originates in trigger execution context

---

## Official Sources Used

- Apex Developer Guide: Invoking Callouts Using Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Apex Developer Guide: Callout Limits and Limitations — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm
- Salesforce Help: "You have uncommitted work pending" — https://help.salesforce.com/s/articleView?id=000389332
- Apex Developer Guide: Queueable Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
