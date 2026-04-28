---
name: data-loader-batch-window-sizing
description: "Choose the right batch size, parallel/serial mode, and load window for Data Loader, Bulk API V1/V2, and custom Database.executeBatch jobs against a given object volume and complexity profile. Covers tradeoffs between batch size, trigger CPU cost, sharing recalculation cost, and row-skew lock contention. NOT for CSV column mapping (see data/data-loader-csv-column-mapping). NOT for picklist validation pre-load (see data/data-loader-picklist-validation-pre-load). NOT for sharing-recalc tuning after the load lands (see data/sharing-recalculation-performance)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
  - Scalability
tags:
  - data-loader
  - bulk-api
  - batch-size
  - row-skew
  - sharing-recalc
  - lock-contention
  - parallel-vs-serial
  - migration
triggers:
  - "what batch size should I use to load 5 million accounts"
  - "UNABLE_TO_LOCK_ROW errors during data loader bulk insert"
  - "data load is taking hours and we cannot tell why"
  - "how do I size a one-time historical migration into Salesforce"
  - "Bulk API V2 parallel vs serial mode for opportunities with territories"
  - "trigger CPU limit hit during 200-record batch insert"
inputs:
  - Target SObject (and whether it has triggers, validation rules, sharing rules, role hierarchy, territories)
  - Total record count for the load
  - OWD setting for the SObject (Public Read/Write vs Private)
  - Whether field history tracking, feed tracking, or duplicate rules are enabled on the object
  - Whether parent records already exist (or must be loaded first / linked via External Id)
  - Daily API call budget headroom (edition + add-ons)
  - Whether the load is one-time historical or recurring
outputs:
  - Recommended batch size (records per batch) with reasoning
  - Recommended mode (Bulk API V2 parallel vs serial; Bulk V1 vs REST Composite vs Batch Apex)
  - Recommended load order (parent → child, or External Id deferred linkage)
  - Estimated runtime range and API call consumption
  - Pre-load freeze plan (trigger bypass, rule disablement) and post-load enrich plan
  - Fallback batch size if the first attempt errors with row-locks or CPU timeouts
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Data Loader Batch Window Sizing

Activate this skill when planning a high-volume insert, update, or upsert through Data Loader, Bulk API V1, Bulk API V2, REST Composite, or a custom `Database.executeBatch` job — and someone needs to pick a defensible batch size and mode before kicking off the load. The wrong batch size on a complex object turns a 30-minute job into a 14-hour job, fills the org's API call budget, and produces a multi-hour sharing-rule recalculation that nobody scheduled.

This skill is NOT about CSV column mapping (see `data/data-loader-csv-column-mapping`), NOT about pre-load picklist validation (see `data/data-loader-picklist-validation-pre-load`), and NOT about tuning sharing recalculation after the load already landed (see `data/sharing-recalculation-performance`). It is the upstream sizing decision: how big each batch should be, whether to run parallel or serial, and how to split the work into windows.

---

## Before Starting

Gather this context before recommending a batch size:

| Context | What to confirm |
|---|---|
| Object profile | Triggers, process builder/flow record-triggered automation, validation rules, duplicate rules, sharing rules, role hierarchy, criteria-based sharing, territory management, field history tracking — each changes per-record cost. |
| Volume tier | Under 10K, 10K–1M, 1M–10M, or 10M+? The right answer flips between tiers. |
| OWD setting | Public R/W skips implicit-share recalc; Private + role hierarchy does not. Loading 100K rows of one is a different physics problem from the other. |
| Parent–child shape | Are parents already present or part of the same load? If part of the load, External Id deferred linkage is usually safer than strict parent-first ordering. |
| API call budget | Enterprise base ~100K calls/day; Bulk V1 consumes per batch, Bulk V2 per job state poll. Confirm headroom before sizing. |
| Time budget | Maintenance window vs business hours. Business hours forces smaller batches and serial mode for sensitive objects. |

The single most common wrong assumption: "200 is the safe default for everything." Data Loader's UI default of 200 is not a recommendation — it is a starting point. For complex Account loads it is often too high; for simple Lead inserts it is wastefully low.

---

## Core Concepts

### 1. Batch size is a tradeoff between API calls and per-batch CPU

Smaller batches mean more API calls (each batch consumes 1 from the daily budget) but lower per-batch CPU consumption. Larger batches reduce API calls but multiply trigger work — `200 records × 10 record-triggered automations × per-record CPU` can hit the **60s synchronous CPU limit** (or **10-minute batch CPU limit** for `Database.Batchable`) on a single batch.

Concrete numbers to memorise:
- **Bulk API V2** allows up to **10,000 records per batch upload**, but the platform internally chunks to 200-row server-side blocks for trigger and rule evaluation. Hitting 10K is rarely the right answer for objects with non-trivial triggers.
- **Data Loader UI** defaults to **200** (Bulk API V1 setting "Use Bulk API" raises this to 10,000 internally chunked).
- **REST Composite** is capped at **200 records per request** and is intentionally a small-volume API.
- **`Database.executeBatch(scope)`** accepts 1–2,000; the practical ceiling for record-triggered work is far lower.

### 2. Parallel mode amplifies row-lock contention

Bulk API V2 runs in **parallel mode by default**. When two parallel batches try to update the same parent record (e.g., two child Contacts whose parent Account is the same), the second batch fails with `UNABLE_TO_LOCK_ROW`. The classic shape is a **row-skewed parent** — one Account with 10,000 Contacts, one Owner with 10,000 Accounts, or one Lookup target with disproportionate children.

**Switch to serial mode** for: Account, Opportunity (especially with territories), any object with a row-skewed parent, any update path that triggers parent rollup recalculation. Serial mode trades wall-clock speed for predictability — it is the right call any time predictability matters more than minimum runtime.

### 3. Sharing recalculation is the hidden cost on Private OWD objects

Inserting **100K Accounts into a Private OWD org with a role hierarchy** triggers implicit-share row creation for every level of the hierarchy that has access. The visible insert finishes quickly; the **sharing recalculation runs asynchronously for hours afterwards** and can lock out reports, list views, and other automation while it runs. This is the #1 reason "the load finished but the org is unusable for the rest of the day."

Mitigations: load with the OWD owner unchanged (avoid post-insert ownership re-assignment), use **Defer Sharing Calculations** (Setup → Sharing Settings → Defer Sharing Calculations) for the load window if available, schedule the load before a low-traffic window, and **never re-parent ownership immediately after the load**.

### 4. Trigger fire impact compounds linearly with batch size

For an Account with 10 record-triggered automations (triggers + record-triggered Flows), a 200-record batch fires **2,000 automation invocations**. Each invocation pays its own SOQL/DML overhead and contributes to the per-transaction governor pool. Doubling the batch to 400 doubles the per-transaction CPU consumption; the chance of hitting the 60-second CPU limit doubles too.

For one-time historical loads, the right move is often a **trigger bypass via Custom Metadata** (e.g., a `TriggerControl__mdt` flag the handlers read) plus a separate **post-load enrich job** that runs the calculations the bypassed triggers would have done. This decouples ingestion from rule evaluation.

### 5. Parent-child loading order vs External Id deferred linkage

Two valid strategies for parent-child mass loads:

- **Strict parent-first ordering** — load Accounts, capture returned Ids, map them onto child Contact records, load Contacts. Reliable, but requires Id-mapping bookkeeping in the ETL layer.
- **External Id deferred linkage** — load Accounts and Contacts in any order, with an `External_Id__c` field on Account and a Contact lookup that uses upsert with External Id. The platform resolves the linkage automatically. Requires schema work upfront but eliminates ordering errors and enables idempotent retries.

External Id is the right default for any migration from another system that already has stable record identifiers. Strict ordering is for greenfield loads where no External Id exists.

---

## Common Patterns

### Pattern A: Public Read/Write simple object, large volume → Bulk V2 parallel, large batch

**When to use:** Lead inserts, Task/Event mass-create, simple custom-object loads with no record-triggered automation and Public R/W OWD.

**How it works:** Bulk API V2, parallel mode, batch size 5,000–10,000. The platform's internal 200-row chunking handles trigger evaluation; you save API calls and complete fast.

**Why not the alternative:** dropping to batch=200 here just multiplies API calls without solving any real problem — there is no sharing recalc, no row-skew, no trigger CPU pressure to manage.

### Pattern B: Private OWD object with triggers and role hierarchy → Bulk V2 serial, smaller batch, deferred sharing

**When to use:** Account loads in a Private R/W org, Opportunity loads with territory management, Contact loads in healthcare/financial-services orgs with strict role hierarchies.

**How it works:** Bulk API V2, **serial mode**, batch size 200–500, **Defer Sharing Calculations** enabled for the duration, load runs in a maintenance window. Triggers stay on (or are bypassed via a CMDT flag with a separate post-load enrich job).

**Why not the alternative:** parallel mode here produces `UNABLE_TO_LOCK_ROW` storms; large batches blow the trigger CPU limit; not deferring sharing turns a 1-hour load into a 6-hour sharing-recalc tail.

### Pattern C: Parent-child mass migration → External Id upsert, two-pass

**When to use:** any migration from a legacy CRM where record identity already exists in the source system; any time the load may need to be re-run idempotently.

**How it works:** add `External_Id__c` (External Id, Unique, Case-Insensitive) to both parent and child SObjects. Pass 1: upsert parents by External Id. Pass 2: upsert children by External Id with the parent lookup populated by parent External Id (Salesforce resolves the lookup at upsert time). No manual Id mapping required.

**Why not the alternative:** strict parent-first ordering with Id capture works but breaks on retry — re-running the load creates duplicate parents unless External Id deduplication is bolted on after the fact. Build the right shape from the start.

### Pattern D: One-time historical load → trigger bypass + post-load enrich

**When to use:** a one-time migration of 5+ years of historical Cases, Orders, or Opportunities where the live triggers are designed for incremental day-to-day inserts, not bulk historical replay.

**How it works:** a `TriggerControl__mdt` Custom Metadata Type with a `Bypass_Object__c` flag the trigger handlers read at the top of `before insert`. Set the flag for the load user, run the load, run a separate **post-load enrich** Batch Apex job that performs the calculations the bypassed triggers would have done (rollups, sharing-rule sub-cases, validation backfill), then unset the flag.

**Why not the alternative:** running historical data through real-time triggers is structurally wrong — the triggers were designed for one record at a time arriving from a UI, not 5 years of records arriving in 30 minutes. They will hit governor limits, fire emails to long-departed users, and create duplicate platform-event traffic.

---

## Decision Guidance

| Situation | Object size & complexity | Batch size | Mode | Notes |
|---|---|---|---|---|
| Simple custom object, no triggers, Public R/W | <10K records | **2,000–10,000** | Bulk V2 parallel | Maximise throughput; no recalc concerns. |
| Standard object with triggers and validation rules, Public R/W | 10K–1M records | **500–1,000** | Bulk V2 parallel | Watch trigger CPU; drop to 200 if `CPU_TIME_LIMIT_EXCEEDED` appears. |
| Private OWD object with sharing rules and role hierarchy | >1M records | **200** | Bulk V2 serial | Defer Sharing Calculations ON; load in maintenance window; expect long async sharing tail. |
| Parent-child mass load (Account + Contact, Order + OrderItem) | any tier | **500** parent / **500** child | Bulk V2 serial | Use External Id deferred linkage; two-pass upsert. |
| Object with row-skewed parent (one Account with 10K children) | any tier | **200** | Bulk V2 **serial** | Parallel guarantees `UNABLE_TO_LOCK_ROW`. Serial is mandatory. |
| Opportunity with Territory Management 2.0 | any tier | **200** | Bulk V2 serial | Territory assignment runs per-record; serial avoids territory-rule lock contention. |
| One-time historical load with rich automation | any tier | **500–2,000** | Bulk V2 parallel **with trigger bypass** | Bypass via CMDT, separate post-load enrich job; treat as two phases. |
| Recurring small daily load | <50K records | **200** | Data Loader UI default OK | Stay on Bulk V1 path; not worth optimising. |

When in doubt, start at **batch=200, serial mode**, run a 5,000-record pilot, measure, then scale up. Going small-and-serial first costs minutes; going large-and-parallel first and rolling back costs a maintenance window.

---

## Recommended Workflow

1. **Profile the target SObject** — list triggers, record-triggered Flows, validation rules, duplicate rules, sharing rules, role hierarchy, territories, field history tracking, feed tracking. Each one changes the recommendation.
2. **Determine the volume tier** — under 10K / 10K–1M / 1M–10M / 10M+. Map to the Decision Guidance table.
3. **Check OWD and parent-child shape** — Public R/W vs Private; standalone vs parent-child; row-skewed parents (any single parent with >10K children pointing at it).
4. **Pick batch size and mode from the table**, then sanity-check against API call budget (`record_count / batch_size = batch_count`; each batch is ~1–2 API calls).
5. **Plan the freeze and the enrich** — if this is a one-time historical load, design the CMDT trigger-bypass flag and the post-load enrich Batch Apex job before kicking off ingestion.
6. **Run a 5,000-record pilot** at the chosen settings; measure runtime, error rate, governor-limit warnings in the debug log. Adjust batch size down if `CPU_TIME_LIMIT_EXCEEDED` or `UNABLE_TO_LOCK_ROW` appears.
7. **Run the full load in a maintenance window** with **Defer Sharing Calculations** enabled (Private OWD only); monitor the async sharing recalc tail before declaring done.
8. **Run `scripts/check_data_loader_batch_window_sizing.py`** with the object profile to confirm the chosen batch size and mode match the recommendation.

---

## Review Checklist

Before kicking off a high-volume load:

- [ ] Object profile (triggers, rules, sharing, hierarchy, territories) is documented
- [ ] Batch size matches the Decision Guidance table for the volume tier and complexity
- [ ] Mode (parallel vs serial) matches the row-skew and parent-rollup risk
- [ ] Parent-child loads use External Id deferred linkage where possible
- [ ] One-time historical loads have a trigger-bypass plan AND a post-load enrich plan
- [ ] Defer Sharing Calculations is ON for Private OWD loads >100K
- [ ] API call budget headroom confirmed (`batch_count` × 2 < daily quota remaining)
- [ ] Pilot run (5,000 records) completed without governor errors before full load
- [ ] Maintenance window identified for Private OWD loads with role hierarchy
- [ ] Field history tracking impact reviewed — every tracked field × every changed record = 1 history row

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that ruin loads:

1. **Defer Sharing Calculations does NOT defer implicit shares for Account–Contact–Opportunity** — only group-membership recalcs and sharing-rule recalcs. Account loads still trigger account-team and account-territory share rows synchronously. See `references/gotchas.md`.
2. **Bulk API V2 internally chunks to 200 even when you upload 10,000** — the platform inserts in 200-row server transactions for trigger evaluation. Setting batch size to 10,000 does NOT bypass the per-200 trigger CPU envelope; it only reduces the API call count.
3. **Trigger CPU is per server transaction, not per batch upload** — chasing CPU errors by raising the batch size does the opposite of what you want. Lowering it or bypassing triggers is the correct lever.
4. **`UNABLE_TO_LOCK_ROW` under parallel mode is not retryable in place** — the failed records must be retried in a separate job (or in serial). Bulk API V2's automatic retry does not solve row-skew row locks.
5. **Field history tracking explodes on bulk update** — updating 1M Accounts with 5 history-tracked fields creates 5M `AccountHistory` rows. Disable history tracking for the load window if the historical state is not being preserved by the load itself.
6. **Loading data as the wrong user creates wrong sharing implications** — loading as a System Administrator with `Modify All Data` populates `OwnerId` to that admin unless explicitly mapped. The cleanup re-parenting later triggers the entire sharing recalc again.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sizing recommendation | Batch size, mode, and load order tailored to the SObject + volume + complexity |
| Pre-load freeze plan | Which triggers/rules/sharing-recalcs to bypass or defer for the load window |
| Post-load enrich plan | Batch Apex (or Flow) job that performs the work bypassed triggers would have done |
| Pilot test plan | 5,000-record dry run with metrics (runtime, error rate, governor warnings) before full load |
| Sizing checker run | `scripts/check_data_loader_batch_window_sizing.py` clean exit confirming chosen settings match the table |

---

## Related Skills

- `data/data-loader-and-tools` — choosing between Data Loader, dataloader.io, Workbench, sf data CLI
- `data/bulk-api-and-large-data-loads` — protocol-level Bulk API V1 vs V2 mechanics
- `data/bulk-api-patterns` — Bulk API job state machine and polling patterns
- `data/sharing-recalculation-performance` — tuning the async sharing recalc tail after a load lands
- `data/external-id-strategy` — designing External Id fields for deferred linkage
- `data/data-loader-csv-column-mapping` — pre-load CSV header validation
- `data/data-loader-picklist-validation-pre-load` — pre-load picklist value verification
- `data/data-migration-planning` — end-to-end migration sequencing (this skill is the per-job sizing layer)
