---
name: conversational-ai-architecture
description: "Use when designing or evaluating a Salesforce conversational AI deployment that involves Agentforce agents, Einstein Bots, or a combination of both. Triggers: Agentforce topic design, Einstein Bot handoff to Agentforce, multi-agent orchestration, conversational channel routing, Atlas Reasoning Engine behavior. Does NOT cover Einstein Bot standalone implementation (see einstein-bot-architecture), Omni-Channel routing for human agents, or Flow-only automation without a conversational surface."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I design topics for an Agentforce agent that handles multiple business functions without mis-routing"
  - "how do I transfer context from an Einstein Bot to an Agentforce agent without losing session data"
  - "what is the right architecture for deploying Agentforce alongside an existing Einstein Bot IVR front-end"
tags:
  - conversational-ai-architecture
  - agentforce
  - einstein-bot
  - atlas-reasoning-engine
  - multi-agent
  - omni-channel
inputs:
  - "List of business functions or intents the conversational experience must handle"
  - "Existing channel inventory (IVR, chat, SMS, Slack, etc.)"
  - "Whether Einstein Bots are already deployed in the org"
  - "Expected concurrent session volume per channel"
outputs:
  - "Agentforce topic design with scope-bounded natural-language descriptions"
  - "Session context transfer mapping between Einstein Bot and Agentforce"
  - "Channel routing diagram showing Omni-Channel, Agentforce, and human agent handoff points"
  - "Architecture decision record covering paradigm choice (Einstein Bot vs. Agentforce vs. hybrid)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Conversational AI Architecture

This skill activates when a practitioner needs to design, review, or troubleshoot a Salesforce conversational AI deployment that uses Agentforce topics-and-actions, Einstein Bots, or a hybrid of both. It enforces the architectural distinction between the two paradigms and provides patterns for channel routing, session context handoff, and multi-topic Agentforce deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org has existing Einstein Bot deployments. If so, identify which channels they serve and whether session context variables are defined on the bot.
- The most common wrong assumption is that Agentforce topics work like Einstein Bot intents — they do not. Topics have no utterance training sets. Scope is controlled entirely by the precision of the natural-language topic description. Writing utterances for topics produces no effect.
- Key limits: an Agentforce agent is subject to the Atlas Reasoning Engine's context window; very long system prompts or topic descriptions degrade routing accuracy. Omni-Channel capacity rules apply to human agents and Einstein Bots but not to Agentforce agents. Agentforce agents do not consume Omni-Channel capacity units.

---

## Core Concepts

### The Two Paradigms: Einstein Bot NLU vs. Agentforce Topics-and-Actions

Einstein Bots use a trained NLU model. Practitioners define intents and provide labeled utterance examples. The model is trained and versioned. Routing decisions are based on predicted intent confidence scores against that trained model.

Agentforce uses the Atlas Reasoning Engine, a large language model that performs intent routing at inference time. There is no training phase. Practitioners define Topics using natural-language descriptions of scope. The Atlas Reasoning Engine reads those descriptions at runtime and routes incoming messages to the most semantically appropriate topic. This means scope boundaries are expressed in prose, not in utterance lists, and imprecision in prose produces routing errors.

Architecturally, these are completely distinct systems. A practitioner cannot apply skills learned on Einstein Bot NLU design directly to Agentforce topic design.

### Topic Description Precision Controls Agentforce Routing Accuracy

Because the Atlas Reasoning Engine routes based on the semantic content of topic descriptions, a vague or overlapping description causes one of two failure modes: the agent accepts messages outside its intended scope (over-matching), or it rejects valid messages because the description is too narrow or ambiguous (under-matching).

A well-written topic description states three things explicitly:
1. What business function the topic covers.
2. What specific requests are in scope (examples in prose, not utterance lists).
3. What is explicitly out of scope for this topic.

Topics serving distinct business functions (billing, technical support, account management) must have descriptions that do not share overlapping scope language. The Atlas Reasoning Engine uses all topic descriptions together to decide routing; overlap between descriptions introduces ambiguity.

### Session Context Transfer from Einstein Bot to Agentforce

When an Einstein Bot hands off to an Agentforce agent via Omni-Channel, session context does not transfer automatically. An Einstein Bot stores data in bot variables. An Agentforce agent receives a new session with no knowledge of prior bot conversation unless the architect explicitly maps bot variables to a transfer payload.

The transfer mechanism is the Einstein Bot's "Transfer to Agent" action, which can pass a set of named attributes to the receiving Omni-Channel queue or directly to an Agentforce agent. The receiving Agentforce agent must have Actions defined to consume those attributes and inject them into the conversation context. Without this explicit mapping, the Agentforce agent starts with no prior context and the customer must repeat information already collected by the bot.

### Multi-Agent Orchestration in Agentforce

Agentforce supports an orchestrator-worker pattern where one Agentforce agent (the orchestrator) delegates to specialized sub-agents. The orchestrator routes based on topic descriptions of the sub-agents, applying the same Atlas Reasoning Engine semantics. This pattern is appropriate when a single business domain is large enough that one agent's topic list would exceed roughly 20 topics — beyond that, routing accuracy and maintainability degrade.

Multi-agent orchestration introduces a new failure mode: context isolation between agents. Each sub-agent has its own session context. The orchestrator must explicitly pass required context when delegating.

---

## Common Patterns

### Pattern 1: Einstein Bot IVR Front-End with Agentforce Escalation

**When to use:** The org has an IVR or simple self-service channel that handles DTMF navigation, identity verification, or FAQ deflection via Einstein Bot, and needs to escalate more complex requests to an Agentforce agent before potentially routing to a human.

**How it works:**
1. Einstein Bot handles the initial channel interaction (IVR DTMF routing, identity verification questions, FAQ deflection).
2. When the bot determines escalation is needed, it calls a "Transfer to Agent" action. Before transferring, the bot populates transfer attributes with collected session data: verified customer ID, detected intent category, conversation summary.
3. The Omni-Channel routing rule directs the transfer to the Agentforce agent queue rather than a human queue.
4. The Agentforce agent receives the transfer attributes and an Action injects them into its working context (e.g., "Customer identity verified: Account ID 001xx. Original request category: billing dispute").
5. If the Agentforce agent determines human escalation is required, it invokes a human handoff action and passes its full conversation transcript to the assigned human agent via Omni-Channel.

**Why not the alternative:** Routing complex requests directly to a human agent from the Einstein Bot skips the LLM reasoning layer, increasing average handle time and requiring agents to re-collect context already gathered by the bot.

### Pattern 2: Scope-Bounded Multi-Topic Agentforce Agent

**When to use:** A single Agentforce agent must handle multiple business functions (e.g., billing, technical support, account management) without mis-routing requests between topics.

**How it works:**
1. Define one Topic per business function. Never share a Topic across functions.
2. Write each topic description in three parts: (a) what this topic covers, (b) concrete example request types in scope, (c) explicit statement of what this topic does not handle.
3. Review all topic descriptions together — any sentence that could apply equally to two topics is an overlap risk. Rewrite to eliminate overlap.
4. Assign Actions to each Topic based on the data access and operations required for that function only. Do not share Actions across Topics unless the Action is truly generic (e.g., "look up account ID").
5. Test routing with adversarial inputs: requests that sit on the boundary between two topics. Tune description wording until routing is consistent.

**Why not the alternative:** A single Topic attempting to cover all business functions using broad language ("help customers with their account") produces unreliable routing because the Atlas Reasoning Engine cannot distinguish between function-specific sub-intents from a vague description.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple FAQ deflection, DTMF routing, or identity verification with no open-ended reasoning | Einstein Bot | Deterministic NLU, no LLM inference cost, faster response for structured flows |
| Complex natural-language requests requiring multi-step reasoning or tool invocation | Agentforce agent | Atlas Reasoning Engine handles ambiguous input; Actions provide structured tool access |
| Existing Einstein Bot + new complex use case | Hybrid: Einstein Bot front-end, Agentforce escalation via Omni-Channel | Preserves existing bot investment; adds reasoning capability without replacing the bot |
| Single business domain with more than 20 distinct topic areas | Multi-agent orchestration (orchestrator + specialist sub-agents) | Routing accuracy degrades with large topic lists on a single agent; specialization improves reliability |
| Two business functions with overlapping natural-language scope | Separate agents or redesign topic descriptions to eliminate overlap | Shared scope language causes Atlas Reasoning Engine mis-routing at inference time |
| Regulated industry requiring deterministic routing audit trail | Einstein Bot or hybrid with explicit routing rules | LLM inference-time routing is probabilistic; compliance requirements may demand deterministic paths |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory existing channels and systems.** Identify which channels are in use (IVR, chat, SMS, Slack, Experience Cloud), whether Einstein Bots are deployed, and which channel serves the target use case. Confirm Omni-Channel is enabled and configured.
2. **Choose the paradigm.** Use the Decision Guidance table to determine whether the solution should be Einstein Bot only, Agentforce only, or a hybrid. Document the decision and reasoning in an architecture decision record.
3. **Design Agentforce Topics.** For each business function, draft a topic description covering scope, example requests, and explicit exclusions. Review all descriptions together for overlap. Aim for 5–15 topics per agent; escalate to multi-agent orchestration if the topic count exceeds 20.
4. **Map session context transfer.** If Einstein Bot is in the architecture, enumerate all bot variables that must be available to the Agentforce agent or human agent at handoff. Define the transfer attribute mapping. Implement and test with a real session.
5. **Configure Actions per Topic.** Assign only the Actions required by each Topic. Avoid giving topics access to Actions they do not need — unused Action access widens the agent's capability surface unnecessarily.
6. **Test adversarial routing scenarios.** For each topic boundary, construct requests that could plausibly match either topic. Verify routing is consistent. Tune topic descriptions until boundary routing is reliable.
7. **Review security and data access.** Confirm that each Action runs with least-privilege record access. Verify that session context transfer does not expose PII beyond what the receiving agent requires.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each Agentforce Topic has a description with explicit in-scope and out-of-scope statements
- [ ] No two Topic descriptions share overlapping scope language
- [ ] Session context transfer from Einstein Bot to Agentforce is explicitly mapped (bot variables to transfer attributes)
- [ ] Agentforce agent Actions are scoped to least-privilege record access
- [ ] Adversarial boundary routing tests pass for all adjacent topic pairs
- [ ] Omni-Channel routing rules correctly direct transfers between Einstein Bot, Agentforce, and human queues
- [ ] Multi-agent orchestration is used if any single agent would exceed 20 topics

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Agentforce topics have no utterance training** — Topic descriptions are prose instructions to the Atlas Reasoning Engine, not NLU training data. Adding lists of example phrases to a topic description does not train a model; it adds context that the LLM reads at inference time. Practitioners familiar with Einstein Bot design expect to "train" the system with utterances — no such step exists in Agentforce. The only lever is description wording precision.
2. **Omni-Channel capacity rules do not apply to Agentforce agents** — Human agents consume capacity units; Einstein Bots are governed by their own session limits. Agentforce agents are not capacity objects and do not appear in Omni-Channel capacity management. A practitioner who configures capacity-based routing for an Agentforce queue will find that capacity rules are ignored for the Agentforce leg of the routing.
3. **Session context is not automatically inherited on bot-to-Agentforce transfer** — When an Einstein Bot executes a "Transfer to Agent" action and the target is an Agentforce agent, the Agentforce agent starts a new session with zero prior context unless transfer attributes are explicitly populated by the bot and consumed by an Agentforce Action. This surprises teams who expect Omni-Channel transfers to carry conversation history automatically.
4. **Topic description overlap causes silent mis-routing** — Unlike an exception or error, routing to the wrong topic produces a plausible-looking wrong response. There is no runtime warning that two topics had overlapping descriptions. The failure manifests as inconsistent behavior on boundary requests, which is difficult to detect without targeted adversarial testing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Agentforce Topic design document | Natural-language descriptions for each topic with explicit scope boundaries, example request types, and exclusions |
| Session context transfer map | Table of Einstein Bot variables mapped to Agentforce transfer attributes and the Actions that consume them |
| Channel routing diagram | Diagram showing Omni-Channel queues, Einstein Bot nodes, Agentforce agent nodes, and human agent nodes with transfer conditions |
| Architecture decision record | Documents the paradigm choice (Einstein Bot / Agentforce / hybrid) with rationale and trade-offs |

---

## Related Skills

- einstein-bot-architecture — For Einstein Bot standalone design, NLU model training, intent/dialog design, and Bot Builder configuration. Use alongside this skill when the architecture includes an Einstein Bot front-end.
- ai-governance-architecture — For governance controls, audit logging, and trust layer configuration when deploying Agentforce in regulated industries.
- omni-channel-routing — For Omni-Channel queue configuration, skill-based routing rules, and capacity model design that affects how transfers between bot, Agentforce, and human agents are executed.
