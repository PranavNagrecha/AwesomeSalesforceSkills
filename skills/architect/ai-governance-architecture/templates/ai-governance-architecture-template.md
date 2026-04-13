# AI Governance Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `ai-governance-architecture`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before proceeding.

- **AI features deployed or planned:** (list all Agentforce agents, Einstein Prediction features, BYOLLM integrations, third-party AI integrations)
- **Regulatory requirements:** (EU AI Act risk category, HIPAA, financial services AI governance, PCI DSS, other)
- **Data Cloud provisioned:** yes / no — (Audit Trail requires Data Cloud; if no, note the gap)
- **BYOLLM models in use:** (list models and current routing path — direct Named Credential vs. Trust Layer routed)
- **Retention requirement:** (specify years — default is 30 days native, regulated industries typically need 6–7 years)
- **Known constraints:** (data residency requirements, existing SIEM platform, MLOps tooling already in place)
- **Failure modes to watch for:** Trust Layer = complete governance assumption; BYOLLM audit gap; 30-day retention expiry

---

## 4-Layer Governance Design

Work through each layer before completing the architecture. Do not skip layers.

### Layer 1 — AI/ML Lifecycle Governance

| Component | Decision | Notes |
|---|---|---|
| Model registry | Salesforce Model Builder / external MLflow / other: ___ | |
| Model versioning | enabled / not configured | |
| Approval gate before production | Flow approval / manual process / none: ___ | |
| Training data documentation | Data Cloud lineage / external catalog / none: ___ | |
| Model retirement policy | documented / not yet defined | |

**Layer 1 gaps identified:**

---

### Layer 2 — Security and Guardrails

| Component | Decision | Notes |
|---|---|---|
| Einstein Trust Layer | enabled / not enabled | |
| Zero-data-retention | toggled on / off | |
| Data masking fields | list fields: ___ | SSN, DOB, Account_Number, etc. |
| Topic guardrails (per agent) | defined as Policy-as-Code / UI only / not configured | |
| Action allowlists (per agent) | defined / not defined | |
| BYOLLM routing through Trust Layer | all routed / partial / none | |

**Layer 2 gaps identified:**

---

### Layer 3 — Audit and Observability

| Component | Decision | Notes |
|---|---|---|
| Generative AI Audit Trail | enabled / not available (no Data Cloud) | |
| Audit Trail export pipeline | Data Cloud → S3 daily / not configured | |
| Export monitoring | alert on export failure / not configured | |
| SIEM integration | Splunk / Datadog / Azure Sentinel / none: ___ | |
| Retention period in SIEM/S3 | ___ years | must meet regulatory minimum |
| Real-time anomaly detection rules | defined in SIEM / not configured | |

**Layer 3 gaps identified:**

---

### Layer 4 — Responsible AI Controls

| Component | Decision | Notes |
|---|---|---|
| Human override points | documented per agent workflow / not defined | |
| Fairness monitoring | scheduled review / automated / none | |
| Transparency documentation | EU AI Act conformity assessment / internal policy / none | |
| Explainability for regulated decisions | SHAP values / feature importance / not required | |
| Incident response for AI failures | runbook defined / not defined | |

**Layer 4 gaps identified:**

---

## Approach

Which pattern from SKILL.md applies? Select one:

- [ ] **4-Layer Governance Architecture Design** — Full framework for regulated industry or high-risk AI deployment
- [ ] **Audit Trail Export Pipeline** — Compliance evidence pipeline for retention beyond 30 days
- [ ] **BYOLLM Routing Governance** — Routing policy design for Bring-Your-Own-LLM integrations
- [ ] **EU AI Act Conformity Assessment** — Documentation design for high-risk AI use cases

**Rationale:** (explain why this pattern fits the request)

---

## Regulatory Mapping

Complete this section for any regulated industry or EU AI Act use case.

| AI Use Case | Regulatory Framework | Risk Category | Control Requirements |
|---|---|---|---|
| (e.g., loan decisioning) | EU AI Act | High-risk (credit decisions) | Risk management system, conformity assessment, human oversight, audit trail |
| (e.g., clinical documentation) | HIPAA | N/A — privacy requirement | 6-year audit log retention, PHI data masking |

**EU AI Act high-risk compliance deadline:** August 2026

---

## Review Checklist

Work through this before marking governance design complete.

- [ ] All deployed AI features inventoried (Agentforce, Einstein Prediction, BYOLLM, third-party)
- [ ] Einstein Trust Layer confirmed as Layer 2 only — not presented as complete governance
- [ ] Data Cloud provisioning confirmed (required for Generative AI Audit Trail)
- [ ] Audit Trail export pipeline designed — retention period meets regulatory minimum
- [ ] Export pipeline monitoring designed — alerts if export fails for > 24 hours
- [ ] BYOLLM routing through Trust Layer confirmed for each BYOLLM integration
- [ ] No Named Credentials point directly to external LLM providers without Trust Layer routing
- [ ] Topic guardrails defined as Policy-as-Code for all Agentforce agents
- [ ] Human override points documented for each high-risk AI use case
- [ ] EU AI Act conformity assessment documentation scoped (if high-risk use case present)
- [ ] 30-day native Audit Trail retention limitation explicitly addressed with export pipeline

---

## Output Artifacts Checklist

- [ ] AI governance architecture document (4-layer framework with technology mapping per layer)
- [ ] Audit trail architecture design (Data Cloud → S3/SIEM pipeline with retention and alert design)
- [ ] Policy-as-Code specifications (topic guardrails, data masking rules, action allowlists)
- [ ] Regulatory compliance matrix (EU AI Act or equivalent risk category mapping)

---

## Notes

Record any deviations from the standard pattern and why.

(e.g., "Data Cloud not available — Audit Trail not feasible natively; designed external-only audit pipeline via MuleSoft direct capture before Trust Layer.")
