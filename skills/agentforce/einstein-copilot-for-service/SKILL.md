---
name: einstein-copilot-for-service
description: "Service-specific AI features in Service Cloud: Case Classification setup and optimization, Article Recommendations configuration, Reply Recommendations, Work Summary (After-Visit Summary), Service Replies with Einstein, Auto-Routing, and Einstein Conversation Mining. NOT for the license, entitlement and data-threshold check before first enablement — use agentforce/agentforce-service-ai-setup. NOT for building an Agentforce agent — use agentforce/agentforce-agent-creation. NOT for its topic boundary design — use agentforce/agent-topic-design."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "How do I enable Einstein Case Classification and why are my case fields not being auto-populated?"
  - "Article Recommendations are not showing up when my agents work a case — what do I need to configure?"
  - "How do I set up Reply Recommendations so agents get suggested chat responses?"
  - "Work Summary is enabled but my agents cannot generate a case summary from the transcript — what is missing?"
  - "Einstein is routing cases incorrectly or not routing at all through Omni-Channel — how do I troubleshoot?"
  - "Einstein Conversation Mining is enabled but not showing any bot conversation insights — what are the requirements?"
  - "report how often agents accept Einstein Case Classification recommendations"
  - "rerun assignment rules after Case Classification fills in case fields"
tags:
  - einstein
  - service-cloud
  - case-classification
  - article-recommendations
  - reply-recommendations
  - work-summary
  - service-replies
  - einstein-for-service
  - omni-channel
  - einstein-conversation-mining
inputs:
  - Service Cloud org with Service Cloud Einstein license or Einstein 1 Service edition
  - List of Einstein for Service features to enable or troubleshoot
  - Case volume and history (for classification model training requirements)
  - Knowledge base status (for article recommendation and Service Replies grounding)
  - Omni-Channel setup status (for Auto-Routing requirements)
outputs:
  - Enabled and configured Einstein for Service AI features
  - Case Classification model trained and populating case fields automatically
  - Article Recommendations surfacing relevant Knowledge articles in the console
  - Reply Recommendations available to agents in messaging and chat
  - Work Summary generating post-conversation case summaries
  - Service Replies drafting email and chat responses grounded in Knowledge
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Einstein Copilot for Service

This skill activates when a practitioner needs to enable, configure, review, or troubleshoot the service-specific AI features in Service Cloud: Case Classification, Article Recommendations, Reply Recommendations, Work Summary, Service Replies with Einstein, Auto-Routing, and Einstein Conversation Mining. It does NOT cover core Agentforce agent creation, Agent Builder subagent design (subagents were called topics before April 2026), or Einstein Trust Layer configuration — use the dedicated skills for those areas.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License type:** Confirm whether the org has Service Cloud Einstein (add-on), Einstein 1 Service edition, or only core Service Cloud. The Generative AI guide lists Service Replies and Work Summaries as Einstein generative AI features, "Available in: Enterprise, Performance, and Unlimited Editions with an Einstein for Sales, Einstein for Platform, or Einstein for Service add-on." UNVERIFIED (2026-10-03): the earlier statement that the base Service Cloud Einstein add-on excludes them and that Einstein 1 Service or a separate entitlement is required; confirm the contract.
- **Case volume for classification:** Case Classification learns from closed cases. UNVERIFIED (2026-10-03): the earlier minimum of 400 closed cases per classified field was not found in a fetched source. Orgs with few closed cases or inconsistent field population will see poor recommendations.
- **Knowledge base readiness:** Article Recommendations and Service Replies with Einstein both require an active, published Salesforce Knowledge base. If Knowledge articles are not published, neither feature has content to surface or ground responses against.
- **Routing dependency:** EinsteinAgentSettings controls whether routing runs again after Case Classification changes fields: `runAssignmentRules` ("assignment rules are run after Einstein Case Classification automatically updates field values") and `reRunAttributeBasedRules` (skills-based routing rules), both false by default. UNVERIFIED (2026-10-03): the separate "Einstein Auto-Routing" feature described in earlier versions was not found in a fetched source.

---

## Core Concepts

### Case Classification

Einstein Case Classification uses a machine learning model trained on your org's historical closed cases to predict the correct field values for incoming cases — fields such as Case Type, Priority, Case Reason, and custom picklist fields on the Case object. When a new case arrives, the model proposes values and can either auto-populate the fields or surface suggestions to agents depending on the configuration mode chosen.

**Setup path:** Setup > Service > Einstein Classification Apps > Case Classification > Enable. Select the fields to include in the classification model. The model trains on closed cases. UNVERIFIED (2026-10-03): the earlier statements that fields are limited to picklists, that 400 closed cases per field are recommended, and that training takes 24 to 72 hours were not found in a fetched source. In metadata, the switch is `einsteinAgentRecommendations` on EinsteinAgentSettings (renamed from CaseClassificationSettings in API 52.0).

**Two classification modes (how recommendations reach agents):** For a picklist field, Einstein stores up to 10 value recommendations per case (AIInsightValue), and "just the top three predictions appear to agents in the Einstein Field Recommendations component." A recommendation already shown is marked Defunct so it isn't presented again.
1. **Auto-populate mode:** Einstein fills the selected fields automatically when a case is created or updated. The agent sees the pre-populated value and can override it. This mode increases efficiency but may cause incorrect values to persist if agents do not review them.
2. **Suggestion mode:** Einstein surfaces recommendations in the Case Classification component on the record page — agents see the suggested value and click to accept or reject it. This mode preserves agent judgment and creates feedback loops that improve model accuracy over time.

**Model retraining:** UNVERIFIED (2026-10-03): the earlier statements about a Salesforce-managed retrain schedule and a manual retrain button were not found in a fetched source. Measure quality from data instead: AIRecordInsight (TargetId is the case, PredictionField the field), AIInsightValue (the recommended values and Confidence), and AIInsightFeedback (AiFeedback Positive or Negative; AiInsightFeedbackType Explicit or Implicit).

### Article Recommendations

Einstein Article Recommendations surfaces relevant Knowledge articles to agents while they are actively working a case. The recommendations appear in the Knowledge component on the Case record page or in the service console. The model uses the case subject, description, and communication history as input signals to rank articles.

**Requirements:** Salesforce Knowledge must be enabled and articles must be published (not draft or archived). In metadata, ServiceAISetupDefinition (appSourceType ARTICLE_RECOMMENDATION, required supportedLanguages, setupStatus such as TRAINING, READY_TO_ACTIVATE, SERVING) and ServiceAISetupField (Case Subject and Description, article Title, Content, and Summary, ranked by fieldPosition) describe what Einstein reads. UNVERIFIED (2026-10-03): the earlier statement that the model learns from case-to-article attachments was not found in a fetched source.

**Agent workflow impact:** Recommendations improve when agents consistently use the "Attach to Case" action when a Knowledge article helps resolve a case. This creates the training feedback loop. Orgs that enable Article Recommendations without establishing this workflow habit see diminishing recommendation quality over time.

### Reply Recommendations

Einstein Reply Recommendations analyzes closed chats for frequently used text snippets. "When the model is ready, Einstein generates a list of these snippets as ReplyText records for you to review and publish, or convert, to quick text." Published replies are recommended to agents in the Lightning Service Console for chats or messaging sessions. UNVERIFIED (2026-10-03): the earlier statement that agents see up to three suggested replies.

**Requirements:** A predictive model must analyze closed chats, and an admin must review and publish the generated ReplyText records (Status NEW, PUBLISHED, or PUBLISH_FAILED) before anything is recommended. Because the replies come from closed chats, "they may contain customer data"; edit them before publishing. UNVERIFIED (2026-10-03): the earlier "few thousand messaging interactions" threshold.

**Channels supported:** The Object Reference says agents can insert recommended replies "into chats or messaging sessions." UNVERIFIED (2026-10-03): the earlier channel list (SMS, WhatsApp, Facebook Messenger) and the statement that email is excluded.

### Work Summary (After-Visit Summary)

Einstein Work Summary uses generative AI to auto-generate a summary of a service interaction — including what the issue was, what steps were taken, and how it was resolved — based on the conversation transcript. The summary is written into the case record automatically or made available for the agent to review before saving.

**License requirement:** Work Summary is a generative AI feature ("AI-generated case summaries... Based on a conversation"). UNVERIFIED (2026-10-03): the earlier statement that it is excluded from the base Service Cloud Einstein add-on and greyed out without a separate entitlement. In metadata, the Work Summaries invocable actions are `getCaseInfoToSummarize` and `getConvTrscpForRecord` (API 63.0).

**Data flow:** The transcript is sent through the Einstein Trust Layer before the LLM processes it. Correction (2026-10-03): earlier versions said no customer data leaves Salesforce's infrastructure. The prompt does reach the LLM provider through the LLM gateway; zero data retention means the provider does not keep it, and data masking (where the feature supports it) replaces sensitive values first.

### Service Replies with Einstein

Service Replies with Einstein uses generative AI to draft complete email and chat responses for agents, grounded in published Knowledge articles. The agent can accept, edit, or discard the draft. Grounding in Knowledge reduces hallucination risk — the model is constrained to synthesize answers from published content rather than generating free-form responses.

**License requirement:** Same note as Work Summary (UNVERIFIED beyond the add-on availability statement). In metadata, `enableGenReplyRecommendations` on AIReplyRecommendationsSettings turns on Einstein Service Replies, and `enableServiceEinsteinGPTGrounding` turns on Service AI Grounding. The Draft Service Replies standard prompt templates are listed as "Not used with agent," and the Einstein Data Library feature table lists Einstein Service Replies as not enabled with AI agents.

**Knowledge grounding:** The quality of Service Replies is directly tied to Knowledge article quality and coverage. If your Knowledge base does not cover the topics agents regularly handle, the generated drafts will be generic or pulled from thin content. Knowledge curation is a prerequisite for Service Replies quality, not an afterthought.

### Einstein Auto-Routing and Omni-Channel Integration

Classification output reaches routing through your own rules: EinsteinAgentSettings can re-run assignment rules (`runAssignmentRules`) or skills-based routing rules (`reRunAttributeBasedRules`) after Case Classification updates field values, and flows can call the `applyCaseClassificationRecommendations` invocable action (API 57.0), which "Takes a Case ID as input and outputs a case SObject with recommendations applied." UNVERIFIED (2026-10-03): "Einstein Auto-Routing" as a separate feature.

**Hard dependency:** Omni-Channel queues, routing configurations, and skills must be in place before classification-driven routing can work; the classification only sets field values that your assignment or skills-based rules read.

### Einstein Conversation Mining (ECM)

Einstein Conversation Mining analyzes bot conversation transcripts (from Salesforce bots or Agentforce Service Agents) to identify patterns: common topics customers raise, drop-off points in bot flows, cases where the bot escalated unnecessarily, and areas where a new bot topic could deflect more volume. ECM surfaces these insights in a dashboard in Setup.

**Use case:** ECM is an ongoing optimization tool, not a one-time setup step. UNVERIFIED (2026-10-03): the earlier "30+ days live" guidance was not found in a fetched source.

---

## Common Patterns

### Mode 1: Enable and Configure Einstein for Service from Scratch

**When to use:** Net-new org enabling Einstein for Service AI features for the first time, or a post-implementation where the license just provisioned.

**How it works:**

1. Verify license: Confirm Service Cloud Einstein or Einstein 1 Service is provisioned (Setup > Company Information > Feature Licenses). For Work Summary or Service Replies, also confirm Einstein Generative AI entitlement is present.
2. Enable Case Classification: Setup > Service > Einstein Classification Apps > Case Classification > Enable. Select the case fields to classify (start with 2–3 high-value picklist fields like Type, Priority, Reason). Do not select fields with poor historical data completeness.
3. Assign permission sets: Assign `Service Cloud Einstein` or `Einstein for Service` permission sets to agents and admins. Einstein for Service features are permission-set gated. UNVERIFIED (2026-10-03): these permission set names were not found in a fetched source; check the names in your org's Setup.
4. Add the Case Classification component to the Lightning Service Console or Case record page layout so agents see suggestions.
5. Enable Article Recommendations: Setup > Service > Einstein Article Recommendations > Enable. Confirm Knowledge is published and articles exist. Add the Einstein Article Recommendations component to the Case record page.
6. Wait for model training: Classification and article recommendation models train asynchronously. Monitor Setup > Service > Einstein Classification Apps for training status. Scores and suggestions appear only after the first training pass completes (24–72 hours). UNVERIFIED (2026-10-03): the 24 to 72 hour figure and the status names were not found in a fetched source; in metadata, ServiceAISetupDefinition setupStatus moves through values such as TRAINING, READY_TO_ACTIVATE, and SERVING.
7. Enable Reply Recommendations (if chat or messaging is in scope): Setup > Service > Einstein Reply Recommendations > Enable. Build the model on closed chats, review and edit the generated ReplyText records, and publish them to quick text before activating the model.
8. Enable Work Summary and Service Replies only if Einstein Generative AI license is confirmed.

**Why not enabling all at once without data review:** Enabling Case Classification for fields with sparse or inconsistent historical values produces a poor model. The classification suggestions will be wrong frequently, agents will stop trusting them, and the AI adoption effort becomes a recovery project rather than a success story.

### Mode 2: Improve Case Classification Quality

**When to use:** Case Classification is running but agents report that auto-populated values are frequently wrong; the feature is active but model accuracy is low.

**How it works:**

1. Review model stats: Setup > Service > Einstein Classification Apps > Case Classification > View Model. Check the model precision and recall per field. Low precision on a field means frequent incorrect classifications; remove that field from the model if it remains consistently low. UNVERIFIED (2026-10-03): the View Model page and its precision and recall figures were not found in a fetched source; the AIInsightFeedback query in `references/examples.md` measures acceptance from data.
2. Audit field data quality: Run a Case report filtering to closed cases in the last 12 months. Measure the null/blank rate for each classified field. If more than 20% of closed cases have a blank value for a field, the model lacks sufficient signal for that field.
3. Reduce the field scope: Start with the 1–2 fields where data completeness is highest. A classification model for fewer fields with clean data outperforms a broad model with noisy training data.
4. Switch classification mode: If auto-populate is causing agents to accept wrong values without reviewing, switch to suggestion mode. This adds one click but captures agent corrections as training feedback that improves the model over time.
5. Trigger retraining: After cleaning data or narrowing field scope, trigger a manual model retrain from Setup.

**Why not leaving the model running with poor accuracy:** A low-accuracy classification model actively harms operations. Cases routed to the wrong queue based on incorrect classifications create reassignment overhead that exceeds any efficiency gains from automation.

### Mode 3: Troubleshoot Article Recommendations Not Appearing

**When to use:** Article Recommendations is enabled but agents do not see any article suggestions on case records, or suggestions are irrelevant.

**How it works:**

1. Verify Knowledge is enabled and articles are published: Check Setup > Knowledge Settings. Confirm articles are in Published status — draft articles are not surfaced by recommendations.
2. Check that the Einstein Article Recommendations component is on the page layout: The recommendations only appear if the component is added to the Lightning record page. Check the Lightning App Builder for the Case record page.
3. Confirm model training status: Setup > Service > Einstein Article Recommendations. If the model shows "Insufficient Data," the org does not have enough case-to-article association history. The fix is to ensure agents consistently link articles to cases when resolving them. UNVERIFIED (2026-10-03): the "Insufficient Data" status text; ServiceAISetupDefinition setupStatus values are FIELDS_SELECTED, TRAINING, READY_TO_ACTIVATE, SERVING, RETIRED, ARCHIVED, and READY_FOR_REVIEW.
4. Check article language configuration: Article Recommendations respect the Knowledge article language. If cases are being submitted in a language for which no published articles exist in that language, no recommendations appear.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has few closed cases with consistent field values (400 per field was the earlier figure, UNVERIFIED) | Defer Case Classification; focus on data quality first | The model will train but predictions will be unreliable; poor suggestions erode agent trust before it is established |
| Agents need AI-drafted email/chat responses | Verify Einstein Generative AI license before enabling Service Replies | Service Replies is a generative AI feature requiring Einstein 1 Service or Einstein Generative AI add-on — not included in base Service Cloud Einstein |
| Article Recommendations surface irrelevant articles | Audit Knowledge article quality and agent article-linking habit before tuning the model | Recommendations are only as good as the case-to-article training signal; weak article adoption = weak recommendations |
| Reply Recommendations configured but showing no suggestions | Confirm the model has run on closed chats and that ReplyText records are PUBLISHED, not NEW or PUBLISH_FAILED | Only published replies are recommended |
| Classified cases routed to unexpected queues | Check recommended values (AIInsightValue) first, then whether EinsteinAgentSettings re-runs assignment or skills-based rules | Routing reads the field values classification wrote |
| Work Summary greyed out in Setup | Verify Einstein Generative AI / Einstein 1 Service license is present | Work Summary is generative AI — not included in Service Cloud Einstein add-on alone |
| Einstein Conversation Mining shows no insights | Confirm bot has been live for 30+ days with meaningful transcript volume | ECM requires historical transcript data to mine; no history = no insights |

---


## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "When classification fills in a case field, should the case be routed again?" | Assignment and skills-based rules don't re-run unless EinsteinAgentSettings says so; both default to false (Gotcha 1) | A yes or no for assignment rules and for skills-based rules | Classified cases land in the right queue without manual reassignment |
| "How will you know whether agents trust the recommendations?" | Only the top three of up to 10 recommendations show, and feedback is Explicit or Implicit (Gotcha 2) | An AIInsightFeedback report on acceptance by field | Low-value fields are removed on evidence |
| "Who reviews generated replies before agents see them?" | ReplyText must be published to quick text and may contain customer data (Gotcha 4) | A reviewer and a review cadence | No customer details leak into canned replies |
| "Which languages and article fields should Article Recommendations read?" | ServiceAISetupDefinition needs supportedLanguages; fields are ranked by fieldPosition (Gotcha 5) | Languages plus the ranked case and article fields | Recommendations match the languages cases arrive in |
| "Will an Agentforce agent handle the same conversations?" | The Draft Service Replies templates are not used with agents, and Service Replies is not enabled with AI agents (Gotcha 7) | Which surfaces use embedded features and which use the agent | Nobody expects Service Replies tuning to change agent answers |
| "Which settings must move between orgs?" | EinsteinAgentSettings was renamed from CaseClassificationSettings, and ExternalAIModel can't be retrieved with a wildcard (Gotchas 6, 8) | A manifest with named members | Retrieves and deploys bring the real settings |

## Recommended Workflow

1. Confirm licenses and scope with the Questions table: which embedded features, which channels, and whether an agent shares the conversations.
2. Enable features in Setup, then retrieve their settings into source control (`EinsteinAgent` and `AIReplyRecommendations` Settings, ServiceAISetupDefinition and ServiceAISetupField, ExternalAIModel by name) using `references/metadata-examples.md`.
3. Decide routing after classification (`runAssignmentRules`, `reRunAttributeBasedRules`) and add the Einstein Field Recommendations component where agents work.
4. For Reply Recommendations, review generated ReplyText records, remove customer data, and publish to quick text before activating the model.
5. Run `python3 scripts/check_einstein_copilot_for_service.py --manifest-dir <project>` to catch routing that won't re-run, missing languages or bad field mappings for Article Recommendations, and settings files under old names.
6. After go-live, report acceptance from AIRecordInsight, AIInsightValue, and AIInsightFeedback (`references/examples.md`), and drop fields agents keep rejecting.

---

## Review Checklist

Run through these before marking Einstein for Service AI work complete:

- [ ] Service Cloud Einstein or Einstein 1 Service license confirmed in Setup > Company Information > Feature Licenses
- [ ] For Work Summary / Service Replies: Einstein Generative AI entitlement separately confirmed
- [ ] Einstein for Service permission sets assigned to all target agents (names UNVERIFIED; check Setup)
- [ ] Case Classification model training status confirmed as Active (not "In Progress" or "Insufficient Data")
- [ ] Classified fields have >80% data completeness in closed case history — validated via Case report
- [ ] Case Classification component added to the Case record page or service console layout
- [ ] Knowledge is enabled, articles are published, and agents are trained to link articles to cases at resolution
- [ ] Einstein Article Recommendations component added to the Case record page
- [ ] If Reply Recommendations in scope: model built on closed chats, ReplyText reviewed for customer data, replies published
- [ ] If Work Summary in scope: Einstein Generative AI license confirmed and feature enabled; Trust Layer reviewed
- [ ] If classification drives routing: `runAssignmentRules` or `reRunAttributeBasedRules` set in EinsteinAgentSettings, and Omni-Channel queues and skills active
- [ ] Classification suggestion mode vs. auto-populate mode decision documented and consistent with agent workflow

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Case Classification model trains on closed cases — open cases with no history produce no suggestions** — The classification model uses historical closed case data as its training source. UNVERIFIED (2026-10-03): the specific thresholds behind "few closed cases" are not documented in a fetched source. If an org has recently migrated to Salesforce or is net-new, it may have many open cases but very few closed ones. The model may train but return low-confidence suggestions or none at all until enough cases have been closed. This is not a configuration error — it is a data maturity constraint.

2. **Work Summary and Service Replies require Einstein Generative AI license, not just Service Cloud Einstein** — Service Cloud Einstein (the add-on) covers Case Classification, Article Recommendations, and Reply Recommendations. It does NOT include any generative AI drafting capabilities. Work Summary and Service Replies require Einstein 1 Service edition or the separate Einstein Generative AI entitlement. Orgs that purchase only Service Cloud Einstein will find these settings greyed out or absent in Setup — not because of a configuration problem but because of a licensing gap.

3. **Reply Recommendations need a model and published replies before anything is suggested**: The model analyzes closed chats and generates ReplyText records; an admin must review and publish them to quick text, and only published replies are recommended once the model is activated. Correction (2026-10-03): earlier versions described a separate "Training Data job"; the Object Reference describes the model plus review-and-publish steps.

4. **Routing reads classification output, so routing errors are often classification errors**: When classified cases land in the wrong queue, check both the recommended values (AIInsightValue) and whether EinsteinAgentSettings re-runs assignment or skills-based rules. The first debugging instinct is usually to inspect the Omni-Channel routing rules. In most cases, the root cause is that the Case Classification model is producing incorrect field values, and those incorrect values drive the routing decision. Always verify classification field accuracy on recent cases before debugging routing configuration.

5. **Article Recommendations model requires agents to consistently link articles to cases to build training signal** — UNVERIFIED (2026-10-03): the training-signal mechanism below is not described in a fetched source. The Einstein Article Recommendations model learns which articles are relevant to which case types by analyzing historical case-to-article associations. If agents resolve cases without attaching or linking Knowledge articles, the training corpus never grows and recommendation quality stays flat or degrades. Establishing the article-linking habit in the agent workflow is a prerequisite for recommendation quality — it is not something the technology can compensate for.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Case Classification | Model trained, selected fields populating suggestions or auto-values on new cases |
| Case Classification component | Added to case record page layout; agents can see and accept/reject suggestions |
| Article Recommendations setup | Knowledge confirmed published, recommendation component on case page, agents trained on article-linking habit |
| Reply Recommendations activated | Replies reviewed and published to quick text, suggestions appearing in chat and messaging sessions |
| Work Summary enabled | Generative summary available post-conversation if Einstein Generative AI license confirmed |
| Service Replies enabled | AI-drafted email/chat responses grounded in Knowledge available to agents |
| Classification-driven routing | EinsteinAgentSettings re-runs assignment or skills-based rules after classification updates fields |
| Einstein for Service checklist | Completed review checklist confirming all prerequisites met before go-live |

---

## Related Skills

- `einstein-trust-layer` — Configure data masking, grounding enforcement, and audit trails for all Einstein generative features (Work Summary, Service Replies) before enabling them in production
- `agentforce-agent-creation` — Use when creating an autonomous Agentforce Service Agent (Agentforce Agent Builder) rather than enabling the embedded Service Cloud Einstein AI features covered by this skill
- `agent-topic-design` — Use when designing subagents and actions for an Agentforce autonomous agent, not when configuring the embedded Einstein for Service features
