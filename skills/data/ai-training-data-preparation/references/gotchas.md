# Gotchas — AI Training Data Preparation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Fields Below ~70% Fill Rate Are Silently Dropped by Einstein Discovery

**What happens:** When creating an Einstein Discovery story, fields with low fill rates are silently excluded from feature selection. The story completes successfully with no error or warning. The only way to discover the exclusion is by navigating to the story's field settings after training and checking whether the expected fields appear.

**Impact:** A key predictor field that the business expects the model to use is simply absent. Model accuracy appears lower than expected with no explanation. Teams often waste time trying to tune other parameters before realizing a key field was excluded.

**How to avoid:** Audit fill rates for all candidate feature fields before story creation. Run aggregate SOQL queries: `SELECT COUNT(Id) total, COUNT(Outcome_Field__c) outcome_count, COUNT(Feature_Field__c) feature_count FROM Object__c`. Ensure all key fields are above 70% before proceeding.

---

## Gotcha 2: EPB Begins Training Automatically on Save

**What happens:** Unlike Einstein Discovery (where training is an explicit batch job), Einstein Prediction Builder begins model training immediately when you save the field selection in Setup. If data quality issues exist at save time, a poor-quality model is immediately trained and can become active.

**Impact:** A team that enables EPB to "test the setup" discovers a partially-configured model is already making predictions on live records. Disabling and retraining requires navigating back through Setup and waiting for re-training.

**How to avoid:** Complete all data preparation (fill rate audit, leakage review, class balance check) before enabling EPB in Setup. Treat the Setup save action as production deployment.

---

## Gotcha 3: Einstein Discovery Reads from CRM Analytics — New Fields Need Dataflow Update

**What happens:** Einstein Discovery stories read data from CRM Analytics datasets, not directly from Salesforce objects. If a new field is added to a Salesforce object after the existing Data Sync or dataflow is configured, the new field does not automatically appear in the CRM Analytics dataset. It must be explicitly added to the dataflow or recipe and the dataset must be re-run.

**Impact:** Teams add a promising new predictor field to the object, expect Einstein Discovery to pick it up, and discover weeks later that the field was never available for the story because the dataflow was never updated.

**How to avoid:** After adding any new field intended for Einstein Discovery, update the sfdcDigest or recipe to include the field, run the dataflow, and verify the field appears in the dataset before attempting to create or retrain a story.
