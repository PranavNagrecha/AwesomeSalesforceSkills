# LLM Anti-Patterns — Einstein Copilot For Service

Common mistakes AI coding assistants make when generating or advising on Einstein AI features for Service Cloud.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Enabling Case Classification Without Sufficient Training Data

**What the LLM generates:** "Enable Einstein Case Classification and cases will be automatically classified" without noting the minimum data requirements — at least 400 closed cases with consistent values in the target classification fields (Type, Reason, Priority) over the past 6 months.

**Why it happens:** LLMs describe enablement steps without data prerequisites. Einstein Case Classification trains a model on historical case patterns. Without sufficient volume and consistency, the model either fails to train or misclassifies cases.

**Correct pattern:**

UNVERIFIED (2026-10-03): the numeric prerequisites in this block (400 cases, 6 months,
25 examples per value, 48 hours, max 3 fields) come from earlier versions and were not
found in a fetched source. Treat them as review thresholds, and measure acceptance
from AIInsightFeedback after go-live (`references/examples.md`, Example 4).

```text
Einstein Case Classification prerequisites:

Data requirements:
- Minimum 400 closed cases with populated target fields
- Target fields: Type, Reason, Priority, or custom picklist fields
- Values must be consistent (not 50 variations of the same category)
- Cases should span the past 6 months for recency relevance
- Each classification value needs at least 25 examples

Enablement:
1. Audit target field data quality BEFORE enabling
2. Setup > Einstein Case Classification > Enable
3. Select fields to classify (max 3 fields recommended)
4. Wait for model training (up to 48 hours)
5. Review acceptance per field (AIRecordInsight, AIInsightValue, AIInsightFeedback)
6. Start with recommendations (not auto-apply), and leave runAssignmentRules /
   reRunAttributeBasedRules off until acceptance is proven

Common failures:
- Model does not build: fewer than 400 cases or too many
  null values in target fields
- Low accuracy: field values are inconsistent (e.g., "Billing",
  "billing", "Billing Issue", "Bill" all mean the same thing)
- Classification disappears for new case types not in training data
```

**Detection hint:** Flag Case Classification enablement that does not check data volume or quality. Check for target fields with more than 20 picklist values (may dilute training). Flag auto-apply mode without a recommendation-first validation phase.

---

## Anti-Pattern 2: Confusing Article Recommendations with Knowledge Search

**What the LLM generates:** "Enable Einstein Article Recommendations and agents will see recommended articles when working cases" without distinguishing between Einstein Article Recommendations (ML-based, automatic) and standard Knowledge Search (manual, keyword-based). The two have different setup paths and different behavior.

**Why it happens:** Both features surface Knowledge articles to service agents. LLMs conflate them. Einstein Article Recommendations uses a model trained on case-to-article attachment history, while Knowledge Search is a keyword lookup.

**Correct pattern:**

```text
Article Recommendations vs Knowledge Search:

Einstein Article Recommendations:
- Automatically suggests articles based on case field values
- Requires: Knowledge enabled, articles published, history of
  agents attaching articles to cases (minimum 1000 case-article pairs)
- Appears in the Knowledge component on the case page
- Improves over time as agents accept or reject suggestions
- Setup: Einstein for Service > Article Recommendations

Standard Knowledge Search:
- Agent manually searches by keyword
- No ML model required
- Always available once Knowledge is enabled
- Setup: Knowledge Settings + Knowledge component on page layout

Common issue: "Article Recommendations enabled but no suggestions appear"
→ Insufficient case-article attachment history for the model to train
→ Articles are in Draft status (must be Published)
→ Knowledge component not added to the case Lightning page

They are complementary, not interchangeable.
```

**Detection hint:** Flag Article Recommendation guides that skip the language list and field ranking (ServiceAISetupDefinition supportedLanguages, ServiceAISetupField fieldPosition). UNVERIFIED (2026-10-03): the earlier case-article attachment requirement and the 1,000-pair threshold.

---

## Anti-Pattern 3: Expecting Reply Recommendations to Work Without Messaging History

**What the LLM generates:** "Enable Reply Recommendations and agents will get suggested chat responses" without noting that the feature requires historical chat transcript data with resolved conversations and must be configured per messaging channel.

**Why it happens:** Reply Recommendations is positioned as an easy-to-enable feature. LLMs skip the data and channel requirements. The model needs patterns from successful past conversations to generate relevant suggestions.

**Correct pattern:**

Correction (2026-10-03): the Object Reference describes the mechanism as a model that
"analyzes closed chats for frequently used text snippets," then ReplyText records that an
admin reviews and publishes to quick text; only published replies are recommended. The
volume, per-channel, feedback-loop, and "suggestions appear as the customer types" details
below are UNVERIFIED.

```text
Reply Recommendations prerequisites:

Data requirements:
- Historical chat transcripts from Messaging or Chat
- Minimum: several hundred resolved conversations
- Transcripts must include agent replies (not just bot or auto-responses)
- Conversations should cover the use cases you want suggestions for

Channel configuration:
- Enabled per messaging channel (not org-wide toggle)
- Setup: Einstein for Service > Reply Recommendations
- Select the channel (Messaging for Web, Chat, etc.)
- Configure which agents see recommendations

Behavior:
- Suggestions appear as the customer types
- Agent clicks to accept, edits, then sends
- Feedback loop: accepted suggestions improve future recommendations
- Rejected or ignored suggestions signal the model to adjust

Common failures:
- "No suggestions appear" — insufficient transcript data
- Suggestions are irrelevant — historical transcripts are from a
  different use case than current conversations
- Suggestions stop appearing — the channel was reconfigured or
  the model needs retraining

Reply Recommendations require ongoing transcript volume to stay relevant.
```

**Detection hint:** Flag Reply Recommendation enablement that does not mention transcript history requirements. Check for enablement on channels with no historical messaging data.

---

## Anti-Pattern 4: Not Distinguishing Between Work Summaries and Case Summaries

**What the LLM generates:** "Enable Einstein Work Summary and agents can generate case summaries" conflating two different features: Work Summary (generates a summary from a messaging or voice conversation transcript) and Case Summary (generates a summary from the full case record including activities, comments, and emails).

**Why it happens:** Both features produce text summaries in Service Cloud. LLMs treat "summary" as a single capability. The input data, configuration, and output location differ significantly.

**Correct pattern:**

```text
Work Summary vs Case Summary:

Einstein Work Summary:
- Input: messaging conversation transcript or voice call transcript
- Output: after-conversation summary for wrap-up
- Triggered: at end of messaging session or call
- Use case: agent documentation of what was discussed
- Requires: Messaging or Service Cloud Voice transcript data
- Setup: Einstein for Service > Work Summaries

Einstein Case Summary (Generative):
- Input: full case record — activities, emails, case comments,
  related records
- Output: holistic summary of the case lifecycle
- Triggered: on-demand by the agent from the case page
- Use case: agent picking up a case needs context quickly
- Requires: Einstein Generative AI enabled, Trust Layer configured
- Setup: Einstein for Service > Case Summaries

Configuration matters:
- Work Summary needs transcript-based channels active
- Case Summary needs generative AI (different license tier)
- Both need the Einstein for Service permission set
- Both use the Trust Layer for data masking and grounding

Advise the correct feature based on the actual use case.
```

**Detection hint:** Flag advice that uses "Work Summary" and "Case Summary" interchangeably. Check for Work Summary enablement on orgs without messaging or voice channels. Flag Case Summary enablement without generative AI licensing.

---

## Anti-Pattern 5: Enabling Einstein for Service Features Without Omni-Channel Routing Configuration

**What the LLM generates:** "Enable Einstein for Service and cases will be intelligently routed" without noting that Einstein-powered routing requires Omni-Channel to be configured with Skills-Based Routing or Queue-Based Routing, and that Einstein only enhances the routing — it does not replace the Omni-Channel foundation.

**Why it happens:** LLMs present Einstein routing as a standalone feature. In reality, Einstein classification feeds INTO Omni-Channel routing rules. Without Omni-Channel properly configured, classification values are populated but cases are not automatically routed.

**Correct pattern:**

```text
Einstein + Omni-Channel routing stack:

Layer 1: Omni-Channel Foundation (required)
- Omni-Channel enabled in Setup
- Service Channels defined (Case, Messaging, etc.)
- Routing Configuration created (queue-based or skills-based)
- Agents assigned to queues with Presence Statuses

Layer 2: Einstein Case Classification (optional enhancement)
- Classifies incoming cases (Type, Reason, Priority)
- Populates field values on the case record

Layer 3: Routing Rules (connects classification to routing)
- Assignment Rules or Omni-Channel Flow uses classification values
  to route to the correct queue or skilled agent
- EinsteinAgentSettings runAssignmentRules / reRunAttributeBasedRules
  (default false) make those rules run again after classification
  updates field values
- Example: if Einstein sets Priority = High AND Type = Billing,
  route to the Senior Billing Agents queue

Common mistake:
- Einstein classifies the case correctly
- But no routing rule uses the classification fields
- Case sits unrouted in the default queue

Verification:
1. Einstein populates classification fields (check case record)
2. Routing rules reference those fields (check assignment rules)
3. Omni-Channel routes to the correct queue (check agent workload)
```

**Detection hint:** Flag Einstein routing advice that does not mention Omni-Channel as a prerequisite. Check for classification fields not referenced in any routing or assignment rule. Flag orgs with Einstein Case Classification enabled but no Omni-Channel configuration.

---

## Anti-Pattern 6: Expecting Classification to Re-Route Cases by Itself

**What the LLM generates:** "Once Case Classification sets the Type, Omni-Channel will route the case to the right queue."

**Why it happens:** The model assumes field changes always trigger routing.

**Correct pattern:** EinsteinAgentSettings `runAssignmentRules` and `reRunAttributeBasedRules` decide whether assignment rules or skills-based routing rules run after classification updates field values, and both default to false. Set the one that matches your routing, or call `applyCaseClassificationRecommendations` in a flow and route from there.

**Detection hint:** A classification design that mentions routing but neither setting.

---

## Anti-Pattern 7: Publishing Generated Replies Without Review

**What the LLM generates:** "Select all generated replies and publish them to quick text."

**Why it happens:** Bulk publish looks efficient.

**Correct pattern:** ReplyText records are built from closed chats, "they may contain customer data," and each should be edited before publishing. Check for PUBLISH_FAILED records after publishing.

**Detection hint:** A Reply Recommendations rollout plan with no review step.

