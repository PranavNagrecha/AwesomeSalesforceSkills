# Gotchas: AI Training Data Preparation

Non-obvious behaviours that let a model train on the wrong data, or refuse to train. Each gotcha names its source. "Data Cloud Guide" means the Data Cloud guide, Summer '26 (data_cloud.pdf), chapter Use AI Models (Create Predictive AI Models From Scratch, Address Data Issues, Evaluate Model Quality, Glossary for Predictive AI, Einstein Studio Model Builder Guidelines and Limits). "Metadata API" means the Metadata API Developer Guide, Version 67.0. "ED REST Guide" means the Einstein Discovery REST API Developer Guide, Spring '26 (local corpus `knowledge/imports/bi-dev-guide-rest-sdd.md`).

## Gotcha 1: A Model That Looks Too Good Is Usually Leaking

**What happens:** A win-prediction model scores near-perfect accuracy in training and predicts nothing useful on open opportunities.

**When it occurs:** A predictor carries the answer. "Leakage occurs when the data used to train your model includes one or more variables that contain the information that you're trying to predict." Einstein Studio rates accuracy as performant, too low, or too high, and "Too high means the model is perfect or nearly perfect, which indicates potential data leakage or overfitting." Typical carriers are fields set at close: stage, probability, close reason.

**How to avoid:** Record when each predictor becomes known relative to the outcome, and drop anything set at or after it. Run the checker: it fails a predictor identical to the outcome (`TRN-LEAK-01`) and warns on post-outcome names (`TRN-LEAK-02`). Treat a "too high" rating as a stop sign.

**Source:** Data Cloud Guide, Glossary for Predictive AI (Leakage); Evaluate Model Quality (Accuracy).

---

## Gotcha 2: Einstein Studio Has Hard Row and Column Bounds

**What happens:** Model creation stops because the data source is too small, or a wide extract with 80 candidate columns is refused.

**When it occurs:** "The data source must meet these requirements": 400 to 20 million rows, and 3 columns (1 outcome variable plus 2 other columns) to 50 columns. The Model Builder limits table also lists 50 input variables for Einstein-created models and 100 for connected (BYOM) models.

**How to avoid:** Count rows and columns on the actual extract before starting, and trim predictors to the 49 most defensible. The checker enforces both bounds (`TRN-ROWS-01`, `TRN-COLS-01`).

**Source:** Data Cloud Guide, Create Predictive AI Models From Scratch (data source requirements table); Einstein Studio Model Builder Guidelines and Limits.

---

## Gotcha 3: More Than 100 Categories Per Variable Is Not Supported

**What happens:** A predictor such as ZIP code or account name contributes nothing, or most of its values end up lumped together.

**When it occurs:** "Created models in Einstein Studio support up to 100 categories per variable. You can optionally consolidate the remaining categories (categories with fewer than 25 observations) into a category called Other." The guide adds that high-cardinality attributes "are rarely used in predictive modeling."

**How to avoid:** Bucket high-cardinality fields into meaningful groups (region instead of ZIP), drop ID-like fields, and standardize category spelling first ("Remove spelling variations"). The checker warns above 100 distinct values (`TRN-CARD-01`) and on one-value-per-row columns (`TRN-ID-01`).

**Source:** Data Cloud Guide, Glossary (Cardinality); Address Data Issues (High-Cardinality Fields; Standardize Categorical Values).

---

## Gotcha 4: Nulls Become a Category, and Dropping Rows Can Hide the Pattern

**What happens:** A sparse field shows "Unspecified" as a top factor, or an over-filtered training set no longer looks like real data.

**When it occurs:** "Null values are put into a category called Unspecified." For missing values the guide recommends imputing from a distribution rather than a mean, and warns: "Don't get too ambitious with filtering out missing values. Sometimes the pattern is in the missing data."

**How to avoid:** Decide per field: impute, keep nulls as a deliberate category, or exclude. Earlier versions of this skill said Einstein Discovery silently drops fields below about 70% fill rate. UNVERIFIED (2026-10-03): not found in a fetched source; the checker uses 70% only as a configurable review threshold (`TRN-FILL-01`, `--min-fill`).

**Source:** Data Cloud Guide, Glossary (Cardinality, null handling); Address Data Issues (Missing Values).

---

## Gotcha 5: Type, Data, and Goal Freeze When the Model Is Created

**What happens:** After training, the team realizes the goal should minimize rather than maximize, or the wrong data source was picked, and the model has to be rebuilt.

**When it occurs:** "All steps can be edited when creating a model. After the model is created, some steps can't be edited, such as: Choose Type, Select Data, and Set Goal." For Prediction Builder metadata, MLDataDefinition `entityDeveloperName` "can't be updated" after creation and `type` "can't be updated" after the model is created.

**How to avoid:** Get written sign-off on the use case type, the data source, and the goal direction before Save & Train. Keep those three in the decision record.

**Source:** Data Cloud Guide, Create Predictive AI Models From Scratch (review step note). Metadata API, MLDataDefinition (entityDeveloperName, type).

---

## Gotcha 6: A Rare Outcome Makes Accuracy Meaningless

**What happens:** An escalation model is right 97% of the time by predicting "no" for every case, and never flags an escalation.

**When it occurs:** The positive class is a small share of rows. Earlier versions of this skill said Prediction Builder needs at least 200 positive and 200 negative records. UNVERIFIED (2026-10-03): not found in a fetched source. The Data Cloud Guide measures binary accuracy with area under the curve (AUC), which is less fooled by imbalance than raw accuracy.

**How to avoid:** Count each class before training, report AUC and recall rather than raw accuracy, and plan the decision threshold with the business. The checker warns when the minority class is under 5% (`TRN-BAL-01`, a team heuristic, adjustable with `--min-minority`).

**Source:** Data Cloud Guide, Evaluate Model Quality (AUC for binary classification).

---

## Gotcha 7: Collinear Fields Split Importance and Confuse Explanations

**What happens:** City and State both appear in the model, each with modest importance, and stakeholders cannot tell which matters.

**When it occurs:** "Collinearity occurs when two or more predictor variables are highly correlated." The guide's example: "customers who live in the city of Tampa also live in the state of Florida." Einstein Studio importance already prefers one of two correlated variables.

**How to avoid:** Keep one field from each reporting hierarchy or highly correlated pair, chosen for business meaning.

**Source:** Data Cloud Guide, Address Data Issues (Duplicate, Redundant, or Highly Correlated Variables); Glossary (Importance).

---

## Gotcha 8: Einstein Discovery Reads Its Story Source, Not the Object

**What happens:** A new predictor field added to Opportunity never shows up in the Einstein Discovery story.

**When it occurs:** A story's source is an AnalysisSetup, AnalyticsDataset, LiveDataset, or Report. A field added to the object is not in a dataset source until the dataflow or recipe that builds the dataset includes it and runs.

**How to avoid:** After adding a field for a story, update the dataflow or recipe, run it, confirm the field in the dataset, then retrain.

**Source:** ED REST Guide, Story Collection resource (`sourceType` values) and Analytics Dataset Source.

---

## Gotcha 9: Prediction Builder Training Timing Is Not Documented in Metadata

**What happens:** A team saves a Prediction Builder configuration to "test the setup" and finds a model already scoring records.

**When it occurs:** Earlier versions of this skill said EPB begins training immediately when field selection is saved in Setup. UNVERIFIED (2026-10-03): this comes from Salesforce Help and was not found in a fetched source. The Metadata API shows MLPredictionDefinition `status` values Enabled, Disabled, and Draft, and a `pushbackField` that the prediction writes scores to.

**How to avoid:** Finish the data audit before saving the prediction. When deploying through metadata, deploy with `status` Draft first, and enable only after review.

**Source:** Metadata API, MLPredictionDefinition (status, pushbackField).
