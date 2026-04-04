# Gotchas — Einstein Prediction Builder

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleting and Recreating a Prediction Definition Creates a New Score Field API Name

**What happens:** When a prediction definition is deleted and a new one is created — even with the same name — Salesforce generates a brand new score field on the object with a different auto-generated API name. Any existing SOQL queries, Flow references, validation rules, or Apex code that hardcoded the original score field API name will silently query an empty or nonexistent field rather than throw an error. Score-based filtering logic stops working without any visible failure.

**When it occurs:** When a prediction is deleted during development or rework and recreated with corrected settings. This is common early in a project when prediction definitions are being iterated.

**How to avoid:** Treat the score field API name as a deployment artifact. Document it in the work template immediately after first activation. Before deleting a prediction, audit all SOQL queries, Flow element filters, and Apex references to the old score field name. After recreation, update all references to the new field name. Consider using a Formula field that aliases the generated score field name to a stable, human-readable API name for downstream references.

---

## Gotcha 2: Records With Missing Predictor Field Values Are Not Scored

**What happens:** A record that is missing values in the majority of fields Einstein selected as predictors will not receive a score during the scoring run. The score field on that record remains null. There is no error, no notification, and no indication in the UI that the record was skipped. From a report or List View perspective, null-score records simply appear as if Einstein has not run yet.

**When it occurs:** This is most common when: (a) a new custom field is added as a predictor and historical records have not been backfilled, (b) lead or contact records imported via Data Loader are missing company, industry, or phone fields, or (c) records created through an integration do not populate fields that the Einstein model relies on.

**How to avoid:** Before activating a prediction, run a SOQL query to count records where key predictor fields are null. If more than 20–30% of the target record population has null values in two or more top predictor fields, address data quality first — either through a backfill process or by excluding those null-value fields from the predictor set. After activation, run a spot check: select 10 unsecured records that should be scored and confirm their score fields are populated within 48 hours.

---

## Gotcha 3: Einstein Prediction Builder Is Not the Same as Einstein Discovery

**What happens:** Practitioners researching "Einstein AI predictions" encounter both Einstein Prediction Builder (EPB) and Einstein Discovery (now part of Tableau CRM / CRM Analytics). They conflate the two products or attempt to use EPB for use cases that require Einstein Discovery's capabilities — specifically continuous (regression) outcomes or multi-class classification — and are surprised when EPB only offers binary predictions.

**When it occurs:** When a stakeholder asks for predictions like "how much revenue will this account generate?" (continuous regression), "which of three tiers will this customer land in?" (multi-class), or "what should we do to improve the outcome?" (prescriptive recommendations). All of these require Einstein Discovery, not EPB.

**How to avoid:** Clarify the prediction type before starting setup. Einstein Prediction Builder answers exactly one type of question: will this yes-or-no outcome happen? If the outcome has more than two possible values, requires a numeric forecast, or requires prescriptive improvement suggestions, stop and redirect to Einstein Discovery in CRM Analytics. EPB and Einstein Discovery are separate licensed products, separate setup paths, and separate data flows. Using EPB for the wrong use case means building a prediction that cannot produce the outcome the stakeholder needs.

---

## Gotcha 4: Model Refresh Does Not Automatically Retrain the Model

**What happens:** Einstein Prediction Builder refreshes scores daily by default, re-scoring records against the existing trained model. This is not the same as retraining — the underlying model weights and predictor field selections are not updated on the daily refresh. As business patterns change over time (new lead sources, changing sales processes, seasonal variation), the model becomes stale and accuracy degrades. Score distributions may shift over months without any warning.

**When it occurs:** Any time more than 3–6 months pass without a manual retrain, especially in orgs with high record velocity or significant business changes (new products, new market segments, new data capture processes).

**How to avoid:** Schedule a quarterly model review as an operational task. During the review, open the prediction definition in Setup, click "Retrain," review the new model's quality metrics against the prior version, and activate the new model if it is equal or better. EPB supports model comparison — review both versions before switching. If accuracy on the new model drops, investigate whether training data quality has changed (new field gaps, outcome field reliability, data distribution shifts).

---

## Gotcha 5: The 10 Active Prediction Limit Is Org-Wide and Hard

**What happens:** An org can have a maximum of 10 active prediction definitions at any time. When this limit is reached, attempts to activate a new prediction fail silently in some cases or display a generic error. Practitioners who reach this limit during a project iteration cycle may not realize the limit exists and spend time troubleshooting the wrong thing.

**When it occurs:** In larger orgs where multiple teams have been independently building predictions over time, or during active development when test predictions from earlier iterations were never deactivated.

**How to avoid:** Before creating a new prediction definition in any org, check Setup > Einstein Prediction Builder to count active predictions. If the org is at 9 or 10, deactivate at least one before proceeding. Maintain a registry of active predictions (owner, use case, last retrain date) as part of org governance documentation to avoid hitting the limit without warning.
