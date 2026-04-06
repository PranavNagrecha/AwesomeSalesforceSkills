---
name: agentforce-persona-design
description: "Use when defining or refining the tone, voice, and behavioral personality of an Agentforce agent: system instruction encoding, brand voice alignment, adaptive response formats, multi-persona strategies. NOT for agent topic design (use agent-topic-design) or testing methodology (use agent-testing-and-evaluation)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "how do I make my Agentforce agent sound more professional and empathetic"
  - "agent tone and voice configuration in Agentforce agent builder"
  - "how to write agent-level system instructions for persona and brand alignment"
  - "Agentforce agent gives inconsistent responses across conversations"
  - "how to test and validate the persona of an Agentforce agent"
tags:
  - agentforce
  - persona-design
  - agent-instructions
  - brand-voice
  - conversational-ai
inputs:
  - "Brand voice guidelines or style guide (tone adjectives, prohibited phrases)"
  - "Target audience and channel (web chat, Slack, API, mobile)"
  - "Existing agent-level system instructions if any"
outputs:
  - "Agent-level system instructions with tone and persona encoded"
  - "Conversation preview test plan for brand voice validation"
  - "Multi-persona strategy recommendation if multiple audiences are served"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Agentforce Persona Design

This skill activates when an Agentforce practitioner needs to define, encode, or refine the personality and tone of an Agentforce agent through system-level instructions. It covers persona instruction writing, brand voice alignment, AI Assist for instruction review, adaptive response format configuration, and multi-persona strategies using multiple distinct agents.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether persona design is at the agent level (system instructions) or topic level (topic instructions) — these are distinct and this skill covers the agent level only.
- Gather brand voice guidelines from the organization: adjective pairs (e.g., empathetic but concise, professional but approachable), prohibited phrases, and any existing style guides.
- Confirm the target channel(s) — adaptive response formats (Spring '26) allow different rendering decisions per channel, and a persona that works for web chat may need adjustment for Slack or API responses.

---

## Core Concepts

### Agent-Level System Instructions vs Topic Instructions

Agentforce has two instruction layers:
1. **Agent-level system instructions** — apply to every conversation regardless of which topic is active. This is where persona, tone, and brand voice live.
2. **Topic instructions** — apply only when the agent is handling that specific topic. These define scope and behavior for a particular subject, not the overall personality.

Persona must be encoded in agent-level instructions. Topic instructions should not repeat or override persona — they focus on task execution.

### Tone Encoding via Descriptive Voice Adjectives

Tone in Agentforce is encoded through descriptive adjectives in the opening paragraph of the agent-level instructions. The LLM uses these adjectives to calibrate response style. Effective patterns:
- "You are a helpful, empathetic customer service assistant. Your responses are concise and professional."
- "You communicate in a warm, conversational tone. You avoid jargon and always confirm the customer's issue before offering a solution."

Avoid encoding tone via lists of rules with modal verbs (must/never/always) — these cause reasoning loops where the LLM spends inference budget evaluating rule compliance rather than generating a helpful response.

### AI Assist for Instruction Review

Agent Builder in Salesforce includes an AI Assist feature that analyzes agent-level instructions and flags conflicting, ambiguous, or overly prescriptive guidance. Use AI Assist after drafting instructions to identify:
- Contradicting directives (e.g., "always be brief" and "always explain your reasoning in detail")
- Ambiguous modal verb chains (must/never/always sequences)
- Instructions that overlap with topic-level configuration

### Adaptive Response Formats (Spring '26)

Available from Spring '26, adaptive response formats allow the agent's responses to be rendered differently depending on the channel. Supported output formats include plain text (for API/voice), Markdown (for web chat and Slack), and structured JSON (for programmatic channel rendering). This is configured at the channel level in agent deployment settings, not in the system instructions themselves. The persona instruction should not hardcode formatting syntax — let the channel configuration handle rendering.

### Multi-Persona Strategy

Multi-persona means deploying multiple distinct Agentforce agents, each with its own system instructions and brand voice, not a single agent with mode-switching behavior. A single agent cannot switch personas mid-conversation based on user input — the persona is set at conversation start from the agent's instructions. If different audiences need different personas (e.g., enterprise customers vs. consumer end-users), deploy separate agents per audience.

---

## Common Patterns

### Brand Voice Encoding Pattern

**When to use:** Initial persona design for a new agent or when an existing agent's tone is inconsistent with brand standards.

**How it works:**
1. Gather 3–5 voice adjective pairs from the brand style guide (e.g., "empathetic yet efficient", "authoritative but approachable").
2. Write the opening paragraph of agent-level instructions as a role declaration with voice adjectives:
   ```
   You are Aria, a customer service agent for Acme Financial Services. You communicate with empathy and confidence. Your responses are direct and professional — you avoid jargon, confirm the customer's concern before acting, and always end with a clear next step.
   ```
3. Add a brief behavioral guideline for tone in edge cases (confusion, escalation):
   ```
   When a customer is frustrated, acknowledge their experience before providing a solution. Never minimize the issue. If you cannot resolve the issue, proactively offer to connect them with a human agent.
   ```
4. Run AI Assist to check for conflicts and ambiguous instructions.
5. Test in conversation preview with 5–10 scripted utterances designed to probe tone at the edges (frustrated user, complex request, off-topic question).

**Why not topic instructions:** Persona encoded in topic instructions applies only when that topic is active. If the LLM selects a different topic or falls back to the default, the persona may disappear.

### Conversation Preview Test Plan

**When to use:** Validating persona after instructions are written, or after a brand voice change.

**How it works:** Design a set of scripted utterances that probe the persona at its edges:
- Friendly/routine: "Can you help me check my order status?" — expected: warm, concise, helpful
- Frustrated user: "This is the third time I've had this problem, fix it now!" — expected: empathetic acknowledgment before resolution
- Off-topic: "What's the weather like?" — expected: polite redirect consistent with persona
- Complex request: "Explain your data privacy policy in detail" — expected: professional, no jargon, offers to escalate if needed

Run each in conversation preview and score against the brand voice adjectives. A persona is working when the adjectives are observable in the response.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single brand voice for all audiences | One agent with agent-level persona instructions | Simpler to maintain; consistent identity |
| Different audiences need different tones (B2B vs B2C) | Separate agents per audience segment | Single agent cannot switch persona mid-conversation |
| Tone is inconsistent across conversations | Audit agent-level instructions for contradictions using AI Assist | Contradictory instructions cause non-deterministic tone |
| Channel requires different response format (Slack vs API) | Configure adaptive response formats at channel level (Spring '26) | Do not hardcode markdown/JSON in persona instructions |
| Agent is using excessive must/never/always chains | Rewrite as positive behavioral statements with adjectives | Modal verb chains cause reasoning loops |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Collect brand voice guidelines: tone adjective pairs, prohibited phrases, sample approved content in brand voice.
2. Draft agent-level system instructions starting with a role declaration paragraph that embeds 3–5 voice adjectives. Keep the instruction block under 2000 characters — shorter is more reliable.
3. Run AI Assist in Agent Builder to check for conflicting or ambiguous instructions. Fix all flagged items.
4. Test in conversation preview with a structured test plan: 5+ utterances covering routine, frustrated, off-topic, and complex request scenarios.
5. Score each response against the target voice adjectives. Iterate on wording until all scenarios are consistent.
6. If multiple audiences need different personas, create a separate agent per audience and document which agent handles which audience in the deployment configuration.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Persona is in agent-level instructions, not topic instructions
- [ ] Opening instruction paragraph contains role declaration and 3–5 tone adjectives
- [ ] No contradictory directives (e.g., "be brief" AND "explain everything in detail")
- [ ] No long must/never/always chains — rewritten as positive behavioral statements
- [ ] AI Assist has been run and all flagged issues resolved
- [ ] Conversation preview test completed with at least 5 scripted utterances including a frustrated user scenario
- [ ] Adaptive response formats configured at channel level if needed (Spring '26+)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Modal verb chains cause reasoning loops** — Long sequences of `must`/`never`/`always` instructions in agent-level system instructions cause the LLM to spend inference tokens evaluating rule compliance instead of generating a helpful response. The result is slower, more generic, and less on-brand responses. Replace rule lists with behavioral descriptions using voice adjectives.
2. **Persona in topic instructions only applies when that topic is active** — If an instruction like "always respond formally" is placed in a topic's instructions rather than the agent-level instructions, it only applies when the LLM routes to that topic. Any fallback, escalation, or unmatched intent will bypass the persona instruction.
3. **AI Assist reviews instructions but does not enforce them at runtime** — AI Assist is a static analysis tool that runs in Agent Builder. It does not enforce instructions at conversation runtime. Conflicting instructions that AI Assist flags may still appear to work in simple test cases but fail at the edges under varied user inputs.
4. **A single agent cannot switch personas based on user input** — Attempting to instruct the agent to "behave formally with enterprise users and casually with consumers" in a single instruction set leads to inconsistent behavior. The LLM cannot reliably detect user type mid-conversation and switch personas.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Agent-level system instructions | Drafted persona text ready for paste into Agent Builder |
| Conversation preview test plan | Scripted utterances with expected tone outcomes for QA |
| Multi-persona agent roster | If multiple audiences are served, a list of agents with their persona profiles |

---

## Related Skills

- agent-topic-design — designing topic scope and instructions for task execution (separate from persona)
- agent-testing-and-evaluation — structured testing methodology for agent conversations
- agentforce-agent-creation — end-to-end agent setup including channel assignment and deployment
