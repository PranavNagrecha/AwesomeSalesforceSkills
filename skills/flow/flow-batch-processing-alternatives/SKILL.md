---
name: flow-batch-processing-alternatives
description: "Use when a Scheduled Flow or Record-Triggered Flow needs to process more records than Flow can safely handle in a single run. Covers Flow limit realities, scheduled-path chunking, Data Cloud batch transforms, and Apex. NOT for choosing async across a general workflow (see async-selection decision tree) — use flow/flow-large-data-volume-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "scheduled flow hitting limits"
  - "flow batch alternative"
  - "process thousands of records in flow"
  - "flow vs queueable batch"
  - "flow interview limit"
tags:
  - flow
  - scale
  - batch
  - async
  - limits
inputs:
  - Current Scheduled Flow or Record-Triggered Flow
  - Volume of records per run (today and projected)
  - Governor / DML / CPU limits currently observed
outputs:
  - Decision on continuing in Flow, chunking in Flow, or escalating to Apex
  - Implementation pattern (scheduled path, Platform Event, Queueable)
  - Monitoring and retry plan
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow Batch Processing Alternatives

## Purpose

Flow can process a lot of records — until it can't. Admin teams often build a
Scheduled Flow expecting it to handle "whatever comes," then hit a CPU or DML
limit silently, with no retry. This skill lays out the real limits,
chunking patterns that extend Flow's reach, and the clean escalation path to
Apex Queueable or Batch when the workload outgrows Flow.

## Recommended Workflow

1. **Compute the real cost: `per-interview cost × batch size`.** Count the Get
   Records and DML elements on the path a single interview takes, multiply by
   the batch size (200 unless you changed it), and compare that to the
   per-transaction limits. This number, not the record count, is what fails.
2. **Hoist first, size second.** If the per-interview cost is a query or a DML
   that could live outside the per-record path, fix that — it is free.
   `flow/flow-bulkification` owns the technique.
3. **Lower the batch size only for irreducible per-interview work.** Set it on
   the Start element, 1–200, on runtime version 63.0 or later. It buys governor
   headroom at a proportional cost in throughput. The lever only moves down; 200
   is already the default and the maximum.
4. **Check the org-wide daily ceiling.** Schedule-triggered flow interviews are
   capped at 250,000 per 24 hours, or user licenses × 200, whichever is greater
   — shared across every scheduled flow in the org.
5. **Add per-chunk observability before you add scale.** A log row per chunk
   (id, count, outcome, timestamp), an alert on rate change, and an off switch
   that does not require deactivating the flow.
6. **Escalate to Apex for a capability, never for a record count.** See the
   table below, and cite the branch of
   `standards/decision-trees/async-selection.md` that resolved the choice.

## Real Flow Limits That Bite

- **Governor limits are per transaction, not per interview.** A schedule-triggered
  flow runs one interview per matching record, and the platform groups those
  interviews into batches of up to 200 that share one transaction's budget. One
  Get Records plus one Update per interview is 200 SOQL and 200 DML statements in
  a single transaction — which is why the flow fails at 200 records for the same
  reason it fails at 300,000. Volume is never the variable; `per-interview cost ×
  batch size` is.
- **Which ceiling that lands against depends on the runtime version.** The
  *Improve Scheduled Flow Performance with Updated Limits* release update puts
  schedule-triggered flows on **asynchronous** per-transaction limits from runtime
  version 61.0 — 200 SOQL and 60,000 ms CPU rather than 100 and 10,000 ms. A
  custom batch size already requires 63.0, so any flow this skill tells you to
  size is on asynchronous limits. Read the error number before diagnosing:
  `Too many SOQL queries: 101` means the flow is still on a pre-61.0 runtime;
  `: 201` means it is on asynchronous limits and the per-interview work is
  genuinely too heavy.
- **DML did not move.** DML statements stay at 150 per transaction on both sides,
  and DML rows at 10,000. One Update per interview at a full 200-interview batch
  breaches 150 even where the 200 queries fit exactly. On a modern scheduled flow,
  DML is usually what fails first, not SOQL.
- **Batch size is settable from the Start element, 1–200,** on runtime version
  63.0 or later. Below that version the field has no effect and the flow silently
  keeps the 200 default.
- **The daily interview ceiling is org-wide:** 250,000 per 24 hours or user
  licenses × 200, whichever is greater. Adding a high-volume job consumes headroom
  every other scheduled flow relies on.
- **Interviews carry no ordering guarantee** within or across batches.
- **CPU is the quiet one.** 60,000 ms asynchronous covers 200 interviews of
  formula-heavy, related-record work less comfortably than teams expect — and a
  flow still on a pre-61.0 runtime version is working with 10,000 ms.
- **There is no graceful partial retry inside Flow.** The next scheduled run is
  not a retry; it re-evaluates the filter.

## Chunking Patterns Inside Flow

- **Start-element batch size:** the first thing to reach for on recurring work.
  One field, no moving parts.
- **Platform Event fan-out:** each chunk becomes an independent transaction with
  its own fault path and log row, so failure is scoped and retryable per chunk.
  The subscriber is itself batched at up to 200 messages and needs bulkifying
  too — fanning out at the publisher does not exempt it.
- **Scheduled Path on a record-triggered flow:** spreads load across time for
  work that is triggered by a record change rather than scheduled.
- **Checkpoint control record:** a `Last_Processed_Id__c` plus `Id >` ordering,
  a status field as an off switch, and a progress counter. Now a last resort for
  recurring work, still the right answer for a one-shot backfill that needs those
  three artifacts.
- **Invocable Apex as a pure splitter:** Flow keeps orchestration, Apex does the
  chunking arithmetic. Pass the whole collection — never call the invocable
  inside the loop.

## When To Move To Apex

Escalate for a capability Flow does not have, not for a record count.

| Reason | What Flow cannot do |
|---|---|
| Retry with a known outcome | Flow has no finalizer. `System.Finalizer` sees `SUCCESS` or `UNHANDLED_EXCEPTION` and can re-enqueue a failed Queueable up to five times |
| Per-record callouts | Callouts cannot follow DML in the same transaction; Flow's sequencing options are narrower |
| State across transactions | `Database.Stateful` retains instance member variables between transactions (statics still reset) |
| Multi-million-record scans | `Database.QueryLocator` streams; a Flow Get Records is bounded by 50,000 rows per transaction |
| Chained steps surviving partial failure | Queueable chaining plus a finalizer gives explicit control |

What escalation does **not** buy: headroom against the daily ceiling. Batch Apex
method executions are capped at 250,000 per 24 hours or user licenses × 200 —
the same number and formula as flow interviews. It also does not buy unbounded
concurrency: 5 batch jobs queued or active, with up to 100 more Holding in the
flex queue, org-wide and shared with managed packages.

If the daily ceiling is the binding constraint, the fix is to process fewer
records — tighter filters, incremental rather than full scans — not a different
engine.

## Target Apex Patterns

- **Queueable + Finalizer:** chained work needing an explicit success/failure
  signal and bounded retry.
- **Database.Batchable:** large scans with stable logic. Scope defaults to 200,
  caps at 2,000 for a `QueryLocator`, and the documentation notes the optimal
  scope is a factor of 2,000.
- **Platform Events + subscriber:** asynchronous fan-out with independent failure
  domains.

Link the Apex implementation back to Flow through an Invocable Action so admins
keep an orchestration view they can read and disable.

## Monitoring Plan

- Log each chunk's start, end, record count, and status to a custom object.
- Emit a Platform Event on failure for ops dashboards.
- Alert when chunks skipped or CPU used > 80% of limit.

## Anti-Patterns (see `references/llm-anti-patterns.md`)

- "We'll just raise the Scheduled Flow batch size" — the lever only moves down,
  and raising it would make the arithmetic worse.
- Analysing governor limits per interview instead of per transaction.
- Costing a schedule-triggered flow against the synchronous SOQL limit of 100
  when its runtime version puts it on 200 — and prescribing an Apex rewrite for
  a transaction that was never over the ceiling.
- Calling an Invocable Action inside a Flow loop.
- Proposing the checkpoint control record for recurring work that a batch-size
  field would fix.
- Rejecting a Platform Event fan-out on the delivery allocation, which does not
  apply to flows.
- Expecting smaller chunks to fix a Mixed DML error.

## Related

- `flow/flow-bulkification` — the fix that batch sizing is often a substitute for.
- `flow/flow-and-platform-events` — fan-out mechanics and the subscriber's own
  batch.
- `flow/flow-large-data-volume-patterns` — LDV query and index behaviour.
- `apex/apex-transaction-finalizers` — the retry semantics Flow lacks.
- `standards/decision-trees/async-selection.md` — the formal engine choice.

## Official Sources Used

- Per-Transaction Apex Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Using Batch Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Transaction Finalizers — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Improve Performance with Batching for Scheduled Flows (Summer '26) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_scheduled_flow_batching.htm&release=262&type=5
- Improve Scheduled Flow Performance with Updated Limits (Summer '24 release update; scheduled flows move to asynchronous limits at runtime version 61.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_release_update_improve_scheduled_flow_performance_with_updated_limitsxml.htm&release=250&type=5
- Schedule-Triggered Flow Considerations — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_trigger_schedule.htm&type=5
- Platform Event Allocations — delivery excludes Apex triggers, flows and Process Builder; those consume the publishing allocation — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Subscribe to Platform Events with Apex Triggers — "when governor limits are different for synchronous and asynchronous Apex, the synchronous limits apply to platform event triggers" — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex.htm

The full annotated list is in `references/well-architected.md`.
