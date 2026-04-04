# Gotchas — Einstein Copilot for Service

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Case Classification Model Trains on Closed Cases — Field Null Rates in Historical Data Silently Degrade Model Quality

**What happens:** An admin enables Case Classification and selects several fields (Case Type, Priority, Case Reason). The feature shows "Active" status in Setup after training completes. However, classification suggestions are wrong far more often than expected, or the model shows "Low Confidence" on certain fields.

**When it occurs:** The historical closed case data has high null rates on the selected fields. For example, if 60% of closed cases have `Case Reason` set to null (agents historically left it blank), the model learns that "blank" is a frequently correct label and produces blank or low-confidence predictions. The admin has no inline warning about null rate quality during setup — they only discover the problem after the model trains and suggestions are poor.

**How to avoid:** Before selecting fields for classification, run a SOQL report to measure null rate per field on closed cases:
```text
SELECT COUNT()
FROM Case
WHERE IsClosed = true AND ClosedDate >= LAST_N_DAYS:365 AND CaseType = null
```
Fields with more than 20% null rates in the training population will produce unreliable models. Establish data quality baseline first — enforce required fields on case close via validation rules — then enable classification for those fields after 60–90 days of clean data accumulation.

---

## Gotcha 2: Reply Recommendations Require an Explicit Training Data Job — Enabling the Feature Alone Does Nothing

**What happens:** An admin enables Einstein Reply Recommendations in Setup and assigns the permission set to agents. The feature toggle shows as Active. Agents use messaging channels for days or weeks but see no suggested replies. The admin cannot find an obvious error in Setup.

**When it occurs:** Any time an admin follows the standard Einstein for Service enablement flow without noticing the separate Training Data tab in the Reply Recommendations setup area. Unlike Case Classification — which starts training automatically on save — Reply Recommendations has a decoupled Training Data preparation step that must be manually initiated. Until the Training Data job completes, the recommendation model has no corpus and generates no suggestions.

**How to avoid:** After enabling Reply Recommendations, always navigate explicitly to the Training Data tab and initiate the training job. Confirm job status reaches "Complete" before releasing the feature to agents. Include "Training Data job completed" as a non-negotiable item on the Einstein for Service go-live checklist.

---

## Gotcha 3: Work Summary and Service Replies Are Generative AI Features — They Require Einstein Generative AI License, Not Just Service Cloud Einstein

**What happens:** An admin with Service Cloud Einstein provisioned navigates to Setup > Service > Service Replies with Einstein or Setup > Service > Work Summary and finds the settings greyed out with a tooltip indicating additional licensing is required. The org clearly has an Einstein license (confirmed in Feature Licenses), but the generative features are blocked.

**When it occurs:** Service Cloud Einstein (the add-on license) covers ML-based features: Case Classification, Article Recommendations, and Reply Recommendations. It does NOT include generative AI drafting capabilities. Work Summary and Service Replies require the Einstein Generative AI entitlement, which is only included in Einstein 1 Service edition or as a separately purchased add-on. This split is non-obvious in the product UI and in Salesforce marketing materials.

**How to avoid:** At the start of any Einstein for Service engagement, audit the Feature Licenses list for both "Service Cloud Einstein" AND "Einstein Generative AI." Build a clear feature-to-license mapping in the project scope document. Do not include Work Summary or Service Replies in the project scope, user training, or go-live materials until Einstein Generative AI entitlement is confirmed.

---

## Gotcha 4: Auto-Routing Inherits Case Classification Errors — Routing Problems Are Usually Classification Problems

**What happens:** After enabling Einstein Auto-Routing, cases start appearing in the wrong queues. The admin audits Omni-Channel routing rules and finds them correctly configured. The routing rules look right on paper, but cases still misroute in production.

**When it occurs:** Auto-Routing uses the field values set by Case Classification to make routing decisions. If the Case Classification model is predicting incorrect values for Case Type or Case Reason — the fields driving the routing rules — those incorrect values cause routing to the wrong queue. The routing engine is functioning correctly; it is routing based on the field values it receives. The defect is upstream in the classification layer.

**How to avoid:** Never enable Auto-Routing before validating Case Classification accuracy. A recommended approach: run Case Classification in suggestion mode for 2–4 weeks, then sample 50–100 recent cases and compare Einstein's suggested field values against what agents actually set. Calculate a per-field accuracy rate. Only enable Auto-Routing when per-field accuracy is at an acceptable threshold for your use case (typically 80%+). Add "Classification accuracy sampled and validated" to the Auto-Routing go-live checklist.

---

## Gotcha 5: Article Recommendations Degrade If Agents Stop Linking Articles to Cases

**What happens:** Einstein Article Recommendations are working well at launch — agents see relevant articles and the adoption metrics look good. Three months later, recommendation quality has dropped noticeably. Articles being surfaced are less relevant or increasingly generic. No configuration change was made.

**When it occurs:** The Article Recommendations model is trained on case-to-article association history — cases where agents attached or linked a Knowledge article to the case (signaling that article helped solve the issue). If agents change their resolution behavior and stop attaching articles (e.g., they start copying article content into the case comments instead), the training feedback loop breaks. The model's signal degrades over time as old associations age out of the training window and no new associations are being created.

**How to avoid:** Treat agent article-linking behavior as a managed process, not a one-time training event. Include "Attach article to case at resolution" as a formal workflow step in agent SOPs and coaching programs. Monitor article-to-case attachment rates as an operational KPI alongside recommendation click-through rate. If attachment rates drop, investigate whether the workflow step is being skipped before assuming the model has degraded.

---

## Gotcha 6: Case Classification Does Not Validate in Sandboxes the Same as Production

**What happens:** An admin enables Case Classification in a full sandbox for testing. After waiting 24–72 hours, the model status shows "Insufficient Data" or suggestions never appear on cases created in the sandbox.

**When it occurs:** Full sandboxes are refreshed from production data, but sandboxes may have significantly fewer closed cases depending on the refresh age and the sandbox data mask configuration. Additionally, the Case Classification model in a sandbox trains separately from production and requires its own threshold of closed case data in the sandbox. If the sandbox has a smaller or masked case dataset, the classification model may not meet training thresholds.

**How to avoid:** Use sandbox testing to validate the Case Classification component UI, page layout placement, permission set assignments, and admin setup steps. Do not rely on sandbox to validate that suggestions are accurate or that the model is production-quality. Classification model quality validation must happen in production with real closed case data. Communicate this limitation clearly to stakeholders who expect full end-to-end testing in sandbox.
