# Examples — Einstein Copilot for Service

## Example 1: Case Classification Not Populating Fields After 72 Hours

**Context:** A Service Cloud org has just enabled Einstein Case Classification via Setup > Service > Einstein Classification Apps. The admin selected three fields: Case Type, Priority, and Case Reason. Permission sets are assigned, the Case Classification component is on the record page layout, and 72 hours have passed. Agents open new cases and none of the selected fields are being suggested or auto-populated. The admin opens Setup > Service > Einstein Classification Apps > Case Classification and sees the model status "Insufficient Data" for Case Reason and a low-confidence warning for Case Type.

**Problem:** The org's closed case history has inconsistent field population. A report on closed cases from the last 12 months reveals that only 35% of closed cases have a value in `Case Reason` — the rest are blank. Case Classification requires consistent field values in the training data. With 65% of training examples having a null value for Case Reason, the model cannot learn a meaningful pattern for that field and either defers training or produces suggestions that are no better than random.

**Solution:**

There is no code fix for this — the underlying requirement is data quality and volume.

1. Run a Case report to measure field completeness for each classified field:

```text
// SOQL to check null rate on classified fields for the training window
SELECT COUNT()
FROM Case
WHERE IsClosed = true
  AND ClosedDate >= LAST_N_DAYS:365
  AND CaseReason = null
```

2. If null rate > 20% for a field, remove that field from the classification model until data quality improves. Navigate to Setup > Service > Einstein Classification Apps > Case Classification > Edit, and deselect the low-quality field.
3. For Case Reason: run a data quality campaign — contact the team that closes cases and establish a validation rule requiring `Case Reason` on case close. After 60–90 days of clean data accumulation, re-add the field to the model.
4. For Case Type (where data is better): confirm the model status moves to "Active" after the data quality correction. Active status means suggestions will appear for agents.

**Why it works:** The Case Classification model training window draws from closed cases with Closed Date in the past 12 months (the exact window can vary by release — verify in current Salesforce documentation). Fields with high null rates look like a valid class label of "nothing" to the model, producing a model biased toward predicting blank values. Removing low-quality fields narrows the model scope to where it can be reliable.

---

## Example 2: Reply Recommendations Enabled But No Suggestions Appearing in Messaging

**Context:** A Service Ops admin enables Einstein Reply Recommendations for a Messaging for In-App and Web channel. The feature is toggled on in Setup, the permission set is assigned to agents, and the Reply Recommendations component is confirmed to be in the service console layout. Two weeks after go-live, agents report seeing no suggested replies during messaging sessions — the suggestion area is empty.

**Problem:** The Training Data job — a mandatory prerequisite step for Reply Recommendations — was never run. The admin completed the Setup toggle and permission assignments but did not navigate to the Training Data setup tab and initiate the job. Without a completed Training Data run, the Reply Recommendations model has no corpus of successful past agent replies to learn from and cannot generate any suggestions.

**Solution:**

1. Navigate to Setup > Service > Einstein Reply Recommendations > Training Data.
2. Select the messaging channel(s) to use as the training source and click "Start Training Data Job."
3. Wait for the job to complete — training jobs for Reply Recommendations can take several hours to a day depending on transcript volume.
4. Once the Training Data job status shows "Complete," the Reply Recommendations model will activate automatically.
5. Agents should see suggested replies during their next messaging session. If suggestions still do not appear after 24 hours post-completion, verify the Reply Recommendations component is in the correct console layout and that agents are using a messaging channel included in the training scope.

```text
// No code change required — this is a declarative configuration fix.
// Setup path:
// Setup > Service > Einstein Reply Recommendations > Training Data
// > Select channel(s) > Start Training Data Job
// Wait for status: "Complete" before expecting suggestions in console
```

**Why it works:** Unlike Case Classification, which begins training automatically when enabled and field selection is saved, Reply Recommendations uses a separate Training Data pipeline that must be explicitly initiated. This is a deliberate design — the admin selects which historical channel data to use for training, giving control over the quality of the training corpus. The feature is architecturally split into two steps: data preparation (Training Data job) and model inference (suggestion generation). Completing only the first step (feature enable) skips the data preparation step entirely.

---

## Example 3: Service Replies Greyed Out in Setup Despite Service Cloud Einstein Being Provisioned

**Context:** A Salesforce admin at a service-heavy org has Service Cloud Einstein enabled and confirmed in Setup > Company Information > Feature Licenses. The admin navigates to Setup > Service > Service Replies with Einstein to enable AI-drafted responses for agents, but the toggle is greyed out and a tooltip reads "This feature requires additional licensing."

**Problem:** Service Replies with Einstein is a generative AI feature that requires the Einstein Generative AI entitlement (included in Einstein 1 Service edition or as a separate add-on). The org has Service Cloud Einstein — which covers Case Classification, Article Recommendations, and Reply Recommendations — but does NOT have the Einstein Generative AI entitlement. Service Cloud Einstein and Einstein Generative AI are separate SKUs. Without the generative AI license layer, all generative features (Service Replies, Work Summary) are locked.

**Solution:**

1. Run a license check: Setup > Company Information > Feature Licenses. Look for an entry labeled "Einstein Generative AI" or confirm the edition is "Einstein 1 Service." If only "Service Cloud Einstein" appears, the generative AI entitlement is absent.
2. If generative AI is required for the project scope, escalate to the account team to either upgrade to Einstein 1 Service edition or purchase the Einstein Generative AI add-on.
3. Do not include Service Replies or Work Summary in user training materials, change management documentation, or go-live scope until the license is confirmed.
4. In the interim, consider whether Einstein Reply Recommendations (covered by Service Cloud Einstein) can serve a similar — if narrower — agent efficiency goal. Reply Recommendations surface suggested replies based on past successful responses; they are not generative but are included in the existing license.

**Why it works:** Salesforce structures its AI capabilities across license tiers: Service Cloud Einstein covers ML-based features (classification, recommendations trained on your data). Einstein Generative AI covers LLM-based features (drafting, summarization). Understanding this boundary prevents scoping and delivery failures when a project assumes all Einstein features come bundled together.

---

## Anti-Pattern: Enabling Auto-Routing Before Case Classification Model Is Validated

**What practitioners do:** An admin enables Case Classification and Einstein Auto-Routing simultaneously, then configures Omni-Channel routing rules to use the Case Type and Case Reason field values that Einstein populates. Cases start routing almost immediately, but the wrong teams are receiving cases — billing cases are going to the technical support queue, and product questions are routing to the billing team.

**What goes wrong:** The Case Classification model is in its early training phase and producing low-confidence or incorrect field values. Auto-Routing blindly trusts whatever field values are on the case — including incorrect Einstein classifications — and routes accordingly. The routing errors are not random; they are systematically wrong in the pattern the model learned, which means a large percentage of cases misroute simultaneously.

**Correct approach:** Enable and validate Case Classification in suggestion mode for at least 2–4 weeks before enabling Auto-Routing. During this period, agents review and accept/reject suggestions — this builds agent trust, creates model feedback, and gives the admin time to review classification accuracy via reports. Only after the classification model shows consistent accuracy (validated by sampling recent case classifications against agent overrides) should Auto-Routing be enabled. Stage the rollout: start Auto-Routing on one Case Type or channel with high classification confidence before expanding broadly.
