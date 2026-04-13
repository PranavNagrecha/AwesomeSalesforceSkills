# LLM Anti-Patterns — AI Governance Architecture

Common mistakes AI coding assistants make when generating or advising on AI Governance Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating "Enable Einstein Trust Layer" as Complete AI Governance

**What the LLM generates:** A governance checklist or architecture recommendation where the only action items are enabling Einstein Trust Layer, toggling zero-data-retention, and optionally configuring content classification. The output concludes that AI governance is configured with no mention of model lifecycle governance, audit trail export, or responsible AI controls.

**Why it happens:** Training data for Salesforce AI topics frequently references Einstein Trust Layer as the primary AI safety mechanism, which it is for prompt-level safety. LLMs conflate "AI safety" (Trust Layer scope) with "AI governance" (full 4-layer scope). The Trust Layer documentation is prominent and detailed; MLOps governance, audit trail retention limits, and Policy-as-Code have less coverage in public training corpora.

**Correct pattern:**

```
AI governance for Salesforce requires four layers, not one:

Layer 1 — AI/ML Lifecycle: Model registry, version control, approval gates before 
           production deployment (Salesforce Model Builder or external MLflow)
Layer 2 — Security/Guardrails: Einstein Trust Layer, topic guardrails, data masking,
           BYOLLM routing policies
Layer 3 — Audit/Observability: Generative AI Audit Trail (requires Data Cloud),
           daily export to S3/SIEM, 7-year retention for regulated industries
Layer 4 — Responsible AI Controls: Human override design, fairness monitoring,
           transparency documentation, EU AI Act conformity assessment

Einstein Trust Layer addresses Layer 2 only.
Governance sign-off requires all four layers.
```

**Detection hint:** Flag any AI governance architecture output that does not mention at least three of the following: model registry, audit trail retention/export, BYOLLM routing, human override, Policy-as-Code, responsible AI controls. Single-layer outputs are almost always incomplete.

---

## Anti-Pattern 2: Recommending Setup Audit Trail for AI Activity Monitoring

**What the LLM generates:** Advice to use the Salesforce Setup Audit Trail to monitor AI model activity, check which models were invoked, or audit Einstein/Agentforce interactions. Sometimes the LLM references the Setup Audit Trail's 180-day retention as suitable for AI compliance evidence.

**Why it happens:** The Setup Audit Trail is the most well-known audit mechanism in Salesforce and is frequently referenced in compliance and security discussions. LLMs generalize from "audit trail for Salesforce activity" to "use Setup Audit Trail for AI activity" without distinguishing between configuration-change auditing (Setup Audit Trail scope) and AI model invocation auditing (Generative AI Audit Trail scope).

**Correct pattern:**

```
Two distinct audit mechanisms — different scope, different retention:

Setup Audit Trail:
  - Tracks: org configuration changes (metadata, settings, user management)
  - Does NOT track: AI model invocations, prompt/response content, agent actions
  - Retention: 180 days
  - Storage: Standard org storage, no Data Cloud required

Generative AI Audit Trail:
  - Tracks: AI/LLM invocations, prompt metadata (masked), model responses,
            user identity, model version, timestamp
  - Does NOT track: org configuration changes
  - Retention: 30 days (requires export pipeline for long-term compliance)
  - Storage: Data Cloud required — no alternative path

For AI activity monitoring, use the Generative AI Audit Trail, not Setup Audit Trail.
```

**Detection hint:** Search output for "Setup Audit Trail" in context of AI monitoring, AI compliance, or model invocation auditing. Any such reference is incorrect for AI activity scope.

---

## Anti-Pattern 3: Designing Real-Time AI Anomaly Detection on Native Audit Trail Alone

**What the LLM generates:** An architecture that triggers real-time alerts or automated responses based on the Salesforce Generative AI Audit Trail — for example, "when the Audit Trail shows a blocked topic attempt, immediately notify the security team." The design assumes Audit Trail data is available in near-real-time.

**Why it happens:** LLMs familiar with SIEM and security event architectures apply the assumption that audit logs are streamed or near-real-time, which is true for many cloud security products. The Salesforce Generative AI Audit Trail's hourly refresh cadence is a platform-specific constraint that is not well-represented in general security architecture training data.

**Correct pattern:**

```
Salesforce Generative AI Audit Trail constraints:
  - Refresh cadence: hourly (not streaming, not real-time)
  - Implication: anomalous events are visible up to ~60 minutes after they occur natively

Architecture for real-time AI anomaly detection:
  1. Configure Data Cloud → S3 export (daily batch for compliance retention)
  2. Integrate SIEM (Splunk, Datadog, Azure Sentinel) with S3 export stream
  3. Apply real-time detection rules in SIEM — SIEM provides the real-time layer
  4. SIEM alerts fire to security team (not Data Cloud/Audit Trail native alerts)
  5. Audit Trail in Data Cloud serves as the Salesforce-native review surface (near-real-time)

Do NOT design real-time response automation directly on Salesforce Audit Trail refresh events.
```

**Detection hint:** Look for architecture descriptions that mention "real-time" or "immediate" alerts triggered from the Salesforce Audit Trail directly, without a SIEM intermediary. The 60-minute refresh latency makes this pattern unreliable.

---

## Anti-Pattern 4: Assuming All AI Calls Are Automatically Captured in the Audit Trail

**What the LLM generates:** A governance architecture or compliance statement asserting that all AI interactions within the Salesforce org are captured in the Generative AI Audit Trail, without checking whether BYOLLM integrations route through the Trust Layer.

**Why it happens:** LLMs default to the assumption that a platform-level feature (Audit Trail) captures all platform activity within scope. The nuance that BYOLLM calls made via direct Named Credential callouts bypass Trust Layer routing — and therefore bypass Audit Trail capture — is a platform-specific gap that is underrepresented in training data. The LLM has no signal that "direct callout = audit bypass."

**Correct pattern:**

```
Generative AI Audit Trail coverage depends on routing:

Captured by Audit Trail:
  - Einstein generative features (Einstein Copilot, Agentforce with standard LLMs)
  - BYOLLM calls explicitly routed through Trust Layer Named Credential gateway

NOT captured by Audit Trail:
  - BYOLLM calls via Named Credentials pointing directly to external LLM APIs
    (e.g., callout:OpenAI_Direct, callout:Anthropic_API)
  - Third-party AI integrations that call external APIs outside Trust Layer routing

Governance check: inventory all Named Credentials in the org. 
Any Named Credential referencing openai.com, anthropic.com, azure.openai.com, 
cohere.ai, or equivalent external LLM endpoints should be flagged for audit trail 
routing verification.
```

**Detection hint:** Look for governance compliance statements that say "all AI interactions are audited" or "the Audit Trail captures all LLM calls" without explicitly confirming BYOLLM routing through Trust Layer. This is almost always an unverified assumption.

---

## Anti-Pattern 5: Treating 30-Day AI Audit Trail Retention as Sufficient for Regulated Industries

**What the LLM generates:** A compliance architecture that relies on native Generative AI Audit Trail storage for audit evidence, notes the 30-day retention, and either accepts it without comment or compares it favorably to the Setup Audit Trail's 180-day retention — without designing an export pipeline.

**Why it happens:** LLMs calibrate "sufficient retention" based on general compliance knowledge without knowing the specific retention requirements of target industries. The Setup Audit Trail's 180-day retention is frequently cited as adequate for many Salesforce compliance scenarios. The Generative AI Audit Trail's 30-day retention is newer platform behavior, less represented in training data, and the gap to regulated-industry requirements (6–7 years for HIPAA and financial services) is not surfaced without domain-specific knowledge.

**Correct pattern:**

```
Generative AI Audit Trail native retention: 30 days
Setup Audit Trail native retention: 180 days

Regulated industry minimum retention requirements (examples):
  - HIPAA (healthcare): 6 years
  - EU AI Act high-risk systems: duration of AI system lifecycle + buffer
  - Financial services AI model risk (SR 11-7): typically 7 years
  - PCI DSS: 1 year (12 months online, remainder offline)

30-day native retention is insufficient for ANY regulated industry.

Required architecture:
  1. Data Cloud Audit Trail export pipeline to S3 (daily batch)
  2. S3 lifecycle policy: active tier (90 days) → Glacier (remainder of retention period)
  3. Retention period set to match regulatory requirement (minimum 6–7 years for 
     healthcare/financial services)
  4. Export pipeline monitoring: alert if export fails for > 24 hours (gap risk)
```

**Detection hint:** Search output for acceptance of 30-day retention without an export pipeline in any context involving healthcare, financial services, EU AI Act high-risk use cases, or general "long-term compliance evidence." Any such acceptance is a compliance risk.
