# Examples — Agentforce Persona Design

## Example 1: Encoding Brand Voice for a Financial Services Agent

**Context:** A financial services company is deploying an Agentforce agent named "Aria" on their customer-facing web chat. Brand guidelines specify: empathetic, trustworthy, concise, no financial jargon, always acknowledge the customer's concern before offering a resolution.

**Problem:** The initial agent instructions were written as a list of rules: "Never use jargon. Always acknowledge concerns. Must be empathetic." The agent's responses were formulaic, inconsistent, and occasionally ignored the tone rules during complex queries. AI Assist flagged "always" and "must" as chain conflicts.

**Solution:**
Agent-level system instructions after revision:
```
You are Aria, a trusted financial services assistant for Acme Financial. You communicate with empathy and quiet confidence — you listen to the customer's concern before offering a solution, and you explain complex topics in plain language without technical jargon.

When a customer is frustrated or confused, acknowledge their experience directly before moving to resolution. If you cannot resolve the issue within your scope, offer a warm handoff to a human agent rather than ending the conversation.

Keep responses focused and concise — aim for 2-3 sentences unless a detailed explanation is genuinely needed.
```

**Why it works:** The revision uses voice adjectives ("empathy and quiet confidence", "plain language") that the LLM uses to calibrate tone rather than evaluating rule compliance. The behavioral guidance for edge cases (frustration, scope limits) is descriptive rather than prohibitive, reducing reasoning loop risk.

---

## Example 2: Multi-Persona Strategy for B2B and B2C Audiences

**Context:** A software company serves both enterprise IT admins (technical, formal) and end-users (non-technical, casual). They initially tried to encode both personas in one agent using conditional instructions: "If the user asks a technical question, be formal; otherwise be casual."

**Problem:** The single-agent approach was unreliable. The LLM could not consistently detect user type from the opening message, so the tone was inconsistent. Enterprise customers complained the agent was too casual; end-users found the technical tone confusing.

**Solution:**
1. Created two separate Agentforce agents:
   - **TechAdvisor** — agent-level instructions with formal, precise, technically fluent voice. Deployed to the admin console channel.
   - **HelpBot** — agent-level instructions with conversational, jargon-free, patient voice. Deployed to the end-user help portal.
2. Each agent's instructions encode the brand values common to both (trustworthy, responsive), with distinct tone adjectives per audience.
3. Channel routing determines which agent handles the conversation — no runtime persona switching.

**Why it works:** Persona in Agentforce is set at the agent level and applies uniformly for the agent's lifetime. Trying to switch personas mid-conversation based on detected user type is unreliable because the LLM cannot consistently infer audience type from early utterances. Separate agents with separate deployments per audience is the only reliable multi-persona architecture.

---

## Anti-Pattern: Encoding Persona Only in Topic Instructions

**What practitioners do:** Add tone and voice instructions to individual topic instructions (e.g., "Respond formally when discussing billing") rather than agent-level system instructions, assuming this is equivalent.

**What goes wrong:** Topic instructions only apply when the LLM routes to that specific topic. If the conversation matches a different topic, falls back to unhandled intent, or is in the escalation path, the persona instructions are absent. The agent's tone becomes inconsistent — formal during billing discussions, neutral or generic elsewhere.

**Correct approach:** Encode persona exclusively in agent-level system instructions. Topic instructions should focus on task scope, required actions, and response format for that topic — not tone or voice. The agent-level persona applies uniformly across all topics and fallback states.
