# Well-Architected Notes — Conversational AI Architecture

## Relevant Pillars

- **Security** — Agentforce agents invoke Actions that execute with the org's record access model. An over-permissioned Action can expose records outside the customer's scope. The session context transfer from Einstein Bot to Agentforce must not carry PII in unencrypted transfer attributes beyond what the downstream agent requires. Human escalation transcripts written to Case records must be governed by the org's field-level security and record sharing model.
- **Performance** — Atlas Reasoning Engine routing latency is sensitive to topic description length and complexity. Excessively long topic descriptions increase inference time. Topic counts beyond roughly 20 on a single agent degrade both routing accuracy and response latency. Multi-agent orchestration trades some additional orchestration latency for improved per-specialist accuracy.
- **Scalability** — Agentforce session concurrency scales with platform capacity, not with Omni-Channel capacity configuration. Channel routing architecture must account for burst traffic scenarios where Agentforce session limits may be reached; fallback routing to human queues must be configured to handle overflow gracefully without dropping the conversation.
- **Reliability** — The hybrid Einstein Bot + Agentforce architecture introduces multiple handoff points, each of which is a failure boundary. A failed transfer attribute injection means the Agentforce agent operates without verified identity context — a reliability and potential security issue. Transfer paths must be tested end-to-end including failure scenarios (e.g., what happens if the Agentforce agent is unavailable at transfer time).
- **Operational Excellence** — Agentforce routing accuracy is not monitored automatically; there is no built-in alert for topic mis-routing. Operational excellence requires establishing a testing protocol for adversarial boundary inputs that is run on each topic description change. Conversation transcripts must be reviewed periodically to detect routing drift as natural-language usage patterns evolve.

## Architectural Tradeoffs

**Einstein Bot vs. Agentforce for structured flows:** Einstein Bot NLU is deterministic and auditable — the same input produces the same intent classification. Agentforce Atlas Reasoning Engine routing is probabilistic at inference time. For regulated industries or compliance-sensitive flows (identity verification, dispute initiation), Einstein Bot provides a stronger audit trail. The tradeoff is capability: Agentforce handles open-ended natural-language requests that Einstein Bot cannot reliably classify.

**Single agent vs. multi-agent orchestration:** A single agent with all topics in one place is operationally simpler — one deployment unit, one system prompt, one set of Actions to govern. But routing accuracy degrades as topic count grows, and a broad capability surface means more Actions are available for potential misuse. Multi-agent orchestration improves accuracy and reduces capability surface per sub-agent at the cost of additional orchestration latency and complexity in context propagation between agents.

**Hybrid architecture vs. full Agentforce:** A hybrid Einstein Bot + Agentforce deployment preserves existing Einstein Bot investments (IVR DTMF logic, identity verification flows, FAQ deflection) while adding Agentforce reasoning for complex requests. The tradeoff is increased handoff complexity: each transfer boundary must be explicitly managed. A full-Agentforce architecture is simpler architecturally but requires rebuilding structured flows that Einstein Bot handles more efficiently.

## Anti-Patterns

1. **Single broad-scope agent with no topic boundaries** — Deploying one Agentforce agent with a generic topic description covering all business functions prevents meaningful action scoping. The agent's capability surface becomes the union of all Actions across all functions, increasing the risk that a mis-routed request invokes an Action inappropriate for the context. Topic boundaries are the primary mechanism for scoping capability; removing them undermines both reliability and security.

2. **Skipping session context transfer mapping** — Treating the Einstein Bot to Agentforce handoff as an automatic context-passing operation leads to agents that start every escalated session with no customer context. This breaks the customer experience (requiring re-identification) and can introduce security issues (an unverified session proceeds as if identity verification occurred). Context transfer must be explicitly designed and tested — it does not happen automatically.

3. **Relying on Omni-Channel capacity management for Agentforce throttling** — Designing overflow and load-balancing logic using Omni-Channel capacity rules that target Agentforce queues produces configuration that is silently ignored at runtime. The overflow path is never triggered, meaning the architecture has no actual overflow protection for Agentforce. Capacity management for Agentforce must be designed against platform session limits, not Omni-Channel capacity objects.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Agentic Patterns and Implementation with Agentforce — https://architect.salesforce.com/decision-guides/agentic-patterns
- Enterprise Agentic Architecture and Design Patterns — https://architect.salesforce.com/decision-guides/enterprise-agentic-architecture
- The Seamless Handoff: Integrating Einstein Enhanced Bots with Agentforce Agents — https://developer.salesforce.com/blogs/2024/10/the-seamless-handoff-integrating-einstein-enhanced-bots-with-agentforce-agents
