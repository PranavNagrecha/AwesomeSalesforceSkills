# Examples — Einstein Discovery Deployment

## Example 1: Activating a Refreshed Model and Re-Scoring Existing Opportunities

**Context:** A sales operations admin has set up a weekly model refresh job for an Einstein Discovery opportunity win-rate model. The refresh job completed overnight but the Predicted Win Rate field on Opportunity records still shows values from the old model.

**Problem:** The admin assumes the refresh automatically updates the model used for scoring. The records continue to show stale predictions based on the previous model version, and the team is making decisions on outdated scores.

**Solution:**

```
Step 1 — In Setup, navigate to Model Manager (or CRM Analytics Studio > Model Manager).
Step 2 — Open the prediction definition for the opportunity win-rate model (1OR prefix).
Step 3 — Click the Models tab. Locate the newly refreshed model version (highest version number
          or latest Created Date). Confirm status is "Enabled".
Step 4 — Click the new model version row > Set as Active.
          Confirm the Active badge moves to the new version.
Step 5 — Navigate to Scoring Jobs > New Scoring Job.
          Select "All records" (or the appropriate record filter).
          Run immediately (do not wait for the next scheduled run).
Step 6 — Monitor the job status until it shows Completed.
          Spot-check several Opportunity records — the Predicted Win Rate field
          should now reflect values computed by the new model.
```

**Why it works:** Model refresh and model activation are separate actions. The refresh creates a new model version but leaves the active version unchanged. Scoring jobs always use the active model. Explicitly promoting the new version to Active, then triggering a fresh bulk predict job, ensures all records are scored with the updated model.

---

## Example 2: Adding Einstein Discovery Recommendations to a Screen Flow for Sales Reps

**Context:** A sales operations admin wants reps to see Einstein Discovery win-rate predictions and improvement actions while working a deal inside a guided screen flow, without requiring any Apex development.

**Problem:** The team previously assumed they needed a developer to write Apex callouts to the Connect REST API to surface predictions inside a Flow. This created a backlog dependency.

**Solution:**

```
Step 1 — Confirm the prediction definition (1OR prefix) is Active and the correct
          model version is promoted. Note the prediction definition name.

Step 2 — In Flow Builder, create a new Screen Flow (or open the existing one).

Step 3 — Add an Action element. In the action search, type "Einstein Discovery".
          Select the "Einstein Discovery" action type.

Step 4 — Configure the action:
          - Prediction Definition: select [your prediction definition name]
          - Input Mappings: map Opportunity fields (Amount, StageName, CloseDate, etc.)
            to the action's input parameters. These must match the predictor fields
            the story was trained on.
          - Output Mappings: map the action's output variables to Flow variables:
              {!PredictedWinRate}    ← Predicted Value output
              {!TopFactor1}         ← Top predictor 1
              {!TopFactor2}         ← Top predictor 2
              {!ImprovementAction1} ← First improvement recommendation

Step 5 — Add a Screen element after the action. Display the Flow variables in
          Display Text or custom components to show the rep:
          "Predicted Win Rate: {!PredictedWinRate}%"
          "Top Factor: {!TopFactor1}"
          "Recommended Action: {!ImprovementAction1}"

Step 6 — Save and Activate the Flow. Test with a sample Opportunity record.
```

**Why it works:** The Einstein Discovery Action in Flow is a first-class declarative element — no Apex, no REST API configuration needed. The action calls the active model in the prediction definition at Flow runtime, returns output as Flow variables, and the admin maps those variables to screen components. The entire integration is admin-configurable in Flow Builder.

---

## Anti-Pattern: Expecting Records to Auto-Update When Predictor Fields Change

**What practitioners do:** After deploying a prediction definition and running the initial bulk predict job, admins assume that when a sales rep updates the Opportunity Amount or Stage, the Predicted Win Rate field on that record automatically recalculates.

**What goes wrong:** The prediction score field does NOT update on record save. The score remains at whatever value was written by the last bulk predict job. Reps see stale predictions — a deal that has been updated significantly may still show the prediction from days ago. This erodes trust in Einstein Discovery recommendations.

**Correct approach:** Schedule recurring bulk predict jobs in Model Manager (daily or more frequently for dynamic data). The scoring engine writes updated prediction scores on all records in scope each time the job runs. For near-real-time scoring on individual records where latency matters, use the Einstein Discovery Action in a record-triggered Flow — but understand that this adds to the org's daily predictions limit consumption. For most admin deployments, a daily scheduled bulk predict job is the right balance between freshness and limit consumption.
