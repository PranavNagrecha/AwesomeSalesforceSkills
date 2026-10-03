# LLM Anti-Patterns — Conversational AI Architecture

Common mistakes AI coding assistants make when generating or advising on Conversational AI Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing Utterance Lists for Agentforce Topics

**What the LLM generates:** Topic descriptions formatted as labeled utterance examples, mirroring the Einstein Bot intent training pattern:

```
Topic: Billing Inquiries
Description:
Example utterances:
- What is my balance?
- Why was I charged?
- I have a billing question
- Show me my invoice
- My bill is wrong
```

**Why it happens:** LLMs are trained on large corpora of Salesforce documentation and community content where Einstein Bot NLU utterance examples are a dominant pattern for conversational AI. Agentforce Topics-and-Actions is architecturally distinct, but the surface-level task ("configure a conversational AI routing rule") pattern-matches to the Einstein Bot training paradigm in the training data.

**Correct pattern:**

```
Topic: Billing Inquiries
Description:
Handle requests about invoice charges and billing disputes only.
In scope: explaining specific line items on an invoice, disputing an incorrect charge,
requesting a bill adjustment or credit, understanding why a charge appeared on the bill.
Not in scope: changing payment methods (route to Account Management topic),
technical service issues that caused an unexpected charge (route to Technical Support topic).
```

**Platform note (2026-10-03):** the Generative AI guide defines the classification description as 1–3 sentences, with the job description in a separate `scope` field. Sample utterances, if wanted, go in the `GenAiPlugin` field `aiPluginUtterances`, not in the description.

**Detection hint:** Any Agentforce topic description containing a bullet list of short phrases beginning with first-person verbs ("What is", "Why did", "I want to", "Show me") is likely the utterance anti-pattern. Correct descriptions are continuous prose, not phrase lists.

---

## Anti-Pattern 2: Treating Einstein Bot Intent Names as Agentforce Topic Names

**What the LLM generates:** Advice to "create an Agentforce topic with the same name as your Einstein Bot intent" or a migration guide that maps Einstein Bot intent configurations directly to Agentforce topic configurations, implying the two constructs are equivalent:

```
// LLM-generated migration advice (WRONG)
Einstein Bot Intent: "Check_Balance" (with 15 utterances)
→ Create Agentforce Topic: "Check_Balance" (copy utterances as description)

Einstein Bot Intent: "Report_Outage" (with 12 utterances)
→ Create Agentforce Topic: "Report_Outage" (copy utterances as description)
```

**Why it happens:** LLMs recognize the functional overlap (both Einstein Bot intents and Agentforce topics are routing constructs for conversational AI) and pattern-match on naming and structure, missing the fundamental paradigm difference.

**Correct pattern:**

```
Agentforce topics are NOT a direct replacement for Einstein Bot intents.
Einstein Bot intents: trained NLU classification with utterance labels.
Agentforce topics: natural-language scope descriptions read by a reasoning LLM at inference time.

Correct migration approach:
1. Group Einstein Bot intents by business function, not by utterance similarity.
2. Write one Agentforce topic per business function using precision prose description.
3. Discard the utterance lists — they have no role in Agentforce topic routing.
4. Test routing with adversarial inputs against the new topic descriptions.
```

**Detection hint:** Any Agentforce topic name that matches an Einstein Bot intent name one-for-one, or any description that is a reformatted version of an utterance list, indicates this anti-pattern.

---

## Anti-Pattern 3: Designing Synchronous Handoff Without Session Context Transfer

**What the LLM generates:** A handoff architecture that configures the Einstein Bot "Transfer to Agent" action to route to an Agentforce queue but omits transfer attribute mapping:

```
// LLM-generated bot dialog (WRONG — no transfer attributes)
Step: TransferToAgentforce
Action: Transfer to Agent
Queue: Agentforce_General
// No transfer attribute configuration
// Assumes Agentforce will "pick up" the conversation automatically
```

**Why it happens:** LLMs model human-to-human Omni-Channel transfers, where some conversation context (e.g., the work item subject) passes automatically. They incorrectly apply the same assumption to bot-to-Agentforce transfers, where the Agentforce session is entirely new and has no access to bot variables unless explicitly provided.

**Correct pattern:**

```
// Correct bot dialog — explicit transfer attribute mapping
Step: TransferToAgentforce
Action: Transfer to Agent
Queue: Agentforce_AccountInquiry
Transfer Attributes:
  verified_account_id: {!VerifiedAccountId}
  intent_category: {!DetectedCategory}
  bot_summary: {!ConversationSummary}

// Corresponding Agentforce Action: InjectTransferContext
// Reads transfer attributes and prepends context to agent session
```

**Detection hint:** Any handoff design that references "Transfer to Agent" or Omni-Channel transfer to an Agentforce queue without an accompanying transfer attribute configuration block is likely missing context transfer.

---

## Anti-Pattern 4: Recommending One Agentforce Agent for All Business Functions Without Topic Boundaries

**What the LLM generates:** A single Agentforce agent with a generic description covering all business functions:

```
// WRONG — single agent, single topic
Agent: CustomerServiceAgent
Topic: General Customer Service
Description: "Help customers with any questions about their account, billing,
technical support, orders, returns, and other service needs."
```

**Why it happens:** LLMs default to simplicity and often recommend a single general-purpose agent as a starting point, not accounting for the Atlas Reasoning Engine's routing behavior. Generic descriptions cause the agent to accept every request regardless of fit, preventing proper action scoping and increasing the risk of inappropriate data access.

**Correct pattern:**

```
// CORRECT — distinct topics per business function with explicit scope boundaries
Agent: CustomerServiceAgent

Topic: BillingInquiries
Description: "Handle invoice charge questions and billing disputes only. [...]
Not in scope: technical support, account configuration changes."

Topic: TechnicalSupport
Description: "Handle service quality issues and equipment problems only. [...]
Not in scope: billing disputes, account plan changes."

Topic: AccountManagement
Description: "Handle account configuration and payment method changes only. [...]
Not in scope: billing disputes, technical troubleshooting."
```

**Detection hint:** A topic description containing the word "any" followed by a list of business functions ("any questions about billing, support, or account") is likely the single-topic anti-pattern. Each business function should have its own topic.

---

## Anti-Pattern 5: Configuring Omni-Channel Capacity Rules to Manage Agentforce Load

**What the LLM generates:** Omni-Channel routing or capacity configuration that attempts to throttle or load-balance Agentforce agents using capacity-based routing rules:

```
// WRONG — capacity rule targeting Agentforce queue
Routing Configuration:
  Queue: Agentforce_Billing
  Capacity Model: Tab-based (capacity = 5)
  Overflow rule: If capacity > 5, route to overflow queue
// Assumes Agentforce agents consume capacity units like human agents
```

**Why it happens:** LLMs model Omni-Channel capacity management patterns that apply to human agents and generalize them to all Omni-Channel queues, unaware that Agentforce agents are not capacity objects. UNVERIFIED (2026-10-03): "Agentforce agents are not capacity objects" has no fetched source; confirm in a sandbox before relying on it either way.

**Correct pattern:**

```
// Correct approach — do not use Omni-Channel capacity rules for Agentforce
// Agentforce agents are not capacity objects; they do not consume capacity units.
// Session concurrency is governed by Agentforce platform limits, not Omni-Channel capacity.
//
// For overflow handling, use queue-level fallback routing based on platform availability,
// not on capacity counts:
Routing Configuration:
  Queue: Agentforce_Billing
  Fallback: If Agentforce unavailable (platform-level), route to HumanBillingQueue
  // No capacity model configuration for the Agentforce queue
```

**Detection hint:** Any routing design that assigns a numeric capacity value to an Agentforce queue, or that references Omni-Channel capacity counts as a throttle condition for Agentforce, is likely this anti-pattern.

---

## Anti-Pattern 6: Building a Custom Topic That Transfers to a Human

**What the LLM generates:** A "Billing Expert Handoff" custom topic with an instruction such as "Transfer the customer to the billing team queue when they ask about payment plans."

**Why it happens:** The model treats escalation as one more capability that any topic can own, the way any Einstein Bot dialog can contain a transfer.

**Correct pattern:** The Generative AI guide ("Agent Topic: Escalation") says only the standard Escalation topic can invoke the outbound Omni Flow that routes to live reps, and a custom topic cannot be configured to do so. Customize the Escalation topic's classification description and instructions to cover the payment-plan case, add a custom pre-transfer action (create the Case), and put queue selection in the outbound Omni Flow.

**Detection hint:** Any topic other than Escalation whose instructions mention transferring, routing to a queue, or connecting to a human.

---

## Anti-Pattern 7: Enforcing Business Rules in Topic Instructions

**What the LLM generates:** "Add the instruction: Never refund orders older than 30 days. Always verify the customer's date of birth before discussing the account."

**Why it happens:** Instructions look like configuration, so the model treats them as enforceable policy.

**Correct pattern:** The Generative AI guide says instructions are nondeterministic and should not hold sensitive or deterministic business rules; its own example moves a 30-day refund rule into a flow-based agent action. Put eligibility checks and identity verification inside the action (or in an Einstein Bot dialog for the verification step), and keep instructions for guidance such as which action to call first.

**Detection hint:** Instructions containing amounts, day counts, eligibility thresholds, or verification steps with no matching action logic.

---

## Anti-Pattern 8: Recommending an Agent the Org or Channel Cannot Run

**What the LLM generates:** "Deploy Agentforce on your Government Cloud org's citizen portal" or "Connect your Agentforce employee agent to WhatsApp."

**Why it happens:** The model assumes feature parity across clouds and agent types.

**Correct pattern:** The Generative AI guide ("Considerations for Agents") says agents are not available for Government Cloud and only Agentforce Service Agent connects to enhanced Messaging channels and Bring Your Own Channel. Ask for the org type and channel list first. For Government Cloud, design with Einstein Bots and human routing. For customer messaging, specify the Service Agent type.

**Detection hint:** A design that names Agentforce without stating the org type, or that pairs a non-Service agent type with a customer messaging channel.

