---
name: analytics-recipe-design
description: "Use this skill when designing or building CRM Analytics Data Prep recipes — including node selection, join patterns, bucket field configuration, formula expressions, and scheduling. Triggers: 'build a recipe', 'join datasets in analytics', 'bucket a measure field', 'schedule a recipe', 'data prep transformation'. NOT for dataflow JSON and its node types — use admin/analytics-dataflow-development. NOT for tuning a slow or oversized dataset — use data/analytics-dataset-optimization."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "How do I join two datasets in a CRM Analytics recipe without losing rows?"
  - "I need to bucket a numeric field into tiers in Data Prep — which node do I use?"
  - "My recipe output has fewer rows than expected after adding a join"
  - "schedule a CRM Analytics recipe to run every night through the REST API"
  - "fix a Data Prep recipe that drops rows after a join node"
tags:
  - crm-analytics
  - recipe
  - data-prep
  - transformation
inputs:
  - "Source dataset names and their Salesforce object origins"
  - "Join keys and cardinality expectations (one-to-one, one-to-many)"
  - "Desired output columns, aggregation logic, and scheduling cadence"
outputs:
  - "Node-by-node recipe design with join type rationale"
  - "Bucket and formula node configuration guidance"
  - "Schedule Resource API call structure for recipe scheduling"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
runtime_orphan: true
runtime_orphan_reason: "No run-time agent covers CRM Analytics / Einstein Discovery. This skill was previously listed in audit-router's Mandatory Reads, but no audit-router classifier routes to it and report_dashboard's own scope excludes CRM Analytics migration, so the citation was decorative rather than load-bearing. Removed 2026-08-14 rather than left as a citation an agent never honoured. Re-wire when a CRM Analytics agent exists."
---

# Analytics Recipe Design

Use this skill to design CRM Analytics Data Prep recipes: choosing node types, configuring joins without silent row loss, building bucket dimensions, writing formula expressions, and scheduling the recipe through the Schedule resource. This skill does NOT cover SAQL query writing, dashboard lens design, or legacy dataflow JSON configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has CRM Analytics enabled and the user holds the Edit Dataset Recipes user permission (Analytics Platform Setup Guide, user permissions table). A user with only Recipes View Only (beta) can open the recipe editor but cannot create, change, or delete recipes.
- Identify whether the recipe replaces an existing dataflow. Recipes are the recommended path for new development, but existing dataflows are not migrated automatically. UNVERIFIED (2026-10-03): "recommended path as of Spring '25" is not stated in the guides read for this pass.
- Know the row counts of your input datasets. A recipe defined with `runMode` = `Full` reprocesses its whole input on every run. The Data Prep Recipe REST API also lists `Incremental` and `Streaming` run modes (API 57.0), so check which mode the recipe uses before budgeting run time.
- Clarify the join cardinality. An Inner join where the requirement is "keep every left-side row" drops unmatched rows, and that is the most common cause of unexplained row shrinkage.
- Confirm the Integration User can read every object and field the recipe extracts. A recipe job fails when the Integration User lacks permission on an extracted object or field.

---

## Questions to Ask Before Configuring

Ask these before opening the recipe canvas. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "For each join, must every row of the primary dataset survive, even with no match?" | Inner, Lookup, LeftOuter, and the other join types keep different rows (gotcha 1) | The join type per Join node, written down with its reason | Row counts that reconcile to the source instead of a silent shortfall found by a stakeholder |
| "How fresh must the output be, and which other dataflows and recipes already run in this org?" | Recipe and dataflow runs share a 60-run rolling 24-hour limit and a 3-concurrent-recipe cap (gotcha 3) | A schedule frequency that fits the run budget | Scheduled jobs that keep running instead of queuing or being refused at the daily limit |
| "Which users may see which rows of the output dataset?" | A security predicate set on the Output node applies only when the dataset is first created (gotcha 5) | The predicate or sharing-inheritance decision before the first run | Row-level security in place from day one, not retrofitted by editing the dataset |
| "Does the Integration User have read access to every object and field this recipe extracts?" | The job fails when the Integration User lacks a permission (gotcha 4) | A field list checked against the Integration User profile | A first run that succeeds instead of a failed job and a permission hunt |
| "Will this recipe be moved between orgs with Metadata API or a package?" | `WaveRecipe` carries a required `dataflow` ID and wildcard retrieval skips the related dataflow (gotcha 6) | A manifest that names the recipe and its dataflow explicitly | A deployment that brings the whole recipe, not an orphaned definition |
| "Is any formula copied from a SAQL lens?" | Recipe formulas use the `Sql` or `Legacy` expression type, not SAQL (gotcha 7) | Formulas written for the recipe engine | Formula nodes that validate on save instead of failing at run time |

What a proper configuration adds over "just building the recipe": output row counts you can explain, a schedule that fits the org's run limits, and row-level security that exists before anyone opens the dataset.

---

## Core Concepts

### Recipe Node Types

A Data Prep recipe is a directed graph of typed nodes. In the REST representation each node has an `action` (for example `load`, `filter`, `save`), a `parameters` object, and a `sources` list naming upstream nodes.

| Node | Role |
|---|---|
| **Load** | Reads a registered dataset or connected object into the recipe graph. Every recipe starts with at least one Load node. |
| **Filter** | Applies row-level inclusion or exclusion predicates. Reduces row count without changing schema. |
| **Join** | Combines two input streams on one or more key fields. Join type controls how unmatched rows are handled. |
| **Bucket** | Creates a new categorical column by assigning rows to named buckets. The API has measure, dimension, and date bucket inputs. |
| **Formula** | Adds a computed column. The formula parameters declare an expression type of `Sql` or `Legacy`. |
| **Append** | Unions two inputs with compatible schemas. Rows from both inputs are preserved. |
| **Aggregate** | Groups rows and computes aggregations. Reduces row count to one row per group. |
| **Flatten** | Expands a hierarchical dataset (commonly a role hierarchy) into a flat structure. |
| **Output (save)** | Writes the result to a named CRM Analytics dataset. The save node's dataset `label` is the name users see in Analytics Studio. |

### Join Types and Row Preservation

The Data Prep Recipe REST API's `JoinParametersInput.joinType` accepts seven values. Choosing the wrong one is the most frequent cause of silent data loss in recipes.

| Join Type | Left Rows | Right Rows | Typical Use Case |
|---|---|---|---|
| **Inner** | Matched only | Matched only | Intersection: only rows that exist in both inputs |
| **LeftOuter** | All | Matched only | Enrich the left input; unmatched right rows discarded |
| **RightOuter** | Matched only | All | Enrich the right input; unmatched left rows discarded |
| **Outer** | All | All | Full merge; unmatched rows on either side preserved |
| **Lookup** | All | Matched columns added | Enrich the left input with right-side columns; preserves every left row |
| **MultiValueLookup** | All | Multiple matched values | Left row enriched with every matching right value |
| **Cross** | Every combination | Every combination | Cartesian product; row count multiplies |

**Lookup vs Inner** is the critical distinction. Lookup keeps every left-side row and fills right-side columns where a match exists. Inner drops any left-side row with no match. If the requirement is "show all accounts and add owner details where available", use Lookup. UNVERIFIED (2026-10-03): the "up to 5 key fields" limit for Lookup is not in the REST API guide.

### Bucket Node Configuration

A Bucket node adds a new column by classifying an existing field into labeled groups. The bucket type must match the source field kind:

- **Measure bucket** classifies numeric ranges (for example Revenue below 10,000 as "SMB").
- **Dimension bucket** classifies discrete string values into groups (for example "CA" and "NY" as "West"). Unmatched values fall into a configurable "Other" bucket.
- **Date bucket** classifies date fields into calendar periods.

The output is a new column. The source field remains in the schema unless a later node removes it.

### Formula Node Expression Language

Formula nodes are not SAQL. The REST API's `FormulaParametersInput.expressionType` is `Sql` or `Legacy`, and SQL formula fields declare a result type of `Text`, `Number`, `DateOnly`, `DateTime`, or `Multivalue`. A Formula node placed before an Aggregate node works on row-level data; to compute on a SUM or COUNT, place the Aggregate node first.

UNVERIFIED (2026-10-03): the function names this skill previously listed (`CONCAT()`, `LEFT()`, `IF()`, `CASE()`, `ISNULL()`, `BLANKVALUE()`, `DATE()`, `YEAR()`) are not documented in the Data Prep Recipe REST API guide. The function reference lives only on help.salesforce.com, which did not fetch. Validate every expression in the formula editor before relying on it.

---

## Common Patterns

### Pattern: Lookup Enrichment Without Losing Rows

**When to use:** A primary fact dataset (Opportunities) needs descriptive columns from a secondary dataset (Accounts) without dropping Opportunity rows that lack an Account match.

**How it works:**
1. Load the primary dataset (Opportunities).
2. Load the secondary dataset (Accounts).
3. Add a Join node with `joinType` = `Lookup`.
4. Set `leftKeys` to `AccountId` and `rightKeys` to `Id`.
5. Keep only the right-side columns you need (for example `Industry`, `AnnualRevenue`).
6. Connect to an Output node.

Unmatched Opportunity rows appear in the output with null values for the added columns. They are not dropped.

### Pattern: Tiered Dimension via Measure Bucket

**When to use:** A numeric measure (Annual Revenue) needs to become a groupable dimension for dashboard filtering.

**How it works:**
1. Load the dataset containing the numeric field.
2. Add a Bucket node with source field type Measure.
3. Define ranges and labels: 0 to 9,999 as "SMB"; 10,000 to 99,999 as "Mid-Market"; 100,000 and above as "Enterprise".
4. Name the output column (for example `Revenue_Tier`).
5. Connect downstream to Output or Aggregate.

### Pattern: Schedule and Run a Recipe Through the REST API

**When to use:** A recipe must refresh on a cadence, or an external scheduler must start it.

**How it works:** The recipe resource (`GET /wave/recipes/<recipeId>?format=R3`) returns `scheduleAttributes`, but a schedule is created, changed, or removed only through the Schedule resource:

```bash
# Create or replace the schedule (weekly, Monday and Thursday, 00:45 Los Angeles time)
curl -X PUT "$INSTANCE/services/data/v67.0/wave/asset/05vB0000000xxxxxxx/schedule" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"frequency":"weekly","daysOfWeek":["Monday","Thursday"],"time":{"hour":0,"minute":45,"timeZone":"America/Los_Angeles"}}'

# Read the schedule
curl "$INSTANCE/services/data/v67.0/wave/asset/05vB0000000xxxxxxx/schedule" -H "Authorization: Bearer $TOKEN"

# Run now: the dataflowId is the recipe's targetDataflowId (starts with 02KB), not the recipe Id
curl -X POST "$INSTANCE/services/data/v67.0/wave/dataflowjobs" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"dataflowId":"02KB000000xxxxxxxx","command":"start"}'
```

`frequency` takes `hourly`, `weekly`, `monthly`, `monthlyrelative`, or `eventdriven`; there is no cron expression. `DELETE` on the same Schedule URL removes the schedule. The full worked example, including the recipe metadata and manifest, is in `references/metadata-examples.md`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Enrich the left dataset and keep every left row | Lookup join | Preserves every left-side row; adds right-side columns where matched |
| Keep only rows present in both datasets | Inner join | Intersection semantics; unmatched rows on either side are dropped |
| Classify a numeric measure into named tiers | Measure Bucket node | Produces a new column without altering the source field |
| Add a computed column | Formula node, `Sql` expression type | Recipe formulas are not SAQL |
| Combine two datasets with the same schema | Append node | All rows from both inputs are preserved |
| Refresh on a cadence | `PUT /wave/asset/<recipeId>/schedule` | The Schedule resource owns schedules; `scheduleAttributes` on the recipe is read-back only |
| Run after the Salesforce Local sync finishes | Event-based schedule (`"frequency":"eventdriven"`) | Event-based schedules apply to dataflows and recipes, with at most 5 dependent jobs |
| Large inputs (millions of rows) | Push Filter nodes as early as possible; check `runMode` | A `Full` run reprocesses the whole input |

---

## Recommended Workflow

1. **Gather requirements and answer the questions above.** List input datasets, join keys, cardinality, output columns, aggregation logic, row-level security, and refresh cadence. Confirm the user has Edit Dataset Recipes and the Integration User can read every extracted field.
2. **Design the node graph on paper.** Load, then Filter early, then Join, then Bucket or Formula, then Aggregate if needed, then Output. Write the join type and its reason for every Join node.
3. **Build the nodes in Data Prep.** For Join nodes set the keys and type. For Bucket nodes match the bucket type to the field kind. For Formula nodes use the recipe expression language and validate in the editor. Set the security predicate on the Output node before the first run.
4. **Run once and reconcile row counts.** Compare each Load node's input count with the output dataset count. Unexplained shrinkage almost always means an Inner join where Lookup or LeftOuter was intended. Remember that the editor preview runs as the Security User and shows only rows the previewing user can access.
5. **Schedule through the Schedule resource.** `PUT /wave/asset/<recipeId>/schedule` with a `frequency` body. Check the org's 60-run rolling 24-hour budget first.
6. **Package and promote.** Retrieve `WaveRecipe` together with its `WaveDataflow` by name (wildcard retrieval omits the dataflow). Deploy, then confirm the schedule in the target org, because schedules are not part of the recipe metadata. See `references/metadata-examples.md`.

---

## Review Checklist

- [ ] Every Join node has an explicitly documented type
- [ ] Joins that must preserve left-side rows use Lookup or LeftOuter, not Inner
- [ ] Output row count reconciled against input dataset counts after the first run
- [ ] Bucket nodes match the source field kind (Measure / Dimension / Date)
- [ ] Formula nodes validated in the recipe editor; no SAQL functions
- [ ] Security predicate set on the Output node before the first run, or sharing inheritance decided
- [ ] Schedule created with `PUT /wave/asset/<recipeId>/schedule` and fits the 60-run daily budget
- [ ] Integration User can read every extracted object and field
- [ ] Manifest names both the `WaveRecipe` and its `WaveDataflow`

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Inner join drops unmatched left rows | Output is short and the run still reports success |
| 2 | Schedules live on `/wave/asset/<id>/schedule` | Cron bodies and `/wave/recipes/<id>/schedules` calls do nothing useful |
| 3 | 60 runs per rolling 24 hours, 3 concurrent recipe runs | Hourly schedules starve other jobs; at the limit nothing runs |
| 4 | Integration User permissions gate extraction | The job fails on the first unreadable field |
| 5 | Output-node security predicate applies at creation only | Later predicate edits in the recipe have no effect |
| 6 | `WaveRecipe` wildcard retrieval omits the dataflow | A deploy carries an incomplete recipe |
| 7 | Formula expression type is `Sql` or `Legacy`, not SAQL | Copied lens expressions fail |
| 8 | Preview runs as the Security User | Preview counts differ from job output counts |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Recipe node graph design | Written node sequence with join type rationale for each Join node |
| Schedule request | `PUT /wave/asset/<recipeId>/schedule` body with `frequency`, days, and time |
| Output dataset schema | Expected columns, types, row count estimate, and security predicate |
| Deployment manifest | `package.xml` listing the `WaveRecipe` and its `WaveDataflow` |

---

## Related Skills

- `admin/crm-analytics-app-creation`: use alongside this skill when the recipe is part of a net-new CRM Analytics app setup
- `admin/analytics-dashboard-design`: use after this skill when the output dataset feeds dashboard lenses and SAQL queries
