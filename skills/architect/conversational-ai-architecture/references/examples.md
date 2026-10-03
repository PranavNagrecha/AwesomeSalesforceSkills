# Examples — Conversational AI Architecture

## Example 1: Retail Bank Deploying Agentforce with Einstein Bot IVR Front-End

**Context:** A retail bank has an existing Einstein Bot handling IVR navigation and identity verification on the phone channel. The bank wants to add Agentforce to handle account inquiry requests that require natural-language reasoning (e.g., "why is my balance lower than expected after my last transaction?") without replacing the bot's DTMF routing and identity verification logic.

**Problem:** Without a structured handoff pattern, the Agentforce agent receives transfers with no knowledge of the verified customer identity or the request category collected by the bot. The customer must re-verify identity and re-state their request. Average handle time increases. If the Agentforce agent cannot resolve the issue and escalates to a human, the human agent also receives no prior context.

**Solution:**

The architecture uses three layers: Einstein Bot (IVR front-end) → Agentforce agent (reasoning layer) → human agent (escalation).

> UNVERIFIED (2026-10-03): the "Transfer to Agent" attribute mapping and the auto-invoked `InjectBotTransferContext` action below are illustrative pseudo-configuration. No fetched source documents either mechanism. The documented carrier is a `MessagingSession` field mapped to an agent context variable; Example 3 shows that design.

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

> Correction (2026-10-03): the Generative AI guide ("Parts of a Topic") defines the classification description as 1–3 sentences and gives the job description its own `scope` field. The multi-line blocks below mix both. In the org, put the first sentence in the classification description, the "In scope / Not in scope" sentences in `scope`, and any "route to" guidance in instructions. Example 3 shows the split.

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

**What goes wrong:** Agentforce topics have no utterance training pipeline. (Correction 2026-10-03: the `GenAiPlugin` metadata type does have an `aiPluginUtterances` field used to pick a topic at runtime. Sample utterances belong there, not in the description.) The Atlas Reasoning Engine reads the entire description as prose context at inference time. An utterance list is not structurally different from a prose description to the LLM — it is just a list of short phrases. This format does not improve routing accuracy and often degrades it by consuming description space with low-information fragments instead of precise scope-defining prose. The practitioner then believes the topic is "trained" and does not investigate description wording as a routing lever.

**Correct approach:** Write topic descriptions as precise prose stating what is in scope, what example request types look like, and what is explicitly out of scope. Treat the description as instructions to a reasoning model, not as training labels for a classifier.

```
// CORRECT
"Handle requests about invoice charges and billing disputes only.
In scope: explaining specific line items on an invoice, disputing an incorrect charge,
requesting a bill adjustment or credit, understanding why a charge appeared.
Not in scope: changing payment methods (route to Account Management),
technical service issues causing unexpected charges (route to Technical Support)."
```

---

## Example 3: Decision Record and Reference Architecture for a Utility Company Messaging Agent

**Context:** A regional electricity utility (Service Cloud Enterprise Edition, commercial cloud, not Government Cloud) runs an Einstein Bot on its web Messaging for In-App and Web channel. The bot verifies the customer with an account number and postcode, then hands off to human reps. The business wants an Agentforce agent to answer outage, billing and move-house requests after verification, with humans for payment-plan negotiation.

**Decision record (machine-readable form):**

```yaml
adr: CAI-007
title: Hybrid Einstein Bot verification with Agentforce Service Agent for open requests
status: proposed
date: 2026-10-03
context:
  org: Service Cloud Enterprise Edition, commercial instance (agents are not available for Government Cloud)
  channel: Messaging for In-App and Web (enhanced Messaging) -> messageType EmbeddedMessaging
  existing: Einstein Bot "Utility_Verify" performs account verification deterministically
decision:
  front_end: keep Einstein Bot for verification (deterministic, explainable step)
  reasoning_layer: Agentforce Service Agent (only agent type that connects to enhanced Messaging)
  human_handoff: standard Escalation topic -> outbound Omni Flow -> queue Payment_Plans
options_rejected:
  - option: Agentforce-only with verification in topic instructions
    reason: instructions are nondeterministic; verification must be enforced in an action or a bot dialog
  - option: custom "Payment Plan" topic that transfers to a rep
    reason: only the standard Escalation topic can route to live reps
metadata:
  agent: Bot (type ExternalCopilot, agentType AgentforceServiceAgent)
  planner: GenAiPlannerBundle (topics created inside the agent, Winter '26+)
  topics: GenAiPlugin (asset-library topics)
  actions: GenAiFunction
context_variables:
  - name: Verified_Account_Id
    maps_to: MessagingSession.Verified_Account_Id__c
    includeInPrompt: true
  - name: Verification_Method
    maps_to: MessagingSession.Verification_Method__c
    includeInPrompt: true
  - name: Postcode_Answer
    maps_to: none
    note: never stored on the session; Trust Layer masking is disabled for agents
limits_checked:
  actions_per_topic: "<= 15 recommended (largest topic has 6)"
  agents_per_org: "up to 20 (this is agent 2)"
licences:
  - Einstein for Service or Einstein Platform add-on with Agentforce enabled
  - agent user with the Agentforce Service Agent User permission set (Agent User license)
  - Agentforce usage billed under the "Agentforce: ASA" usage subtype (conversation windows)
consequences:
  - topic changes require agent deactivation; ship them as metadata in the Tuesday 06:00 window
  - channel fallback points at queue General_Service while the agent is inactive
```

**Topic design (one topic shown, split across the fields the platform defines):**

| `GenAiPlugin` field | Value for topic `Outage_Help` |
|---|---|
| `masterLabel` | Outage Help |
| `description` (classification, 1–3 sentences) | Answers questions about current or planned power outages at the customer's verified address, including restoration estimates. |
| `scope` | Your job is only to report outage status and restoration estimates for the verified account's premises and to log a new outage report. You aren't able to discuss bills, payments or moving house. |
| `genAiPluginInstructions` | Always use the Get Outage Status action before answering; never estimate a restoration time yourself. If the account is not verified, ask the customer to restart verification. |
| `aiPluginUtterances` | "Is there a power cut on my street?" / "When will my electricity be back?" |
| `genAiFunctions` | `Get_Outage_Status` (flow), `Log_Outage_Report` (flow) |
| `canEscalate` | false (only the standard Escalation topic escalates) |

**Escalation design:** the standard Escalation topic's classification description is edited to escalate when the customer asks for a payment plan, as well as when they ask for a human. A custom action `Create_Payment_Plan_Case` runs first, so the rep receives a Case. The topic carries no standard actions. `Bot.defaultOutboundFlow` names a fallback flow that routes to `General_Service` if the primary escalation is unavailable.

**Why it works:** the deterministic step stays in the bot, the agent type matches the channel, verified context crosses the handoff as session fields rather than as prompt text the bot invents, and the only escalation path is the one the platform supports. Each choice traces to a gotcha (8, 7, 3, 9, 5, 6 in `gotchas.md`).

