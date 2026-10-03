# Examples — Einstein Copilot for Service

## Example 1: Case Classification Not Populating Fields After 72 Hours

**Context:** A Service Cloud org has just enabled Einstein Case Classification via Setup > Service > Einstein Classification Apps. The admin selected three fields: Case Type, Priority, and Case Reason. Permission sets are assigned, the Case Classification component is on the record page layout, and 72 hours have passed. Agents open new cases and none of the selected fields are being suggested or auto-populated. The admin opens Setup > Service > Einstein Classification Apps > Case Classification and sees the model status "Insufficient Data" for Case Reason and a low-confidence warning for Case Type.

**Problem:** The org's closed case history has inconsistent field population. A report on closed cases from the last 12 months reveals that only 35% of closed cases have a value in `Case Reason` — the rest are blank. Case Classification requires consistent field values in the training data. With 65% of training examples having a null value for Case Reason, the model cannot learn a meaningful pattern for that field and either defers training or produces suggestions that are no better than random.

**Solution:**

There is no code fix for this — the underlying requirement is data quality and volume.

1. Run a Case report to measure field completeness for each classified field:

```sql
SELECT COUNT(Id) closed_cases, COUNT(Reason) reason_filled, COUNT(Type) type_filled, COUNT(Priority) priority_filled
FROM Case
WHERE IsClosed = true
  AND ClosedDate = LAST_N_DAYS:365
```

Correction (2026-10-03): the earlier query filtered on `CaseReason`, which is not a Case field; the standard field is `Reason` (and Case Type is `Type`). `COUNT(field)` counts non-null values, so each ratio to `closed_cases` is that field's fill rate.

2. If a field is mostly empty, remove it from the classification model until data quality improves (the earlier "over 20% null" cutoff is UNVERIFIED, 2026-10-03). Navigate to Setup > Service > Einstein Classification Apps > Case Classification > Edit, and deselect the low-quality field.
3. For Case Reason: run a data quality campaign — contact the team that closes cases and establish a validation rule requiring `Case Reason` on case close. After 60–90 days of clean data accumulation, re-add the field to the model.
4. For Case Type (where data is better): confirm the model status moves to "Active" after the data quality correction. Active status means suggestions will appear for agents.

**Why it works:** UNVERIFIED (2026-10-03): the 12-month training window is not documented in a fetched source. Fields with high null rates look like a valid class label of "nothing" to the model, producing a model biased toward predicting blank values. Removing low-quality fields narrows the model scope to where it can be reliable.

---

## Example 2: Reply Recommendations Enabled But No Suggestions Appearing

**Context:** A Service Ops admin enables Einstein Reply Recommendations for a chat channel. The feature is on, agents have access, and the console layout is set. Two weeks later, agents see no suggested replies.

**Problem:** The model ran on closed chats and generated ReplyText records, but nobody reviewed or published them. Only replies published to quick text are recommended once the model is activated. Correction (2026-10-03): an earlier version blamed a "Training Data job"; the Object Reference describes the model, the generated ReplyText records, and the publish step.

**Solution:**

1. Open the Einstein Reply Recommendations Setup page and review the generated replies (ReplyText records).
2. Edit each reply to remove customer data ("they may contain customer data"), then publish to quick text.
3. Check for replies left in PUBLISH_FAILED and fix the validation or access error, or delete them.
4. Activate the model so published replies are recommended in the Lightning Service Console.
5. Monitor the backlog with SOQL:

```sql
SELECT Status, Source, Language, COUNT(Id) replies
FROM ReplyText
GROUP BY Status, Source, Language
```

**Why it works:** ReplyText Status shows NEW, PUBLISHED, or PUBLISH_FAILED, and Source shows EINSTEIN_GENERATED or USER_EDITED, so the query tells you how many replies are waiting for review and in which languages.

---

## Example 3: Service Replies Greyed Out in Setup Despite Service Cloud Einstein Being Provisioned

**Context:** A Salesforce admin at a service-heavy org has Service Cloud Einstein enabled and confirmed in Setup > Company Information > Feature Licenses. The admin navigates to Setup > Service > Service Replies with Einstein to enable AI-drafted responses for agents, but the toggle is greyed out and a tooltip reads "This feature requires additional licensing."

**Problem:** UNVERIFIED (2026-10-03): this example's licensing explanation comes from earlier versions and was not confirmed in a fetched source; the Generative AI guide only says these features are available "with an Einstein for Sales, Einstein for Platform, or Einstein for Service add-on." Service Replies with Einstein is a generative AI feature that requires the Einstein Generative AI entitlement (included in Einstein 1 Service edition or as a separate add-on). The org has Service Cloud Einstein, which covers Case Classification, Article Recommendations, and Reply Recommendations, but does NOT have the Einstein Generative AI entitlement. Service Cloud Einstein and Einstein Generative AI are separate SKUs. Without the generative AI license layer, all generative features (Service Replies, Work Summary) are locked.

**Solution:**

1. Run a license check: Setup > Company Information > Feature Licenses. Look for an entry labeled "Einstein Generative AI" or confirm the edition is "Einstein 1 Service." If only "Service Cloud Einstein" appears, the generative AI entitlement is absent.
2. If generative AI is required for the project scope, escalate to the account team to either upgrade to Einstein 1 Service edition or purchase the Einstein Generative AI add-on.
3. Do not include Service Replies or Work Summary in user training materials, change management documentation, or go-live scope until the license is confirmed.
4. In the interim, consider whether Einstein Reply Recommendations (covered by Service Cloud Einstein) can serve a similar — if narrower — agent efficiency goal. Reply Recommendations surface suggested replies based on past successful responses; they are not generative but are included in the existing license.

**Why it works:** Salesforce structures its AI capabilities across license tiers: Service Cloud Einstein covers ML-based features (classification, recommendations trained on your data). Einstein Generative AI covers LLM-based features (drafting, summarization). Understanding this boundary prevents scoping and delivery failures when a project assumes all Einstein features come bundled together.

---

## Example 4: Measuring Recommendation Acceptance by Field

**Context:** Three months after go-live, the service director asks whether Case Classification is worth keeping on every field.

**Solution:** Report acceptance from the Einstein insight objects. The Object Reference says to use "the root AIRecordInsight object and its child objects, AIInsightFeedback and AIInsightValue."

```sql
SELECT AiRecordInsight.PredictionField, AiInsightFeedbackType, AiFeedback, COUNT(Id) decisions
FROM AIInsightFeedback
WHERE CreatedDate = LAST_N_DAYS:90
GROUP BY AiRecordInsight.PredictionField, AiInsightFeedbackType, AiFeedback
```

**Why it works:** AiInsightFeedbackType separates decisions made after seeing the recommendation (Explicit) from field changes made elsewhere (Implicit), and AiFeedback records whether the recommended value was applied (Positive) or another value was (Negative). UNVERIFIED (2026-10-03): the relationship name `AiRecordInsight` is inferred from the `AiRecordInsightId` field; if the query fails, group by `AiRecordInsightId` and join in a second query.

---

## Anti-Pattern: Routing on Classified Values Before Validating Them

**What practitioners do:** An admin turns on Case Classification and, in the same release, sets `runAssignmentRules` in EinsteinAgentSettings so assignment rules re-run on the values Einstein writes. Billing cases start landing in the technical queue.

**What goes wrong:** Routing reads whatever values classification wrote, so systematic recommendation errors become systematic misroutes.

**Correct approach:** Run classification as recommendations first, measure acceptance per field with the Example 4 query, and only then turn on `runAssignmentRules` or `reRunAttributeBasedRules` for the fields agents accept. UNVERIFIED (2026-10-03): the earlier "2 to 4 weeks in suggestion mode" period is a practitioner rule of thumb, not a documented requirement.
