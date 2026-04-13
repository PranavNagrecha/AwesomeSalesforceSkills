# Gotchas — AI Governance Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Einstein Trust Layer Is One Layer of Four — Not Complete AI Governance

**What happens:** Organizations enable Einstein Trust Layer, confirm zero-data-retention is active, and declare AI governance complete. Subsequent regulatory audits or security reviews reveal no model lifecycle governance, no long-term audit evidence, and no human override documentation.

**When it occurs:** Universally, when an architect conflates "AI safety controls" with "AI governance." Trust Layer addresses prompt-level safety at inference time. It does not govern how models are trained, versioned, approved for production, or retired. It does not satisfy EU AI Act Article 9 risk management system requirements, HIPAA AI interaction audit requirements, or financial services AI governance frameworks that require model risk management documentation.

**How to avoid:** Use the 4-layer governance framework explicitly. Document in the architecture that Trust Layer is Layer 2 (Security and Guardrails). Confirm all four layers have design coverage before governance sign-off: AI/ML Lifecycle (model registry, approval gates), Security/Guardrails (Trust Layer, topic guardrails, data masking), Audit/Observability (Audit Trail + export pipeline), Responsible AI Controls (human override, fairness monitoring, transparency docs).

---

## Gotcha 2: AI Audit Trail Has 30-Day Retention and Requires Data Cloud — Neither Is Obvious

**What happens:** Orgs that enable the Generative AI Audit Trail assume it behaves like the standard Setup Audit Trail (180-day retention, no extra platform requirement). In practice, the Generative AI Audit Trail requires Data Cloud as its storage layer and retains records for only 30 days. Records older than 30 days are permanently deleted with no recovery option.

**When it occurs:** When an org activates Agentforce or Einstein generative features without first provisioning Data Cloud, the Audit Trail is simply unavailable — there is no fallback storage path. When Data Cloud is present but no export pipeline is configured, the 30-day window passes and compliance evidence is lost. This is especially damaging for regulated industries where audit records must be retained for 6–7 years.

**How to avoid:** Two distinct precautions are required. First, confirm Data Cloud is provisioned before relying on the Generative AI Audit Trail — orgs without Data Cloud have no native AI audit capability. Second, design and deploy a Data Cloud → S3/SIEM export pipeline within the 30-day retention window. Set export frequency to daily to maintain a continuous export with adequate margin. Never treat the 30-day native retention as sufficient for any regulated use case.

---

## Gotcha 3: BYOLLM Calls Bypass the Audit Trail Unless Explicitly Routed Through Trust Layer

**What happens:** An organization integrates a BYOLLM model (OpenAI GPT-4, Anthropic Claude, Azure OpenAI) using a Salesforce Named Credential pointing directly to the external LLM API endpoint. Audit Trail appears to be working correctly for standard Einstein features. The BYOLLM interactions are silently absent from the Audit Trail with no error or warning. The gap is invisible until a compliance audit requests logs for BYOLLM-assisted interactions.

**When it occurs:** Any time a BYOLLM integration is built as a direct Named Credential callout to an external LLM provider rather than routing through the Einstein Trust Layer gateway. This is the default pattern for many BYOLLM integrations because routing through Trust Layer requires explicit configuration. Integrations added after initial governance setup are especially prone to this omission.

**How to avoid:** Define a BYOLLM routing policy as a governance rule: all LLM callouts must use Named Credentials that route through the Trust Layer gateway endpoint, not directly to external providers. Enforce this policy at code review. Use the checker script (`check_ai_governance_architecture.py`) to detect Named Credentials referencing external LLM providers (openai, anthropic, azure, cohere) without Trust Layer routing. Review the full list of Named Credentials in the org against the inventory of known LLM providers after any BYOLLM integration work.

---

## Gotcha 4: Zero-Data-Retention and Audit Requirements Create an Architectural Tension That Must Be Explicitly Resolved

**What happens:** Einstein Trust Layer's zero-data-retention guarantee means prompts and responses are not stored on Salesforce infrastructure after the API call completes. This is a privacy and security feature. However, compliance frameworks requiring AI interaction audit logs (HIPAA, EU AI Act, financial services AI governance) need prompts and responses to be logged. These two requirements appear to be in direct conflict.

**When it occurs:** When an architect enables zero-data-retention to satisfy a data residency or privacy requirement without simultaneously designing an external logging pipeline. The Generative AI Audit Trail captures masked prompt metadata even with zero-data-retention active — but organizations that disable data masking or misconfigure the Trust Layer may inadvertently prevent audit-relevant data from being logged.

**How to avoid:** Understand that zero-data-retention and audit trail logging operate at different levels. Zero-data-retention means Salesforce does not retain raw prompts in its LLM infrastructure after the call. The Generative AI Audit Trail still captures masked prompt text, user identity, timestamp, model version, and response metadata. The architectural resolution is: enable data masking on PII fields (satisfies zero-data-retention spirit), configure Audit Trail (captures masked interaction metadata for compliance), and export Audit Trail to SIEM for long-term retention. Document this resolution explicitly in the governance architecture.
