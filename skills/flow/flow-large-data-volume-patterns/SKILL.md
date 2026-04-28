---
name: flow-large-data-volume-patterns
description: "Use when Flows must stay healthy at large data volumes: total SOQL rows returned per transaction, unbounded Get Records, collection sizing, scheduled or record-triggered scale, and when to cap or move work async. Triggers: 'Too many query rows 50001 flow', 'Get Records returns too many rows', 'LDV flow design', 'flow collection limit', 'record triggered flow production data volume'. NOT for writing or tuning Batch Apex jobs, Bulk API 2.0 data loads, or general Flow Builder UX when volume and governor ceilings are not the concern."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "Too many query rows 50001 in my record triggered flow"
  - "Get Records in Flow returns more rows than I expected at scale"
  - "how do I cap records retrieved in Flow Get Records Spring 25"
  - "LDV org automation record triggered flow keeps failing in production"
  - "flow works in sandbox but fails when related object has millions of rows"
tags:
  - flow-large-data-volume-patterns
  - governor-limits
  - get-records
  - ldv
  - soql-rows
  - collections
inputs:
  - "flow type (record-triggered, autolaunched, scheduled, screen) and entry conditions"
  - "approximate row counts for objects queried and related fan-out per transaction"
  - "whether Get Records is first record only, all records, or capped with a limit"
outputs:
  - "risk assessment against query-row and collection ceilings"
  - "redesign options: cap queries, narrow filters, async path, or Apex boundary"
  - "test plan for production-like volumes"
dependencies:
  - flow/flow-bulkification
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

Large data volume (LDV) problems in Flow usually show up as sudden production failures while sandbox tests look fine. The platform still applies the same transactional ceilings as Apex, including the total count of rows returned by SOQL across the whole transaction. A single `Get Records` element that asks for "all" matching rows can return up to the platform query-rows ceiling for that transaction; when related data grows, the same element crosses the line and the interview fails with a query-rows error. This skill focuses on those volume ceilings, how to cap and narrow retrieval, how collections participate in memory pressure, and when Flow should hand off to asynchronous or code-based processing. Pair it with `flow-bulkification` for loop and per-iteration query patterns.

LDV is the only domain in Flow where "it works in sandbox" is explicitly misleading. Sandboxes don't have production's data distribution; dev orgs have even less. The discipline this skill teaches is MODELING production scale in design reviews, not discovering it during an incident.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Confirm **maximum rows** each `Get Records` could return in production (not just "a few" in a dev org).
- Identify **everything else** in the same transaction: other flows, Apex, validation rules, and duplicate rules all share one governor budget.
- Note whether the flow is **before-save or after-save**, **scheduled**, or **autolaunched from bulk paths**; each changes how often the expensive elements run.
- What's the worst-case related-record count? (`Contact` per `Account` can be 10k+ in some CRM orgs; `Case` per `Account` can be millions in service-heavy orgs.)
- Does the object use `Indexed Custom Fields` or Skinny Tables? (Affects query performance planning.)

## Core Concepts

### Total SOQL rows are aggregated per transaction

Salesforce counts rows returned by SOQL across the transaction toward a single 50,000-row limit. In Flow, each `Get Records` issues SOQL (unless the documented exception applies, such as certain metadata reads). Several modest queries that each return many rows can fail together even when no single query looks "large." Volume planning must use **total rows returned**, not only query count.

**Shared across:**
- All Flows in the same transaction.
- All Apex triggers on the same save.
- All Validation Rules.
- All Duplicate Rules.

Example failure mode: a record-triggered before-save Flow queries 2,000 Contacts; an after-save Flow on the same save queries 10,000 Cases; the Apex trigger queries 40,000 Opportunities. Each alone is fine; together they hit 52,000 — over the 50k ceiling. The save rolls back entirely.

### Unbounded "get all" retrieval is an LDV smell

Designs that retrieve "all" child or related rows for a parent without a tight filter, sort, and row cap assume the related set stays small. In LDV orgs that assumption breaks first. Prefer selective filters, ordering with a clear business rule, and an explicit maximum number of records to retrieve where the product supports it, so behavior stays predictable as data grows.

Unbounded retrieval examples:
- "Get Records: all Contacts where AccountId = current Account" — fails when the Account has 10k+ contacts.
- "Get Records: all Cases where Status != 'Closed'" — fails when open-case backlog grows.
- "Get Records: all Opportunities where CloseDate > TODAY - 365" — fails when the org has years of pipeline.

### Collections and interview data add memory pressure

Flows store intermediate collections in the interview's working set. Very large collections increase the chance of heap-related failures (6MB sync / 12MB async) and slow element execution even before hard limits. Shaping data early — fewer fields, fewer rows, pre-aggregation in a database-friendly layer — reduces risk.

**Heap cost per field type (rough):**
- Text / Phone / Email / URL: ~50-100 bytes per field per record.
- Number / Currency / Date / DateTime: ~16 bytes.
- Reference (lookup): ~18 bytes for the ID.
- Long Text Area: variable, can be huge.

A collection of 10k records with 10 fields each easily hits 10k × 10 × 100 = 10MB. Past the sync heap limit.

### Flow is not the right engine for every LDV batch

When the requirement is to scan or update millions of rows on a schedule, platform batch patterns outside the interactive Flow interview (Batch Apex, integration pipeline) are usually more appropriate. Flow can still coordinate a bounded unit of work, publish an event, or call invocable Apex that implements chunking.

**Signals Flow is the wrong engine:**
- Source set > 10k records.
- Per-record processing exceeds 100ms.
- Processing must continue across multiple async invocations.
- True batch semantics needed (start/execute/finish callbacks).

## Common Patterns

### Pattern 1: Cap and narrow `Get Records` before production data arrives

**When to use:** Related object cardinality is unknown or unbounded, or the flow only needs a bounded slice.

**Structure:**
1. Add selective filters on indexed fields (Id, Name, CreatedDate, LastModifiedDate, or custom-indexed custom fields).
2. Select only the fields the flow USES; don't leave "all fields" checked.
3. Sort by a business-meaningful field (usually CreatedDate DESC or similar).
4. Set "Number of Records to Store" to an explicit limit (e.g. 100). Available when the flow only needs top-N semantics.
5. Document the worst-case row count in the Flow description.

### Pattern 2: One query, in-memory correlation, single write

**When to use:** Many triggering records need related data, but fan-out per parent is bounded.

**Structure:** Query once with a parent-centric filter (IDs from the triggering collection), build or filter collections in Assignment + Collection Filter elements, update in bulk after correlation. See `flow/flow-bulkification` Pattern 1 for the canonical form; here the emphasis is on **row count** of that single query staying under budget.

### Pattern 3: Async handoff for unbounded work

**When to use:** The business process truly requires processing an unpredictable or large set that cannot be capped safely in Flow.

**Structure:**
1. Synchronous Flow validates + stamps status + publishes a Platform Event.
2. Platform-Event-Triggered Flow OR Apex subscriber processes the event async.
3. If the work is chunked (e.g. "process these 500 records"), the async subscriber invokes Queueable or Batch Apex.
4. Document idempotency (what if the event is delivered twice?).

### Pattern 4: Row-budget worksheet before design approval

**When to use:** Any record-triggered Flow on a high-volume object.

**Structure:**
```
Production volume assumptions:
- Bulk cardinality: 200 (API standard batch size)
- Expected peak concurrency: 10 batches/minute

Per-interview query budget:
  Get Records #1 (related Contacts): max 50 rows × 200 interviews = 10,000 rows ✅
  Get Records #2 (Account details):  max 1 row × 200 interviews = 200 rows ✅
  Subflow query:                    max 10 rows × 200 interviews = 2,000 rows ✅
  Total:                                                         12,200 rows ✅ (under 50k)

If Apex triggers on same object run concurrently:
  Apex trigger SOQL estimate:                                    20,000 rows
  Combined:                                                      32,200 rows ✅ (still under 50k but tight)
```

Design approvers MUST see this math before sign-off.

## Decision Guidance

| Situation | Recommended approach | Reason |
|-----------|----------------------|--------|
| Error mentions query rows near 50,000 | Audit every `Get Records` in the transaction path; add caps and filters | Total returned rows drive the failure |
| Related list can grow without bound | Do not model "load all children" in synchronous Flow (Pattern 1 or 3) | Unbounded retrieval structurally unsafe |
| Need latest or first logical row | Sort + first record only, or cap with limit | Bounded semantics |
| Nightly millions-of-rows processing | Batch Apex or integration outside Flow (Pattern 3) | Flow interviews are not bulk ETL engines |
| Custom Metadata / settings reads | Follow product docs for query cost | Some metadata reads are optimized; standard objects are not |
| Design review on LDV-prone flow | Require Pattern 4 worksheet | Math before sign-off |
| Flow works in sandbox, fails in prod | Run worst-case volume test in full-copy sandbox | Dev sandboxes hide LDV failures |

## Recommended Workflow

1. **Inventory retrieval** — List every `Get Records`, subflow, and invocable Apex in the path; estimate worst-case rows per element and the sum across the transaction.
2. **Read current limits** — Confirm Flow and transaction limits from Salesforce Help for your edition, especially query rows and DML rows, before changing design.
3. **Apply caps first** — Tighten filters, reduce selected fields, add sort and row cap options; remove any "retrieve all" that is not strictly required.
4. **Align with bulkification** — Run `flow-bulkification` patterns so no loop multiplies queries or DML; recompute row totals after refactor.
5. **Test at volume** — Use realistic parent counts and related-list sizes (copy-based or integration test); assert the flow still completes when related tables are large.
6. **Escalate deliberately** — If caps break business requirements, document the gap and move processing to async Apex, orchestration, or an external system rather than expanding Flow scope.
7. **Row-budget sign-off** — Require Pattern 4 worksheet attached to change-management ticket.

## Review Checklist

- [ ] Each `Get Records` has a documented worst-case row count under production assumptions.
- [ ] No synchronous path depends on retrieving an unbounded "all related" set.
- [ ] Sort and "first record only" or explicit row limits match the business rule.
- [ ] Combined SOQL row usage for Flow + other automation in the same transaction has headroom.
- [ ] Large scheduled or batch-style work is not implemented solely as a wide Flow on huge objects without chunking.
- [ ] Fault paths and monitoring exist for the high-volume scenario, not only single-record UI tests.
- [ ] Row-budget worksheet (Pattern 4) attached to change-management artifacts.
- [ ] Full-copy sandbox test done (not just dev sandbox).
- [ ] Field selection narrowed to what the Flow actually uses (heap discipline).

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org's data distribution, the flow's transaction context, and co-existing automation
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; always compute the math
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **Sandbox parity** — Small related sets in developer sandboxes do not exercise query-row limits; failures appear first in full-copy or production-like data.
2. **Shared transaction** — Imports and APIs can place many records in one transaction; a flow that was safe per user save can fail under bulk loading.
3. **Field set size** — Querying "all fields" or wide layouts increases heap pressure per row; retrieve only what the flow uses.
4. **Non-selective filters on non-indexed fields** — Salesforce's query optimizer may refuse to run the query if it's too expensive; `QUERY_TIMEOUT` is the symptom.
5. **Cross-object queries have tighter limits** — `SELECT Id FROM Account WHERE Id IN (SELECT AccountId FROM Contact)` evaluates the inner + outer against the same limits.
6. **`WITH SECURITY_ENFORCED` in Flow (indirect via Apex)** — if an invocable Apex uses this, FLS-blocked fields cause the query to fail entirely; confirm Guest/external user FLS.
7. **Platform Cache can hide staleness issues** — if the Flow reads from cached data, LDV tests might not surface cache-miss latency spikes.
8. **Big Objects have a different query model** — can't use them the same way as sObjects in Flow; async SOQL required.
9. **Batch Apex called from Flow still obeys Flow's governor budget for the invocation** — the Apex async execution is separate, but the Flow-side setup costs money too.
10. **"Number of Records to Store" limit doesn't always mean the query returns fewer rows** — for some filter shapes, Salesforce fetches more than the limit then caps in-memory; query row count can still exceed budget.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Get Records with no filter AND no limit** → Flag as Critical. LDV ticking time bomb.
- **Get Records retrieving "all fields"** → Flag as High. Heap pressure; narrow selection.
- **Record-triggered Flow on a high-volume object with no row-budget worksheet** → Flag as High. Design review gap.
- **No full-copy sandbox testing plan for LDV-prone Flow** → Flag as High. Production will be the first real test.
- **Collection size approaching 10k records** → Flag as High. Near heap limit.
- **Combined Apex + Flow SOQL math not documented** → Flag as Medium. Hidden shared-budget risk.
- **Non-selective filter on non-indexed field** → Flag as High. Query optimizer may refuse.
- **LDV design without async escalation option documented** → Flag as Medium. No escape hatch.

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Row-budget worksheet | Table of each retrieval element, filter, estimated max rows, running total |
| Refactor decision | Whether capping, async, or Apex boundary is chosen and why |
| Volume test plan | Full-copy sandbox scenarios with assertions |
| Production monitoring | FlowInterviewLog thresholds + alerts for row-count spikes |

## Related Skills

- **flow/flow-bulkification** — loop-safe query + DML patterns; use together for bulk-load scenarios.
- **flow/flow-runtime-error-diagnosis** — parse specific Flow fault messages and map to elements.
- **flow/fault-handling** — LDV failures need fault-routing explicitly.
- **flow/scheduled-flows** — when scheduled-trigger LDV is the concern.
- **data/bulk-api-and-large-data-loads** — for data pipeline volume outside Flow interviews.
- **apex/governor-limits** — shared-transaction concerns.
- **apex/batch-apex-patterns** — when the right escalation is Batch Apex.
