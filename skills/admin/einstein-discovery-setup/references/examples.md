# Examples — Einstein Discovery Setup

## Example 1: Deploying an Opportunity Win-Rate Prediction with Writeback

**Context:** A sales operations admin wants Einstein Discovery to score all open Opportunities with a predicted win probability and surface the score on the Opportunity record page. The org has a CRM Analytics license.

**Problem:** The admin creates a story and enables predictions, but after training completes and the bulk scoring job runs, the predicted score field does not appear on the Opportunity record page or in reports for any rep.

**Solution:**

After enabling predictions in the Deploy tab and running the bulk scoring job, the admin must complete two steps that Einstein does NOT perform automatically:

1. Assign field-level security to the writeback field:
   - Navigate to Setup > Object Manager > Opportunity > Fields & Relationships
   - Locate the system-created Einstein writeback field (typically prefixed `Einstein_` followed by the prediction name)
   - Click Field-Level Security and grant Read access to all relevant profiles (Sales User, Sales Manager, System Administrator, etc.)

2. Add the field to the Opportunity page layout:
   - Navigate to Setup > Object Manager > Opportunity > Page Layouts
   - Drag the writeback field onto the layout in the desired section
   - Save the layout

After both steps, reps will see the current prediction score on the record page. The score updates only when the next bulk scoring job runs — not when the rep edits the record.

**Why it works:** Field-level security gates who can see any custom field, and a new field is not on any layout until someone adds it. UNVERIFIED (2026-10-03): that Einstein Discovery creates writeback fields with no field-level security at all, that the field is prefixed `Einstein_`, and that it is invisible even to administrators, are help-only claims carried from an earlier version of this example. Granting access explicitly is safe either way.

---

## Example 2: Stale Prediction Scores After Model Refresh

**Context:** A sales operations admin has Einstein Discovery running weekly model refreshes on an Opportunity churn prediction. After a month, the ops team notices that prediction scores stopped reflecting recent deal outcomes. Investigation shows the model was last refreshed successfully three weeks ago.

**Problem:** The model refresh jobs completed successfully each week, but the scores are still based on the original model from four weeks ago.

**Solution:**

Each time a model refresh job completes, the admin must manually activate the new model version before it is used for scoring:

Step-by-step:
1. Navigate to Analytics Studio > open the story > Model Manager tab
2. Find the most recently completed model version — it will show status "Ready" (not "Active")
3. Review the accuracy metrics (AUC, F1, precision/recall for binary, or R² for regression) and compare against the currently active model
4. If the new model is acceptable, click "Activate" on the new version
5. Confirm that the prior version status changes to "Inactive" and the new version shows "Active"
6. Trigger a new bulk scoring job from the Deploy tab so all existing records are re-scored with the new model

The admin should add this activation step to the operational runbook and, if possible, configure an alert or calendar reminder for after each scheduled refresh window.

**Why it works (as reported, UNVERIFIED (2026-10-03): help-only):** Einstein Discovery does not auto-activate refreshed model versions because activation is an intentional quality gate — admins should review model metrics before rolling out a new version to production scoring. The system provides no automatic reminder or warning when scoring is running against a stale model version, so the manual activation step must be operationally tracked.

---

## Anti-Pattern: Creating the Story via Setup Instead of Analytics Studio

**What practitioners do:** Admins who are unfamiliar with Einstein Discovery navigate to Setup > Einstein > Einstein Features or Setup > Einstein > Einstein Discovery and expect to find a story creation wizard. They may find prediction-related setup options but not the full three-step story wizard.

**What goes wrong:** The three-step story creation wizard lives exclusively in CRM Analytics Studio (App Launcher > Analytics Studio > Create > Story). Setup-based Einstein menus contain related configuration (enabling Einstein features, reviewing prediction definitions) but not the full story authoring experience. Admins who cannot find the wizard may incorrectly conclude that Einstein Discovery is not provisioned or that their license is insufficient.

**Correct approach:** Always launch story creation from Analytics Studio. Verify that the CRM Analytics license is provisioned and that the admin user has the CRM Analytics Admin permission set assigned. Then navigate to App Launcher > Analytics Studio > Create > Story to access the three-step wizard.

---

## Example 3: Promoting a Prediction Definition Without Losing the Writeback Field

**Context:** The win prediction from Example 1 is approved in a full sandbox. The release team promotes metadata with the Salesforce CLI.

**Problem:** A previous release retrieved the `DiscoveryGoal` from a developer sandbox where writeback was never configured. The file had no `pushbackField`, and deploying it deleted the production writeback field and its scores.

**Solution:** Retrieve from the org that holds the real configuration, and fail the release if a goal file lost its `pushbackField`:

```bash
# Retrieve the prediction definition and the model it deploys
sf project retrieve start --metadata "DiscoveryGoal:Opportunity_Win_Prediction" "DiscoveryAIModel:Opportunity_Win_Model" --target-org fullsandbox

# Gate: every goal that had a pushbackField on main must still have one
for f in $(git diff --name-only origin/main -- 'force-app/main/default/discovery/*.goal-meta.xml'); do
  if git show "origin/main:$f" 2>/dev/null | grep -q "<pushbackField>" && ! grep -q "<pushbackField>" "$f"; then
    echo "BLOCK: $f dropped pushbackField; deploying it deletes the writeback field"; exit 1
  fi
done
```

**Why it works:** The Metadata API guide states that removing a pushback field from the goal metadata deletes the field from the Salesforce object. The gate turns that rule into a check the release cannot skip. UNVERIFIED (2026-10-03): the source-format file name (`<name>.goal-meta.xml`) follows the usual `-meta.xml` convention for the `.goal` suffix; confirm it against a real retrieve.

