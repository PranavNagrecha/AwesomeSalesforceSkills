---
name: ai-training-data-preparation
description: "Use this skill when preparing data for Salesforce Einstein ML features: Einstein Discovery story creation, Einstein Prediction Builder model setup, feature field selection, outcome definition, data quality thresholds, and leakage detection. Trigger keywords: Einstein Discovery data requirements, training data for Einstein, ML feature engineering, Einstein Prediction Builder data prep, AI model training data. NOT for generic CRM data quality management, Data Cloud ingestion pipeline setup, or standard CRM Analytics dashboard analytics."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "how do I prepare my Salesforce data for Einstein Discovery story creation"
  - "my Einstein Prediction Builder model has low accuracy — what data quality issues should I check"
  - "what is the minimum number of records I need to train an Einstein Discovery model"
  - "which fields should I exclude to avoid data leakage in my Einstein ML model"
  - "how do I choose between Einstein Discovery and Einstein Prediction Builder for my use case"
  - "fill rate below threshold is causing Einstein to drop fields from my model"
tags:
  - einstein
  - machine-learning
  - einstein-discovery
  - prediction-builder
  - data-quality
  - ai
inputs:
  - "Salesforce object and fields intended as the ML training dataset"
  - "Outcome field (the value the model should predict)"
  - "License context: CRM Analytics license available or not"
  - "Minimum row count and data completeness metrics per field"
outputs:
  - "Feature field selection checklist with fill-rate thresholds"
  - "Outcome field definition and leakage audit"
  - "Data preparation checklist for Einstein Discovery story or EPB model"
  - "Decision matrix: Einstein Discovery vs Einstein Prediction Builder"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# AI Training Data Preparation

Use this skill when setting up data for Salesforce Einstein ML models — specifically Einstein Discovery (story-based ML requiring CRM Analytics license) and Einstein Prediction Builder (binary classification, no CRM Analytics license required). This skill covers outcome field design, fill-rate analysis, leakage detection, and feature field curation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which Einstein product is in scope: Einstein Discovery (regression, multi-class, binary — requires CRM Analytics license) or Einstein Prediction Builder (binary only, no CRM Analytics license)?
- What is the exact outcome field: binary yes/no, a numeric value, or a category?
- What is the row count and fill rate for the intended training object?
- Are any candidate predictor fields derived from post-outcome data (leakage risk)?

---

## Core Concepts

### Minimum Row and Fill-Rate Thresholds

Einstein Discovery requires a **minimum of 400 rows** where the outcome field is populated. Fields with a fill rate below approximately **70%** are silently dropped from feature selection during story creation — the platform does not warn you that a field was excluded. If a key predictor has low fill rate, the model trains without it and accuracy degrades without explanation.

Einstein Prediction Builder requires at least **200 records** where the outcome condition is true and at least 200 where it is false, with a recommended minimum of 400 total records for stable predictions.

### Outcome Field Design and Leakage

The outcome field must represent a value that was **unknown at the time the predictors were captured**. Fields that are created or populated as a direct result of the outcome (e.g., a "Closed Won Reason" field that only exists after an opportunity closes) are proxy fields and introduce leakage. Models trained with leakage show inflated accuracy metrics during training but fail in production because the proxy fields are unavailable at prediction time.

Einstein Discovery flags predictors with over **30% correlation to the outcome** as potential leakage candidates and marks them for scrutiny in story settings. These fields must be reviewed manually — high correlation alone does not confirm leakage, but undocumented high-correlation fields are a red flag.

### Einstein Discovery vs Einstein Prediction Builder

These are distinct products with distinct data paths:

- **Einstein Prediction Builder (EPB)**: Binary outcomes only (e.g., "Will this opportunity close?"), works on standard and custom objects, no CRM Analytics license required. Training begins automatically when field selection is saved in Setup.
- **Einstein Discovery**: Supports regression (continuous numeric), binary, and multi-class outcomes. Requires a CRM Analytics license. Stories are built in Analytics Studio. Training pipeline is a separate batch job that must be explicitly initiated.

The data preparation steps differ: EPB reads directly from Salesforce objects; Einstein Discovery requires the data to be accessible in CRM Analytics via a Data Sync or dataflow. Fields excluded from the CRM Analytics dataset cannot be included in an Einstein Discovery story.

---

## Common Patterns

### Pattern: Outcome Field Audit Before Story Creation

**When to use:** Before creating any Einstein Discovery story or enabling an EPB prediction.

**How it works:**
1. Run a SOQL aggregate query to count rows where outcome field is NOT NULL vs total rows.
2. Calculate fill rate: `COUNT(outcome_field) / COUNT(Id)`. If below 80%, investigate data entry gaps.
3. Check whether the outcome field is populated at the same time as predictors or only after the event you are predicting — if populated after, it is a leakage candidate.
4. For EPB: verify binary balance. If the positive class is less than 5% of total records, the model will have low precision for positive predictions.

**Why not skip this:** Einstein Discovery's silent field-dropping means a 50% fill-rate predictor disappears from the feature set with no error. You will not know it is missing unless you explicitly audit field inclusion in story settings after training.

### Pattern: Feature Field Selection Matrix

**When to use:** When curating which fields to include as predictors in a story or EPB model.

**How it works:** Build a field inventory with three columns: (1) fill rate, (2) business meaning (does the field exist before or after the outcome?), (3) correlation-to-outcome suspicion level. Exclude: post-outcome fields, formula fields that derive directly from the outcome, and fields with fill rate below 70%. Include: fields populated during creation or progression of the record, not at closure.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Binary yes/no outcome, no CRM Analytics license | Einstein Prediction Builder | EPB runs on native Salesforce objects; no Analytics Studio needed |
| Continuous (regression) or multi-class outcome | Einstein Discovery only | EPB supports binary classification only |
| CRM Analytics license available, need explainability | Einstein Discovery | Story UI provides feature contribution, what-if analysis |
| Training data has < 400 outcome-positive rows | Fix data volume first | Both products need minimum rows; results below threshold are unreliable |
| Key predictor field has < 70% fill rate | Improve fill rate via validation rules | Field will be dropped silently by Einstein Discovery |
| Predictor field correlated > 30% with outcome | Review for leakage; exclude if post-outcome | High correlation on a post-outcome proxy inflates model accuracy artificially |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm product scope** — Determine whether Einstein Discovery or EPB is required based on outcome type (binary vs regression/multi-class) and license availability.
2. **Audit outcome field** — Run a fill-rate check on the outcome field. Verify it is populated before (not because of) the predicted event. Flag any proxy leakage candidates.
3. **Inventory predictor fields** — List all candidate feature fields. Check fill rate for each. Mark fields below 70% as at-risk. Mark fields populated post-outcome as leakage candidates.
4. **Check minimum row counts** — Count rows where outcome is populated. For EPB, count positive-class and negative-class rows separately.
5. **Remediate gaps** — Fix fill-rate issues before enabling training. Use required fields, validation rules, or process automation to enforce data completeness on key predictors.
6. **Configure training** — For EPB: enable in Setup and select fields (trains automatically on save). For Einstein Discovery: confirm data is in CRM Analytics via Data Sync, create story, review field inclusion list after training.
7. **Validate model output** — Review confusion matrix, precision/recall, and feature contribution. If a known-important field is absent, check whether it was silently dropped.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Outcome field fill rate is above 80% (minimum 400 rows with outcome populated)
- [ ] Outcome field is populated before (not as a result of) the predicted event
- [ ] No post-outcome proxy fields included as predictors
- [ ] All key predictor fields have fill rate above 70%
- [ ] For EPB: positive-class and negative-class records are both >= 200
- [ ] For Einstein Discovery: data is accessible in CRM Analytics dataset
- [ ] After training: confirmed key predictor fields appear in feature contributions list

---

## Salesforce-Specific Gotchas

1. **Silent field dropping below ~70% fill rate** — Einstein Discovery silently excludes fields with low fill rates from feature selection. There is no error or warning in the story UI. You only discover this by checking the field list in story settings after training.

2. **EPB trains automatically on save** — Unlike Einstein Discovery, EPB begins training immediately when you save field selection in Setup. If your data quality is not ready, a bad model becomes immediately active.

3. **Einstein Discovery requires CRM Analytics data access** — Fields must be in the CRM Analytics dataset. If you add a new field to the Salesforce object after Data Sync is configured, you must update the dataflow or recipe to include it before it becomes available for story training.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field fill-rate audit | SOQL-based fill rate per candidate predictor field |
| Outcome leakage checklist | Documents whether each high-correlation field was populated before or after the predicted event |
| EPB vs Einstein Discovery decision record | Documents which product was selected and why |

---

## Related Skills

- `agentforce/einstein-discovery-development` — Use for story creation, model deployment, and Einstein Discovery REST API integration after data preparation is complete
- `agentforce/einstein-prediction-builder` — Use for EPB model configuration and deployment in Setup UI
- `data/analytics-data-preparation` — Use for CRM Analytics XMD metadata management affecting which fields appear in Einstein Discovery stories
- `admin/analytics-dataset-management` — Use for dataset scheduling and row limit management determining training data freshness
