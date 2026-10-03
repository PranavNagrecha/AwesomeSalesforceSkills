# LLM Anti-Patterns — Agentforce Persona Design

Common mistakes AI coding assistants make when generating or advising on Agentforce Persona Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Modal Verb Rule Lists as Persona Instructions

**What the LLM generates:** A bulleted list of rules like "You must always greet the user. You must never use jargon. You must always acknowledge the customer's concern. You must never provide financial advice." placed in agent-level system instructions.

**Why it happens:** LLMs default to rule-list formatting for instructions because it mirrors how constraints are typically presented in fine-tuning data and system prompt engineering examples. UNVERIFIED (2026-10-03): the earlier claim that modal verb chains cause reasoning loops. The documented behaviour is that agents follow strong language like "always" and "never" strictly and that conflicting instructions degrade performance (Generative AI guide, Best Practices for Writing Topic Instructions).

**Correct pattern:**
```
You are a warm and professional customer service assistant. You listen to customer concerns
before offering solutions. You communicate clearly and avoid technical jargon. When a
customer is frustrated, you acknowledge their experience with empathy before moving
to resolution.
```

**Detection hint:** More than 3 consecutive "You must" or "You never" or "You always" lines in a block of agent instructions.

---

## Anti-Pattern 2: Placing All Persona Instructions in Subagent Instructions

**What the LLM generates:** Tone and voice directives inside individual subagent instructions (subagents were called topics before April 2026) — e.g., within the "Billing" subagent instructions: "Respond formally and professionally when handling billing questions" — rather than in agent-level system instructions.

**Why it happens:** The LLM knows that Agentforce has both agent-level and subagent-level instructions but conflates them as interchangeable containers for behavioral guidance. The scoping difference (agent-level = always applies; subagent-level = only when active) is a nuance not widely documented.

**Correct pattern:**
```
Persona and tone belong ONLY in agent-level system instructions.
Subagent instructions should contain:
- Subagent scope definition (what this subagent handles, what it does NOT handle)
- Required actions the agent must take within the subagent
- Response format preferences for this specific subagent
Subagent instructions should NOT contain tone, voice, or brand voice guidelines.
```

**Detection hint:** Any tone adjective ("professional", "empathetic", "concise") appearing in subagent-level instructions rather than the agent-level instructions block.

---

## Anti-Pattern 3: Recommending a Single Agent With Persona Switching Logic

**What the LLM generates:** Instructions like: "If the user is an enterprise customer, respond formally. If the user is a consumer, respond casually." placed in agent-level instructions as a conditional persona switching mechanism.

**Why it happens:** LLMs pattern-match to chatbot design principles from general conversational AI where conditional persona switching is sometimes discussed. In Agentforce, the LLM cannot reliably detect user type mid-conversation and cannot switch personas based on runtime conditions.

**Correct pattern:**
```
Multi-persona = multiple agents, not conditional instructions.
Deploy separate agents with distinct system instructions for each audience segment.
Route users to the appropriate agent via channel configuration or an entry-point dispatcher.
```

**Detection hint:** Any "if the user is..." or "when talking to enterprise customers..." conditional persona logic in agent-level instructions.

---

## Anti-Pattern 4: Saying Persona Has No Metadata Home, or Inventing One

**What the LLM generates:** Either "persona is only free text in the instructions box, there is nothing structured", or invented elements such as an `instructions` field on `BotVersion` or a persona attribute on `GenAiPlugin`. An earlier version of this file made the first claim and named a `BotVersion` instructions field; both are wrong.

**Why it happens:** Assistants know agents are metadata and either over-generalize ("everything is a field") or under-generalize ("persona is just prose").

**Correct pattern:**
```text
Where persona actually lives (Metadata API reference; Agentforce Developer Guide, Agent Script Blocks):

Tone             BotVersion.toneType = Casual | Formal | Neutral (builder: Language Settings)
Instructions     Agent Script system.instructions in the AiAuthoringBundle .agent file
System messages  Agent Script system.messages.welcome and .error (both required)
Context          Agent Script config.role, config.company, config.description

BotVersion has no instructions field; its role and company fields are
"Reserved for internal use". Read retrieved metadata to review persona,
and change it in the builder or the Agent Script file.
```

**Detection hint:** References to `BotVersion.instructions`, persona attributes on `GenAiPlugin`, or Apex that "sets the agent persona".

---

## Anti-Pattern 5: Treating AI Assist as a Runtime Enforcement Mechanism

**What the LLM generates:** Advice that once "AI Assist has approved the instructions, the agent will consistently follow them in production."

**Why it happens:** LLMs familiar with code analysis tools (linters, static analyzers) transfer the concept that "passing the analyzer = correct behavior at runtime." AI Assist is a design-time tool, not a runtime enforcer. UNVERIFIED (2026-10-03): AI Assist is described only in a blog source; the testing advice holds for any authoring-time review.

**Correct pattern:**
```
AI Assist identifies potential instruction conflicts and ambiguities during authoring.
It does NOT guarantee runtime consistency.
Runtime validation requires:
1. Conversation preview testing with structured test utterances
2. Production monitoring via agent analytics and session traces
3. Periodic re-testing after any instruction change
```

**Detection hint:** Any statement that "AI Assist ensures the agent will..." or "AI Assist validates that the agent will..." in a context about production behavior.

---

## Anti-Pattern 6: Writing Tone Into Prose While Ignoring the Tone Setting

**What the LLM generates:** Three paragraphs of "be formal and polished" instructions, with no mention of the Language Settings tone, which is still on its Casual default.

**Why it happens:** Assistants assume tone can only be expressed in the prompt.

**Correct pattern:** Set the tone (Formal, Neutral or Casual) first, then use instructions for what the setting cannot express: vocabulary, how to acknowledge frustration, red lines. Expect actions with a specified tone, such as Draft or Revise Email, to keep their own tone (Generative AI guide, Considerations for Agents).

**Detection hint:** Persona guidance that never mentions the tone setting or `toneType`.

---

## Anti-Pattern 7: A Welcome Message That Hides the Bot

**What the LLM generates:** "Hi, I'm Sarah! How can I help you today?" with no sign that Sarah is automated, sometimes followed by a long paragraph of capabilities.

**Why it happens:** Assistants optimize for warmth and engagement.

**Correct pattern:** Introduce the agent as a bot or AI assistant and pair a human-sounding name with its job ("Hi, I'm Robbie, an automated returns agent"), stay under the 800-character limit, and add consent wording if data use needs it (Generative AI guide, Define System Messages).

**Detection hint:** A welcome message with a first name and no word such as "automated", "AI" or "assistant".

