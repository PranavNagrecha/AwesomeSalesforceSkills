# Examples — Agentforce Guardrails

## Example 1: Customer-Facing Service Agent With Restricted Topics and Fallback Instruction

**Context:** A telco has deployed an Agentforce agent on their customer portal (Experience Cloud) to handle plan upgrades, billing inquiries, and tech support. After launch, conversation logs show the agent occasionally discussing competitor plans and engaging with off-topic requests (e.g., general technology advice). No restricted topics have been configured and the agent-level system instruction is minimal ("You are a helpful customer service agent.").

**Problem:** Without restricted topics or a fallback system instruction, the agent uses its base LLM knowledge to answer any question that does not match a configured topic, including competitor comparisons and out-of-scope advice. This creates regulatory and brand risk.

**Solution:**

```text
-- Agent-Level System Instruction (revised) --
This agent assists TelcoX customers with plan upgrades, billing inquiries, and technical support for TelcoX services only.

If a user's request does not match any of these topics, respond exactly:
"I can only assist with TelcoX plan, billing, and technical support questions.
For other inquiries, please call our support line at 1-800-555-0100."

Do not provide information about competitor products, pricing, or promotions.
Do not provide general technology advice unrelated to TelcoX services.
Maintain a professional and courteous tone at all times.

-- Restricted Topic Entries --
Subject: "Competitor products, pricing, and promotions"
Refusal response: "I'm only able to help with TelcoX services. For competitor information, please visit their websites directly."

Subject: "General technology advice unrelated to TelcoX products"
Refusal response: "I can only assist with questions about TelcoX services. For general tech support, please consult a specialist."
```

**Why it works:** The fallback system instruction handles all post-classification gaps — requests that do not match any topic. The restricted topic entries operate pre-classification and block prohibited subjects before the LLM even attempts topic routing. Together, the two layers provide defense-in-depth: pre-classification blocking plus post-classification fallback.

---

## Example 2: Internal IT Helpdesk Agent — Escalation Topic With Omni-Channel Routing

**Context:** An IT helpdesk agent is deployed on an internal Salesforce org. It handles password resets, VPN issues, and hardware requests via configured topics. The agent is expected to escalate to a human IT specialist when issues are complex or when the user explicitly requests human help. The project team configured the Escalation topic and set a pre-handoff message but did not complete the Omni-Channel queue setup. In testing, users see "Connecting you to a specialist..." but no conversation ever arrives in the Omni-Channel queue.

**Problem:** The Escalation topic requires a live Omni-Channel routing destination. Without a valid queue or flow assignment, the topic technically fires and shows the pre-handoff message, but the handoff call silently fails. No error is surfaced.

**Solution:**

```text
-- Omni-Channel Setup Checklist --
1. Setup > Omni-Channel Settings: Enable Omni-Channel [CONFIRMED]
2. Setup > Queues: Create "IT Specialist Queue" with IT specialist members assigned [DONE]
3. Setup > Omni-Channel Flows or Routing Configurations:
   - Create routing config "IT Escalation Routing" with queue = IT Specialist Queue
   - Capacity model: Tab-based, capacity per agent = 3
4. Agent Setup > Escalation Topic:
   - Routing type: Queue
   - Routing destination: IT Specialist Queue
   - Pre-handoff message: "Connecting you to an IT specialist. Average wait time is 2 minutes."
5. Test: Initiate escalation in sandbox -> confirm conversation appears in Omni-Channel
   supervisor panel and is accepted by a test agent -> PASSED

-- Topic filter applied to Escalation Topic --
No invocable actions are attached to the Escalation topic.
Password reset and hardware request actions are restricted to their respective topics only,
preventing the agent from invoking them mid-escalation.
```

**Why it works:** Completing the Omni-Channel configuration end-to-end (queue creation, routing config, and Escalation topic assignment) is the only way to make handoffs work. The topic filter ensures no automated actions fire during the escalation flow, which could create data issues if the user's session is being handed to a human.

---

## Example 3: Scope Field vs. Classification Description — Fixing Misrouted Topics

**Context:** An agent has two topics: "Returns and Refunds" and "General Inquiry". The General Inquiry topic Scope field contains the line: "Do not help with returns or refunds." Despite this, users asking about returns are sometimes routed to General Inquiry instead of Returns and Refunds, and the agent then provides refund-related information (because the base LLM knows about refunds even when the Scope says not to).

**Problem:** The practitioner added the restriction to the wrong field. Scope is read after topic selection. It cannot prevent a topic from being selected — only the Classification Description controls that. Because the Returns and Refunds topic's Classification Description is too vague, some return-related phrasings fall through to General Inquiry.

**Solution:**

```text
-- Returns and Refunds Topic (revised) --
Classification Description:
"Select this topic when the user mentions returning a product, requesting a refund,
exchanging an item, or asking about the return policy, return window, or restocking fees.
Also select this topic when the user says their order arrived damaged or incorrect."

Scope:
"This topic handles return initiation, refund status checks, and return policy information
for orders placed in the last 90 days. It does not process exchanges directly — direct the
user to the exchange request form. It does not override return policy exceptions."

-- General Inquiry Topic (revised) --
Classification Description:
"Select this topic for general questions about store hours, contact information, account
settings, and product availability. Do not select this topic for return or refund requests."

Scope:
"This topic addresses general informational questions. It does not initiate returns,
process refunds, or provide order-specific information."
```

**Why it works:** The Classification Description revision on Returns and Refunds adds specific phrasings that trigger correct routing. The General Inquiry Classification Description explicitly tells the LLM not to route return/refund requests here. Scope remains declarative post-selection guidance. The two fields now serve their distinct purposes.

---

## Anti-Pattern: Over-Relying on Topic Scope to Block Prohibited Subjects

**What practitioners do:** Write long Scope fields with prohibitions like "Do not discuss politics, religion, competitor products, medical advice, or legal advice" on every topic, expecting this to block those subjects.

**What goes wrong:** Scope fields are post-selection constraints. A user who asks about a prohibited subject may still be routed to a topic (because the Classification Description matched some part of their query), and the LLM may partially comply with the Scope prohibition or partially answer before the constraint activates. Scope-based prohibitions are unreliable because they depend on the LLM respecting them during action planning, not on a platform-level pre-classification block.

**Correct approach:** Add Restricted Topic entries for subjects that must never be discussed. Restricted topics operate as a pre-classification filter — the user's input is checked against restricted topic definitions before any topic is selected. Use the Scope field only for in-topic behavioral boundaries (what actions this topic will or will not take), not for cross-topic subject blocking.
