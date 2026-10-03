# LLM Anti-Patterns — Agentforce Tool Use Patterns

Common mistakes AI coding assistants make when authoring Agentforce tools.

## Anti-Pattern 1: Vague method labels

**What the LLM generates:** `@InvocableMethod(label='Get Order')` with no description.

**Why it happens:** LLMs default to minimum-viable annotations.

**Correct pattern:** Label + description that contrasts with neighboring actions: `label='Look Up Order (by order number)', description='Retrieve a specific order by its customer-facing order number. USE WHEN the user provides the order number. DO NOT use for listing — use List Recent Orders instead.'`

**Detection hint:** Method labels shorter than 4 words OR missing description.

---

## Anti-Pattern 2: Dumping full sObject in return

**What the LLM generates:**

```apex
public class Result {
    @InvocableVariable public Account account;
}
```

**Why it happens:** LLMs default to returning the whole thing "just in case".

**Correct pattern:** Return a purpose-built DTO with 3-6 primitive fields. Human-readable strings ("$149.99" not 149.99).

**Detection hint:** Return type is an sObject or sObject-typed `@InvocableVariable`.

---

## Anti-Pattern 3: Generic argument names

**What the LLM generates:** `@InvocableVariable public String id;` or `public String value;`.

**Why it happens:** LLMs transfer from generic REST patterns.

**Correct pattern:** Semantic names + explicit format: `@InvocableVariable(label='Order Number' description='...') public String orderNumber;`. The Apex Developer Guide examples separate annotation parameters with whitespace, not commas.

**Detection hint:** Variables named `id`, `value`, `input`, `data` with no context.

---

## Anti-Pattern 4: Missing `callout=true`

**What the LLM generates:** Action issues `Http.send()` but annotation omits `callout=true`.

**Why it happens:** LLMs author the annotation once and don't revisit when adding HTTP logic.

**Correct pattern:** `@InvocableMethod(label='...' callout=true)` whenever HTTP is involved. The Apex Developer Guide documents the modifier's effect in screen flows (transaction control when there is uncommitted work); declare it anyway so the same invocable is safe when a flow reuses it.

**Detection hint:** `HttpRequest` or `Http.send` inside an invocable without `callout=true`.

---

## Anti-Pattern 5: No soft-error field on return

**What the LLM generates:** Exception-only error handling; no `error` output field.

**Why it happens:** LLMs default to throw/catch.

**Correct pattern:** Report failures in an `error` output field and keep one result per input, in the same order. The Apex Developer Guide says to wrap results in an object that reports failures and to return the same number of results as inputs even if errors occur. Subagent instructions branch on `error`.

**Detection hint:** Return DTOs without an `error` or `status` field.

---

## Anti-Pattern 6: Monolithic multi-step action

**What the LLM generates:** `Cancel_And_Refund_And_Notify_Order(orderNumber)` — one action does three things.

**Why it happens:** LLMs minimize action count to reduce "clutter".

**Correct pattern:** Three actions, each independently callable. Agent composes.

**Detection hint:** Action names joining multiple verbs with "and" / "then".

---

## Anti-Pattern 7: Binary-encoding data in string fields

**What the LLM generates:** Base64-encoded blob passed in a `String` variable.

**Why it happens:** LLMs work around platform type limits with encoding hacks.

**Correct pattern:** If the data is too large for an action, store it and pass a reference (e.g., a `ContentDocumentId`).

**Detection hint:** Parameters named `base64` or `encoded` or larger than a few KB.

---

## Anti-Pattern 8: Un-grounded generation in Prompt Builder

**What the LLM generates:** Prompt Template with free-text prompt and no record inputs.

**Why it happens:** LLMs write the prompt first, then add inputs as an afterthought.

**Correct pattern:** Every Prompt Template should ground with at least one record field or retrieval result. Ungrounded templates are just chatbots.

**Detection hint:** Prompt Template with no Record Type input or zero field references.

---

## Anti-Pattern 9: Retrieval without no-results handling

**What the LLM generates:** Retrieval action returns `List<Result>`. On zero hits, returns empty list. Agent hallucinates.

**Why it happens:** LLMs don't think about empty-list edge cases in retrieval.

**Correct pattern:** Return a boolean `noResults` flag. Agent prompt: "If noResults is true, say 'I couldn't find that.'"

**Detection hint:** Retrieval actions without an explicit no-results marker.

---

## Anti-Pattern 10: Action description containing the exact user phrase verbatim

**What the LLM generates:** Description is "Use when user says 'cancel my order'."

**Why it happens:** LLMs pattern-match on training data that shows exact phrase matching.

**Correct pattern:** Description in terms of user intent, not exact phrases: "USE WHEN the user wants to cancel an order they've already placed."

**Detection hint:** Descriptions containing quoted user phrases.

---

## Anti-Pattern 11: Telling the author that output descriptions do not matter

**What the LLM generates:** Advice to spend effort only on the method description and input descriptions, because "outputs are not shown to the model".

**Why it happens:** Assistants generalize from function-calling APIs where only the call signature is described.

**Correct pattern:** Write output instructions that say what the value is and what the agent should do with it. Set "Show in conversation" on outputs the agent may repeat, and make sure at least one output has `copilotAction:isUsedByPlanner` set to `true`; the Metadata API reference says the planner returns random responses otherwise.

**Detection hint:** Blank output descriptions in `output/schema.json`, or checker rule TU-020.

---

## Anti-Pattern 12: Reusing a Flow-style invocable that takes collections or sObjects

**What the LLM generates:** An agent action wired to `run(List<List<Account>> accounts)` or a request class with `List<Id> recordIds`.

**Why it happens:** The invocable already exists for Flow, so reusing it looks efficient.

**Correct pattern:** Give the agent its own invocable with primitive request fields. The Generative AI guide (Spring '26) says custom actions that reference Apex or flows support only primitive data types and that collections aren't supported.

**Detection hint:** Checker rule TU-004 (collection-typed invocable variable) and TU-003 (generic Object).

---

## Anti-Pattern 13: Formatting the tool output for display inside the action

**What the LLM generates:** An action that returns pre-built HTML or Markdown tables so the agent "shows it nicely".

**Why it happens:** Assistants assume the action controls rendering.

**Correct pattern:** Return plain values and let the agent compose the reply. The Generative AI guide states that when you create a custom action you can't specify how the output appears; it is formatted automatically. When a custom UI is genuinely needed, use custom Lightning types, which the Agentforce Developer Guide documents for that purpose.

**Detection hint:** Output fields named `html`, `markdown` or `table`, or strings containing tags.

