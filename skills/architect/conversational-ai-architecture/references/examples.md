# Examples — Conversational AI Architecture

## Example 1: Retail Bank Deploying Agentforce with Einstein Bot IVR Front-End

**Context:** A retail bank has an existing Einstein Bot handling IVR navigation and identity verification on the phone channel. The bank wants to add Agentforce to handle account inquiry requests that require natural-language reasoning (e.g., "why is my balance lower than expected after my last transaction?") without replacing the bot's DTMF routing and identity verification logic.

**Problem:** Without a structured handoff pattern, the Agentforce agent receives transfers with no knowledge of the verified customer identity or the request category collected by the bot. The customer must re-verify identity and re-state their request. Average handle time increases. If the Agentforce agent cannot resolve the issue and escalates to a human, the human agent also receives no prior context.

**Solution:**

The architecture uses three layers: Einstein Bot (IVR front-end) → Agentforce agent (reasoning layer) → human agent (escalation).

Einstein Bot configuration — transfer attributes populated before handoff:

```
// Einstein Bot "Transfer to Agent" action — transfer attribute mapping
Transfer attribute: verified_account_id   → Bot variable: {!VerifiedAccountId}
Transfer attribute: intent_category       → Bot variable: {!DetectedIntentCategory}
Transfer attribute: ivr_selections        → Bot variable: {!IVRSelectionPath}
Transfer attribute: bot_conversation_id   → Bot variable: {!BotSessionId}
```

Agentforce agent — an Action defined to consume transfer attributes at session start:

```
// Agentforce Action: InjectBotTransferContext
// Invoked automatically when session receives transfer attributes
// Injects verified_account_id into agent working context
// Sets account lookup scope to the verified account only
// Prepends summary to conversation context:
//   "Customer identity verified via IVR. Account ID: [verified_account_id].
//    Request category: [intent_category]. IVR path: [ivr_selections]."
```

Omni-Channel routing rule:

```
// Routing rule: EscalationFromBot
// Condition: incoming transfer has attribute intent_category = "account_inquiry"
// Route to: Agentforce agent queue "AccountInquiryAgent"
// Fallback: if Agentforce unavailable, route to human queue "AccountServicing"
```

When the Agentforce agent determines human escalation is required, it invokes a human handoff Action that writes the full conversation transcript to the Case record and assigns the Omni-Channel work item to the human queue with the transcript attached.

**Why it works:** The explicit transfer attribute mapping ensures no context is lost at each layer boundary. The Agentforce agent's reasoning starts with a known-verified identity, eliminating re-verification. The human agent receives the full transcript from both the bot and the Agentforce agent, so no re-collection is needed at escalation. The Einstein Bot investment (identity verification flow, DTMF routing) is preserved without modification.

---

## Example 2: Multi-Topic Agentforce Deployment with Scope-Bounded Topic Descriptions

**Context:** A telecommunications company deploys a single Agentforce agent to handle three business functions: billing inquiries, technical support, and account management. Initial testing shows the agent frequently routes billing questions to technical support and vice versa.

**Problem:** The initial topic descriptions are written in broad terms:

```
// WRONG — Billing topic description (too broad, overlaps with Account Management)
"Help customers with questions about their bill, charges, account balance,
payment methods, and any financial aspects of their account."

// WRONG — Account Management topic description (overlaps with Billing)
"Assist customers with managing their account, including payment information,
account details, and service changes."
```

The phrase "payment methods" and "payment information" appears in both descriptions. The Atlas Reasoning Engine cannot distinguish which topic owns a request like "I need to update my payment method." Routing becomes inconsistent.

**Solution:**

Rewrite each topic description with three explicit parts: what is in scope, example request types, and explicit exclusions.

```
// CORRECT — Billing topic description
"Handle requests about invoice charges and billing disputes only.
In scope: explaining specific line items on an invoice, disputing an incorrect charge,
requesting a bill adjustment or credit, understanding why a charge appeared.
Not in scope: changing payment methods (route to Account Management),
technical service issues causing unexpected charges (route to Technical Support),
or account upgrades and downgrades (route to Account Management)."

// CORRECT — Account Management topic description
"Handle requests to change account configuration and payment settings.
In scope: updating a stored payment method, changing a service plan or tier,
adding or removing a service add-on, updating contact or billing address.
Not in scope: disputing charges on an existing invoice (route to Billing),
troubleshooting service outages or equipment (route to Technical Support)."

// CORRECT — Technical Support topic description
"Handle requests about service quality, outages, and equipment problems.
In scope: diagnosing connectivity issues, troubleshooting equipment faults,
reporting or checking status of a service outage, requesting a technician visit.
Not in scope: billing or invoice questions (route to Billing),
changes to account configuration or plan (route to Account Management)."
```

Each description now explicitly names the other topics by function and excludes their scope. The Atlas Reasoning Engine has clear, non-overlapping prose for routing.

**Why it works:** The Atlas Reasoning Engine routes by semantic similarity between the incoming request and each topic description. When descriptions contain identical or near-identical phrases, routing is ambiguous. Explicit cross-exclusions in prose tell the reasoning engine which topic does not own a given request type, reducing ambiguity at boundaries. Adversarial testing on boundary requests ("update my payment method," "why did my bill change after a service issue") should be run after each description revision to confirm consistent routing.

---

## Anti-Pattern: Writing Utterance Lists in Agentforce Topic Descriptions

**What practitioners do:** Practitioners experienced with Einstein Bot design attempt to "train" Agentforce topics by adding lists of example utterances to the topic description field, following the Einstein Bot pattern:

```
// WRONG — Agentforce topic description written as utterance list
"Billing topic.
Example utterances:
- What is my balance?
- Why was I charged?
- I have a billing question
- Show me my invoice
- My bill is wrong
- Billing dispute
- Charge on my account"
```

**What goes wrong:** Agentforce topics have no utterance training pipeline. The Atlas Reasoning Engine reads the entire description as prose context at inference time. An utterance list is not structurally different from a prose description to the LLM — it is just a list of short phrases. This format does not improve routing accuracy and often degrades it by consuming description space with low-information fragments instead of precise scope-defining prose. The practitioner then believes the topic is "trained" and does not investigate description wording as a routing lever.

**Correct approach:** Write topic descriptions as precise prose stating what is in scope, what example request types look like, and what is explicitly out of scope. Treat the description as instructions to a reasoning model, not as training labels for a classifier.

```
// CORRECT
"Handle requests about invoice charges and billing disputes only.
In scope: explaining specific line items on an invoice, disputing an incorrect charge,
requesting a bill adjustment or credit, understanding why a charge appeared.
Not in scope: changing payment methods (route to Account Management),
technical service issues causing unexpected charges (route to Technical Support)."
```
