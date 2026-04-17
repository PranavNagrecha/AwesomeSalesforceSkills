# LLM Anti-Patterns — Agentforce Multi-Turn Patterns

Common mistakes AI coding assistants make when authoring Agentforce multi-turn conversations.

## Anti-Pattern 1: Treating the LLM context window as durable memory

**What the LLM generates:** Agent topic prompts that reference "earlier in the conversation" with no fallback when the turn is truncated out of context.

**Why it happens:** LLMs pattern-match from chat apps where the whole history is always in scope.

**Correct pattern:** Capture facts into explicit session variables. Reference `{!session.orderNumber}` in prompts, not "the order the user mentioned earlier."

**Detection hint:** Prompt text containing "previously", "earlier", "as you mentioned" without a session-variable reference.

---

## Anti-Pattern 2: One variable for everything

**What the LLM generates:** A single `session.context` variable that's a concatenated blob of everything the user has said.

**Why it happens:** LLMs default to string-concatenation patterns when they don't think about schema.

**Correct pattern:** One variable per atomic fact. `session.orderNumber`, `session.itemId`, `session.reason` — each typed, each scoped independently.

**Detection hint:** Session variables of type "Text(Long)" used for multi-field data.

---

## Anti-Pattern 3: No cascade reset on corrections

**What the LLM generates:** When authoring a correction handler, updates the changed variable but leaves dependents stale.

**Why it happens:** LLMs treat variables as independent; they miss implicit dependencies.

**Correct pattern:** Author a variable-dependency graph. When `orderNumber` changes, reset `itemId` and `reason`. Document dependencies in variable descriptions.

**Detection hint:** Correction handlers that update one variable without accompanying reset logic.

---

## Anti-Pattern 4: Re-asking for identity on every topic entry

**What the LLM generates:** Each topic starts with "First, can I have your account number?"

**Why it happens:** LLMs treat topics as independent scripts.

**Correct pattern:** Cross-topic identity variables with timed expiry. See the SKILL's Pattern 2.

**Detection hint:** More than one topic with an identity-verification as its first step.

---

## Anti-Pattern 5: Unbounded clarifying-question loops

**What the LLM generates:** "If user response unclear, ask for clarification" — no loop bound.

**Why it happens:** LLMs don't think about infinite loops in conversational design.

**Correct pattern:** Two-strike rule. After 2 consecutive unparseable turns, escalate to human. Document the strike count as an explicit session variable.

**Detection hint:** Topic logic that re-asks without incrementing a strike counter.

---

## Anti-Pattern 6: Synchronous identity lookup on every turn

**What the LLM generates:** Agent calls `Verify_User_Identity` at the start of every turn.

**Why it happens:** LLMs default to "verify-before-action" without caching.

**Correct pattern:** Verify once, cache in session variable, re-verify only on topic transitions or long pauses.

**Detection hint:** Topic logic that calls a verification action more than once per conversation.

---

## Anti-Pattern 7: Topic entry conditions that don't handle missing variables

**What the LLM generates:** Topic entry condition: `session.accountId != null`. If the variable was never set, the topic never activates.

**Why it happens:** LLMs don't think about null-handling in declarative conditions.

**Correct pattern:** Entry condition includes an alternate path: "if `session.accountId` is null, ask for it first, then proceed."

**Detection hint:** Topic entry conditions that reference session variables without a null-path.

---

## Anti-Pattern 8: Logging raw session variables to observability

**What the LLM generates:** `logger.info('session state: ' + JSON.serialize(session))`

**Why it happens:** LLMs default to logging whole objects.

**Correct pattern:** Log only keys and non-PII values. PII fields (accountId, phone, address) should be redacted or referenced by hash.

**Detection hint:** Log lines that serialize the entire session or include PII field names.

---

## Anti-Pattern 9: Escalation without transcript handoff

**What the LLM generates:** "Escalate to human queue" action without passing conversation context.

**Why it happens:** LLMs treat escalation as a "transfer" primitive without thinking about what the human needs.

**Correct pattern:** Escalation payload includes: full transcript, all session variables (redacted appropriately), handoff reason, suggested next actions. The human starts with context.

**Detection hint:** Escalation actions with only a `queueId` argument.

---

## Anti-Pattern 10: Using turn numbers in variable names

**What the LLM generates:** `session.turn3Response`, `session.turn4Answer`.

**Why it happens:** LLMs map conversation to array-like structures.

**Correct pattern:** Name by semantics: `session.orderNumber`, `session.returnReason`. Turn numbers are not stable — user corrections can renumber the conceptual turns.

**Detection hint:** Session variable names containing digits matching turn numbers.
