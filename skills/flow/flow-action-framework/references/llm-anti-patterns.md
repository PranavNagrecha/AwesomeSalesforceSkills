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

---

## Anti-Pattern 7: Emitting an `<actionCalls>` element without `flowTransactionModel`

**What the LLM generates:** A tidy-looking fragment with `name`, `label`, `actionName`,
`actionType`, `connector` and `inputParameters` — and no `<flowTransactionModel>`, because
the action "obviously runs in the current transaction".

**Why it happens:** Most published flow snippets in training data predate API 51.0, when
the field did not exist, and the field reads like tuning rather than structure.

**Correct pattern:** `FlowActionCall` marks `actionName`, `actionType` and
`flowTransactionModel` `Required` (`api_meta.txt` L68462-68466, L68479-68480). Emit
`<flowTransactionModel>CurrentTransaction</flowTransactionModel>` as the default and
justify anything else. The guide's own sample sets it even on `chatterPost` (L73259).

**Detection hint:** An `<actionCalls>` block whose child tags do not include
`flowTransactionModel`.

---

## Anti-Pattern 8: Reaching for `actionType` `flow` to call a subflow

**What the LLM generates:** "Add an Action element with `actionType` set to `flow` and
`actionName` set to your child flow's API name" — offered from inside a screen or
autolaunched flow.

**Why it happens:** `flow` is a real value in `InvocableActionType`, and the word matches
the user's question better than "subflow" does.

**Correct pattern:** From a `processType` of `Flow` or `AutolaunchedFlow`, the legal
mechanism is a `<subflows>` element (`FlowSubflow`), not an action call — the enum entry
for `flow` says so in its own sentence (`api_meta.txt` L68749-68753). Emit `<subflows>`
with `flowName`, `inputAssignments` and `outputAssignments`, and send the user to
`flow/subflows-and-reusability` for the contract.

**Detection hint:** `<actionType>flow</actionType>` in a document that also contains
`<processType>Flow</processType>` or `<processType>AutoLaunchedFlow</processType>`.

---

## Anti-Pattern 9: Promising that a fault connector catches an action timeout

**What the LLM generates:** "Wire a fault connector from the action so that timeouts and
errors both route to your logging path."

**Why it happens:** In most runtimes a timeout *is* an exception, and the LWC local-action
docs genuinely do route timeouts to the fault connector — so the generalisation looks safe.

**Correct pattern:** For an asynchronous `actionCalls` element these are two different
connectors: `faultConnector` fires "if the action call results in an error"
(`api_meta.txt` L68476-68477) and `timeoutConnector` "if an async action execution is timed
out" (L68532-68534, API 62.0+), enabled by `timeoutPathUsage`
(`EnableTimeoutPath`, L68536-68540, API 66.0+). Only for an LWC **local action** does the
guide state that a timeout takes the fault connector (`lwc_guide.txt` L8863). Say which
case you mean.

**Detection hint:** The word "timeout" in the same recommendation as "fault connector",
with no mention of `timeoutConnector` or `timeoutPathUsage`.

---

## Anti-Pattern 10: Inventing standard action names and their input parameters

**What the LLM generates:** A confident `<actionCalls>` for "Send Email" or "Submit for
Approval" with plausible input parameter names (`recipientEmail`, `emailBody`,
`objectId`) that do not exist.

**Why it happens:** The `InvocableActionType` enum is public and quotable, so the *type* is
easy to get right; the per-action parameter contracts live in the Actions Developer Guide,
which is a separate publication, so the *names* get reconstructed from memory.

**Correct pattern:** Only two standard actions' parameter names are demonstrated in the
Metadata API guide's sample flow — `chatterPost` with `text` and `subjectNameOrId`
(`api_meta.txt` L73249-73269). For anything else, describe it in the target org first:
`GET /services/data/vXX.X/actions/standard/<name>` or
`/actions/custom/<type>/<name>` (`api_rest.txt` L13762-13763, L13918-13919). Mark
reconstructed parameter names as unverified rather than shipping them silently — see the
marked `emailAlert` element in `references/metadata-examples.md` § 1.

**Detection hint:** An `<inputParameters><name>` for a non-Apex `actionType` with no
citation and no "confirm with a describe call" caveat.
