# LLM Anti-Patterns — Einstein Prediction Builder

Common mistakes AI coding assistants make when generating or advising on Einstein Prediction Builder.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Prediction Builder When Einstein Discovery Is More Appropriate

**What the LLM generates:** "Use Einstein Prediction Builder to predict revenue amount" when Prediction Builder only supports binary classification (yes/no outcomes). Numeric predictions (regression) require Einstein Discovery (Tableau CRM / CRM Analytics).

**Why it happens:** LLMs treat "prediction" as a generic capability. Prediction Builder is limited to binary outcomes — will this lead convert (yes/no), will this opportunity close (yes/no). Predicting continuous values (deal size, days to close, churn probability as a percentage) is not supported.

**Correct pattern:**

```text
Einstein Prediction Builder scope:

SUPPORTED (binary classification):
- Will this lead convert? (Yes/No)
- Will this opportunity close-won? (Yes/No)
- Will this case escalate? (Yes/No)
- Will this customer churn? (Yes/No)

NOT SUPPORTED (use Einstein Discovery instead):
- What will the deal amount be? (numeric regression)
- How many days until this case is resolved? (numeric)
- What is the probability score from 0-100? (continuous)
- Which of 5 product categories will the customer buy? (multi-class)

Einstein Discovery (CRM Analytics):
- Supports regression, multi-class classification, and time series
- Requires CRM Analytics (Tableau) license
- More complex setup but broader prediction capabilities

Decision guide:
- Binary outcome on a standard/custom object → Prediction Builder
- Numeric outcome or multi-class → Einstein Discovery
- Need to understand WHY the prediction was made → Einstein Discovery
```

**Detection hint:** Flag Prediction Builder recommendations for non-binary outcomes. Check for predictions targeting numeric fields (Amount, Days Open) or picklists with more than 2 values.

---

## Anti-Pattern 2: Not Meeting Minimum Data Requirements

**What the LLM generates:** "Create a prediction on your custom object and Einstein will start scoring" without noting that Prediction Builder requires at minimum 400 records with known outcomes (at least 100 in each category: true and false).

**Why it happens:** LLMs describe the UI workflow without data prerequisites. Prediction Builder silently fails to build a model or produces a low-quality model when data volume is insufficient.

**Correct pattern:**

```text
Prediction Builder data requirements:

Minimum thresholds:
- 400 records total with the outcome field populated
- At least 100 records where outcome = True
- At least 100 records where outcome = False
- Records should span a meaningful time period (6+ months)

Quality requirements:
- Outcome field must be a checkbox or formula returning true/false
- Predictor fields should be populated on most records
  (fields that are 90% null add no value)
- No data leakage: predictor fields should not contain
  the outcome itself (e.g., "Closed Won Stage" predicting
  "Is Closed Won" is circular)

Improving model quality:
- More data is better: 1000+ records significantly improves accuracy
- Balanced classes: 50/50 split is ideal, 70/30 is acceptable,
  95/5 requires careful evaluation of the model scorecard
- Diverse predictor fields: include fields from different
  data categories (dates, picklists, numbers, lookups)

If the model fails to build:
1. Check record count with outcome populated
2. Verify class balance (true vs false counts)
3. Remove highly correlated or leaking fields from segment
```

**Detection hint:** Flag Prediction Builder setup that does not verify data volume. Check for outcome fields with extreme class imbalance (>90/10 split). Flag predictions on objects with fewer than 400 records.

---

## Anti-Pattern 3: Including Data-Leaking Fields in the Prediction

**What the LLM generates:** A prediction definition that includes fields which are populated AFTER the outcome is already known, creating a circular prediction that scores perfectly in training but is useless in practice.

**Why it happens:** LLMs select predictor fields based on correlation with the outcome without considering temporal causality. A field like "Reason for Closure" is perfectly correlated with "Is Closed Won" but is only populated after the opportunity is already closed — making it useless for predicting future outcomes.

**Correct pattern:**

```text
Data leakage detection in Prediction Builder:

Leaking fields (DO NOT include as predictors):
- Fields populated only after the outcome is known
  Example: "Close Reason" for predicting "Is Closed Won"
  Example: "Resolution Notes" for predicting "Is Escalated"
- Fields derived from the outcome
  Example: "Won Amount" for predicting "Is Won"
- Fields updated by automation triggered by the outcome
  Example: "Post-Close Survey Sent" for predicting closure

Safe predictor fields:
- Fields populated BEFORE the outcome
  Example: Lead Source, Industry, Annual Revenue
- Fields that exist at the time of prediction
  Example: Number of Activities, Days in Current Stage
- Fields independent of the outcome
  Example: Account Rating, Region, Product Line

How to verify:
1. For each predictor field, ask: "Is this field populated
   BEFORE or AFTER the outcome occurs?"
2. Check the model scorecard: if accuracy is above 95%,
   suspect data leakage
3. Review the top predictive fields — if they are suspiciously
   perfect, they may be leaking
```

**Detection hint:** Flag prediction definitions where a predictor field name contains the outcome concept (e.g., "Close" in a prediction about closing). Check for model accuracy above 95% which may indicate leakage. Flag predictor fields that are only populated on closed or resolved records.

---

## Anti-Pattern 4: Not Embedding the Score on the Record Page for User Consumption

**What the LLM generates:** "Activate the prediction and users will see the score" without noting that the prediction score field must be explicitly added to the Lightning record page layout, and that users need to understand what the score means to act on it.

**Why it happens:** Prediction Builder creates the score field automatically, but it is not added to page layouts by default. LLMs assume activation equals visibility. Additionally, a bare number (e.g., "Score: 72") without context is not actionable for most sales or service reps.

**Correct pattern:**

```text
Score deployment for user adoption:

1. Add score field to Lightning page:
   - Edit the Lightning record page in Lightning App Builder
   - Add the Einstein Prediction component (not just the field)
   - The component shows score + top factors + explanation

2. Add score field to list views:
   - Create list views sorted by prediction score
   - "High Probability Leads" — filter Score > 70

3. Contextualize the score:
   - Add a custom help text or guidance component explaining:
     "This score predicts the likelihood of [outcome].
     Scores above 70 indicate high probability.
     The top factors show why."

4. Integrate into workflows:
   - Use the score field in Flow or assignment rules
   - Example: auto-assign leads with score > 80 to senior reps
   - Example: flag opportunities with score < 30 for pipeline review

5. Do NOT:
   - Show the raw score without the explanation component
   - Use the score as the sole decision criterion
   - Hide the score from the rep (transparency builds trust)
```

**Detection hint:** Flag prediction activation without Lightning page layout updates. Check for score fields not present on any page layout. Flag deployments that show the score number without the Einstein Prediction component (which includes explanations).

---

## Anti-Pattern 5: Not Monitoring Model Performance After Deployment

**What the LLM generates:** "Enable the prediction and it will continuously improve" without noting that prediction models must be monitored for accuracy drift, and that data pattern changes (new products, market shifts, process changes) can degrade model performance over time.

**Why it happens:** LLMs present ML models as self-maintaining. Prediction Builder does retrain automatically on a schedule, but it does not alert admins when accuracy drops or when the data distribution shifts. Without monitoring, a degraded model continues scoring records with misleading predictions.

**Correct pattern:**

```text
Prediction model monitoring:

Regular review cadence:
- Monthly: check model scorecard in Setup
- Quarterly: compare predicted vs actual outcomes
- After major changes: new products, process changes, reorg

Model scorecard metrics to track:
- Accuracy: overall correct predictions
- AUC (Area Under Curve): model discrimination ability
- Precision and Recall by class: false positive vs false negative rates

Degradation indicators:
- Accuracy drops below 65% — model is not useful
- Predictions cluster around 50% — model lost discrimination
- Top predictive fields changed unexpectedly — data pattern shift
- Score distribution changed — new data does not match training

Response to degradation:
1. Check if data quality changed (field values, volume)
2. Check if business process changed (new stages, new products)
3. Consider rebuilding the prediction with updated segment criteria
4. If the model cannot recover, deactivate rather than mislead users

Prediction Builder retrains automatically, but automatic retraining
on bad data produces a bad model faster.
```

**Detection hint:** Flag prediction deployments with no monitoring plan. Check for predictions active for more than 6 months without a scorecard review. Flag models with accuracy below 65% that are still active.

---
