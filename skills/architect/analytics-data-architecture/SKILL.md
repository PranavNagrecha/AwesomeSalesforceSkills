---
name: analytics-data-architecture
description: "Use this skill when designing CRM Analytics dataset architecture, planning dataflow or Recipe ELT strategies, implementing incremental extraction patterns, or integrating external data lakes (Snowflake, BigQuery, Redshift). Trigger keywords: CRM Analytics dataset design, dataflow performance, Recipe incremental, remote connection data lake, analytics ELT strategy, dataset row limits. NOT for standard Salesforce object data modeling, Salesforce Data Cloud architecture, or MuleSoft integration design."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Scalability
triggers:
  - "How should I design my CRM Analytics datasets to avoid hitting row limits or refresh windows?"
  - "How do I set up incremental loads in CRM Analytics Recipes so I'm not reprocessing everything every run?"
  - "We want to connect Snowflake or BigQuery as an external data source in CRM Analytics — how do we configure that?"
tags:
  - crm-analytics
  - architecture
  - dataset-design
  - incremental
  - data-lake
  - architect
inputs:
  - "List of Salesforce objects and external sources to be included in analytics"
  - "Estimated dataset row volumes and growth projections"
  - "Current dataflow / Recipe refresh schedules and run frequency"
  - "External data lake platform in use (Snowflake, BigQuery, Redshift, or none)"
  - "Org CRM Analytics license tier (Growth, Plus, or Einstein Analytics)"
outputs:
  - "Dataset design recommendations with row-limit risk assessment"
  - "ELT strategy: what transforms belong in dataflow/Recipe vs. SAQL runtime"
  - "Incremental extraction pattern (snapshot-join technique for Recipes)"
  - "Remote Connection setup guidance for external data lake integration"
  - "Dataflow run-budget analysis against the 60-run rolling window"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Data Architecture

Use this skill when architecting CRM Analytics data pipelines end-to-end: designing datasets for scale, choosing the right ELT strategy, implementing incremental extraction where native support is absent, and integrating external cloud data sources. It activates when the practitioner needs to make structural decisions — not just configure an existing setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Dataset row volumes:** Confirm approximate current and projected row counts per dataset. The hard ceiling is 2 billion rows per dataset (org allocation-dependent); breaching it causes dataflow failures with no automatic truncation.
- **Run frequency:** Map every dataflow and Recipe to its refresh schedule. The platform enforces a limit of 60 combined dataflow and Recipe runs per rolling 24-hour window (not a calendar-day reset). Orgs with many high-frequency refreshes hit this limit before hitting row limits.
- **Incremental requirement:** Ask whether the business needs near-real-time data or batch-daily. Dataflows support incremental extraction via Data Sync (SystemModstamp-based). Recipes do NOT — every Recipe run reprocesses the full input dataset. Incremental behavior in Recipes must be simulated.
- **External sources:** Confirm whether Snowflake, BigQuery, Redshift, or another external warehouse is in scope. These are connected via Remote Connections in Data Manager — not through dataflow JSON.
- **License tier:** Some advanced Recipe nodes and connector types require Einstein Analytics Plus or higher. Verify before designing around them.

---

## Core Concepts

### Dataset Row Limits and the 2-Billion-Row Ceiling

CRM Analytics datasets have a per-dataset row cap that is org-allocation-dependent, with the practical ceiling at 2 billion rows per dataset. Exceeding this limit causes the dataflow or Recipe writing to that dataset to fail; the platform does not silently truncate. The architectural response is to split large datasets by time window or business dimension (e.g., current-year vs. historical), implement archival datasets with reduced granularity, and filter aggressively in the ELT layer before data lands in the dataset — not at SAQL query time.

The total row count across all datasets in an org also has an allocation. Architects must track both per-dataset and org-wide consumption, especially when onboarding new data sources.

### The 60-Run Rolling Window

The platform allows at most 60 combined dataflow and Recipe runs within any rolling 24-hour window. This is not a calendar-day reset — it is a true rolling window. An org that runs 60 jobs between 08:00 and 09:00 cannot run another job until 08:00 the following day for each slot to clear.

This is the most common architectural bottleneck in mature CRM Analytics orgs. The correct design responses are:
- Consolidate multiple single-object dataflows into fewer multi-object dataflows.
- Schedule high-frequency refreshes only for the datasets actually driving live dashboards.
- Use a tiered refresh strategy: critical datasets hourly (within budget), supporting datasets daily.
- Monitor run consumption via the Dataflow Monitor in Analytics Studio.

### ELT Strategy: Push Work into the Dataflow Layer, Not SAQL

SAQL (Salesforce Analytics Query Language) executes at dashboard query time. Every user interaction with a dashboard that triggers a SAQL query recomputes from the stored dataset. Joins, aggregations, and complex filters placed in SAQL run repeatedly at runtime and do not scale.

The correct ELT strategy is to perform all joins, filters, augments, and computed columns during the dataflow or Recipe run. The dataset that lands in CRM Analytics should be query-ready: denormalized, pre-joined, and pre-filtered to the relevant time window. SAQL should only perform final aggregations and simple filters that vary per user interaction.

This distinction is sometimes called "push-down ELT": move the heavy lifting upstream into the dataflow/Recipe layer where it runs once per refresh cycle, not once per user query.

### Incremental Extraction: Dataflows vs. Recipes

**Dataflows** support incremental extraction natively through the Data Sync replication layer. When a Salesforce object is synced using incremental mode, Data Sync tracks the `SystemModstamp` of the last-replicated record. On subsequent syncs, only records with a newer `SystemModstamp` are replicated. The dataflow then processes the delta. This requires the source object to have `SystemModstamp` indexed and the Data Sync connection configured for incremental mode in Data Manager.

**Recipes do NOT support native incremental loads.** Every Recipe run reads its full input dataset from scratch — there is no built-in mechanism to process only changed rows. The correct workaround is the snapshot-join technique:
1. On first run, write the output dataset as the "current snapshot."
2. On subsequent runs, join the full current source data against the prior snapshot dataset.
3. Use a computed field comparing `LastModifiedDate` (from source) against the snapshot date to identify new or changed records.
4. Union the unchanged rows from the snapshot with the changed rows from the current source pull.
5. Write the merged result as the new snapshot, overwriting the previous one.

This approach requires careful schema management — the snapshot dataset schema must match the Recipe output schema exactly, or the union step fails.

---

## Common Patterns

### Pattern 1: Snapshot-Join Incremental for Recipes

**When to use:** A Recipe refreshes a large dataset (millions of rows) from a Salesforce object and full reprocessing takes too long or consumes too much run budget.

**How it works:**
1. Create a Recipe that reads the source object (e.g., `Opportunity`) and writes the first full load to `opp_snapshot` dataset.
2. On the next scheduled Recipe run, the Recipe reads both the live source and `opp_snapshot`.
3. A Join node compares `LastModifiedDate` from the live source against the stored `snapshot_date` field in `opp_snapshot`.
4. Records where `LastModifiedDate > snapshot_date` are treated as changed; all others come from `opp_snapshot` unchanged.
5. An Append node unions both sets; a Formula node stamps `today()` as the new `snapshot_date`.
6. The output overwrites `opp_snapshot`.

**Why not the alternative:** Without this pattern, every Recipe run reprocesses the full Opportunity table. In orgs with 5M+ Opportunity records, this can take 20–40 minutes per run and consumes a full slot from the 60-run window.

### Pattern 2: Push-Down ELT — Denormalize in Dataflow, Not SAQL

**When to use:** Dashboard queries are slow because SAQL is joining two or more datasets at runtime, or because complex SAQL expressions (e.g., windowed calculations) are running per user interaction.

**How it works:**
1. Identify the join keys between the source datasets (e.g., `Opportunity.AccountId` → `Account.Id`).
2. Add an Augment transformation in the dataflow to embed the Account fields needed by the dashboard directly into the Opportunity dataset.
3. Add a Computeexpression transformation to pre-calculate derived fields (e.g., `Days_to_Close = DATEDIFF(CloseDate, CreatedDate)`).
4. Write a single flat dataset to CRM Analytics.
5. Update dashboard SAQL to remove multi-dataset joins — queries now target the single flat dataset.

**Why not the alternative:** Multi-dataset SAQL joins are evaluated on every query execution. They cannot be cached across users and scale poorly as dataset row counts grow.

### Pattern 3: External Data Lake Integration via Remote Connections

**When to use:** The org needs to query or ingest data from Snowflake, BigQuery, or Amazon Redshift alongside Salesforce object data.

**How it works:**
1. In Analytics Studio, navigate to Data Manager → Connections.
2. Create a Remote Connection of the appropriate type (Snowflake, BigQuery, or Redshift). Enter connection credentials, project/database identifiers, and authentication parameters.
3. Once the Remote Connection is saved, it appears as an input source available to Recipes.
4. In a Recipe, add the Remote Connection as an input node and select the target table or view.
5. Join, filter, and transform the external data alongside Salesforce object data within the Recipe.
6. Write the output to a CRM Analytics dataset. Note: the output lives in CRM Analytics — it does NOT write back to the external lake.

**Why not the alternative:** Remote Connection configuration belongs in Data Manager, not in dataflow JSON. Dataflow JSON does not have a native connector type for Snowflake, BigQuery, or Redshift. Attempting to configure these sources in dataflow JSON will fail.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Large Salesforce object (1M+ rows), needs near-daily refresh | Data Sync incremental mode + dataflow | Native SystemModstamp-based incremental; no custom workaround required |
| Large dataset in Recipe, full reprocessing too slow | Snapshot-join technique in Recipe | Recipes have no native incremental; snapshot-join is the only supported simulation |
| Dashboard queries joining two datasets at runtime | Augment in dataflow (push-down ELT) | Pre-join at refresh time; SAQL executes once-per-query, not once-per-refresh |
| Run budget approaching 60-run limit | Consolidate dataflows; use tiered schedules | Each dataflow run counts equally; fewer, larger runs are more efficient |
| External Snowflake/BigQuery/Redshift source needed | Remote Connection in Data Manager | Dataflow JSON has no connector type for these sources |
| Dataset approaching 2B row cap | Split by time window or business dimension | Platform fails the write — no auto-truncation; must design around the cap |
| Pre-calculated KPIs needed across many dashboard queries | Computeexpression in dataflow or Recipe | Compute once at ELT time; eliminates repeated SAQL formula evaluation per user |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory datasets and run volumes.** List every dataflow and Recipe in the org with its row count, estimated growth rate, and current refresh schedule. Map total scheduled runs per 24-hour window against the 60-run budget.
2. **Identify ELT placement issues.** Review existing SAQL queries in dashboards for joins, augments, and heavy computations. Flag any that could be pre-computed in the ELT layer and move them upstream into dataflow or Recipe transformations.
3. **Design the incremental strategy.** For each large dataset, determine whether it is sourced from a dataflow (use Data Sync incremental mode) or a Recipe (implement snapshot-join). Document the snapshot dataset name, the comparison field (`LastModifiedDate`), and the schema contract.
4. **Configure external sources.** If Snowflake, BigQuery, or Redshift data is needed, create Remote Connections in Data Manager before building any Recipe nodes. Confirm credentials, network access (IP allowlisting for Salesforce IPs if required), and authentication method (OAuth vs. username/password).
5. **Validate against limits.** Confirm no individual dataset is projected to exceed 2 billion rows. Confirm combined run schedules do not exceed 60 runs per rolling 24-hour window. Adjust schedules or consolidate dataflows as needed.
6. **Test incremental correctness.** For any snapshot-join Recipe, run two consecutive test cycles: first to seed the snapshot, second to confirm only changed records are re-processed. Validate row counts before and after to confirm no duplication or data loss.
7. **Document and schedule.** Record dataset ownership, refresh owners, row-limit thresholds, and escalation path for run-budget exhaustion. Set up Dataflow Monitor alerts where available.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All dataset projected row counts verified against the 2-billion-row per-dataset cap
- [ ] Total daily run count verified against the 60-run rolling window limit
- [ ] All joins, augments, and computed fields pushed into ELT (dataflow/Recipe), not left in SAQL
- [ ] Incremental strategy confirmed per source: Data Sync incremental for dataflows, snapshot-join for Recipes
- [ ] External source connections created in Data Manager (not configured in dataflow JSON)
- [ ] Snapshot-join Recipes tested across two consecutive runs to confirm no duplication or data loss
- [ ] Dataflow Monitor or equivalent alerting configured for run-budget and row-limit thresholds

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Recipes have no native incremental mode** — Every Recipe run reprocesses the entire input dataset. Architectures that claim "only changed rows are processed" in a Recipe without a snapshot-join step are incorrect and will reprocess the full source on every run, consuming the full run slot and runtime every time.
2. **60-run limit is a rolling 24-hour window, not a calendar-day reset** — An org that exhausts its 60-run budget at 10:00 AM cannot run another job until 10:00 AM the following day as each slot clears. Calendar-day assumptions (e.g., "resets at midnight") produce incorrect capacity planning.
3. **Remote Connections for external lakes belong in Data Manager, not dataflow JSON** — Snowflake, BigQuery, and Redshift sources are configured as Remote Connections under Data Manager → Connections. Dataflow JSON has no connector node type for these sources. Architects who attempt to embed connection parameters in dataflow JSON will find the dataflow fails to validate.
4. **Remote Connections do not write back to the external lake** — CRM Analytics only reads from external sources via Remote Connections. Output datasets are always written to CRM Analytics internal storage. Any architecture that expects analytics transformations to populate the external data warehouse requires a separate ETL pipeline outside CRM Analytics.
5. **Data Sync incremental mode requires SystemModstamp to be indexed** — If the source Salesforce object does not have `SystemModstamp` available or the Data Sync connection is set to full-replace mode, no incremental extraction occurs. This is a silent misconfiguration — the dataflow succeeds but processes full data on every run.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dataset design document | List of datasets with projected row counts, growth rates, split strategy, and row-limit risk rating |
| ELT strategy map | Table mapping each join/augment/computation to its ELT layer placement (dataflow, Recipe, or SAQL) |
| Run budget analysis | Schedule of all dataflow and Recipe runs plotted against the 60-run rolling window |
| Incremental pattern specification | Per-dataset incremental approach (Data Sync incremental vs. snapshot-join), including snapshot dataset name and comparison field |
| Remote Connection setup checklist | Step-by-step configuration for each external source in Data Manager |

---

## Related Skills

- admin/analytics-dataset-management — Row-level dataset configuration, field type settings, refresh scheduling, and platform quota management at the admin level
- admin/crm-analytics-app-creation — Creating and structuring CRM Analytics apps, permission assignment, and initial dataset wiring
- admin/analytics-dashboard-design — Dashboard SAQL bindings, faceting, and chart configuration; use alongside this skill when optimizing query performance
