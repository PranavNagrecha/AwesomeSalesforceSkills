---
name: limits-and-scalability-planning
description: "Use when planning a new org build for scale, auditing an existing org for governor limit exposure, or investigating a limit-related incident. Trigger phrases: 'org is hitting governor limits', 'how many custom objects can we have', 'will our data volume cause performance issues', 'batch job keeps failing with limit errors', 'planning for 10 million records', 'platform event throughput limits', 'SOQL limit exceeded in production'. NOT for code-level optimization (use apex-cpu-and-heap-optimization), NOT for individual SOQL query tuning (use apex/soql-optimization), NOT for Batch Apex authoring mechanics (use apex/batch-apex)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
  - Reliability
  - Operational Excellence
tags:
  - governor-limits
  - scalability
  - data-volume
  - batch-apex
  - platform-events
  - soql-selectivity
  - storage-limits
  - async-apex
  - architecture-planning
  - org-limits
  - cpu-limits
  - heap-limits
  - dml-limits
  - sharing-recalculation
triggers:
  - "our org is hitting governor limits in production and we need to understand the risk"
  - "we are planning a new data model with high record volumes — what limits do we need to design around"
  - "batch job keeps failing because of limit errors mid-execution"
  - "how close are we to the org-wide custom object limit"
  - "platform event delivery is dropping messages at high throughput"
  - "planning a mass data migration involving millions of records"
  - "our SOQL queries are causing full table scans on large objects"
inputs:
  - "Current or projected record counts per key object"
  - "Transaction patterns: synchronous user actions, async background jobs, integrations"
  - "Async processing approach: Batch Apex, Queueable, Future, Platform Events"
  - "Existing org metadata counts: custom objects, fields, active flows"
  - "Integration callout requirements and throughput expectations"
  - "Data sharing model: private vs. public, sharing rules, role hierarchy depth"
  - "Storage usage: current data storage and file storage consumption"
outputs:
  - "Governor limit risk assessment per transaction category (sync, async, batch)"
  - "Org-wide metadata limit headroom analysis"
  - "Data volume risk flags and remediation strategies"
  - "Async offloading recommendations"
  - "SOQL selectivity review checklist"
  - "Platform event throughput sizing"
  - "Storage capacity projection"
  - "Filled limits-and-scalability-planning-template.md"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when designing a new Salesforce implementation for scale, auditing an existing org for governor limit exposure before a major release, or troubleshooting a production incident caused by limit violations. This skill provides a structured approach to understanding, measuring, and planning around Salesforce's governor limit architecture. It does not cover individual code optimization techniques — for code-level CPU and heap tuning, use `apex-cpu-and-heap-optimization`.

---

## Before Starting

- **What execution context is relevant?** Synchronous user transactions, asynchronous jobs (Batch, Queueable, Future), or scheduled platform events all have different limit profiles.
- **What are the current record counts on key objects?** Objects with more than 1 million records require different query and DML strategies than smaller objects.
- **Is there an active incident or is this preventive planning?** Mode 1 (planning), Mode 2 (audit), and Mode 3 (troubleshoot) each have a different entry point.
- **What is the org edition?** Enterprise and Unlimited Edition orgs have higher metadata limits (800 custom objects) than Professional Edition orgs.

---

## Core Concepts

### How Governor Limits Work

Salesforce enforces governor limits per transaction to ensure fair resource sharing across all tenants on a shared infrastructure. Every Apex execution — whether triggered by a user action, a scheduled job, a platform event trigger, or an inbound API call — runs inside a transaction that has hard resource ceilings. When any ceiling is hit, the transaction fails immediately with a `System.LimitException`. There is no warning; the only prevention is design.

Limits are not shared across transactions. A Batch Apex job that processes 10,000 records in 10 batches of 1,000 gets a fresh governor limit reset for each batch execution. This is the fundamental reason Batch Apex exists: it provides a controlled way to work around single-transaction limits by chunking work.

### Synchronous Transaction Limits

These apply to all Apex executed in the context of a synchronous user action (button click, page load, inbound REST/SOAP call, platform event trigger in synchronous mode):

| Resource | Limit |
|---|---|
| SOQL queries | 100 per transaction |
| DML statements | 150 per transaction |
| DML rows | 10,000 per transaction |
| CPU time | 10,000ms (10 seconds) |
| Heap size | 6MB |
| Callouts (HTTP or web service) | 100 per transaction |
| Callout total timeout | 120 seconds |
| Records locked simultaneously | 10 |

### Asynchronous Transaction Limits

Future methods, Queueable Apex, and scheduled Apex run asynchronously. They receive the same SOQL and DML limits as synchronous code, but CPU and heap are higher:

| Resource | Limit |
|---|---|
| SOQL queries | 100 per transaction |
| DML statements | 150 per transaction |
| DML rows | 10,000 per transaction |
| CPU time | 60,000ms (60 seconds) |
| Heap size | 12MB |
| Callouts | 100 per transaction |

The expanded CPU limit (6x synchronous) is why callout-heavy or compute-heavy operations should be moved to `@future`, Queueable, or Batch Apex.

### Batch Apex Limits

Batch Apex (`Database.Batchable`) is the correct pattern for processing large data sets that exceed single-transaction limits. Key limits:

| Resource | Limit |
|---|---|
| Records processed per 24-hour rolling window | 50,000,000 (50 million) |
| Batch jobs in queue or active simultaneously | 5 |
| Minimum scope size | 1 record |
| Maximum scope size | 2,000 records |
| Recommended scope for most workloads | 200 records |
| CPU time per batch execute() call | 60,000ms (async limit) |
| Heap per batch execute() call | 12MB (async limit) |

**Scope size tuning:** The default scope size when not specified in `Database.executeBatch()` is 200. Smaller scopes (50–100) reduce heap and CPU pressure per chunk at the cost of more `execute()` calls and more governor limit cycles. Larger scopes (1,000–2,000) maximize throughput but risk heap overflow if each record produces a large object graph. Tune scope size based on record complexity and the operations in `execute()`.

**Queue contention:** The limit of 5 active/queued batch jobs applies across all jobs in the org. If multiple teams submit batch jobs simultaneously — data migrations, nightly rollups, integration sync jobs — they will queue behind each other. Plan batch job schedules to avoid collision. Apex Flex Queue (capacity: 100 jobs) can hold additional jobs in `Holding` state before they enter the active queue.

### Org-Wide Metadata Limits

These apply to the entire org and do not reset per transaction:

| Resource | Limit (Enterprise/Unlimited) |
|---|---|
| Custom objects | 800 |
| Custom fields per object | 500 (shared across all field types) |
| Active flows (all types) | 4,000 |
| Custom tabs | 25 |
| Custom apps | 10 (Enterprise), unlimited (Unlimited) |
| Apex classes | 5,000 |
| Apex triggers | 5,000 |

The 500 custom fields per object limit is a shared pool. Long text area fields, formula fields, and lookup fields all count toward the same 500. Orgs that model a single object (e.g., `Account`) as a multi-purpose record type with many field sets risk exhausting this limit. Review field usage regularly and archive or deprecate unused fields.

### Data Volume Planning

Data volume directly affects query performance, sharing recalculation, and storage. Plan around these thresholds:

**Query performance thresholds:**
- Objects with fewer than 100,000 records: standard indexes cover most queries.
- Objects with 1–5 million records: selective queries with indexed filters perform well; non-selective queries begin to cause full table scans.
- Objects with 5+ million records: consider skinny tables (contact Salesforce support to create) for frequently queried field subsets. Skinny tables are internal read-optimized copies of selected fields and eliminate the need for the query engine to join to the main record table.

**SOQL selectivity rules:** A query is selective when it uses indexed fields and the result set is a small fraction of total records. The selectivity thresholds that Salesforce uses internally:
- For objects with fewer than 333,333 records: result set must be fewer than 10% of total records.
- For objects with 333,333–1,000,000 records: result set must be fewer than 33,333 records.
- For objects with more than 1,000,000 records: result set must be fewer than 333,000 records, or fewer than 10% — whichever is smaller.
Non-selective queries bypass indexes and scan the full object table. On large objects this causes CPU timeout and "query took too long" errors.

**Data skew — sharing recalculation:** When a single user or a small set of users owns a disproportionate number of records (more than 10,000 records per owner is the threshold for skew concern), sharing recalculation after ownership changes becomes slow and can lock the org for extended periods. Common causes: integration users who own all imported records, queue-based ownership without ownership reassignment, single admin owning all accounts. Mitigation: distribute ownership, use public read/write sharing where data sensitivity allows, or use territory management.

### Platform Event Limits

| Resource | Limit |
|---|---|
| Event deliveries per 24-hour rolling window | 250,000 (standard orgs) |
| Event deliveries per 24-hour rolling window | 500,000 (high-volume add-on) |
| Maximum event message size | 1MB |
| Stored events (replay) | 3 days |
| Event bus throughput | dependent on org type and event volume |

Platform events are not a substitute for high-frequency streaming. At 250,000 deliveries per 24 hours, a single integration sending events every second hits the limit in roughly 70 hours of sustained operation. Batch or aggregate events where possible, and monitor usage against the limit in Setup > Platform Events.

### Storage Limits

| Resource | Base | Per-License Add |
|---|---|---|
| Data storage (Enterprise) | 1GB | 20MB per user license |
| File storage (Enterprise) | 1GB | 2GB per user license |
| Data storage (Unlimited) | 1GB | 120MB per user license |

Data storage counts every record in every standard and custom object, plus chatter activity, email logs, and archived records. File storage counts attachments, files, documents, and Content records. When either limit is approached, record creation fails. Monitor storage in Setup > Storage Usage and plan archival or deletion strategies before limits are reached.

---

## Mode 1: Plan for Scale (New Build)

Use this mode when designing a new org, new feature, or new integration before development begins.

### Step 1 — Build the Governor Limit Inventory

For each planned transaction type (user action, trigger, integration event, batch job), document:

1. **SOQL count:** How many queries are needed? Include queries from helper methods, triggers on related objects, and validation rules that use formula fields backed by SOQL.
2. **DML count:** How many DML statements and rows per transaction? Each `insert`, `update`, `delete`, `upsert` on a different SObject type is one DML statement.
3. **CPU budget:** Estimate CPU usage. Complex formula field evaluation, large collection iterations, and string manipulation all consume CPU. If callouts are involved, they consume CPU during response parsing.
4. **Heap budget:** Estimate peak heap. Large SOQL result sets, deep object graphs, and string concatenation in loops are common heap killers.

### Step 2 — Identify Async Offload Candidates

Move any of the following to async execution:
- Operations that do not need to complete before the user sees a response
- Callouts that are not required in the same transaction as a record save
- Rollup calculations over large related lists
- Cross-object field sync that touches more than 200 records
- Integration payloads that require transformation and outbound delivery

### Step 3 — Plan Data Volume Milestones

Project record growth for key objects at 1-year, 3-year, and 5-year intervals. Flag any object projected to exceed 1 million records and design queries to use indexed fields from day one. Large volume objects need:
- A selective WHERE clause using indexed fields on every query
- No SELECT * in Apex — select only the fields needed
- Skinny table consideration when 5 million records is in scope within 3 years

### Step 4 — Plan Storage

Calculate data storage: estimated records × average record size (roughly 2KB per standard record, more for objects with many long text fields). Add file storage for attachments, content versions, and emails. If projected storage exceeds 80% of allocated within 2 years, include an archival strategy in the design (Big Objects for cold archival, data export + deletion for compliance retention, or a Salesforce Shield archive strategy).

### Step 5 — Check Metadata Headroom

Count existing custom objects, fields per object, and active flows. Calculate headroom against org limits. Flag any object approaching 400 custom fields (80% of the 500 limit) for a field audit before adding new fields.

---

## Mode 2: Audit an Existing Org for Limit Risk

Use this mode when reviewing an org before a major release, after an acquisition, or during a health check engagement.

### Audit Checklist

**Governor limit exposure:**
- [ ] Review Apex debug logs for `LIMIT_USAGE_FOR_NS` entries — look for transactions consuming more than 70% of any governor limit.
- [ ] Check for SOQL queries in loops — any `[SELECT ...]` inside a `for` loop is an immediate risk.
- [ ] Review Batch Apex scope sizes — any job with scope > 500 should be validated against heap usage.
- [ ] Check for synchronous callouts in triggers — callouts from before/after triggers run in the same user transaction; slow external systems extend CPU time.
- [ ] Verify that future method chains do not exist — `@future` methods cannot call other `@future` methods. This is a hard runtime error.

**Org-wide metadata headroom:**
- [ ] Custom objects used vs. 800 limit — flag anything above 700 (87.5%).
- [ ] Custom fields per object — review any object above 400 fields.
- [ ] Active flows — flag anything above 3,500 active flows (87.5% of 4,000).

**Data volume risks:**
- [ ] Identify objects with more than 1 million records using record counts in Setup > Storage Usage.
- [ ] Review sharing model on large-volume objects — private sharing on an object with 10M records and complex role hierarchy is a recalculation risk.
- [ ] Check for data skew — any owner with more than 10,000 records on a private-sharing object.

**Platform event throughput:**
- [ ] Review platform event usage in Setup > Platform Events — check the 24-hour delivery count against the 250,000 limit.
- [ ] Identify any event subscriber triggers that perform high-SOQL or high-DML operations — they share the same governor limits as other async Apex.

**Storage:**
- [ ] Check current data and file storage consumption in Setup > Storage Usage.
- [ ] Identify the top storage consumers — which objects hold the most records? Which users have the most file storage?

### Risk Rating Model

| Risk Level | Criteria |
|---|---|
| Critical | Any governor limit at > 90% in a production transaction, or metadata count > 90% of org limit |
| High | Any governor limit at 70–90% in production, or data volume > 5M on an object with non-selective queries |
| Medium | Limits at 50–70% of ceiling, or objects projected to hit thresholds within 12 months |
| Low | Below 50% with no projected breach within 24 months |

---

## Mode 3: Troubleshoot a Limit-Related Incident

Use this mode when a production incident involves `System.LimitException`, timeout errors, or unexpected job failures.

### Diagnostic Table

| Symptom | Most Likely Cause | Where to Investigate |
|---|---|---|
| `Too many SOQL queries: 101` | SOQL inside a loop, or SOQL from managed packages consuming shared quota | Debug log — filter for `SOQL_EXECUTE_BEGIN` entries; check for loops |
| `Too many DML statements: 151` | DML inside a loop, or multiple DML across too many object types | Debug log — filter for `DML_BEGIN` entries |
| `CPU time limit exceeded` | Complex formulas, large collection iteration, string operations, or unindexed sort in Apex | Debug log — check `CUMULATIVE_LIMIT_USAGE` for CPU line; profile with System.currentTimeMillis() checkpoints |
| `Heap size too large` | Large SOQL result set held in memory, deeply nested object graphs, or string concatenation in a loop | Reduce SELECT fields, process in chunks, use aggregateResult instead of record collections |
| `Batch job stuck in queue` | 5-job active/queued limit reached | Check Apex Jobs in Setup; cancel or complete queued jobs before submitting new ones |
| `Maximum batch size exceeded` | scope argument to executeBatch() is > 2,000 | Reduce scope; default to 200 |
| `Callout loop` | Future methods chained, or a trigger fires on an object updated by a callout response | Review async method chain; use Platform Events to decouple |
| `Query took too long` | Non-selective SOQL on a large object (full table scan) | Add indexed WHERE clauses; check SOQL selectivity thresholds |
| `Record lock timeout` | DML on the same records from concurrent transactions | Reduce batch scope to limit the number of records locked simultaneously; stagger concurrent jobs |
| Platform events dropping | 250,000/24hr delivery limit exceeded | Check Setup > Platform Events delivery metrics; throttle event emission rate |

### Limit Incident Response Steps

1. **Capture a debug log** at FINEST level from the failing user or job. Look for `LIMIT_USAGE_FOR_NS` entries at the end — this shows the exact limits consumed when the failure occurred.
2. **Identify the worst-offending limit** — the one closest to its ceiling.
3. **Trace the caller** — which method, trigger, or flow caused the limit spike?
4. **Apply the shortest-path fix first** — if SOQL is in a loop, extract it. If heap is too large, reduce the SELECT field list or chunk the data set.
5. **Validate the fix in a full-volume sandbox** — limit errors that only occur at scale cannot be reliably caught in developer orgs with small data sets.
6. **Add monitoring** — insert `System.debug(Limits.getQueries() + ' / ' + Limits.getLimitQueries())` checkpoints in high-risk transactions to catch future creep before it becomes an incident.

---

## Planning Strategies Reference

| Strategy | When to Use | Key Consideration |
|---|---|---|
| Async offloading | Any non-user-facing operation that does not need same-transaction result | Use `@future`, Queueable, or Batch based on complexity and chaining needs |
| Chunking via Batch Apex | Processing > 10,000 records per business operation | Tune scope for heap budget; schedule to avoid queue congestion |
| Custom Settings for bypass flags | Feature flags, bypass logic for data migrations | Custom Settings are cached after first access; no SOQL cost after first read |
| Hierarchical rollup patterns | Parent aggregations over many child records | Use Platform Events + Batch rollup rather than trigger-time rollup on millions of children |
| Skinny tables | Read-heavy queries on objects > 5M records | Requires Salesforce support case; significant read performance gain |
| Big Objects | Historical archival, cold storage | Async SOQL only; no standard DML; designed for write-once-read-rarely patterns |
| Platform Events for decoupling | Callouts, downstream processing, cross-org messaging | Monitor 250K/24hr delivery ceiling; do not use as a high-frequency message bus without the add-on |
| Field audit before adding fields | Object approaching 400 custom fields | Unused fields still count against the 500 limit; deprecate and delete rather than accumulate |

---

## Related Skills

- `apex/batch-apex` — for Batch Apex authoring patterns and trigger mechanics
- `apex/async-patterns` — for Queueable, Future, and scheduling patterns
- `apex-cpu-and-heap-optimization` — for code-level CPU and heap tuning (NOT this skill)
- `data/large-data-volumes` — for LDV indexing, skinny tables, and archival strategies
- `architect/solution-design-patterns` — for automation layer selection

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

