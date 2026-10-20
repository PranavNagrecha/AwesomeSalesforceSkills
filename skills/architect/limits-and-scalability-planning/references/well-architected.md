# Well-Architected Alignment — limits-and-scalability-planning

## Pillar: Scalability

Governor limits are the primary mechanism Salesforce uses to enforce scalability on a multi-tenant platform. A well-architected org treats limits not as obstacles but as design constraints that force good architecture decisions: bulkification, async offloading, selective queries, and data ownership distribution.

**Scalability patterns this skill enforces:**
- Batch Apex for large data set operations — limits force chunking, which is inherently scalable.
- SOQL selectivity — queries that use indexed filters scale with data volume; full table scans do not.
- Async offloading — moving non-user-facing work out of synchronous transactions allows the user experience to scale independently of back-end processing time.
- Org metadata headroom management — staying below 80% of metadata limits ensures the org can accommodate future growth without a governance emergency.

**Anti-patterns this skill catches:**
- SOQL inside loops — does not scale; O(n) queries cause limit failure at moderate record volumes.
- DML inside loops — same problem; fails when the loop body repeats more than 150 times (150 DML statements, Apex Developer Guide 264 L19757).
- Hard-coded selectivity assumptions — queries that are selective at 10,000 records become non-selective at 1,000,000 records; design for projected volume, not current volume.

---

## Pillar: Performance

Governor limits intersect directly with user-perceived performance. A transaction that consumes 9,500ms of CPU is 9.5 seconds of wait time for the user before the page responds. A non-selective SOQL query on a large object can run until Salesforce cancels the transaction at the 120-second SOQL run-time ceiling (Apex Developer Guide 264 L20051).

**Performance guidance this skill provides:**
- Skinny table consideration for objects > 5M records — reduces query I/O significantly for frequently queried field subsets.
- Data skew identification — sharing recalculation delays that manifest as slow record saves are caused by skewed ownership, not code bugs.
- Heap reduction strategies — reducing SELECT field lists and chunking data processing reduces peak heap and avoids the GC overhead that inflates CPU time.

---

## Pillar: Reliability

Limit violations cause immediate transaction failures with no graceful degradation. A production `LimitException` means the user action failed, the record was not saved, and the integration message was not delivered. Reliability in a Salesforce context means designing ahead of limit risk so that failures are caught in testing rather than production.

**Reliability practices this skill mandates:**
- Full-volume sandbox testing — limit risks that are invisible at 1,000 records become failures at 1,000,000. Test in a sandbox seeded with production-scale data.
- Debug log checkpoints — `System.debug(Limits.getQueries())` instrumentation in high-risk transactions gives early warning before limits are reached.
- Batch job queue planning — ensuring the 5-job limit is not saturated during peak periods prevents jobs from failing to start.
- Platform event monitoring — tracking hourly publishing (250,000 EE/UE) and 24-hour external delivery (25,000 EE / 50,000 UE) consumption prevents dropped events that create data inconsistency (Platform Events Developer Guide 264 L7071, L7141).

---

## Pillar: Operational Excellence

Scalability planning is an ongoing operational practice, not a one-time design activity. Limits change across Salesforce releases, data volumes grow, new packages add resource consumption, and new teams add automation without awareness of existing overhead.

**Operational practices this skill recommends:**
- Regular storage audits (quarterly minimum) using Setup > Storage Usage.
- Metadata limit reviews before each major release — custom object and field headroom as part of the release checklist.
- Apex Jobs monitoring for batch queue saturation during peak business periods.
- Governance policies for new custom object and new custom field requests above threshold counts.
- Limit consumption documentation in deployment runbooks for batch-heavy releases.

---

## Official Sources Used

Winter '27 (release 264, API 68.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text.

- Apex Developer Guide 264 — per-transaction limits: 100/200 SOQL, 150 DML statements, 10,000 DML rows, 10,000/60,000 ms CPU, 10 MB / 25 MB heap, 100 callouts, 120 s callout timeout (L19747–19782); Scheduled Apex runs on synchronous limits (L19739)
- Apex Developer Guide 264 — certified managed packages get their own per-transaction limits, including their own 100 SOQL; non-certified packages share the org's; heap, CPU and transaction time are not separated (L19873–19880, L19891–19892, L19920–19924)
- Apex Developer Guide 264 — Batch Apex: 50 million QueryLocator rows per job (L17902–17903, L20059); scope max 2,000 for QueryLocator and default 200 (L17904–17910); preemptive async-capacity check (L17895–17899); 250,000-or-licenses×200 daily async executions counting start/execute/finish (L19936–19940, L20001–20002); 5 queued/active jobs, 100 flex-queue jobs (L19983, L19985); 6 MB org Apex code (L20076)
- Salesforce Developer Limits and Allocations Quick Reference 264 — Bulk API batch allocation of 15,000 batches per rolling 24 hours, shared by Bulk API and Bulk API 2.0 (L300–302); 150,000,000 ingest records per 24 h (L348); 10 MB per batch / 150 MB per Bulk API 2.0 job (L391)
- Platform Events Developer Guide 264 — publishing 250,000/hour EE/UE (L7141); delivery 50,000 UE / 25,000 EE / 10,000 DE per 24 h (L7071); Apex/flow subscribers excluded from delivery (L7039–7041); 1 MB message (L7000); 72 h retention (L291); add-on increments (L7231–7233); triggers run on synchronous limits with batches up to 2,000 (L2339, L3098)
- Large Data Volumes Best Practices 264 — index selectivity thresholds (L463, L468, L476–479); skinny tables via Customer Support, 200 columns (L332, L381); no owner over 10,000 records, no parent over 10,000 children (L1033, L1052)
- REST API Developer Guide 264 — limits resource keys `DailyAsyncApexExecutions`, `HourlyPublishedPlatformEvents`, `DailyDeliveredPlatformEvents`, `DataStorageMB`, `FileStorageMB`, and no custom-object key (L7923–8222)
- Metadata API Developer Guide 264 — `ApexSettings.enableEnforceSummer26ApexHeapLimit`, Winter '27-only nonproduction heap opt-out (L113855–113862)
- Not in the corpus (those claims carry inline dated markers in the package): Salesforce Help "General Limits" (custom objects, fields, tabs, apps, flows, storage) and the field-deletion topics (15-day soft delete, Purge at 75%)
- Salesforce Well-Architected Overview — quality model framing for Scalability, Performance, Reliability, and Operational Excellence pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
