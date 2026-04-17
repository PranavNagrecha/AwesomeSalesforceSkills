---
name: flow-transactional-boundaries
description: "Reason about when a Flow is inside the caller's transaction vs starts its own. Pick Before-Save vs After-Save vs Async Path vs Pause + Resume when transaction boundaries matter. Covers governor-limit sharing, DML sequencing, recoverability, and the exact semantics of each Flow entry point. NOT for choosing Flow vs Apex (use automation-selection.md). NOT for Flow-to-Flow invocation contracts (use subflows-and-reusability)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - flow
  - transactions
  - before-save
  - after-save
  - scheduled-path
  - pause
  - orchestration
  - governor-limits
triggers:
  - "before-save vs after-save flow"
  - "flow called from apex governor limits"
  - "scheduled path transaction boundary"
  - "pause element in screen flow"
  - "orchestration step transaction"
  - "mixed dml error from flow"
  - "publish after commit in flow"
inputs:
  - Flow entry point (record-triggered, screen, autolaunched, scheduled, orchestration)
  - Work the flow must perform (DML, callouts, loops, time delay)
  - Upstream caller context (DML trigger, Apex, UI, scheduler, Platform Event)
outputs:
  - A transaction-boundary diagram for the flow
  - "Recommendation: Before-Save / After-Save / Scheduled Path / Pause / separate async"
  - Governor-limit budget per boundary
  - Idempotency + recoverability notes
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Transactional Boundaries

## When to use this skill

Activate this skill when:

- You need to decide whether a piece of Flow work should run **inline** (Before-Save / After-Save) or be pushed to a **new transaction** (Scheduled Path, Platform Event, pause, subflow-after-callout).
- You're debugging a governor-limit exception in a flow that fires mid-transaction.
- You're building a flow that calls a callout or does heavy DML and need to know which pattern is safe.
- You're composing record-triggered flows with Apex triggers and need to predict the shared limit footprint.
- You're deciding between a Screen Flow pause and an Orchestration stage for a multi-day workflow.

Do NOT use this skill to pick Flow vs Apex (that's `standards/decision-trees/automation-selection.md`), or to pick a Flow subtype (that's `standards/decision-trees/flow-pattern-selector.md` — this skill is activated AFTER that tree).

## Core concept — what is a "transaction" in Flow?

A Salesforce transaction is a unit of work bounded by:

- **Start:** a DML statement from a trigger, a user save from the UI, an Apex entry point (controller action, @HttpPost, future start), or a scheduler firing.
- **End:** the DML commits, or a rollback, or a governor-limit exception terminates the transaction.

Inside one transaction:
- SOQL queries count against the 100-query limit.
- DML rows count against the 10,000-row limit.
- CPU time counts against the 10-second limit (or 60s for async).
- All triggers, Before-Save flows, After-Save flows, validation rules, escalations, and Apex sharing share these limits.

Flow can either **join** an existing transaction or **start its own**. The choice changes everything about how the flow behaves under load and what happens on failure.

## Transaction behavior per Flow entry point

### Before-Save record-triggered flow

- Joins the triggering DML transaction.
- **No DML elements allowed.** Can only update the triggering record (via assignments), look up related records, and loop over collections.
- **No callouts.** Not supported in this context.
- **No subflows that do DML.** Autolaunched subflows that would do DML are blocked.
- Runs BEFORE the record is written, so changes to field values are free (no extra DML).
- Governor limits are **shared** with the rest of the transaction — but Before-Save is cheap, so the shared cost is usually negligible.

Use when: deriving field values on the same record. Setting `Status__c` from `Amount` + `Stage`. Copying account fields onto a case. Calculating a normalized phone.

### After-Save record-triggered flow

- Joins the triggering DML transaction.
- All elements allowed: DML, callouts (must be wrapped in a `Transaction Control` boundary or routed via a subflow to a pausable context), loops, subflows.
- DML row count **adds to** the shared 10,000-row limit with the trigger and any other after-save automations.
- **Callouts from After-Save inline will throw `System.CalloutException: Callout from triggers are currently not supported`.** To do callouts, either (a) mark the flow "Run Asynchronously" (scheduled-path-of-zero-minutes), or (b) emit a Platform Event and subscribe async.

Use when: creating related records, posting to Chatter, sending emails synchronously, updating unrelated records in the same transaction.

### Scheduled Path (on an after-save record-triggered flow)

- Starts a **new transaction**.
- Fresh governor limits. No DML sharing with the original trigger.
- The path fires at a configurable offset (+0 minutes = async-now, +30 days = SLA reminder).
- Callouts allowed.
- **Replays independently of the original save.** If the original save rolled back, the scheduled path never fires.
- If the record is deleted before the path fires, the path silently drops.

Use when: you want "eventually consistent" work that must not block the save; SLA reminders; fanout to related records; callouts.

### Autolaunched flow called from Apex

- Joins the calling Apex transaction.
- Governor limits shared with Apex.
- Apex can call a flow via `Flow.Interview.createInterview(flowName, params).start()` or via `@InvocableMethod`.
- Exceptions in the flow bubble up as `Flow.FlowException`; wrap the Apex call in try/catch if the caller wants to continue on flow failure.

Use when: Apex orchestrates the transaction but needs a declarative subroutine (admin-maintainable logic).

### Autolaunched flow called as a subflow

- Joins the parent flow's transaction.
- Shares limits with parent.
- **A subflow cannot escape the parent's transactional context** — if the parent is Before-Save, the subflow is too.

### Screen flow (user-facing)

- Each **save point** in a screen flow (a DML element then a subsequent screen) is its own transaction.
- The commit happens when the user clicks Next past a screen following a DML element, or at the final Finish.
- If the user navigates away, uncommitted changes are lost.
- Pause elements **persist the interview to the database** and end the current transaction.

### Screen flow with a Pause element

- Pause writes the `FlowInterview` record, ends the current transaction, and schedules resume.
- On resume (user click, time trigger, Platform Event received), a **new transaction** begins.
- All state (variables, collections) is serialized and deserialized — large state can hit serialization limits.

### Scheduled flow (fired by the clock, not by a record)

- Starts a new transaction.
- Fresh governor limits.
- Processes the record set defined in the flow's scheduler config; if the set is > 250k rows, the flow silently stalls on limits — escalate to Batchable Apex.

### Platform-Event-triggered flow

- Fires on event delivery; each event delivery is a **new transaction**.
- High-Volume Platform Events are delivered in batches (up to 2,000 per subscriber execution).
- Fresh governor limits per batch.
- **Ordering not guaranteed** unless you use "Published After Commit" on the publisher side AND subscribe with a single subscriber.

### Orchestration stage

- Each stage transition is a new transaction.
- Stage state persists in the `OrchestrationInstance` record.
- Work items (human tasks) assigned at stage entry; stage advances only when all work items complete.
- Ideal for multi-day workflows that would overrun screen-flow session timeouts.

## Recommended Workflow

1. **Read `standards/decision-trees/flow-pattern-selector.md`** to confirm the flow subtype.
2. **Classify the work** as (a) field derivation on same record, (b) inline DML across records, (c) needs callouts, (d) must be delayed / scheduled, (e) spans multiple user sessions, (f) spans multiple humans.
3. **Pick the transaction boundary** per the table in this skill.
4. **Draw the boundary diagram** — list every DML, every callout, every subflow and mark which transaction it runs in.
5. **Compute the governor-limit budget per boundary** — if a Before-Save joins a transaction already running 85 SOQL, your flow's 15 SOQL budget is tight.
6. **Plan idempotency** — any work in a new transaction must be safe to run twice (scheduled paths, platform-event fanouts retry on failure).
7. **Document the boundary diagram in the flow description** so downstream maintainers don't bypass the reasoning.

## Key patterns

### Pattern 1 — "Derive then act" split

Before-Save derives fields on the same record; After-Save (same flow or a sibling flow) creates related records.

```
[Trigger record updated]
        │
        ▼
[Before-Save Flow]  ← derives Normalized_Phone__c, Region__c
        │ (same txn)
        ▼
[Record written to DB]
        │ (same txn)
        ▼
[After-Save Flow]   ← creates related Task + Chatter post
        │ (same txn)
        ▼
[Transaction commits]
```

Savings: the Before-Save avoids a second DML for the field update — roughly a 90% cost reduction vs an After-Save that re-updates.

### Pattern 2 — "Callout-required → Scheduled Path +0"

An After-Save flow needs to call an external service. Inline callouts are blocked in a trigger context. Route via a Scheduled Path with +0 minutes.

```
[Record inserted]
        │
        ▼
[After-Save Flow entry]
        │
        ▼
[Scheduled Path: +0 minutes, criteria: Status = 'Ready']
        │  (new txn, fresh limits)
        ▼
[HTTP callout to vendor]
        │
        ▼
[Update record with vendor ref]
```

Key detail: the +0 minutes doesn't mean "immediate" — the scheduler picks up the work, typically within 1–5 minutes. Not suitable for latency-sensitive needs.

### Pattern 3 — Multi-day approval via Orchestration

Instead of a screen flow with pause elements (fragile, limited to one user's session), use an Orchestration with three stages: Legal Review → Procurement Review → Customer Sign-off. Each stage is a new transaction; each assigns a work item to a named user or queue.

See `skills/flow/orchestration-flows` for stage authoring.

### Pattern 4 — "Platform Event fanout" for decoupled writes

A single trigger needs to update 5 unrelated objects. Instead of inline After-Save DML (which shares the 10,000-row limit with the trigger), publish one Platform Event and have 5 independent PE-triggered flows each handle one target. Each subscriber runs in its own transaction with fresh limits.

## Bulk safety

- **Before-Save flows are the most bulk-safe** — no DML, simple element set, shared-limit impact is tiny.
- **After-Save flows must be written with bulk DML in mind** — use a Create Records element with a collection, never a loop with a DML inside.
- **Scheduled Paths process records in batches of up to 200.** If your record set per trigger event is larger than that, multiple scheduled-path executions run in parallel — plan for concurrent writes and set `Allow Concurrent Execution = true` only when truly safe.
- **Platform-Event-triggered flows** receive events in batches of up to 2,000 per Standard PE, 10,000 per High-Volume PE. The flow's loop body runs once per event in the batch; loops must be bulk-safe.
- **Scheduled flows run once per scheduled execution** and process the query result set. If you use a Loop element, every DML inside is one-per-record — convert to a collection and do a single Update Records.

## Error handling

- **Before-Save:** errors bubble as record save errors (user sees the Flow Error message as a save error). No fault path needed; the triggering DML is rolled back.
- **After-Save inline:** errors roll back the entire triggering transaction unless wrapped in a fault path that catches + logs. Always wire a Fault connector (see `skills/flow/fault-handling`).
- **Scheduled Path:** errors end the scheduled-path transaction; the original save is already committed, so no rollback. Salesforce retries the scheduled-path execution up to 3 times with exponential backoff, then marks it failed. Use the Flow runtime error report.
- **Platform-Event-triggered:** on failure, the event is re-queued (Standard PE) or dropped (High-Volume PE with non-idempotent subscriber). Write subscribers to be idempotent — use an external-id field to dedupe.
- **Screen flow pause:** if resume fails, the interview stays in "Paused Error" state. Monitor via the Paused and Waiting Interviews list.

## Well-Architected mapping

- **Reliability** — transaction boundary choice determines rollback scope. Before-Save failures roll back the user's save (often desirable for validation-like work). Scheduled Paths isolate failures (won't poison the original save). Pick based on whether the work is essential (inline) or eventually consistent (async).
- **Performance** — Before-Save is much cheaper than After-Save for field derivation. Scheduled Paths trade latency for limit isolation. Orchestrations add persistence overhead — use only when multi-day work genuinely needs it.
- **Security** — cross-transaction work (Scheduled Paths, Platform Events) runs as the "Automated Process" user or the record owner depending on version settings. CRUD/FLS posture may differ from the original trigger; verify with `skills/apex/apex-security-crud-fls` principles.

## Gotchas

See `references/gotchas.md`.

## Testing

See `skills/flow/flow-testing`. Key testing concerns per boundary:

- Before-Save: assert field values on the returned record without DML.
- After-Save: assert DML results via SOQL after test setup commits.
- Scheduled Path: invoke `Test.startTest()` / `Test.stopTest()` — scheduled-path records fire synchronously inside the test block.
- Platform-Event-triggered: use `Test.startTest() / Test.stopTest()` to flush the event bus.

## Official Sources Used

- Salesforce Help — Flow Run-Time Behavior: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_runtime.htm
- Salesforce Developer — Trigger Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Salesforce Help — Scheduled Paths in Record-Triggered Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_scheduled_path.htm
- Salesforce Developer — Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
