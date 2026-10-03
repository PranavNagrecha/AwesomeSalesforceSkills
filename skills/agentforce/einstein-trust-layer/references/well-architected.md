# Well-Architected Notes — Einstein Trust Layer

## Relevant Pillars

### Security

The Einstein Trust Layer is primarily a security control surface. Its relevance to the Security pillar is direct and comprehensive:

- **Data masking** keeps detected PII and PCI data out of prompts sent to external LLMs, enforcing data minimization at the prompt level. It is disabled for Agentforce agents.
- **Zero Data Retention agreements** with LLM providers (e.g., OpenAI) bound the data processing relationship so that customer data is not retained or used for third-party model training.
- **Prompt defense** mitigates prompt injection attacks, which represent a new attack surface introduced by LLM integration.
- **Toxicity detection** acts as an output filter preventing harmful, biased, or inappropriate content from being surfaced to users.
- **Grounding controls** ensure that AI responses are anchored to organizational data with existing Salesforce permission model enforcement — the LLM cannot access data that the running user does not have access to through normal Salesforce security.

Security posture for generative AI is not binary. Each Trust Layer component addresses a distinct threat vector. A secure deployment requires all components to be configured, not just one.

### Reliability

The Trust Layer introduces reliability considerations that practitioners must account for in AI feature design:

- **Prompt size under masking**: earlier versions cited a 65,536-token cap with masking active; UNVERIFIED (2026-10-03), as the figure is not in the Generative AI guide. The guide documents an automatic summary when a prompt is too large, so test the largest prompts with masking on.
- **Masking policy propagation delay** — changes to masking configuration take a few minutes to take effect. Deployments that assume immediate consistency may encounter stale behavior in automated tests.
- **Toxicity detection false positives** can cause valid responses to be flagged and suppressed, resulting in unexpected user-facing errors in production. Prompt design must account for this.
- **Data 360 dependency** — if Data 360 is unavailable or misconfigured, audit trail functionality is unavailable. This can create a compliance gap during outages. Sandboxes cannot test masking configuration, Data Cloud grounding, or audit data at all.

## Architectural Tradeoffs

**Data masking vs. response relevance:** Masking replaces entity names with placeholders before the LLM processes the prompt. The LLM generates its response using generic placeholders (e.g., `PERSON_0`) rather than the actual name. In most cases, the LLM maintains contextual relevance because placeholders preserve entity type. However, in edge cases where the LLM's response depends on the specific value (e.g., name-based cultural context), masking can reduce response quality. Evaluate response quality with masking active before go-live.

**Comprehensive grounding vs. context window budget:** More grounding context generally produces more accurate AI responses — but every additional record, knowledge article, or text field retrieved increases the token count. Practitioners must make explicit decisions about which context to include, using measured `promptTokens__c` from the audit data rather than a fixed ceiling (the 65,536-token figure from earlier versions is UNVERIFIED).

**Audit trail completeness vs. data volume:** Audit trail records every AI interaction including the full prompt text. For high-volume deployments (thousands of agent interactions per day), this generates significant data volume in Data 360. The retention period configuration is a lever to manage storage cost, but shortening retention to reduce cost can conflict with compliance requirements. Size the retention period against both the compliance mandate and the expected interaction volume.

## Anti-Patterns

1. **Treating ZDR as a complete data protection strategy** — ZDR governs retention by the LLM provider after processing. It does not prevent PII from being transmitted to that provider in the first place. Organizations that rely solely on ZDR without enabling data masking are exposing PII to external model providers transiently, which may violate GDPR, HIPAA, or PCI-DSS obligations. The correct posture is ZDR + data masking as complementary controls.

2. **Enabling AI features before configuring the audit trail** — The audit trail is not retroactive. Interactions that occur before enablement are permanently unrecoverable for compliance purposes. Audit trail should be treated as a go-live prerequisite, not a post-deployment enhancement.

3. **Designing prompt templates without testing under data masking conditions** — Prompts are typically developed and tested in sandbox environments that may have Trust Layer in a different state than production. A prompt that passes all tests without masking may fail in production if masking is active and the context window is exceeded, or if the LLM's response quality degrades with heavily-masked input. Every prompt template must be validated with masking active before production deployment.

## Official Sources Used

Read for this revision (2026-10-03):

- Quickstart Your Einstein Generative AI Solution, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf. Einstein Trust Layer (ZDR policy, Designed for Trust, Response Journey, Region and Language Support, Trust Layer Limits in sandboxes, Set up Einstein Trust Layer, Large Language Model Data Masking, LLM Data Masking Considerations, Select What Data To Mask, Audit Trail, Verify Masked Data, Review Toxicity Scores); Einstein Generative AI Analytics (audit and feedback data types, billing, DMO field names); Geo-Aware LLM Request Routing; Agentforce Agents (masking disabled for agents); Prompt Builder (Work with Large Prompts, masking details in preview).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. EinsteinAISettings (enableTrustPIIMasking, enableAIFeedbackWithDC), EinsteinGptSettings (enableEinsteinGptPlatform, provider blocks, disableAIProviderRegionFallback, malformed sample), GenAiPromptTemplate (suffix, folder, data providers). No EinsteinSettings type exists in this guide.

Listed in the original version and not re-read:

- Einstein Trust Layer, Get Started (Agentforce Developer Guide): https://developer.salesforce.com/docs/einstein/genai/guide/trust.html (developer.salesforce.com returned 403 on 2026-10-03).
- Data Masking (Agentforce Developer Guide): https://developer.salesforce.com/docs/einstein/genai/guide/data-masking.html (403 on 2026-10-03).
- Inside the Einstein Trust Layer (Salesforce Developers Blog): https://developer.salesforce.com/blogs/2023/10/inside-the-einstein-trust-layer (blog; source of the Flan-T5 and grounding-mode claims now marked UNVERIFIED).
- The Einstein Trust Layer, Meet the Einstein Trust Layer (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/meet-the-einstein-trust-layer
- The Einstein Trust Layer, Follow the Prompt Journey (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/follow-the-prompt-journey
- The Einstein Trust Layer, Follow the Response Journey (Trailhead): https://trailhead.salesforce.com/content/learn/modules/the-einstein-trust-layer/follow-the-response-journey
- Configure LLM Data Masking Policies (Trailhead): https://trailhead.salesforce.com/content/learn/modules/llm-data-masking-in-the-einstein-trust-layer/configure-llm-data-masking-policies
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
