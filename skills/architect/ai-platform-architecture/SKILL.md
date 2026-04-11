---
name: ai-platform-architecture
description: "Use this skill when designing or evaluating the holistic Salesforce AI platform strategy: model tier selection (Salesforce Default vs BYOLLM vs zero-data-retention partner models), Trust Layer design decisions at the architecture level, and multi-agent Supervisor/Specialist orchestration topology. Trigger keywords: AI platform strategy, model selection strategy, Supervisor agent topology, multi-agent orchestration, Einstein LLM gateway, BYOLLM architecture, trust layer design, agentic platform design, model tier decision. NOT for individual agent action development, Trust Layer feature configuration steps, RAG grounding mechanics, or BYOLLM registration procedures (see agentforce/einstein-trust-layer, agentforce/rag-patterns-in-salesforce, agentforce/model-builder-and-byollm for those)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
triggers:
  - "which LLM should I use for Salesforce agents handling sensitive financial data"
  - "how do I design a multi-agent architecture with a supervisor agent in Salesforce"
  - "should I use Salesforce Default model or bring my own LLM for our Agentforce deployment"
  - "what are the architectural constraints of the Einstein Trust Layer that affect model selection"
  - "how do I structure agent topology for a complex enterprise Agentforce implementation"
tags:
  - ai-platform-architecture
  - model-selection
  - trust-layer-design
  - multi-agent-orchestration
  - supervisor-specialist-topology
  - byollm
  - einstein-llm-gateway
  - agentforce
inputs:
  - Salesforce org edition and add-ons provisioned (Agentforce licenses, Data Cloud, Einstein platform)
  - Data sensitivity classification for data accessed by agents (PII, PCI, PHI, proprietary)
  - Regulatory and compliance requirements (data residency, audit trail, zero-retention mandates)
  - Business capability scope — number and types of agent roles being designed
  - Existing LLM provider contracts or preferences for BYOLLM consideration
outputs:
  - Model tier selection recommendation with rationale (Salesforce Default vs BYOLLM vs zero-data-retention partner)
  - Trust Layer architectural constraints checklist affecting model and topology decisions
  - Multi-agent topology diagram (Supervisor/Specialist roles, routing rules, handoff contracts)
  - Decision table for model assignment per agent role based on data sensitivity
  - Review checklist for AI platform architectural sign-off
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# AI Platform Architecture

This skill activates when a practitioner needs to make holistic platform-level architecture decisions for Salesforce AI: which model tier to assign to which agent roles, how to design the Einstein Trust Layer constraints into the architecture from the start, and how to structure multi-agent Supervisor/Specialist topologies that are operationally maintainable at enterprise scale. It is intentionally distinct from skills covering individual feature configuration or grounding mechanics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify data sensitivity across all agent touchpoints.** The most consequential architectural decision — which model tier to use — is driven by whether the data accessed by the agent requires zero-data-retention guarantees. Classify all CRM objects, fields, and external data sources the agents will ground against before selecting any model.
- **Confirm Agentforce and Data Cloud provisioning.** Multi-agent orchestration and Trust Layer audit trail both require specific license provisioning. Supervisor agents require an Einstein Agent license tier that enables orchestration. Data Cloud is required for audit trail and for dynamic grounding via Data Cloud Data Streams.
- **The most common wrong assumption:** Practitioners conflate model selection (choosing which model alias is assigned in Model Builder) with platform model strategy (deciding when and why to use Salesforce Default vs BYOLLM vs a zero-data-retention partner model). These are different decisions at different abstraction levels — one is a configuration step, the other is an architectural constraint that shapes the entire platform design.
- **Non-negotiable Trust Layer constraints:**
  - When data masking is active, the context window is hard-capped at 65,536 tokens. This is an architectural constraint, not a tunable parameter.
  - Zero data retention is enforced at the LLM gateway for all requests routed through Salesforce Default models. Third-party models accessed via BYOLLM do not automatically inherit ZDR — the ZDR guarantee must be independently confirmed with the provider.

---

## Core Concepts

### Model Tier Selection Strategy

Salesforce exposes three model tiers through Model Builder and the Agentforce platform:

1. **Salesforce Default Models** — Salesforce-hosted or Salesforce-contracted models (including OpenAI enterprise API integrations) that route through the Einstein Trust Layer. These models carry Salesforce's zero-data-retention contractual guarantee. They are the correct choice when you need ZDR guarantees managed by Salesforce and when the 65,536-token context window (with masking active) is sufficient.

2. **BYOLLM (Bring Your Own LLM)** — Models registered in Model Builder that connect to an external LLM provider endpoint via a custom configuration. BYOLLM bypasses the Salesforce LLM gateway for the actual inference call. **Critically: BYOLLM models do not automatically receive Trust Layer data masking or ZDR guarantees.** An architect must independently confirm ZDR and data handling terms with the external provider and configure any masking upstream. BYOLLM is appropriate when a provider's specific capabilities, pricing, or contractual relationship are required, and when the architect has independently validated the provider's data-handling posture.

3. **Zero-Data-Retention Partner Models** — A growing set of third-party models listed in Model Builder that Salesforce has pre-negotiated ZDR agreements with (distinct from Salesforce Default models). These offer ZDR guarantees with provider diversity. As of Spring '25, check the current Model Builder listing for which partner models carry Salesforce-negotiated ZDR.

Model tier selection is an architectural decision, not a preference. Routing sensitive data through a BYOLLM endpoint without independently verified ZDR creates an unacceptable compliance exposure.

### Trust Layer Design Constraints

The Einstein Trust Layer enforces constraints that must be treated as hard architectural inputs rather than late-stage configuration choices:

- **65,536-token context limit when masking is active.** Multi-step agent workflows that chain large grounded contexts can exceed this limit. Architecture must account for context budget across the full Supervisor/Specialist conversation chain, not just individual agent turns.
- **Data masking for Agentforce agents is disabled by default as of Spring '25.** An architecture that relies on masking for agent prompts must explicitly verify this capability is enabled and available for the target Salesforce release.
- **ZDR applies at the LLM gateway, not at the prompt level.** Masking intercepts PII before it reaches the LLM gateway. ZDR prevents the LLM provider from retaining what does arrive. Both controls are required for comprehensive data protection — neither alone is sufficient.
- **Trust Layer does not apply to agent-to-agent communication by default.** In a multi-agent topology, messages passed between a Supervisor agent and Specialist agents pass through platform routing. The Trust Layer audit trail covers the external LLM calls, not necessarily intermediate orchestration messages.

### Multi-Agent Supervisor/Specialist Topology

The Agentforce platform supports a Supervisor/Specialist multi-agent pattern documented in the Enterprise Agentic Architecture and Design Patterns guide (Salesforce Architects):

- **Supervisor Agent** — Receives the user intent, decomposes it into subtasks, routes subtasks to appropriate Specialist agents, and synthesizes results. The Supervisor does not execute domain-specific actions directly.
- **Specialist Agents** — Execute scoped capabilities (e.g., an Order Management Specialist, a Knowledge Retrieval Specialist). Each Specialist has a focused action set and topic configuration.
- **Handoff contracts** — The inputs and outputs between Supervisor and Specialist must be explicitly designed. Ambiguous handoffs cause routing failures or hallucinated responses when the Specialist lacks expected context.
- **Model assignment per agent role** — The Supervisor and each Specialist can be assigned different models. A Specialist handling financial transactions should be assigned a model with verified ZDR. A Specialist handling only non-sensitive internal knowledge retrieval may use a higher-context, lower-cost model. Model assignment is an architectural choice, not a default.

---

## Common Patterns

### Pattern: Tiered Model Assignment Based on Data Sensitivity

**When to use:** When deploying multiple Agentforce agents with different data access profiles in the same org — common in enterprise deployments where one agent handles HR, another handles financial records, and another handles internal knowledge retrieval.

**How it works:**
1. Classify the data sensitivity for each planned agent role (PII, PCI, proprietary, non-sensitive).
2. For agents accessing sensitive data: assign only Salesforce Default models or ZDR-confirmed partner models. Document the ZDR basis.
3. For agents accessing non-sensitive, high-volume data: evaluate whether a BYOLLM with larger context window is appropriate, after independently confirming provider data handling.
4. Capture the model assignment rationale in the architecture decision record alongside each agent's data access scope.
5. Configure Model Builder to enforce the assignment — do not rely on default model inheritance.

**Why not use a single model for all agents:** A uniform model assignment means the most restrictive constraint (ZDR, 65,536-token context with masking) applies even to agents that don't need it, restricting throughput and context budget unnecessarily. Conversely, using a permissive BYOLLM uniformly exposes sensitive agents to unverified data handling.

### Pattern: Supervisor/Specialist Topology with Explicit Handoff Contracts

**When to use:** When a user-facing agent must coordinate across multiple business domains — for example, a service agent that needs to check order status, retrieve knowledge articles, and update a case record in a single conversation.

**How it works:**
1. Define the Supervisor agent's scope: intent classification, routing logic, and response synthesis only. Do not assign domain-specific action sets to the Supervisor.
2. Design each Specialist with a single-domain action set, a defined input schema (what context the Supervisor must pass), and a defined output format (what the Specialist returns to the Supervisor).
3. Configure routing rules in the Supervisor topic configuration that map intent signals to specific Specialist agent invocations.
4. Design the context budget: the combined context from Supervisor prompt + Specialist outputs + user history must remain under the 65,536-token limit if masking is active.
5. Test the handoff contracts explicitly — invoke each Specialist with edge-case inputs to confirm it handles missing or malformed context gracefully rather than hallucinating.

**Why not use a single monolithic agent:** A monolithic agent with all actions embedded in one agent topic configuration hits topic routing limits, produces unpredictable action selection at scale, and cannot be independently tested or updated by domain teams. Supervisor/Specialist enables independent agent lifecycle management.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agent accesses PII or PCI data | Use Salesforce Default model or ZDR-confirmed partner model; never BYOLLM without independent ZDR verification | ZDR guarantee must be contractually established; BYOLLM does not inherit Salesforce's ZDR agreement |
| Context window approaching 65,536 tokens with masking active | Reduce grounding scope per agent turn; shift to dynamic grounding with scoped retrievals instead of full-record injection | 65,536-token limit is a hard platform constraint; cannot be increased when masking is active |
| Complex multi-domain use case in one agent | Design Supervisor/Specialist topology with explicit handoff contracts | Monolithic agents degrade at scale; topology enables independent domain team ownership |
| Regulatory requirement for LLM interaction audit | Enable Trust Layer audit trail and confirm Data Cloud provisioning before any AI feature goes live | Audit trail is not retroactive; gaps before enablement cannot be backfilled |
| Need a model with larger context than Salesforce Default offers | Evaluate BYOLLM only for non-sensitive data agents after independently confirming provider ZDR and data handling terms | BYOLLM offers provider flexibility but loses platform-managed Trust Layer guarantees |
| Supervisor agent routing is producing incorrect Specialist handoffs | Review Specialist topic configuration descriptions — the Supervisor uses topic descriptions for routing; vague descriptions cause misrouting | Routing is LLM-driven based on topic descriptions; precision in topic wording is an architecture concern, not a configuration detail |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on AI platform architecture:

1. **Classify data sensitivity across all agent touchpoints** — Map every CRM object, field, and external data source each planned agent role will access. Assign a sensitivity tier (regulated, sensitive, internal, public) to each agent's data scope before any model or topology decisions.
2. **Select model tiers based on sensitivity classification** — Assign Salesforce Default or ZDR-confirmed partner models to all agents with regulated or sensitive data access. For non-sensitive agents, evaluate BYOLLM options only after independently confirming provider data handling. Document the basis for each assignment.
3. **Design the Supervisor/Specialist topology** — Define which agent is the Supervisor (routing + synthesis only), define each Specialist's scope and action set, and write explicit handoff contracts specifying input schema and output format for each Supervisor-to-Specialist interaction.
4. **Calculate context budgets** — Sum the expected context consumption across the full conversation chain (Supervisor system prompt + user history + each grounded Specialist turn). Validate that the total stays within the 65,536-token constraint when data masking is active.
5. **Configure Trust Layer controls** — Confirm data masking is enabled for each applicable agent feature, audit trail is active with a retention period aligned to compliance requirements, and ZDR status is verified for each model tier assigned.
6. **Test topology and model assignments** — Run end-to-end tests with realistic data (including PII-format test data to validate masking) before going live. Test Specialist handoffs with edge-case inputs. Review audit trail records to confirm interaction logging is active.
7. **Document the architecture decisions** — Record model tier assignments with rationale, topology diagram, handoff contracts, and Trust Layer configuration state in a decision record. This is the foundation for ongoing compliance audits and future agent additions.

---

## Review Checklist

Run through these before marking AI platform architecture work complete:

- [ ] Data sensitivity classification documented for all agent data touchpoints
- [ ] Model tier selection rationale recorded for each agent role (Salesforce Default / ZDR partner / BYOLLM)
- [ ] ZDR status independently confirmed for any BYOLLM endpoint used by agents handling regulated data
- [ ] Supervisor/Specialist topology defined with explicit handoff contracts (input schema and output format per Specialist)
- [ ] Context budget calculated and verified under 65,536 tokens for masking-active scenarios
- [ ] Trust Layer data masking confirmed active for all applicable agent features
- [ ] Audit trail enabled with retention period set before any agents go live
- [ ] End-to-end topology tests run with realistic data including PII-format test data
- [ ] Architecture decision record created with model assignments, topology diagram, and Trust Layer configuration state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **BYOLLM does not inherit Trust Layer data masking or ZDR** — When a model is registered as BYOLLM in Model Builder, the LLM inference call goes directly to the external provider endpoint. The Einstein Trust Layer masking pipeline does not intercept this call. Practitioners who enable Trust Layer data masking at the org level assume it applies to all models, including BYOLLM — it does not. Sensitive data sent to a BYOLLM endpoint is sent unmasked unless the architect builds a separate interception layer.

2. **The 65,536-token context limit applies to the full conversation chain, not individual agent turns** — In a multi-agent topology, the Supervisor may aggregate outputs from multiple Specialists before synthesizing a response. Each Specialist turn consumes context budget. If masking is active, the total accumulated context across all turns in the conversation must remain under 65,536 tokens. Architects who plan context budgets at the individual agent level and ignore the chain accumulation will encounter runtime failures in production on complex multi-step conversations.

3. **Supervisor routing is LLM-driven and degrades with vague Specialist topic descriptions** — The Supervisor agent uses the topic configuration descriptions of available Specialist agents to determine routing. This classification is performed by the LLM, not by deterministic rules. Vague, overlapping, or similar-sounding Specialist topic descriptions cause the Supervisor to misroute requests in production. Topic description precision is an architecture concern that must be designed and tested explicitly, not treated as a configuration detail.

4. **Model Builder model alias changes propagate immediately and affect all agents assigned that alias** — A model alias in Model Builder is a shared reference. If an architect changes the underlying model for an alias (e.g., swapping from gpt-4o to a different model version), every Agentforce agent assigned that alias picks up the change immediately without a deployment step. This can silently change behavior across multiple production agents. Each agent role that has distinct behavioral or compliance requirements should be assigned a dedicated alias, not a shared one.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Model tier selection matrix | Table mapping each agent role to assigned model tier with data sensitivity classification and ZDR rationale |
| Supervisor/Specialist topology diagram | Visual or structured representation of agent roles, routing rules, and handoff contracts |
| Context budget calculation | Estimated token usage per agent turn and chain total, validated against the 65,536-token masking constraint |
| Trust Layer architecture checklist | Completed checklist confirming masking, ZDR, audit trail, and context limit compliance per agent role |
| Architecture decision record | Documented rationale for model assignments, topology choices, and Trust Layer configuration state |

---

## Related Skills

- agentforce/einstein-trust-layer — for detailed configuration steps of Trust Layer security controls (masking, ZDR verification, audit trail enablement)
- agentforce/model-builder-and-byollm — for BYOLLM registration procedures, model alias configuration, and Model Builder setup
- agentforce/rag-patterns-in-salesforce — for grounding mechanics, retrieval strategy, and RAG pipeline design within Agentforce
- architect/ai-agent-org-integration-architecture — for Salesforce org integration patterns when agents interact with external systems
