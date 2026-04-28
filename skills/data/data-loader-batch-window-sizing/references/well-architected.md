# Well-Architected Notes — Data Loader Batch Window Sizing

This skill maps primarily to **Reliability**, **Performance**, **Scalability**, and **Operational Excellence** in the Salesforce Well-Architected framework. It also has direct **Cost Optimization** implications because batch sizing decisions are the single largest driver of API-call consumption and storage growth during data migrations.

## Relevant Pillars

- **Reliability** — the right batch size and mode prevent the failures that turn a load into an incident:
  - *Predictable* — serial mode + small batches makes runtime estimable and failure modes deterministic. Parallel mode against a row-skewed parent makes failure non-deterministic and unrecoverable in the same job.
  - *Resilient* — External Id deferred linkage makes loads idempotent: a re-run after partial failure does not create duplicates. Parent-first ordering with capture-and-map breaks under retry.
  - *Recoverable* — pre-load freeze (trigger bypass via CMDT) plus post-load enrich means a failure mid-enrich is recoverable by re-running the enrich job, not by replaying the entire ingestion.

- **Performance** — sizing the batch window IS the performance optimisation:
  - *Throughput* — larger batches reduce API call overhead and Bulk job state-machine overhead, which matters when daily API budget is constrained.
  - *Latency* — smaller batches reduce per-batch trigger CPU consumption, which matters for objects with rich record-triggered automation. The right batch size minimises wall-clock time without breaching governor envelopes.
  - *Avoiding wasted work* — Defer Sharing Calculations + post-load enrich avoid the multi-hour async sharing-recalc tail that effectively idles the org for hours after a "successful" load.

- **Scalability** — the pattern scales from 10K to 10M+ records by tier-shifting the recommendation, not by retrying with the same default:
  - *Tiered defaults* — Decision Guidance table prescribes different batch sizes and modes for <10K, 10K–1M, 1M–10M, 10M+ tiers. The same load profile that works at 10K does NOT scale to 10M.
  - *Bulk-shape by construction* — recommending External Id deferred linkage and Bulk V2 over REST Composite means the load shape is bulk-native from the start, not a UI-shape that breaks at 100K records.
  - *Decoupled phases* — splitting ingestion (trigger-bypassed) from enrichment (post-load Batch Apex) means each phase can be scaled and retried independently.

- **Operational Excellence** — every choice in this skill is a runbook concern:
  - *Observable* — pilot runs (5,000 records) produce metrics (runtime, error rate, governor warnings) that inform the full-load decision. The runbook is data-driven, not vibes-driven.
  - *Manageable* — Defer Sharing Calculations gates an explicit re-enable step in the runbook; trigger bypass via CMDT gates an explicit unset step. Each operational concern has a corresponding action in the workflow.
  - *Compliant* — running as a dedicated load user (not a personal admin) preserves audit trails, makes the load attributable, and avoids accidentally inheriting admin's role-hierarchy implications.

- **Cost Optimization** — explicit even though not in the schema enum:
  - *API call budget* — `record_count / batch_size = batch_count` and each batch is ~2 API calls. Choosing batch=10,000 vs batch=200 for a 5M load is the difference between **1,000 calls** and **50,000 calls** consumed against the daily quota. For Enterprise orgs at 100K calls/day, this is a hard budget item.
  - *Storage cost* — disabling field history tracking on bulk-update fields for the load window prevents million-row history-table explosions that consume data storage allocation (which is billable beyond included entitlements).
  - *Compute cost* — async sharing recalculation is "free" CPU but is not free *opportunity cost*: the org is unusable while it runs, which is a real productivity cost. Mitigating it via Defer Sharing Calculations is a cost-optimisation action.

## Architectural Tradeoffs

| Lever | Smaller / Slower side | Larger / Faster side |
|---|---|---|
| Batch size | Lower CPU pressure per batch; more API calls; longer wall clock | Fewer API calls; risk of CPU/CPU/lock errors; faster wall clock when it works |
| Parallel vs serial | Predictable, no row-lock risk; longer wall clock | Faster wall clock when shape supports it; UNABLE_TO_LOCK_ROW on row-skew |
| Trigger bypass | Decouples ingestion from rule eval; requires post-load enrich | Single-pass simplicity; vulnerable to governor limits on rich automation |
| Defer Sharing Calculations | Org usable during load; explicit re-enable step | "Set and forget"; multi-hour async tail blocks reports |
| External Id deferred linkage | Idempotent re-runs; schema work upfront | No schema changes; brittle on retry |

The cross-cutting principle: **buy predictability with wall-clock time**. Salesforce loads fail in spectacular ways when optimised purely for speed; sizing decisions should err on the side of "too small / too serial / too deferred" because the failure modes of "too large / too parallel / too synchronous" are far more expensive to recover from.

## Anti-Patterns

1. **Defaulting to batch=200 for every object regardless of complexity** — 200 is wrong for both ends of the spectrum. Simple Public R/W loads waste API calls at 200; complex Private OWD loads with rich automation hit CPU at 200. Tier the recommendation to volume + complexity per the Decision Guidance table.

2. **Optimising for wall-clock time before correctness** — picking parallel mode and large batches "to finish faster," then dealing with `UNABLE_TO_LOCK_ROW` errors after the fact. The retry pass takes longer than starting in serial would have, AND it produces a partially loaded org that is harder to reason about.

3. **Treating sharing recalculation as invisible** — declaring the load done at "Bulk job complete" and letting business stakeholders find out hours later that reports are still slow. Sharing recalc tail is part of the load runtime; communicate it.

4. **Loading with a personal admin account** — pollutes the audit trail, attaches the load to a person's role placement in the hierarchy, and makes "let's just re-assign owners later" a structurally expensive cleanup. Use a dedicated load user with explicit permissions.

5. **Using REST Composite for >100K records "because it's familiar"** — REST Composite is capped at 200 records per request and is an order of magnitude slower than Bulk V2 for the same volume. Anything over a few thousand records belongs on Bulk V2 (or Bulk V1 via Data Loader's "Use Bulk API" checkbox).

## Official Sources Used

- **Bulk API 2.0 Developer Guide — Job state machine and limits**: <https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/bulk_api_2_0.htm> — canonical source for the 10,000-records-per-batch upload limit and the parallel/serial mode semantics.
- **Bulk API 2.0 Developer Guide — Ingest job lineSeparator and batch processing**: <https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/walkthrough_upload_curl.htm> — describes the internal 200-row server-transaction chunking referenced in Gotcha 6.
- **Salesforce Help — Data Loader Guide**: <https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5> — UI defaults (batch size 200, "Use Bulk API" toggle) and behaviour reference.
- **Salesforce Help — Defer Sharing Calculations**: <https://help.salesforce.com/s/articleView?id=sf.security_sharing_defer_sharing_calc.htm&type=5> — what the deferral covers (group-membership and sharing-rule recalc) and what it does not (territory, account-team, opportunity-team, manual shares).
- **Salesforce Help — Reduce Lock Contention (UNABLE_TO_LOCK_ROW)**: <https://help.salesforce.com/s/articleView?id=000387590&type=1> and the Architect's "Working with Very Large SOQL Queries" guidance — the row-skew failure model and the "switch to serial" remediation.
- **Salesforce Help — Best Practices for Deployments with Large Data Volumes**: <https://help.salesforce.com/s/articleView?id=sf.large_data_volumes_lex_best_practices.htm&type=5> — official LDV (Large Data Volume) playbook covering API selection, indexing, sharing, and parent-child loading order.
- **Apex Developer Guide — Governor Limits**: <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm> — 60-second synchronous CPU limit, 10-minute Batch Apex CPU limit, 100-DML-statements limit referenced throughout.
- **Salesforce Help — Field History Tracking**: <https://help.salesforce.com/s/articleView?id=sf.tracking_field_history.htm&type=5> — confirms the 1-history-row-per-tracked-field-per-changed-record fan-out.
- **Salesforce Architect — Large Data Volumes (LDV) Patterns**: <https://architect.salesforce.com/decision-guides/large-data-volumes> — architecture-level guidance on chunking, indexing, and parent-child loading.
- **Salesforce Architect — Well-Architected Reliability Pillar**: <https://architect.salesforce.com/well-architected/reliable> — frames the predictable / resilient / recoverable sub-attributes referenced above.
- **Salesforce Architect — Well-Architected Performance Pillar**: <https://architect.salesforce.com/well-architected/efficient> — frames the throughput / latency / wasted-work framing for batch sizing.
