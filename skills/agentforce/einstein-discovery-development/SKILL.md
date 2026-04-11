---
name: einstein-discovery-development
description: "Use this skill when integrating Einstein Discovery predictions into Salesforce apps, automating bulk scoring jobs, deploying stories as prediction definitions, managing models via API, or querying prediction history. Trigger keywords: Einstein Discovery, smartdatadiscovery, predict endpoint, bulk scoring job, model refresh job, prediction definition, story deployment, regression prediction, multiclass prediction, CRM Analytics ML. NOT for CRM Analytics dashboard design, TCRM dataset management, Einstein Prediction Builder binary classification (which requires no CRM Analytics license), or Einstein Next Best Action recommendation strategies."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I call Einstein Discovery predictions from Apex or an external system?"
  - "My bulk prediction scoring job paused and I need to understand why it stopped"
  - "How do I deploy a story model and surface prediction scores on a Lightning record page?"
  - "I need to refresh my Einstein Discovery model automatically on a schedule"
  - "How do I get prediction factors and improvement suggestions from the Discovery REST API?"
tags:
  - einstein-discovery-development
  - einstein-discovery
  - prediction-api
  - bulk-scoring
  - model-management
  - crm-analytics
  - smartdatadiscovery
inputs:
  - "CRM Analytics (Tableau CRM) license confirmed in the org"
  - "An existing Einstein Discovery story built and at least one model in Enabled status"
  - "The prediction definition ID (1OR prefix) for the model to call"
  - "Salesforce record IDs or raw row data to score, or a bulk job schedule requirement"
  - "Whether prediction factors (top predictors) and improvements (prescriptions) are required in the response"
outputs:
  - "Correct Connect REST API endpoint path and request body for single or bulk prediction calls"
  - "Bulk predict-job configuration, including how to handle daily limit pauses"
  - "Model refresh job setup guidance for automated retraining schedules"
  - "Field mapping configuration for embedding prediction scores on Salesforce records"
  - "Prediction history query pattern using the predicthistory endpoint"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Einstein Discovery Development

Use this skill when a practitioner needs to programmatically integrate Einstein Discovery predictions into Salesforce—calling the Connect REST API to score records, running bulk predict jobs, deploying story models to Lightning pages, managing model refresh schedules, or querying prediction history. This skill covers the full development lifecycle: story creation through API, prediction definition management, batch scoring orchestration, and surfacing insights in the Salesforce UI.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License confirmation:** Einstein Discovery requires a CRM Analytics (formerly Tableau CRM) license. This is distinct from Einstein Prediction Builder, which does not require a CRM Analytics license. If the org does not have CRM Analytics provisioned, Einstein Discovery features and the `/smartdatadiscovery/` API endpoints are unavailable.
- **Prediction definition ID:** Every API call to score records or manage bulk jobs requires the prediction definition ID (prefix `1OR`). Retrieve it with `GET /services/data/vXX.0/smartdatadiscovery/predictiondefinitions`. Do not confuse this with the story ID or the model ID.
- **Scoring is batch or on-demand, never event-driven:** Einstein Discovery prediction scores written to Salesforce record fields are populated by bulk scoring jobs or by an explicit API call. Changing a field value on a record does not automatically re-score it. Plan for explicit job triggers or scheduled batch runs.
- **Daily predictions limit:** Each org has a daily predictions limit enforced across all prediction definitions. Bulk scoring jobs automatically pause when this limit is reached and resume the next calendar day. Build monitoring logic that handles `Paused` job status.

---

## Core Concepts

### Prediction Definitions and the Story Lifecycle

A **story** is the authored analytical artifact in Einstein Discovery. Once a story is complete, it can be deployed as a **prediction definition**, which links the trained model to a Salesforce entity (object) and makes it callable via API. A prediction definition has a unique ID with prefix `1OR`. Prediction definitions can have multiple models, and one model is designated active at a time. The active model is used for all real-time and bulk predictions unless explicitly overridden.

Stories are managed through the Stories Resources in the Connect REST API (`/services/data/vXX.0/smartdatadiscovery/stories`). Prediction definitions are managed separately via `/smartdatadiscovery/predictiondefinitions`.

### Single-Record vs. Bulk Prediction

The **Predict endpoint** (`POST /smartdatadiscovery/predict`) accepts up to 200 record IDs or raw data rows per call. It returns a synchronous response. Use this for real-time scoring in Apex callouts, Flow, or external integrations.

**Bulk predict jobs** (`/smartdatadiscovery/predictjobs`) are asynchronous batch jobs designed to score large populations—all records matching a filter, all records in a terminal state, or historical data for model validation. Bulk jobs run in the background and can be monitored by polling the job's status field. Status values include `Queued`, `Running`, `Paused`, `Completed`, and `Failed`. The `Paused` state is specifically caused by the org-level daily predictions limit; the job automatically resumes the next day without user intervention.

### Model Management and Refresh Jobs

**Model metadata** is managed via the Model Resources (`/smartdatadiscovery/models`). These endpoints let you retrieve model coefficients, metrics, field importance rankings, and the model card. Importantly, these REST endpoints update model metadata only—they do not retrain the predictive model itself.

**Model refresh jobs** (`/smartdatadiscovery/refreshjobs`) trigger a retraining of the Einstein Discovery model against current data. A refresh job reads the story configuration and re-executes the model training pipeline. Refresh jobs are configured via the Model Manager in CRM Analytics setup and can also be triggered programmatically. After a refresh job completes, the new model version must be explicitly activated as the prediction definition's active model before it is used for scoring.

### Prediction Factors and Improvements (Prescriptions)

Starting in API version 50.0, the predict endpoint returns only the score by default. To retrieve the **top predictors** (middleValues) and **improvement suggestions** (prescriptions), include a `settings` object in the request body with `maxPrescriptions`, `maxMiddleValues`, and `prescriptionImpactPercentage`. These fields were previously returned by default before v50.0, so older integrations may break if migrated to newer API versions without adding explicit settings.

---

## Common Patterns

### Pattern 1: Apex Callout for Single-Record Prediction

**When to use:** A Lightning component, trigger, or Flow invocable method needs a real-time prediction score for a single Opportunity or Case record at the moment the user is working with it.

**How it works:**
1. Authenticate via OAuth (session ID or Named Credential).
2. POST to `/services/data/v66.0/smartdatadiscovery/predict` with the prediction definition ID and the record ID(s).
3. Parse the response's `predictions[0].prediction.total` for the score, and `predictions[0].prescriptions` for improvement suggestions.
4. Return the score to the calling component or write it to a custom field.

**Why not polling bulk jobs:** For single-record on-demand scoring, bulk jobs add unnecessary latency. Use the synchronous predict endpoint for up to 200 records.

### Pattern 2: Scheduled Bulk Scoring Job for Mass Re-Scoring

**When to use:** After a model refresh, or nightly to keep prediction score fields current across all Account or Opportunity records.

**How it works:**
1. POST to `/smartdatadiscovery/predictjobs` with the prediction definition ID and a filter to scope records.
2. Store the returned job ID.
3. Poll `GET /smartdatadiscovery/predictjobs/{jobId}` until status is `Completed`, `Failed`, or `Paused`.
4. If `Paused`, log the pause reason (daily limit) and skip retrying—the job resumes automatically next day.
5. On completion, prediction scores are written to the configured output fields on each record.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single or small set of records needing real-time score in a user interaction | `POST /smartdatadiscovery/predict` with type `Records`, up to 200 IDs | Synchronous, low latency, returns factors and prescriptions |
| Re-score all records after model retrain | Bulk predict job via `/smartdatadiscovery/predictjobs` | Designed for large populations; handles daily limits automatically |
| Predict against data not in Salesforce records (hypothetical scenarios) | `POST /smartdatadiscovery/predict` with type `RawData` | Accepts raw column values without requiring existing record IDs |
| Retrieve which fields drive predictions (model explainability) | `GET /smartdatadiscovery/models/{modelId}/metrics` | Returns feature importance and model coefficients without invoking scoring |
| Retrain model on fresh data | Trigger a refresh job via `/smartdatadiscovery/refreshjobs` and activate result | Re-executes story training pipeline; new model must be activated separately |
| Binary yes/no outcome, no CRM Analytics license | Use Einstein Prediction Builder instead | EPB requires no CRM Analytics license; Einstein Discovery requires it |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites:** Verify the org has a CRM Analytics license, that at least one story has been built and deployed as a prediction definition, and that the prediction definition is in `Enabled` status. Retrieve the prediction definition ID using `GET /services/data/vXX.0/smartdatadiscovery/predictiondefinitions`.
2. **Determine scoring mode:** Decide whether the use case requires real-time single-record scoring (synchronous predict endpoint) or bulk population scoring (predict jobs). This determines the API path, authentication pattern, and error handling required.
3. **Construct and validate the request:** Build the request body with the correct `type` (`Records`, `RawData`, or `RecordOverrides`), the prediction definition ID, and—if factors or improvements are needed—the `settings` object with `maxPrescriptions` and `maxMiddleValues`. Test against a small set before full-scale scoring.
4. **Handle daily limit pauses (bulk jobs only):** Implement polling logic that gracefully handles the `Paused` status. Do not attempt to restart a paused job; it resumes automatically. Log the pause event and set an alert if the job remains paused beyond the expected daily reset window.
5. **Activate new model versions after refresh:** If a model refresh job has been triggered, poll its status and, upon completion, use the Model Resources endpoints to activate the new model version on the prediction definition before running the next bulk scoring job.
6. **Verify output field population:** After a bulk scoring job completes, spot-check prediction score fields on target records using SOQL to confirm the job wrote output correctly. Check for `missingColumns` in the `importWarnings` section of the response, which indicates field mapping gaps.
7. **Review and document limits:** Record the daily predictions limit consumed, the model version active on each prediction definition, and the refresh schedule. Keep these in operational runbooks; they are critical for capacity planning.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CRM Analytics license confirmed; org is not relying on Einstein Prediction Builder for this use case
- [ ] Prediction definition ID (1OR prefix) confirmed and status is `Enabled`
- [ ] Correct API version specified in the URL path (minimum v31.0 for basic predict; v50.0+ for explicit factors/prescriptions settings)
- [ ] `settings` object included if prediction factors or improvement suggestions are required
- [ ] Bulk job polling logic handles `Paused` status without attempting manual restart
- [ ] Model refresh job completion triggers explicit model activation before next scoring run
- [ ] `importWarnings.missingColumns` checked in predict responses to catch field mapping gaps
- [ ] Daily predictions limit and model version documented in operational runbook

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Prediction scores are not event-driven** — Changing a field value on a Salesforce record does not trigger re-scoring. Scores are written by bulk predict jobs or explicit API calls. Teams that expect scores to update in real time after field edits will see stale data until the next scheduled job runs.
2. **`settings` object required from API v50.0 onward for factors** — Before v50.0, the predict endpoint returned top predictors and prescriptions by default. Starting in v50.0, only the score is returned unless `settings.maxPrescriptions` and `settings.maxMiddleValues` are explicitly set in the request. Integrations migrated from older API versions silently lose explainability data.
3. **Bulk jobs pause on daily limit, not fail** — When an org reaches its daily predictions limit, a running bulk scoring job transitions to `Paused` status, not `Failed`. Code that treats non-`Completed` statuses as errors will incorrectly flag this as a failure and may attempt unnecessary restarts or alert on a non-issue.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Predict API request body | JSON payload for `POST /smartdatadiscovery/predict` with correct type, prediction definition ID, records, and optional settings |
| Bulk predict job configuration | Job creation payload and polling logic for `POST /smartdatadiscovery/predictjobs` |
| Model refresh job trigger | API call sequence to trigger retraining and activate the resulting model version |
| Prediction history query | Request to `GET /smartdatadiscovery/predicthistory` scoped to a time range and prediction definition |
| Field mapping review | Checklist of `importWarnings.missingColumns` to resolve before running production scoring |

---

## Related Skills

- `einstein-prediction-builder` — Use instead when the outcome is binary (yes/no), no CRM Analytics license is available, or the point-and-click EPB setup is preferred over story-based ML
- `einstein-next-best-action` — Use when prediction scores feed into recommendation strategies for NBA offers or actions
- `analytics-dataset-management` — Use when the Einstein Discovery story's data source is a CRM Analytics dataset that needs preparation or refresh before model training
