---
name: flow-governor-limits-deep-dive
description: "Compute and budget governor-limit consumption per Flow type with worked math: SOQL, DML rows, CPU time, heap. Includes per-entry-point budget tables, cross-automation shared-limit math, and tuning strategies when a flow hits a ceiling. NOT for general bulkification (use flow-bulkification). NOT for Apex limits (use apex-governor-limits)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - flow
  - governor-limits
  - performance
  - soql
  - dml
  - cpu
  - heap
triggers:
  - "flow governor limits"
  - "flow soql 101 error"
  - "flow cpu time limit"
  - "flow dml rows exceeded"
  - "flow heap size exceeded"
  - "shared limits trigger flow"
inputs:
  - Flow type + entry context
  - Expected records per batch / per transaction
  - Concurrent automations on the same object
  - Existing Apex trigger limit consumption
outputs:
  - Per-element limit budget
  - Shared-transaction budget forecast
  - Tuning recommendations (bulkify, split, async-ify)
  - Pre-deployment benchmark plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Governor Limits Deep Dive

## When to use this skill

Activate when:

- A flow throws `System.LimitException: Too many SOQL queries: 101` or similar.
- You're architecting a flow that will run in a high-volume context (data loader imports, bulk API writes, batch recalcs).
- You need to estimate the limit footprint of adding a flow to an already-busy object trigger stack.
- You're tuning a flow that runs close to the limit ceiling in production.
- You're investigating CPU timeouts on record-triggered flows.

Do NOT use this skill for:
- General Flow bulkification patterns (use `skills/flow/flow-bulkification`).
- Apex-only limit math (use `skills/apex/apex-governor-limits` if it exists).
- Schema-design decisions driven by record volume (use `skills/architect/large-data-volume-design`).

## Core concept — limits are per-transaction, not per-flow

The platform enforces governor limits **per transaction**, not per flow. Two Before-Save flows on the same object share the transaction's SOQL budget. A flow running inside a triggered Apex context inherits the trigger's current consumption.

### Critical limits for flows

| Limit | Synchronous | Async | Shared across transaction |
|---|---|---|---|
| SOQL queries | 100 | 200 | Yes |
| SOQL rows | 50,000 | 50,000 | Yes |
| DML statements | 150 | 150 | Yes |
| DML rows | 10,000 | 10,000 | Yes |
| CPU time | 10,000 ms | 60,000 ms | Yes |
| Heap size | 6 MB | 12 MB | Yes |
| Callouts | 100 | 100 | Yes |

### Per-element cost approximation

| Flow element | SOQL | DML | Notes |
|---|---|---|---|
| Get Records | 1 per element | 0 | Rows count against 50,000 rows |
| Create Records | 0 | 1 per element | Rows count against 10,000 |
| Update Records | 0 | 1 per element | Rows count against 10,000 |
| Delete Records | 0 | 1 per element | Rows count against 10,000 |
| Loop | 0 | 0 | Depends on what's inside |
| Assignment | 0 | 0 | Free |
| Decision | 0 | 0 | Free |
| Subflow | Inherited | Inherited | Counts against parent transaction |
| Action (invocable Apex) | Varies | Varies | Apex action's own SOQL + DML add up |

**The key trap:** a Loop with a Get Records inside = 1 SOQL per loop iteration. 200 iterations = 200 SOQL = immediate limit breach.

## Recommended Workflow

1. **Enumerate every DML-class element** in the flow (Get, Create, Update, Delete, subflow, action).
2. **Map which elements are inside loops.** Loop + DML/SOQL inside is the #1 limit-breach pattern. Hoist outside the loop via collection-based DML.
3. **Account for shared limits.** If the flow runs on Account save, it shares the 100-SOQL budget with all other Account triggers, VRs, Before-Save flows, After-Save flows, and sharing recalculation.
4. **Run a budget check:** `(max_batch_size × per_record_cost) ≤ 0.7 × limit` — leave 30% headroom for other automations sharing the transaction.
5. **If budget is tight, tune:** hoist SOQL/DML out of loops, consolidate Get Records with OR-filters, cache field values, split work across transactions (Scheduled Paths, Platform Events).
6. **Pre-deployment benchmark.** In sandbox, exercise the flow with 200-record batches. Measure SOQL, DML, CPU via `Limits.getQueries()` wrapper in an Apex test.

## Key patterns

### Pattern 1 — Budget a record-triggered flow

Context: flow fires on Account update. Expected batch size: 200 records.

Elements:
- Get Records: related Contacts (1 SOQL, returns avg 5 Contacts per Account = 1000 rows).
- Loop over Contacts with Update Records inside. ← ALARM.

Un-tuned cost per batch:
- SOQL: 1 (Get Records outside loop)
- Contact Update: 1000 DML statements (1 per contact inside loop)

DML-statement limit: 150. Breach at the 150th Contact.

Tuned:
- Outside the loop, collect Contact updates into a collection variable.
- Single Update Records (collection) = 1 DML statement, 1000 DML rows.

Tuned cost: 1 SOQL + 1 DML, 1000 rows. Well under limits.

### Pattern 2 — Shared-transaction forecasting

Account trigger stack:
- Before-Save Validation (3 Get Records = 3 SOQL)
- Record-Triggered After-Save Flow A (2 Get Records + 1 Update = 2 SOQL + 1 DML)
- Record-Triggered After-Save Flow B (NEW — 4 Get Records + 1 Create = 4 SOQL + 1 DML)
- Existing Apex trigger (avg 15 SOQL + 3 DML per 200 records)

Total per 200-record batch: 24 SOQL + 5 DML (200 rows).
Available: 100 SOQL, 150 DML, 10,000 DML rows.
Headroom: 76 SOQL (OK).

Adding Flow B costs 4 SOQL + 1 DML from the shared pool. Fine here; if a fourth flow were to be added adding 10 more SOQL, the margin would shrink.

### Pattern 3 — Async offload

Same context but Flow B needs to do heavy enrichment (15 SOQL per record):
- Inline: 15 × 200 = 3000 SOQL. Breach.
- Async: mark Flow B's entry as "Run Asynchronously" (Scheduled Path +0 minutes). Fresh transaction per batch of 200 records; fresh 100-SOQL budget.

Trade-off: ~1-5 minute delivery delay, new-transaction idempotency requirement.

### Pattern 4 — CPU time tuning

Large loops with Assignments and Decisions consume CPU. Pattern that works in a 10-record test breaches at 200 records:

- Pre-compute lookups into a Map outside the loop (O(1) access inside).
- Avoid nested Loops; if you need Map-of-List shape, pre-compute outside.
- Move complex Formula evaluations out of inner Decisions.

CPU time is the hardest limit to diagnose — symptoms are timeouts, not explicit limit errors.

### Pattern 5 — Heap size management

Loop that accumulates all results into a big collection:
- 50,000 sObjects × avg 1 KB each = 50 MB. Heap limit breached at ~6 MB (async: 12 MB).
- Tuning: process in chunks via Scheduled Paths, or use a pass-through filter (transform + DML per chunk, don't accumulate).

## Bulk safety

This skill IS the bulk-safety math skill. Rules:
- Never DML inside a Loop.
- Never SOQL inside a Loop.
- Never accumulate unbounded results into a collection.
- Budget for shared transaction — don't assume the flow owns the whole 100 SOQL.

## Error handling

Limit exceptions terminate the transaction. Fault paths can't catch `System.LimitException` — the flow has already exceeded. The only recovery is:
- Reduce element consumption (bulkification).
- Split across transactions (async).
- Reduce batch size upstream (if caller is controllable).

## Well-Architected mapping

- **Performance** — budgeting limits is performance engineering. A flow with 70% limit headroom survives load spikes; a flow at 95% breaks under the first busy day.
- **Reliability** — shared-transaction math is what predicts cascading failures. Adding "one more flow" to a busy stack without budget analysis is the classic way orgs become fragile.

## Gotchas

See `references/gotchas.md`.

## Testing

```apex
@IsTest
static void testFlowStaysUnderLimits() {
    // Prepare 200-record bulk scenario.
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 200; i++) {
        accounts.add(new Account(Name = 'Test ' + i));
    }

    Test.startTest();
    insert accounts;
    Test.stopTest();

    // Assert total transaction stayed under 0.7 × limits.
    System.assertTrue(Limits.getQueries() < 70, 'SOQL budget exceeded');
    System.assertTrue(Limits.getDMLStatements() < 105, 'DML budget exceeded');
}
```

## Official Sources Used

- Salesforce Developer — Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Help — Flow Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Salesforce Help — Trigger Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Salesforce Architects — Performance Engineering: https://architect.salesforce.com/
