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

**Correct pattern:** Semantic names + explicit format: `@InvocableVariable(label='Order Number', description='...') public String orderNumber;`

**Detection hint:** Variables named `id`, `value`, `input`, `data` with no context.

---

## Anti-Pattern 4: Missing `callout=true`

**What the LLM generates:** Action issues `Http.send()` but annotation omits `callout=true`.

**Why it happens:** LLMs author the annotation once and don't revisit when adding HTTP logic.

**Correct pattern:** `@InvocableMethod(label='...', callout=true)` whenever HTTP is involved.

**Detection hint:** `HttpRequest` or `Http.send` inside an invocable without `callout=true`.

---

## Anti-Pattern 5: No soft-error field on return

**What the LLM generates:** Exception-only error handling; no `error` output field.

**Why it happens:** LLMs default to throw/catch.

**Correct pattern:** Pair a throw-path (fatal) with an `error` output field (recoverable). Agent prompts branch on `error`.

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
