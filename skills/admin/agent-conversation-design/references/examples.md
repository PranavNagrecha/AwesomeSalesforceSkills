# Examples — Agent Conversation Design

## Example 1: Expanding a Thin Utterance Set for a Returns Intent

**Context:** A retail company deployed an Einstein Bot with a "Start a Return" intent. The intent has 12 utterances, all written by the implementation team. The bot correctly handles "I want to return an item" but misses "how do I send something back", "return policy", and frustrated variants like "this is broken I need to return it". The fallback rate for this intent is 34%.

**Problem:** The utterance set was authored from scratch by consultants using formal, grammatically correct phrasing. Real users don't type that way. The 12 utterances provide no register or vocabulary coverage beyond the most obvious phrasings. The NLU model has no examples to generalize from for synonyms ("send back", "ship back", "exchange") or motivated-buyer language ("defective", "wrong size", "not what I ordered").

**Solution:**

Step 1 — Export first customer messages from the last 12 months for cases with subject "return", "refund", "exchange". Filter to cases where the bot attempted handling. Extract 180 raw phrasings.

Step 2 — Cluster by vocabulary:
- Cluster A — "return" verb: 60 utterances, mine 8 variants including typos ("retrun", "retun")
- Cluster B — "send back / ship back": 25 utterances, mine 5 variants
- Cluster C — "exchange / swap": 20 utterances, mine 5 variants
- Cluster D — product-state language ("broken", "defective", "wrong item", "damaged"): 30 utterances, mine 6 variants
- Cluster E — frustrated register ("I need to return this NOW", "just let me return it"): 15 utterances, mine 4 variants

Step 3 — Author manually:
- 5 error/typo variants: "retrun", "retun item", "reeturn", "cant return", "return????"
- 3 abbreviation variants: "want refund", "rtn pls", "need rma"

Final set: 51 utterances covering all five clusters.

**Why it works:** Case-mined phrasings are representative of what actual users type. Clustering by vocabulary ensures the model sees synonyms as equivalent signals, not distinct intents. The frustrated-register cluster is the most important addition: frustrated users are the ones most likely to escalate if the bot fails, so robust coverage of that register prevents fallback-driven escalations.

---

## Example 2: Rewriting a Single-Stage Fallback to Progressive Clarification

**Context:** A financial services company's Einstein Bot uses a single fallback message: "I'm sorry, I didn't understand that. Please try rephrasing your question." The bot has 8 intents. The fallback rate is 28%, and of those fallback sessions, 71% end in escalation without the user ever successfully self-serving.

**Problem:** The existing fallback gives no signal about what the bot *can* handle. Users who land in fallback don't know whether to rephrase, use different words, or just ask for a human. The message is apologetic but not actionable, and it doesn't reduce user effort.

**Solution:**

Replace the single fallback with a three-stage progressive clarification pattern:

```
[Fallback Stage 1 — first unmatched message in session]
"I want to make sure I point you in the right direction. Are you asking about one of these?
  • Checking your account balance
  • Recent transactions
  • Reporting a lost or stolen card
  • Something else"

[Fallback Stage 2 — second consecutive unmatched message]
"I'm still not finding a match for what you're asking. Would you like me to connect you with one of our account specialists who can pull up your account and help directly?"

[Fallback Stage 3 — user declines or no response within 90 seconds]
"Got it — I'll connect you now. An account specialist from our customer support team will be with you shortly. I'm passing along your message so they're ready to help."
```

**Why it works:** Stage 1 reduces cognitive load by presenting the most common topics as a multiple-choice shortcut. This alone deflects 30–40% of fallback sessions back into successful intent resolution. Stage 2 frames escalation as a service rather than a system failure. Stage 3 uses named destination language ("account specialist") and sets an expectation for the handoff, which reduces user frustration during wait time.

---

## Example 3: Writing Agentforce Topic Descriptions with Explicit Scope Boundaries

**Context:** An Agentforce deployment has two topics: "Billing Questions" and "Payment Help". Both topics are routing overlapping queries — a user asking "why is my bill so high" is sometimes routed to Billing Questions and sometimes to Payment Help. The inconsistency is caused by both topic descriptions being vague.

**Problem:**
- Billing Questions description: "Helps customers with billing-related questions"
- Payment Help description: "Assists with payment-related inquiries"

Both descriptions contain terms ("billing", "payment") that are semantically adjacent. The LLM's topic routing decision is probabilistic across these two descriptions, producing inconsistent routing for queries that sit at the boundary.

**Solution:**

Rewrite each description with explicit subject matter and exclusion clauses:

```
Billing Questions:
"Use for questions about invoice amounts, billing cycle dates, charges or fees on a bill, billing address updates, or requests for bill copies or statements. Do NOT use for payment method changes, payment processing issues, or refund requests — those belong in Payment Help."

Payment Help:
"Use for questions about how to make a payment, payment method updates (credit card, bank account), payment processing failures or errors, and refund status. Do NOT use for questions about invoice amounts, billing address, or statement copies — those belong in Billing Questions."
```

**Why it works:** Explicit exclusion clauses in the topic description give the LLM a disambiguation signal at the boundary. When a query like "why is my bill so high" arrives, the Billing Questions description now provides a stronger positive signal ("charges or fees on a bill") and the Payment Help description provides a negative signal ("do not use for invoice amounts"). The routing becomes deterministic for boundary cases.

---

## Anti-Pattern: Writing Escalation Copy That Uses Internal Queue Labels

**What practitioners do:** When configuring the transfer message for bot-to-agent handoff, practitioners use the internal Salesforce queue name directly: "Transferring to Tier2_Billing_EN_US_Q1."

**What goes wrong:** Users see "Transferring to Tier2_Billing_EN_US_Q1" in the chat window. This is meaningless to customers, erodes trust, and signals that the bot is exposing system internals. Worse, if the queue is renamed in the org (a common occurrence during reorganizations), the transfer message becomes stale and incorrect.

**Correct approach:** Always write escalation copy in user-facing terms derived from the team's function, not the internal queue identifier. "I'm connecting you with our billing support team" is durable (survives queue renames), meaningful to the customer, and sets correct expectations. Store the user-facing team name in the dialog script separately from the platform queue configuration so the copy can be reviewed and updated independently of the routing logic.
