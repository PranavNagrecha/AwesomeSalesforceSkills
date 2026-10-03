---
name: ai-training-data-preparation
description: "Judging whether Salesforce data is fit to train an Einstein model: feature field selection, outcome definition, data quality and fill-rate thresholds, leakage detection. Trigger keywords: Einstein Discovery data requirements, training data for Einstein, ML feature engineering, Einstein Prediction Builder data prep, AI model training data. NOT for authoring the story in CRM Analytics Studio — use admin/einstein-discovery-setup. NOT for setting up the prediction itself — use agentforce/einstein-prediction-builder."
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
  - "we're having issues with machine learning"
  - "audit a training extract for leakage and fill rate before building an Einstein Studio predictive model"
  - "check whether my CSV has enough rows and columns to train a model in Model Builder"
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
  - "A CSV extract of the training data, for the bundled checker"
outputs:
  - "Feature field selection checklist with fill-rate thresholds"
  - "Outcome field definition and leakage audit"
  - "Data preparation checklist for Einstein Discovery story or EPB model"
  - "Decision matrix: Einstein Discovery vs Einstein Prediction Builder"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# AI Training Data Preparation

Use this skill when setting up data for a Salesforce predictive model: an Einstein Studio predictive model built in Model Builder on Data Cloud data, an Einstein Discovery story in CRM Analytics, or an Einstein Prediction Builder prediction on Salesforce objects. It covers outcome design, fill rates, leakage, cardinality, and class balance, and ships a checker that audits a training extract before anything trains.

Grounding note (2026-10-03): the numeric requirements that a fetched official source states belong to Einstein Studio predictive models (Data Cloud guide, "Create Predictive AI Models From Scratch"). The Einstein Discovery and Prediction Builder thresholds in earlier versions of this skill come from Salesforce Help pages, which do not fetch; they are kept below with UNVERIFIED markers.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which product is in scope: Einstein Studio predictive model (Data Cloud, regression or binary classification), Einstein Discovery (CRM Analytics license), or Einstein Prediction Builder (Setup, on Salesforce objects)?
- What is the exact outcome field: binary yes/no, a numeric value, or a category?
- What are the row count, column count, and fill rate for the intended training data?
- Are any candidate predictor fields derived from post-outcome data (leakage risk)?

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What exactly is the outcome, and when in the record's life is it known?" | Fields set at or after the outcome leak it, and a model that looks too accurate is the symptom (Gotcha 1) | An outcome definition plus a "known before" date for every predictor | Accuracy in training is the accuracy users get on open records |
| "How many rows and columns will the training data have?" | Einstein Studio predictive models need 400 to 20 million rows and 3 to 50 columns (Gotcha 2) | Counts from the actual extract, not the object | The model trains on the first attempt instead of failing setup |
| "Which predictors are free-text or ID-like with many distinct values?" | Einstein Studio supports up to 100 categories per variable, and high-cardinality fields rarely help (Gotcha 3) | A list of fields to bucket, drop, or consolidate | Predictors the model can use, and explanations people can read |
| "What fills the gaps in sparse fields, and why are they sparse?" | Nulls become an Unspecified category, and dropping too many rows hides real patterns (Gotcha 4) | A per-field rule: impute, bucket, or exclude | Sparse fields help or are removed on purpose, not by accident |
| "Is the type, data source, and goal final?" | After an Einstein Studio model is created, Choose Type, Select Data, and Set Goal can't be edited (Gotcha 5) | Sign-off on type, source, and goal before Save & Train | No rebuild because the outcome direction was wrong |
| "How rare is the positive outcome?" | A rare outcome lets a model look accurate while predicting the majority class (Gotcha 6) | Class counts and a threshold plan | The business sees useful recall, not a flat "no" for everyone |

---

## Core Concepts

### Data Requirements by Product

**Einstein Studio predictive models (grounded).** The data source must have at least 400 and at most 20 million rows, and at least 3 columns (1 outcome plus 2 others) and at most 50. Supported use cases are regression (continuous numbers) and binary classification (two-value text outcomes). "Created models in Einstein Studio support up to 100 categories per variable"; categories with fewer than 25 observations can be consolidated into Other, and null values go into a category called Unspecified.

**Einstein Discovery.** Earlier versions of this skill said Einstein Discovery requires a minimum of 400 rows where the outcome is populated, and that fields with a fill rate below about 70% are silently dropped from feature selection. UNVERIFIED (2026-10-03): both figures come from Salesforce Help and were not found in a fetched source; the Analytics Platform Setup Guide points to "Einstein Discovery Limits" without listing them. Treat 70% as a review threshold, not a platform rule.

**Einstein Prediction Builder.** Earlier versions said EPB requires at least 200 records where the outcome is true and 200 where it is false, with 400 total recommended. UNVERIFIED (2026-10-03): not found in a fetched source. The Metadata API types behind predictions are MLDataDefinition (`includedFields`, `excludedFields`, `trainingFilter`, `scoringFilter`, `segmentFilter`; `entityDeveloperName` and `type` can't be updated after creation) and MLPredictionDefinition (`predictionField`, `pushbackField`, `status` Enabled, Disabled, or Draft).

### Outcome Field Design and Leakage

"Leakage occurs when the data used to train your model includes one or more variables that contain the information that you're trying to predict. This can result in models that are extremely accurate when, in actuality, they are problematic." The outcome must be unknown at the time the predictors were captured. Fields created or populated as a result of the outcome (a "Closed Won Reason" filled at close) are proxies. For Einstein Studio models, an accuracy rating of "too high means the model is perfect or nearly perfect, which indicates potential data leakage or overfitting."

Earlier versions said Einstein Discovery flags predictors with over 30% correlation to the outcome as leakage candidates. UNVERIFIED (2026-10-03): not found in a fetched source. The Data Cloud glossary does say correlation "is quantified as a percentage" and is "not causation," so a high correlation is a prompt to investigate, not proof.

### Choosing Between the Products

- **Einstein Studio predictive model**: regression or binary classification on Data Cloud data, built in Model Builder; usable in flows, prediction jobs, batch data transforms, agents, prompt templates, Apex, and REST.
- **Einstein Discovery**: stories in CRM Analytics; needs a CRM Analytics license (the Setup Guide lists Einstein Discovery support under CRM Analytics Plus). The Einstein Discovery REST API lists a story's `sourceType` as AnalysisSetup, AnalyticsDataset, LiveDataset, or Report, so the data must already sit in one of those; for a dataset source, new object fields need the dataflow or recipe updated and run first.
- **Einstein Prediction Builder**: predictions on Salesforce objects configured in Setup. The earlier statement that EPB supports binary outcomes only is UNVERIFIED (2026-10-03): the MLPredictionDefinition `type` values include BinaryClassification, Regression, and MulticlassClassification, but the reference does not say which ones Prediction Builder offers.

---

## Common Patterns

### Pattern: Outcome and Predictor Audit Before Training

**When to use:** Before creating any model, story, or prediction.

**How it works:**
1. Extract the candidate training rows to CSV with the outcome and every candidate predictor.
2. Run `python3 scripts/check_ai_training_data_preparation.py --manifest-dir <folder> --outcome <field> --type binary|regression`.
3. Resolve every ERROR (row and column limits, outcome shape, predictors identical to the outcome).
4. Review every WARN: post-outcome field names, high cardinality, low fill, constant columns, rare positive class.
5. Record which fields were dropped and why.

**Why not skip this:** A leaking field or an unusable categorical can make a model look excellent in training and useless on open records.

### Pattern: Feature Field Selection Matrix

**When to use:** When curating which fields to include as predictors.

**How it works:** Build a field inventory with: fill rate, when the field is populated relative to the outcome, distinct-value count, and correlation-to-outcome suspicion. Exclude post-outcome fields, formulas derived from the outcome, ID-like fields, and fields you cannot fill. Collapse collinear fields ("customers who live in the city of Tampa also live in the state of Florida") to one.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Regression or binary outcome on Data Cloud data | Einstein Studio predictive model | Grounded requirements: 400 to 20 million rows, 3 to 50 columns |
| Need stories, what-if analysis in CRM Analytics | Einstein Discovery | Requires a CRM Analytics license and a dataset |
| Prediction on a Salesforce object configured in Setup | Einstein Prediction Builder | Data definition and prediction deploy as MLDataDefinition and MLPredictionDefinition |
| Fewer than 400 training rows | Fix data volume first | Below the Einstein Studio minimum; results would not train |
| Categorical predictor with more than 100 values | Bucket or consolidate first | Einstein Studio supports up to 100 categories per variable |
| Model accuracy rated "too high" | Hunt for leakage before activating | The Data Cloud guide names leakage or overfitting as the cause |

---

## Recommended Workflow

1. **Confirm product scope** with the Decision Guidance table, based on outcome type, data location, and license.
2. **Define the outcome** and the date each predictor becomes known; list post-outcome fields to exclude.
3. **Extract and audit** the training data to CSV and run `scripts/check_ai_training_data_preparation.py` with `--outcome` and `--type`; fix every ERROR.
4. **Remediate** fill-rate, cardinality, and collinearity warnings: impute, bucket, consolidate, or exclude, and write down each decision.
5. **Configure training**: for Einstein Studio, confirm type, data, and goal before Save & Train because they can't be edited later; for Prediction Builder, set `includedFields` and `excludedFields` explicitly and deploy with `status` Draft (`references/metadata-examples.md`).
6. **Validate the model**: check the accuracy rating (performant, too low, too high), top predictors, and confirm no excluded or leaking field appears among them.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Outcome field defined, and populated before (not as a result of) the predicted event
- [ ] No post-outcome proxy fields among predictors
- [ ] Row and column counts inside the target product's limits (Einstein Studio: 400 to 20 million rows, 3 to 50 columns)
- [ ] Categorical predictors at or under 100 distinct values, or consolidated
- [ ] Sparse predictors have a written impute, bucket, or exclude decision
- [ ] Checker run on the extract with zero ERROR
- [ ] After training: accuracy not rated "too high", and key predictors appear among top predictors

---

## Salesforce-Specific Gotchas

1. **Too-high accuracy is a warning**: Einstein Studio rates accuracy as performant, too low, or too high; "too high" indicates potential leakage or overfitting.

2. **Setup choices freeze**: After an Einstein Studio model is created, Choose Type, Select Data, and Set Goal can't be edited.

3. **Einstein Discovery reads from its story source**: Stories read an AnalyticsDataset, LiveDataset, or Report source, not the object directly. A field added to the object after the dataflow or recipe was built is not in a dataset source until the dataflow or recipe includes it and runs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Training extract audit | Checker output: row and column limits, outcome shape, leakage, cardinality, fill, balance |
| Outcome leakage checklist | Documents whether each high-correlation field was populated before or after the predicted event |
| Product decision record | Documents which product was selected and why |
| Prediction Builder metadata | MLDataDefinition and MLPredictionDefinition files with explicit included and excluded fields |

---

## Related Skills

- `agentforce/einstein-discovery-development` — Use for story creation, model deployment, and Einstein Discovery REST API integration after data preparation is complete
- `agentforce/einstein-prediction-builder` — Use for EPB model configuration and deployment in Setup UI
- `data/analytics-data-preparation` — Use for CRM Analytics XMD metadata management affecting which fields appear in Einstein Discovery stories
- `admin/analytics-dataset-management` — Use for dataset scheduling and row limit management determining training data freshness
