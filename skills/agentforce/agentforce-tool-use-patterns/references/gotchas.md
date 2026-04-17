# Gotchas — Agentforce Tool Use Patterns

Non-obvious platform behaviors that cause production problems.

## Gotcha 1: Label changes break existing topics

**What happens:** Renaming an action's `label` in the `@InvocableMethod` annotation can silently break topics that reference the action by label.

**When it occurs:** Refactoring Apex without checking which topics reference the action.

**How to avoid:** Topics should reference actions by API name, not label. Audit topic metadata for label references before renaming.

---

## Gotcha 2: `callout=true` is required for any HTTP work, even via Named Credential

**What happens:** Runtime `CalloutException: Callout from triggers are currently not supported` when the agent invokes the action.

**When it occurs:** Action does any `Http.send()` but `callout=true` is omitted.

**How to avoid:** Set `callout=true` whenever the action touches HTTP. This also changes which Flow contexts can call the action.

---

## Gotcha 3: Output variable descriptions aren't shown to the LLM

**What happens:** Descriptions set on output `@InvocableVariable` fields don't improve LLM response quality — they're not part of the prompt.

**When it occurs:** Authors spend time on output descriptions expecting them to influence generation.

**How to avoid:** Focus description effort on: (a) the method-level description (routes selection), (b) input variable descriptions (drives arg correctness). Output descriptions are for human developers reading the metadata.

---

## Gotcha 4: External Service schema changes silently break actions

**What happens:** The external API changes its response schema. The Salesforce External Service definition is stale. The agent gets `null` back or hits a serialization error.

**When it occurs:** Partner APIs without versioning, or when the OpenAPI spec wasn't re-imported after a change.

**How to avoid:** Pin to versioned endpoints. Regenerate External Services on vendor schema changes. Monitor for deserialization failures.

---

## Gotcha 5: Retrieval returns zero results silently

**What happens:** Agent cites policy text that doesn't exist.

**When it occurs:** Vector search returns zero hits; the agent hallucinates rather than say "I don't know."

**How to avoid:** Return a sentinel `no_results=true` on zero hits. Agent prompt explicitly handles: "If no_results is true, reply 'I couldn't find that information in our policies — let me connect you with someone.'"

---

## Gotcha 6: Two actions with overlapping descriptions cause routing instability

**What happens:** LLM picks `Look_Up_Order` sometimes, `Search_Orders` other times, for the same user turn.

**When it occurs:** Description overlap without discriminating "USE WHEN / DO NOT use" clauses.

**How to avoid:** Pair actions with contrasting language. See Example 1 in `references/examples.md`.

---

## Gotcha 7: LLM passes the example value verbatim

**What happens:** Description says "e.g. A7842". LLM passes literal "A7842" when the user said "my last order."

**When it occurs:** Descriptions use concrete examples without framing.

**How to avoid:** Use contextual framing: "Format example only: A7842. The actual value should come from the user's turn." Or better, constrain via pattern validation in the action.

---

## Gotcha 8: Flow action errors don't propagate gracefully to the agent

**What happens:** Flow action faults. Agent responds with "An error occurred" — opaque, unhelpful.

**When it occurs:** Flow fault path not wired, or fault message isn't user-safe.

**How to avoid:** Every Flow action must have a fault path that returns a structured error message. The agent's topic prompt should handle the error field: "If error is set, apologize and offer alternatives."

---

## Gotcha 9: Prompt Template inputs silently truncate

**What happens:** A Prompt Template with `Case.Description` as input produces low-quality output for cases with 10,000-character descriptions.

**When it occurs:** Input exceeds the model's effective window for the template's prompt length.

**How to avoid:** Pre-summarize long inputs via an Apex action before passing to the Prompt Template. Alternatively, use a retrieval-based pattern instead of direct field injection.

---

## Gotcha 10: Action name ambiguity across namespaces

**What happens:** Managed-package action `mynamespace__Look_Up_Order` and an unmanaged action `Look_Up_Order` coexist. The agent picks wrong.

**When it occurs:** Partial migration from unmanaged to managed package.

**How to avoid:** Don't have two actions with the same local name. Either fully migrate or namespace the unmanaged side.

---

## Gotcha 11: Action `category` affects what the LLM sees

**What happens:** Action put in category "Utilities" doesn't surface for a user asking for a "customer" action.

**When it occurs:** Categories chosen for code organization, not LLM semantics.

**How to avoid:** Treat category as part of the prompt. "Customer Support" category surfaces for customer-related turns; "Utilities" for admin work. Use categories that match the user's mental model.
