---
name: einstein-copilot-for-service
description: "Service-specific AI features in Service Cloud: Case Classification setup and optimization, Article Recommendations configuration, Reply Recommendations, Work Summary (After-Visit Summary), Service Replies with Einstein, Auto-Routing, and Einstein Conversation Mining. NOT for core Agentforce setup, agent topic design, Agent Builder configuration, or Einstein Trust Layer setup."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Einstein Copilot for Service

This skill activates when a practitioner needs to enable, configure, review, or troubleshoot the service-specific AI features in Service Cloud: Case Classification, Article Recommendations, Reply Recommendations, Work Summary, Service Replies with Einstein, Auto-Routing, and Einstein Conversation Mining. It does NOT cover core Agentforce agent creation, Agent Builder topic design, or Einstein Trust Layer configuration — use the dedicated skills for those areas.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License type:** Confirm whether the org has Service Cloud Einstein (add-on), Einstein 1 Service edition, or only core Service Cloud. Case Classification, Article Recommendations, and Reply Recommendations require Service Cloud Einstein or Einstein 1 Service. Work Summary and Service Replies with Einstein (generative AI) require the Einstein Generative AI (Einstein GPT) license layer, which is NOT included in the base Service Cloud Einstein add-on — it requires Einstein 1 Service or the separate Einstein Generative AI entitlement.
- **Case volume for classification:** Case Classification requires a minimum of 400 closed cases with a consistent set of field values used for training. Orgs with fewer closed cases or highly inconsistent field population will see poor classification accuracy or a model that fails to train.
- **Knowledge base readiness:** Article Recommendations and Service Replies with Einstein both require an active, published Salesforce Knowledge base. If Knowledge articles are not published, neither feature has content to surface or ground responses against.
- **Omni-Channel dependency:** Einstein Auto-Routing requires Omni-Channel to be configured and active. Auto-Routing is not a standalone feature — it augments the Omni-Channel routing engine using Einstein classification signals.

---

## Core Concepts

### Case Classification

Einstein Case Classification uses a machine learning model trained on your org's historical closed cases to predict the correct field values for incoming cases — fields such as Case Type, Priority, Case Reason, and custom picklist fields on the Case object. When a new case arrives, the model proposes values and can either auto-populate the fields or surface suggestions to agents depending on the configuration mode chosen.

**Setup path:** Setup > Service > Einstein Classification Apps > Case Classification > Enable. Select the fields to include in the classification model (limited to picklist fields on the Case object). The model trains on closed cases; Salesforce recommends at least 400 closed cases per field being classified with consistent (non-null) values in that field for reliable training. Initial model training completes in 24–72 hours for orgs that meet the data threshold.

**Two classification modes:**
1. **Auto-populate mode:** Einstein fills the selected fields automatically when a case is created or updated. The agent sees the pre-populated value and can override it. This mode increases efficiency but may cause incorrect values to persist if agents do not review them.
2. **Suggestion mode:** Einstein surfaces recommendations in the Case Classification component on the record page — agents see the suggested value and click to accept or reject it. This mode preserves agent judgment and creates feedback loops that improve model accuracy over time.

**Model retraining:** The classification model retrains periodically (Salesforce-managed schedule). Admins can trigger a manual retrain from Setup after correcting data quality issues.

### Article Recommendations

Einstein Article Recommendations surfaces relevant Knowledge articles to agents while they are actively working a case. The recommendations appear in the Knowledge component on the Case record page or in the service console. The model uses the case subject, description, and communication history as input signals to rank articles.

**Requirements:** Salesforce Knowledge must be enabled and articles must be published (not draft or archived). The Einstein Article Recommendations feature uses a model trained on case-to-article associations — cases that were solved using specific articles signal that those articles are relevant for similar future cases. If agents never attach or link Knowledge articles to cases, the model has no training signal.

**Agent workflow impact:** Recommendations improve when agents consistently use the "Attach to Case" action when a Knowledge article helps resolve a case. This creates the training feedback loop. Orgs that enable Article Recommendations without establishing this workflow habit see diminishing recommendation quality over time.

### Reply Recommendations

Einstein Reply Recommendations analyzes successful past agent chat/messaging replies and surfaces similar suggested responses to agents when they are handling messaging sessions. Agents see up to three suggested replies they can send with one click or edit before sending.

**Requirements:** Reply Recommendations require a Training Data setup step — Salesforce needs a corpus of historical chat transcripts or messaging session data to analyze and extract high-quality response patterns. The Training Data job must be run before the model can be activated. Minimum data thresholds apply (Salesforce recommends at least a few thousand messaging interactions for useful recommendations).

**Channels supported:** Reply Recommendations work in Messaging (SMS, WhatsApp, Facebook Messenger via Messaging for In-App and Web), and Live Agent Chat. They are NOT available for email cases.

### Work Summary (After-Visit Summary)

Einstein Work Summary uses generative AI to auto-generate a summary of a service interaction — including what the issue was, what steps were taken, and how it was resolved — based on the conversation transcript. The summary is written into the case record automatically or made available for the agent to review before saving.

**License requirement:** Work Summary is a generative AI feature and requires Einstein Generative AI / Einstein 1 Service — it is NOT included in the base Service Cloud Einstein add-on. Attempting to enable Work Summary without the generative AI entitlement results in the option being greyed out or absent in Setup.

**Data flow:** The transcript is sent through the Einstein Trust Layer — Salesforce's AI security framework — before being processed by the underlying LLM. No customer data leaves Salesforce's infrastructure. The Trust Layer applies data masking and grounding enforcement before the LLM processes the input.

### Service Replies with Einstein

Service Replies with Einstein uses generative AI to draft complete email and chat responses for agents, grounded in published Knowledge articles. The agent can accept, edit, or discard the draft. Grounding in Knowledge reduces hallucination risk — the model is constrained to synthesize answers from published content rather than generating free-form responses.

**License requirement:** Same as Work Summary — requires Einstein Generative AI / Einstein 1 Service, not just Service Cloud Einstein.

**Knowledge grounding:** The quality of Service Replies is directly tied to Knowledge article quality and coverage. If your Knowledge base does not cover the topics agents regularly handle, the generated drafts will be generic or pulled from thin content. Knowledge curation is a prerequisite for Service Replies quality, not an afterthought.

### Einstein Auto-Routing and Omni-Channel Integration

Einstein Auto-Routing uses the Case Classification model's output to route cases to the correct queue or agent group via Omni-Channel. Instead of manually configuring static routing rules, Einstein classification signals (Case Type, Case Reason, skill tags) drive the routing decision dynamically.

**Hard dependency:** Omni-Channel must be fully configured — including queues, routing configurations, and presence configurations — before Einstein Auto-Routing can be layered on. Einstein Auto-Routing does not replace Omni-Channel; it feeds classification signals into the Omni-Channel routing engine.

### Einstein Conversation Mining (ECM)

Einstein Conversation Mining analyzes bot conversation transcripts (from Salesforce bots or Agentforce Service Agents) to identify patterns: common topics customers raise, drop-off points in bot flows, cases where the bot escalated unnecessarily, and areas where a new bot topic could deflect more volume. ECM surfaces these insights in a dashboard in Setup.

**Use case:** ECM is an ongoing optimization tool, not a one-time setup step. It is most valuable after a bot has been live for 30+ days with meaningful transcript volume.

---

## Common Patterns

### Mode 1: Enable and Configure Einstein for Service from Scratch

**When to use:** Net-new org enabling Einstein for Service AI features for the first time, or a post-implementation where the license just provisioned.

**How it works:**

1. Verify license: Confirm Service Cloud Einstein or Einstein 1 Service is provisioned (Setup > Company Information > Feature Licenses). For Work Summary or Service Replies, also confirm Einstein Generative AI entitlement is present.
2. Enable Case Classification: Setup > Service > Einstein Classification Apps > Case Classification > Enable. Select the case fields to classify (start with 2–3 high-value picklist fields like Type, Priority, Reason). Do not select fields with poor historical data completeness.
3. Assign permission sets: Assign `Service Cloud Einstein` or `Einstein for Service` permission sets to agents and admins. Einstein for Service features are permission-set gated.
4. Add the Case Classification component to the Lightning Service Console or Case record page layout so agents see suggestions.
5. Enable Article Recommendations: Setup > Service > Einstein Article Recommendations > Enable. Confirm Knowledge is published and articles exist. Add the Einstein Article Recommendations component to the Case record page.
6. Wait for model training: Classification and article recommendation models train asynchronously. Monitor Setup > Service > Einstein Classification Apps for training status. Scores and suggestions appear only after the first training pass completes (24–72 hours).
7. Enable Reply Recommendations (if messaging is in scope): Setup > Service > Einstein Reply Recommendations > Enable. Run the Training Data job first. Assign to messaging channels.
8. Enable Work Summary and Service Replies only if Einstein Generative AI license is confirmed.

**Why not enabling all at once without data review:** Enabling Case Classification for fields with sparse or inconsistent historical values produces a poor model. The classification suggestions will be wrong frequently, agents will stop trusting them, and the AI adoption effort becomes a recovery project rather than a success story.

### Mode 2: Improve Case Classification Quality

**When to use:** Case Classification is running but agents report that auto-populated values are frequently wrong; the feature is active but model accuracy is low.

**How it works:**

1. Review model stats: Setup > Service > Einstein Classification Apps > Case Classification > View Model. Check the model precision and recall per field. Low precision on a field means frequent incorrect classifications; remove that field from the model if it remains consistently low.
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
3. Confirm model training status: Setup > Service > Einstein Article Recommendations. If the model shows "Insufficient Data," the org does not have enough case-to-article association history. The fix is to ensure agents consistently link articles to cases when resolving them.
4. Check article language configuration: Article Recommendations respect the Knowledge article language. If cases are being submitted in a language for which no published articles exist in that language, no recommendations appear.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has fewer than 400 closed cases with consistent field values | Defer Case Classification; focus on data quality first | The model will train but predictions will be unreliable; poor suggestions erode agent trust before it is established |
| Agents need AI-drafted email/chat responses | Verify Einstein Generative AI license before enabling Service Replies | Service Replies is a generative AI feature requiring Einstein 1 Service or Einstein Generative AI add-on — not included in base Service Cloud Einstein |
| Article Recommendations surface irrelevant articles | Audit Knowledge article quality and agent article-linking habit before tuning the model | Recommendations are only as good as the case-to-article training signal; weak article adoption = weak recommendations |
| Reply Recommendations configured but showing no suggestions | Confirm Training Data job has been run and messaging volume thresholds are met | Reply Recommendations require a completed Training Data step; without it the model has no corpus |
| Auto-Routing producing unexpected queue assignments | Confirm Case Classification fields driving routing are accurate first, then review Omni-Channel routing configuration | Auto-Routing inherits classification errors; fix classification quality before debugging routing rules |
| Work Summary greyed out in Setup | Verify Einstein Generative AI / Einstein 1 Service license is present | Work Summary is generative AI — not included in Service Cloud Einstein add-on alone |
| Einstein Conversation Mining shows no insights | Confirm bot has been live for 30+ days with meaningful transcript volume | ECM requires historical transcript data to mine; no history = no insights |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking Einstein for Service AI work complete:

- [ ] Service Cloud Einstein or Einstein 1 Service license confirmed in Setup > Company Information > Feature Licenses
- [ ] For Work Summary / Service Replies: Einstein Generative AI entitlement separately confirmed
- [ ] `Service Cloud Einstein` or `Einstein for Service` permission sets assigned to all target agents
- [ ] Case Classification model training status confirmed as Active (not "In Progress" or "Insufficient Data")
- [ ] Classified fields have >80% data completeness in closed case history — validated via Case report
- [ ] Case Classification component added to the Case record page or service console layout
- [ ] Knowledge is enabled, articles are published, and agents are trained to link articles to cases at resolution
- [ ] Einstein Article Recommendations component added to the Case record page
- [ ] If Reply Recommendations in scope: Training Data job completed and messaging channel assignment confirmed
- [ ] If Work Summary in scope: Einstein Generative AI license confirmed and feature enabled; Trust Layer reviewed
- [ ] If Auto-Routing in scope: Omni-Channel queues, routing configurations, and presence configurations all active
- [ ] Classification suggestion mode vs. auto-populate mode decision documented and consistent with agent workflow

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Case Classification model trains on closed cases — open cases with no history produce no suggestions** — The classification model uses historical closed case data as its training source. If an org has recently migrated to Salesforce or is net-new, it may have many open cases but very few closed ones. The model may train but return low-confidence suggestions or none at all until enough cases have been closed. This is not a configuration error — it is a data maturity constraint.

2. **Work Summary and Service Replies require Einstein Generative AI license, not just Service Cloud Einstein** — Service Cloud Einstein (the add-on) covers Case Classification, Article Recommendations, and Reply Recommendations. It does NOT include any generative AI drafting capabilities. Work Summary and Service Replies require Einstein 1 Service edition or the separate Einstein Generative AI entitlement. Orgs that purchase only Service Cloud Einstein will find these settings greyed out or absent in Setup — not because of a configuration problem but because of a licensing gap.

3. **Reply Recommendations require the Training Data job to run before the model activates — enabling the feature is not enough** — Unlike Case Classification, which trains automatically after enablement, Reply Recommendations have a mandatory prerequisite Training Data job that must be explicitly kicked off by an admin in Setup before the model can be built. Simply enabling the feature and assigning it to a channel produces no suggestions. The Training Data job must complete successfully first.

4. **Auto-Routing uses Case Classification signals — routing errors are usually classification errors, not routing rule errors** — When Einstein Auto-Routing sends cases to the wrong queue, the first debugging instinct is to inspect the Omni-Channel routing rules. In most cases, the root cause is that the Case Classification model is producing incorrect field values, and those incorrect values drive the routing decision. Always verify classification field accuracy on recent cases before debugging routing configuration.

5. **Article Recommendations model requires agents to consistently link articles to cases to build training signal** — The Einstein Article Recommendations model learns which articles are relevant to which case types by analyzing historical case-to-article associations. If agents resolve cases without attaching or linking Knowledge articles, the training corpus never grows and recommendation quality stays flat or degrades. Establishing the article-linking habit in the agent workflow is a prerequisite for recommendation quality — it is not something the technology can compensate for.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Case Classification | Model trained, selected fields populating suggestions or auto-values on new cases |
| Case Classification component | Added to case record page layout; agents can see and accept/reject suggestions |
| Article Recommendations setup | Knowledge confirmed published, recommendation component on case page, agents trained on article-linking habit |
| Reply Recommendations activated | Training Data job complete, suggestions appearing in messaging/chat sessions for agents |
| Work Summary enabled | Generative summary available post-conversation if Einstein Generative AI license confirmed |
| Service Replies enabled | AI-drafted email/chat responses grounded in Knowledge available to agents |
| Auto-Routing configuration | Omni-Channel routing updated to use Einstein classification signals for queue assignment |
| Einstein for Service checklist | Completed review checklist confirming all prerequisites met before go-live |

---

## Related Skills

- `einstein-trust-layer` — Configure data masking, grounding enforcement, and audit trails for all Einstein generative features (Work Summary, Service Replies) before enabling them in production
- `agentforce-agent-creation` — Use when creating an autonomous Agentforce Service Agent (Agentforce Agent Builder) rather than enabling the embedded Service Cloud Einstein AI features covered by this skill
- `agent-topic-design` — Use when designing topics and actions for an Agentforce autonomous agent, not when configuring the embedded Einstein for Service features
