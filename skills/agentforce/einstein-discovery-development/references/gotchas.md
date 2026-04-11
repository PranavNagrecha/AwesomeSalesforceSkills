# Gotchas — Einstein Discovery Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Bulk Scoring Jobs Pause Silently at the Daily Predictions Limit, Not Fail

**What happens:** When a bulk predict job (`/smartdatadiscovery/predictjobs`) is running and the org reaches its daily predictions limit, the job transitions to `Paused` status and stops processing records. It does not error out. It does not send a notification. It automatically resumes the following calendar day when the limit resets. Any integration that treats `Paused` as an error condition and calls DELETE on the job or alerts as a hard failure will produce false alarms and may interrupt a legitimate scoring run.

**When it occurs:** This is most common in large orgs with multiple prediction definitions running bulk jobs concurrently, or when a nightly scoring job is started too late in the day after other API calls have already consumed most of the limit. The limit is org-wide and shared across all prediction definitions and real-time predict calls.

**How to avoid:** Build polling logic that explicitly branches on `Paused` with a log-and-exit pattern rather than an error-and-retry pattern. Do not delete or recreate paused jobs. If scoring must complete within a day, spread bulk jobs across definitions and schedule them early in the UTC calendar day. Monitor daily prediction consumption separately via the API Total Usage event type.

---

## Gotcha 2: Prediction Factors and Prescriptions Are Opt-In from API Version 50.0 Onward

**What happens:** Prior to API version 50.0, `POST /smartdatadiscovery/predict` returned top predictors (`middleValues`) and improvement suggestions (`prescriptions`) in every response by default. Starting with v50.0, the endpoint returns only the prediction score unless the caller explicitly includes a `settings` object with `maxPrescriptions` and `maxMiddleValues`. Integrations that were built on older API versions and then upgraded to v50.0+ silently lose all explainability data—the score is returned, but `middleValues` and `prescriptions` are empty arrays with no error.

**When it occurs:** Any integration that pins to a specific API version and then upgrades, or any new integration that uses v50.0+ without reading the release notes for the endpoint change. Since there is no error and the score is still returned, the missing explainability data can go unnoticed until users notice the Lightning component no longer shows improvement tips.

**How to avoid:** Always include a `settings` object in predict requests when factors or improvements are required:
```json
{
  "predictionDefinition": "1ORB000000000bOOAQ",
  "type": "Records",
  "records": ["006RM000002bEfiYAE"],
  "settings": {
    "maxPrescriptions": 3,
    "maxMiddleValues": 3,
    "prescriptionImpactPercentage": 75
  }
}
```
Treat empty `prescriptions` and `middleValues` arrays as a signal to audit the request, not assume the model has no relevant factors.

---

## Gotcha 3: A Refreshed Model Must Be Explicitly Activated Before Bulk Scoring Uses It

**What happens:** When a model refresh job completes, the new model version is created in the system with a new model ID, but the prediction definition's active model is NOT automatically switched. The prediction definition continues pointing to the previous model. All subsequent predict calls—both real-time and bulk—use the old model until a developer or admin explicitly activates the new model version on the prediction definition. This means orgs can run weeks or months of scoring against a stale model while believing they are using the updated one.

**When it occurs:** This catches teams who set up automated model refresh jobs (via Model Manager or the refreshjobs endpoint) but do not complete the activation step. The Model Manager UI shows the new model as "inactive" but this is easy to miss if the team relies on API monitoring only.

**How to avoid:** After each refresh job completes (poll `GET /smartdatadiscovery/refreshjobs/{jobId}` for `Completed` status), call `GET /smartdatadiscovery/predictiondefinitions/{predDefId}/models` to identify the new model version, then use the Model Resources endpoint to activate it. Include this activation step as a required phase in any automated retraining pipeline before triggering bulk scoring.

---

## Gotcha 4: `type: Records` Requires the Record IDs to Belong to the Prediction Definition's Subscribed Entity

**What happens:** If you pass record IDs from a different Salesforce object than the one the prediction definition is subscribed to, Einstein Discovery returns a prediction error per record rather than a useful score. The error surface is in `predictions[N].status` being `"Error"` rather than `"Success"`, and the outer HTTP status code is still 200. It is easy to confuse a partial failure (some records succeed, some fail) with a complete success.

**When it occurs:** This happens when developers reuse a predict utility method across multiple objects, or when a prediction definition is rebuilt pointing to a different entity but old record IDs are still passed in test scripts.

**How to avoid:** Before constructing the predict request, verify the prediction definition's `subscribedEntity` field from `GET /smartdatadiscovery/predictiondefinitions/{predDefId}`. Check each prediction in the response for `status: "Error"` separately—do not only check the HTTP response code.

---

## Gotcha 5: Einstein Discovery Requires CRM Analytics License; Einstein Prediction Builder Does Not

**What happens:** Teams researching "Einstein ML predictions" conflate Einstein Discovery with Einstein Prediction Builder. They allocate CRM Analytics licenses, set up the Discovery API integration, and then discover the business requirement was a simple binary outcome (churn: yes/no) that Einstein Prediction Builder handles out of the box without any CRM Analytics license. The reverse also occurs: teams try to build regression or multi-class predictions using Einstein Prediction Builder and discover it only supports binary classification.

**When it occurs:** At the start of a project when the prediction type and licensing requirements are not clarified upfront. Both products appear under the "Einstein" umbrella in Salesforce documentation and admin interfaces.

**How to avoid:** Use this decision matrix at project kickoff:
- Binary yes/no outcome, no CRM Analytics license → Einstein Prediction Builder
- Regression (continuous value), multi-class classification, or time-series → Einstein Discovery (requires CRM Analytics)
- Need for full story narrative, data exploration, and prescriptions → Einstein Discovery

Confirm license availability in Setup > Company Information before committing to either path.
