# Examples — Agentforce Sales AI Setup

## Example 1: Opportunity Scoring Enabled But No Scores Appear After 72 Hours

**Context:** A mid-market Sales Cloud org has enabled Einstein Opportunity Scoring via Setup. The toggle is on, the permission set is assigned to reps, and the Opportunity Score field is on the page layout. Seventy-two hours have passed and no scores appear on any open opportunity records.

**Problem:** The model training silently failed because the org only has 140 closed opportunities with a Closed Date in the last 24 months — below the 200-opportunity minimum. The Setup UI shows the feature as "enabled" and does not proactively warn about insufficient data at enablement time. The only way to discover the issue is to check Setup > Einstein > Opportunity Scoring > Model Status, which shows "Insufficient Data."

**Solution:**

```sql
-- Run in Developer Console or Workbench to check data readiness BEFORE enabling
SELECT COUNT(Id) closedOppsInRange
FROM Opportunity
WHERE IsClosed = true
AND CloseDate = LAST_N_DAYS:730
```

If the result is below 200, do not proceed with Opportunity Scoring enablement. Options:
- Import historical closed opportunity data from a legacy CRM.
- Wait until the org accumulates sufficient data through normal business activity.
- Set stakeholder expectations that scores will not appear until the 200-opportunity threshold is crossed.

Once the data threshold is met, disable and re-enable Opportunity Scoring to trigger a new training evaluation.

**Why it works:** The pre-enablement SOQL check surfaces the data gap before the feature is enabled, preventing the "broken Einstein" perception that occurs when the feature is active but silent.

---

## Example 2: Pipeline Inspection AI Insights Column Missing Despite Einstein Being Active

**Context:** A sales operations admin has enabled Pipeline Inspection and confirmed that Opportunity Scoring is in "Active" model status. The Pipeline Inspection view is accessible to the forecast manager but the AI insights column (predictive deal change signals) is completely absent from the view.

**Problem:** Collaborative Forecasting was not enabled in the org. Pipeline Inspection renders the deal movement and engagement data correctly, but the AI insights layer requires Collaborative Forecasting to be active. There is no error message in Pipeline Inspection indicating this dependency.

**Solution:**

1. Navigate to Setup > Forecasts Settings.
2. Enable Forecasting by checking "Enable Forecasting."
3. Create at least one Forecast Type (e.g., Opportunities by Close Date, Revenue).
4. Assign the appropriate Forecast Manager role to the relevant users.
5. Return to Pipeline Inspection — the AI insights column should now appear within a few minutes.

**Why it works:** Pipeline Inspection AI insights are computed against the Collaborative Forecasting data model. The dependency is real and documented but not surfaced in the Pipeline Inspection Setup UI. Enabling Collaborative Forecasting unblocks the AI layer without requiring any additional Einstein configuration.

---

## Anti-Pattern: Assuming Einstein for Sales Includes Generative Email Composition

**What practitioners do:** An admin provisions the Einstein for Sales add-on license, enables Einstein > Sales > Email, and assigns the Einstein for Sales permission set to reps. Reps report that they cannot find an AI "Generate Email" button when composing emails from Opportunity or Contact records.

**What goes wrong:** Einstein for Sales includes email *insights* (smart email suggestions based on activity history) but does NOT include AI email *composition* (the generative AI "write this email for me" capability). Email composition requires a separate Einstein Generative AI license (formerly Einstein GPT). Without that license, the email composition UI element is never surfaced to users, but there is no explicit error — the feature simply does not appear.

**Correct approach:** Before promising generative email composition to sales reps, verify both licenses in Setup > Company Information > Feature Licenses:
- "Einstein for Sales" (or Einstein 1 Sales edition) for foundational email insights
- "Einstein Generative AI" for AI email composition (draft generation)

If only Einstein for Sales is present, document that email composition is out of scope and escalate a license procurement request to the Salesforce Account Executive.
