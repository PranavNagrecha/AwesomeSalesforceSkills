# Gotchas — Opportunity Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleting a Stage Picklist Value Silently Corrupts Active Records

**What happens:** When a Stage picklist value is deleted while Opportunity records still carry that value, Salesforce removes the picklist entry without issuing a blocking error. The Stage field on affected records becomes blank — not replaced with a default, not flagged in a report. Existing records are silently corrupted.

**When it occurs:** Any time an admin deletes (not deactivates) an Opportunity Stage value from Setup > Opportunity Stages while records with that stage exist. This includes sandbox refreshes where stage values are pruned without checking record counts.

**How to avoid:** Before deleting any Stage value:
1. Query: `SELECT COUNT() FROM Opportunity WHERE StageName = 'Old Stage Name'`
2. If count > 0, bulk-reassign those records to an active stage before proceeding.
3. Prefer deactivating the value (unchecking "Active") over deleting it. Deactivation removes it from the picklist dropdown for new records while preserving it on historical closed records.
4. Only hard-delete a Stage value if zero records reference it.

---

## Gotcha 2: ForecastCategoryName Labels Are Platform-Fixed and Cannot Be Renamed

**What happens:** Admins expect to rename forecast category labels (e.g., "Best Case" → "Upside") via Setup > Opportunity Stages or the picklist editor. These labels are not customer-configurable — they are platform-reserved values. Any attempt to rename them either fails with an error or silently reverts.

**When it occurs:** During implementations where business stakeholders want custom forecast category names that match their internal terminology. The category labels visible in forecast reports and the Forecast tab always display the platform values: Pipeline, Best Case, Commit, Closed, Omitted.

**How to avoid:** Communicate to stakeholders early that these five labels are fixed. Use stage names and Path guidance text to express the org's internal terminology. Document the mapping between internal terms and platform labels in training materials. Do not attempt to rename ForecastCategoryName via metadata deploys — the deploy will either fail or be ignored.

---

## Gotcha 3: Opportunity Splits Cannot Be Disabled Once Data Exists

**What happens:** After enabling Opportunity Splits and saving even one split record on an opportunity, the feature cannot be turned off. The "Disable Splits" option in Setup is either removed or non-functional once split data exists. This is permanent for that org.

**When it occurs:** Admins who enable splits in production for a pilot, then try to roll back because the pilot failed or the business process changed.

**How to avoid:** Treat enabling Opportunity Splits in production as a one-way door. Always:
1. Pilot splits in a full sandbox first.
2. Get explicit sign-off from business stakeholders that the split model is permanent.
3. Confirm that Team Selling is enabled before enabling Splits — the platform dependency is hard.
4. Never enable splits in production speculatively or for testing purposes.

---

## Gotcha 4: Team Selling Must Be Enabled Before Opportunity Splits

**What happens:** Attempting to enable Opportunity Splits without first enabling Opportunity Teams (Team Selling) results in a platform error. The Splits Setup page may be inaccessible or show an error message requiring Teams to be enabled first.

**When it occurs:** When an admin enables Splits directly without following the documented setup order, typically when working from memory or an incomplete runbook.

**How to avoid:** The correct order is: (1) Setup > Opportunity Team Settings > Enable Opportunity Teams, then (2) Setup > Opportunity Settings > Enable Opportunity Splits. Never reverse this order. Include this as a step in any deployment runbook involving splits.

---

## Gotcha 5: Path Settings Do Not Enforce Stage Progression

**What happens:** Admins configure Path with stages in a logical order and assume this prevents reps from skipping stages or saving at an unexpected stage. Path is visual guidance only — it has no save-blocking behavior. Reps can freely jump from stage 1 to stage 7 without triggering any error from Path.

**When it occurs:** Any time Path is the sole mechanism relied upon for stage compliance. This is especially common after an admin demonstrates Path in a UAT session where reps manually follow the stages — the UAT passes, but enforcement was never real.

**How to avoid:** Pair Path with validation rules for any progression requirement that must be enforced. Clearly document in the business requirements which stage transitions are required vs. guided. Validation rules using `PRIORVALUE(StageName)` and `ISPICKVAL()` are the correct enforcement mechanism.

---

## Gotcha 6: Stages Assigned to a Sales Process Must Exist Globally First

**What happens:** Admins try to add a new stage directly inside a Sales Process without first creating it in the global Opportunity Stages picklist. The platform requires the stage to exist globally before it can be added to a process. Attempting to bypass this produces an error.

**When it occurs:** When admins confuse the Sales Process editor with the global picklist editor, particularly when onboarding new business units that need custom stages.

**How to avoid:** Always create and configure new Stage values in Setup > Opportunity Stages first (including setting IsClosed, IsWon, Probability, and ForecastCategoryName). Only then return to Setup > Sales Processes to add the new stage to the relevant process.

---

## Gotcha 7: Overlay Split Totals Are Not Validated Against 100%

**What happens:** Revenue splits enforce a total of exactly 100% — the platform blocks saving if the total is not 100%. Overlay splits have no such constraint. Overlay split totals can be 50%, 150%, or 300% — the platform accepts any value. This is by design but surprises admins who expect consistent validation behavior across split types.

**When it occurs:** When admins test overlay splits and expect the same 100% validation they see on revenue splits. Also occurs when auditing overlay data and finding unexpected totals.

**How to avoid:** Document the behavioral difference clearly in user training. For orgs that want to cap overlay credit, implement a custom validation rule or Flow that checks overlay split totals per opportunity if the business requires a limit.
