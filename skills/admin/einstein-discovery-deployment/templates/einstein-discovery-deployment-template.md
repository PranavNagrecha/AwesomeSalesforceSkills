# Einstein Discovery Deployment — Checklist Template

Use this template when deploying or updating an Einstein Discovery model in a Salesforce org. Complete each section before marking the deployment done.

---

## Deployment Scope

**Prediction definition name:** _______________
**Prediction definition ID (1OR prefix):** _______________
**Target object:** _______________
**Prediction type:** [ ] Binary classification  [ ] Regression  [ ] Multiclass
**Model version being activated:** _______________
**Deployment environment:** [ ] Sandbox  [ ] Production

---

## Prerequisites

- [ ] CRM Analytics (Tableau CRM) license is active in the target org
- [ ] Einstein Discovery story is complete and at least one model is in Enabled status
- [ ] Prediction definition (1OR prefix) exists and is accessible in Model Manager
- [ ] Target Salesforce object fields for output mapping are identified
- [ ] Page layout or Lightning record page for output field display is identified
- [ ] Record filter criteria for bulk predict jobs are defined

---

## Model Activation

- [ ] Opened prediction definition in Model Manager (Setup > Model Manager)
- [ ] Navigated to Models tab and confirmed the desired model version status is Enabled
- [ ] Selected the target model version and clicked "Set as Active"
- [ ] Confirmed the Active badge is on the correct model version
- [ ] Noted the active model version number: _______________

---

## Output Field Mapping

- [ ] Identified Einstein Discovery output fields to surface:
  - [ ] Predicted Value field: _______________
  - [ ] Top Predictor 1 field: _______________
  - [ ] Top Predictor 2 field: _______________
  - [ ] Improvement Action 1 field: _______________
  - [ ] (Additional output fields as needed)
- [ ] Added output fields to page layout via Setup > Object Manager > [Object] > Page Layouts
  - OR added output fields via Lightning App Builder on the relevant record page
- [ ] Confirmed output fields are visible on a sample record in the target org
- [ ] Verified FLS (field-level security) grants read access to the output fields for all relevant profiles/permission sets

---

## Einstein Discovery Action in Flow (if applicable)

- [ ] Flow Builder opened for the relevant Flow
- [ ] Einstein Discovery Action element added and configured:
  - Prediction definition selected: _______________
  - Input field mappings completed (source record fields → action input parameters)
  - Output variable mappings completed (action output → Flow variables or record fields)
- [ ] Flow saved and activated
- [ ] Flow tested with a sample record — predicted value and factors display correctly

---

## Bulk Predict Job — Initial Run

- [ ] Navigated to Model Manager > [Prediction Definition] > Scoring Jobs
- [ ] Triggered a manual bulk predict job (All records or defined filter)
- [ ] Job status monitored until Completed (or Paused if daily limit reached)
  - If Paused: noted and will resume automatically next calendar day — no action needed
- [ ] Spot-checked 3–5 records — prediction output fields now populated with non-null values

---

## Bulk Predict Job — Recurring Schedule

- [ ] Recurring bulk predict job scheduled in Model Manager:
  - Frequency: [ ] Daily  [ ] Weekly  [ ] Other: _______________
  - Record filter: _______________
  - Start time: _______________
- [ ] Schedule confirmed active in Model Manager Scoring Jobs view

---

## Model Manager Monitoring Configuration

- [ ] Drift alert threshold configured: _______________
- [ ] Accuracy drop alert threshold configured: _______________
- [ ] Scoring job failure notification recipient(s) set: _______________
- [ ] Alert configuration tested (confirmed in alert history after first job run)

---

## Model Refresh Sequence (for post-refresh activation)

Run this sequence each time a model refresh job completes:

- [ ] Model refresh job status confirmed as Completed in Model Manager
- [ ] New model version identified on the Models tab (highest version number or latest Created Date)
- [ ] New model version explicitly set as Active ("Set as Active" clicked and confirmed)
- [ ] Bulk predict job triggered immediately after activation to re-score records
- [ ] Spot-check records to confirm scores reflect the newly activated model

---

## Sign-Off

**Deployed by:** _______________
**Date:** _______________
**Active model version:** _______________
**Initial bulk predict job confirmed Completed:** [ ] Yes  [ ] Paused (will auto-resume)
**Monitoring configured:** [ ] Yes  [ ] Deferred (note reason): _______________

**Notes / deviations from standard process:**

_______________

---

## Related Resources

- Model Manager UI: Setup > CRM Analytics > Model Manager
- Einstein Discovery Action in Flow: Flow Builder > New Element > Action > Einstein Discovery
- Official doc: Manage and Deploy Models in Einstein Discovery — https://help.salesforce.com/s/articleView?id=sf.bi_edd_model_manager.htm
- Official doc: Einstein Discovery Action in Flow — https://help.salesforce.com/s/articleView?id=sf.bi_edd_flow_action.htm
