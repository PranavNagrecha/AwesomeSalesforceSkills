# Well-Architected Notes — Large Scale Deduplication

## Relevant Pillars

- **Reliability** — Duplicate records undermine the accuracy of reporting, attribution, and downstream processing. A reliable dedup strategy eliminates record fragmentation and ensures authoritative data is consistently retrievable. Survivorship rules are a reliability control: without them, merges feel arbitrary and erode user trust in the data model.
- **Operational Excellence** — Large-scale dedup is a repeatable operational capability, not a one-time project. The pattern must be automatable (batch jobs, scheduled scans), auditable (merge logs, error tracking), and recoverable (sandboxed testing, staged rollout). Ongoing duplicate prevention controls prevent accumulation of new dedup debt.
- **Performance** — Matching rule selectivity directly affects save performance on high-volume objects. Non-selective fuzzy matching rules add per-save query overhead. Index coverage on matching fields and restrictive filter logic are performance controls.
- **Scalability** — Apex `Database.merge()` does not scale beyond ~10K–50K pairs without careful batch engineering. For millions of records, the architecture must shift to external matching (Bulk API 2.0 extraction) and either third-party tools or orchestrated batch jobs with checkpoint/resume capability.

## Architectural Tradeoffs

**Apex batch vs. third-party tool:** Apex batch is zero-cost and sufficient for up to ~50K duplicate pairs on standard objects. It requires explicit governor limit management and does not provide a UI for business users to review merge queues. Third-party tools (DemandTools, Cloudingo) add licensing cost but provide UI-driven survivorship configuration, merge queues, audit logs, and parallel API throughput that Apex alone cannot match at volume.

**In-Salesforce matching vs. external matching:** Standard Duplicate Jobs and Matching Rules are convenient but cap out for retroactive large-scale work. External matching (via Bulk API 2.0 export + Python/SQL) can apply richer logic (fuzzy phonetic matching, composite scoring, address normalization) and handles any volume. The tradeoff is tooling complexity and the need to manage a data pipeline outside Salesforce.

**Merge now vs. merge incrementally:** Running all merges in a single large batch maximizes velocity but maximizes risk. An incremental approach — merging highest-confidence duplicate pairs first, then progressively lower-confidence pairs — reduces the blast radius of errors and allows business stakeholders to review edge cases before the next wave.

## Anti-Patterns

1. **One-shot bulk merge without survivorship rules** — Running thousands of merges where the "master" selection is arbitrary (e.g., always pick the record with the lower ID) destroys user trust. Users discover that the wrong company name, owner, or relationship survived. Always define and review survivorship criteria with the business owner before executing merges.

2. **Using standard Duplicate Jobs for retroactive million-record cleanup** — Duplicate Jobs are designed for ongoing hygiene sweeps on recently modified records. Using them as a retroactive dedup engine for millions of historical records results in incomplete processing and a false sense of completion. Use Bulk API 2.0 extraction + external matching for retroactive large-scale work.

3. **Merging without disabling automation** — Running a merge batch with all Flows and triggers active at volume causes cascading governor exceptions, unexpected downstream record creation/deletion, and potential data integrity problems. Automation bypass is a pre-condition for safe large-scale merge operations, not an optional step.

## Official Sources Used

- Apex Developer Guide — Database.merge() DML statement behavior, governor limits (10 merge calls per transaction), supported object types
- Bulk API 2.0 Developer Guide — query job creation, result retrieval, LDV extraction patterns
- Object Reference — Account, Contact, Lead merge semantics and related object re-parenting behavior
- Salesforce Well-Architected Overview — Reliability and Operational Excellence framing for data quality controls
- Salesforce Large Data Volumes Best Practices (knowledge/imports/salesforce-large-data-volumes-best-practices.md) — indexing, query selectivity, matching rule performance at scale
