# LLM Anti-Patterns — AI Training Data Preparation

Common mistakes AI coding assistants make when generating or advising on AI Training Data Preparation.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Treating Outcome Field Selection as Trivial

**What the LLM generates:** "Use IsClosed or IsWon as your outcome field for opportunity prediction."

**Why it happens:** LLMs recognize standard boolean fields and suggest them without auditing whether they are causally appropriate or contain leakage.

**The correct pattern:** The outcome field must be: (1) the event you are actually trying to predict, (2) populated before (not because of) the predicted event, and (3) distinct from proxy fields that are causally downstream. For opportunity win prediction, `IsWon` is appropriate but must be combined with a prediction window — using all closed records regardless of stage at prediction time creates leakage from fields like StageName that change simultaneously with IsWon.

**Detection hint:** If the suggested outcome field or any predictor field is populated at the exact same time as the outcome event, flag it for leakage review.

---

## Anti-Pattern 2: Ignoring Fill-Rate Thresholds for Einstein Discovery

**What the LLM generates:** A field list for an Einstein Discovery story that includes fields with < 50% fill rate without noting the risk.

**Why it happens:** LLMs generate field lists based on field existence, not on fill-rate data that requires a runtime query.

**The correct pattern:** All fields intended as predictors must be audited for fill rate before training, and the audit needs the actual data, not the object schema. Decide per sparse field whether to impute, keep nulls as a category (Einstein Studio puts nulls into "Unspecified"), or exclude. UNVERIFIED (2026-10-03): the earlier claim that Einstein Discovery silently drops fields below about 70% fill rate was not found in a fetched source.

**Detection hint:** If the response recommends Einstein Discovery feature fields without explicitly mentioning fill-rate requirements or an audit step, the response is incomplete.

---

## Anti-Pattern 3: Recommending Einstein Prediction Builder for Non-Binary Outcomes

**What the LLM generates:** "Use Einstein Prediction Builder to predict churn probability score or customer lifetime value."

**Why it happens:** LLMs conflate Einstein Prediction Builder with Einstein Discovery. EPB supports only binary (yes/no) outcomes.

**The correct pattern:** Check the product's supported use cases before recommending it. Einstein Studio predictive models support regression and binary classification (Data Cloud guide). UNVERIFIED (2026-10-03): the earlier claim that EPB supports binary outcomes only; the MLPredictionDefinition `type` values include BinaryClassification, Regression, and MulticlassClassification, but the reference does not say which ones Prediction Builder offers. Confirm in the org's Prediction Builder setup before ruling it out.

**Detection hint:** A product recommendation for a numeric or multi-class outcome that does not state which use case types the product supports.

---

## Anti-Pattern 4: Using Proxy Fields Known Only Post-Outcome

**What the LLM generates:** Including `StageName = 'Closed Won'`, `Probability = 100`, or custom "Reason" fields in the predictor list.

**Why it happens:** LLMs list fields that correlate strongly with the outcome, without checking whether the correlation is because the field was set at the same time as the outcome.

**The correct pattern:** Fields that are populated simultaneously with or because of the outcome are proxy fields that cause leakage. Even if they correlate strongly in training data, they will not be available at prediction time for open records.

**Detection hint:** Review each suggested predictor: ask "Is this field populated before the outcome occurs, or at/after?" Fields populated only when the outcome is finalized are leakage candidates.

---

## Anti-Pattern 5: Omitting Class Balance Check for EPB

**What the LLM generates:** "Enable Einstein Prediction Builder using the outcome condition 'Escalated__c = true'." — without checking positive class count.

**Why it happens:** LLMs recommend EPB setup steps without running a class balance audit.

**The correct pattern:** Count positive and negative records before enabling any prediction. When the positive class is a small share of rows, a model can predict the negative class for nearly everything and still look accurate; report AUC and recall instead of raw accuracy. UNVERIFIED (2026-10-03): the earlier minimum of 200 positive and 200 negative records for EPB was not found in a fetched source.

**Detection hint:** If the response does not include a step to count positive-class vs. negative-class records before enabling EPB, the data preparation is incomplete.

---

## Anti-Pattern 6: Ignoring the Einstein Studio Row and Column Bounds

**What the LLM generates:** "Export the 250 opportunities from last quarter with all 70 fields and train a model in Model Builder."

**Why it happens:** The model treats any data set as trainable.

**The correct pattern:** Einstein Studio predictive models need 400 to 20 million rows and 3 to 50 columns (one outcome plus at least two predictors). Widen the date range or the record scope, and trim predictors to the most defensible 49.

**Detection hint:** A training plan with a row count under 400 or more than 50 columns.

---

## Anti-Pattern 7: Feeding IDs and Free-Text Names as Predictors

**What the LLM generates:** A predictor list that includes Account Name, Owner Id, ZIP code, and Opportunity Name.

**Why it happens:** Every column looks like signal to the model generating the list.

**The correct pattern:** Einstein Studio supports up to 100 categories per variable, and high-cardinality attributes "are rarely used in predictive modeling." Drop identifiers, bucket geographic codes into regions, and standardize category spellings.

**Detection hint:** Predictors whose distinct-value count is close to the row count, or above 100.

