---
name: agentforce-agent-handoff-patterns
description: "Use when designing how an Agentforce agent transfers the conversation to a human agent (Omni-Channel), to another bot/agent, or to an alternate workflow — including context package, deflection, escalation triggers, and user messaging. Triggers: 'agent to human handoff', 'agentforce escalate to omni channel', 'agent to agent handoff', 'transfer conversation with context', 'agent deflection fallback'. NOT for topic scope and selector design — use agentforce/agent-topic-design. NOT for the overall Einstein Bot plus Agentforce estate topology — use architect/conversational-ai-architecture."
category: agentforce
salesforce-version: "Spring '26+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Operational Excellence
triggers:
  - "how to escalate agentforce to a human"
  - "agent to agent handoff pattern"
  - "transfer conversation context to omni channel"
  - "agent deflection fallback rules"
  - "agentforce hand back after human resolution"
  - "route a conversation from my agent to a live service rep"
  - "set up an escalation flow for my Agentforce service agent"
tags:
  - agentforce
  - handoff
  - escalation
  - omni-channel
  - human-in-the-loop
inputs:
  - "conditions that trigger handoff"
  - "destination (human queue, alternate agent, workflow)"
  - "context to package for the receiver"
outputs:
  - "handoff trigger catalog"
  - "context package schema"
  - "user-facing messaging per handoff type"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agentforce Agent Handoff Patterns

Most agent failures are handoff failures. The agent knew it was stuck, did not have a clean way to transfer the conversation, and either looped, hallucinated, or dumped the user into a cold queue without context. Good handoff design treats the transfer as a first-class capability with its own triggers, its own context schema, and its own messaging — not as "throw an error and let Omni-Channel figure it out."

Three kinds of handoff matter: agent-to-human (Omni-Channel), agent-to-agent (swap persona, specialization, or domain), and agent-to-workflow (spawn a case, route to a Flow, schedule a callback). Each has different mechanics but shares the same design skeleton: trigger → context package → user message → receiver acknowledgment → (optional) hand-back.

> **Terminology.** *Subagent* is the April 2026 rename of *topic*. Functionality
> did not change and the API surface did not rename — the metadata type is still
> `GenAiPlugin`, and the skill slug `agentforce/agent-topic-design` keeps the
> older word.

---

## Before Starting

- List the handoff triggers expected for this agent (policy, confidence, scope, authorization, user request).
- List destinations and what each needs to take the conversation from here.
- Confirm Omni-Channel queue structure and presence model.
- Confirm whether hand-back (returning to the agent after human resolution) is a requirement.

## Questions to Ask Before Configuring

Ask these before designing any transfer. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is the agent built in the legacy builder or in Agent Script?" | Legacy agents escalate only through the standard Escalation topic; Agent Script uses `@utils.escalate` with a connection block (Gotchas 6, 7) | The escalation mechanism to configure | A transfer that actually routes instead of a custom topic that never does |
| "Which Omni-Channel flow and queue receive the conversation, and what happens when nobody is available?" | Escalation needs a fallback queue for Messaging Session, and a fallback route if the primary is down (Gotchas 1, 9) | The flow, the queue, and the fallback behaviour | No customer stranded in a silent wait |
| "Which conditions trigger a handoff?" | The Escalation topic escalates only on explicit request until widened (Gotcha 6) | A trigger list across user, confidence, scope, policy, authorization and technical | Handoffs that follow policy, not just "let me speak to a human" |
| "What must the rep see so the customer does not repeat themselves?" | A transcript dump is not a summary (Gotcha 3) | The context package fields and where they are written | A case the rep can act on in seconds |
| "Does the conversation ever come back to the agent, or move between agents?" | Transitions are one way and restart the target; connected subagents are independent agents (Gotchas 4, 5, 12) | The hand-back or delegation design, with the variables that carry state | No repeated questions after a detour |
| "Which channel and agent type serve the customer?" | Only Agentforce Service Agent connects to enhanced Messaging (Gotcha 10) | A confirmed channel and agent type | A design that can be connected |

## Core Concepts

### Platform Mechanics

| Destination | Legacy builder | Agent Script | Source |
|---|---|---|---|
| Service rep (Omni-Channel) | Standard Escalation topic, which routes through its outbound Omni-Channel flow; no custom topic can do this | `@utils.escalate` plus a `connection messaging` block naming the Omni-Channel flow | Generative AI guide, Agent Topic: Escalation; Agentforce Developer Guide, Utils and Agent Script Blocks |
| Fallback when the primary route is unavailable | `Bot.defaultOutboundFlow` (API 65.0 and later) and a fallback queue for Messaging Session | Same | Metadata API reference, Bot; Enhanced Chat example |
| Another agent | Multi-agent configuration | `connected_subagent` block, used as a reasoning action | Agentforce Developer Guide, Agent Script Blocks |
| Another subagent in the same agent | Topic routing | `@utils.transition to @subagent.Name` (one way) | Agentforce Developer Guide, Utils |
| Workflow (case, callback) | Custom action on the Escalation topic or the owning subagent | Custom action, then escalate or end | Generative AI guide, Agent Topic: Escalation |
| End of conversation | Not applicable | `@utils.end_session` | Agentforce Developer Guide, Utils |

`references/metadata-examples.md` shows the context-package action, the Agent Script escalation block and the fallback element to review.

### Handoff Trigger Types

1. **User-initiated** — "I want to speak to a person."
2. **Confidence-based** — agent is unsure after N attempts.
3. **Scope-based** — user crossed into a topic this agent does not cover.
4. **Policy-based** — refund > threshold, fraud flag, VIP customer.
5. **Authorization-based** — action requires manager or regulated approval.
6. **Technical** — system unavailable, data missing.

### Context Package

The handoff receiver needs:
- Original user intent and paraphrased summary.
- Data the agent gathered (account, policy, case numbers).
- Actions attempted and their outcomes.
- Why the handoff fired.
- A conversation transcript link, not the raw transcript in the payload.

### Destinations

| Destination | Use |
|---|---|
| Omni-Channel queue | Human agent, with pre-populated case or conversation. |
| Another Agentforce agent | Specialized persona or different domain. |
| Workflow | Async case, Flow, Queue, scheduled callback. |
| No handoff (refuse + recommend) | Sometimes the right answer is "I can't help; here's how." |

### User Messaging

Every handoff needs an explicit user message that says what is happening and what to expect. "Let me connect you with an agent" is better than silence. Predicted wait time (if known) is better than vague.

### Hand-Back

If the agent will resume after human resolution (common in hybrid service models), the hand-back protocol must preserve or summarize what the human did.

---

## Common Patterns

### Pattern 1: Structured Escalation To Omni-Channel

On trigger: run a custom action that creates a case with a structured description, then escalate through the Escalation topic's Omni-Channel flow (legacy builder) or `@utils.escalate` (Agent Script) with an escalation message. The case captures the context package in a standard format.

### Pattern 2: Warm Agent-To-Agent Handoff

One agent hands to another without losing conversation continuity. In Agent Script the receiver is a `connected_subagent`, a complete independent agent, so pass a summary and the variables it needs rather than the verbatim history.

### Pattern 3: Confidence-Triggered Escalation

After 2 unsuccessful resolution attempts on the same intent, fire escalation. Avoids infinite loops where the agent keeps retrying the same failing path.

### Pattern 4: Authorization Gate Handoff

For actions beyond the agent's authority (e.g. refund > limit), pause, hand to an approver (human or approval process), resume on approval.

### Pattern 5: Deflection-With-Recommendation

If no suitable human is available or the query is out-of-scope with no sensible destination, do not queue indefinitely. Provide a clear next-best-action (support link, callback scheduler).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| User explicitly asks for human | Immediate handoff with context | Respect user intent |
| Agent stuck in a loop | Confidence-triggered escalation | Breaks infinite retries |
| Out-of-scope with no destination | Deflection with recommendation | Do not park user in void |
| Refund > threshold | Authorization-gated handoff | Compliance |
| Specialized domain (e.g. claims vs billing) | Agent-to-agent handoff | Persona clarity |
| Queue overloaded | Callback scheduling, not queue dump | Respect wait-time expectations |

## Review Checklist

- [ ] Each handoff trigger has a destination.
- [ ] Context package schema is documented.
- [ ] User message per handoff type is written.
- [ ] Confidence-based escalation is configured.
- [ ] Deflection path exists when no human is available.
- [ ] Hand-back protocol is designed if applicable.

## Recommended Workflow

1. List handoff triggers relevant to this agent.
2. Map each to a destination.
3. Design the context package (fields, format, size).
4. Write user messaging per handoff type.
5. Implement the transfer mechanism from the Platform Mechanics table: the context-package action, then the Escalation topic flow or `@utils.escalate` with its connection block, plus the fallback queue and fallback route.
6. Test in preview with and without an available rep, and verify hand-back works if required.

---

## Salesforce-Specific Gotchas

1. Escalation needs a fallback queue for the Messaging Session object; without fallbacks, a conversation can wait with no one available.
2. Case routing by owner vs queue has different audit trails.
3. Context dumped as raw text into a case description is unsearchable and bloats storage.
4. Agent-to-agent handoff starts an independent agent: the new agent does not see the previous subagent's instructions.
5. Hand-back is not automatic; within one agent, transitions are one way and restart the target subagent. UNVERIFIED (2026-10-03): how a session resumes after a human takes over.
6. In the legacy builder, only the standard Escalation topic can route to service reps.

## Proactive Triggers

- No confidence-based escalation configured → Flag High. Loops likely.
- Context package is raw transcript dump → Flag Medium. Human agents drown in it.
- No deflection path when queues are empty → Flag High. Users stuck.
- Authorization-gated actions with no handoff → Flag Critical. Agent may act outside authority.
- Hand-back not designed when needed → Flag Medium.

## Output Artifacts

| Artifact | Description |
|---|---|
| Trigger → destination table | Per trigger, where to send |
| Context package schema | Fields and format |
| User message catalog | Per handoff type |

## Related Skills

- `agentforce/agent-topic-design` — subagent scope that informs scope-based handoffs.
- `agentforce/agentforce-guardrails` — guardrails that fire authorization handoffs.
- `admin/omni-channel-routing-setup` — destination queue design.
- `agentforce/agentforce-service-ai-setup` — service-agent integration.
- `agentforce/agentforce-agent-creation`: channel connection and activation, which must precede routing.
