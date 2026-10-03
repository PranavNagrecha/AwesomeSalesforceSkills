---
name: agentforce-persona-design
description: "Use when defining or refining the tone, voice, and behavioral personality of an Agentforce agent: system instruction encoding, brand voice alignment, adaptive response formats, multi-persona strategies. NOT for writing the actual conversational copy — utterances, fallback messages, escalation phrasing — use admin/agent-conversation-design. NOT for topic scope design — use agentforce/agent-topic-design."
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
  - "set the tone of my Agentforce agent to formal"
  - "write the system instructions and welcome message for my agent"
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
version: 2.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agentforce Persona Design

This skill activates when an Agentforce practitioner needs to define, encode, or refine the personality and tone of an Agentforce agent through system-level instructions. It covers persona instruction writing, brand voice alignment, AI Assist for instruction review, adaptive response format configuration, and multi-persona strategies using multiple distinct agents.

Persona is NOT prompt-engineering trivia — it's the single biggest driver of whether users trust the agent. An agent with the right tool set and the wrong persona feels robotic or presumptuous; users disengage. An agent with the right persona and weaker tooling still feels helpful because users forgive capability gaps when the interaction feels human-reasonable.

> **Terminology.** Agentforce *subagents* were called **topics** before April 2026.
> This skill leads with *subagent* because that is the current product term. The
> rename changed nothing about behaviour, and metadata and API names — plus the
> search keywords readers arrive with — still say *topic*.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Identify whether persona design is at the agent level (system instructions) or subagent level (subagent instructions) — these are distinct and this skill covers the agent level only.
- Gather brand voice guidelines: adjective pairs (e.g., empathetic but concise, professional but approachable), prohibited phrases, any existing style guides.
- Confirm the target channel(s) — adaptive response formats (Spring '26) allow different rendering decisions per channel, and a persona that works for web chat may need adjustment for Slack or API responses.
- Who is the primary user? (Employee? Customer? Partner? Guest visitor?)
- What are the most common conversation types? (Routine request? Complaint? Information query? Task handoff?)
- What are the brand's "red-line" behaviors — things the agent MUST NOT do (over-promising, making legal claims, emotional mirroring beyond bounds)?

---

## Questions to Ask Before Configuring

Ask these before writing a word of persona text. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Formal, neutral or casual?" | Tone is a native setting with a Casual default, and it does not reach actions with their own tone (Gotcha 5) | The tone setting, plus the actions whose tone must be tuned separately | The voice is set where the platform reads it, not only in prose |
| "Which agent type is this, and does it have system messages?" | Only Agentforce (Default) and Service Agent have system messages; Agent Script requires welcome and error (Gotcha 8) | The list of system messages to write | No copy written for a surface that does not exist |
| "How must the agent introduce itself, and what consent wording is required?" | The welcome is limited to 800 characters and should disclose that the agent is automated (Gotcha 6) | An approved welcome and error message | Transparent first contact that legal has signed off |
| "Which languages and locales must the voice work in?" | System messages are not translated and locales can fall back to variants (Gotchas 7, 12) | Locale list and translation owners | A consistent voice per language, tested per locale |
| "What must the agent never do, and is any of it a business rule?" | Absolutes are followed strictly, and policy belongs in actions (Gotchas 1, 9) | A short red-line list, with policy items moved to actions | Fewer conflicting rules and policies that hold every time |
| "How will we prove the persona holds at the edges?" | Authoring checks do not enforce runtime behaviour (Gotcha 3) | A regression set of frustrated, off-topic, advice-seeking and confused utterances | A persona that is tested in CI, not judged by feel |

## Core Concepts

### Where Persona Lives in the Platform

Persona has native homes, not only free text (details in `references/metadata-examples.md`):

- **Tone setting.** Formal, Neutral or Casual in Language Settings; the default is Casual. Stored as `BotVersion.toneType`.
- **Agent-level instructions.** Agent Script `system.instructions`, the general instructions for the whole agent.
- **System messages.** Welcome and error messages (required in Agent Script), 800-character welcome limit.
- **Role, company, description.** Agent Script `config` fields that give the reasoning engine context.

### Agent-Level System Instructions vs Subagent Instructions

Agentforce has two instruction layers:
1. **Agent-level system instructions** — apply to every conversation regardless of which subagent is active. This is where persona, tone, and brand voice live.
2. **Subagent instructions** — apply only when the agent is handling that specific subagent. These define scope and behavior for a particular subject, not the overall personality.

Persona must be encoded in agent-level instructions. Subagent instructions should not repeat or override persona — they focus on task execution.

### Tone Encoding via Descriptive Voice Adjectives

Tone in Agentforce is encoded through descriptive adjectives in the opening paragraph of the agent-level instructions. The LLM uses these adjectives to calibrate response style. Effective patterns:
- "You are a helpful, empathetic customer service assistant. Your responses are concise and professional."
- "You communicate in a warm, conversational tone. You avoid jargon and always confirm the customer's issue before offering a solution."

Avoid encoding tone via long lists of must/never/always rules. The Generative AI guide says agents follow strong language like "always" and "never" strictly, so use absolutes only when you mean them, and says contradicting instructions degrade performance. UNVERIFIED (2026-10-03): the earlier claim that such lists "cause reasoning loops"; no official source says so.

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

UNVERIFIED (2026-10-03): this section rests on a Salesforce Developers blog post; none of the official guides read for this revision describe AI Assist. Agent Builder in Salesforce includes an AI Assist feature that analyzes agent-level instructions and flags conflicting, ambiguous, or overly prescriptive guidance. Use AI Assist after drafting instructions to identify:
- Contradicting directives (e.g., "always be brief" and "always explain your reasoning in detail")
- Ambiguous modal verb chains (must/never/always sequences)
- Instructions that overlap with subagent-level configuration

### Adaptive Response Formats (Spring '26)

UNVERIFIED (2026-10-03): this section rests on a Salesforce Developers blog post and was not found in the official guides read for this revision. Available from Spring '26, adaptive response formats allow the agent's responses to be rendered differently depending on the channel. Supported output formats include plain text (for API/voice), Markdown (for web chat and Slack), and structured JSON (for programmatic channel rendering). This is configured at the channel level in agent deployment settings, not in the system instructions themselves. The persona instruction should not hardcode formatting syntax, let the channel configuration handle rendering.

### Multi-Persona Strategy

Multi-persona means deploying multiple distinct Agentforce agents, each with its own system instructions and brand voice, not a single agent with mode-switching behavior. Treat persona as fixed per agent. UNVERIFIED (2026-10-03): the earlier claim that a single agent cannot switch personas; Agent Script reasoning instructions can branch on variables, so conditional wording is possible, but separate agents remain the predictable design. If different audiences need different personas (e.g., enterprise customers vs. consumer end-users), deploy separate agents per audience.

### Persona Drift Risk

UNVERIFIED (2026-10-03): the drift mechanism described here is not documented. What is documented is that Agentforce (Default) uses messages from up to the most recent six turns as context (Generative AI guide, Agents Limits). Persona instructions can appear to degrade over context length, warm at turn 1, brusque at turn 20. Signals of drift:
- Response length grows over the conversation (persona may specify "concise" but LLM lengthens).
- Tone shifts toward default LLM patterns ("I'd be happy to...").
- Signature phrases disappear.

Mitigations: shorter conversations (hand off sooner to human), periodic persona reinforcement in subagent instructions (only if reinforcement aligns; never contradict agent-level), and preferences stored in variables. The guide notes that the LLM does not use the visual order of topic instructions to make decisions, so do not rely on position for priority.

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

**Why not subagent instructions:** Persona encoded in subagent instructions applies only when that subagent is active. If the LLM selects a different subagent or falls back to the default, the persona may disappear.

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
2. Each agent has its own system instructions + persona + subagent set.
3. Route to the appropriate agent at the conversation-entry point (based on user attributes, channel, or URL parameter).
4. Agents may SHARE some subagent-level logic (via subflows or invocables) but NOT persona.

### Pattern 4: Persona Reinforcement for Long Conversations

**When to use:** Conversations routinely exceed 10+ turns and drift is observed.

**Structure:** Brief persona-reinforcement snippet in each subagent's instructions that ALIGNS with (does not override) agent-level persona. Example: "Maintain a warm, concise tone throughout." One sentence — not a second full persona block.

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
| Channel requires different response format (Slack vs API) | Keep formatting out of the persona; test per channel. UNVERIFIED (2026-10-03): channel-level adaptive response formats | Do not hardcode markdown/JSON in persona instructions |
| Agent uses excessive must/never/always chains | Rewrite as positive behavioral statements with adjectives (Pattern 1) | Absolutes are followed strictly and conflicting ones degrade performance |
| Long-conversation drift observed | Add persona reinforcement in subagent instructions (Pattern 4) | System-instruction attention weakens over context |
| Brand has strong prohibitions | Explicit short list (Pattern 5) | Concrete > vague |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Collect brand voice guidelines: tone adjective pairs, prohibited phrases, sample approved content in brand voice.
2. Set the native tone (Formal, Neutral or Casual) and write the system messages: a welcome under 800 characters that introduces the agent as automated, and an error message. Then draft agent-level instructions (Agent Script `system.instructions`) starting with a role declaration that embeds 3 to 5 voice adjectives. Keep the block short; the guide says to start with minimal instructions. UNVERIFIED (2026-10-03): the earlier 2,000-character threshold.
3. Run AI Assist in Agent Builder to check for conflicting or ambiguous instructions. Fix all flagged items.
4. Test in conversation preview with a structured test plan: 5+ utterances covering routine, frustrated, off-topic, complex request, and confusion scenarios. Turn the plan into an `AiEvaluationDefinition` (`references/metadata-examples.md`, Example 4) and lint it with the eval-harness checker so CI repeats it.
5. Score each response against the target voice adjectives. Iterate on wording until all scenarios are consistent.
6. If multiple audiences need different personas, create a separate agent per audience and document which agent handles which audience in the deployment configuration.
7. Monitor production conversations for persona drift; tune subagent-level reinforcement if long-conversation drift is observed.

---

## Review Checklist

- [ ] Persona is in agent-level instructions, not subagent instructions.
- [ ] Opening instruction paragraph contains role declaration and 3–5 tone adjectives.
- [ ] No contradictory directives (e.g., "be brief" AND "explain everything in detail").
- [ ] No long must/never/always chains — rewritten as positive behavioral statements.
- [ ] AI Assist has been run and all flagged issues resolved.
- [ ] Conversation preview test completed with at least 5 scripted utterances including a frustrated user scenario.
- [ ] Formatting kept out of the persona and checked in each real channel (UNVERIFIED 2026-10-03: the earlier "adaptive response formats" feature rests on a blog source only).
- [ ] Tone setting matches the brand (not left at the Casual default by accident).
- [ ] Welcome message under 800 characters and discloses that the agent is automated.
- [ ] Multi-persona requirements routed to separate agents (not one agent with conditional instructions).
- [ ] Prohibited-pattern list (if any) is short and specific.
- [ ] Long-conversation drift mitigation in place if applicable.

---

## Salesforce-Specific Gotchas

1. **Absolutes are followed strictly**: the guide says agents strictly follow "always" and "never", so use them only when meant; conflicting absolutes degrade performance. UNVERIFIED (2026-10-03): the earlier "reasoning loops" mechanism.
2. **Persona in subagent instructions only applies when that subagent is active** — If placed in a subagent's instructions rather than the agent-level instructions, it only applies when the LLM routes to that subagent.
3. **AI Assist reviews instructions but does not enforce them at runtime**: UNVERIFIED (2026-10-03): AI Assist appears only in a blog source; whatever review tool you use, runtime behaviour needs runtime tests.
4. **Conditional persona switching is unpredictable**: separate agents per audience are the predictable design. UNVERIFIED (2026-10-03): the earlier absolute claim that a single agent cannot switch personas.
5. **Long conversations see only recent turns**: Agentforce (Default) uses up to the six most recent turns as context; store preferences in variables. UNVERIFIED (2026-10-03): the earlier attention-decay explanation.
6. **Start with minimal instructions**: the guide recommends the fewest instructions necessary, added one at a time. UNVERIFIED (2026-10-03): the earlier 2,000-character threshold.
7. **Tone adjectives that conflict with the LLM's training produce uncanny output** — e.g., asking an LLM trained on helpful content to be "aloof" usually produces a robotic version of helpful, not aloof.
8. **Channel-specific formatting instructions in the persona break other channels**: e.g., "respond in markdown" breaks API consumers; keep formatting out of the persona and test each channel.
9. **Persona instructions don't carry across agent deployments** — cloning an agent doesn't auto-copy; deploy persona as part of a versioned metadata bundle.
10. **Testing only in conversation preview misses channel-specific behavior** — test in the actual channel (web chat, Slack, API) before launch.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Persona instructions far longer than the task needs** → Flag as Medium. The guide recommends minimal instructions.
- **Many `must/never/always` directives, or two that conflict** → Flag as High. Absolutes are followed strictly; conflicts degrade performance.
- **Tone setting left at the Casual default while the brand is formal** → Flag as High.
- **Welcome message over 800 characters, or not disclosing that the agent is automated** → Flag as High.
- **Persona in subagent instructions instead of agent-level** → Flag as Critical. Coverage gap.
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
| Persona reinforcement snippets | Subagent-level additions (Pattern 4) for long-conversation drift |

---

## Related Skills

- **agentforce/agent-topic-design** — designing subagent scope and instructions for task execution (separate from persona).
- **agentforce/agent-testing-and-evaluation** — structured testing methodology for agent conversations.
- **agentforce/agentforce-agent-creation** — end-to-end agent setup including channel assignment and deployment.
- **agentforce/agent-actions** — the action contract that persona-driven conversations invoke.
- **agentforce/einstein-trust-layer** — Trust-layer settings that interact with persona (PII masking, citation).
- **agentforce/agentforce-observability** — monitoring persona drift in production.
