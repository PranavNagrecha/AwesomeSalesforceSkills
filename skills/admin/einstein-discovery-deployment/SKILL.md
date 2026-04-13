---
name: einstein-discovery-deployment
description: "Use this skill when deploying a trained Einstein Discovery model to production records declaratively — activating a prediction definition, mapping output fields to page layouts, adding the Einstein Discovery Action to a Flow, running bulk predict jobs, and monitoring model health via Model Manager UI. Trigger keywords: prediction definition activation, bulk predict job, Einstein Discovery Flow action, Model Manager, prediction field mapping, model refresh activation, scoring job, Einstein Discovery recommendations on record. NOT for Einstein Discovery setup or story authoring. NOT for developer API integration (see agentforce/einstein-discovery-development)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "How do I add Einstein Discovery recommendations to a page layout after training a model?"
  - "Deploying a trained Einstein Discovery model to production records — prediction definition not showing scores"
  - "Einstein Discovery Flow action not showing recommendations for my records"
  - "My model refresh completed but records still show old prediction scores"
  - "How do I schedule bulk predict jobs for Einstein Discovery in Model Manager?"
tags:
  - einstein-discovery
  - prediction-definition
  - model-deployment
  - bulk-predict
  - flow-action
  - model-manager
  - crm-analytics
  - admin
inputs:
  - "CRM Analytics (Tableau CRM) license confirmed in the org"
  - "An Einstein Discovery story with at least one trained model (Enabled status)"
  - "The prediction definition ID (1OR prefix) for the story to deploy"
  - "Target Salesforce object and record IDs for bulk scoring"
  - "Page layout or Lightning App Builder page where prediction scores should surface"
outputs:
  - "Activated prediction definition with output fields mapped to Salesforce object fields"
  - "Einstein Discovery Action configured in a Flow for in-record recommendations"
  - "Bulk predict job triggered to populate prediction scores on existing records"
  - "Model Manager monitoring configuration with scheduled refresh and scoring jobs"
  - "Checklist confirming deployment is complete and scoring is live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Einstein Discovery Deployment

Use this skill when an admin needs to deploy a trained Einstein Discovery model declaratively — activating the prediction definition, mapping prediction output fields to record pages, configuring the Einstein Discovery Action in Flow, and monitoring model health in Model Manager. This skill covers the declarative admin path only. For developer API integration (Connect REST API, bulk scoring via code, programmatic model refresh), use `agentforce/einstein-discovery-development`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License confirmation:** Einstein Discovery requires a CRM Analytics (formerly Tableau CRM) license. Confirm the license is provisioned before attempting any deployment step.
- **Story readiness:** The Einstein Discovery story must be complete and have at least one model in Enabled status. You cannot create a prediction definition from a story that has no trained model.
- **Prediction definition ID:** Every deployment step centers on the prediction definition (prefix `1OR`). Locate it in Setup > Prediction Definitions or in the Model Manager. Do not confuse this with the story ID or the model ID.
- **Scoring is NOT automatic:** Changing field values on a record does NOT automatically update its prediction score. Bulk predict jobs must be run explicitly to refresh scores. Plan scheduled jobs accordingly.
- **Model refresh does NOT auto-activate:** After a model refresh job completes, the new model version is NOT automatically used for scoring. An admin must explicitly set the new version as active on the prediction definition before scoring picks it up.

---

## Core Concepts

### Prediction Definitions and Activation

A **prediction definition** (prefix `1OR`) is the deployable artifact that links a trained Einstein Discovery model to a Salesforce object and exposes output fields (predicted value, top factors, improvement actions) that can be written to records. A prediction definition can have multiple model versions; exactly one version is designated active at any time. The active model is the one used for all scoring — bulk jobs and Flow actions.

After a **model refresh** (retraining), a new model version is created in the prediction definition. This new version is NOT automatically activated. An admin must go to Model Manager > [Prediction Definition] > Models and explicitly promote the new version to Active. Until that step is done, scoring continues against the old model version, even if the refresh job shows Completed.

### Bulk Predict Jobs and Score Freshness

Prediction scores written to Salesforce record fields (e.g., `AI_Prediction__c`, `AI_Factor_1__c`) are populated by **bulk predict jobs**, not by record saves. When source field values on a record change — for example, a deal stage changes or an opportunity amount is updated — the prediction score on that record does NOT automatically update. The score remains stale until a new bulk predict job is run.

Bulk predict jobs must be scheduled explicitly. Admins configure them in Model Manager under the prediction definition's Scoring Jobs section. Best practice is to schedule daily bulk predict jobs aligned with data refresh cadence. For high-volume orgs, be aware of the org-level daily predictions limit; when the limit is reached the job pauses and resumes automatically the next calendar day.

### Output Field Mapping to Page Layouts and List Views

Once a prediction definition is activated, its output fields can be added to page layouts, Lightning record pages, and list views. The output fields are standard fields added to the target object when the prediction definition is created. Common output fields include:

- **Predicted Value** — the model's prediction (e.g., likelihood to close, predicted revenue)
- **Top Predictors** — the strongest factors driving the prediction for that record
- **Improvement Actions (Prescriptions)** — recommended actions to improve the outcome

Map these fields using the standard page layout editor or Lightning App Builder. Output fields appear in the field list for the target object after the prediction definition is saved.

### Einstein Discovery Action in Flow (Declarative)

The **Einstein Discovery Action** is a native Flow action type that invokes an Einstein Discovery prediction in a screen flow, record-triggered flow, or scheduled flow. This is the declarative path — no Apex or REST API code is needed. The action accepts input field values, calls the active model in the prediction definition, and returns prediction output (predicted value, factors, improvements) as Flow variables that can be displayed, stored, or used in Flow logic.

Key configuration points:
- Select the prediction definition by name in the action's configuration panel
- Map source record fields to the action's input parameters
- Map output variables to output fields on the record (for record-triggered flows) or to screen components (for screen flows)
- The Flow action always calls the **currently active model** in the prediction definition — not a specific version

This declarative path is distinct from the developer API path (which uses `POST /smartdatadiscovery/predict` via Apex callout). Admins should use the Flow action; developers integrating Einstein Discovery into custom code should use the Connect REST API skill.

### Model Manager UI and Monitoring

**Model Manager** (Setup > Model Manager or accessed from the CRM Analytics Studio) is the primary admin surface for monitoring Einstein Discovery model health. From Model Manager, admins can:

- View model accuracy metrics (AUC, F1, RMSE depending on prediction type)
- Check scoring job status and history (Queued, Running, Paused, Completed, Failed)
- Schedule or trigger bulk predict jobs
- Schedule or trigger model refresh jobs
- Review prediction drift alerts (when configured)
- Promote a refreshed model version to Active

Drift alerts and prediction accuracy notifications require configuration — they do not activate by default. An admin must configure alert thresholds in Model Manager before any automatic notification is sent.

---

## Common Patterns

### Activating a Refreshed Model Version

**When to use:** After a scheduled or manually triggered model refresh job completes and a new model version needs to be put into production scoring.

**How it works:**
1. In Model Manager, open the prediction definition.
2. Navigate to the Models tab and confirm the refresh job status is Completed.
3. Identify the new model version (highest version number, or check the created date).
4. Click the new model version > Set as Active.
5. Confirm the active model badge moves to the new version.
6. Run a bulk predict job to re-score records with the newly activated model.

**Why not skip step 4:** If you skip explicitly activating the new version, all scoring jobs (including the Flow action) continue using the previous model. The refresh completes silently and the org never benefits from the updated model.

### Scheduling Bulk Predict Jobs for Score Freshness

**When to use:** When source data changes frequently and prediction scores on records must stay current.

**How it works:**
1. In Model Manager, open the prediction definition.
2. Navigate to Scoring Jobs > Schedule.
3. Set the frequency (daily is recommended for most use cases).
4. Select the record filter — typically all active records in scope.
5. Save the schedule. The next job runs at the configured time.
6. Monitor job status in the Scoring Jobs history view. If the job shows Paused, the org reached its daily predictions limit; it will automatically resume the next day.

**Why not rely on record saves:** Prediction scores are written by the bulk job engine, not by record triggers. A record save or field update has no effect on the stored prediction score.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Admin wants to surface prediction scores on a record page layout | Add output fields via page layout editor after prediction definition is activated | Output fields are standard object fields; no code needed |
| Recommendation logic needed inside a Flow | Use Einstein Discovery Action (declarative Flow action) | No Apex or REST API code required; admin-configurable |
| Custom Apex or external system needs prediction scores | Use agentforce/einstein-discovery-development skill | This skill covers the Connect REST API path, not admin UI |
| Refresh job completed — scores not updating | Explicitly activate the new model version in Model Manager, then run bulk predict | Refresh does not auto-activate; scores do not auto-refresh |
| Scores are stale on records after source field changes | Schedule or manually trigger a bulk predict job | Scores only update when a bulk job runs |
| Need to monitor model accuracy over time | Configure drift alerts in Model Manager | Alerts require configuration; they are not on by default |

---

## Recommended Workflow

Step-by-step instructions for an admin deploying an Einstein Discovery model declaratively:

1. **Verify prerequisites** — Confirm the CRM Analytics license is active, the story is complete, and at least one model is in Enabled status on the prediction definition (1OR prefix). Locate the prediction definition ID in Setup > Prediction Definitions.
2. **Activate the prediction definition** — In Model Manager, open the prediction definition. On the Models tab, confirm the desired model version is Active. If a refresh was recently run, explicitly promote the new version to Active before proceeding.
3. **Map output fields to the page layout** — In Setup > Object Manager > [Target Object] > Page Layouts, add the Einstein Discovery output fields (Predicted Value, Top Predictors, Improvement Actions) to the relevant section. Alternatively, add them via Lightning App Builder for record pages.
4. **Configure the Einstein Discovery Action in Flow (if needed)** — In Flow Builder, add an Einstein Discovery Action element. Select the prediction definition, map input fields from the record to the action's parameters, and map output variables to record fields or screen components. Activate the Flow.
5. **Run an initial bulk predict job** — In Model Manager > Scoring Jobs, trigger a manual bulk predict job to populate prediction scores on all existing records in scope. Do not wait for the first scheduled run — existing records have no scores until a job runs.
6. **Schedule recurring bulk predict jobs** — Configure a daily (or appropriate cadence) scheduled bulk predict job in Model Manager to keep scores fresh as source field values change on records.
7. **Configure monitoring and alerts** — In Model Manager, set up drift alert thresholds and scoring job failure notifications. Confirm the active model, scoring schedule, and alert configuration are all correct before signing off on the deployment.

---

## Review Checklist

Run through these before marking the deployment complete:

- [ ] CRM Analytics license confirmed active in the org
- [ ] Prediction definition (1OR prefix) is in Active status with the correct model version promoted
- [ ] Output fields (Predicted Value, Top Predictors, Improvement Actions) are visible on the target record page layout or Lightning record page
- [ ] Einstein Discovery Action in Flow is configured and the Flow is activated (if recommendations in Flow are required)
- [ ] Initial bulk predict job has been run and prediction scores are populated on existing records
- [ ] Recurring bulk predict job is scheduled with the correct frequency and record filter
- [ ] Model Manager drift alerts and scoring job failure notifications are configured
- [ ] Scoring job status confirmed as Completed (not Paused or Failed) after the initial run

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Model refresh does NOT auto-activate the new version** — After a refresh job completes, the new model version is created but NOT set as the active model. Scoring continues against the old version until an admin explicitly promotes the new version on the prediction definition in Model Manager. Many admins run refresh jobs on a schedule and assume the org automatically benefits from the new model — it does not.
2. **Records do NOT auto-update when source field values change** — Prediction scores on Salesforce records are static values written by the bulk predict engine. When a field used as a predictor (e.g., Amount, Stage) changes, the prediction score on that record does NOT change automatically. Only an explicit bulk predict job updates the stored score. Failing to schedule recurring jobs leads to increasingly stale scores across the org.
3. **Einstein Discovery Action in Flow calls the active model, not a specific version** — If the active model is changed (e.g., a new version is promoted after a refresh), the Flow action immediately starts using the new model on the next execution — no Flow reactivation is needed, but also no warning is given. Admins should validate Flow output after any model version change.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated prediction definition | Prediction definition with the correct model version promoted to Active, ready for scoring |
| Output fields on page layout | Einstein Discovery prediction output fields (Predicted Value, Top Predictors, Improvements) mapped to the target object's record page |
| Einstein Discovery Action Flow | A Flow containing the Einstein Discovery Action configured to deliver recommendations declaratively |
| Bulk predict job schedule | A recurring bulk predict job in Model Manager that keeps prediction scores fresh on records |
| Model Manager monitoring setup | Drift alerts and scoring job failure notifications configured in Model Manager |

---

## Related Skills

- `agentforce/einstein-discovery-development` — Use instead when integrating Einstein Discovery predictions programmatically via the Connect REST API, running bulk jobs from code, or managing prediction definitions through the API rather than the admin UI
- `agentforce/einstein-prediction-builder` — Use instead when the outcome is binary (yes/no) and no CRM Analytics license is available; Einstein Prediction Builder is the point-and-click alternative that does not require CRM Analytics
- `agentforce/einstein-next-best-action` — Use when the goal is surfacing action recommendations (Next Best Actions) driven by recommendation strategies, which may or may not use Einstein Discovery as the underlying model
