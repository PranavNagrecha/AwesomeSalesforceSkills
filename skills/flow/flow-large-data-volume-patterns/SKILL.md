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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

Large data volume (LDV) problems in Flow usually show up as sudden production failures while sandbox tests look fine. The platform still applies the same transactional ceilings as Apex, including the total count of rows returned by SOQL across the whole transaction. A single `Get Records` element that asks for “all” matching rows can return up to the platform query-rows ceiling for that transaction; when related data grows, the same element crosses the line and the interview fails with a query-rows error. This skill focuses on those volume ceilings, how to cap and narrow retrieval, how collections participate in memory pressure, and when Flow should hand off to asynchronous or code-based processing. Pair it with `flow-bulkification` for loop and per-iteration query patterns.

## Before Starting

- Confirm **maximum rows** each `Get Records` could return in production (not just “a few” in a dev org).
- Identify **everything else** in the same transaction: other flows, Apex, validation, and duplicate rules all share one governor budget.
- Note whether the flow is **before-save or after-save**, **scheduled**, or **autolaunched from bulk paths**; each changes how often the expensive elements run.

## Core Concepts

### Total SOQL rows are aggregated per transaction

Salesforce counts rows returned by SOQL across the transaction toward a single query-rows limit. In Flow, each `Get Records` issues SOQL (unless the documented exception applies, such as certain metadata reads). Several modest queries that each return many rows can fail together even when no single query looks “large.” Volume planning must use **total rows returned**, not only query count.

### Unbounded “get all” retrieval is an LDV smell

Designs that retrieve “all” child or related rows for a parent without a tight filter, sort, and row cap assume the related set stays small. In LDV orgs that assumption breaks first. Prefer selective filters, ordering with a clear business rule, and an explicit maximum number of records to retrieve where the product supports it, so behavior stays predictable as data grows.

### Collections and interview data add memory pressure

Flows store intermediate collections in the interview’s working set. Very large collections increase the chance of heap-related failures and slow element execution even before hard limits. Shaping data early—fewer fields, fewer rows, pre-aggregation in a database-friendly layer—reduces risk.

### Flow is not the right engine for every LDV batch

When the requirement is to scan or update millions of rows on a schedule, platform batch patterns outside the interactive Flow interview (for example Batch Apex or an integration pipeline) are usually more appropriate. Flow can still coordinate a bounded unit of work, publish an event, or call invocable Apex that implements chunking.

## Common Patterns

### Cap and narrow `Get Records` before production data arrives

**When to use:** Related object cardinality is unknown or unbounded, or the flow only needs a bounded slice (for example latest N or first match by sort order).

**How it works:** Add selective filters and required fields only. Where available for your org version, use the Get Records option that retrieves all matching records **up to a specified limit** instead of relying on an implicit “retrieve everything” behavior. Combine with `Sort` when “top N” semantics matter.

**Why not the alternative:** Relying on small test data hides the failure until production volume crosses the query-rows threshold.

### One query, in-memory correlation, single write

**When to use:** Many triggering records need related data, but fan-out per parent is bounded or can be bounded.

**How it works:** Query once with a parent-centric filter (for example IDs from the triggering collection), build or filter collections in Assignment and Decision elements, then update in bulk after the loop. This pattern is detailed in `flow-bulkification`; here the emphasis is on **row count** of that single query staying under a budget you calculate up front.

**Why not the alternative:** Multiple wide queries or a wide query plus redundant follow-on queries multiplies returned rows against the same ceiling.

### Async handoff for unbounded work

**When to use:** The business process truly requires processing an unpredictable or large set that cannot be capped safely in Flow.

**How it works:** Keep the synchronous flow minimal: validate, stamp status, enqueue Platform Event, call Queueable or invocable Apex that chunks work, or invoke an integration designed for bulk. Document idempotency and retry behavior.

**Why not the alternative:** Stretching a record-triggered flow to do open-ended retrieval and per-row work fails unpredictably under load.

## Decision Guidance

| Situation | Recommended approach | Reason |
|-----------|----------------------|--------|
| Error mentions query rows near 50,000 | Audit every `Get Records` in the transaction path; add caps and filters | Total returned rows drive the failure |
| Related list can grow without bound | Do not model “load all children” in synchronous Flow | Unbounded retrieval is structurally unsafe |
| Need latest or first logical row | Sort + first record only, or cap with limit | Bounded semantics |
| Nightly millions-of-rows processing | Batch or integration outside Flow interview | Flow interviews are not bulk ETL engines |
| CMT or feature flags | Follow product docs for query cost | Some metadata reads are optimized; standard objects are not |

## Recommended Workflow

1. **Inventory retrieval** — List every `Get Records`, subflow, and invocable Apex in the path; estimate worst-case rows per element and the sum across the transaction.
2. **Read current limits** — Confirm Flow and transaction limits from Salesforce Help for your edition (see `references/well-architected.md`), especially query rows and DML rows, before changing design.
3. **Apply caps first** — Tighten filters, reduce selected fields, add sort and row cap options supported by your release; remove any “retrieve all” that is not strictly required.
4. **Align with bulkification** — Run `flow-bulkification` patterns so no loop multiplies queries or DML; recompute row totals after refactor.
5. **Test at volume** — Use realistic parent counts and related-list sizes (copy-based or integration test); assert the flow still completes when related tables are large.
6. **Escalate deliberately** — If caps break business requirements, document the gap and move processing to async Apex, orchestration, or an external system rather than expanding Flow scope.

## Review Checklist

- [ ] Each `Get Records` has a documented worst-case row count under production assumptions.
- [ ] No synchronous path depends on retrieving an unbounded “all related” set.
- [ ] Sort and “first record only” or explicit row limits match the business rule for “top” or “sample” data.
- [ ] Combined SOQL row usage for Flow plus other automation in the same transaction has headroom.
- [ ] Large scheduled or batch-style work is not implemented solely as a wide Flow on huge objects without chunking.
- [ ] Fault paths and monitoring exist for the high-volume scenario, not only single-record UI tests.

## Salesforce-Specific Gotchas

1. **Sandbox parity** — Small related sets in developer sandboxes do not exercise query-row limits; failures appear first in full-copy or production-like data.
2. **Shared transaction** — Imports and APIs can place many records in one transaction; a flow that was safe per user save can fail under bulk loading.
3. **Field set size** — Querying “all fields” or wide layouts increases heap pressure per row; retrieve only what the flow uses.

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Row-budget worksheet | Table of each retrieval element, filter, estimated max rows, and running total against the transaction limit |
| Refactor decision | Short note on whether capping, async, or Apex boundary is chosen and why |

## Related Skills

- **flow-bulkification** — Loop-safe query and DML patterns; use together for bulk load scenarios.
- **flow-runtime-error-diagnosis** — Parse specific Flow fault messages and map to elements.
- **data/bulk-api-and-large-data-loads** — For data pipeline volume outside Flow interviews.
