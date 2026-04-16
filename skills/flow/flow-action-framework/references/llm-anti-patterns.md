# LLM Anti-Patterns — Flow Action Framework

Common mistakes AI coding assistants make when generating or advising on Flow Action Framework.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing a non-list Apex signature for Flow

**What the LLM generates:** `public static void doWork(String accountId)` annotated with `@InvocableMethod`, with the claim that Flow can call it directly with a text input.

**Why it happens:** Training data mixes generic “callable Apex” patterns with the specific invocable contract; single-argument primitives look ergonomic.

**Correct pattern:**

```
@InvocableMethod(label='...')
public static void doWork(List<Request> requests) { ... }
```

Use a single `List<Request>` parameter (or the documented list-oriented wrapper pattern). Flow’s Apex action maps into that contract.

**Detection hint:** Flag `@InvocableMethod` when the next method signature has no `List<` in the parameter list before the closing parenthesis.

---

## Anti-Pattern 2: Telling the user to “enable Apex” in Flow to see an action

**What the LLM generates:** Vague UI steps such as “turn on Apex in Process Automation settings” instead of class access, compilation, or annotation checks.

**Why it happens:** Over-generalized troubleshooting lists from other platforms.

**Correct pattern:** Verify the class compiles, `@InvocableMethod` is present on `public static` / `global static`, the running user has **Apex Class Access**, and the method is eligible for Flow exposure per the Apex Developer Guide.

**Detection hint:** Keywords like “enable Apex” without mentioning profile/permission set class access or compilation status.

---

## Anti-Pattern 3: Loop-first Flow for bulk Apex that already accepts collections

**What the LLM generates:** Pseudocode Flow: `Loop` over every record → inside loop, **Apex action** with scalar Id input on each iteration.

**Why it happens:** Imperative mental model; failure to connect Flow bulk interviews with invocable list design.

**Correct pattern:** Prefer one Apex action invocation with a collection-typed input matching `List<Wrapper>`; reserve loops for genuinely per-item branching or when Apex cannot be bulkified safely.

**Detection hint:** Phrases like “for each record, call the Apex action” without governor or invocable contract caveats.

---

## Anti-Pattern 4: Confusing External Service actions with Apex actions

**What the LLM generates:** Instructions to “add the REST operation as an Apex action” when the user registered an External Service and should drag the generated **External Service** action.

**Why it happens:** Both appear as invocable-shaped actions in the builder; naming overlap in casual language.

**Correct pattern:** If OpenAPI + Named Credential registration exists, use the External Service action family and mapping described in `flow-external-services`. Use Apex actions only for `@InvocableMethod` classes.

**Detection hint:** REST/OpenAPI/Named Credential context paired with “Apex action” as the only recommendation.

---

## Anti-Pattern 5: Omitting fault handling for Apex actions

**What the LLM generates:** A linear Flow diagram: Start → Apex action → End, with no fault connector or `$Flow.FaultMessage` capture.

**Why it happens:** Happy-path examples dominate training data; Flow fault paths are verbose to draw in text.

**Correct pattern:** Always include a fault path from the Apex action to logging, notification, or user-visible recovery, aligned with reliability requirements.

**Detection hint:** Apex action mentioned without “fault,” “FaultMessage,” or “fault connector.”

---

## Anti-Pattern 6: Directing deep Apex DTO work into this Flow skill only

**What the LLM generates:** Long Apex wrapper class listings when the user asked how to map variables in Flow Builder.

**Why it happens:** Single skill overreach; Apex is easier for the model to emit than Flow XML or step lists.

**Correct pattern:** Keep Flow wiring and action-choice guidance here; delegate `@InvocableVariable` ordering, tests, and service delegation patterns to `invocable-methods`.

**Detection hint:** Large Apex blocks in response to “how do I configure the Flow Apex action element.”
