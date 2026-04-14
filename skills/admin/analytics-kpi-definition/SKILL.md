---
name: analytics-kpi-definition
description: "Use this skill to define, document, and validate KPI metrics for CRM Analytics — covering metric formula design, dimension selection, target-dataset modeling, benchmark setting, and the KPI register that must exist before any dashboard or lens is built. Trigger keywords: KPI definition CRM Analytics, analytics metric design, analytics target attainment, CRM Analytics measures vs dimensions, analytics benchmark. NOT for building CRM Analytics dashboards or lenses (use analytics/dashboard-design), SOQL report KPI design, or Marketing Cloud analytics KPI work."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "stakeholders disagree on how a KPI is calculated before building the analytics dashboard"
  - "need to define metric formulas and target values for CRM Analytics before development starts"
  - "analytics team needs to document which fields are measures vs dimensions for a dataset"
  - "KPI target attainment requires loading a separate targets dataset — how to model and join it"
  - "CRM Analytics recipe needs to know what calculations to apply before the dataset is published"
tags:
  - crm-analytics
  - kpi
  - metrics
  - analytics-requirements
  - analytics-kpi-definition
inputs:
  - "List of KPIs stakeholders need to track"
  - "Business definitions for each metric (what counts, what excludes)"
  - "Target values or benchmark sources"
  - "CRM Analytics dataset name and available fields"
outputs:
  - "KPI register with metric name, formula, dimension, target expression, and benchmark"
  - "Target dataset schema for loading attainment targets"
  - "SAQL snippet for KPI attainment calculation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# Analytics KPI Definition

This skill activates when a practitioner needs to define, document, and validate KPIs for CRM Analytics before any lens or dashboard is built. It produces a KPI register — the canonical artifact that specifies metric formulas, dimension groupings, target attainment models, and benchmark values — that the dashboard builder uses as the single source of truth.

---

## Before Starting

Gather this context before working on anything in this domain:

- KPI definition must happen before dashboard design. Building a lens before the KPI formula is agreed upon leads to re-work when stakeholders dispute the calculation method.
- CRM Analytics distinguishes measures from dimensions at the dataset level. A measure is a numeric field used in aggregation; a dimension is a categorical field used in grouping. This distinction is set when the dataset is configured and affects what aggregation functions are valid.
- The most common wrong assumption: practitioners conflate KPI definition (agreeing on the formula and target) with dashboard wiring (configuring the tile type and chart). These are separate activities — KPI definition is a pre-build requirements task.
- Target attainment in CRM Analytics is modeled by loading a separate targets dataset and joining it at query time via SAQL or recipe — it cannot be done by editing the source dataset in place.

---

## Core Concepts

### Measures vs Dimensions

CRM Analytics datasets have two field types that affect KPI modeling:
- **Measures** — numeric fields (Amount, Quantity, Revenue). Aggregation functions (sum, avg, count, max, min) apply. Used in KPI formulas.
- **Dimensions** — string/categorical fields (Stage, Owner, Region). Used in GROUP BY expressions. Cannot be summed or averaged.

A KPI formula must correctly identify which fields are measures (to aggregate) and which are dimensions (to group by). Using a dimension in a SUM() function produces a SAQL error.

### KPI Target Attainment Pattern

CRM Analytics does not support inline target values in a dataset. The canonical pattern:
1. Create a separate targets dataset with columns matching the KPI's dimension groupings (e.g., Owner, Region, Quarter) plus a Target value measure
2. Join the targets dataset to the actuals dataset at query time using SAQL cogroup or recipe join
3. Compute attainment as `actual / target * 100`

Target datasets must be updated on the same cadence as the reporting period (quarterly targets loaded quarterly). The join key between actuals and targets must be an exact string match — case differences cause nulls.

### Leakage and Proxy Field Risk

Einstein Discovery and CRM Analytics KPI definitions share a common pitfall: using fields that are causally downstream of the outcome (leakage) or fields that are proxies for the outcome (e.g., using Opportunity Close Date in a win-rate formula when Close Date is only populated on Closed Won/Lost records):
- A field filled in only after the outcome is known is a leakage risk for predictive KPIs
- For descriptive/historical KPIs, this is less of a concern but still affects filter logic

---

## Common Patterns

### Pattern: KPI Register

**When to use:** Before any CRM Analytics lens or dashboard is built — for every KPI stakeholders need.

**How it works:**
1. For each KPI: document the metric name, plain-English definition, aggregation formula (SUM/AVG/COUNT/RATIO), dimension(s) to group by, and the dataset + field path
2. Document target model: fixed value, external targets dataset join, or formula-derived
3. Document benchmark: industry benchmark, historical baseline, or threshold
4. Validate: confirm the formula fields are measures in the dataset (not dimensions)

**Why not the alternative:** Building lenses without a KPI register leads to multiple interpretations of the same metric, inconsistent calculation across dashboards, and rework when stakeholders reject the formula.

### Pattern: Target Dataset Schema Design

**When to use:** When any KPI requires attainment tracking (actual vs target).

**How it works:**
1. Define the granularity of targets: by Owner, by Region, by Quarter, or some combination
2. Create a targets dataset schema with columns: all grouping dimensions + Target_Amount (or equivalent measure)
3. Define the load schedule: targets are uploaded via CSV or External Data API on the same cadence as reporting periods
4. Document the SAQL join key: the exact field name and format used to join actuals to targets

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| KPI is a simple sum or count from one dataset | SAQL measure aggregation in lens | Straightforward — no target dataset needed unless attainment tracking required |
| KPI requires target vs actual comparison | Separate targets dataset + SAQL cogroup | CRM Analytics cannot store targets inline in actuals dataset |
| KPI grouping field is a string (Region, Owner name) | Use as dimension in GROUP BY | String fields are dimensions and cannot be aggregated |
| Stakeholders use different formulas for the same metric | KPI register with signed-off definition before build | Locking the formula before build prevents mid-project disputes |
| KPI involves multiple datasets (e.g., Opp + Account data) | Recipe join before dataset publish | Join in recipe so the output dataset has all needed fields before KPI formula is applied |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Collect all KPIs stakeholders mention — even informally named ones. Document every metric and the person requesting it.
2. For each KPI: write a plain-English definition that specifies what counts (included criteria), what excludes (excluded criteria), the time period, and the granularity.
3. Map each KPI to CRM Analytics dataset fields: identify which field is the measure to aggregate, which fields are dimensions for grouping, and confirm field types in the dataset configuration.
4. Identify KPIs that require target attainment: for these, design the targets dataset schema — dimension columns matching the KPI grouping, Target measure column, join key to actuals.
5. Document SAQL formula sketch for each KPI: `sum(Measure) groupby [DimensionField]` with target join pattern if applicable.
6. Get stakeholder sign-off on the KPI register before any lens or dashboard is built — record who approved each formula and target definition.
7. Hand off the signed KPI register to the dashboard builder as the authoritative specification.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every KPI has a plain-English definition with inclusion/exclusion criteria
- [ ] Measure vs dimension classification confirmed for each field used in formulas
- [ ] Target attainment model specified (fixed value / targets dataset / formula)
- [ ] Targets dataset schema designed for all KPIs requiring attainment tracking
- [ ] SAQL formula sketch validated against dataset field types
- [ ] Stakeholder sign-off recorded on KPI register
- [ ] No KPI left as "to be confirmed" before dashboard build starts

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Targets dataset join key must be exact string match** — When joining a targets dataset to an actuals dataset in SAQL, the join key field values must be an exact string match including case. A targets dataset with `Owner = "John Smith"` will not join to an actuals dataset with `Owner = "john smith"`. Null results appear silently — KPIs show actual values with no target column. Document the exact string format for all join keys in the KPI register.
2. **Dimensions cannot be aggregated — SAQL error at runtime** — Using a dimension field in a SUM(), AVG(), or COUNT(Distinct) aggregation produces a SAQL error at lens runtime. Practitioners who haven't checked the dataset schema assume all numeric-looking fields are measures — but fields configured as dimensions in the dataset editor cannot be aggregated regardless of their data type.
3. **Fields below ~70% fill rate are silently dropped from Einstein Discovery** — If CRM Analytics KPIs are later used in Einstein Discovery models, fields below approximately 70% fill rate are silently excluded from feature selection. KPI definitions that depend on sparse fields should document the fill rate risk.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| KPI register | Signed-off table of metric name, plain-English definition, formula, dimensions, target model, and benchmark |
| Targets dataset schema | Column definitions for the external targets dataset to support attainment tracking |
| SAQL formula sketches | Per-KPI SAQL query patterns for developer reference during lens/recipe build |

---

## Related Skills

- `admin/analytics-requirements-gathering` — upstream skill: gather analytics requirements before defining KPIs
- `data/saql-query-development` — use to implement SAQL formulas from the KPI register
- `admin/marketing-reporting-requirements` — companion skill for marketing-specific KPI definition
