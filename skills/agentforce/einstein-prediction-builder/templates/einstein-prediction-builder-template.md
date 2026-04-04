# Einstein Prediction Builder — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `einstein-prediction-builder`

**Request summary:** (fill in what the user asked for)

**Mode:**
- [ ] Mode 1 — Create a new prediction from scratch
- [ ] Mode 2 — Review or audit an existing prediction
- [ ] Mode 3 — Troubleshoot low accuracy or stale scores

---

## Context Gathered

Answer these before starting work:

- **License confirmed?** (Einstein Platform / Sales Cloud Einstein / Service Cloud Einstein): ___
- **Target object:** ___
- **Outcome field name and type** (Checkbox / Picklist): ___
- **Count of records with non-blank outcome values:** ___ (must be 400+; 1,000+ preferred)
- **Positive-to-negative outcome ratio:** ___% positive / ___% negative
- **Leakage fields to exclude** (fields set at or after outcome time): ___
- **Segments needed?** (Y/N) — reason: ___
- **Current prediction status** (Draft / Training / Active / Inactive): ___
- **Active prediction count in org** (max 10): ___

---

## Prediction Definition Summary

| Field | Value |
|---|---|
| Prediction Name | |
| Target Object | |
| Outcome Field | |
| Positive Outcome Value | |
| Negative Outcome Value | |
| Training Record Count | |
| Positive Outcome % | |
| Segments Configured | |
| Excluded Predictor Fields | |
| Exclusion Filter (if any) | |
| Score Field API Name | |
| Activation Date | |
| Last Retrain Date | |

---

## Model Quality Metrics (Record After Training)

| Metric | Value | Baseline | Passes? |
|---|---|---|---|
| Overall Accuracy | | | |
| Precision (Positive Class) | | | |
| Recall (Positive Class) | | | |
| F1 Score | | | |
| Area Under Curve (AUC) | | | |

Activation decision: **[ ] Activate** / **[ ] Do not activate — retrain with corrected data**

Reason (if not activating): ___

---

## Top Predictor Fields (From EinsteinModelFactor__c Audit)

Run this query after activation on a representative sample of records:

```soql
SELECT FieldName, FactorValue, FactorPolarity, Weight
FROM EinsteinModelFactor__c
WHERE PredictionDefinitionId = '<prediction-definition-id>'
  AND RecordId = '<target-record-id>'
ORDER BY Weight DESC
LIMIT 10
```

| Rank | Field Name | Factor Polarity | Business-Relevant Leading Indicator? | Leakage Risk? |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

---

## Approach

**Which mode applies?** (1 / 2 / 3): ___

**Which pattern from SKILL.md applies?**
- [ ] Mode 1: Create a New Prediction From Scratch
- [ ] Mode 2: Review or Audit an Existing Prediction
- [ ] Mode 3: Troubleshoot Low Accuracy or Stale Scores

**Deviation from standard pattern (if any):** ___

---

## Checklist

Copy from SKILL.md review checklist and tick items as you complete them:

- [ ] Einstein Platform / Sales Cloud Einstein / Service Cloud Einstein license confirmed
- [ ] Outcome field has 400+ non-blank records; ideally 1,000+ with balanced distribution
- [ ] Leakage fields reviewed and excluded from predictor field selection
- [ ] Model trained; quality metrics reviewed; model outperforms baseline accuracy
- [ ] Prediction activated (not just in "Trained" state)
- [ ] Score field visible and populated on records within 48 hours of activation
- [ ] "Einstein Prediction" Lightning component added to record page in Lightning App Builder
- [ ] EinsteinModelFactor__c queried on sample records; top factors confirmed as business-relevant
- [ ] Exclusion filters reviewed; records that should be scored are not excluded
- [ ] Model refresh schedule confirmed; retrain cadence documented

---

## Lightning Page Embedding

- [ ] "Einstein Prediction" standard component added to the Lightning record page for target object
- [ ] Component configured to show the correct prediction definition
- [ ] Score and top reason fields visible to target user profile
- [ ] Page layout tested in both Desktop and Mobile views

---

## Retrain Plan

| Review Frequency | Owner | Criteria for Retrain |
|---|---|---|
| Quarterly | | Accuracy drops >5% from baseline OR major business change |

---

## Notes

Record any deviations from the standard pattern and why, known data quality issues, or outstanding items:

___
