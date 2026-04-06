---
name: einstein-bot-architecture
description: "Use when designing conversational AI architecture on Salesforce: Einstein Bot dialog design, Agentforce Agent topic planning, intent models, NLU training strategy, bot-to-agent handoff, escalation paths, knowledge article surfacing, and bot analytics. Triggers: 'einstein bot architecture', 'agentforce dialog design', 'bot handoff to agent', 'intent model training'. NOT for bot implementation code, Apex action authoring, Flow screen design, or Omni-Channel routing rule configuration."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Einstein Bot Architecture

Use this skill when planning or reviewing the architecture of a Salesforce conversational AI solution. It covers the structural decisions that determine whether a bot deflects cases effectively or frustrates customers: dialog design, intent modeling, handoff strategy, knowledge surfacing, and analytics. The skill applies equally to legacy Einstein Bots and the current Agentforce Agent framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which bot platform is the org on? Einstein Bots (legacy, Setup-driven) and Agentforce Agents (current, Agent Builder) have different dialog models and capabilities. Agentforce uses Topics and Actions rather than Dialogs and Dialog Steps.
- What channels does the bot serve? Web chat, Messaging for In-App and Web, WhatsApp, SMS, and Slack all have different UI constraints that affect dialog design (e.g., rich cards are not available on SMS).
- Is Omni-Channel already configured with routing rules and agent skills? The handoff design depends entirely on the existing queue and skill-based routing setup.

---

## Core Concepts

Designing a conversational AI solution on Salesforce requires understanding four interrelated areas: the dialog model, the intent/NLU layer, the handoff mechanism, and the analytics feedback loop. Getting any one of these wrong creates a bot that either dead-ends customers or transfers them without context.

### Dialog Model: Dialogs vs. Topics

Einstein Bots (legacy) use a Dialog-and-Step model where each dialog is a linear sequence of message, question, action, and rule steps. Agentforce Agents replace this with a Topic-and-Action model where topics define the scope of what the agent can handle and actions are the operations it can execute (Flows, Apex, API calls). The architectural implication is significant: Dialogs are imperative (you script every branch), while Topics are declarative (you describe the goal and the agent reasons over available actions). Migrating from one to the other is not a refactor; it is a redesign.

### Intent Model and NLU Training

Both platforms use intent classification to route user input. Each intent requires a minimum of 20 utterances for reliable training, but 50+ utterances per intent is the practical target for production accuracy. Utterances must reflect real customer language, not agent jargon. The intent taxonomy should be flat rather than deeply nested: 15-30 well-scoped intents outperform 100 overlapping ones. Salesforce recommends retraining the model whenever you add or modify intents, and monitoring confidence scores to detect model drift.

### Bot-to-Agent Handoff via Omni-Channel

When the bot cannot resolve a request, it transfers the conversation to a human agent through Omni-Channel. The handoff is not just a routing event; it must pass context. Bot variables (collected answers, intent detected, conversation history) transfer to the agent's console as pre-chat data or custom fields on the LiveChatTranscript or MessagingSession record. Pre-chat form data flows into bot variables at session start. The architecture must define which variables transfer, how they map to case or transcript fields, and what the agent sees on accept.

### Analytics and Continuous Improvement

The Einstein Bot Analytics dashboard tracks deflection rate (conversations resolved without agent), containment rate (conversations that stay in the bot flow), average handle time, and CSAT scores. These metrics drive architectural decisions: low deflection on a specific intent means the dialog needs redesign or knowledge gaps exist; high transfer rates at a particular step reveal a dialog dead-end. Architects should define target metrics before launch and build the feedback loop into the operating model.

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

1. **Assess the platform baseline.** Confirm whether the org runs Einstein Bots (legacy) or Agentforce Agents. Check the Salesforce edition (Einstein Bots require Service Cloud; Agentforce requires the Agentforce add-on). Verify that Omni-Channel is enabled and configured.
2. **Analyze historical case data.** Pull the top case reasons by volume from the Case object. Group them into candidate intents. Validate that each intent can be expressed with 20+ distinct utterances from real customer language.
3. **Design the intent taxonomy.** Create 15-25 well-bounded intents. Map each to a resolution path: knowledge article, self-service action, or agent handoff. Document the fallback intent behavior.
4. **Design the dialog/topic structure.** For Einstein Bots, map each intent to a dialog with clear steps. For Agentforce, define topics with descriptions and map available actions. In both cases, keep conversation depth under 5 turns for simple requests.
5. **Design the handoff architecture.** Define which bot variables transfer to the agent. Map variables to LiveChatTranscript or MessagingSession fields. Configure Skills-Based Routing so the bot routes to the correct agent team. Build the agent console layout to surface transferred context.
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

Non-obvious platform behaviors that cause real production problems:

1. **Intent confidence threshold defaults are too permissive** — The default confidence threshold for intent matching is low enough to route ambiguous input to the wrong dialog. Set the threshold to at least 0.7 in production and route anything below to the fallback intent. Failing to tune this causes silent misroutes that damage CSAT.
2. **Bot variables do not automatically transfer on handoff** — Setting a value in a bot variable does not mean the agent sees it. Each variable must be explicitly mapped to a LiveChatTranscript or MessagingSession field in the Transfer action configuration. Architects who skip this step deliver a bot that transfers customers to agents who have no idea what the conversation was about.
3. **Utterance retraining is not incremental** — When you add utterances to an existing intent or add a new intent, you must retrain the entire model. The old model stays active until the new one completes training. During training, the bot continues to use the old model, which means newly added intents are invisible until training finishes.
4. **Rich message components fail silently on SMS/WhatsApp** — Carousels, quick replies with images, and rich cards render only on web chat and in-app messaging. On SMS and WhatsApp they either degrade to plain text or disappear entirely. The bot does not throw an error; the customer simply sees nothing.
5. **Agentforce topic descriptions are the new dialog design** — In Agentforce, the topic description is what the LLM uses to decide whether a topic applies. A vague description ("handle customer issues") causes the agent to match too broadly. A description must be as precise as an intent definition: specific about what is in scope and what is not.

---

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

- Einstein Bots Overview — https://help.salesforce.com/s/articleView?id=sf.bots_service_intro.htm
- Agentforce Overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_overview.htm
