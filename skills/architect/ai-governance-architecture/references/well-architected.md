# Well-Architected Notes — AI Governance Architecture

## Relevant Pillars

All three pillars identified in the skill frontmatter apply directly. A fourth pillar (Reliability) has meaningful but secondary relevance.

- **Security** — The most critical pillar for this skill. AI governance is fundamentally a security and trust discipline. The Einstein Trust Layer provides prompt injection detection, toxicity filtering, PII data masking, and zero-data-retention guarantees. Policy-as-Code enforcement of topic guardrails and action allowlists enforces least-privilege principles for AI agents. BYOLLM routing through Trust Layer ensures that third-party model calls do not bypass Salesforce security controls. Security Well-Architected guidance applies at every layer: model access controls (Layer 1), prompt-level safety (Layer 2), audit log integrity and access controls (Layer 3), and documented human accountability (Layer 4).

- **Operational Excellence** — AI governance infrastructure must be observable, maintainable, and auditable over time. Policy-as-Code (topic guardrails, data masking rules, action allowlists) stored in version control and deployed through standard DevOps pipelines is a core Operational Excellence pattern — governance policy changes are reviewable, reversible, and traceable. Audit Trail export pipelines require operational monitoring (export job success/failure alerts). Model lifecycle approval workflows (Layer 1) require defined runbooks. Operational Excellence framing justifies treating governance as operational infrastructure, not a one-time setup activity.

- **Reliability** — The Audit Trail export pipeline is a reliability-sensitive component: if daily exports fail silently, compliance evidence is permanently lost when the 30-day native retention window closes. Reliability design for this skill includes export pipeline health monitoring, dead-letter queue or alerting for failed exports, and documented recovery procedures. Human override workflows in high-risk AI use cases also require reliability design — override paths must remain available even when primary AI features degrade.

- **Performance** — Secondary relevance. Trust Layer data masking and content classification add inference latency. For synchronous Agentforce interactions, this is generally acceptable and well within conversational UX tolerances. For high-volume batch AI processing, the masking and routing overhead should be benchmarked. Performance is not a primary design driver for AI governance architecture but should be included in non-functional requirements documentation.

- **Scalability** — Secondary relevance for most deployments. The Audit Trail export pipeline must scale to handle AI interaction volume growth — S3 + SIEM architectures handle this without Salesforce-side capacity planning. Policy-as-Code guardrails are metadata-driven and do not introduce scaling constraints. For orgs with very high Agentforce usage (millions of daily invocations), Data Cloud ingestion limits for Audit Trail data should be reviewed.

---

## Architectural Tradeoffs

**Trust Layer zero-data-retention vs. audit completeness:** Einstein Trust Layer's zero-data-retention guarantee means raw prompts are not stored on Salesforce LLM infrastructure. The Generative AI Audit Trail captures masked prompt metadata — not raw prompt text. For use cases where regulators require the actual prompt content (not just masked metadata), an external logging pipeline capturing prompts before masking is required. This trades off privacy (raw prompt exposure in audit logs) against compliance completeness. The correct resolution depends on the specific regulatory requirement: most frameworks accept masked metadata; some require verbatim logging.

**Centralized Policy-as-Code vs. agility:** Enforcing all AI governance policy changes through code review and deployment pipelines (Policy-as-Code) provides auditability and governance but slows iteration. Teams that need to rapidly update topic guardrails or agent behavior in response to production issues face deployment pipeline friction. The tradeoff is governance rigor vs. operational agility. A recommended middle path: topic guardrails in code review pipeline, but emergency override procedure documented for critical production issues, with post-incident code change required to formalize the override.

**Native Audit Trail (simpler) vs. SIEM integration (real-time):** Native Data Cloud Audit Trail provides a Salesforce-native review surface with no external dependency but has an hourly refresh cadence and 30-day retention. SIEM integration adds operational complexity and cost but provides real-time anomaly detection and long-term retention. For low-risk internal AI tools, native-only may be acceptable. For regulated industries or high-risk AI use cases, SIEM integration is required. Document this decision explicitly in the governance architecture rather than defaulting.

---

## Anti-Patterns

1. **Single-layer governance (Trust Layer only)** — Enabling Einstein Trust Layer and treating AI governance as complete. This leaves model lifecycle governance, long-term audit evidence, and responsible AI controls unaddressed. Well-Architected Security requires defense-in-depth; a single control layer is not defense-in-depth for AI risk. The 4-layer framework is the minimum viable defense-in-depth architecture for production AI governance.

2. **Audit evidence without export pipeline** — Relying on native 30-day Generative AI Audit Trail retention as the audit evidence store for regulated use cases. When a regulatory inquiry arrives 12 months after an AI-assisted decision (as is common in financial services), the audit evidence is gone. Well-Architected Reliability requires that compliance-critical data is durable beyond the platform's default retention window. Designing without an export pipeline is a reliability failure mode for compliance evidence.

3. **BYOLLM integration without routing governance** — Adding BYOLLM integrations as direct Named Credential callouts to external LLM providers without routing through Trust Layer or documenting the audit gap. Each unrouted BYOLLM integration is a silent compliance hole — the Audit Trail shows no record of those interactions. Well-Architected Security requires that all AI data flows are inventoried and governed; undocumented external LLM callouts violate inventory completeness.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Agent Development Lifecycle — https://architect.salesforce.com/decision-guides/agent-development-lifecycle
- Salesforce Generative AI Audit Trail (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.generative_ai_audit_trail.htm
- Einstein Trust Layer overview — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
