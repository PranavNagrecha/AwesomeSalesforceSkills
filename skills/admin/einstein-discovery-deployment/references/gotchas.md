# Gotchas — Einstein Discovery Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Model Refresh Does NOT Auto-Activate the New Version

**What happens:** An admin schedules a weekly model refresh job expecting the org to automatically start using the freshly trained model. The refresh job shows Completed in Model Manager. However, the prediction definition's active model version does not change — all scoring continues against the previous model version.

**When it occurs:** Every time a model refresh job completes, whether triggered manually or by a schedule. The refresh creates a new model version with an incremented version number and Enabled status, but it never promotes itself to Active.

**How to avoid:** After confirming the refresh job status is Completed, navigate to Model Manager > [Prediction Definition] > Models tab. Identify the new version (highest version number). Click the row and select "Set as Active". Confirm the Active badge moves to the new version. Then trigger a bulk predict job to re-score records with the new model. Build this two-step sequence (activate + re-score) into any model refresh runbook or automation.

---

## Gotcha 2: Prediction Scores on Records Are NOT Updated Automatically When Source Fields Change

**What happens:** A sales rep updates the Opportunity Amount, Stage, or Close Date on a record. The Predicted Win Rate field (or any other Einstein Discovery output field) on that record does not change. The score shown on the record page is still the value from the last bulk predict job run.

**When it occurs:** Any time source predictor fields on a record are modified between bulk predict job runs. In fast-moving sales environments with frequent record updates, scores can be days out of date.

**How to avoid:** Schedule recurring bulk predict jobs in Model Manager to run at a cadence that matches data change frequency — daily is the standard recommendation. For use cases that require near-real-time score updates on individual records (e.g., rep-facing screen flows), use the Einstein Discovery Action in a record-triggered Flow to call the model on record save. Be aware that record-triggered Flow scoring counts against the org's daily predictions limit.

---

## Gotcha 3: Einstein Discovery Action in Flow Always Uses the Currently Active Model

**What happens:** An admin promotes a new model version to Active after a refresh. The next time any Flow containing an Einstein Discovery Action runs, it automatically calls the new active model — with no Flow reactivation, no Flow version change, and no warning to the admin. If the new model has different output characteristics (different predictor field mappings or score range), Flow output can change unexpectedly.

**When it occurs:** Any time the active model version on a prediction definition is changed while a Flow using that prediction definition is live and active.

**How to avoid:** Before promoting a new model version to Active, test it on a sandbox or scratch org. After promotion in production, validate that the Einstein Discovery Action output variables in the Flow still map correctly to the expected fields. Pay particular attention to any hard-coded thresholds or decision branches in the Flow that depend on the predicted value range.

---

## Gotcha 4: Model Manager Drift Alerts Require Explicit Configuration — They Are Not On by Default

**What happens:** An admin assumes Model Manager will automatically notify them if model accuracy degrades or prediction distribution shifts significantly. No alerts arrive, and the team continues using a model that has drifted from its training data.

**When it occurs:** Any deployment where the admin does not configure alert thresholds in Model Manager after deploying the prediction definition.

**How to avoid:** In Model Manager, navigate to the prediction definition > Alerts (or Monitoring configuration) and set explicit thresholds for accuracy drop and prediction distribution drift. Confirm the notification recipient list is correct. Test the alert configuration by reviewing the alert history after the first scoring job completes.

---

## Gotcha 5: Bulk Predict Job Pauses When the Org-Level Daily Predictions Limit Is Reached

**What happens:** A large bulk predict job (e.g., scoring 500,000 Opportunity records) starts running and appears to stall. Model Manager shows the job status as Paused rather than Running or Completed. The admin is unsure whether the job failed or is still in progress.

**When it occurs:** When the cumulative predictions consumed across all prediction definitions in the org reach the org's daily predictions limit. The bulk scoring engine automatically pauses the job rather than failing it. The job automatically resumes on the next calendar day without admin intervention.

**How to avoid:** Monitor bulk predict job status in Model Manager after triggering large jobs. A Paused status is expected behavior — it does not indicate a failure. The job will resume automatically. To reduce the risk of hitting the daily limit, stagger large bulk predict jobs across different prediction definitions rather than running them simultaneously. For orgs approaching their limit regularly, review the prediction limit in the CRM Analytics license and consider whether some prediction definitions can be scored less frequently.
