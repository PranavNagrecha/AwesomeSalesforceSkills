---
name: analytics-dataflow-development
description: "Use this skill when building, debugging, or optimizing CRM Analytics dataflows — defining node types (sfdcDigest, Append, Augment, computeExpression, computeRelative, Flatten, dim2mea, sfdcRegister), scheduling runs, handling run failures, and tuning performance. NOT for standard data processing outside CRM Analytics, for recipe-based data prep, or for SAQL dashboard query tuning."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "my dataflow failed partway through and I need to know what happened to my dataset"
  - "how do I join two datasets in a CRM Analytics dataflow without losing rows"
  - "dataflow is hitting the org run limit or taking too long to finish"
  - "I need to add a calculated field at row level inside a dataflow"
  - "how do I schedule a CRM Analytics dataflow to run every night"
tags:
  - crm-analytics
  - dataflow
  - etl
  - transformation
inputs:
  - "List of Salesforce objects and fields to ingest"
  - "Target dataset name and expected row volume"
  - "Join/combination logic between objects"
  - "Calculated field expressions (SAQL)"
  - "Scheduling requirements (frequency, dependencies)"
outputs:
  - "Dataflow JSON definition (.wdf file) with correctly ordered and typed nodes"
  - "Optimization recommendations (filter placement, SliceDataset usage, split strategy)"
  - "Scheduling configuration and run-limit risk assessment"
  - "Failure diagnosis report with corrective action"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Dataflow Development

This skill activates when a practitioner needs to author, debug, or optimize a CRM Analytics dataflow — a JSON-defined ETL pipeline that extracts Salesforce data, applies transformations, and registers the result as a CRM Analytics dataset. It covers node composition, run-limit management, failure recovery, and performance tuning.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org already has dataflows consuming the same source objects; duplicate sfdcDigest nodes across multiple dataflows multiply row-count and run-time cost.
- Identify the target dataset row volume. Datasets are capped at 250 million rows; exceeding this causes the sfdcRegister node to fail.
- Count currently scheduled dataflow and recipe runs. The org is limited to 60 combined dataflow and recipe runs per rolling 24-hour window — not a calendar day reset. New dataflows added to a busy schedule may push the org over the limit.
- Determine whether this is a net-new build or a maintenance task. New development should generally use Recipes (the newer UI-driven ETL tool); dataflows remain the right choice for existing pipelines, complex SAQL expressions not supported in Recipes, or when explicit JSON control is required.

---

## Core Concepts

### Node Types and Pipeline Topology

CRM Analytics dataflows are JSON objects where each key is a node name and the value defines that node's action and parameters. Nodes fall into four functional groups:

**Ingestion nodes** — pull source data into the pipeline:
- `sfdcDigest` — extracts records from a Salesforce object using the Analytics connector. Requires specifying the `object` and a `fields` list. Supports a `filter` parameter to push predicate filtering to the source query.
- `Digest` — reads from a CSV or external data source already uploaded to the org.
- `Edgemart` — references an existing registered CRM Analytics dataset as input. Used for chaining dataflows.

**Combination nodes** — merge multiple node outputs:
- `Append` — row-wise union. All input schemas must be compatible (same field names and types). Unlike SQL UNION ALL, no deduplication occurs.
- `Augment` — column-wise join. **Left-join only.** All rows from the left input are preserved; unmatched rows from the right input are dropped. There is no inner, right, or full-outer join option in dataflows. For multi-join-type requirements use Recipes.

**Enrichment nodes** — transform rows or columns:
- `computeExpression` — evaluates a SAQL expression per row to produce a new field. Runs in row context (no window functions). Used for derived fields, type casts, and conditional logic.
- `computeRelative` — evaluates expressions across a partitioned, ordered window of rows. Used for running totals, rank, and prior-period comparisons. Requires `partitionBy` and `orderBy` parameters.
- `Flatten` — denormalizes hierarchical (parent-child) relationships such as role hierarchy into a flat structure suitable for security predicates or rollup analysis.
- `dim2mea` — converts a dimension (string) field to a measure (numeric) field, enabling aggregation in SAQL queries.
- `Filter` — drops rows that do not match a condition. Has no SOQL pushdown capability but reduces row count for downstream nodes.
- `SliceDataset` — selects a subset of fields from the incoming schema. Used to drop unused columns before expensive operations.

**Terminal node** — writes the result to a dataset:
- `sfdcRegister` — registers the pipeline output as a named CRM Analytics dataset. **Overwrites the existing dataset by default.** There is no append or upsert mode in sfdcRegister; every successful run replaces the entire dataset.

### Run Failure Behavior

A single failing node aborts the entire dataflow run. When a run aborts, the previously registered dataset is left unchanged — it retains its last successful state. No partial writes occur. This means a dataflow with 20 nodes that fails on node 19 produces no change to any registered dataset. Practitioners must check Job Progress Details to identify the failing node, since the error message on the run summary may not pinpoint the root cause.

### Run Quota

The org-wide limit is **60 combined dataflow and recipe runs per rolling 24-hour window**. "Rolling" means the clock starts from each individual run's start time, not from midnight. Adding a new scheduled dataflow to an org already running 58 other jobs per day will breach this limit. Monitor run counts in the Analytics Data Manager or via the REST API before adding schedules.

### Optimization Principles

Large dataflows are the primary source of run-time failures and quota exhaustion. Three optimization strategies apply:

1. **Filter early.** Place `Filter` nodes immediately after `sfdcDigest` or `Edgemart` nodes, before any `Augment` or `computeExpression` nodes. `Augment` is O(n*m) in the worst case; reducing row count before the join significantly cuts runtime.
2. **Slim the schema.** Use `SliceDataset` nodes to drop fields not needed downstream before passing data to `Augment`. Narrower schemas reduce memory usage during join operations.
3. **Split monolithic dataflows.** A single dataflow with 30+ nodes is harder to debug and consumes more per-run resources than two chained dataflows of 15 nodes each. Chain them using `Edgemart` — the upstream dataflow registers an intermediate dataset that the downstream dataflow reads.

---

## Common Patterns

### Pattern: Filtered Augment Join

**When to use:** Joining Opportunity records to Account records to enrich Opportunity data with Account attributes, where only open Opportunities are needed.

**How it works:**
```json
{
  "Extract_Opportunities": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Opportunity",
      "fields": [
        {"name": "Id"},
        {"name": "AccountId"},
        {"name": "Amount"},
        {"name": "StageName"},
        {"name": "CloseDate"}
      ]
    }
  },
  "Filter_Open": {
    "action": "filter",
    "parameters": {
      "source": "Extract_Opportunities",
      "saqlFilter": "StageName != \"Closed Won\" && StageName != \"Closed Lost\""
    }
  },
  "Extract_Accounts": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Account",
      "fields": [
        {"name": "Id"},
        {"name": "Name"},
        {"name": "Industry"},
        {"name": "AnnualRevenue"}
      ]
    }
  },
  "Join_Account_Data": {
    "action": "augment",
    "parameters": {
      "left": "Filter_Open",
      "left_key": ["AccountId"],
      "right": "Extract_Accounts",
      "right_key": ["Id"],
      "right_select": ["Name", "Industry", "AnnualRevenue"],
      "relationship": "Account"
    }
  },
  "Register": {
    "action": "sfdcRegister",
    "parameters": {
      "alias": "Open_Opps_With_Account",
      "name": "Open_Opps_With_Account",
      "source": "Join_Account_Data"
    }
  }
}
```

**Why not the alternative:** Running Augment before Filter passes all Opportunity rows (including closed) through the join, significantly increasing runtime and memory usage for large orgs.

### Pattern: Chained Dataflows for Large Pipelines

**When to use:** A single dataflow has grown to 25+ nodes, is hitting run-time limits, or is difficult to debug because failures could originate anywhere in the graph.

**How it works:**
- Dataflow A performs ingestion and heavy transformation, registers an intermediate dataset (`Intermediate_Opp_Account`).
- Dataflow B reads that intermediate dataset using an `Edgemart` node, applies enrichment and final computeExpression logic, and registers the production dataset.
- Schedule Dataflow B to run after Dataflow A completes (use dependency scheduling or a time offset).

**Why not the alternative:** A monolithic dataflow that fails on the last node wastes all compute from the preceding nodes and delays the error diagnosis cycle.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Building a net-new pipeline on a new org | Use Recipes instead of Dataflows | Recipes are the strategic direction; dataflows are in maintenance mode |
| Maintaining or extending an existing dataflow | Stay in dataflow JSON | Mixing dataflow and recipe for the same dataset causes confusion and scheduling complexity |
| Need an inner join or right join | Use Recipes (Join node supports multiple join types) | Augment in dataflows is left-join-only; no workaround in JSON |
| Need row-level computed field | Use computeExpression node | Supports per-row SAQL expressions without aggregation |
| Need running total or rank across sorted rows | Use computeRelative node | Supports partitioned window expressions; computeExpression cannot reference sibling rows |
| Pipeline taking >45 minutes per run | Split into chained dataflows via Edgemart | Reduces per-run scope and makes failure diagnosis faster |
| Approaching 60 runs/day org limit | Consolidate dataflows that share source objects | Merge sfdcDigest nodes into a single shared dataflow, fan out via Edgemart |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather requirements.** Confirm source objects, required fields, join logic, calculated fields, row volume estimate, and scheduling frequency before writing any JSON.
2. **Check run quota.** Count existing scheduled dataflow and recipe runs in Analytics Data Manager. If the org is within 10 runs of the 60-run rolling limit, raise this before adding a new scheduled dataflow.
3. **Design the node graph on paper first.** Map ingestion nodes → filters → combination nodes → enrichment nodes → sfdcRegister. Place Filter nodes immediately after ingestion and before any Augment joins. Use SliceDataset before Augment to trim unused fields.
4. **Author the dataflow JSON.** Write the `.wdf` file following the node structure. Validate JSON syntax before uploading. Every node must have an `action` and a `parameters` block. Every non-terminal node must be referenced as `source` or `left`/`right` by exactly one downstream node.
5. **Upload and run manually.** Upload the dataflow via Analytics Data Manager. Trigger a manual run and monitor Job Progress Details. Do not rely solely on the run-summary status — inspect individual node durations to identify bottlenecks.
6. **Verify the registered dataset.** After a successful run, open the dataset in the Analytics Studio explorer and confirm row count, field types, and sample values. Check that sfdcRegister used the correct alias (alias determines the API name of the dataset).
7. **Schedule and document.** Set the schedule in Analytics Data Manager. Document the node graph, dataset dependencies, and any Edgemart chain order in the skill template.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Filter nodes are placed before all Augment nodes, not after
- [ ] SliceDataset nodes trim unused fields before expensive joins
- [ ] sfdcRegister alias matches the intended dataset API name (changing alias creates a new dataset)
- [ ] Org is under 50 scheduled runs per rolling 24-hour window (leave buffer)
- [ ] Row volume of the registered dataset is confirmed below 250 million rows
- [ ] All node names are unique within the dataflow JSON
- [ ] Dataflow JSON is valid (no trailing commas, correct bracket pairing)
- [ ] Job Progress Details reviewed after first manual run — no node warnings suppressed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Augment is left-join-only** — practitioners expecting a full join or inner join are surprised when all left-side rows appear in output regardless of match. Unmatched rows get null values for right-side fields. There is no join-type parameter on the Augment node.
2. **sfdcRegister overwrites, never appends** — every successful dataflow run replaces the entire registered dataset. There is no incremental or upsert mode. If a downstream dashboard or SAQL query was mid-execution when the register completed, it may see a briefly empty dataset.
3. **Single node failure aborts the run, prior dataset unchanged** — a failed run leaves the registered dataset in its last successful state. For production datasets refreshed nightly, a failure at 2 AM means dashboards show yesterday's data until the issue is fixed and a new run completes.
4. **60-run limit is rolling, not calendar-day** — the window is a sliding 24 hours from each run's start time, not a midnight-to-midnight reset. Adding a 7 AM dataflow to an org that already ran 60 jobs between 7 AM yesterday and 7 AM today will immediately fail.
5. **computeRelative per-step duration, not total job duration** — the 2-minute run-count exemption check applies per node step, not to the total wall-clock time of the dataflow run. Monitor per-step duration in Job Progress Details rather than total run duration when diagnosing exemption behavior.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dataflow JSON (.wdf) | The complete dataflow definition file, uploadable to Analytics Data Manager |
| Node graph diagram | Visual representation of the node DAG for documentation and debugging |
| Run-limit risk assessment | Count of current scheduled runs vs. 60-run limit with buffer recommendation |
| Dataset verification report | Row count, field types, and sample values from first successful run |

---

## Related Skills

- `crm-analytics-app-creation` — use alongside this skill when the dataflow is being built as part of a new CRM Analytics app; covers app scaffolding, template selection, and dataset-to-dashboard wiring
- `analytics-dataset-management` — use when the focus is dataset configuration, row-level security predicates, or dataset lifecycle management rather than dataflow node authoring
