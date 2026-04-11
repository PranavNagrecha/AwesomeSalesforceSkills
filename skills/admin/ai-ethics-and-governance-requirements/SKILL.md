---
name: ai-ethics-and-governance-requirements
description: "Use this skill when defining AI governance policies, designing human oversight workflows, documenting bias mitigation strategies, or meeting regulatory transparency requirements for Salesforce AI features. Trigger keywords: responsible AI, AI bias, AI audit trail, AI transparency, human-in-the-loop, AI risk inventory, AI disclosure. NOT for Trust Layer technical configuration — that is covered by agentforce/einstein-trust-layer."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Security
  - Operational Excellence
triggers:
  - "how do we document our AI governance policy for Salesforce Einstein features"
  - "what human oversight controls are required before we go live with Agentforce"
  - "how do we detect and mitigate bias in a Salesforce Einstein prediction model"
  - "we need an audit trail for AI-generated recommendations surfaced to sales reps"
  - "what disclosures are required when Salesforce AI content is shown to customers"
  - "how do we build a risk inventory for AI use cases in our org"
tags:
  - ai-governance
  - responsible-ai
  - bias-mitigation
  - human-oversight
  - ai-audit-trail
  - transparency
  - einstein
  - agentforce
inputs:
  - "List of AI features or Agentforce agents currently deployed or planned in the org"
  - "Applicable regulatory or compliance frameworks (e.g., EU AI Act, CCPA, HIPAA)"
  - "Current data residency and retention constraints"
  - "Org profile: industry, customer-facing vs. internal use cases, data sensitivity level"
outputs:
  - "AI governance policy document outlining pillars, ownership, and review cadence"
  - "Risk inventory mapping each AI use case to likelihood, impact, and mitigation owner"
  - "Human oversight design specifying approval gates and escalation rules per use case"
  - "Bias mitigation checklist tied to Einstein model inputs and training data"
  - "AI transparency and disclosure copy for end-user-facing surfaces"
  - "Audit trail specification: what is logged, where, how long it is retained"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# AI Ethics and Governance Requirements

Use this skill when a Salesforce implementation needs governance structure around AI features — not just configuration, but the policies, human oversight rules, risk inventory, bias controls, and transparency disclosures that sit above Trust Layer settings. Activates when stakeholders ask how to make AI use responsible, auditable, and explainable rather than how to configure a specific platform feature.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which AI surface is in scope: Einstein Prediction Builder, Next Best Action (NBA), Agentforce agents, Einstein Copilot, Einstein Discovery, or a third-party LLM integrated through the Trust Layer.
- Whether the org is subject to sector-specific regulation (healthcare HIPAA, financial FINRA, EU AI Act high-risk classification, California CPRA).
- Whether AI-generated output is customer-facing or internal-only — disclosure requirements differ materially.
- Who owns the AI governance function in the customer org: CTO, legal/compliance, data governance council, or a dedicated AI Ethics board.
- The most common wrong assumption: that enabling the Einstein Trust Layer is sufficient governance. Trust Layer covers data protection during LLM calls; governance covers policy, human accountability, bias controls, and ongoing audit.

---

## Core Concepts

### 1. Salesforce Responsible AI Pillars

Salesforce's responsible AI framework rests on five published pillars:

1. **Accuracy** — AI outputs must be grounded, traceable, and evaluated against ground truth.
2. **Safety** — Harmful, toxic, or dangerous content must be prevented before it reaches users. The Einstein Trust Layer's toxicity scoring and prompt defense mechanisms are safety controls, but the policy decision on what constitutes "harmful" is a governance requirement.
3. **Honesty** — AI-generated content must be disclosed as such. Salesforce requires that features surfacing generated text display a disclosure marker. Orgs must define where and how those markers appear.
4. **Empowerment** — Users and customers must be able to override, reject, or escalate AI decisions. Human-in-the-loop gates are a governance design concern, not a platform default.
5. **Sustainability** — AI resource consumption and environmental impact must be tracked as part of responsible use.

### 2. AI Risk Inventory

Before deploying any AI feature, governance requires a risk inventory: a structured list of each AI use case with its likelihood of harm, impact severity, affected user population, and assigned mitigation owner. Salesforce recommends classifying use cases on a 3x3 likelihood-impact grid. High-impact, customer-facing uses — such as denying a loan or surfacing a medical recommendation — require the most stringent human oversight.

The risk inventory is a living document. It must be reviewed each time a model is retrained, a new feature is enabled, or a regulation changes.

### 3. Bias Detection and Mitigation

Einstein models trained on historical Salesforce data can encode historical inequity. Salesforce Help documents a formal bias detection workflow for Einstein Prediction Builder and Einstein Discovery:

- Identify protected attributes (race, gender, age, disability) and proxy attributes (zip code as race proxy, job title as gender proxy).
- Run the Einstein bias detection report, which scores each predictor field for disparate impact against protected groups.
- Remove or bucket proxy fields before model training.
- Establish a regular retraining cadence with a bias re-evaluation checkpoint after each run.

Governance policy must document which attributes are protected in the org's jurisdiction, who reviews the bias report, and what threshold triggers a model withdrawal.

### 4. Audit Trail Requirements

Salesforce audit capabilities relevant to AI governance:

- **Einstein Audit Data** — when Einstein Prediction Builder decisions are logged, the log includes the record ID, prediction score, contributing features, and timestamp. These logs can be exported to Data Cloud for long-term retention.
- **Field History Tracking** — tracks changes to fields that AI writes to (e.g., a score field updated by Einstein). Does not capture the AI model version or input features — that gap must be filled by a custom logging mechanism.
- **Event Monitoring** — logs API access patterns, including which user or connected app triggered an AI inference. Essential for detecting unauthorized AI use.
- Governance must specify: what is logged, the minimum retention period, who has read access to the audit log, and the incident response procedure for anomalous AI behavior.

---

## Common Patterns

### Pattern 1: Governance Policy Document Driven by Pillar Mapping

**When to use:** The org is deploying its first Agentforce agent or Einstein feature and legal/compliance needs a written policy before go-live approval.

**How it works:**
1. Map every deployed AI feature to the five Salesforce responsible AI pillars.
2. For each pillar, define the control (e.g., Accuracy → grounding source, review cadence; Honesty → disclosure copy and placement; Empowerment → override mechanism and escalation SLA).
3. Assign a named owner and review date for each control.
4. Publish the resulting policy document to stakeholders and gate go-live on sign-off.

**Why not skip the policy:** Orgs that configure Trust Layer without a written policy have no accountability chain when an AI decision is disputed. Regulators and auditors ask for documented controls, not screenshots of platform settings.

### Pattern 2: Human Oversight Gate for High-Risk Decisions

**When to use:** AI is recommending or taking actions with significant downstream impact — price changes, case escalation, credit decisions, medical triage.

**How it works:**
1. Classify the use case on the likelihood-impact grid. Flag anything with high impact.
2. Design a Salesforce approval process or Flow-based review gate that intercepts the AI recommendation before it is applied.
3. Log the reviewer identity, timestamp, the AI recommendation shown, and the final human decision — whether it accepted or overrode the AI.
4. Set an SLA for review turnaround that does not create an approval bottleneck in the core business process.
5. Report on override rates; a very high override rate signals the model needs retraining.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| AI is customer-facing and output is visible to end users | Require explicit AI-generated content disclosure marker per Salesforce Honesty pillar | Regulatory requirement in EU AI Act and multiple US state laws; Salesforce requires it by design |
| AI use case is internal low-impact (e.g., suggested email subject line to rep) | Lightweight governance: disclosure in UI, basic audit log, quarterly review | Proportionality — full risk inventory overhead not warranted |
| AI use case is high-impact (credit, medical, legal, enforcement) | Full risk inventory, human oversight gate, independent bias audit, external legal review | Regulatory exposure and reputational risk justify additional controls |
| Model is retrained with new data | Trigger bias re-evaluation before new model is promoted to production | Bias baselines shift with data distribution changes |
| Third-party LLM is integrated via Trust Layer | Governance must document zero-data-retention policy and verify Trust Layer is enforcing it | GDPR and CCPA data processor obligations; Trust Layer enforces zero retention with approved third-party models |
| Org is subject to EU AI Act | Classify use case risk tier; high-risk uses require conformity assessment, human oversight, and technical documentation | EU AI Act is binding law for orgs with EU users regardless of where org is headquartered |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory all active AI features** — pull a list of every Einstein feature, Agentforce agent, and third-party LLM integration enabled in the org. Include sandbox and UAT environments, not just production.
2. **Classify each use case by risk tier** — apply the 3x3 likelihood-impact grid. Label each use case: low, medium, or high risk. Flag all customer-facing and high-impact uses for deeper review.
3. **Map controls to the five responsible AI pillars** — for each use case, define the Accuracy, Safety, Honesty, Empowerment, and Sustainability control. Identify gaps where no control exists yet.
4. **Design human oversight gates** — for medium- and high-risk use cases, specify the review mechanism (approval process, escalation flow), the reviewer role, and the logging requirement.
5. **Run and document the bias evaluation** — for Einstein Prediction Builder and Einstein Discovery models, run the built-in bias detection report. Document protected attributes, findings, and any fields removed or adjusted as a result.
6. **Draft transparency disclosures** — write the AI-generated content disclosure copy for each customer-facing surface. Confirm legal has approved the language.
7. **Validate audit trail coverage** — confirm each AI feature produces a timestamped, attributable audit log. Identify gaps (e.g., Field History Tracking not capturing model version) and fill with custom logging or Data Cloud retention rules.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] AI feature inventory is complete and covers all environments including sandbox
- [ ] Every use case is classified on the likelihood-impact grid with a named owner
- [ ] Responsible AI pillar mapping is documented and has no unaddressed gaps
- [ ] Human oversight gates are designed and tested for all medium- and high-risk use cases
- [ ] Bias detection report has been run and results are documented for all Einstein models
- [ ] AI-generated content disclosures are present on all customer-facing AI surfaces
- [ ] Audit trail specification is written and retention period meets regulatory minimum
- [ ] Governance policy document has received sign-off from legal/compliance and an executive sponsor

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Einstein Trust Layer is not equivalent to AI governance** — The Trust Layer handles data protection during LLM inference (prompt masking, zero-retention, toxicity scoring). It does not produce a risk inventory, does not enforce human oversight gates, and does not generate bias reports. Orgs that equate Trust Layer enablement with AI governance completion will fail an audit.
2. **Field History Tracking does not capture model version or input features** — When an Einstein model writes a score to a field, Field History Tracking logs the before/after value and the user identity of the record owner — not the AI model version, confidence interval, or contributing features. A custom platform event or Data Cloud log must be added to capture those for audit purposes.
3. **Bias report baseline shifts on every retraining** — Einstein Prediction Builder's bias report produces a snapshot, not a continuous monitor. When a model is retrained, the protected-attribute scores reset. Governance policy must require a new bias report run before the retrained model is promoted, not just at initial deployment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AI Governance Policy Document | Written policy mapping each AI use case to controls across the five responsible AI pillars, with named owners and review cadence |
| Risk Inventory | Spreadsheet or Confluence page classifying each use case by likelihood, impact, mitigation, and owner |
| Human Oversight Design | Specification of approval gates, escalation paths, reviewer roles, SLAs, and override logging for each high-risk use case |
| Bias Mitigation Checklist | Protected attributes list, proxy fields identified, bias report findings, and sign-off record |
| Transparency Disclosure Copy | Legal-approved disclosure language for each customer-facing AI surface |
| Audit Trail Specification | What is logged, log retention period, access control, and incident response runbook |

---

## Related Skills

- agentforce/einstein-trust-layer — use alongside this skill for the technical Trust Layer configuration that implements the safety and zero-retention controls defined in governance policy
- agentforce/agentforce-agent-design — use alongside this skill when designing Agentforce agents; human oversight gates must be designed at agent-build time, not added post-deployment
- architect/ai-ready-data-architecture — use when the governance requirement surfaces data quality or retention architecture decisions
