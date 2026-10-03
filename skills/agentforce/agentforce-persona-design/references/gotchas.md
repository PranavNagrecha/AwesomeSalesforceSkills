# Gotchas: Agentforce Persona Design

Non-obvious platform behaviours that shape how an agent sounds. Gotchas 1 to 4 are carried from the earlier version; Gotcha 1 is reframed because the official guidance contradicts part of it, and Gotchas 3 and 4 rest on blog posts only, so they are marked UNVERIFIED. Gotchas 5 to 12 are cited.

## Gotcha 1: Absolutes are followed strictly, so every "always" and "never" must be meant

**What happens:** A persona written as a long list of "always" and "never" rules produces stiff replies, and conflicting rules produce inconsistent ones.

**When it occurs:** Instructions are written as a rule list with many strong directives, some of which conflict ("always explain fully", "never exceed two sentences").

**How to avoid:** Describe the voice in plain sentences and keep absolutes for real red lines. Remove contradictions before testing. Start with few instructions and add them one at a time, testing for regressions between changes.

**Correction:** the earlier text said modal-verb chains "cause reasoning loops". No official source says that. The Generative AI guide says the opposite of ignoring them: "an agent tends to strictly follow strong language like 'always' and 'never'", so use them "only when you mean it". It also says contradicting instructions "can cause errors and degrade performance".

**Source:** Generative AI guide (Spring '26), Best Practices for Writing Topic Instructions.

---

## Gotcha 2: Persona in subagent instructions applies only inside that subagent

**What happens:** The agent is formal while handling billing and generic everywhere else.

**When it occurs:** Tone instructions are added to individual subagents instead of the agent level.

**How to avoid:** Put the persona in the agent-level instructions. In Agent Script that is the `system` block, which "contains general instructions for the agent"; subagent reasoning instructions should cover the task.

**Source:** Agentforce Developer Guide, Agent Script Blocks (system block versus subagent block).

---

## Gotcha 3: AI Assist reviews instructions but does not enforce them

**What happens:** Instructions pass an authoring-time review, then the agent still goes off-brand with unusual or adversarial input.

**When it occurs:** An authoring aid is treated as the final quality gate.

**How to avoid:** Test persona edges in preview and in a regression suite (see `references/metadata-examples.md`, Example 4) after every instruction change.

**Source:** UNVERIFIED (2026-10-03): the AI Assist feature is described only in a Salesforce Developers blog post cited by the earlier version; none of the official guides read for this revision mention it. The testing advice stands on its own: the Generative AI guide says LLMs are nondeterministic and instructions need iterative testing.

---

## Gotcha 4: Channel-specific formatting depends on release and channel

**What happens:** Formatting instructions ("use Markdown") render as raw symbols in channels that do not support them.

**When it occurs:** Formatting is hard-coded in the persona.

**How to avoid:** Keep formatting out of the persona and test in each real channel. Note that custom actions cannot control how their output appears; it is formatted automatically.

**Source:** Generative AI guide, Considerations for Custom Actions ("you can't specify how the output appears in an agent conversation"). UNVERIFIED (2026-10-03): the earlier claims about an "Adaptive Response Formats" feature generally available from Spring '26, which rest on a blog post only.

---

## Gotcha 5: Tone is a setting, and it does not reach every action

**What happens:** The team rewrites instructions to sound formal, while the agent's tone setting is still the default Casual. Or a formal setting does not change the drafts produced by an email action.

**When it occurs:** The native tone setting is overlooked, or expected to govern actions with their own tone.

**How to avoid:** Set the tone (Formal, Neutral or Casual) in Language Settings first; the default is Casual. Expect actions with a specified tone, such as Draft or Revise Email, to keep their own tone. Restart the preview after changing it.

**Source:** Generative AI guide, Update Language Settings ("By default, your agent's tone is casual") and Considerations for Agents ("Tone settings don't affect the output of agent actions that have a specified tone, such as Draft or Revise Email"); Metadata API reference, BotVersion `toneType`.

---

## Gotcha 6: The welcome message has a limit and a disclosure job

**What happens:** A long, human-sounding welcome is rejected, or customers believe they are talking to a person.

**When it occurs:** The welcome message is written as marketing copy with a human persona name.

**How to avoid:** Keep it under 800 characters. Introduce the agent as a bot or AI assistant; if it has a human-sounding name, pair the name with its job ("an automated returns agent"). Use the welcome to state how data is used if consent matters.

**Source:** Generative AI guide, Define System Messages.

---

## Gotcha 7: System messages are not translated, and language settings cover generated text only

**What happens:** A Spanish-speaking customer gets an English welcome and Spanish answers.

**When it occurs:** Extra languages are added in Language Settings and system messages are assumed to follow.

**How to avoid:** Add one manual translation per system message for each extra language. Remember that language settings apply to LLM-generated messages, not system messages, and do not change actions that have a specified language.

**Source:** Generative AI guide, Considerations for Agents ("Language settings apply to LLM-generated messages only. System messages, such as an agent's welcome message, aren't translated").

---

## Gotcha 8: Not every agent type has system messages

**What happens:** A designer writes welcome and error copy for an agent type that has no system messages.

**When it occurs:** The persona plan assumes every agent has a welcome message.

**How to avoid:** Check the agent type first. Only the default Agentforce agent and Agentforce Service Agent have system messages in the builder. In Agent Script, `welcome` and `error` are required messages in the `system` block.

**Source:** Generative AI guide, Define System Messages; Agentforce Developer Guide, Agent Script Blocks ("welcome and error are required messages").

---

## Gotcha 9: Persona cannot carry business rules

**What happens:** A persona line such as "never promise a refund above 100 dollars" is followed most of the time, not always.

**When it occurs:** Policy is written into the voice.

**How to avoid:** Enforce policy in the action (Apex or flow) and keep the persona to how the agent speaks.

**Source:** Generative AI guide, Best Practices for Writing Topic Instructions ("Build sensitive or deterministic business rules into the logic of an action itself, not the topic instructions").

---

## Gotcha 10: Long conversations see only recent turns

**What happens:** Early in a conversation the agent uses the customer's stated preference; later it forgets it.

**When it occurs:** Persona or preference relies on something said many turns ago.

**How to avoid:** Store important preferences in variables, and keep persona in agent-level instructions rather than in the conversation. For Agentforce (Default), messages from up to the most recent six turns are used as context.

**Source:** Generative AI guide, Agents Limits ("Messages from up to the most recent six turns, including agent and user messages, are used as context"). UNVERIFIED (2026-10-03): the earlier general claim that persona "drifts" as attention to system instructions weakens over context length.

---

## Gotcha 11: Instruction order on screen is not a priority order

**What happens:** The team puts the persona first and expects it to outrank later instructions.

**When it occurs:** Priority is expressed by position.

**How to avoid:** State precedence and sequence explicitly in words ("If the customer is upset, acknowledge it before anything else").

**Source:** Generative AI guide, Best Practices for Writing Topic Instructions: "The LLM doesn't use the visual order of instructions in the Topic Configuration tab to make decisions." UNVERIFIED (2026-10-03): the earlier claim that the opening paragraph of agent-level instructions is weighted highest.

---

## Gotcha 12: Requested locales can come back as a close variant

**What happens:** A persona for Belgian French customers answers in French as used in France.

**When it occurs:** The requested locale is not supported and the model falls back to a nearby one.

**How to avoid:** Check the supported locale list before promising a regional voice, and test each locale in preview.

**Source:** Generative AI guide, Considerations for Agents ("Some LLMs generate responses that are close variants but not exact matches for the requested locale").
