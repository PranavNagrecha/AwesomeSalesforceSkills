---
name: agent-action-input-slot-extraction
description: "Use when designing how an Agentforce agent extracts structured input parameters (slots) from a user's natural-language utterance to invoke an action. Triggers: 'agent extract date from user', 'agent action argument extraction', 'agentforce slot filling', 'agent invocable input mapping', 'agent fails to fill required parameter'. NOT for action authoring (use agentforce/agent-actions) or for prompt-template variable binding (use agentforce/prompt-builder-templates)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
triggers:
  - "agent action not getting the date the user said"
  - "agentforce slot filling missing required argument"
  - "how to teach the agent to extract phone number from utterance"
  - "agent invocable input mapping description"
  - "ambiguous user input agent re-prompt"
tags:
  - agentforce
  - actions
  - slot-filling
  - prompt-design
inputs:
  - "the action's invocable input variables (name, type, description, required)"
  - "sample user utterances and the slot values that should be extracted"
  - "policy for missing/ambiguous slots (re-prompt vs. default vs. abort)"
outputs:
  - "input variable descriptions tuned for slot extraction"
  - "utterance → slot test cases"
  - "re-prompt strategy for missing required inputs"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Agent Action Input Slot Extraction

Activate when the agent invokes an Apex/Flow action correctly but with the *wrong* arguments — date misread, account id missing, picklist value paraphrased, phone number truncated. The skill produces tuned input-variable descriptions, utterance-level test cases, and a re-prompt policy for ambiguous or missing inputs.

---

## Before Starting

Gather this context before working on anything in this domain:

- The action's invocable definition: each input variable's `name`, `type`, `description`, and `required` flag. The description is the primary signal the LLM uses to extract values; vague descriptions → wrong slots.
- Real user utterances. Synthetic test cases miss the verbal patterns users actually produce ("schedule it for next Tuesday afternoon, ish").
- Whether the action is a one-shot invocation or part of a multi-turn flow. Multi-turn allows re-prompts; one-shot must succeed-or-fail with the first utterance.

---

## Core Concepts

### How slot extraction works

When the agent recognizes that an action should be invoked, it constructs an LLM prompt containing:

- The action's invocable input variables and their descriptions
- The user's utterance(s)
- The conversation context

The LLM extracts values for each input variable and validates them against the input type. Missing required inputs trigger a re-prompt cycle.

The **description** field is the lever. A description like `"Date"` gets misread for any date in the utterance. `"The customer's preferred appointment date in ISO 8601 (YYYY-MM-DD); reject relative phrases like 'next week'"` constrains extraction.

### Types and coercion

| Input type | Extraction behavior | Common failure |
|---|---|---|
| `Date` | LLM parses natural language → ISO date | "next Tuesday" parses inconsistently across timezones |
| `DateTime` | Same + time-of-day | Vague times ("afternoon") get pinned to noon by default |
| `String` | Free-form | Verbose users put unrelated content in the slot |
| `Picklist` (Apex enum / Flow choice) | LLM matches utterance to one of the values | Synonyms get rejected unless described |
| `Id` (lookup) | LLM extracts a name; the action must resolve to an Id | LLM hallucinates IDs starting with valid prefixes |
| `Boolean` | Affirmative/negative cues | Negation in mid-sentence ("no, wait, yes") |

### Re-prompt strategy

When a required slot can't be extracted, the agent re-prompts: `"What date should I schedule the appointment for?"`. The re-prompt template should be configured per input. Without configuration, the agent generates a generic prompt that often confuses the user.

For **ambiguous** extraction (two plausible values), the better pattern is to confirm: `"Did you mean Tuesday March 12 or March 19?"`.

---

## Common Patterns

### Pattern: explicit format constraint in description

**When to use:** Date, datetime, phone, id, anything with a canonical format.

**How it works:** Description includes the format and an explicit reject clause. `"Account record ID; must be exactly 18 alphanumeric characters starting with '001'. Reject names or fragments."`

**Why not the alternative:** A description of "Account ID" alone causes the LLM to hallucinate IDs from account names.

### Pattern: enumerate picklist values inline

**When to use:** Apex enum or Flow choice as input.

**How it works:** Description lists every valid value with disambiguation. `"Severity: one of LOW (cosmetic, no impact), MEDIUM (workaround exists), HIGH (production blocked). Synonyms: 'critical' = HIGH; 'minor' = LOW."`

**Why not the alternative:** Without enumeration, the LLM matches user phrasing to the closest type member, often wrong (`'urgent'` → MEDIUM when policy says HIGH).

### Pattern: name-to-Id resolution outside the LLM

**When to use:** Action takes a record Id but users speak in names.

**How it works:** Define the input as a `String accountName`. Inside the Apex/Flow action, resolve to Id via SOQL with proper escaping and ambiguity handling. Never let the LLM emit IDs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| User must specify an exact date | `Date` input + ISO-format description + reject relatives | Relative phrasing parses inconsistently |
| Action takes a lookup record | `String name` input; Apex resolves to Id | LLMs hallucinate IDs; resolution belongs in Apex |
| Required slot may be missing | Configure re-prompt text per input | Generic re-prompt confuses users |
| Multiple plausible values for a slot | Disambiguate via confirmation prompt before action | Action with wrong slot is worse than slow action |
| Free-form note text | `String` with no constraint description | LLM extracts the user's verbatim sentence; no extraction logic needed |

---

## Recommended Workflow

1. List every invocable input the action exposes. For each, ask: what's the canonical type? what synonyms or formats might appear? is it required?
2. Write a **specific** description per input. Include format, examples, reject clauses. Treat the description as the LLM's instruction manual for that slot.
3. Build a sample-utterance test set: 10–20 utterances per slot covering typical, edge-case, and adversarial phrasings.
4. For required slots, configure a re-prompt template that names the missing slot and gives an example.
5. For lookup-type slots, change the input from `Id` to `String <name>` and resolve inside the action; document the lookup ambiguity policy (first match? prompt for clarification? abort?).
6. Run the test utterances through the agent test harness (Agent Builder → Test in App). Record extraction accuracy per slot.
7. Iterate on the descriptions until extraction accuracy crosses your bar (typically ≥95% for high-stakes actions, lower for low-stakes).

---

## Review Checklist

- [ ] Each input has a description that includes format + examples + reject clauses
- [ ] Picklist/enum inputs enumerate values with synonym disambiguation
- [ ] Lookup/Id inputs are taken as names, resolved inside the action
- [ ] Required-slot re-prompts configured with slot name and example
- [ ] Test-utterance suite covers ≥10 utterances per slot
- [ ] Accuracy measured and meets the action's stakes

---

## Salesforce-Specific Gotchas

1. **Description text is the primary lever; the variable name is secondary** — `String d` with description "appointment date" extracts as well as `String appointmentDate` with the same description. Don't rely on naming.
2. **Date inputs default to the running user's timezone** — "next Tuesday" relative to which timezone? Specify in the description.
3. **Required + no value extracted = agent emits a built-in re-prompt** — Often phrased awkwardly. Always override.
4. **Hallucinated IDs validate as the right shape but reference no record** — Apex must check existence and surface a clear error to the agent loop, not silently fail.
5. **Picklist values must match exactly** — The LLM may emit "high" when the picklist value is "HIGH". Apex enum coercion fails. Normalize case in the action.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Tuned invocable input definitions | Updated `description=` strings on every input |
| Test-utterance suite | YAML/CSV: utterance → expected slot values |
| Re-prompt template per slot | Per-input override of the generic agent re-prompt |
| Resolution policy for lookup inputs | Documented in the action's class header |

---

## Related Skills

- agentforce/agent-actions — for the broader action design and invocation flow
- agentforce/agentforce-tool-use-patterns — for when an action call leads into another tool call
- agentforce/agentforce-eval-harness — for measuring extraction accuracy at scale
- agentforce/custom-agent-actions-apex — for Apex implementation patterns of name-to-Id resolution
