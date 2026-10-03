# LLM Anti-Patterns — Einstein Discovery Setup

Common mistakes AI coding assistants make when generating or advising on Einstein Discovery Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating the Admin Wizard with the Developer REST API

**What the LLM generates:** Instructions that mix the CRM Analytics Studio story wizard steps with Connect REST API endpoint calls, or that direct an admin to use `/smartdatadiscovery/` API endpoints to set up predictions rather than the wizard UI.

**Why it happens:** LLMs are trained on both admin documentation and developer API documentation for Einstein Discovery. The two surfaces are conceptually related (both create and manage predictions) but are separate tools for separate audiences. LLMs frequently blur the boundary and produce hybrid instructions that are correct for neither audience.

**Correct pattern:**

```
Admin path: App Launcher > Analytics Studio > Create > Story
(three-step wizard: outcome variable, analysis mode, explanatory variables)

Developer path: POST /services/data/vXX.0/smartdatadiscovery/predictiondefinitions
(programmatic story deployment and scoring via Connect REST API)

Do not mix these paths in a single set of instructions.
```

**Detection hint:** Look for instructions that tell an admin to "call the API" or use "POST /smartdatadiscovery/" as part of a setup flow, or that tell a developer to "navigate to Analytics Studio" to configure scoring parameters that should be in code.

---

## Anti-Pattern 2: Assuming a Refreshed Model Automatically Activates

**What the LLM generates:** "Schedule model refreshes weekly and Einstein will automatically use the latest model for scoring." Or: "After the refresh job completes, your predictions will reflect the newly trained model."

**Why it happens:** Most ML platforms automatically promote a newly trained model if it meets quality thresholds. LLMs apply this default assumption to Einstein Discovery, where activation is instead an explicit manual admin step. Training data about Einstein Discovery is sparse compared to generic ML pipeline documentation.

**Correct pattern:**

```
Model refresh job completes → new model version status: "Ready" (NOT active)
Admin must navigate to Model Manager → review metrics → click "Activate"
Only then does scoring use the new model version
Trigger a new bulk scoring job after activation to re-score existing records
```

**Detection hint:** Any response that omits the manual activation step after describing model refresh setup is applying this anti-pattern. Flag any mention of "automatic" or "automatically" in the context of model refresh and activation.

UNVERIFIED (2026-10-03): the platform behavior this anti-pattern relies on is documented only on help.salesforce.com, which did not fetch for the 2026-10-03 pass. Test it in a sandbox before stating it to users; see `gotchas.md` gotcha 8.

---

## Anti-Pattern 3: Treating the Writeback Field as Editable or Event-Driven

**What the LLM generates:** "When a rep updates the Opportunity Stage, Einstein will recalculate the prediction score." Or: "You can write to the writeback field using a Flow to override the prediction."

**Why it happens:** Standard Salesforce custom fields are writable and can be updated via Flow, triggers, or direct API. LLMs apply this default behavior to Einstein Discovery writeback fields, which are system-managed and read-only by design.

**Correct pattern:**

```
Writeback field behavior:
- Read-only: cannot be updated by Flow, trigger, DML, or user edit
- Updated ONLY by: bulk scoring job or explicit Einstein Discovery API call
- NOT updated by: record save, field change, related record change, or any normal record lifecycle event
```

**Detection hint:** Any suggestion to use Flow's Update Records action, a trigger's DML operation, or a validation rule that checks the "current" writeback value as if it is real-time data indicates this anti-pattern.

UNVERIFIED (2026-10-03): the platform behavior this anti-pattern relies on is documented only on help.salesforce.com, which did not fetch for the 2026-10-03 pass. Test it in a sandbox before stating it to users; see `gotchas.md` gotcha 8.

---

## Anti-Pattern 4: Skipping Field-Level Security Assignment After Writeback Field Creation

**What the LLM generates:** Deployment instructions that end at "Enable Predictions in the Deploy tab and run the bulk scoring job" without mentioning FLS assignment.

**Why it happens:** Einstein Discovery creates the writeback field and populates it silently. LLMs that describe deployment steps often omit FLS because it is a general Salesforce concept, not one that is tightly coupled to Einstein Discovery in most training material. The result looks complete but leaves the field invisible to all users.

**Correct pattern:**

```
After enabling predictions and creating writeback field:
1. Setup > Object Manager > [Target Object] > Fields & Relationships
2. Locate the Einstein writeback field
3. Click Field-Level Security
4. Grant Read access to all relevant profiles and permission sets
5. Add field to page layout(s) where prediction scores should appear
Without this step, the field exists and holds data but is invisible to all users.
```

**Detection hint:** Any Einstein Discovery deployment walkthrough that does not include a step for "Field-Level Security" or "FLS" for the writeback field is missing this required post-deployment action.

UNVERIFIED (2026-10-03): the platform behavior this anti-pattern relies on is documented only on help.salesforce.com, which did not fetch for the 2026-10-03 pass. Test it in a sandbox before stating it to users; see `gotchas.md` gotcha 8.

---

## Anti-Pattern 5: Recommending Einstein Discovery for Orgs Without a CRM Analytics License

**What the LLM generates:** "To use Einstein Discovery on your Opportunity records, navigate to Setup > Einstein and enable the feature." Or generic Einstein Discovery setup guidance without first confirming the CRM Analytics license.

**Why it happens:** LLMs often conflate Einstein features that are included in standard Sales Cloud licenses (Einstein Activity Capture, Einstein Lead Scoring via EPB) with Einstein Discovery, which requires a separate CRM Analytics (formerly Tableau CRM) license. The distinction is not obvious from documentation that refers broadly to "Einstein."

**Correct pattern:**

```
Before recommending Einstein Discovery:
1. Confirm CRM Analytics license in Setup > Company Information > Licenses
2. If CRM Analytics is not provisioned: recommend Einstein Prediction Builder instead
   - EPB handles binary predictions (yes/no) without requiring CRM Analytics
   - EPB has its own Setup-based wizard distinct from Analytics Studio
3. If CRM Analytics IS provisioned: proceed with Einstein Discovery in Analytics Studio
```

**Detection hint:** Any Einstein Discovery setup response that does not include a license verification step is applying this anti-pattern. Watch for phrases like "Einstein Discovery is available in all Enterprise and above orgs" — this is incorrect; the CRM Analytics license is required separately.

---

## Anti-Pattern 6: Directing Admins to Set Up Stories via the Setup Menu Instead of Analytics Studio

**What the LLM generates:** "Go to Setup > Einstein > Einstein Discovery to create a new prediction story."

**Why it happens:** Many Salesforce features are configured entirely within Setup. LLMs default to Setup-based navigation for Salesforce admin tasks, even for features whose authoring surface lives in a separate application.

**Correct pattern:**

```
Story creation: App Launcher > Analytics Studio > Create > Story
(NOT Setup > Einstein > Einstein Discovery)

Setup > Einstein menus contain:
- Einstein feature toggles and license information
- Prediction definition management (after deployment)
- NOT: the story authoring wizard
```

**Detection hint:** Any instructions directing an admin to "Setup > Einstein Discovery > Create Story" or similar Setup-only navigation for the story creation wizard indicate this anti-pattern.

UNVERIFIED (2026-10-03): the platform behavior this anti-pattern relies on is documented only on help.salesforce.com, which did not fetch for the 2026-10-03 pass. Test it in a sandbox before stating it to users; see `gotchas.md` gotcha 8.

---

## Anti-Pattern 7: Deploying a Goal File That Lost Its `pushbackField`

**What the LLM generates:** "Retrieve the DiscoveryGoal from your dev sandbox and deploy it to production," with no check of the writeback element.

**Why it happens:** Most metadata deploys are additive or overwrite harmlessly, so the model does not expect a deploy to delete data.

**Correct pattern:** "Removing a pushback field from the goal metadata causes the field to be deleted from the Salesforce object as well." Retrieve from the org with the real writeback configuration, and block any deploy whose goal diff removes `pushbackField`.

**Detection hint:** A promotion plan for `DiscoveryGoal` with no diff review of `pushbackField`.

---

## Anti-Pattern 8: Hand-Authoring Model Metadata

**What the LLM generates:** An edited `.model-meta.xml` that changes `classificationThreshold` or adds model fields, offered as a way to tune a model.

**Why it happens:** The model sees an XML file with readable fields and assumes it is editable configuration.

**Correct pattern:** "Write operations for DiscoveryAIModel objects are generally not supported," and the `UserUpload` source type is not supported in the Metadata API. Tune and retrain in Einstein Discovery, upload external models through Model Manager, and deploy models only as retrieved.

**Detection hint:** Any manual edit to a `DiscoveryAIModel` file.

---

## Anti-Pattern 9: Describing the Algorithm Choice as "Regression or GBM"

**What the LLM generates:** "Einstein Discovery automatically picks between linear regression and gradient boosting."

**Why it happens:** Older material described a two-algorithm choice.

**Correct pattern:** The metadata enumeration `DiscoveryAlgorithmType` lists `Best` (tournament), `Glm`, `Gbm`, `Xgboost`, and `Drf`, and `DiscoveryPredictionType` includes `MulticlassClassification`. State the algorithm recorded on the model, and treat how the wizard chooses it as something to check in the org.

**Detection hint:** A two-algorithm claim, or no mention of multiclass when the outcome has more than two values.

---

## Anti-Pattern 10: Ignoring Segment Order and the Sensitive-Field Flags

**What the LLM generates:** A prediction definition with a catch-all model listed first, or a deployment walkthrough that never mentions fields flagged sensitive or disparate impact.

**Why it happens:** Filter order and fairness flags are not visible in a story summary, and the model does not know the first matching filter wins.

**Correct pattern:** Order deployed models from most specific filter to the unfiltered catch-all, within ten active models. Review every model field with `isSensitive` or `isDisparateImpact` set, and record the decision before scores reach users.

**Detection hint:** An unfiltered model ahead of filtered ones, or no sensitive-field review step.

