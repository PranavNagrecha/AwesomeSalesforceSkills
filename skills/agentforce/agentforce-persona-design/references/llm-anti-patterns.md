# LLM Anti-Patterns — Agentforce Persona Design

Common mistakes AI coding assistants make when generating or advising on Agentforce Persona Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Modal Verb Rule Lists as Persona Instructions

**What the LLM generates:** A bulleted list of rules like "You must always greet the user. You must never use jargon. You must always acknowledge the customer's concern. You must never provide financial advice." placed in agent-level system instructions.

**Why it happens:** LLMs default to rule-list formatting for instructions because it mirrors how constraints are typically presented in fine-tuning data and system prompt engineering examples. The Agentforce-specific behavior where modal verb chains cause reasoning loops is not captured in general LLM training.

**Correct pattern:**
```
You are a warm and professional customer service assistant. You listen to customer concerns
before offering solutions. You communicate clearly and avoid technical jargon. When a
customer is frustrated, you acknowledge their experience with empathy before moving
to resolution.
```

**Detection hint:** More than 3 consecutive "You must" or "You never" or "You always" lines in a block of agent instructions.

---

## Anti-Pattern 2: Placing All Persona Instructions in Topic Instructions

**What the LLM generates:** Tone and voice directives inside individual topic instructions (e.g., within the "Billing" topic instructions: "Respond formally and professionally when handling billing questions") rather than in agent-level system instructions.

**Why it happens:** The LLM knows that Agentforce has both agent-level and topic-level instructions but conflates them as interchangeable containers for behavioral guidance. The scoping difference (agent-level = always applies; topic-level = only when active) is a nuance not widely documented.

**Correct pattern:**
```
Persona and tone belong ONLY in agent-level system instructions.
Topic instructions should contain:
- Topic scope definition (what this topic handles, what it does NOT handle)
- Required actions the agent must take within the topic
- Response format preferences for this specific topic
Topic instructions should NOT contain tone, voice, or brand voice guidelines.
```

**Detection hint:** Any tone adjective ("professional", "empathetic", "concise") appearing in topic-level instructions rather than the agent-level instructions block.

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

## Anti-Pattern 4: Suggesting Persona Is Configurable in Metadata XML or Apex

**What the LLM generates:** Code showing how to set an agent's persona via Apex or by editing GenAiPlugin metadata XML fields.

**Why it happens:** LLMs know that Agentforce configuration is represented as metadata and that many Salesforce behaviors are configurable via Apex or metadata. They extrapolate that persona must also be a structured metadata field, when in fact it is free-form text in the instructions field of the agent definition.

**Correct pattern:**
```
Persona instructions are free-form text in the agent's system instructions field.
In Agent Builder UI: Edit the "Instructions" text area in the agent configuration.
In metadata: The instructions text is in the BotVersion metadata's instructions field,
but this is not structured — it is a single text block, not keyed persona attributes.
```

**Detection hint:** Any Apex code or structured metadata field references when the question is about persona or tone configuration.

---

## Anti-Pattern 5: Treating AI Assist as a Runtime Enforcement Mechanism

**What the LLM generates:** Advice that once "AI Assist has approved the instructions, the agent will consistently follow them in production."

**Why it happens:** LLMs familiar with code analysis tools (linters, static analyzers) transfer the concept that "passing the analyzer = correct behavior at runtime." AI Assist is a design-time tool, not a runtime enforcer.

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
