# LLM Anti-Patterns — Einstein Discovery Deployment

Common mistakes AI coding assistants make when generating or advising on Einstein Discovery deployment. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Model Refresh Automatically Activates the New Version

**What the LLM generates:** Instructions like "schedule a weekly model refresh job; the org will automatically use the new model when the job completes" or a runbook that ends after the refresh step with no activation step included.

**Why it happens:** LLMs conflate "refresh" (retraining) with "deploy" (activation). Training data often describes CI/CD pipelines where build completion implies deployment. Einstein Discovery decouples these: a completed refresh job creates a new model version but does not promote it to Active.

**Correct pattern:**

```
Model refresh → job status = Completed
   ↓
Model Manager > [Prediction Definition] > Models tab
   ↓
Identify new version (highest version number) → Set as Active
   ↓
Trigger bulk predict job to re-score records with the newly active model
```

**Detection hint:** Any guidance that describes model refresh without an explicit "Set as Active" step is incomplete. Look for the phrase "refresh completes automatically" or "the new model is automatically deployed" — both are incorrect.

---

## Anti-Pattern 2: Expecting Records to Get Updated Scores When Their Fields Change

**What the LLM generates:** Statements like "when a rep updates the Opportunity Amount, the Predicted Win Rate field will refresh automatically" or "Einstein Discovery scores update in real time as records change."

**Why it happens:** LLMs associate field changes with formula field recalculation or roll-up summary updates, which do happen automatically on record save. Einstein Discovery output fields do not follow this pattern — they are written by the bulk scoring engine, not by record triggers.

**Correct pattern:**

```
Field value changes on a record → prediction score does NOT change
Prediction score only changes when:
  1. A bulk predict job runs and covers that record, OR
  2. The Einstein Discovery Action in a record-triggered Flow executes on that record save
      (uses daily predictions limit per execution)
```

**Detection hint:** Any mention of "real-time prediction updates" or "auto-refresh on field change" for Einstein Discovery output fields without reference to the Flow action or a bulk job is incorrect.

---

## Anti-Pattern 3: Conflating the Admin Deployment Workflow With the Developer API Integration

**What the LLM generates:** When asked how to add Einstein Discovery predictions to a record page, the LLM responds with Apex code calling `/services/data/vXX.0/smartdatadiscovery/predict`, or describes REST API authentication and endpoint configuration — developer constructs that are not part of the admin deployment path.

**Why it happens:** LLMs have more training data on API-based integrations and Apex patterns. The declarative admin surface (Model Manager, page layout editor, Flow Einstein Discovery Action) is less prominent in developer-focused documentation.

**Correct pattern:**

```
Admin deployment path (this skill):
  - Activate prediction definition in Model Manager (Setup UI)
  - Add output fields to page layout or Lightning record page (point-and-click)
  - Configure Einstein Discovery Action in Flow Builder (declarative, no code)
  - Schedule bulk predict jobs in Model Manager (Setup UI)

Developer API path (agentforce/einstein-discovery-development skill):
  - POST /services/data/vXX.0/smartdatadiscovery/predict (Apex callout)
  - POST /smartdatadiscovery/predictjobs (programmatic bulk job)
  - PATCH /smartdatadiscovery/predictiondefinitions/{id} (API model management)
```

**Detection hint:** If the guidance includes `smartdatadiscovery` API endpoints, Apex HTTP callout classes, or Named Credentials for a question about admin-level deployment, it is on the wrong skill path.

---

## Anti-Pattern 4: Not Scheduling Bulk Predict Jobs After Model Activation

**What the LLM generates:** A deployment runbook that ends at "activate the prediction definition" or "set the model as active." The runbook does not include a step to run or schedule a bulk predict job. The result is a deployed prediction definition with no prediction scores on any existing records.

**Why it happens:** LLMs treat "activation" as the final step in a deploy workflow, analogous to publishing a Flow or deploying metadata. They do not account for the separate job-run step required to populate scores on existing records.

**Correct pattern:**

```
Post-activation steps (mandatory):
  1. Run an initial bulk predict job immediately after first activation
     (existing records have no scores until a job runs)
  2. Schedule recurring bulk predict jobs (daily recommended)
     to keep scores fresh as source field values change
  3. Monitor first scheduled job to confirm Completed status
```

**Detection hint:** Any deployment checklist that ends at "activate prediction definition" without a following "run bulk predict job" step is incomplete. Existing records remain unscored.

---

## Anti-Pattern 5: Assuming Model Manager Monitoring Requires No Configuration for Drift or Failure Alerts

**What the LLM generates:** Statements like "Model Manager automatically alerts admins when model accuracy drops" or "the system will notify you if the model drifts from its training data."

**Why it happens:** LLMs generalize monitoring behavior from systems that ship with default alerting. Einstein Discovery's Model Manager provides monitoring surfaces but does not send notifications unless alert thresholds are explicitly configured by an admin.

**Correct pattern:**

```
Model Manager post-deployment configuration:
  1. Navigate to the prediction definition > Alerts (or Monitoring)
  2. Set accuracy drop threshold (e.g., alert when AUC drops below 0.75)
  3. Set prediction distribution drift threshold
  4. Confirm notification recipient list
  5. Test alert configuration by reviewing the alert history tab after
     the first scoring job completes
  
Default state: no alerts are sent until thresholds are configured.
```

**Detection hint:** Any guidance that says alerts, drift detection, or failure notifications are "automatic" or "built-in" without referencing configuration steps is incorrect for Einstein Discovery Model Manager.
