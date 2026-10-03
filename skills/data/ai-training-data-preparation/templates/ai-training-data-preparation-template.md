# AI Training Data Preparation — Work Template

Use this template when preparing data for an Einstein Discovery story or Einstein Prediction Builder model.

---

## Scope

**Project / Object being modeled:** _______________
**Einstein product:** [ ] Einstein Studio predictive model (Data Cloud; regression or binary)  [ ] Einstein Prediction Builder (Setup; confirm supported outcome types)  [ ] Einstein Discovery (requires CRM Analytics)
**Outcome field:** _______________
**Outcome type:** [ ] Binary (yes/no)  [ ] Regression (numeric value)  [ ] Multi-class (category)

---

## Step 1: Outcome Field Audit

| Check | Result |
|---|---|
| Outcome field API name | |
| Fill rate (COUNT of non-null / COUNT total) | |
| Is outcome populated before or after the predicted event? | |
| Any proxy fields populated at the same time as outcome? | |

---

## Step 2: Feature Field Inventory

| Field API Name | Fill Rate | Populated Before Outcome? | Leakage Suspect? | Include? |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

## Step 3: Minimum Row Count Check

| Metric | Required | Actual |
|---|---|---|
| Total rows with outcome populated | 400 min (Einstein Studio) | |
| Columns including outcome | 3 to 50 (Einstein Studio) | |
| Positive-class rows (EPB) | 200 min (UNVERIFIED review threshold) | |
| Negative-class rows (EPB) | 200 min (UNVERIFIED review threshold) | |
| Checker run | `scripts/check_ai_training_data_preparation.py` exit 0 | |

---

## Step 4: Remediation Plan

Fields needing fill-rate improvement:
- _______________

Fields excluded due to leakage:
- _______________

---

## Step 5: Product Decision

**Selected product:** [ ] EPB  [ ] Einstein Discovery  
**Rationale:** _______________

---

## Step 6: Post-Training Validation

- [ ] Key predictor fields appear in feature contributions list
- [ ] Confusion matrix reviewed — precision and recall acceptable
- [ ] No leakage fields appear in top features
