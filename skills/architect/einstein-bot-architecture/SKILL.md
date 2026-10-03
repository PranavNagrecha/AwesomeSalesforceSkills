---
name: einstein-bot-architecture
description: "Use when designing conversational AI architecture on Salesforce: Einstein Bot dialog design, Agentforce Agent topic planning, intent models, NLU training strategy, bot-to-agent handoff, escalation paths, knowledge article surfacing, and bot analytics. Triggers: 'einstein bot architecture', 'agentforce dialog design', 'bot handoff to agent', 'intent model training'. NOT for multi-agent orchestration or Atlas Reasoning Engine behavior - use architect/conversational-ai-architecture. NOT for the fallback and escalation wording itself - use admin/agent-conversation-design."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Scalability
  - Reliability
triggers:
  - "how should I design my Einstein Bot dialog structure"
  - "what is the best way to hand off from bot to live agent"
  - "how many utterances do I need for intent training"
  - "how do I surface knowledge articles from an Einstein Bot"
  - "should I migrate from Einstein Bots to Agentforce Agents"
  - "design what the bot does when transfer to an agent fails after hours"
  - "roll back a bad Einstein Bot release without breaking the intent model"
tags:
  - einstein-bot-architecture
  - agentforce
  - conversational-ai
  - intent-model
  - bot-handoff
  - nlu-training
  - knowledge-articles
  - bot-analytics
inputs:
  - "service use cases the bot must handle (FAQs, case creation, order status, appointment scheduling)"
  - "current channel mix (web chat, messaging, WhatsApp, SMS)"
  - "whether the org uses Einstein Bots (legacy) or Agentforce Agents (current)"
  - "existing Omni-Channel configuration and agent skill groups"
  - "Knowledge article structure and article types in use"
outputs:
  - "conversational AI architecture document covering dialog structure, intent taxonomy, and handoff design"
  - "intent model training plan with utterance targets and coverage matrix"
  - "escalation path diagram showing bot-to-agent transfer triggers and context passing"
  - "bot analytics measurement plan with deflection, containment, and CSAT metrics"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Einstein Bot Architecture

Use this skill when planning or reviewing the architecture of a Salesforce conversational AI solution. It covers the structural decisions that determine whether a bot deflects cases effectively or frustrates customers: dialog design, intent modeling, handoff strategy, knowledge surfacing, and analytics. The skill applies equally to legacy Einstein Bots and the current Agentforce Agent framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which bot platform is the org on? Einstein Bots (legacy, Setup-driven) and Agentforce Agents (current, Agent Builder) have different dialog models and capabilities. Agentforce uses Topics and Actions rather than Dialogs and Dialog Steps.
- What channels does the bot serve? Web chat, Messaging for In-App and Web, WhatsApp, SMS, and Slack all have different UI constraints that affect dialog design (e.g., rich cards are not available on SMS).
- Is Omni-Channel already configured with routing rules and agent skills? The handoff design depends entirely on the existing queue and skill-based routing setup.
- Which messaging product carries the bot? Legacy chat (`LiveChatTranscript`) is "in maintenance-only mode" per the Object Reference; Messaging for In-App and Web uses `MessagingSession`.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is this an Einstein Bot or an Agentforce agent, and on legacy chat or Messaging for In-App and Web?" | One `BotDefinition` object, two design models; legacy chat gets no new features (Gotchas 6, 7) | The design model and the channel object the context will land on | No redesign forced six months after launch |
| "Which customer facts must reach the bot and the rep, from which fields, on which channels?" | Context arrives only through per-channel context variable mappings (Gotcha 1) | A mapping table: variable, channel type, sObject field | The rep never asks the customer to repeat themselves |
| "What happens when a transfer fails or no rep is online?" | A failed transfer without a designed path leaves silence (Gotcha 4) | A `TransferFailed` dialog and an `agentRequired` decision per channel | After-hours conversations end in a case or callback, not a dead session |
| "How will we roll back a bad release?" | Versions share one intent set; reactivating a version does not restore intents (Gotchas 2, 12) | Intent-set backups and a redeploy procedure | Rollback that actually rolls back |
| "How strict must intent matching be, and is `intentThreshold` enabled here?" | Strictness is a 1-to-5 setting that Support enables, not a 0.7 confidence value (Gotcha 3) | Overlap fixed in the taxonomy first; strictness set only if needed | Fewer silent misroutes without guessing at a non-existent field |
| "Which parts of the bot cannot be deployed by metadata?" | Messaging channel links must be set in the UI (Gotcha 5) | A manual post-deploy step in the runbook | Production bots that are actually connected to their channels |

What proper configuration adds over "just building dialogs": context that survives the handoff, a designed failure path, and releases that can be reversed.

---

## Core Concepts

Designing a conversational AI solution on Salesforce requires understanding four interrelated areas: the dialog model, the intent/NLU layer, the handoff mechanism, and the analytics feedback loop. Getting any one of these wrong creates a bot that either dead-ends customers or transfers them without context.

### Dialog Model: Dialogs vs. Topics

Einstein Bots (legacy) use a Dialog-and-Step model where each dialog is a linear sequence of message, question, action, and rule steps. Agentforce Agents replace this with a Topic-and-Action model where topics define the scope of what the agent can handle and actions are the operations it can execute (Flows, Apex, API calls). The architectural implication is significant: Dialogs are imperative (you script every branch), while Topics are declarative (you describe the goal and the agent reasons over available actions). Migrating from one to the other is not a refactor; it is a redesign.

### Intent Model and NLU Training

Both platforms use intent classification to route user input. Practitioners aim for 20 utterances per intent as a floor and 50+ for production accuracy (UNVERIFIED (2026-10-03): neither figure appears in a fetched Salesforce source). All versions of an Einstein Bot share one intent set (`Bot.botMlDomain`), so intent changes affect every version. Utterances must reflect real customer language, not agent jargon. The intent taxonomy should be flat rather than deeply nested: 15-30 well-scoped intents outperform 100 overlapping ones. Retrain the model whenever you add or modify intents, and review misroutes to detect drift. Matching strictness is controlled by `BotVersion.intentThreshold`, a 1-to-5 scale that Salesforce Customer Support must enable (Metadata API v67.0).

### Bot-to-Agent Handoff via Omni-Channel

When the bot cannot resolve a request, it transfers the conversation to a human agent through Omni-Channel. The handoff is not just a routing event; it must pass context. Bot variables (collected answers, intent detected, conversation history) reach the agent's console through fields on the `LiveChatTranscript` or `MessagingSession` record. Inbound facts flow into context variables only where a `ConversationContextVariableMapping` binds the variable to an sObject field for that channel type. The architecture must define which variables transfer, how they map to case or transcript fields, and what the agent sees on accept.

### Analytics and Continuous Improvement

Bot analytics should track deflection rate (conversations resolved without an agent), containment rate (conversations that stay in the bot flow), average handle time, and CSAT (UNVERIFIED (2026-10-03): the exact metrics on the standard Einstein Bot analytics dashboard were not confirmed). Define goals on the bot version (`conversationGoals`, BotStep type `GoalStep`) so resolution is recorded, not inferred. These metrics drive architectural decisions: low deflection on a specific intent means the dialog needs redesign or knowledge gaps exist; high transfer rates at a particular step reveal a dialog dead-end. Architects should define target metrics before launch and build the feedback loop into the operating model.

---

## Common Patterns

### Tiered Deflection Architecture

**When to use:** The org handles high case volume across a mix of simple (FAQ, password reset, order status) and complex (billing disputes, technical troubleshooting) requests.

**How it works:**

1. Layer 1 — Knowledge surfacing: Bot matches user intent to Knowledge articles using Einstein Article Recommendations. If the user confirms the article resolved their issue, the conversation ends (deflected).
2. Layer 2 — Guided self-service: Bot collects structured input (order number, account details) and executes a Flow or Apex action to perform the operation (check status, reset password, create case).
3. Layer 3 — Agent handoff: Bot transfers with full context (intent, collected variables, articles shown) to a skill-based Omni-Channel queue.

**Why not the alternative:** Sending every conversation directly to agents defeats the purpose of the bot. Sending every conversation through a scripted flow without a knowledge layer forces unnecessary dialog maintenance for content that changes frequently.

### Intent Taxonomy Design

**When to use:** Starting a new bot or restructuring an existing one that has low confidence scores or high misroutes.

**How it works:**

1. Extract the top 30 case reasons from historical Case data (Subject, Description, Reason picklist).
2. Cluster into 15-25 distinct intents. Each intent must have a clear boundary: if you cannot write 20 unique utterances that unambiguously belong to one intent and not another, the intents overlap and should be merged.
3. Create a coverage matrix mapping each intent to its resolution path (knowledge article, self-service action, or agent queue).
4. Reserve a fallback intent for unrecognized input. The fallback should offer 2-3 suggested intents before escalating.

**Why not the alternative:** Building intents from agent assumptions rather than real case data produces an intent model that does not match actual customer language. This is the single most common cause of poor bot performance.

### Contextual Handoff with Omni-Channel Skills-Based Routing

**When to use:** The org has multiple agent teams with different expertise and the bot must route to the right team with full conversation context.

**How it works:**

1. During the bot conversation, set a bot variable for the detected intent and another for the required skill.
2. On the Transfer to Agent step (Einstein Bots) or Transfer action (Agentforce), map bot variables to LiveChatTranscript or MessagingSession fields.
3. Configure the Omni-Channel routing to use Skills-Based Routing. The skill assignment comes from the bot variable, not a static queue.
4. Build the agent console layout to surface the transferred context prominently (bot transcript, collected data, articles already shown).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Greenfield bot project on Spring '25+ org | Use Agentforce Agents with Topics and Actions | Current platform direction; declarative topic model scales better than scripted dialogs |
| Existing Einstein Bot with good intent model and stable dialogs | Keep Einstein Bot; plan Agentforce migration roadmap | Migration is a redesign, not a refactor; do not disrupt a working bot without cause |
| Bot serves SMS and WhatsApp channels | Design text-only dialog flows; no rich cards or carousels | Rich components are not rendered on these channels; they silently degrade |
| More than 40 intents with overlapping utterances | Consolidate to 15-25 intents; merge overlapping ones | Large overlapping intent sets cause confidence score degradation and misroutes |
| Bot needs real-time data lookup (order status, account balance) | Use Apex actions (Einstein Bots) or Apex/Flow actions (Agentforce) | External callouts from bot dialogs require Apex or Flow; direct SOQL is not available in bot steps |
| Multi-language support required | Use Translation Workbench for bot dialog labels and utterances | Each language needs its own utterance set for intent training; machine translation of utterances degrades NLU accuracy |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a conversational AI architecture:

1. **Assess the platform baseline.** Run the inventory query in `references/examples.md` to see each `BotDefinition` with its `Type` and active `BotVersion`. Confirm licensing (UNVERIFIED (2026-10-03): "Einstein Bots require Service Cloud; Agentforce requires the Agentforce add-on" is from earlier material). The Bot metadata type is "available only if Chat and Einstein Bots are enabled". Verify that Omni-Channel is enabled and configured.
2. **Analyze historical case data.** Pull the top case reasons by volume from the Case object. Group them into candidate intents. Validate that each intent can be expressed with 20+ distinct utterances from real customer language.
3. **Design the intent taxonomy.** Create 15-25 well-bounded intents. Map each to a resolution path: knowledge article, self-service action, or agent handoff. Document the fallback intent behavior.
4. **Design the dialog/topic structure.** For Einstein Bots, map each intent to a dialog with clear steps. For Agentforce, define topics with descriptions and map available actions. In both cases, keep conversation depth under 5 turns for simple requests.
5. **Design the handoff architecture.** Define which bot variables transfer to the agent and map them per channel to `LiveChatTranscript` or `MessagingSession` fields. Assign a `TransferFailed` dialog. Configure Skills-Based Routing so the bot routes to the correct agent team. Build the agent console layout to surface transferred context. Add the manual channel-connection step to the deployment runbook.
6. **Define the analytics measurement plan.** Set target deflection rate (typically 30-50% for a mature bot), containment rate, and CSAT thresholds. Configure the Bot Analytics dashboard. Plan a monthly review cadence to retrain intents and adjust dialogs based on metrics.
7. **Plan the rollout.** Start with 3-5 high-volume, low-complexity intents. Measure for 2-4 weeks. Expand intent coverage incrementally. Do not launch with the full intent taxonomy; iterate based on real performance data.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform confirmed (Einstein Bots vs. Agentforce) and edition/licensing validated
- [ ] Intent taxonomy documented with 15-25 intents, each with 20+ utterances
- [ ] Resolution path mapped for every intent (knowledge, self-service, or handoff)
- [ ] Handoff design specifies which variables transfer and how they map to transcript/session fields
- [ ] Omni-Channel routing configured for skill-based assignment from bot context
- [ ] Fallback intent behavior defined (suggested intents before escalation)
- [ ] Analytics targets set for deflection rate, containment, and CSAT
- [ ] Multi-channel behavior validated (rich components degrade gracefully on text-only channels)
- [ ] Rollout plan starts with limited intent scope and expands iteratively

---

## Salesforce-Specific Gotchas

Full detail and sources in `references/gotchas.md`. The short list, with two corrections to earlier versions of this skill:

1. Intent strictness is `BotVersion.intentThreshold`, a 1-to-5 scale that Support enables. The earlier "set the threshold to 0.7" advice is withdrawn.
2. All versions of a bot share one intent set; reactivating an old version does not roll back intents. The earlier "each version keeps its own trained model" statement is withdrawn.
3. Context reaches the bot only through per-channel context variable mappings.
4. Assign a `TransferFailed` dialog; a failed transfer otherwise leaves the customer waiting.
5. Messaging channel links are set in the UI and do not deploy with Bot metadata.
6. Legacy chat is in maintenance-only mode; design new bots on Messaging for In-App and Web.

## Output Artifacts

| Artifact | Description |
|---|---|
| Conversational AI architecture document | Covers platform choice, dialog/topic structure, intent taxonomy, handoff design, and channel strategy |
| Intent coverage matrix | Maps each intent to utterance count, resolution path, and owning agent queue |
| Handoff specification | Documents bot variables, field mappings, routing rules, and agent console layout for transferred conversations |
| Analytics measurement plan | Defines deflection, containment, and CSAT targets with review cadence |
| Rollout plan | Phased intent expansion schedule with success criteria for each phase |

---

## Related Skills

- omni-channel-capacity-model — Use alongside this skill when designing the agent-side capacity and routing that receives bot handoffs
- multi-channel-service-architecture — Use when the bot architecture spans multiple messaging channels and the channel strategy affects dialog design
- service-cloud-architecture — Use for the broader Service Cloud design context that the bot architecture sits within

---

## Official Sources Used

- Metadata API Developer Guide and Object Reference, Version 67.0 (full list in `references/well-architected.md`)
- Einstein Bots Overview — https://help.salesforce.com/s/articleView?id=sf.bots_service_intro.htm
- Agentforce Overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_overview.htm
