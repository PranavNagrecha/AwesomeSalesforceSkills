---
name: ai-use-case-assessment
description: "Use this skill to identify, score, and prioritize Salesforce AI use cases before any implementation begins — covering opportunity identification, Impact-Effort matrix scoring, feasibility evaluation across Technical/Operational/Data/Risk dimensions, and ROI framing. NOT for implementation, enablement, feature configuration, or data architecture design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "where should we start with AI in our Salesforce org"
  - "how do we evaluate whether an AI use case is feasible for our organization"
  - "we want to build a business case for adopting Einstein or Agentforce"
  - "how do we prioritize which AI features to implement first"
  - "our data is not clean — can we still use AI and what should we check"
  - "stakeholders want an ROI estimate before approving an AI project"
tags:
  - ai-use-case-assessment
  - ai-strategy
  - einstein
  - agentforce
  - data-readiness
  - roi-estimation
  - feasibility
  - impact-effort-matrix
inputs:
  - "List of candidate AI use cases or business problems the org wants AI to address"
  - "Current Salesforce product licenses and edition (e.g., Enterprise + Data Cloud, Unlimited)"
  - "High-level description of data sources, volumes, and whether Data Cloud or a CRM Analytics dataset is in place"
  - "Stakeholder constraints: timeline, budget, risk tolerance, regulatory environment"
  - "Existing org complexity indicators (number of custom objects, active automations, API integrations)"
outputs:
  - "Scored Impact-Effort matrix with each candidate use case plotted into a quadrant"
  - "Feasibility scorecard per use case across Technical, Operational, Data Readiness, and Risk dimensions"
  - "Prioritized shortlist with a rationale and recommended sequencing"
  - "Data readiness gap list with minimum remediation steps required before AI activation"
  - "High-level ROI framing (payback period drivers, opportunity cost narrative) — not a financial projection"
dependencies:
  - ai-ready-data-architecture
  - agentforce-service-ai-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# AI Use Case Assessment

This skill activates when a practitioner or organization needs to decide **which AI use cases to pursue on Salesforce, in what order, and whether they are feasible** — before any implementation work begins. It produces a structured prioritization and feasibility output grounded in the Salesforce AI Use Case Identification framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License and edition confirmation:** Many Einstein features require specific add-ons. Einstein for Service generative features (Work Summaries, Service Replies) require the Einstein for Service add-on license; Agentforce requires the Agentforce platform license. Confirm what is purchased before scoring technical feasibility.
- **Data posture:** The single most common failure mode is assuming that CRM data is AI-ready. Verify whether Data Cloud is licensed and populated, whether key objects (Case, Lead, Opportunity) have sufficient record volume and field completeness for the features being assessed.
- **Stakeholder alignment on scope:** Assessment work frequently expands into implementation scoping mid-session. Stay inside the assessment boundary — the outputs of this skill feed an implementation project, not replace one.

---

## Core Concepts

### 1. Impact-Effort Matrix

The Salesforce AI use case framework organizes candidate use cases into four quadrants based on two axes: **business impact** (revenue, cost reduction, customer satisfaction, risk mitigation) and **implementation effort** (technical complexity, data readiness requirements, change management burden).

| Quadrant | Impact | Effort | Action |
|---|---|---|---|
| Quick Wins | High | Low | Prioritize first |
| Big Bets | High | High | Plan for later; needs groundwork |
| Low-Hanging Fruit | Low | Low | Fill gaps; good for momentum |
| Money Pits | Low | High | Avoid or defer indefinitely |

Scoring is qualitative and consensus-driven. A facilitated workshop with business and IT stakeholders is the standard approach. Use a 1–3 scale per dimension, sum the axis scores, and plot the result. Do not use the matrix as a rigid formula — it is a facilitation and alignment tool.

### 2. Feasibility Dimensions

Each use case is assessed across four dimensions before it can be recommended:

**Technical Feasibility** — Does the org have the correct license, edition, and platform prerequisites? Is the required Salesforce feature generally available or still in beta? Are there integration dependencies (e.g., external LLM calls, Data Cloud unification) that are not yet in place?

**Operational Feasibility** — Will the business process support AI-generated outputs? Are there human-in-the-loop review steps required? Does the team have the capacity to manage, monitor, and retrain AI models over time?

**Data Readiness** — Salesforce recommends scoring data readiness across four sub-dimensions: availability (does the data exist in the org?), quality (is it clean, consistent, deduplicated?), unification (is it unified across sources in Data Cloud?), and governance (is data access controlled, compliant with privacy regulations, and auditable?). Each sub-dimension can be scored 1 (not ready) to 3 (fully ready). A composite score below 6 typically means the use case should be gated pending data remediation.

**Risk Profile** — What are the failure modes if the AI output is wrong? High-risk use cases (autonomous financial decisions, clinical recommendations in Health Cloud, legally binding communications) require additional governance controls, human review gates, and explicit bias and hallucination mitigation before they can be approved.

### 3. ROI Framing (Not Financial Projection)

Salesforce does not mandate a single ROI formula. Common financial framing levers include:
- **Internal Rate of Return (IRR)** and **Net Present Value (NPV)** for capital expenditure proposals
- **Payback period** for operational cost-reduction use cases
- **Opportunity cost narrative** for use cases where the cost is forgoing revenue or competitive position

The output of assessment is a structured narrative of where value is expected to come from and what assumptions must be true — not a spreadsheet projection. Financial projection belongs in a business case document produced by finance stakeholders.

---

## Common Patterns

### Pattern 1: Facilitated Use Case Discovery Workshop

**When to use:** At the start of an AI initiative before any feature has been selected. Typically used with 5–15 stakeholders from business, IT, and compliance.

**How it works:**
1. Brainstorm candidate AI use cases from each stakeholder group (20–30 min). Use Salesforce's reference use case library (Agentforce use cases on salesforce.com) as a prompt.
2. Group related use cases and remove duplicates.
3. Score each remaining use case on Impact (1–3) and Effort (1–3) using silent voting, then reveal and discuss outliers.
4. Plot results on the Impact-Effort matrix quadrants.
5. Apply the four feasibility dimensions to the top 5–8 Quick Wins and Big Bets to produce a shortlist.

**Why not selecting use cases based on enthusiasm alone:** Stakeholder excitement frequently clusters around Big Bets (high impact, high effort) without accounting for data readiness gaps that make those use cases 12–18 months away from feasibility.

### Pattern 2: Data Readiness Gate Before Feasibility Scoring

**When to use:** When the org suspects its data is incomplete or ungoverned, before investing time in the full Impact-Effort exercise.

**How it works:**
1. For each candidate use case, identify the primary data objects it depends on (e.g., Einstein Case Classification needs Case records with populated Subject and Description fields; Einstein Opportunity Scoring needs Opportunity history with stage progressions).
2. Score each data source on the four sub-dimensions (availability, quality, unification, governance) on a 1–3 scale per sub-dimension.
3. Any use case with a composite data readiness score below 6 out of 12 is flagged as **Data Blocked** and removed from the active shortlist until remediation is confirmed.
4. Produce a remediation list: which objects need field completion campaigns, which sources need Data Cloud ingestion, which governance policies need to be documented.

**Why not skipping the data readiness gate:** The most common cause of failed AI projects in Salesforce orgs is activating a feature (e.g., Einstein Lead Scoring) against sparse or dirty data, which produces model outputs with no predictive validity. The business observes no value, trust in AI erodes, and the initiative is cancelled.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is new to AI and has no existing Data Cloud | Start with Low-Hanging Fruit and Quick Wins that do not require Data Cloud (e.g., Einstein Email Insights, Case Classification on clean Case data) | Builds trust and momentum before committing to Data Cloud investment |
| Stakeholders want an ROI estimate before approving | Produce a payback period narrative using benchmark ranges from Salesforce research (e.g., "customers report 20–30% reduction in handle time for Service Cloud Einstein Work Summaries") rather than a custom financial model | Avoids false precision; anchors to published Salesforce customer evidence |
| Data readiness score is below 6 for all top use cases | Prioritize data remediation work and route to `ai-ready-data-architecture` skill before re-running assessment | There is no shortcut: AI on bad data produces bad outputs that destroy stakeholder trust |
| Use case involves autonomous financial or medical decisions | Flag as high-risk; require ethics review and human-in-the-loop design before feasibility is confirmed | Salesforce AI Acceptable Use Policy requires human oversight for high-risk automated decisions |
| Org has Agentforce licenses but no use case shortlist | Run Pattern 1 (Discovery Workshop) against Salesforce's published Agentforce use case library to seed the brainstorm | Prevents blank-slate paralysis and anchors discussion to feasible, productized capabilities |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm scope and inputs.** Collect the candidate use case list, current license inventory, and any known data constraints. If no use case list exists, facilitate a brainstorm against the Salesforce Agentforce use case library and Trailhead AI use case identification module.
2. **Score the Impact-Effort matrix.** For each candidate, assign an Impact score (1–3) and an Effort score (1–3) with written justification. Place each in the appropriate quadrant: Quick Wins (high impact, low effort), Big Bets (high impact, high effort), Low-Hanging Fruit (low impact, low effort), Money Pits (low impact, high effort).
3. **Run feasibility scoring on shortlisted use cases.** For all Quick Wins and Big Bets, score all four feasibility dimensions: Technical (licenses, prerequisites), Operational (process fit, team capacity), Data Readiness (availability, quality, unification, governance — 1–3 each), Risk Profile (consequence of AI error, regulatory exposure).
4. **Apply the data readiness gate.** Any use case with a composite data readiness score below 6 is moved to a Blocked list with specific remediation requirements documented.
5. **Produce the prioritized shortlist.** Order remaining use cases by Impact-Effort quadrant first, then by data readiness score within each quadrant. Include a one-sentence rationale per use case.
6. **Frame ROI narratives.** For the top 3–5 use cases, document the primary value driver (cost reduction, revenue increase, risk mitigation, productivity), the key assumption that must hold, and the payback period category (< 6 months, 6–18 months, 18+ months).
7. **Document handoff to implementation.** Identify which skills or workstreams each approved use case routes to next: `ai-ready-data-architecture` for data remediation, `agentforce-service-ai-setup` for Service Einstein enablement, or a feature-specific implementation skill.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every candidate use case has an Impact score, Effort score, and quadrant assignment with written justification
- [ ] All Quick Wins and Big Bets have been scored across all four feasibility dimensions
- [ ] Data readiness sub-dimension scores (availability, quality, unification, governance) are recorded per use case
- [ ] Use cases with data readiness composite score below 6 are moved to Blocked list with remediation steps
- [ ] Prioritized shortlist is ordered and includes a one-sentence rationale per use case
- [ ] ROI narrative (value driver, key assumption, payback category) documented for top 3–5 use cases
- [ ] No implementation guidance has been provided — assessment outputs feed the implementation project intake, not substitute for it

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Einstein feature availability varies by edition AND license add-on** — Enterprise Edition + Sales Cloud does not include Einstein Lead Scoring by default; it requires the Einstein for Sales add-on. Similarly, generative AI features in Service Cloud require the Einstein for Service add-on even if the org has Unlimited Edition. Technical feasibility scores that skip license verification will produce incorrect "go" recommendations.
2. **Data Cloud is required for many Agentforce grounding use cases** — Agentforce agents that need to retrieve customer context at scale (e.g., "what did this customer buy last quarter") require Data Cloud for real-time unification. Assessing these use cases as feasible without confirming Data Cloud is licensed and populated leads to scoped-out implementations that cannot deliver the assessed value.
3. **Model training status affects Einstein predictive feature readiness** — Einstein Lead Scoring and Einstein Opportunity Scoring require a minimum record volume (typically 1,000+ records with sufficient outcome variance) before the model can train. An org may have the correct license but still have a feature stuck in "Gathering Data" state for weeks. This delay is not communicated during purchasing and must be included in the effort score.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Impact-Effort Matrix | Scored quadrant plot with all candidate use cases positioned and justified |
| Feasibility Scorecard | Per-use-case table with Technical, Operational, Data Readiness, and Risk scores |
| Prioritized Shortlist | Ordered list of approved use cases with rationale and sequencing recommendation |
| Data Readiness Gap List | Blocked use cases with sub-dimension scores and minimum remediation steps |
| ROI Narrative | Value driver, key assumption, and payback category per top use case |

---

## Related Skills

- `ai-ready-data-architecture` — Use when data readiness gaps are identified; covers Data Cloud ingestion, object schema design, and field quality improvement for AI features
- `agentforce-service-ai-setup` — Use when a Service Einstein use case has been approved and implementation is ready to begin; covers prerequisite verification, license activation, and feature sequencing
