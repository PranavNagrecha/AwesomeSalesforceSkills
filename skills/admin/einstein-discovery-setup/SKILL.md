---
name: einstein-discovery-setup
description: "Use this skill when an admin needs to create an Einstein Discovery story in CRM Analytics Studio, configure prediction definitions, deploy writeback fields, set up what-if analysis, or manage model refresh and activation. Trigger keywords: Einstein Discovery story, prediction definition, writeback field, CRM Analytics Studio, model refresh, what-if analysis, bulk scoring, prediction field, 1OR prefix. NOT for Prediction Builder (Einstein Prediction Builder is a separate product requiring no CRM Analytics license). NOT for the developer API path (programmatic scoring via the Connect REST API — see einstein-discovery-development skill)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I create an Einstein Discovery story in CRM Analytics Studio?"
  - "Setting up prediction fields for Einstein Discovery on Opportunity records"
  - "Enabling Einstein Discovery recommendations on records using the admin wizard"
  - "How do I deploy an Einstein Discovery model so scores appear on page layouts?"
  - "Einstein Discovery writeback field is not showing up in reports or page layouts"
tags:
  - einstein-discovery-setup
  - einstein-discovery
  - crm-analytics
  - prediction-definition
  - writeback-field
  - story-creation
  - model-refresh
  - what-if-analysis
inputs:
  - "CRM Analytics license confirmed as provisioned in the org"
  - "Target Salesforce object and outcome field for the story (e.g., Opportunity.IsClosed)"
  - "Whether the use case requires Insights-only or Insights+Predictions (writeback to record fields)"
  - "Confirmation that admin has CRM Analytics Admin permission set or equivalent"
  - "List of explanatory variables (fields) available on the target object or related objects"
outputs:
  - "Guidance for completing the three-step story creation wizard in CRM Analytics Studio"
  - "Prediction definition configuration (1OR prefix, enabled status, target object mapping)"
  - "Writeback field setup instructions including field-level security assignment steps"
  - "Model refresh schedule and manual activation procedure"
  - "What-if analysis configuration guidance for surfacing recommendations on record pages"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Einstein Discovery Setup

Use this skill when an admin needs to configure Einstein Discovery through the CRM Analytics Studio wizard interface — creating stories, deploying prediction definitions, setting up writeback fields on Salesforce objects, enabling what-if analysis for recommendations, and managing model refresh and activation. This skill covers the point-and-click admin path only. For the developer API path (programmatic scoring, bulk predict jobs, REST endpoint integration), use the `einstein-discovery-development` skill instead.

---

## Before Starting

Gather this context before working on anything in this domain:

- **CRM Analytics license:** Einstein Discovery requires a CRM Analytics (formerly Tableau CRM) license. It is not available in orgs without this license. Confirm provisioning in Setup > Company Information > Licenses before starting. This is a distinct license from Einstein Prediction Builder, which does not require CRM Analytics.
- **Admin surface:** Story creation happens in CRM Analytics Studio, not in the main Setup menu. Navigate to App Launcher > Analytics Studio > Create > Story. Admins who look in Setup > Einstein > Einstein Discovery will not find the story wizard there.
- **Writeback field limits:** Einstein Discovery supports a maximum of three writeback fields per Salesforce entity (object). If the org already has three writeback fields on the target object, a new one cannot be created without removing an existing one.
- **Model activation is not automatic:** After a model refresh job completes, the new model version is NOT automatically activated. Scoring continues against the prior model version indefinitely until an admin explicitly activates the new version on the prediction definition. There is no error or warning in the UI when this happens.

---

## Core Concepts

### Story Creation Wizard — Three Steps

Einstein Discovery story creation follows a three-step wizard in CRM Analytics Studio:

1. **Define the outcome variable:** Choose whether to maximize, minimize, or predict a binary outcome on the target field. Binary outcome (true/false, won/lost, converted/not) uses classification models. Numeric outcomes (revenue, score) use regression models. This step also selects the target Salesforce object.

2. **Choose analysis mode:** Select either "Insights only" or "Insights and Predictions."
   - *Insights only* — Einstein analyzes historical data and surfaces correlations and top predictors, but does not deploy a live prediction model that scores records. No writeback field is created.
   - *Insights and Predictions* — Einstein trains a full predictive model (regression or GBM, auto-selected based on outcome type and data profile) and deploys it as a prediction definition that can score new records.

3. **Configure explanatory variables:** Choose which fields from the target object (and related objects) Einstein should use as predictors. More relevant variables generally improve model accuracy, but irrelevant or leakage fields (fields that are only populated after the outcome occurs, such as `CloseDate` on a win prediction) must be excluded to avoid artificially inflated accuracy.

Einstein automatically selects the best-performing model between regression and Gradient Boosting Machine (GBM) based on internal evaluation metrics. Admins do not choose the model algorithm directly.

### Prediction Definition and the 1OR Prefix

When a story is deployed with "Insights and Predictions" mode enabled, Salesforce creates a **prediction definition** — a metadata record that links the trained model to the target Salesforce object. Prediction definitions have IDs with the prefix `1OR`.

The prediction definition is the runtime handle for the deployed model. It controls:
- Which model version is active for scoring
- Which Salesforce object records are scored
- Which writeback fields receive prediction scores
- Whether scoring uses bulk jobs or API calls

Prediction definitions can be viewed and managed in CRM Analytics Studio under the story's Deploy tab, and also via the `PredictionDefinition` metadata in Setup.

### Writeback Fields — System-Managed and Read-Only

A **writeback field** is a special system-managed custom field that Einstein Discovery creates on the target Salesforce object to store prediction scores and improvement suggestions. Key behaviors:

- **Read-only:** The writeback field is system-managed. It cannot be edited by users, Flow, triggers, or direct API updates. Any attempt to set its value via DML will be rejected.
- **Populated only by bulk scoring jobs or explicit API calls:** The field is NOT updated when a record is saved, when a related field changes, or during any normal record lifecycle event. It only updates when a bulk scoring job runs against the prediction definition, or when an explicit scoring API call writes a result.
- **Maximum three per entity:** Each Salesforce object can have at most three Einstein Discovery writeback fields across all prediction definitions. Attempting to create a fourth will fail.
- **Field-level security is not pre-assigned:** After the writeback field is created, FLS is not automatically granted to any profile or permission set. Admins must manually assign read access to the field for the profiles or permission sets that need to see it in reports, list views, and page layouts. Until FLS is assigned, the field is invisible to all users including admins.

### Model Refresh and Manual Activation

Model refresh jobs retrain the Einstein Discovery model against the most current data. Refresh jobs can be triggered manually from the story's Model Manager view in CRM Analytics Studio, or configured to run on a schedule.

Critical behavior: **a completed refresh job does not automatically activate the new model version.** After a refresh completes, the prediction definition continues scoring against the previous model version. The new model version appears in the Model Manager with a status of "Ready" but is not used until an admin explicitly selects it and clicks "Activate." Failing to activate results in silent scoring drift — the model is stale, but no error or notification is shown.

---

## Common Patterns

### Pattern 1: End-to-End Story Deployment with Writeback

**When to use:** An admin needs to create a new Einstein Discovery story on the Opportunity object, deploy it with prediction scoring, and surface the score on the Opportunity record page.

**How it works:**
1. Navigate to Analytics Studio > Create > Story.
2. Step 1: Select Opportunity as the target object, choose the outcome variable (e.g., `IsClosed` binary, or `Amount` numeric).
3. Step 2: Select "Insights and Predictions."
4. Step 3: Add explanatory variables. Exclude any fields that only populate after close (e.g., `CloseDate`, `ContractId`).
5. Let Einstein train the story. After training completes, open the story's Deploy tab.
6. Enable "Prediction" and optionally enable "Improvement Suggestions." This creates the prediction definition and writeback fields.
7. Navigate to Setup > Object Manager > Opportunity > Fields & Relationships, find the new Einstein writeback field (prefixed `Einstein_`) and assign FLS to relevant profiles.
8. Add the writeback field to the Opportunity page layout and optionally embed the Einstein Discovery component for what-if analysis.
9. Trigger an initial bulk scoring job from the Deploy tab to populate the writeback field for existing records.

**Why not skip FLS assignment:** Without FLS, the writeback field is invisible in reports and layouts even for admins. The field technically exists and is being populated, but no user can see the data.

### Pattern 2: Model Refresh Activation After Scheduled Retraining

**When to use:** A scheduled model refresh job has completed and the admin needs to ensure new scores reflect the updated model.

**How it works:**
1. After receiving notification (or checking manually) that a refresh job completed, navigate to Analytics Studio > the story > Model Manager.
2. Confirm the new model version shows status "Ready." Note the accuracy metrics — compare to the previous active version before activating.
3. If the new model performs at least as well as the previous version, click "Activate" on the new version.
4. Trigger a new bulk scoring job from the Deploy tab to rescore all records using the activated model.
5. Verify the writeback field values have updated on sample records in Salesforce.

**Why not skip activation:** If the refresh completed but the new model is not activated, all ongoing scoring — including any bulk jobs triggered after the refresh — continues against the old model version. There is no UI warning, error log, or notification indicating this is happening.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Admin needs predictions without CRM Analytics license | Use Einstein Prediction Builder instead | Einstein Discovery requires CRM Analytics; EPB does not |
| Prediction should update automatically on record save | Use Einstein Prediction Builder | Einstein Discovery writeback fields only update via bulk scoring jobs or API; they are not event-driven |
| Admin needs point-and-click story creation | Use this skill (admin wizard in CRM Analytics Studio) | No-code three-step wizard is the standard admin path |
| Developer needs programmatic scoring via REST API | Use `einstein-discovery-development` skill | The admin wizard and the REST API are separate surfaces; this skill covers only the wizard path |
| Up to three prediction scores needed on one object | Configure up to three writeback fields per entity | System maximum of three writeback fields per object; plan which predictions are most valuable |
| Model refresh has completed but scores look stale | Manually activate new model version in Model Manager, then run bulk scoring job | New model versions are not auto-activated; scoring runs against old version until explicit activation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites:** Verify the org has a CRM Analytics license in Setup > Company Information > Licenses. Confirm the admin has the CRM Analytics Admin permission set. Identify the target Salesforce object and the specific outcome field for the story.

2. **Create the story in Analytics Studio:** Navigate to App Launcher > Analytics Studio > Create > Story. Complete the three-step wizard: (a) define the outcome variable and target object, (b) select "Insights and Predictions" if writeback scoring is required, (c) configure explanatory variables and explicitly exclude leakage fields (fields populated only after the outcome).

3. **Deploy the prediction definition:** After story training completes, open the Deploy tab. Enable "Prediction" to create the prediction definition (1OR prefix). Optionally enable "Improvement Suggestions" for what-if analysis recommendations. Note the prediction definition ID for operational documentation.

4. **Assign field-level security to writeback fields:** Locate the system-generated Einstein writeback field(s) in Setup > Object Manager > [Target Object] > Fields & Relationships. Manually grant read access via FLS to all profiles or permission sets that need to view prediction scores in reports, list views, or page layouts. This step is not automatic and the field is invisible until completed.

5. **Add the writeback field to page layouts and run initial scoring:** Add the writeback field to the relevant page layout. From the Deploy tab, trigger an initial bulk scoring job to populate the field for all existing records. Verify the field is populated on a sample of records after the job completes.

6. **Configure model refresh schedule:** In the story's Model Manager, set up a refresh schedule appropriate to the data change frequency (e.g., weekly or monthly). Document the schedule and the manual activation step required after each refresh.

7. **After each model refresh — activate manually:** When a refresh job completes, review the new model's accuracy metrics in Model Manager, compare against the current active model, and explicitly activate the new model version. Then trigger a new bulk scoring job to update record scores.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CRM Analytics license confirmed in Setup > Company Information > Licenses
- [ ] Story created in Analytics Studio using the three-step wizard (not Setup menu)
- [ ] Leakage fields excluded from explanatory variables in Step 3 of the wizard
- [ ] "Insights and Predictions" selected (not "Insights only") if writeback scoring is required
- [ ] Prediction definition created and status is Enabled (1OR prefix ID noted)
- [ ] Writeback field FLS assigned to all relevant profiles and permission sets
- [ ] Writeback field added to page layout(s) where scores should appear
- [ ] Initial bulk scoring job triggered and writeback field values verified on sample records
- [ ] Model refresh schedule configured and documented
- [ ] Post-refresh activation step documented in admin runbook (new model versions are not auto-activated)
- [ ] Writeback field count on target object confirmed to be three or fewer

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Refreshed model is NOT automatically activated — scoring silently runs against stale model** — After a model refresh job completes, the new model version sits in "Ready" status but is not used for any scoring until an admin explicitly activates it. The system provides no error, warning, or alert indicating that the active model is outdated. This is the most common source of silent model drift in production Einstein Discovery deployments.

2. **Writeback field is read-only and only updates via bulk scoring or API — never on record save** — The Einstein Discovery writeback field is system-managed. Changing field values on the source record does not trigger re-scoring. A flow or trigger that modifies related fields will not cause the writeback field to update. Admins and users who edit records expecting to see updated predictions will see no change until the next bulk scoring job runs.

3. **Maximum three writeback fields per Salesforce entity** — Each Salesforce object can have at most three Einstein Discovery writeback fields across all prediction definitions. If an object already has three and a new deployment attempts to create a fourth, the deployment fails. Audit existing writeback fields before deploying new prediction definitions on high-use objects like Opportunity or Contact.

4. **Writeback field FLS is not granted automatically — field is invisible until manually set** — Einstein Discovery creates the writeback field and populates it via scoring jobs, but does not assign field-level security to any profile or permission set. The field will not appear in reports, list views, page layouts, or SOQL results for any user until an admin explicitly grants read permission via FLS.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Story configuration summary | Outcome variable selection, analysis mode, and explanatory variable list with leakage exclusions noted |
| Prediction definition record | Created 1OR-prefixed prediction definition with Enabled status on the target object |
| Writeback field setup confirmation | Einstein writeback field(s) on the target object with FLS assigned to relevant profiles |
| Page layout update | Writeback field added to the record page layout so users can see prediction scores |
| Model refresh runbook | Documented schedule and manual activation procedure for post-refresh activation |

---

## Related Skills

- `einstein-discovery-development` — Use when a developer needs to call the Einstein Discovery Connect REST API for programmatic scoring, bulk predict jobs, or model management via API (not the admin wizard)
- `einstein-prediction-builder` — Use instead when the outcome is binary (yes/no) and the org does not have a CRM Analytics license, or when the point-and-click EPB setup wizard is preferred for simple binary predictions
- `crm-analytics-vs-tableau-decision` — Use when deciding whether Einstein Discovery (requiring CRM Analytics) is the right tool versus other analytics or ML options in the Salesforce ecosystem
