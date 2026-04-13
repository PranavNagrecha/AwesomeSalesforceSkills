---
name: analytics-recipe-design
description: "Use this skill when designing or building CRM Analytics Data Prep recipes — including node selection, join patterns, bucket field configuration, formula expressions, and scheduling. Triggers: 'build a recipe', 'join datasets in analytics', 'bucket a measure field', 'schedule a recipe', 'data prep transformation'. NOT for SAQL queries, dashboard design, or dataflow JSON authoring."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "How do I join two datasets in a CRM Analytics recipe without losing rows?"
  - "I need to bucket a numeric field into tiers in Data Prep — which node do I use?"
  - "My recipe output has fewer rows than expected after adding a join"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Recipe Design

Use this skill to design CRM Analytics Data Prep recipes: selecting the right node types, configuring joins without silent row loss, building bucket dimensions, writing formula expressions, and wiring up recipe schedules through the Schedule Resource API. This skill does NOT cover SAQL query writing, dashboard lens design, or legacy dataflow JSON configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has CRM Analytics enabled and the user has the Analytics Cloud - Analytics User or CRM Analytics Plus User permission set.
- Identify whether the recipe replaces an existing dataflow — recipes are the recommended path for new development as of Spring '25, but existing dataflows are not automatically migrated.
- Know the row counts of your input datasets. Recipes reprocess the full input on every run — there is no native incremental load support, so large inputs have a direct impact on run time and quota consumption.
- Clarify the join cardinality. Using an Inner join when the requirement is "preserve all left-side rows" silently drops unmatched rows and is the single most common source of unexplained row count shrinkage.

---

## Core Concepts

### Recipe Node Types

A CRM Analytics recipe is a directed acyclic graph of typed nodes on a visual canvas in Data Prep. Every node has exactly one function:

| Node | Role |
|---|---|
| **Load** | Reads a registered dataset or connected object into the recipe graph. Every recipe starts with at least one Load node. |
| **Filter** | Applies row-level inclusion/exclusion predicates. Reduces row count without changing schema. |
| **Join** | Combines two input streams on one or more key fields. Join type controls how unmatched rows are handled — see Join Types below. |
| **Bucket** | Creates a new categorical dimension column by assigning rows to named buckets based on value ranges or discrete values. Typed by field kind: Measure, Dimension, or Date. |
| **Formula** | Adds a computed column using the recipe expression language (not SAQL). Supports arithmetic, string, date, and conditional functions. |
| **Append** | Unions two datasets with compatible schemas (like SQL UNION ALL). Rows from both inputs are preserved. |
| **Aggregate** | Groups rows and computes aggregations (SUM, COUNT, MIN, MAX, AVG). Reduces row count to one row per group. |
| **Flatten** | Expands a hierarchical dataset (commonly used with Salesforce role hierarchies) into a flat structure. |
| **Output** | Writes the result of the preceding node graph to a named CRM Analytics dataset. A recipe must have at least one Output node. |

### Join Types and Row Preservation

The Join node supports six types. Choosing the wrong type is the most frequent cause of silent data loss in recipes:

| Join Type | Left Rows | Right Rows | Typical Use Case |
|---|---|---|---|
| **Inner** | Matched only | Matched only | Intersection — only rows that exist in both datasets |
| **LeftOuter** | All | Matched only | Enrich left dataset; unmatched right rows discarded |
| **RightOuter** | Matched only | All | Enrich right dataset; unmatched left rows discarded |
| **Outer** | All | All | Full merge; unmatched rows on either side preserved |
| **Lookup** | All | Matched columns added | Enrich left dataset by looking up right-side columns; preserves every left row |
| **MultiValueLookup** | All | Multiple matched rows expanded | Left row duplicated for each matching right row |

**Lookup vs Inner** is the critical distinction: Lookup preserves all left-side rows and appends matched right-side column values (up to 5 key fields). Inner drops any left-side row that has no match in the right dataset — silently. If the requirement is "show all accounts and add owner details where available," use Lookup, not Inner.

### Bucket Node Configuration

A Bucket node adds a new dimension column by classifying an existing field into labeled groups. The bucket type must match the source field kind:

- **Measure bucket** — classifies numeric ranges (e.g., Revenue < 10000 → "SMB", 10000–99999 → "Mid-Market", >= 100000 → "Enterprise"). Ranges are inclusive/exclusive as configured.
- **Dimension bucket** — classifies discrete string values into groups (e.g., "CA", "NY" → "West"; "TX", "FL" → "South"). Unmatched values fall into a configurable "Other" bucket.
- **Date bucket** — classifies date fields into calendar periods (e.g., fiscal quarter, calendar year).

The output is always a new string dimension column. The source field remains in the schema unless explicitly removed by a subsequent node.

### Formula Node Expression Language

Formula nodes use the CRM Analytics recipe expression language, which is syntactically distinct from SAQL. It supports:

- Arithmetic: `+`, `-`, `*`, `/`
- String functions: `CONCAT()`, `LEFT()`, `RIGHT()`, `TRIM()`, `UPPER()`, `LOWER()`
- Date functions: `DATE()`, `YEAR()`, `MONTH()`, `DAY()`, `NOW()`
- Conditional: `IF(condition, true_value, false_value)`, `CASE()`
- Null handling: `ISNULL()`, `BLANKVALUE()`

Formula results can be typed as Text, Number, or Date. Formulas cannot reference aggregated values — that requires an Aggregate node upstream.

---

## Common Patterns

### Pattern: Lookup Enrichment — Add Context Columns Without Losing Rows

**When to use:** You have a primary fact dataset (e.g., Opportunities) and want to add descriptive columns from a secondary dataset (e.g., Account details) without dropping any Opportunity rows that may lack an Account match.

**How it works:**
1. Load the primary dataset (Opportunities).
2. Load the secondary dataset (Accounts).
3. Add a Join node, set type to **Lookup**.
4. Configure the join key (e.g., `AccountId` = `Id`).
5. Select only the right-side columns you need (e.g., `Industry`, `AnnualRevenue`).
6. Connect to an Output node.

Unmatched Opportunity rows (where `AccountId` is null or absent in the Account dataset) will appear in the output with null values for the added columns — they are never dropped.

**Why not Inner:** An Inner join silently drops every Opportunity without a matching Account, causing row count shrinkage that is invisible unless you compare input and output counts explicitly.

### Pattern: Tiered Dimension via Measure Bucket

**When to use:** A numeric measure (e.g., Annual Revenue) needs to become a groupable dimension for dashboard filtering or segment analysis.

**How it works:**
1. Load the dataset containing the numeric field.
2. Add a **Bucket** node; select source field type = Measure.
3. Define ranges and labels:
   - 0–9,999 → "SMB"
   - 10,000–99,999 → "Mid-Market"
   - 100,000+ → "Enterprise"
4. Name the output column (e.g., `Revenue_Tier`).
5. Connect downstream to Output or Aggregate.

The new `Revenue_Tier` column appears in the dataset schema as a dimension. It can be used as a grouping field in SAQL queries and dashboard lenses without any changes to the query layer.

### Pattern: Recipe Scheduling via Schedule Resource API

**When to use:** You need a recipe to refresh on a defined cadence (hourly, daily, weekly).

**How it works:** Recipe scheduling is NOT configured inside the recipe definition itself. It is managed through a separate Schedule Resource API call:

```
POST /services/data/v62.0/wave/recipes/{recipeId}/schedules
Content-Type: application/json

{
  "scheduleType": "cron",
  "cronExpression": "0 0 3 * * ?",
  "timeZone": "America/Los_Angeles"
}
```

To retrieve the current schedule:
```
GET /services/data/v62.0/wave/recipes/{recipeId}/schedules
```

To delete a schedule:
```
DELETE /services/data/v62.0/wave/recipes/{recipeId}/schedules
```

The `recipeId` is the `id` field from the recipe resource (`/wave/recipes/{id}`). Schedules can also be managed in the Analytics Studio UI under the recipe's scheduling panel, but the API is required for automation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to enrich left dataset, preserving all left rows | Lookup join | Preserves every left-side row; adds right-side columns where matched |
| Need only rows present in both datasets | Inner join | Intersection semantics; rows without a match in either dataset are dropped |
| Need to classify a numeric measure into named tiers | Measure Bucket node | Produces a new categorical dimension column without altering source field |
| Need to add a computed column using field arithmetic | Formula node | Recipe expression language supports arithmetic, string, date, and conditional functions |
| Need to combine two datasets with the same schema | Append node | SQL UNION ALL equivalent; all rows from both inputs are preserved |
| Need to schedule a recipe refresh | Schedule Resource API POST | Schedules are external to the recipe definition; must be set via API or UI scheduling panel |
| Large input datasets (millions of rows) | Minimize upstream node count; push Filter nodes as early as possible | Recipes reprocess full input on every run; early filtering reduces work for downstream nodes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather requirements** — Identify all input datasets, join keys, cardinality expectations, required output columns, aggregation logic, and refresh schedule. Confirm the org has CRM Analytics enabled and the user has sufficient permissions.
2. **Design the node graph on paper** — Map out the recipe DAG before opening the canvas: Load nodes → Filter (if row reduction is needed early) → Join → Bucket/Formula → Aggregate (if needed) → Output. Identify join types explicitly for each Join node.
3. **Validate join type selection** — For every Join node, confirm whether all left-side rows must be preserved. If yes, use Lookup or LeftOuter, not Inner. Document the join type rationale in the recipe description field.
4. **Build and configure nodes in Data Prep** — Open the recipe canvas in Analytics Studio. Add nodes in the designed order. For Join nodes, configure key fields (up to 5 for Lookup). For Bucket nodes, match the bucket type to the source field kind (Measure, Dimension, or Date). For Formula nodes, write expressions in the recipe expression language, not SAQL.
5. **Run the recipe and verify row counts** — After the first run, compare input dataset row counts against the output dataset row count. Unexplained shrinkage almost always indicates an Inner join where a Lookup or LeftOuter was needed.
6. **Configure the schedule** — If a refresh cadence is required, POST to `/wave/recipes/{recipeId}/schedules` with the desired cron expression. Do not look for a schedule field inside the recipe definition — it does not exist there.
7. **Validate the output dataset** — Confirm that all expected columns are present, bucket labels are correct, formula outputs match expected values on sample rows, and the dataset is accessible in Analytics Studio under the correct app.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Join node has an explicitly documented type — no undocumented default joins in the graph
- [ ] All joins that must preserve left-side rows use Lookup or LeftOuter, not Inner
- [ ] Output row count matches expected count (compared against input dataset counts)
- [ ] Bucket nodes match source field kind (Measure / Dimension / Date)
- [ ] Formula nodes use recipe expression language syntax, not SAQL
- [ ] Recipe schedule is configured via Schedule Resource API or Analytics Studio scheduling panel, not embedded in the recipe definition
- [ ] Recipe has been run at least once and the output dataset is visible in Analytics Studio

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Inner join silently drops unmatched rows** — Unlike a Lookup, an Inner join removes any row from the left dataset that has no matching row in the right dataset. There is no warning, no error, and no row count diff displayed on the canvas. The only way to detect this is to compare input and output dataset row counts after a run. Use Lookup when the intent is "enrich, not filter."
2. **Recipe scheduling is a separate API resource** — There is no `schedule` field inside the recipe definition JSON. Schedules are managed exclusively through the `/wave/recipes/{recipeId}/schedules` endpoint (or the Analytics Studio UI). Attempting to embed scheduling in the recipe body has no effect.
3. **Formula nodes cannot reference post-aggregate values** — A Formula node placed before an Aggregate node operates on raw row-level data. If a formula needs to reference a SUM or COUNT, the Aggregate node must come first, and the Formula node must be placed downstream of it.
4. **Recipes do not support native incremental loads** — Every recipe run reprocesses the full input dataset from scratch. There is no built-in delta or watermark mechanism. For large datasets, the full run time and quota cost must be budgeted accordingly. Incremental patterns require custom filtering logic (e.g., a Filter node on a date field combined with an Append node to union with a previously stored output dataset).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Recipe node graph design | DAG diagram or written node sequence with join type rationale for each Join node |
| Schedule Resource API call | POST body for `/wave/recipes/{recipeId}/schedules` with cron expression and timezone |
| Output dataset schema | List of expected columns, types, and row count estimate post-transformation |

---

## Related Skills

- `crm-analytics-app-creation` — Use alongside this skill when the recipe is part of a net-new CRM Analytics app setup (app creation, dataset registration, permission assignment)
- `analytics-dashboard-design` — Use after this skill when the recipe output dataset needs to be wired into dashboard lenses and SAQL queries
