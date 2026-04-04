# Examples — Einstein Copilot for Sales

## Example 1: Opportunity Scoring Not Showing Scores After 48 Hours

**Context:** A Sales Cloud org has just enabled Einstein Opportunity Scoring via Setup. The permission sets are assigned, the `Opportunity Score` field is on the page layout, and 48 hours have passed. Reps open opportunity records and the score field is blank. The admin opens Setup > Einstein > Opportunity Scoring and sees the status "Insufficient Data."

**Problem:** The org has only 140 closed opportunities with a Closed Date in the last two years — below the 200-record minimum. The feature is enabled but the model will not train, so no scores are generated. The UI gives no inline warning on the opportunity record; reps just see a blank field.

**Solution:**

There is no code fix for this — the underlying requirement is data volume. The correct path is:

1. Run an Opportunity report filtered to `IsClosed = true` and `CloseDate >= LAST_N_DAYS:730` to get the exact count.
2. If count < 200, do not expect scores. Communicate to stakeholders that scoring will become available once the pipeline history meets the threshold.
3. If the org is migrating from another CRM, consider importing historical opportunity data (Won and Lost) via Data Loader to meet the threshold faster.
4. Once 200+ closed opportunities exist, return to Setup > Einstein > Opportunity Scoring and click "Retrain Model." Training completes within 24–72 hours.

```text
// SOQL to verify closed opp count for the training window
SELECT COUNT()
FROM Opportunity
WHERE IsClosed = true
  AND CloseDate >= LAST_N_DAYS:730
```

**Why it works:** The training window is exactly the last 730 days (2 years) of Closed Date. Opportunities closed before that window do not contribute to model training even if they exist in the org. Counting within this exact window gives the accurate signal.

---

## Example 2: EAC Emails Relating to Contacts but Not to Opportunities

**Context:** A mid-market sales team has EAC enabled and running. Reps confirm that emails sent to contacts appear on the Contact Activity Timeline. However, the same emails do not appear on the related Opportunity's Activity Timeline, even though the contact is the primary contact on the opportunity.

**Problem:** The EAC configuration profile assigned to these users has the object scope set to `Contacts` and `Leads` only. `Opportunities` is not selected in the profile. EAC matches and relates activities per the object scope configured in the profile — it does not automatically expand relations to parent records unless the profile explicitly includes each object.

**Solution:**

1. Navigate to Setup > Einstein > Einstein Activity Capture > Configuration.
2. Select the configuration profile assigned to the affected users.
3. Under "Activities," expand the object scope and add `Opportunities` to the selected objects.
4. Save and allow 15–30 minutes for the sync to re-evaluate recent emails against the expanded scope.

```text
// No code change required — this is a declarative configuration fix.
// Configuration path:
// Setup > Einstein > Einstein Activity Capture > [Profile Name] > Activities > Object Scope
// Add "Opportunities" to the selected objects list.
```

**Why it works:** EAC evaluates which Salesforce records to relate each synced activity to based on the object scope in the configuration profile. Without `Opportunities` in scope, the system creates the EmailMessage record and relates it to the matching Contact, but does not traverse to the Opportunity even if the contact appears on that opportunity.

---

## Example 3: Pipeline Inspection AI Insights Empty Panel After Enabling

**Context:** A Sales Ops admin enables Pipeline Inspection for the forecast management team. The Pipeline Inspection view loads correctly and shows the deal table. However, the "AI Insights" side panel is empty — no deal health indicators, no score change flags, no risk alerts.

**Problem:** Pipeline Inspection was enabled two weeks before Opportunity Scoring was enabled. The AI insights panel in Pipeline Inspection draws its data from the Opportunity Scoring model. Because the Opportunity Scoring model has not yet completed its first training pass (it was enabled only three days ago), there is no score data for Pipeline Inspection to surface.

**Solution:**

1. Confirm Opportunity Scoring model status: Setup > Einstein > Opportunity Scoring. Status must show "Active" (not "In Progress" or "Insufficient Data").
2. Once the model is Active and scores are visible on opportunity records, the Pipeline Inspection AI insights panel populates automatically on the next page load — no additional configuration is required.
3. If the model status shows "Active" but insights are still empty, check that users viewing Pipeline Inspection have the `Sales Cloud Einstein` permission set and that they manage forecasts with open opportunities that have been scored.

**Why it works:** Pipeline Inspection AI insights are not an independent ML model — they are a presentation layer over Opportunity Score data. The feature cannot surface insights for deals that have no score, so the panel correctly shows empty until scoring data exists.

---

## Anti-Pattern: Assuming Einstein for Sales Includes Generative Email Drafting

**What practitioners do:** An admin purchases Einstein for Sales, enables it, assigns the `Einstein for Sales User` permission set, and then goes to Setup to enable "Einstein Generative Email" or "Einstein Copilot for Sales Email Composition." They cannot find the setting or the setting is greyed out.

**What goes wrong:** Einstein for Sales includes Opportunity Scoring, EAC, Pipeline Inspection insights, and Einstein Email Recommendations (the older, template-based reply suggestions). It does NOT include the generative AI email drafting capability that allows reps to compose full emails from a prompt. That capability is part of Einstein Generative AI (Einstein GPT), which is included in Einstein 1 Sales edition or purchasable as a separate add-on. Without the generative AI license, the compose-with-AI button does not appear in the email activity composer.

**Correct approach:** Before committing to a feature rollout that includes AI email drafting, verify the org's license manifest at Setup > Company Information > Feature Licenses. Look for "Einstein Generative AI" or confirm the edition is "Einstein 1 Sales." If only "Einstein for Sales" appears, either upgrade to Einstein 1 Sales or purchase the Einstein Generative AI add-on before building user enablement materials that reference email drafting.
