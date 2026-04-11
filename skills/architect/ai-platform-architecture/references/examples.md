# Examples — AI Platform Architecture

## Example 1: Tiered Model Assignment for a Financial Services Agentforce Deployment

**Context:** A financial services firm is deploying three Agentforce agents: a Loan Status Agent (accesses loan account records including SSNs and account numbers), an Internal Knowledge Agent (accesses only internal policy documents with no PII), and a Case Routing Agent (accesses case records with customer names and contact details). The architecture team must select models for each agent before any configuration begins.

**Problem:** Without a tiered model strategy, the default approach is to assign all agents to the same model alias. If the team selects a BYOLLM endpoint for its larger context window without checking its data handling terms, the Loan Status Agent routes SSNs and account numbers to an external provider without ZDR guarantees. If the team selects the Salesforce Default model for all agents, the Internal Knowledge Agent is unnecessarily constrained by the 65,536-token masking limit even though it never handles PII.

**Solution:**

```
Model Tier Assignment Matrix — Financial Services

Agent Role           | Data Sensitivity | Model Tier Assignment          | ZDR Basis
---------------------|-----------------|-------------------------------|-----------------------------
Loan Status Agent    | PCI + PII (SSNs,| Salesforce Default Model       | Salesforce contractual ZDR
                     | account numbers)|                               | with external LLM providers
Case Routing Agent   | PII (names,     | ZDR-confirmed partner model    | Salesforce-negotiated ZDR
                     | contact info)   | (confirmed via Model Builder   | agreement confirmed in
                     |                 | listing)                      | Model Builder
Internal Knowledge   | Internal (no PII| BYOLLM with larger context     | Provider terms reviewed;
Agent                | or PCI)         | window                         | no sensitive data in scope

Decision record: BYOLLM approved only for Internal Knowledge Agent after confirming
provider does not retain prompts for training and does not log prompt content.
```

**Why it works:** Each model assignment is derived from the data classification of that specific agent's touchpoints, not from a uniform platform preference. The Loan Status and Case Routing agents are protected by verified ZDR. The Internal Knowledge Agent gets the larger context window it needs without subjecting the platform to unnecessary compliance risk. Model Builder alias per agent role prevents a shared alias change from silently affecting all three agents.

---

## Example 2: Supervisor/Specialist Topology for an Enterprise Service Agent

**Context:** A B2B SaaS company is building a customer-facing service agent that must handle three distinct workflows: checking order status (requires querying Order and OrderItem objects), retrieving troubleshooting knowledge (requires searching a Knowledge base), and creating or updating support cases. The team initially builds this as a single monolithic Agentforce agent with all three action sets.

**Problem:** The monolithic agent has 14 agent actions configured across three domains. Topic routing becomes unreliable — the agent intermittently treats a "check order" request as a knowledge search, returns knowledge articles when the user asks to create a case, and occasionally attempts to update a case when the user only asked about order status. The agent also has no clean ownership model — the Order team and the Knowledge team both need to update the same agent configuration.

**Solution:**

```
Supervisor/Specialist Topology

[User]
  |
  v
[Supervisor Agent]
  - System prompt: classify intent, route to specialist, synthesize final response
  - No domain-specific actions assigned
  - Topic config: three distinct topic descriptions with non-overlapping trigger keywords
  |
  +--[Order Specialist Agent]
  |    - Actions: GetOrderStatus, GetOrderLineItems
  |    - Input contract: { orderId: string, customerId: string }
  |    - Output contract: { orderStatus: string, lineItems: array, estimatedDelivery: date }
  |
  +--[Knowledge Specialist Agent]
  |    - Actions: SearchKnowledge, GetArticleContent
  |    - Input contract: { searchQuery: string, productCategory: string }
  |    - Output contract: { articles: array<{title, summary, url}> }
  |
  +--[Case Specialist Agent]
       - Actions: CreateCase, UpdateCase, GetCaseStatus
       - Input contract: { caseId?: string, accountId: string, subject?: string, description?: string }
       - Output contract: { caseId: string, caseNumber: string, status: string }

Model assignments:
  Supervisor: Salesforce Default (accesses no raw data directly)
  Order Specialist: Salesforce Default (accesses PII in Order records)
  Knowledge Specialist: BYOLLM with large context window (accesses non-sensitive knowledge articles only)
  Case Specialist: Salesforce Default (accesses PII in Case and Account records)
```

**Why it works:** Each Specialist has a single-domain scope with an explicit input/output contract. The Supervisor uses non-overlapping topic descriptions to route deterministically. Independent teams can update Specialist configurations without touching the Supervisor or other Specialists. Model assignments are differentiated by data sensitivity — the Knowledge Specialist benefits from a larger context window without imposing ZDR constraints on the whole topology.

---

## Anti-Pattern: Conflating Model Alias Selection with Platform Model Strategy

**What practitioners do:** Architects jump directly into Model Builder to pick a model alias and assign it to an agent without first classifying the data the agent accesses or confirming ZDR status. The selection is driven by model name recognition ("GPT-4o is more capable") or cost ("this model has lower pricing") rather than platform architectural constraints.

**What goes wrong:** The architect selects a BYOLLM endpoint because it offers a 128,000-token context window. The agent is configured to ground against records containing SSNs and account numbers. In production, every agent interaction sends unmasked PII to the external provider because BYOLLM bypasses Trust Layer masking. The external provider's terms do not include ZDR. The organization has a compliance breach that is difficult to detect because the audit trail only captures what passes through the Salesforce LLM gateway — BYOLLM calls to external endpoints are not captured in the same audit trail.

**Correct approach:** Classify data sensitivity first. Assign model tiers based on classification. Confirm ZDR basis for any non-Salesforce-Default model. Treat model alias selection in Model Builder as the final step of a decision already made at the architecture level, not the first step.
