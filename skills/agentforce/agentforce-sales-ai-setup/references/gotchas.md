# Gotchas — Agentforce Sales AI Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Opportunity Scoring Does Not Train in Sandboxes

**What happens:** Einstein Opportunity Scoring is enabled in a sandbox org. The feature toggle shows active, the permission set is assigned, and the Opportunity Score field is on the page layout. No scores ever appear on opportunity records.

**When it occurs:** Any time an admin or developer attempts to validate Opportunity Scoring in a sandbox (Full, Partial, Developer, or Developer Pro). This is a documented Salesforce platform constraint — model training only occurs against production org data.

**How to avoid:** Do not attempt to validate score generation in a sandbox. Use the sandbox only to test the enablement flow (Setup toggles, permission set assignment, page layout configuration). Validate actual score output in a scratch org loaded with production-representative data, or in the production org itself. Document this limitation clearly in any UAT acceptance criteria so testers do not mark the feature as defective.

---

## Gotcha 2: Pipeline Inspection AI Insights Silently Require Collaborative Forecasting

**What happens:** Pipeline Inspection is enabled and the Opportunity Scoring model is Active. The Pipeline Inspection view loads and shows deal movement data, but the AI insights column (predictive deal change signals, commit risk flags) is completely absent. There is no error, no "feature not available" message, and no Setup validation warning.

**When it occurs:** Whenever Collaborative Forecasting is not enabled in the org at the time Pipeline Inspection is set up. The dependency is not enforced or communicated in the Pipeline Inspection enablement UI or wizard.

**How to avoid:** Always enable and confirm Collaborative Forecasting is active (Setup > Forecasts Settings > Enable Forecasting) before enabling Pipeline Inspection. Verify at least one Forecast Type is configured. This is a pre-enablement gate that must be checked explicitly. Include a Collaborative Forecasting status check in every Einstein for Sales setup checklist.

---

## Gotcha 3: Einstein Generative Email Composition Is a Distinct License from Einstein for Sales

**What happens:** An admin enables Einstein for Sales, assigns the Einstein for Sales permission set to reps, and enables the Email feature in Setup > Einstein > Sales > Email. Reps cannot find the AI email composition ("Generate Email") button in the email composer on Opportunity or Contact records. Enabling and re-enabling the feature does not help.

**When it occurs:** Any time a practitioner assumes that Einstein for Sales includes generative AI email drafting. Einstein for Sales includes email *insights* (suggestions based on rep activity history) but not AI email *composition*. The composition feature requires the Einstein Generative AI add-on license, which is a separate, independently purchased license tier.

**How to avoid:** Check Setup > Company Information > Feature Licenses for both "Einstein for Sales" AND "Einstein Generative AI" before planning email composition rollout. If only Einstein for Sales is present, email composition is unavailable regardless of configuration. Escalate a license procurement request through the Salesforce Account Executive. Do not promise reps the generative email feature until both licenses are confirmed.

---

## Gotcha 4: Opportunity Scoring Feature Appears Active With Zero Scores and No Warning

**What happens:** Setup shows Opportunity Scoring as enabled. Model Status shows "Insufficient Data" — but this status is only visible if an admin navigates to Setup > Einstein > Opportunity Scoring and reads the status field. The Opportunity Score field on records is blank. Reps and admins conclude Einstein is broken.

**When it occurs:** Any org where the closed opportunity count (IsClosed = true, CloseDate in last 24 months) is below 200. The enablement UI allows the toggle to be turned on regardless of data volume. There is no pre-enablement validation gate.

**How to avoid:** Always run a pre-enablement SOQL check before enabling Opportunity Scoring: `SELECT COUNT(Id) FROM Opportunity WHERE IsClosed = true AND CloseDate = LAST_N_DAYS:730`. If the result is below 200, defer enablement and communicate the data gap to stakeholders rather than enabling a feature that will silently produce no output.

---

## Gotcha 5: Opportunity Scoring Model Retrains Weekly — Score Gaps After Data Imports

**What happens:** An org imports historical closed opportunity data to cross the 200-opportunity threshold. Opportunity Scoring is enabled. No scores appear for several days after the import, even though the import is confirmed complete and the record count is well above 200.

**When it occurs:** Opportunity Scoring's model retrains on a weekly schedule. After the initial training completes (24–72 hours post-enablement), the model only picks up newly closed opportunities at the next weekly cycle. If the org was below threshold, crosses it via import, and then re-enables scoring, the next training run still follows the standard weekly cadence — it does not immediately retrain.

**How to avoid:** Set stakeholder expectations that score generation after a data import may take up to 7 days from when the training threshold was crossed. If faster scoring is critical, contact Salesforce Support to request a manual model retrain trigger — this is not available through the self-service Setup UI.
