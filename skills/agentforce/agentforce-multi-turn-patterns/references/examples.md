# Examples — Agentforce Multi-Turn Patterns

## Example 1: Multi-turn return request with state rollback

**Context:** A customer-support agent collects order number, item, and reason across 3 turns. In turn 3, the user corrects their order number. All downstream state must reset.

**Problem:** Naive implementations keep the old `itemId` (resolved from the wrong order), producing a broken return record.

**Solution:**

```
Turn 1 (user): "I want to return my order."
  session.orderNumber = null
  session.itemId = null
  session.reason = null

Turn 2 (user): "A7842"
  session.orderNumber = "A7842"
  → Look_Up_Order(A7842) → returns 2 items
  agent: "Which item — the Blue Scarf or the Wool Hat?"

Turn 3 (user): "actually my order is A7843"
  Decision: orderNumber changed; cascade-reset downstream.
  session.orderNumber = "A7843"
  session.itemId = null   // reset
  session.reason = null   // reset
  → Look_Up_Order(A7843) → returns 1 item
  agent: "Got it — A7843 has 1 item (Hoodie). Returning the Hoodie?"
```

**Why it works:** The variable dependency graph is explicit. When `orderNumber` changes, its dependents (`itemId`, `reason`) are reset. The agent doesn't carry over state that would produce a corrupt return.

---

## Example 2: Cross-topic account verification

**Context:** User starts in Support topic (verifies identity via case number) and later switches to Billing topic (which would normally require identity verification too).

**Problem:** Re-asking for verification feels broken; skipping it is a security hole.

**Solution:**

Declare `session.verifiedAccountId` at cross-topic scope when the Support topic completes identity verification. Billing topic's entry condition checks `session.verifiedAccountId != null`; if present, skip re-verification. If the Billing topic exits and a third topic opens beyond a short window (e.g., 10 minutes), force re-verification.

```
Support topic:
  - Collect caseNumber.
  - Look_Up_Case → returns accountId.
  - Verify_Account_Identity → sets session.verifiedAccountId (cross-topic).
  - session.verifiedAt = now (cross-topic).

Billing topic entry:
  - Check session.verifiedAccountId.
  - Check (now - session.verifiedAt) < 10 minutes.
  - If both pass: proceed. Else: re-verify.
```

**Why it works:** Verification survives the topic boundary but expires quickly enough to preserve security posture.

---

## Example 3: Two-strike escalation with transcript handoff

**Context:** Agent can't understand user's request after two tries.

**Problem:** Escalating without transcript makes the human agent start from zero — user abandons.

**Solution:**

```
Turn 1:
  User: "my thing broke"
  Agent: "Sorry, I want to help. Could you tell me which product or order you're asking about?"

Turn 2:
  User: "you know, the thing"
  Agent: "I'm not quite catching what you're referring to — one more try and I'll connect you with someone who can help. Is this about a recent purchase, a subscription, or something else?"

Turn 3:
  User: "never mind"
  Agent: "Let me connect you with a specialist who can help." [Escalate]

Escalation payload:
  - Full transcript (3 turns).
  - session.* (any captured facts — empty here).
  - Handoff reason: "two-strike escalation, user frustrated".
  - Assigned queue: Tier-2 Support.
```

**Why it works:** Bounded escalation prevents infinite looping. Transcript + session handoff means the human starts with context.

---

## Anti-Pattern: Asking three clarifying questions in a row

**What practitioners do:** Treat each ambiguity as an independent question and ask them serially.

**What goes wrong:** Users abandon mid-conversation; third-question response rate is < 40%.

**Correct approach:** Batch when possible. "To help with your return, I need three things: your order number, which item, and the reason." Get everything up front, parse into multiple session variables from one user turn.

---

## Anti-Pattern: Re-verifying identity on every topic transition

**What practitioners do:** Treat every topic as a fresh conversation and re-ask for identity.

**What goes wrong:** Users feel like the agent doesn't know them.

**Correct approach:** Cross-topic verification variable with a timed expiry. See Example 2.
