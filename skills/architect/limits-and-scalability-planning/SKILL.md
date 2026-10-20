---
name: limits-and-scalability-planning
description: "Use when planning a new org build for scale, auditing an existing org for governor limit exposure, or investigating a limit-related incident. Trigger phrases: 'org is hitting governor limits', 'how many custom objects can we have', 'will our data volume cause performance issues', 'batch job keeps failing with limit errors', 'planning for 10 million records', 'platform event throughput limits', 'SOQL limit exceeded in production'. NOT for one transaction's limits - use apex/governor-limits. NOT for tuning an individual SOQL query - use data/soql-query-optimization. NOT for Batch Apex authoring mechanics - use apex/batch-apex-patterns."
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

Use this skill when designing a new Salesforce implementation for scale, auditing an existing org for governor limit exposure before a major release, or troubleshooting a production incident caused by limit violations. This skill provides a structured approach to understanding, measuring, and planning around Salesforce's governor limit architecture. It does not cover individual code optimization techniques — for code-level CPU and heap tuning, use `apex-cpu-and-heap-optimization`.

---

## Before Starting

- **What execution context is relevant?** Synchronous user transactions, asynchronous jobs (Batch, Queueable, Future), or scheduled platform events all have different limit profiles.
- **What are the current record counts on key objects?** The query optimizer's index thresholds change at the first million records (Large Data Volumes Best Practices 264 L463, L468), so objects past 1 million need selectivity planning that smaller objects do not.
- **Is there an active incident or is this preventive planning?** Mode 1 (planning), Mode 2 (audit), and Mode 3 (troubleshoot) each have a different entry point.
- **What is the org edition?** Metadata allocations (custom objects, custom fields per object) differ by edition. UNVERIFIED (2026-10-20): the per-edition counts live in Salesforce Help "General Limits", which is not in the Winter '27 corpus; read the org's own figures before sizing.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which context runs each heavy job: trigger, Queueable, Future, or Batch `execute`?" | Async raises SOQL, CPU and heap but not the DML ceilings (Gotcha 3) | The limit column each inventory row in the template is scored against |
| "Is any of this work Scheduled Apex?" | Scheduled Apex is async but runs on the synchronous limits (Gotcha 3; Asynchronous Transaction Limits) | Rows sized against 100 SOQL / 10MB heap, or a plan to enqueue a Queueable from the scheduler |
| "What formulas, validation rules and package triggers fire on the busiest objects?" | All of it shares the one CPU budget, not just your Apex (Gotcha 1) | A CPU estimate taken from a profiled `CUMULATIVE_LIMIT_USAGE`, not from code review |
| "How many separate DML calls does the heaviest transaction make, and how many rows in total?" | Statements (150) and rows (10,000) fail independently (Gotcha 4) | Both counts in the inventory, with the closer one rated |
| "What is the largest single structure held in memory — a string, a JSON payload, a related-record graph?" | Heap fails at the peak, not the average (Gotcha 6) | A batch scope or chunk size derived from the peak, not the record count |
| "Do the sandboxes used for load testing keep the Summer '26 heap via `ApexSettings.enableEnforceSummer26ApexHeapLimit`?" | During Winter '27 a pinned sandbox reports 6MB / 12MB headroom while production has 10MB / 25MB (Gotcha 6) | A load-test result that is read against the right ceiling |
| "How many custom fields does each growing object hold, including ones deleted in the last 15 days?" | Deleted fields keep counting until hard delete (Gotcha 7; the 15-day window is UNVERIFIED (2026-10-20), Help-only) | Real field headroom before the next release adds fields |

Asking these before sizing turns a generic limits table into a plan scored against the context each job actually runs in, with the CPU and heap figures measured rather than assumed.

---

## Core Concepts

### How Governor Limits Work

Salesforce enforces governor limits per transaction to ensure fair resource sharing across all tenants on a shared infrastructure. Every Apex execution — whether triggered by a user action, a scheduled job, a platform event trigger, or an inbound API call — runs inside a transaction that has hard resource ceilings. When any ceiling is hit, the transaction fails immediately with a `System.LimitException`. There is no warning; the only prevention is design.

Limits are not shared across transactions. A Batch Apex job that processes 10,000 records in 10 batches of 1,000 gets a fresh governor limit reset for each batch execution (Apex Developer Guide 264 L19733). This is the fundamental reason Batch Apex exists: it provides a controlled way to work around single-transaction limits by chunking work.

### Synchronous Transaction Limits

These apply to all Apex executed in the context of a synchronous user action (button click, page load, inbound REST/SOAP call), to Scheduled Apex, and to platform event triggers, which run asynchronously but get the synchronous limits (Platform Events Developer Guide 264 L2339). Values from Apex Developer Guide 264 L19747–19782:

| Resource | Limit |
|---|---|
| SOQL queries | 100 per transaction |
| Records retrieved by SOQL | 50,000 per transaction |
| DML statements | 150 per transaction |
| DML rows | 10,000 per transaction |
| CPU time | 10,000ms (10 seconds) |
| Heap size | 10MB (Winter '27 release, not API-version-gated; 6MB through Summer '26) |
| Callouts (HTTP or web service) | 100 per transaction |
| Callout total timeout | 120 seconds |

### Asynchronous Transaction Limits

Future methods, Queueable Apex, and Batch Apex run under the asynchronous column. Scheduled Apex is asynchronous but runs on the synchronous limits (Apex Developer Guide 264 L19739). DML limits match synchronous code; SOQL, CPU and heap are higher (264 L19747, L19780):

| Resource | Limit |
|---|---|
| SOQL queries | 200 per transaction |
| DML statements | 150 per transaction |
| DML rows | 10,000 per transaction |
| CPU time | 60,000ms (60 seconds) |
| Heap size | 25MB (Winter '27 release, not API-version-gated; 12MB through Summer '26) |
| Callouts | 100 per transaction |

Heap rose at Winter '27 (Apex Developer Guide 264 L19780). During Winter '27 only, a nonproduction org can keep the Summer '26 heap via `ApexSettings.enableEnforceSummer26ApexHeapLimit` (Metadata API 264 L113855–113862), so confirm that setting before trusting a sandbox load test's heap headroom for production.

The expanded CPU limit (6x synchronous) is why callout-heavy or compute-heavy operations should be moved to `@future`, Queueable, or Batch Apex.

### Batch Apex Limits

Batch Apex (`Database.Batchable`) is the correct pattern for processing large data sets that exceed single-transaction limits. Key limits:

| Resource | Limit |
|---|---|
| Records a `Database.QueryLocator` can return, per job | 50 million; above that the job is terminated and marked Failed (Apex Developer Guide 264 L17902–17903, L20059) |
| Org-wide 24-hour rolling async budget | 250,000 or licenses × 200, whichever is greater, shared by Batch, Queueable, future and scheduled; every `start`, `execute` and `finish` call counts as one execution (264 L19936–19940, L20001–20003) |
| Batch jobs in queue or active simultaneously | 5 (264 L19985) |
| Minimum scope size | 1 record (scope must be greater than zero, 264 L17419) |
| Maximum scope size | 2,000 records for a QueryLocator start; a higher value is chunked to 2,000, and an iterable start has no upper bound (264 L17904–17907) |
| Default scope | 200 records (264 L17909–17910) |
| CPU time per batch execute() call | 60,000ms (async limit) |
| Heap per batch execute() call | 25MB (async limit; 12MB through Summer '26) |

There is no "records per 24 hours" cap on Batch Apex; the 24-hour ceiling is the async execution count. Batch Apex checks it up front: if the job needs more executions than remain, `Database.executeBatch` throws `AsyncApexExecutions Limit exceeded` and the job does not start (264 L17895–17899).

**Scope size tuning:** The default scope size when not specified in `Database.executeBatch()` is 200. Smaller scopes (50–100) reduce heap and CPU pressure per chunk at the cost of more `execute()` calls and more governor limit cycles. Larger scopes (1,000–2,000) maximize throughput but risk heap overflow if each record produces a large object graph. Tune scope size based on record complexity and the operations in `execute()`.

**Queue contention:** The limit of 5 active/queued batch jobs applies across all jobs in the org, and only one batch job's `start` method runs at a time (264 L17921). If multiple teams submit batch jobs simultaneously — data migrations, nightly rollups, integration sync jobs — they will queue behind each other. Plan batch job schedules to avoid collision. Apex Flex Queue (capacity: 100 jobs, 264 L19983) can hold additional jobs in `Holding` state before they enter the active queue.

### Org-Wide Metadata Limits

These apply to the entire org and do not reset per transaction. UNVERIFIED (2026-10-20): every value in this table except the Apex code row comes from Salesforce Help "General Limits", which is not in the Winter '27 corpus, and the package previously carried a conflicting custom-object figure (800 here, 200 EE / 2,000 UE in llm-anti-patterns.md Anti-Pattern 6). Treat the numbers as placeholders and read the org's edition allocation before scoring headroom.

| Resource | Limit (Enterprise/Unlimited) |
|---|---|
| Custom objects | 800 (UNVERIFIED, see above) |
| Custom fields per object | 500 (Enterprise), 800 (Unlimited/Performance) — shared across all field types |
| Relationship fields (lookup + master-detail) per object | 40 |
| Roll-up summary fields per object | 25 |
| Active flows (all types) | 4,000 |
| Custom tabs | 25 |
| Custom apps | 10 (Enterprise), unlimited (Unlimited) |
| Apex code, all classes and triggers in the org | 6 MB of code, excluding managed-package code and `@isTest` classes; raisable by support case (Apex Developer Guide 264 L20076, L20089–20091, L20095). The earlier "5,000 classes / 5,000 triggers" rows had no source and were removed. |

The 500 custom fields per object limit is a shared pool. Long text area fields, formula fields, and lookup fields all count toward the same 500. Orgs that model a single object (e.g., `Account`) as a multi-purpose record type with many field sets risk exhausting this limit. Review field usage regularly and archive or deprecate unused fields.

### Data Volume Planning

Data volume directly affects query performance, sharing recalculation, and storage. Plan around these thresholds:

**Query performance tiers (this skill's planning heuristic, not a Salesforce threshold):**
- Objects with fewer than 100,000 records: standard indexes cover most queries.
- Objects with 1–5 million records: selective queries with indexed filters perform well; non-selective queries begin to cause full table scans.
- Objects with 5+ million records: consider skinny tables for frequently queried field subsets. Salesforce Customer Support creates them; you cannot create or modify them yourself, they avoid the join between standard and custom field tables, and they hold at most 200 columns from a single object (Large Data Volumes Best Practices 264 L332–333, L339, L381–382).

**SOQL selectivity rules:** The query optimizer uses an index only when the filter matches a small enough share of the object (Large Data Volumes Best Practices 264 L463, L468):
- Standard index: the filter matches less than 30% of the first million records and less than 15% of additional records (2 million records → 450,000 or fewer).
- Custom index: less than 10% of the first million records and less than 5% of additional records (5 million records → 300,000 or fewer).
- AND: indexes are used unless one returns more than 20% of the records; OR: unless they all return more than 10%, and every OR field must be indexed (264 L476–479).
Non-selective queries bypass indexes and scan the full object table; a SOQL query that runs past 120 seconds cancels the transaction (Apex Developer Guide 264 L20051).

**Data skew — sharing recalculation:** When a single user or a small set of users owns a disproportionate number of records (avoid any user owning more than 10,000 records, Large Data Volumes Best Practices 264 L1033; likewise no parent with more than 10,000 children, L1052), sharing recalculation after ownership changes becomes slow and can lock the org for extended periods. Common causes: integration users who own all imported records, queue-based ownership without ownership reassignment, single admin owning all accounts. Mitigation: distribute ownership, use public read/write sharing where data sensitivity allows, or use territory management.

### Platform Event Limits

Default allocations without an add-on (Platform Events Developer Guide 264):

| Resource | Limit |
|---|---|
| Event publishing, per rolling hour | 250,000 (Performance/Unlimited and Enterprise), 50,000 (Developer) (L7141) |
| Event delivery to API subscribers (Pub/Sub API, CometD, empApi, event relays), per rolling 24 hours, summed across subscribers | 50,000 (Performance/Unlimited), 25,000 (Enterprise and Professional with API add-on), 10,000 (Developer) (L7071) |
| Add-on license | +100,000 deliveries per day and +25,000 publishes per hour per add-on (L7231–7233) |
| Maximum event message size | 1MB (L7000) |
| Event retention | 72 hours for high-volume events; 24 hours for legacy standard-volume (L291–292) |
| Platform event trigger batch | up to 2,000 events per execution, versus 200 for an object trigger (L3098–3099) |

Deliveries to Apex triggers, flows and processes do not count against the delivery allocation (L7039–7041), so the delivery figure sizes external subscribers only. A single external client receiving one event per second takes 86,400 deliveries a day, past every default delivery allocation within the day. Batch or aggregate events where possible, and read usage from the REST limits resource (`HourlyPublishedPlatformEvents`, `DailyDeliveredPlatformEvents`, REST API Developer Guide 264 L8030, L8047).

### Storage Limits

UNVERIFIED (2026-10-20): the storage allocation table below is from Salesforce Help, which is not in the Winter '27 corpus; read the org's actual allocation from the REST limits resource (`DataStorageMB`, `FileStorageMB`, which need Manage Users — REST API Developer Guide 264 L8191–8193) before projecting.

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

Calculate data storage: estimated records × average record size (roughly 2KB per standard record, more for objects with many long text fields — UNVERIFIED (2026-10-20): the 2KB figure is Help-only, not in the corpus). Add file storage for attachments, content versions, and emails. If projected storage exceeds 80% of allocated within 2 years, include an archival strategy in the design (Big Objects for cold archival, data export + deletion for compliance retention, or a Salesforce Shield archive strategy).

### Step 5 — Check Metadata Headroom

Count existing custom objects, fields per object, and active flows. Calculate headroom against org limits. Flag any object approaching 400 custom fields (80% of the 500 limit; the 500 itself is UNVERIFIED, see Org-Wide Metadata Limits) for a field audit before adding new fields.

Count deleted-but-not-yet-purged fields in that total. Setup > Object Manager > *object* > Fields & Relationships > Deleted Fields lists them; each one still consumes its slot in the 500/800 pool — and in the 40-relationship or 25-roll-up pool for its type — until the hard-delete process completes, which is up to 15 days after the delete (UNVERIFIED (2026-10-20): the soft-delete behaviour and 15-day window are Help-only; see Gotcha 7). If the plan's remediation for a near-full object is "delete unused fields," schedule it 15 days ahead of the release that needs the headroom, or plan to Erase and Purge.

---

## Mode 2: Audit an Existing Org for Limit Risk

Use this mode when reviewing an org before a major release, after an acquisition, or during a health check engagement.

### Audit Checklist

**Governor limit exposure:**
- [ ] Review Apex debug logs for `LIMIT_USAGE_FOR_NS` entries — look for transactions consuming more than 70% of any governor limit.
- [ ] Check for SOQL queries in loops — any `[SELECT ...]` inside a `for` loop is an immediate risk.
- [ ] Review Batch Apex scope sizes — any job with scope > 500 should be validated against heap usage.
- [ ] Check for synchronous callouts in triggers — callouts from before/after triggers run in the same user transaction; slow external systems extend CPU time.
- [ ] Verify that future method chains do not exist — `@future` methods cannot call other `@future` methods (the future-method allowance is 0 in batch and future contexts, Apex Developer Guide 264 L19771). This is a hard runtime error.

**Org-wide metadata headroom** (flag at 87.5% of the edition's allocation; the allocations themselves are UNVERIFIED, see Org-Wide Metadata Limits):
- [ ] Custom objects used vs. the edition limit (800 in this package's table) — flag anything above 87.5%.
- [ ] Custom fields per object — review any object above 400 fields.
- [ ] Active flows — flag anything above 87.5% of the active-flow allocation (4,000 in this package's table).

**Data volume risks:**
- [ ] Identify objects with more than 1 million records using record counts in Setup > Storage Usage.
- [ ] Review sharing model on large-volume objects — private sharing on an object with 10M records and complex role hierarchy is a recalculation risk.
- [ ] Check for data skew — any owner with more than 10,000 records on a private-sharing object.

**Platform event throughput:**
- [ ] Read `HourlyPublishedPlatformEvents` and `DailyDeliveredPlatformEvents` from the REST limits resource — compare publishing against the hourly allocation (250,000 EE/UE) and external-subscriber deliveries against the 24-hour allocation (25,000 EE, 50,000 UE) (Platform Events Developer Guide 264 L7071, L7141).
- [ ] Identify any event subscriber triggers that perform high-SOQL or high-DML operations — platform event triggers get the synchronous limits (100 SOQL), not the async column (Platform Events Developer Guide 264 L2339), and receive up to 2,000 events per batch (L3098).

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
| `Too many SOQL queries: 101` | SOQL inside a loop, or SOQL from a non-certified package, which shares the org's quota (certified managed packages get their own 100, Apex Developer Guide 264 L19880, L19891–19892) | Debug log — filter for `SOQL_EXECUTE_BEGIN` entries; check for loops |
| `Too many DML statements: 151` | DML inside a loop, or multiple DML across too many object types | Debug log — filter for `DML_BEGIN` entries |
| `CPU time limit exceeded` | Complex formulas, large collection iteration, string operations, or unindexed sort in Apex | Debug log — check `CUMULATIVE_LIMIT_USAGE` for CPU line; profile with System.currentTimeMillis() checkpoints |
| `Heap size too large` | Large SOQL result set held in memory, deeply nested object graphs, or string concatenation in a loop | Reduce SELECT fields, process in chunks, use aggregateResult instead of record collections |
| `Batch job stuck in queue` | 5-job active/queued limit reached | Check Apex Jobs in Setup; cancel or complete queued jobs before submitting new ones |
| `AsyncApexExecutions Limit exceeded` on `executeBatch` | The job needs more `start`/`execute`/`finish` executions than remain in the 24-hour async budget; Batch Apex checks before starting (Apex Developer Guide 264 L17895–17899) | Read `DailyAsyncApexExecutions` from the REST limits resource; raise scope or reschedule. A scope above 2,000 on a QueryLocator start is not an error — it is chunked to 2,000 (264 L17904–17906) |
| `Callout loop` | Future methods chained, or a trigger fires on an object updated by a callout response | Review async method chain; use Platform Events to decouple |
| `Query took too long` | Non-selective SOQL on a large object (full table scan) | Add indexed WHERE clauses; check SOQL selectivity thresholds |
| `Record lock timeout` | DML on the same records from concurrent transactions | Reduce batch scope to limit the number of records locked simultaneously; stagger concurrent jobs |
| Platform events dropping | External-subscriber delivery allocation exceeded (`403::Organization total events daily limit exceeded`) or hourly publishing allocation exceeded (`LIMIT_EXCEEDED`) (Platform Events Developer Guide 264 L7440, L7471) | Read `DailyDeliveredPlatformEvents` / `HourlyPublishedPlatformEvents`; throttle or aggregate emission |

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
| Skinny tables | Read-heavy queries on objects > 5M records (heuristic) | Requires Salesforce Customer Support; max 200 columns, single object; not copied to non-Full sandboxes (Large Data Volumes Best Practices 264 L332, L381–384) |
| Big Objects | Historical archival, cold storage | Async SOQL only; no standard DML; designed for write-once-read-rarely patterns |
| Platform Events for decoupling | Callouts, downstream processing, cross-org messaging | Monitor the hourly publishing (250,000 EE/UE) and 24-hour external delivery (25,000 EE / 50,000 UE) allocations; do not use as a high-frequency message bus to external clients without the add-on |
| Field audit before adding fields | Object approaching 400 custom fields | Unused fields still count against the 500 limit — and so do deleted ones, until hard delete completes (up to 15 days; UNVERIFIED (2026-10-20), Help-only) |

---

## Related Skills

- `apex/batch-apex-patterns` — for Batch Apex authoring patterns and trigger mechanics
- `apex/async-apex` — for Queueable, Future, and scheduling patterns
- `apex/apex-cpu-and-heap-optimization` — for code-level CPU and heap tuning (NOT this skill)
- `architect/large-data-volume-architecture` — for LDV indexing, skinny tables, and archival strategies
- `architect/solution-design-patterns` — for automation layer selection

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Pick the mode (Plan for Scale, Audit, or Troubleshoot) and answer the Questions table above, recording each job's execution context.
2. Copy `templates/limits-and-scalability-planning-template.md` and fill one inventory row per synchronous path, async job and batch, scoring each against its own column (Scheduled Apex on the synchronous one).
3. Replace estimated CPU and heap with figures read from a representative debug log's `CUMULATIVE_LIMIT_USAGE` block, and note whether the test org pins the Summer '26 heap.
4. Run `python3 scripts/check_limits_plan.py --file <your-plan.md> --strict` and close every MISSING required check and every stale-heap WARN (a 6 MB / 12 MB heap figure not labelled Summer '26).
5. Record each High or Critical row with its mitigation (smaller scope, async offload, field-list reduction) and the follow-up skill from Related Skills.

---

