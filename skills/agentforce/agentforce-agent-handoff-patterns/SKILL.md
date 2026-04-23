---
name: agentforce-agent-handoff-patterns
description: "Use when designing how an Agentforce agent transfers the conversation to a human agent (Omni-Channel), to another bot/agent, or to an alternate workflow — including context package, deflection, escalation triggers, and user messaging. Triggers: 'agent to human handoff', 'agentforce escalate to omni channel', 'agent to agent handoff', 'transfer conversation with context', 'agent deflection fallback'. NOT for topic selector design (see agent-topic-design)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Agentforce Agent Handoff Patterns

Most agent failures are handoff failures. The agent knew it was stuck, did not have a clean way to transfer the conversation, and either looped, hallucinated, or dumped the user into a cold queue without context. Good handoff design treats the transfer as a first-class capability with its own triggers, its own context schema, and its own messaging — not as "throw an error and let Omni-Channel figure it out."

Three kinds of handoff matter: agent-to-human (Omni-Channel), agent-to-agent (swap persona, specialization, or domain), and agent-to-workflow (spawn a case, route to a Flow, schedule a callback). Each has different mechanics but shares the same design skeleton: trigger → context package → user message → receiver acknowledgment → (optional) hand-back.

---

## Before Starting

- List the handoff triggers expected for this agent (policy, confidence, scope, authorization, user request).
- List destinations and what each needs to take the conversation from here.
- Confirm Omni-Channel queue structure and presence model.
- Confirm whether hand-back (returning to the agent after human resolution) is a requirement.

## Core Concepts

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

- **Omni-Channel queue** — human agent, with pre-populated case or conversation.
- **Another Agentforce agent** — specialized persona or different domain.
- **Workflow** — async case, Flow, Queue, scheduled callback.
- **No handoff (refuse + recommend)** — sometimes the right answer is "I can't help; here's how."

### User Messaging

Every handoff needs an explicit user message that says what is happening and what to expect. "Let me connect you with an agent" is better than silence. Predicted wait time (if known) is better than vague.

### Hand-Back

If the agent will resume after human resolution (common in hybrid service models), the hand-back protocol must preserve or summarize what the human did.

---

## Common Patterns

### Pattern 1: Structured Escalation To Omni-Channel

On trigger: create a case with a structured description, route to the queue, deliver a friendly transfer message, end the agent session. The case captures the context package in a standard format.

### Pattern 2: Warm Agent-To-Agent Handoff

One agent hands to another without losing conversation continuity. The receiving agent reads a summary (not the verbatim history) to avoid token bloat and topic confusion.

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

## Well-Architected Pillar Mapping

- **User Experience** — explicit transfers and expected-wait messaging reduce frustration.
- **Reliability** — loops and dead ends are the top agent failure modes; handoff design prevents them.
- **Operational Excellence** — structured context packages reduce human-agent ramp time.

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
5. Implement the transfer mechanism (case creation, queue route, workflow spawn).
6. Verify hand-back works if required.

---

## Salesforce-Specific Gotchas

1. Omni-Channel routing honors agent presence; if no one is available, the conversation can sit indefinitely unless you add fallbacks.
2. Case routing by owner vs queue has different audit trails.
3. Context dumped as raw text into a case description is unsearchable and bloats storage.
4. Agent-to-agent handoff resets topic context — the new agent does not see the previous topic's instructions.
5. Hand-back requires the original agent session to still be alive, or you need an explicit resumption mechanism.

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

- `agentforce/agent-topic-design` — topic scope that informs scope-based handoffs.
- `agentforce/agentforce-guardrails` — guardrails that fire authorization handoffs.
- `admin/omni-channel-routing-design` — destination queue design.
- `agentforce/agentforce-service-ai-setup` — service-agent integration.
