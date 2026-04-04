---
name: einstein-bots-to-agentforce-migration
description: "Use when migrating an existing Einstein Bot (legacy or Enhanced) to Agentforce: feature mapping, conversation design translation, cutover planning, hybrid bot/agent architecture, and context handoff. Triggers: 'migrate einstein bot to agentforce', 'convert legacy bot to agentforce', 'einstein bot retiring deadline', 'hybrid bot agentforce pattern', 'bot dialog to topic migration'. NOT for new Agentforce setup with no existing bot — use agentforce/agentforce-agent-creation instead."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "how do I migrate my Einstein Bot to Agentforce before the legacy chat retirement deadline"
  - "convert existing bot dialogs and intents to Agentforce topics and actions"
  - "hybrid pattern keeping legacy bot alongside Agentforce for structured flows"
  - "how does context pass from a bot session to an Agentforce handoff"
  - "what does the create AI agent from bot tool do and is the migration lossless"
tags:
  - einstein-bots
  - agentforce
  - migration
  - legacy-chat
  - bot-to-agent
inputs:
  - "existing Einstein Bot type: legacy (Classic) or Enhanced Bot"
  - "inventory of dialogs, intents, utterances, and bot variables currently in use"
  - "target channel: Messaging for Web, Embedded Service, or both"
  - "deadline context: Legacy Chat retiring Feb 14 2026 — confirm current date relative to this"
  - "hybrid vs full-cutover decision: whether structured flows should remain bot-driven"
outputs:
  - "feature-mapping table: bot constructs to Agentforce equivalents"
  - "migration approach decision: use 'Create AI Agent from Bot' tool vs manual scaffold"
  - "hybrid architecture pattern with context handoff configuration"
  - "cutover checklist with rollback steps"
  - "post-migration validation plan including handoff latency testing"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Einstein Bots to Agentforce Migration

Use this skill when the task is migrating an existing Einstein Bot to Agentforce — mapping legacy constructs to their Agentforce equivalents, deciding on a hybrid vs full-cutover strategy, translating dialogs into Topics and Actions, and planning a safe cutover before the Legacy Chat retirement deadline. This skill does not cover net-new Agentforce agent creation from scratch — see `agentforce/agentforce-agent-creation` for that.

> **Critical deadline:** Legacy Chat (the chat channel used by Classic and some Enhanced Bots) is retiring **February 14, 2026**. Any bot running on Legacy Chat must be moved to a supported channel (Messaging for In-App and Web, or Agentforce) before that date or it will stop serving users.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What type of bot exists?** Legacy (Classic) Einstein Bot vs Enhanced Bot. The "Create AI Agent from Bot" migration tool only works with Enhanced Bots. Classic Bot owners must scaffold their Agentforce agent manually.
- **Is the org on Enhanced Bot infrastructure?** Enhanced Bots are required for both the migration tool and for a clean hybrid pattern. Check Setup > Einstein Bots and confirm whether the bot lists as "Enhanced" in the type column.
- **What is the current channel?** Legacy Chat, Embedded Service (Messaging for In-App and Web), or both? Legacy Chat is the only channel being retired on Feb 14 2026 — Embedded Service channels without Legacy Chat underpinnings are not affected by the retirement itself, but the agent migration may still be desirable.
- **What structured flows must be preserved exactly?** Password reset, order status lookups with form validation, and other deterministic flows are good candidates for the hybrid pattern rather than a full rewrite in Agentforce.
- **Is Einstein enabled and the Agentforce toggle active?** Both are required before the migration tool or any Agentforce agent creation is possible.

---

## Core Concepts

### The "Create AI Agent from Bot" Tool Is a Draft Generator, Not a Lossless Migration

Salesforce provides a Beta "Create AI Agent from Bot" tool (Setup > Einstein Bots > [Your Enhanced Bot] > Create AI Agent) that generates a draft Agentforce agent from an existing Enhanced Bot. This tool automates the structural scaffolding — it does not produce a production-ready agent.

The translation is intentionally lossy because the underlying execution model has changed:

| Bot Construct | Agentforce Equivalent | Translation Notes |
|---|---|---|
| Dialog | Topic | Dialog name and purpose become Topic name and description |
| Dialog Step | Action | Each step that performs work becomes a candidate Action |
| Intent / Utterances | Topic instructions (natural language) | Utterances become examples in the topic description — no NLU training required |
| Bot Variables | MessagingSession custom fields or Flow variables | Context must be passed explicitly through a handoff mechanism |
| Escalation to Agent | Human Escalation action | Escalation target must be re-configured in the new agent |

The tool generates Topics from Dialogs. It does not generate production-ready Action implementations. Review every generated Topic and Action placeholder before treating the draft as deployable.

The tool is only available for **Enhanced Bots**. Legacy (Classic) Bots must be migrated by hand.

### Agentforce Uses LLM Semantic Routing, Not Utterance Training

Legacy bots required utterance training — you provided dozens of example phrases, trained an NLU model, and re-trained when coverage gaps emerged. Agentforce uses a large language model that routes conversations semantically based on the Topic description and instructions you provide. This is a fundamental shift in the authoring model:

- You write **clear, specific Topic descriptions** in natural language, not utterance lists.
- The LLM matches user intent against Topic descriptions without training.
- Edge-case routing failures are fixed by refining Topic descriptions, not by adding more utterances.
- Utterances imported by the migration tool become illustrative examples in Topic instructions — they are hints, not a trained classifier.

This means migrated Topics often need their descriptions sharpened. A Dialog named "Order Status" becomes a Topic with the same name — but the description must tell the LLM exactly when to route there: "Use this topic when a customer asks about the current state, shipping progress, or delivery date of an existing order."

### GenAiPlannerBundle Is What Makes It an Agent

At the metadata level, the difference between a Classic Bot and an Agentforce agent is the presence of a `GenAiPlannerBundle` attached to the `BotVersion`. Without `GenAiPlannerBundle`, a deployed Bot metadata component is a chatbot, not an Agentforce reasoning agent. The "Create AI Agent from Bot" tool writes this bundle. Manual migrations must include it.

When deploying, always retrieve and deploy `Bot`, `BotVersion`, `GenAiPlannerBundle`, `GenAiPlugin` (Topics), and `GenAiFunction` (Actions) together as a single bundle. Missing any component leaves the agent in an inconsistent state.

### Hybrid Pattern: Keep the Bot for Structured Flows

A full cutover to Agentforce is not always the right move, especially for deterministic structured flows (form-driven data capture, exact-match lookups, regulated disclosures). The endorsed hybrid pattern is:

1. Keep the Enhanced Bot as the entry point for structured flows.
2. Hand off to Agentforce when the conversation needs LLM reasoning, open-ended queries, or knowledge retrieval.
3. Pass context from the bot session to the Agentforce agent via `MessagingSession` custom fields populated by a Flow that runs before the bot session ends.

This pattern lets teams migrate incrementally without rebuilding every dialog into an Agentforce Action on day one.

---

## Common Patterns

### Pattern 1: Use the Migration Tool for an Enhanced Bot

**When to use:** The bot is Enhanced, the team wants a structural head start, and the migration is not time-critical (Beta tool quality).

**How it works:**

1. Navigate to Setup > Einstein Bots > select the Enhanced Bot > click **Create AI Agent**.
2. The tool generates a draft Agentforce agent with one Topic per Dialog and placeholder Actions per dialog Step.
3. Open the generated agent in Agentforce Builder. For each Topic:
   - Rewrite the description to be a clear LLM-routing instruction, not just the dialog name.
   - Remove utterance lists that were imported — convert key phrases to illustrative sentences in the Topic instructions.
   - Implement real Action logic — the tool creates placeholders; each Action needs a Flow, Apex, or API connection wired in.
4. Configure the Agent User (EinsteinServiceAgent User) using the dropdown picker.
5. Add or update `MessagingSession` custom fields to carry bot context into the new agent.
6. Test in Conversation Preview. Pay particular attention to:
   - Topic routing boundaries — the LLM may route differently than the NLU classifier did.
   - Handoff latency — LLM planning introduces a response delay that differs from scripted bot step execution; validate this is within the experience SLA.
7. Activate and assign to the target channel deployment.

### Pattern 2: Manual Migration for a Classic Bot

**When to use:** The bot is Classic/Legacy — the migration tool is unavailable.

**How it works:**

1. Export or document the full dialog map from Setup > Einstein Bots.
2. Create a new Agentforce agent via Setup > Agentforce Agents > New Agent (see `agentforce/agentforce-agent-creation`).
3. For each dialog, create a Topic in Agentforce Builder with a description written as a routing instruction.
4. For each dialog step that performs an action (SOQL lookup, variable assignment, record update, escalation), create an Agentforce Action backed by a Flow or Apex.
5. Replace all utterance-driven intent matching with Topic description language — test with conversational variants.
6. Do not migrate bot variable storage as-is. Map each bot variable to either an Action output, a MessagingSession custom field, or a session variable in the new conversation model.
7. Test, activate, and cut over the channel before Feb 14 2026 if currently on Legacy Chat.

### Pattern 3: Hybrid Bot + Agentforce with Context Handoff

**When to use:** Structured dialogs must be preserved exactly (compliance, data validation), while open-ended queries should go to Agentforce.

**How it works:**

1. Keep the Enhanced Bot as the primary entry point on the channel.
2. At the point in the bot flow where the conversation should transition to Agentforce reasoning, trigger a Flow from the bot.
3. In the Flow, populate `MessagingSession` custom fields with the relevant session context: authenticated user ID, case number, bot-captured slot values, conversation stage.
4. End the bot dialog and initiate the Agentforce session. The Agentforce agent reads the `MessagingSession` custom fields at session start via a "Get Session Context" Action.
5. Agentforce handles the open-ended portion. If the user re-triggers a structured flow, the agent can invoke it as an Action backed by a Flow that replicates the bot dialog logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Enhanced Bot, migrating before deadline | Use "Create AI Agent from Bot" tool, then refine Topics and implement Actions | Generates structural scaffold quickly; still requires Topic description rewrites and Action implementations |
| Classic/Legacy Bot, migrating before deadline | Manual scaffold a new Agentforce agent, map dialogs to Topics by hand | Migration tool does not support Classic Bots |
| Bot has complex structured flows that must work exactly as-is | Hybrid pattern: keep bot for structured flows, hand off to Agentforce for open-ended | Full rewrite risk is high; hybrid reduces scope |
| Currently on Legacy Chat channel | Immediate priority: move to Messaging for In-App and Web before Feb 14 2026 | Legacy Chat retiring Feb 14 2026 regardless of migration status |
| Migrated agent feels slower than original bot | Investigate handoff latency; test LLM planning response time vs scripted step timing | LLM planning introduces inherent latency that scripted bots do not have |
| Utterances not routing correctly after migration | Rewrite Topic descriptions as routing instructions; do not add more utterances | Agentforce routes by LLM semantic match, not trained NLU — utterances are not the fix |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Inventory the existing bot** — document bot type (Classic or Enhanced), channel (Legacy Chat vs Messaging), all dialogs, intents, variables, escalation targets, and integrations. Confirm whether the Feb 14 2026 Legacy Chat deadline applies.
2. **Decide on migration approach** — Enhanced Bot: consider using the migration tool as a scaffold. Classic Bot: plan a manual scaffold. For both: decide hybrid vs full-cutover based on the structured flow inventory.
3. **Scaffold the Agentforce agent** — use the migration tool (Enhanced only) or create manually via Setup > Agentforce Agents. Treat any generated output as a draft; do not activate until Topics and Actions are reviewed.
4. **Rewrite Topic descriptions** — each Topic description must tell the LLM exactly when to route there. Replace dialog names with specific, natural-language routing instructions. Remove raw utterance imports.
5. **Implement Actions** — each Action placeholder must be backed by real logic: a Flow, an Apex class, or a configured external service action. Test each Action in isolation before testing end-to-end flows.
6. **Configure context handoff** — for hybrid patterns, add `MessagingSession` custom fields, populate them in a pre-handoff Flow, and implement a "Get Session Context" Action in the Agentforce agent.
7. **Test handoff latency and cut over** — validate LLM planning response time against the experience SLA. Activate, assign to channel, and confirm Legacy Chat cutover completes before the Feb 14 2026 deadline.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Bot type confirmed — Classic or Enhanced. Migration tool eligibility determined.
- [ ] Legacy Chat channel status confirmed — if in use, cutover planned before Feb 14 2026.
- [ ] Every Dialog has a corresponding Topic with a clear LLM-routing description (not just the dialog name).
- [ ] Raw utterance imports replaced with Topic description language or removed.
- [ ] Every Action placeholder from the migration tool has real logic implemented (Flow, Apex, or service action).
- [ ] GenAiPlannerBundle is present in the deployed BotVersion metadata — confirms agent reasoning capability.
- [ ] Agent User (EinsteinServiceAgent User) is selected via dropdown, not typed.
- [ ] Context handoff via MessagingSession custom fields tested end-to-end (hybrid pattern).
- [ ] Handoff latency measured and confirmed within experience SLA.
- [ ] Agent activated and assigned to the correct channel deployment.
- [ ] Einstein Trust Layer configuration reviewed for the new agent's data access patterns.
- [ ] Rollback plan documented — prior bot remains deployable until cutover is confirmed stable.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **"Create AI Agent from Bot" is Beta and Enhanced-only** — teams running Classic/Legacy bots discover the migration tool is unavailable only when they attempt it. Classic bots have no automated migration path; manual scaffolding is the only option.
2. **Utterance lists do not train the Agentforce routing model** — importing utterances from the old bot and expecting them to improve routing is the most common migration mistake. Agentforce uses LLM semantic matching; utterances imported by the tool are illustrative text in the Topic description, not a trained classifier.
3. **LLM planning latency differs from scripted bot response time** — classic bots execute deterministic dialog steps with near-instant response. Agentforce agents invoke an LLM planning cycle before executing an Action. This latency may breach existing experience SLAs.
4. **GenAiPlannerBundle must be included in every deployment** — deploying only Bot and BotVersion leaves the agent in a chatbot state, not an Agentforce agent. Always deploy the full bundle: Bot, BotVersion, GenAiPlannerBundle, GenAiPlugin, GenAiFunction.
5. **MessagingSession custom fields are not automatically populated by the bot** — the hybrid context handoff requires an explicit Flow step in the bot that writes context values to MessagingSession custom fields before session transition. Omitting this Flow step means the Agentforce agent starts with no context from the bot portion of the conversation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration approach decision | Documented choice of migration tool vs manual scaffold, and hybrid vs full-cutover, with rationale |
| Feature mapping table | Completed mapping of all existing dialogs, intents, and variables to Agentforce Topics, Actions, and session fields |
| Topic description drafts | LLM-routing-ready descriptions for each Topic, replacing the dialog name/utterance-based model |
| Context handoff configuration | MessagingSession custom field schema and the pre-handoff Flow design for hybrid pattern |
| Cutover checklist | Channel-specific steps to retire Legacy Chat and activate the Agentforce agent before Feb 14 2026 |
| Post-migration validation plan | Test cases including handoff latency, topic routing accuracy, escalation paths, and context continuity |

---

## Related Skills

- `agentforce/agentforce-agent-creation` — use for net-new agent setup when no existing bot is in scope.
- `agentforce/agent-topic-design` — use when refining Topic descriptions and routing boundaries after migration scaffold.
- `agentforce/agent-actions` — use when implementing Action logic and contracts for migrated dialog steps.
- `agentforce/agent-channel-deployment` — use when configuring the Messaging for In-App and Web channel to replace Legacy Chat.
- `agentforce/einstein-trust-layer` — use to validate data masking, ZDR, and grounding policies for the new agent before activation.
