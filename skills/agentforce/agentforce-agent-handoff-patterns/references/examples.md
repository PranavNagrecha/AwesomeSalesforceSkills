# Agentforce Agent Handoff — Examples

## Example 1: Structured Escalation With Summary

**Context:** Service agent cannot resolve a refund request above the agent's authority.

**Procedure:**
- Agent runs a custom action that creates a Case with a structured summary (intent, what was tried, requested refund amount, policy conflict reason). The full Apex action and test are in `references/metadata-examples.md`.
- The conversation escalates through the Escalation topic's Omni-Channel flow (legacy builder) or `@utils.escalate` (Agent Script) to the `Tier2_Refunds` queue.
- Agent says: "I'm connecting you to a specialist. They'll see a summary of what we've discussed so you don't need to repeat yourself. Estimated wait: 3 minutes."

The case description the rep sees:

```text
Customer intent: Refund of 450 dollars for a damaged blender (order 00000102)
What was tried: Looked up the order; confirmed delivery; refund exceeds the 200 dollar agent limit
Handoff reason: POLICY_LIMIT
Transcript: linked on the messaging session record
```

**Why it works:** Human agent opens the case, sees summary, continues without "tell me the whole story."

---

## Example 2: Confidence-Triggered Escalation

Agent attempts to resolve a password reset twice; both fail (user enters unknown email). On third attempt, a confidence-triggered escalation fires: "I'm having trouble with this. Let me connect you with support."

The attempt counter lives in a variable, and the escalate tool is offered only when the counter reaches the limit. Agent Script excerpt (not YAML):

```text
reasoning:
    actions:
        escalate_to_human: @utils.escalate
            description: "Call this when the customer still cannot reset the password after two attempts"
            available when @variables.reset_attempts >= 2
```

The clause after `available when` must be a conditional expression built from supported operators, and `>=` is one of them (Agentforce Developer Guide, Tools (Reasoning Actions) and Supported Operators).

Avoids the infinite-retry loop users hate.

---

## Example 3: Deflection-With-Recommendation

Out-of-hours, queue is empty, user asks a niche question. Agent says: "I can't connect you to a specialist right now. Please visit [link] or I can schedule a callback for tomorrow morning."

---

## Anti-Pattern: Raw Transcript In Case Description

A team packaged the full verbatim conversation (sometimes 30+ turns) into the Case description. Human agents dreaded opening these cases. Fix: send a link to the transcript, and a structured summary.
