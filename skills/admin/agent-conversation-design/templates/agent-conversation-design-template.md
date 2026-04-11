# Agent Conversation Design — Work Template

Use this template when authoring or auditing the conversation copy layer for an Einstein Bot or Agentforce deployment.

## Scope

**Skill:** `agent-conversation-design`

**Request summary:** (fill in what the practitioner asked for — e.g., "expand utterances for Returns intent", "rewrite fallback copy", "write escalation criteria for VIP handoff")

**Platform:** [ ] Einstein Bots (dialog/intent model)  [ ] Agentforce (topic/action model)  [ ] Both

---

## Context Gathered

**Intent / Topic inventory:**

| Intent or Topic Name | Current Utterance Count | Fallback Rate (if known) | Escalation Destination |
|---|---|---|---|
| | | | |
| | | | |

**Brand voice adjectives:** (e.g., empathetic, concise, professional)
- Adjective 1:
- Adjective 2:
- Adjective 3:

**Target channel(s):** (web chat / mobile / Slack / API / other)
- Channel 1: _________________ | Max message length: _____ chars | Markdown: Y/N | Emoji: Y/N
- Channel 2: _________________ | Max message length: _____ chars | Markdown: Y/N | Emoji: Y/N

**Escalation destinations (user-facing names):**
- Destination 1 (internal queue name): _________________ → User-facing name: _________________
- Destination 2 (internal queue name): _________________ → User-facing name: _________________

---

## Utterance Set — [Intent/Topic Name]

**Target count:** _____ utterances (minimum 20 for production; 50+ recommended for high volume)

**Case data source:** (case export date range, filter criteria used)

| # | Utterance Text | Register | Variant Type |
|---|---|---|---|
| 1 | | Formal | Original |
| 2 | | Casual | Synonym |
| 3 | | Frustrated | Register variant |
| 4 | | Abbreviated | Abbreviation |
| 5 | | Frustrated | Typo variant |
| ... | | | |

**Coverage check:**
- [ ] Formal register: _____ utterances
- [ ] Casual register: _____ utterances
- [ ] Frustrated register: _____ utterances
- [ ] Typo / error variants: _____ utterances
- [ ] Vocabulary clusters covered: _____ distinct synonym groups

---

## Fallback Copy

### Stage 1 — First Unmatched Message

```
[Bot message — stage 1 fallback]
I want to make sure I help with the right thing. Are you asking about one of these?
  • [Top topic 1 in user-facing language]
  • [Top topic 2 in user-facing language]
  • [Top topic 3 in user-facing language]
  • Something else
```

### Stage 2 — Second Consecutive Unmatched Message

```
[Bot message — stage 2 fallback]
I'm still not finding a match for what you're asking.
Would you like me to connect you with [User-facing team name]
who can [specific value: e.g., "pull up your account and help directly"]?
```

### Stage 3 — Auto-Handoff (user declines or no response after ___ seconds)

```
[Bot message — stage 3 fallback / transfer message]
Got it — I'll connect you now. [User-facing team name] will be with you shortly.
I'm passing along your message so they're ready to help.
```

---

## Escalation Intent Utterances

**Escalation intent name:** (e.g., "Escalate_To_Human", "Request_Agent")

| # | Utterance | Register |
|---|---|---|
| 1 | agent | Keyword |
| 2 | human | Keyword |
| 3 | talk to a person | Casual |
| 4 | I want to speak to a representative | Formal |
| 5 | connect me to a real person | Casual |
| 6 | get me a human now | Frustrated |
| 7 | just get me an agent | Frustrated |
| 8 | I need to talk to someone | Casual |
| 9 | agent!!!! | High-emotion |
| 10 | human pls | Abbreviated |
| ... | (add org-specific variants) | |

**Condition-based escalation triggers** (for platform configuration, not copy):

| Trigger Condition | Escalation Destination | Priority |
|---|---|---|
| (e.g., Account.VIP__c = true) | (user-facing team name) | High |
| (e.g., Case.Priority = Critical) | (user-facing team name) | High |
| (e.g., Bot fallback fired 3 times) | (user-facing team name) | Standard |

---

## Dialog Script — [Intent/Topic Name]

**Channel:** _________________

**Persona adjectives applied:** _________________

```
User: [Opening utterance — formal/casual variant]

Bot:  [Turn 1 — acknowledge + clarify if needed]
      [Keep under ___ characters for [channel]]

User: [User response — normal path]

Bot:  [Turn 2 — resolution or next step]
      [Named CTA or confirmation: "Your [X] has been [Y]."]

User: [Optional follow-up or confirmation]

Bot:  [Turn 3 / close — persona-consistent sign-off]
```

**Persona review:**
- [ ] Turn 1 reflects voice adjective: _________________
- [ ] Turn 2 is within max length for [channel]
- [ ] Turn 3 closes with brand-consistent phrasing
- [ ] No internal jargon or system identifiers visible to user
- [ ] Escalation path scripted if this intent can overflow to human handoff

---

## Agentforce Topic Description (if applicable)

**Topic name:** _________________

**Description draft:**

```
Use for: [explicit subject matter — 2–4 specific scenarios]
Do NOT use for: [explicit exclusion — route to [Other Topic Name] instead]
```

**Routing boundary test:** (submit the following borderline queries 5 times each in conversation preview and confirm consistent routing)

| Borderline Query | Expected Topic | Actual Topic (run 1–5) | Pass/Fail |
|---|---|---|---|
| | | / / / / / | |
| | | / / / / / | |

---

## Review Checklist

- [ ] Every intent has 20+ utterances (50+ for high-volume production intents)
- [ ] Utterances cover formal, casual, frustrated, and typo/abbreviated registers
- [ ] Fallback copy follows 3-stage progressive clarification pattern
- [ ] Escalation copy uses user-facing team names, not internal queue identifiers
- [ ] Escalation intent includes high-emotion and frustrated-register utterances
- [ ] Agentforce topic descriptions include explicit scope and exclusion clauses
- [ ] Dialog scripts authored per channel where channel register differs
- [ ] All bot copy reviewed against brand voice adjectives
- [ ] No internal system identifiers (queue names, IDs) visible in any customer-facing message
- [ ] Fallback intent utterance list is EMPTY (Einstein Bots only)

---

## Notes

(Record any deviations from the standard patterns, org-specific constraints, or decisions made during this session.)
