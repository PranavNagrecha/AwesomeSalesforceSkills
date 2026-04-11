# Well-Architected Notes — AI Platform Architecture

## Relevant Pillars

- **Security** — The most critical pillar for AI platform architecture. Model tier selection determines whether PII and regulated data receive Zero Data Retention guarantees. Trust Layer masking must be an architectural input, not a post-configuration decision. BYOLLM models require independent security vetting since they bypass platform-managed data protection controls. The principle of least privilege applies to agent data scopes: agents should be grounded only against the minimal set of fields required to perform their function.

- **Reliability** — Multi-agent topologies introduce new failure modes: Supervisor routing errors, Specialist timeout or unavailability, and context budget overflows. Architecture must define fallback behaviors when a Specialist agent fails to return a valid response. Context budget calculations must be validated at architecture time — a context overflow at runtime produces a hard failure with no graceful degradation unless designed explicitly.

- **Scalability** — The 65,536-token context cap with masking active is a hard scalability ceiling. As organizations add more agent turns, richer grounding, and longer conversation history, context budget becomes a first-class scalability constraint. Supervisor/Specialist topology distributes complexity across independently scalable agents, but each Specialist still consumes tokens in the Supervisor's aggregation context. Dynamic grounding with scoped retrievals is the scalable alternative to static full-record grounding.

- **Performance** — Each agent turn in a multi-agent chain adds latency. A Supervisor invoking three Specialists sequentially has 3x the LLM round-trip latency of a single-agent design. Architecture should consider whether Specialist invocations can be parallelized and what acceptable end-to-end latency targets are. BYOLLM endpoints introduce provider-dependent latency variability that Salesforce Default models avoid.

- **Operational Excellence** — Shared model aliases are an operational risk: a single alias change affects all assigned agents simultaneously. Dedicated aliases per agent role enable controlled rollout of model changes. Audit trail coverage must be confirmed to include all agent types — BYOLLM gaps require compensating controls. Topology changes (adding a new Specialist) must be tested for Supervisor routing regression, not just for the new Specialist in isolation.

## Architectural Tradeoffs

**Single model vs. tiered model assignment:** A single model for all agents simplifies configuration but applies the most restrictive constraint (ZDR requirement, 65,536-token masking context) to agents that do not need it, or conversely applies a permissive model to agents that require stronger guarantees. Tiered assignment is more complex to govern but correctly scopes protections to the data risk of each agent.

**Monolithic agent vs. Supervisor/Specialist topology:** A monolithic agent with all capabilities is simpler to configure initially but degrades at scale: topic routing becomes unreliable with many topics, teams contend over a single configuration artifact, and the full agent must be retested when any capability changes. Supervisor/Specialist topology has a higher initial design cost (handoff contracts, routing precision) but provides independent lifecycle management, testability, and scoped compliance controls per Specialist.

**Salesforce Default models vs. BYOLLM:** Salesforce Default models provide platform-managed ZDR, masking, and audit trail with no additional integration work. BYOLLM provides provider diversity and potentially larger context windows but requires the architect to independently solve for data protection, ZDR confirmation, and audit logging. The tradeoff is architecture-managed safety vs. platform-managed safety.

## Anti-Patterns

1. **Uniform model assignment without data classification** — Assigning the same model alias to all agents without first classifying data sensitivity per agent. Results in either over-protection (applying ZDR constraints where unnecessary) or under-protection (routing regulated data through models without ZDR guarantees). The correct approach derives model assignment from data classification, not from a platform default or team preference.

2. **Treating Trust Layer controls as optional post-configuration** — Designing the agent topology and model assignments first, then adding Trust Layer controls as a compliance checkbox at the end. Because the 65,536-token context limit is a hard constraint that affects topology and grounding design, and because BYOLLM bypasses masking entirely, Trust Layer constraints must be architectural inputs from the start of the design process.

3. **Shared model aliases across agents with different compliance requirements** — Using a single Model Builder alias for all agents because it simplifies initial setup. Results in a shared blast radius when the alias is updated, and prevents granular rollback or staged rollout of model changes per agent role.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Agentforce Developer Guide — Trust Layer — https://developer.salesforce.com/docs/einstein/genai/guide/trust.html
- Enterprise Agentic Architecture and Design Patterns (Salesforce Architects) — https://architect.salesforce.com/design/decision-guides/agentic-architecture
- Model Builder and BYOLLM — Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/model-builder.html
- Einstein Trust Layer — Data Masking — https://developer.salesforce.com/docs/einstein/genai/guide/data-masking.html
- Salesforce Well-Architected Security — https://architect.salesforce.com/well-architected/secure
