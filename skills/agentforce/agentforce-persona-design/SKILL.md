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
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agentforce Persona Design

This skill activates when an Agentforce practitioner needs to define, encode, or refine the personality and tone of an Agentforce agent through system-level instructions. It covers persona instruction writing, brand voice alignment, AI Assist for instruction review, adaptive response format configuration, and multi-persona strategies using multiple distinct agents.

Persona is NOT prompt-engineering trivia — it's the single biggest driver of whether users trust the agent. An agent with the right tool set and the wrong persona feels robotic or presumptuous; users disengage. An agent with the right persona and weaker tooling still feels helpful because users forgive capability gaps when the interaction feels human-reasonable.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Identify whether persona design is at the agent level (system instructions) or topic level (topic instructions) — these are distinct and this skill covers the agent level only.
- Gather brand voice guidelines: adjective pairs (e.g., empathetic but concise, professional but approachable), prohibited phrases, any existing style guides.
- Confirm the target channel(s) — adaptive response formats (Spring '26) allow different rendering decisions per channel, and a persona that works for web chat may need adjustment for Slack or API responses.
- Who is the primary user? (Employee? Customer? Partner? Guest visitor?)
- What are the most common conversation types? (Routine request? Complaint? Information query? Task handoff?)
- What are the brand's "red-line" behaviors — things the agent MUST NOT do (over-promising, making legal claims, emotional mirroring beyond bounds)?

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

**Adjective-based persona pattern:**
```
You are <NAME>, a <ROLE> for <ORGANIZATION>. You communicate with
<ADJECTIVE1> and <ADJECTIVE2>. Your responses are <ADJECTIVE3> and
<ADJECTIVE4> — you avoid <PROHIBITED_PATTERN>, and you always
<SIGNATURE_BEHAVIOR>.
```

Concrete instantiation:
```
You are Aria, a customer service agent for Acme Financial Services.
You communicate with empathy and confidence. Your responses are direct
and professional — you avoid jargon, and you always confirm the
customer's concern before acting.
```

### AI Assist for Instruction Review

Agent Builder in Salesforce includes an AI Assist feature that analyzes agent-level instructions and flags conflicting, ambiguous, or overly prescriptive guidance. Use AI Assist after drafting instructions to identify:
- Contradicting directives (e.g., "always be brief" and "always explain your reasoning in detail")
- Ambiguous modal verb chains (must/never/always sequences)
- Instructions that overlap with topic-level configuration

### Adaptive Response Formats (Spring '26)

Available from Spring '26, adaptive response formats allow the agent's responses to be rendered differently depending on the channel. Supported output formats include plain text (for API/voice), Markdown (for web chat and Slack), and structured JSON (for programmatic channel rendering). This is configured at the channel level in agent deployment settings, not in the system instructions themselves. The persona instruction should not hardcode formatting syntax — let the channel configuration handle rendering.

### Multi-Persona Strategy

Multi-persona means deploying multiple distinct Agentforce agents, each with its own system instructions and brand voice, not a single agent with mode-switching behavior. A single agent cannot switch personas mid-conversation based on user input — the persona is set at conversation start from the agent's instructions. If different audiences need different personas (e.g., enterprise customers vs. consumer end-users), deploy separate agents per audience.

### Persona Drift Risk

Persona instructions degrade over context length. In long conversations, the LLM's attention to the system instructions weakens and the persona can drift — warm at turn 1, brusque at turn 20. Signals of drift:
- Response length grows over the conversation (persona may specify "concise" but LLM lengthens).
- Tone shifts toward default LLM patterns ("I'd be happy to...").
- Signature phrases disappear.

Mitigations: shorter conversations (hand off sooner to human), periodic persona reinforcement in topic instructions (only if reinforcement aligns — don't contradict agent-level), system-instruction placement that the model weights more heavily (opening paragraph is highest-priority).

---

## Common Patterns

### Pattern 1: Brand Voice Encoding

**When to use:** Initial persona design for a new agent or when an existing agent's tone is inconsistent with brand standards.

**Structure:**
1. Gather 3–5 voice adjective pairs from the brand style guide (e.g., "empathetic yet efficient", "authoritative but approachable").
2. Write the opening paragraph of agent-level instructions as a role declaration with voice adjectives.
3. Add a brief behavioral guideline for tone in edge cases (confusion, escalation, off-topic).
4. Run AI Assist to check for conflicts and ambiguous instructions.
5. Test in conversation preview with 5–10 scripted utterances designed to probe tone at the edges.

**Why not topic instructions:** Persona encoded in topic instructions applies only when that topic is active. If the LLM selects a different topic or falls back to the default, the persona may disappear.

### Pattern 2: Conversation Preview Test Plan

**When to use:** Validating persona after instructions are written, or after a brand voice change.

**Structure:** Design a set of scripted utterances that probe the persona at its edges:
- Friendly/routine: "Can you help me check my order status?" — expected: warm, concise, helpful.
- Frustrated user: "This is the third time I've had this problem, fix it now!" — expected: empathetic acknowledgment before resolution.
- Off-topic: "What's the weather like?" — expected: polite redirect consistent with persona.
- Complex request: "Explain your data privacy policy in detail" — expected: professional, no jargon, offers to escalate if needed.
- Confusion: "I don't understand what you're asking" — expected: patient re-explanation, not just a restatement.

Run each in conversation preview and score against the brand voice adjectives. A persona is working when the adjectives are observable in the response.

### Pattern 3: Multi-Persona Agent Family

**When to use:** Different audiences need fundamentally different personas (B2B vs B2C, internal vs external).

**Structure:**
1. Build a SEPARATE agent per audience.
2. Each agent has its own system instructions + persona + topic set.
3. Route to the appropriate agent at the conversation-entry point (based on user attributes, channel, or URL parameter).
4. Agents may SHARE some topic-level logic (via subflows or invocables) but NOT persona.

### Pattern 4: Persona Reinforcement for Long Conversations

**When to use:** Conversations routinely exceed 10+ turns and drift is observed.

**Structure:** Brief persona-reinforcement snippet in each topic's instructions that ALIGNS with (does not override) agent-level persona. Example: "Maintain a warm, concise tone throughout." One sentence — not a second full persona block.

### Pattern 5: Prohibited-Pattern Explicit List

**When to use:** The brand has strong "never say" or "never promise" constraints.

**Structure:** Explicit negative-phrase list in the agent-level instructions:
```
You never:
- Promise specific financial outcomes
- Guarantee delivery times without confirming logistics data
- Apologize for issues outside the company's control as if they were our fault
```

Kept SHORT — long prohibition lists are modal-verb chains and cause reasoning loops.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single brand voice for all audiences | One agent with agent-level persona instructions | Simpler to maintain; consistent identity |
| Different audiences need different tones (B2B vs B2C) | Separate agents per audience segment (Pattern 3) | Single agent cannot switch persona mid-conversation |
| Tone is inconsistent across conversations | Audit agent-level instructions for contradictions using AI Assist | Contradictory instructions cause non-deterministic tone |
| Channel requires different response format (Slack vs API) | Configure adaptive response formats at channel level (Spring '26) | Do not hardcode markdown/JSON in persona instructions |
| Agent uses excessive must/never/always chains | Rewrite as positive behavioral statements with adjectives (Pattern 1) | Modal verb chains cause reasoning loops |
| Long-conversation drift observed | Add persona reinforcement in topic instructions (Pattern 4) | System-instruction attention weakens over context |
| Brand has strong prohibitions | Explicit short list (Pattern 5) | Concrete > vague |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Collect brand voice guidelines: tone adjective pairs, prohibited phrases, sample approved content in brand voice.
2. Draft agent-level system instructions starting with a role declaration paragraph that embeds 3–5 voice adjectives. Keep the instruction block under 2000 characters — shorter is more reliable.
3. Run AI Assist in Agent Builder to check for conflicting or ambiguous instructions. Fix all flagged items.
4. Test in conversation preview with a structured test plan: 5+ utterances covering routine, frustrated, off-topic, complex request, and confusion scenarios.
5. Score each response against the target voice adjectives. Iterate on wording until all scenarios are consistent.
6. If multiple audiences need different personas, create a separate agent per audience and document which agent handles which audience in the deployment configuration.
7. Monitor production conversations for persona drift; tune topic-level reinforcement if long-conversation drift is observed.

---

## Review Checklist

- [ ] Persona is in agent-level instructions, not topic instructions.
- [ ] Opening instruction paragraph contains role declaration and 3–5 tone adjectives.
- [ ] No contradictory directives (e.g., "be brief" AND "explain everything in detail").
- [ ] No long must/never/always chains — rewritten as positive behavioral statements.
- [ ] AI Assist has been run and all flagged issues resolved.
- [ ] Conversation preview test completed with at least 5 scripted utterances including a frustrated user scenario.
- [ ] Adaptive response formats configured at channel level if needed (Spring '26+).
- [ ] Multi-persona requirements routed to separate agents (not one agent with conditional instructions).
- [ ] Prohibited-pattern list (if any) is short and specific.
- [ ] Long-conversation drift mitigation in place if applicable.

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — collect brand voice guidelines, audience, channels
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **Modal verb chains cause reasoning loops** — Long sequences of `must`/`never`/`always` instructions cause the LLM to spend inference tokens evaluating rule compliance instead of generating a helpful response.
2. **Persona in topic instructions only applies when that topic is active** — If placed in a topic's instructions rather than the agent-level instructions, it only applies when the LLM routes to that topic.
3. **AI Assist reviews instructions but does not enforce them at runtime** — AI Assist is a static analysis tool; conflicting instructions it flags may still appear to work in simple tests but fail at the edges.
4. **A single agent cannot switch personas based on user input** — Attempting conditional persona switching leads to inconsistent behavior.
5. **Persona drift over long conversations** — LLM's attention to system instructions weakens over context length; mitigation via topic-level reinforcement.
6. **Instruction length past 2000 characters degrades reliability** — the LLM's ability to hold the full persona diminishes with length; prefer tight.
7. **Tone adjectives that conflict with the LLM's training produce uncanny output** — e.g., asking an LLM trained on helpful content to be "aloof" usually produces a robotic version of helpful, not aloof.
8. **Channel-specific formatting instructions in the persona breaks other channels** — e.g., "respond in markdown" breaks API consumers; use adaptive response formats instead.
9. **Persona instructions don't carry across agent deployments** — cloning an agent doesn't auto-copy; deploy persona as part of a versioned metadata bundle.
10. **Testing only in conversation preview misses channel-specific behavior** — test in the actual channel (web chat, Slack, API) before launch.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Persona instructions > 2000 characters** → Flag as High. Reliability risk.
- **Modal verb chains (3+ `must/never/always` in a row)** → Flag as High. Reasoning loop risk.
- **Persona in topic instructions instead of agent-level** → Flag as Critical. Coverage gap.
- **No AI Assist run logged** → Flag as Medium. Static-analysis gap.
- **Single agent trying to serve B2B + B2C with conditional instructions** → Flag as High. Multi-persona needed.
- **No conversation-preview test plan** → Flag as High. Persona-validation gap.
- **Formatting instructions hardcoded in persona (Markdown tables, JSON)** → Flag as High. Channel-portability break.
- **Persona drift observed in production conversations > 10 turns** → Flag as Medium. Add reinforcement pattern (Pattern 4).

## Output Artifacts

| Artifact | Description |
|---|---|
| Agent-level system instructions | Drafted persona text ready for paste into Agent Builder |
| Conversation preview test plan | Scripted utterances with expected tone outcomes for QA |
| Multi-persona agent roster | If multiple audiences served, list of agents with persona profiles |
| AI Assist review log | Documented issues flagged and resolution |
| Persona reinforcement snippets | Topic-level additions (Pattern 4) for long-conversation drift |

---

## Related Skills

- **agentforce/agent-topic-design** — designing topic scope and instructions for task execution (separate from persona).
- **agentforce/agent-testing-and-evaluation** — structured testing methodology for agent conversations.
- **agentforce/agentforce-agent-creation** — end-to-end agent setup including channel assignment and deployment.
- **agentforce/agent-actions** — the action contract that persona-driven conversations invoke.
- **agentforce/einstein-trust-layer** — Trust-layer settings that interact with persona (PII masking, citation).
- **agentforce/agentforce-observability** — monitoring persona drift in production.
