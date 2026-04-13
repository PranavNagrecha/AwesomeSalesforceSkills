---
name: ai-governance-architecture
description: "System architecture for Salesforce AI governance: MLOps pipeline design, AI Audit Trail architecture, Einstein Trust Layer security design, Policy-as-Code engine, and regulatory compliance design for EU AI Act and similar frameworks. NOT for general Salesforce security architecture, AI ethics policy documentation, or individual Agentforce agent configuration."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I architect AI governance for Salesforce Agentforce deployments"
  - "designing an AI audit trail and model lifecycle governance system on Salesforce"
  - "Einstein Trust Layer vs full AI governance — what else do I need beyond Trust Layer"
  - "how to meet EU AI Act requirements for high-risk AI systems using Salesforce"
  - "designing Policy-as-Code guardrails for Agentforce and Einstein AI"
tags:
  - ai-governance
  - agentforce
  - einstein-trust-layer
  - audit-trail
  - responsible-ai
  - mlops
  - compliance
  - architecture
inputs:
  - "List of AI/ML features deployed or planned (Agentforce, Einstein Prediction, BYOLLM)"
  - "Regulatory requirements (EU AI Act, industry-specific AI regulations)"
  - "Data residency and sovereignty requirements"
  - "Existing MLOps tools and model registry (if any)"
outputs:
  - "AI governance architecture document with 4-layer framework"
  - "Audit trail architecture design"
  - "Policy-as-Code guardrail specifications"
  - "Regulatory compliance mapping (EU AI Act or equivalent)"
dependencies:
  - ai-platform-architecture
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# AI Governance Architecture

This skill activates when an architect needs to design a comprehensive AI governance system for a Salesforce org — covering the 4-layer governance framework (AI/ML Lifecycle, Security/Guardrails, Audit/Observability, Responsible AI Controls), Audit Trail architecture, Policy-as-Code engine, and regulatory compliance design. It does NOT cover individual Agentforce agent configuration, general security architecture, or AI ethics policy documentation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Einstein Trust Layer is not full AI governance** — The Trust Layer provides zero-data-retention guarantees, prompt injection detection, and toxicity filtering. It is ONE security layer in a complete governance stack. Full governance additionally requires MLOps lifecycle management, Policy-as-Code enforcement, and immutable audit trail architecture.
- **AI Audit Trail requires Data Cloud** — Salesforce Generative AI Audit Trail logs are stored in Data Cloud. There is no alternative storage path. Orgs without Data Cloud cannot use the native Audit Trail feature. The audit trail refreshes hourly — real-time detection of model misuse is impossible natively.
- **30-day audit retention** — AI Audit Trail has a 30-day default retention (distinct from the 180-day Setup Audit Trail). Long-term compliance evidence requires exporting to an external system (S3, SIEM) within the 30-day window.
- **BYOLLM calls bypass audit trail** — Bring-Your-Own-LLM model calls that are not explicitly routed through the Trust Layer do not appear in the Salesforce Generative AI Audit Trail. BYOLLM governance requires explicit routing configuration.
- **EU AI Act high-risk compliance deadline** — August 2026. Salesforce orgs using AI for high-risk use cases (employment, credit, healthcare decisions) need a compliant governance framework in place.

---

## Core Concepts

### The 4-Layer AI Governance Framework

Comprehensive Salesforce AI governance spans four layers:

**Layer 1 — AI/ML Lifecycle Governance:** Model registry, training data documentation, model versioning, approval gates before production deployment. Requires MLOps pipeline integration (Weights & Biases, MLflow, or Salesforce Model Builder's built-in versioning).

**Layer 2 — Security and Guardrails:** Einstein Trust Layer (zero-data-retention, prompt injection detection, toxicity filtering), topic guardrails on Agentforce agents, data masking for PII in prompts, BYOLLM routing policies.

**Layer 3 — Audit and Observability:** Salesforce Generative AI Audit Trail (requires Data Cloud), prompt/response logging, model performance monitoring, usage analytics. 30-day retention requires external export pipeline.

**Layer 4 — Responsible AI Controls:** Fairness monitoring (bias detection), human-in-the-loop override design, transparency documentation, explainability requirements for regulated use cases.

### AI Audit Trail Architecture

The Salesforce Generative AI Audit Trail captures:
- Prompt text (masked if data masking is enabled)
- Model response
- User identity and timestamp
- Model version and endpoint used

Architectural constraints:
- Requires Data Cloud — no alternative storage
- Refreshes hourly — not real-time
- 30-day retention — must export for long-term compliance
- BYOLLM calls are not captured unless explicitly routed through Trust Layer

Recommended architecture for long-term compliance:
1. Configure Data Cloud Audit Trail export to S3 or SIEM (Splunk, Datadog)
2. Set export frequency to daily (within 30-day window)
3. SIEM provides real-time alerting on anomalous model behavior
4. Data Cloud provides the Salesforce-native audit surface for near-real-time review

### Policy-as-Code Engine

Policy-as-Code for Salesforce AI governance enforces rules declaratively:
- Agentforce topic guardrails (define what topics agents CANNOT discuss)
- Einstein Trust Layer data masking policies (mask SSN, credit card numbers before prompt send)
- Agentforce action allowlists (which Apex actions, Flows, or APIs an agent can invoke)
- Model routing policies (which LLM model handles which use case)

Policy changes require code review and deployment — they are not ad-hoc UI configuration. This provides auditability of governance policy changes over time.

---

## Common Patterns

### 4-Layer Governance Architecture Design

**When to use:** Any organization deploying Agentforce, Einstein Prediction Builder, or BYOLLM models in a regulated industry or for high-risk use cases.

**How it works:**
1. Layer 1: Integrate model registry (Salesforce Model Builder or external MLflow) with approval workflow before any model is promoted to production.
2. Layer 2: Enable Einstein Trust Layer. Configure topic guardrails on all Agentforce agents. Configure data masking for PII fields. Define BYOLLM routing policies.
3. Layer 3: Enable Generative AI Audit Trail (requires Data Cloud). Configure daily export to S3/SIEM. Set up SIEM alerts for anomaly patterns (unusual prompt volumes, blocked topic attempts).
4. Layer 4: Define fairness monitoring thresholds. Document human override points in agent workflows. Create transparency documentation for each deployed model.

**Why not just Trust Layer:** Trust Layer provides prompt-level safety controls. It does not govern the model lifecycle, provide long-term audit evidence, or satisfy EU AI Act documentation requirements. Governance requires all four layers.

### Audit Trail Export Pipeline

**When to use:** Regulated industries (financial services, healthcare) requiring AI audit evidence beyond 30 days, or when real-time anomaly detection is required.

**How it works:**
1. Configure Data Cloud data stream export to S3 (daily batch).
2. S3 triggers Lambda or MuleSoft flow to ingest into SIEM (Splunk/Datadog).
3. SIEM applies detection rules: high-frequency unusual topics, blocked content patterns, after-hours model invocations.
4. SIEM alerts fire to security team on anomaly detection.
5. Audit records retained in S3 for compliance evidence period (typically 7 years).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Basic AI safety for Agentforce | Einstein Trust Layer + topic guardrails | Minimum viable safety layer |
| Regulated industry AI deployment | Full 4-layer governance framework | Compliance and audit evidence requirements |
| Long-term audit evidence (> 30 days) | Data Cloud Audit Trail + S3/SIEM export | Audit Trail retention is only 30 days natively |
| BYOLLM governance | Explicit routing through Trust Layer + extended audit | BYOLLM calls bypass audit unless explicitly routed |
| EU AI Act high-risk use case | 4-layer framework + conformity assessment documentation | August 2026 compliance deadline |
| Real-time anomaly detection | SIEM integration with Audit Trail export | Audit Trail refreshes hourly, not real-time |

---

## Recommended Workflow

1. **AI inventory** — List all deployed and planned AI/ML features: Agentforce agents, Einstein Prediction, BYOLLM models, third-party AI integrations. This drives the governance scope.
2. **Regulatory mapping** — Map each AI use case to applicable regulations (EU AI Act risk categories, financial services AI guidance, healthcare AI requirements). Identify high-risk use cases requiring conformity assessment documentation.
3. **Layer-by-layer design** — Design each governance layer independently: model lifecycle (Layer 1), Trust Layer and guardrails (Layer 2), audit and observability (Layer 3), responsible AI controls (Layer 4).
4. **Audit trail architecture** — Design the Data Cloud → S3/SIEM export pipeline. Determine retention period and access controls for audit records.
5. **Policy-as-Code design** — Define all governance policies as code artifacts (topic guardrails, data masking rules, action allowlists). Establish code review process for policy changes.
6. **BYOLLM routing** — For any BYOLLM integration, explicitly confirm routing through Trust Layer for audit capture. Document which models are routed and which are not.
7. **Review** — Confirm Trust Layer is not presented as complete governance. Confirm 30-day Audit Trail retention limitation is addressed with export. Confirm BYOLLM routing is documented.

---

## Review Checklist

- [ ] All deployed AI features inventoried and mapped to regulatory risk categories
- [ ] Einstein Trust Layer is one layer in a 4-layer framework (not the whole governance story)
- [ ] Generative AI Audit Trail export pipeline designed for retention > 30 days
- [ ] BYOLLM calls explicitly routed through Trust Layer for audit capture
- [ ] Agentforce topic guardrails defined and documented as Policy-as-Code
- [ ] Human override points documented for high-risk AI use cases
- [ ] EU AI Act high-risk use case conformity assessment documentation scoped

---

## Salesforce-Specific Gotchas

1. **Trust Layer is not a complete AI governance framework** — Enabling Trust Layer addresses prompt safety and zero-data-retention. It does not address model lifecycle governance, long-term audit evidence, fairness monitoring, or regulatory documentation. Organizations that enable Trust Layer and consider governance done are exposed.
2. **AI Audit Trail requires Data Cloud and has 30-day retention** — Organizations without Data Cloud have no native AI Audit Trail. Even with Data Cloud, the 30-day retention window means compliance evidence must be exported within 30 days or it is permanently lost.
3. **BYOLLM calls bypass the audit trail by default** — BYOLLM model invocations do not automatically appear in the Generative AI Audit Trail. Explicit routing configuration through the Trust Layer is required. Organizations that add BYOLLM integrations after initial governance setup frequently miss this.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AI governance architecture document | 4-layer framework design with technology mapping per layer |
| Audit trail architecture design | Data Cloud → S3/SIEM pipeline with retention and alert design |
| Policy-as-Code specifications | Topic guardrails, data masking rules, and action allowlists as deployable artifacts |
| Regulatory compliance matrix | EU AI Act or equivalent risk category mapping with control evidence requirements |

---

## Related Skills

- `ai-platform-architecture` — For model selection, Trust Layer design, and multi-agent orchestration at the platform level
- `data-cloud-architecture` — For Data Cloud configuration required to support the AI Audit Trail
