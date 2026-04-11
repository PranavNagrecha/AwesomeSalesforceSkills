---
name: agent-conversation-design
description: "Use when writing or auditing the conversational copy layer of a Salesforce bot or Agentforce agent: utterance authoring strategy, fallback message copy, escalation-criteria phrasing, and persona-consistent dialog scripting across channels. NOT for platform configuration (bot builder setup, topic metadata wiring, action mapping, or Agentforce deployment) — see architect/einstein-bot-architecture and agentforce/agentforce-persona-design for those concerns."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "how do I write utterances for my Einstein Bot intent so it actually matches user messages"
  - "my bot fallback message sounds robotic and frustrates users, how should I rewrite it"
  - "how to phrase escalation criteria so the bot hands off to an agent at the right time"
  - "writing dialog scripts that stay on-brand across web chat and mobile"
  - "how many utterances do I need per intent and how should I vary them"
tags:
  - conversation-design
  - utterance-authoring
  - fallback-strategy
  - escalation-criteria
  - dialog-scripting
  - einstein-bots
  - agentforce
inputs:
  - "Intent taxonomy or topic list with at least names and brief descriptions"
  - "Brand voice guidelines or tone adjective pairs (can be informal)"
  - "Target channel(s): web chat, mobile, Slack, API"
  - "Historical case data or common customer phrasings if available"
  - "Escalation destinations: queue names, skill routing targets"
outputs:
  - "Utterance set per intent with coverage across register, vocabulary, and error-correction variants"
  - "Fallback message copy with progressive clarification pattern"
  - "Escalation criteria phrasing for each handoff trigger"
  - "Dialog script for the most complex or highest-volume intent"
  - "Persona consistency checklist for copy review"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Agent Conversation Design

This skill activates when a practitioner needs to author, improve, or audit the conversational copy layer of an Einstein Bot or Agentforce deployment. It covers the craft of writing utterances, fallback messages, escalation phrasing, and persona-consistent dialog scripts — not the platform mechanics of wiring those elements together. If a bot is misrouting, the platform structure (intents, topics, action mapping) is covered by architect/einstein-bot-architecture and agentforce/agentforce-persona-design; this skill handles the textual content that feeds those structures.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether the deployment uses **Einstein Bots (dialog/intent model)** or **Agentforce (topic/action model)** — the routing mechanism differs, but utterance authoring principles apply to both. In Agentforce, topic description text and utterance examples in test cases are the equivalent of bot intents.
- Identify the target **channel** — utterance vocabulary and dialog length norms differ between web chat (can be verbose), mobile (keep responses to 2–3 lines), and Slack (expect informal phrasing and typos).
- Understand the **escalation destinations** available (queues, skills, agents) before writing escalation copy — vague escalation messages ("someone will help you") that don't match the actual routing cause user confusion when the assigned agent has the wrong skill.

---

## Core Concepts

### Utterance Coverage Strategy

An utterance is a sample phrasing a user might say to trigger an intent. The NLU model learns to match new messages by generalizing from these examples. Coverage has three dimensions:

1. **Register variation** — formal ("I would like to cancel my subscription"), casual ("cancel my sub"), and frustrated ("just cancel it already")
2. **Vocabulary variation** — synonyms and alternate terms a user might use for the same concept ("cancel", "terminate", "end", "stop", "delete my account")
3. **Error-correction variants** — common typos, abbreviations, and partial phrasing ("cncel", "cncl acct", "how do i stop")

The minimum threshold for a production intent is 20 utterances; 50+ is recommended where case volume data is available to mine real phrasings. Fewer than 15 utterances leads to high false-negative rates — the model fails to match messages it should resolve.

For Agentforce, the topic description text is the primary routing signal, not an utterance list. A vague description like "handles billing questions" causes the agent to over-match and route unrelated queries to that topic. Write descriptions with explicit scope boundaries: "Use for questions about invoice amounts, payment history, or billing address updates. Do not use for payment method changes or refunds."

### Fallback Copy and Progressive Clarification

A fallback fires when the NLU model cannot route a message to any intent above the confidence threshold. Poor fallback copy ("I didn't understand that, please try again") provides no signal to the user about how to rephrase and triggers repeated fallback loops.

Effective fallback copy follows a **progressive clarification pattern**:
1. **First fallback**: Acknowledge the gap without blaming the user and offer 2–3 concrete rephrasing options: "I didn't quite catch that. Are you asking about your order status, a return, or something else?"
2. **Second fallback**: Confirm intent before escalating: "I'm still not finding a match. Do you want me to connect you with a human agent who can help?"
3. **Third fallback**: Auto-escalate with a context-transfer message to the receiving agent.

The copy on the second fallback is the most important: a vague "do you want to speak to an agent?" prompt gets lower acceptance than one that names the value ("a specialist who can pull up your account and resolve this directly").

### Escalation Criteria Phrasing

Escalation criteria define the conditions under which the bot transfers to a human agent. These conditions exist at two layers:

1. **Explicit user request** — phrasing like "agent", "human", "talk to a person", "representative". The utterance set for the escalation intent must cover all common variants including frustrated variants ("just get me a real person").
2. **Condition-based criteria** — business rules that trigger escalation regardless of user phrasing (e.g., account is flagged for VIP handling, case priority is high, topic requires authenticated action the bot cannot perform).

When writing escalation copy, name the receiving destination in user-visible terms: "I'm connecting you to our billing specialist team" performs better than "transferring to an agent" because it sets accurate expectations about who will respond and for what purpose.

### Persona Consistency Across Channels

A dialog script written in formal language for web chat will feel jarring if the same intent fires in a Slack bot where users expect casual phrasing. Persona consistency means applying the same voice adjectives from the brand guidelines at the right register for the channel. Write a **channel register matrix** — one row per channel, columns for formality level, max response length, and emoji/markdown allowance — before scripting dialogs.

---

## Common Patterns

### Mining Historical Cases for Utterance Sets

**When to use:** Building or expanding utterances for a high-volume intent when case history is available.

**How it works:**
1. Export the last 6–12 months of cases for the intent's subject area. Filter to cases that were resolved by the bot or that the bot attempted to handle.
2. Extract the first customer message from each case. This is the closest proxy for the utterance the NLU must match.
3. Cluster by vocabulary and register. Each distinct cluster should produce 3–5 utterance variants.
4. Add 5–10 frustrated and typo variants manually — these are systematically underrepresented in case data because agents often re-ask for clarification before logging, stripping the original phrasing.
5. Validate coverage against the three dimensions: register, vocabulary, error-correction.

**Why not write utterances from scratch:** Human-generated utterances tend to be too formal and too correct. Real users type fast, make errors, and use abbreviations. Case-mined phrasings produce a more representative training set.

### Progressive Fallback Dialog Script

**When to use:** Designing the fallback path for any bot deployment, especially first-time builds.

**How it works:**

```
[Fallback 1 — NLU confidence below threshold]
Bot: "I want to make sure I help with the right thing. Are you asking about:
  • Checking an order
  • Making a return
  • Something else?"

[Fallback 2 — still no confident match]
Bot: "I'm not finding a good match for what you're asking.
Would you like me to connect you with a member of our support team who can pull up your account?"

[Fallback 3 — user declines or no response]
Bot: "No problem — I'll go ahead and connect you. A member of the [Team Name] team will be with you shortly. I'm passing along your message so they're ready to help."
```

**Why not a single generic fallback:** A single "I didn't understand" message offers no resolution path, forces the user to start over with no guidance, and creates a dead end that damages trust in the bot for future interactions.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Intent has fewer than 20 utterances | Mine case data first, then manually add register and error variants | Sub-20 utterance sets produce high false-negative rates at production volume |
| Bot is firing fallback on known phrasings | Audit utterance vocabulary against actual user messages in conversation logs | Utterance set likely has register or vocabulary gap, not a model issue |
| Agentforce topic is routing unrelated queries | Rewrite topic description with explicit scope boundaries and exclusion clauses | Topic description is the routing signal; vague descriptions cause over-matching |
| Users are declining the escalation offer | Rewrite escalation prompt to name the destination and the value ("billing specialist") | Generic "speak to an agent" has lower acceptance than destination-specific copy |
| Dialog feels inconsistent across channels | Build a channel register matrix before scripting; author per-channel variants | Tone that works for formal web chat is often wrong for Slack or mobile |
| Fallback loop is firing 3+ times before resolution | Implement progressive clarification with offer set on first fallback | Single generic fallback provides no rephrasing signal to the user |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather inventory** — collect the full intent or topic list, brand voice adjective pairs, target channels, and escalation destinations before writing any copy.
2. **Mine utterances from case data** — for each intent, extract first customer messages from 6–12 months of relevant case history. Cluster by vocabulary and register. Target 50+ utterances per intent for production volume; 20 minimum.
3. **Author fallback copy** — write a three-stage progressive clarification fallback using concrete offer sets on stage one and a named destination on stage two. Confirm the escalation destination name is the user-facing team name, not an internal queue label.
4. **Write escalation intent utterances** — cover all variants of "talk to a human" including frustrated phrasings. Add condition-based escalation criteria documentation for the bot platform configuration (not copy, but inputs the platform engineer needs).
5. **Script the top 3 highest-volume dialog flows** — write the full user/bot exchange, not just bot messages in isolation. Check each bot turn for persona adjective alignment. Validate response length is appropriate for the target channel.
6. **Review against the persona consistency checklist** — compare voice adjectives from brand guidelines against each bot message. Flag any turn that sounds off-brand or uses prohibited phrases.
7. **Hand off to platform configuration** — package utterance sets, fallback copy, escalation criteria, and dialog scripts as inputs to the bot builder or Agentforce configuration step. This skill ends at copy delivery; platform wiring is out of scope.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every intent has 20+ utterances; production intents targeting high volume have 50+
- [ ] Utterances cover at least three registers: formal, casual, and frustrated
- [ ] Utterances include typo and abbreviation variants
- [ ] Fallback copy follows a progressive clarification pattern (3 stages)
- [ ] Escalation copy names the destination in user-facing terms, not internal queue labels
- [ ] Agentforce topic descriptions include explicit scope boundaries and exclusion clauses
- [ ] Dialog scripts have been authored per channel where channel register differs
- [ ] All bot copy reviewed against brand voice adjectives (persona consistency check)
- [ ] No bot message uses internal jargon, system error codes, or technical identifiers

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Agentforce topic description vagueness causes silent over-matching** — A topic description like "handles customer account questions" is broad enough that the LLM routes almost any account-adjacent query to it, including queries that should go to a more specific topic. This produces incorrect resolutions without an obvious error signal. Write descriptions with explicit boundary clauses ("does not handle payment method changes or refunds") to constrain routing.
2. **Utterance case sensitivity does not matter, but punctuation does** — The Einstein Bots NLU model normalizes case, but punctuation variants ("cancel." vs "cancel" vs "cancel!") can produce different tokenization results in older model versions. Always include a punctuation-free variant and an exclamation variant for high-emotion intents.
3. **Fallback intent utterances compete with regular intents** — If any utterance is placed in the fallback intent's training data, it can pull legitimate queries away from their correct intents. The fallback intent must have zero utterances; it activates only below the confidence threshold, not by intent matching.
4. **Escalation message is visible to the customer AND passed to the receiving agent** — The transfer message configured in the bot dialog is displayed to the customer and typically included in the conversation transcript passed to the human agent. Copy that addresses the customer directly ("I'm connecting you now") can confuse the agent if they read the transcript as a message directed at them. Use neutral handoff phrasing that works for both audiences or configure a separate customer-visible message and a transcript note.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Utterance sets by intent | CSV or markdown table of 20–50+ utterances per intent, tagged by register and variant type |
| Progressive fallback dialog | Three-stage fallback copy with offer set on stage 1, named destination on stage 2, auto-handoff on stage 3 |
| Escalation intent utterances | Full utterance list for the escalation/human-request intent including frustrated variants |
| Escalation criteria documentation | Condition-based escalation triggers written as inputs for platform configuration |
| Dialog scripts (top flows) | Full user/bot exchange scripts for the 3 highest-volume intents, reviewed for persona consistency |
| Persona consistency checklist | Per-message review against brand voice adjectives, flagged turns highlighted |

---

## Related Skills

- architect/einstein-bot-architecture — platform structure, intent taxonomy design, and handoff architecture (use before this skill for new builds)
- agentforce/agentforce-persona-design — agent-level system instruction writing and tone encoding for Agentforce
- agentforce/agent-testing-and-evaluation — structured test methodology including AiEvaluationDefinition for conversation quality
