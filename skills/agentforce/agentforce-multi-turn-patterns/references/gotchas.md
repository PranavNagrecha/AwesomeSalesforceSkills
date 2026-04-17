# Gotchas — Agentforce Multi-Turn Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Session variables don't survive a topic exit unless scoped cross-topic

**What happens:** State captured in topic A disappears when the conversation enters topic B. The agent asks the user to re-provide the order number it already had.

**When it occurs:** Declaring session variables at topic-internal scope (default) when they should be cross-topic (e.g., `verifiedAccountId`).

**How to avoid:** At variable creation, explicitly mark cross-topic scope for any fact that should survive topic transitions. Document scope in the variable description.

---

## Gotcha 2: The LLM "forgets" mid-conversation as context fills

**What happens:** 10 turns into a conversation, the agent starts ignoring a fact the user stated in turn 2.

**When it occurs:** The LLM context window truncates the oldest turns as new turns are added. Anything not re-injected via session variables or tool returns falls off.

**How to avoid:** Store every persistent fact in a session variable. On each turn, include the accumulated session state in the prompt. Don't rely on the raw turn history.

---

## Gotcha 3: Two browser tabs from the same user = two concurrent sessions

**What happens:** User opens a second tab, and each tab has its own conversation state. Actions taken in one tab don't reflect in the other.

**When it occurs:** By design — Agentforce sessions are per-browser-session, not per-user.

**How to avoid:** Document this in user-facing help. For stateful work, write durable state to platform data (Case, custom object) instead of session variables so both tabs see the same record.

---

## Gotcha 4: "User correction" doesn't invalidate downstream session variables

**What happens:** User says "actually, change the order number to A7843". Agent updates `orderNumber` but `itemId` (resolved from the old order) is now stale.

**When it occurs:** Correction patterns that update one variable without cascading reset.

**How to avoid:** Design variable dependencies explicitly. When `orderNumber` is updated mid-flow, reset `itemId` and re-ask.

---

## Gotcha 5: Session timeout silently wipes state

**What happens:** User walks away for 30 minutes. On return, the agent has forgotten everything; the user must start over.

**When it occurs:** Session timeout is shorter than the user's expected resume window.

**How to avoid:** For long-running workflows (returns, complex tickets), persist critical session variables to a platform data record (e.g., a custom `Agent_Conversation__c`) on each significant turn. On resume, rehydrate from that record.

---

## Gotcha 6: Clarifying questions accumulate — one-shot is better than three-shot

**What happens:** Agent asks three clarifying questions in a row. User abandons the conversation.

**When it occurs:** Author treats each ambiguity independently and asks one question per ambiguity.

**How to avoid:** Batch ambiguities when possible: "To help you, I need to know: (1) your order number, (2) which item, and (3) the reason. You can include all three in one reply." Only ask one at a time when the batch would be too long or the second question depends on the first answer.

---

## Gotcha 7: Escalation doesn't carry context forward

**What happens:** Agent escalates to a human after 2 failed turns; human receives just the latest message with no history.

**When it occurs:** The escalation action only forwards the current turn, not the full transcript + session variables.

**How to avoid:** On escalation, post the full transcript as a case comment or conversation log; pass critical session variables in the case description. The human should start with full context, not from scratch.

---

## Gotcha 8: Two topics with overlapping keywords cause routing instability

**What happens:** User says "cancel". Sometimes it routes to Cancel_Subscription; sometimes to Cancel_Order. Same input, different routes run-to-run.

**When it occurs:** Topic descriptions aren't discriminating. The LLM makes coin-flip decisions.

**How to avoid:** Rewrite topic descriptions so they're mutually exclusive. Use concrete examples in each topic's description. If ambiguity is unavoidable, add a router topic that asks: "Are you trying to cancel your subscription or an individual order?"

---

## Gotcha 9: Variables typed as `String` when they should be `Id` or `Date`

**What happens:** Agent stores an order number as a String, but later tries to use it in a SOQL filter requiring an Id. Runtime error.

**When it occurs:** Weakly-typed session variables without explicit type enforcement.

**How to avoid:** Use the most restrictive type possible (Id for record references, Date for dates). Validate via an Apex action on variable-set if the agent can't set the type at capture time.

---

## Gotcha 10: Auto-summary of conversation history isn't a substitute for explicit state

**What happens:** Agentforce's built-in turn-history summarization compresses older turns. Facts the user stated early become paraphrased and lose precision.

**When it occurs:** Relying on the summarized history to preserve exact values (like an address or phone number).

**How to avoid:** Capture exact values into session variables at the moment they're stated. Never reconstruct them from summarized history.
