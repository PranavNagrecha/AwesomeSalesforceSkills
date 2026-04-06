# Gotchas — Agentforce Persona Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Long Must/Never/Always Chains Cause Non-Deterministic Responses

**What happens:** When agent-level system instructions contain long sequences of `must`, `never`, and `always` directives (e.g., "You must always acknowledge the customer. You must never use jargon. You must always end with a question. You must never exceed two sentences."), the LLM begins spending inference tokens evaluating rule compliance rather than generating a helpful response. The resulting responses are slower, more generic, and may contradict each other when rules conflict.

**When it occurs:** Instructions written as a bulleted rule list with 5+ modal verb directives, especially when some rules are mutually exclusive (e.g., "always explain fully" AND "always be concise").

**How to avoid:** Replace rule lists with descriptive behavioral paragraphs using voice adjectives. "You are concise and empathetic. You acknowledge concerns before offering solutions." achieves the same goal without rule-evaluation overhead. Use AI Assist to check for conflicting directives before publishing.

---

## Gotcha 2: Persona in Topic Instructions Only Applies When That Topic Is Active

**What happens:** A practitioner adds tone and brand voice instructions to individual topic instructions (e.g., "Respond formally when handling billing questions"). When the agent handles unmatched queries, is in escalation, or routes to a different topic, those tone instructions are absent. The agent's voice becomes inconsistent — formal during billing, neutral or generic during other interactions.

**When it occurs:** Persona instructions are placed at the topic level instead of the agent level, usually because the practitioner follows the same authoring pattern they used for topic-specific behavior.

**How to avoid:** Agent-level system instructions are the only location where persona is consistently applied across all conversations and all topics. Topic instructions should focus on task scope and action guidelines, not tone or brand voice.

---

## Gotcha 3: AI Assist Does Not Enforce Instructions at Runtime

**What happens:** AI Assist in Agent Builder runs static analysis on the instruction text and flags conflicts, but it does not enforce or validate instructions during actual agent conversations. An instruction that AI Assist marks as "no issues" can still be ignored or inconsistently applied by the LLM at runtime, especially under unusual or adversarial user inputs.

**When it occurs:** A practitioner uses AI Assist as the final QA gate and does not run conversation preview tests. The agent passes AI Assist but produces off-brand responses during user acceptance testing.

**How to avoid:** AI Assist is a starting point, not a final validator. Always run conversation preview tests with a structured set of utterances (including edge cases like frustrated users and off-topic queries) after any instruction change. Score responses against the target voice adjectives in the test plan.

---

## Gotcha 4: Adaptive Response Formats Require Spring '26 or Later

**What happens:** Instructions referencing channel-specific formatting (e.g., "Use Markdown for web chat, plain text for API") do not work correctly in orgs running Summer '25 or earlier because the Adaptive Response Formats feature was not generally available until Spring '26. The agent ignores or misinterprets the formatting directives.

**When it occurs:** A practitioner follows Spring '26+ documentation on a sandbox running an earlier release.

**How to avoid:** Check the org's current Salesforce release before implementing adaptive response format configuration. For earlier releases, configure response formatting via the channel deployment settings rather than system instructions, or apply Markdown in the agent instructions knowing it may render as raw markup in non-Markdown channels.
