---
name: einstein-prediction-builder
description: "Einstein Prediction Builder for creating custom binary classification predictions on Salesforce objects: field selection, training data requirements, model activation, score embedding, and monitoring. NOT for Einstein Discovery (Tableau CRM Analytics) or Agentforce agent creation."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "how to predict which leads will convert using Einstein"
  - "set up custom AI prediction on opportunities in Salesforce"
  - "embed prediction score on record page using Einstein Prediction Builder"
  - "Einstein Prediction Builder not generating scores on records"
  - "how many records do I need to train an Einstein custom prediction"
  - "why is my Einstein prediction accuracy low after training"
tags:
  - einstein-prediction-builder
  - binary-classification
  - ai-scoring
  - custom-prediction
  - einstein-platform
inputs:
  - Salesforce org with Einstein Platform license or Sales/Service Cloud Einstein license
  - Standard or custom object with a defined Yes/No binary outcome field and at least 400 records with known outcomes
  - Understanding of which object and outcome field the prediction targets
  - Access to Setup > Einstein Prediction Builder
outputs:
  - Configured and activated Einstein Prediction definition on the target object
  - Score field (e.g., EinsteinScoring__Score__c) on the object populated for all scoreable records
  - Einstein Prediction standard component added to the record Lightning page showing score and top contributing factors
  - Decision guidance on field selection, training data quality, and model refresh strategy
  - Review checklist confirming activation, scoring health, and page layout embedding
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Einstein Prediction Builder

This skill activates when a practitioner needs to create, configure, activate, troubleshoot, or audit a custom Einstein Prediction Builder (EPB) prediction. It covers Mode 1 (create a new prediction from scratch), Mode 2 (review or audit an existing prediction for accuracy and field coverage), and Mode 3 (troubleshoot low accuracy, stale scores, or scoring gaps).

---

## Before Starting

Gather this context before working on anything in this domain:

- **License requirement:** Einstein Prediction Builder requires an Einstein Platform license or a Sales Cloud Einstein / Service Cloud Einstein license. Verify the org's license before proceeding. Without the correct license, the Setup menu entry for Einstein Prediction Builder will not appear.
- **Training data minimum:** A prediction definition requires at least 400 records with known outcomes on the target object. Ideally the dataset contains 1,000 or more records with a balanced positive-to-negative ratio. An imbalanced dataset (e.g., 95% No, 5% Yes) will produce a model that scores most records at or near zero and has poor practical utility.
- **Outcome field type:** The outcome field must be a Checkbox (Boolean) or a Picklist field with exactly two meaningful values mapped to a Yes/No outcome. The prediction is always binary — it answers one question: will this event happen or not?
- **Most common wrong assumption:** Practitioners expect Einstein to score records immediately after a prediction is activated. In practice, initial scoring runs within 24–48 hours after activation. Subsequent model refreshes occur daily by default. Records with missing values in key predictor fields may not receive a score at all.
- **Platform constraint:** Einstein Prediction Builder supports a maximum of 10 active prediction definitions per org. Each prediction can have up to 3 segments with different field configurations.

---

## Core Concepts

### Binary Classification and the Outcome Field

Einstein Prediction Builder creates binary classification models. Every prediction answers exactly one yes/no question about a record: "Will this opportunity close as Won?" or "Will this customer churn within 90 days?" The outcome field is the historical signal Einstein learns from — it must already be populated on existing records so Einstein can identify patterns between Won=True and Won=False records.

The outcome field can be a Checkbox or a two-value Picklist. When using a Picklist, you map the two values to "Positive" (Yes) and "Negative" (No) during prediction setup. Einstein ignores records where the outcome field is blank during training, which means blank outcomes reduce effective training data volume.

### Training, Activation, and Scoring Lifecycle

A prediction definition moves through four states:

1. **Draft** — configuration is in progress; no training has occurred.
2. **Training** — Einstein is building and evaluating the model. Training typically completes within a few hours but can take longer for large datasets or complex field sets.
3. **Active** — the model is live. Einstein scores existing records in the first scoring run (24–48 hours post-activation) and continues scoring new and updated records on the refresh schedule (daily by default).
4. **Inactive** — the prediction has been deactivated. Scores already on records remain but are not updated.

After a model is trained but before activation, Einstein displays model quality metrics including overall accuracy, precision, recall, and a comparison against a baseline "naïve" model. A model should only be activated if it outperforms the baseline on the metrics that matter for the use case.

### Score Fields and the EinsteinModelFactor Object

When a prediction is activated, Salesforce adds a score field to the target object. The field API name follows the pattern `EinsteinScoring_<PredictionName>__Score__c` and stores the prediction score as a numeric value between 0 and 100, representing the model's confidence that the positive outcome will occur.

Einstein also creates associated fields for tier classification (e.g., High/Medium/Low) and score reason text. Scores are queryable via SOQL like any custom field.

To understand which fields drive a specific record's score, query the `EinsteinModelFactor__c` object:

```soql
SELECT FieldName, FactorValue, FactorPolarity, Weight
FROM EinsteinModelFactor__c
WHERE PredictionDefinitionId = '<prediction-definition-id>'
  AND RecordId = '<target-record-id>'
ORDER BY Weight DESC
LIMIT 10
```

This returns the top contributing fields, their values for that record, and whether each factor pushed the score up (positive polarity) or down (negative polarity).

### Field Selection and Segments

During prediction setup, Einstein automatically evaluates all eligible fields on the object and selects those most correlated with the outcome. Eligible fields include text, number, picklist, date, and lookup fields. Formula fields, system fields (CreatedDate, LastModifiedDate), and fields with very high cardinality or sparsity are less useful.

Practitioners can guide field selection by excluding fields that would constitute data leakage — for example, excluding the "Close Date" field when predicting opportunity closure, because that field is set at the same time as the outcome and does not represent a leading indicator.

Segments allow a single prediction to use different field configurations for different subsets of records. For example, a Lead conversion prediction might use different fields for inbound leads vs. outbound leads. Up to 3 segments are supported per prediction.

---

## Common Patterns

### Mode 1: Create a New Prediction From Scratch

**When to use:** A new use case requires a binary AI score on a Salesforce object — such as predicting lead conversion, opportunity win rate, case escalation risk, or customer churn.

**How it works:**

1. Confirm license availability (Einstein Platform, Sales Cloud Einstein, or Service Cloud Einstein).
2. Navigate to Setup > Einstein Prediction Builder > New Prediction.
3. Select the target object. Name the prediction clearly using the pattern `<Object>_<Outcome>_Prediction` (e.g., `Lead_ConversionLikelihood_Prediction`).
4. Select or create the outcome field. Ensure it has at least 400 records with non-blank values, ideally 1,000+ with a balanced Yes/No distribution.
5. Configure field selection: let Einstein auto-select predictor fields, then review and exclude any leakage fields (fields that are set at the same time as or after the outcome).
6. Optionally define segments if the record population has meaningfully different sub-groups with different predictive signals.
7. Click Train. Wait for training to complete (typically a few hours).
8. Review model quality metrics. Confirm the model outperforms the baseline accuracy before activating.
9. Activate the prediction. First scores appear within 24–48 hours.
10. Add the "Einstein Prediction" standard Lightning component to the object's record page in the Lightning App Builder, selecting the newly activated prediction.

**Why not skip training review:** Activating a low-quality model generates scores that are no better than random. Sales reps or service agents who rely on low-quality scores may make worse decisions than they would without AI guidance.

### Mode 2: Review or Audit an Existing Prediction

**When to use:** A prediction is already active but stakeholders question its accuracy, the model needs to be reviewed before a go-live decision, or a compliance audit requires documentation of what fields drive scores.

**How it works:**

1. Navigate to Setup > Einstein Prediction Builder and open the prediction definition.
2. Review the last training date and model quality metrics (accuracy, precision, recall).
3. Check the outcome field's current data distribution — if the ratio of positive to negative outcomes has shifted significantly since the last training, the model may be operating on outdated patterns.
4. Query `EinsteinModelFactor__c` for a sample of records (high-score, low-score, and mid-score) to confirm the driving fields are business-relevant leading indicators, not leakage fields.
5. Review the exclusion filter configuration — confirm records excluded from training are still appropriate to exclude.
6. Document model quality metrics and top factors in the audit artifact (use the template in `templates/einstein-prediction-builder-template.md`).

### Mode 3: Troubleshoot Low Accuracy or Stale Scores

**When to use:** Scores on records are not updating, accuracy has dropped after a period of use, most records are scored near zero or near 100 with no differentiation, or the score field is blank on records that should be scored.

**How it works:**

1. **Blank scores:** Check whether the record meets scoring eligibility. Records excluded by the exclusion filter will not be scored. Records missing values in the majority of predictor fields may be skipped. Verify the last scoring run completed without errors in the Einstein Prediction Builder setup UI.
2. **Stale scores:** Confirm the prediction is Active (not Inactive). Daily refresh runs automatically, but the first refresh may take 24–48 hours. Check if a manual refresh can be triggered from the prediction definition UI.
3. **Low accuracy / poor differentiation:** Re-examine training data. Check whether the outcome field distribution is heavily imbalanced (e.g., fewer than 5% positive outcomes). Consider adding an exclusion filter to balance the training set if needed. Check whether leakage fields are included — a field that is only populated after the outcome has occurred will produce artificially high training accuracy but poor real-world performance.
4. **Accuracy drop over time:** Trigger a model retrain from the prediction definition. If the underlying business patterns have shifted (e.g., a new lead source was introduced), the old model's patterns no longer apply and retraining on current data is required.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fewer than 400 records with known outcomes | Do not proceed with Einstein Prediction Builder; use Flow-based scoring rules instead | EPB requires minimum 400 records; below this threshold the model cannot train |
| Highly imbalanced outcome field (>90% one value) | Apply an exclusion filter to undersample the majority class before training | Imbalanced data produces models that score everything near 0 or 100 with poor recall |
| Leakage fields present (set at same time as outcome) | Explicitly exclude those fields from the prediction field configuration | Leakage fields produce misleading training accuracy and useless real-world scores |
| Need a multi-outcome or continuous score | Use Einstein Discovery in CRM Analytics (Tableau CRM), not Einstein Prediction Builder | EPB is binary-only; Einstein Discovery supports regression and multi-class classification |
| Scores not appearing within 48 hours of activation | Verify prediction is Active, not just Trained; check exclusion filter scope | Activation is required; Training state does not trigger scoring |
| Need to understand what drives a specific record's score | Query EinsteinModelFactor__c filtered by PredictionDefinitionId and RecordId | EinsteinModelFactor__c exposes field-level score contribution per record |
| Multiple sub-populations with different predictor signals | Configure segments within the prediction definition (up to 3 segments) | Segments allow per-segment field selection without creating separate prediction definitions |
| Org has reached 10 active predictions | Deactivate a low-value prediction before creating a new one | EPB has a hard limit of 10 active prediction definitions per org |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking an Einstein Prediction Builder implementation complete:

- [ ] Einstein Platform, Sales Cloud Einstein, or Service Cloud Einstein license confirmed in the org
- [ ] Outcome field has 400+ records with non-blank values; ideally 1,000+ with balanced Yes/No distribution
- [ ] Leakage fields reviewed and excluded from predictor field selection
- [ ] Model trained and quality metrics reviewed; model outperforms baseline accuracy
- [ ] Prediction activated (not just trained)
- [ ] Score field visible on records within 48 hours of activation
- [ ] "Einstein Prediction" Lightning component added to the record page in Lightning App Builder
- [ ] EinsteinModelFactor__c queried on sample records to confirm top factors are business-relevant
- [ ] Exclusion filters reviewed and scoped correctly (records that should be scored are not excluded)
- [ ] Model refresh schedule confirmed (daily by default); retrain plan documented for model drift

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activation is a separate step from training** — After training completes, the prediction is in a "Trained" state but scores are not generated until the practitioner explicitly clicks Activate. Practitioners who skip activation wait 48+ hours for scores that will never appear. Always confirm the prediction status is "Active" in the EPB setup UI.
2. **Blank outcome records are silently excluded from training** — If the outcome field is blank on a record, Einstein ignores that record during training without any warning. An object with 2,000 records but 1,700 blank outcome values will train on only 300 records — below the 400-record minimum — and either fail to train or produce a low-quality model. Always filter and count non-blank outcomes before starting.
3. **Score field API name is auto-generated and cannot be renamed** — The score field Salesforce creates follows a system-generated naming convention. If a prediction definition is deleted and recreated, a new field with a different API name is created. Any SOQL queries, Flow references, or Apex code that hardcoded the original field API name will break silently — they will query the old (now empty) field rather than the new one.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated prediction definition | The configured and active EPB prediction in Setup, generating scores daily |
| Score field on target object | Numeric field (0–100) on each record representing the model's positive-outcome confidence |
| EinsteinModelFactor__c query results | Per-record field-level score drivers for audit or UI display |
| Model quality report | Accuracy, precision, and recall metrics from the training evaluation screen |
| Lightning page with score component | Record page updated with the "Einstein Prediction" standard component |
| Prediction audit template | Completed template documenting field selection, training data, and quality metrics |

---

## Related Skills

- agentforce/einstein-trust-layer — use when AI outputs from EPB scores are surfaced through Agentforce agents and Trust Layer data masking or audit requirements apply
- agentforce/prompt-builder-templates — for grounding Prompt Builder templates with EPB score fields to generate score-aware AI responses
- admin/custom-permissions — for restricting which users can view or interact with prediction score fields and components
