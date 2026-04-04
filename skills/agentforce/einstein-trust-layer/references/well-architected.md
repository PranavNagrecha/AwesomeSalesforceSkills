# Well-Architected Notes — Einstein Trust Layer

## Relevant Pillars

### Security

The Einstein Trust Layer is primarily a security control surface. Its relevance to the Security pillar is direct and comprehensive:

- **Data masking** ensures that PII and PCI data never reaches an external LLM in plain text, enforcing data minimization at the prompt level.
- **Zero Data Retention agreements** with LLM providers (e.g., OpenAI) bound the data processing relationship so that customer data is not retained or used for third-party model training.
- **Prompt defense** mitigates prompt injection attacks, which represent a new attack surface introduced by LLM integration.
- **Toxicity detection** acts as an output filter preventing harmful, biased, or inappropriate content from being surfaced to users.
- **Grounding controls** ensure that AI responses are anchored to organizational data with existing Salesforce permission model enforcement — the LLM cannot access data that the running user does not have access to through normal Salesforce security.

Security posture for generative AI is not binary. Each Trust Layer component addresses a distinct threat vector. A secure deployment requires all components to be configured, not just one.

### Reliability

The Trust Layer introduces reliability considerations that practitioners must account for in AI feature design:

- **Context window constraint with data masking active (65,536 tokens)** is a hard limit that can cause prompt failures at runtime if grounding is not bounded. Prompts that work without masking may fail after masking is enabled.
- **Masking policy propagation delay** — changes to masking configuration take a few minutes to take effect. Deployments that assume immediate consistency may encounter stale behavior in automated tests.
- **Toxicity detection false positives** can cause valid responses to be flagged and suppressed, resulting in unexpected user-facing errors in production. Prompt design must account for this.
- **Data 360 dependency** — if Data 360 is unavailable or misconfigured, audit trail functionality is unavailable. This can create a compliance gap during outages.

## Architectural Tradeoffs

**Data masking vs. response relevance:** Masking replaces entity names with placeholders before the LLM processes the prompt. The LLM generates its response using generic placeholders (e.g., `PERSON_0`) rather than the actual name. In most cases, the LLM maintains contextual relevance because placeholders preserve entity type. However, in edge cases where the LLM's response depends on the specific value (e.g., name-based cultural context), masking can reduce response quality. Evaluate response quality with masking active before go-live.

**Comprehensive grounding vs. context window budget:** More grounding context generally produces more accurate AI responses — but every additional record, knowledge article, or text field retrieved increases the token count. With data masking active, the ceiling is 65,536 tokens. Practitioners must make explicit decisions about which context to include, accepting that more grounding scope means higher failure risk if the budget is not managed.

**Audit trail completeness vs. data volume:** Audit trail records every AI interaction including the full prompt text. For high-volume deployments (thousands of agent interactions per day), this generates significant data volume in Data 360. The retention period configuration is a lever to manage storage cost, but shortening retention to reduce cost can conflict with compliance requirements. Size the retention period against both the compliance mandate and the expected interaction volume.

## Anti-Patterns

1. **Treating ZDR as a complete data protection strategy** — ZDR governs retention by the LLM provider after processing. It does not prevent PII from being transmitted to that provider in the first place. Organizations that rely solely on ZDR without enabling data masking are exposing PII to external model providers transiently, which may violate GDPR, HIPAA, or PCI-DSS obligations. The correct posture is ZDR + data masking as complementary controls.

2. **Enabling AI features before configuring the audit trail** — The audit trail is not retroactive. Interactions that occur before enablement are permanently unrecoverable for compliance purposes. Audit trail should be treated as a go-live prerequisite, not a post-deployment enhancement.

3. **Designing prompt templates without testing under data masking conditions** — Prompts are typically developed and tested in sandbox environments that may have Trust Layer in a different state than production. A prompt that passes all tests without masking may fail in production if masking is active and the context window is exceeded, or if the LLM's response quality degrades with heavily-masked input. Every prompt template must be validated with masking active before production deployment.

## Official Sources Used

- Einstein Trust Layer — Trust Layer Get Started page (Agentforce Developer Guide): https://developer.salesforce.com/docs/einstein/genai/guide/trust.html
- Data Masking — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/data-masking.html
- Inside the Einstein Trust Layer (Salesforce Developers Blog, architecture deep-dive): https://developer.salesforce.com/blogs/2023/10/inside-the-einstein-trust-layer
- The Einstein Trust Layer — Meet the Einstein Trust Layer (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/meet-the-einstein-trust-layer
- The Einstein Trust Layer — Follow the Prompt Journey (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/follow-the-prompt-journey
- The Einstein Trust Layer — Follow the Response Journey (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/follow-the-response-journey
- Configure LLM Data Masking Policies (Trailhead): https://trailhead.salesforce.com/content/learn/modules/llm-data-masking-in-the-einstein-trust-layer/configure-llm-data-masking-policies
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
