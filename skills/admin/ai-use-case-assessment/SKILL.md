---
name: ai-use-case-assessment
description: "Identify, score, and prioritize Salesforce AI use cases before any implementation begins — opportunity identification, Impact-Effort matrix scoring, feasibility evaluation across Technical/Operational/Data/Risk dimensions, and ROI framing. NOT for the license checks and enablement steps once a use case is approved — use agentforce/agentforce-service-ai-setup or agentforce/agentforce-sales-ai-setup. NOT for making the data model AI-ready — use architect/ai-ready-data-architecture."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# AI Use Case Assessment

This skill activates when a practitioner or organization needs to decide **which AI use cases to pursue on Salesforce, in what order, and whether they are feasible** — before any implementation work begins. It produces a structured prioritization and feasibility output grounded in the Salesforce AI Use Case Identification framework.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License and edition confirmation:** Many Einstein features require specific add-ons. Einstein for Service generative features (Work Summaries, Service Replies) require the Einstein for Service add-on license; Agentforce requires the Agentforce platform license. Confirm what is purchased before scoring technical feasibility. UNVERIFIED (2026-10-20): which add-on license each Einstein or Agentforce feature needs is Salesforce Help / pricing material with no corpus line; the corpus lists feature settings, not licence bundles.
- **Data posture:** The single most common failure mode is assuming that CRM data is AI-ready. Verify whether Data Cloud (named Data 360 in the Winter '27 Metadata API guide; `CustomerDataPlatformSettings.enableCustomerDataPlatform`, api_meta 264 L11134-11159) is licensed and populated, whether key objects (Case, Lead, Opportunity) have sufficient record volume and field completeness for the features being assessed.
- **Stakeholder alignment on scope:** Assessment work frequently expands into implementation scoping mid-session. Stay inside the assessment boundary — the outputs of this skill feed an implementation project, not replace one.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which licences and add-ons are provisioned in this org, read from the org rather than from sales material? | Edition alone does not decide feature availability (Gotcha 1). | A technical-feasibility score that will not reverse at activation. |
| For each predictive use case, how are historical outcomes distributed (won/lost, converted/not)? | A lopsided outcome distribution degrades model training (Gotcha 2). | Which predictive use cases need a data-variance fix first. |
| Is Data Cloud enabled, and which sources are ingested, mapped to DMOs and identity-resolved? | A licence is not populated data (Gotcha 3). | The unification score per grounding use case. |
| Is the assessor reading the org's own Setup and metadata, or working from training material? | Course content does not show this org's prerequisites (Gotcha 4). | Evidence attached to every "go" verdict. |
| Can each use case be stated as one feature on one object producing one measurable output? | Strategic wording inflates impact scores (Gotcha 5). | Scores that compare like with like. |
| What happens if the AI output is wrong, and who reviews it before it reaches a customer? | High-risk use cases need human review designed in (Core Concept 2, Risk Profile). | The risk tier and the review gate per use case. |
| Which records and fields does each use case depend on, and how complete are they? | The data readiness gate blocks use cases on sparse data (Pattern 2). | The remediation list and the Blocked set. |

A proper assessment adds a written trail — licence evidence, data scores, risk tier — so the shortlist survives the first implementation review instead of being re-argued.

---

## Core Concepts

### 1. Impact-Effort Matrix

The Impact-Effort framework (UNVERIFIED (2026-10-20): attributed to Salesforce's AI use-case identification material, which is not in the corpus) organizes candidate use cases into four quadrants based on two axes: **business impact** (revenue, cost reduction, customer satisfaction, risk mitigation) and **implementation effort** (technical complexity, data readiness requirements, change management burden).

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

**Data Readiness** — Score data readiness across four sub-dimensions (UNVERIFIED (2026-10-20): the four-part model is attributed to a Salesforce blog, not a corpus guide): availability (does the data exist in the org?), quality (is it clean, consistent, deduplicated?), unification (is it unified across sources in Data Cloud?), and governance (is data access controlled, compliant with privacy regulations, and auditable?). Each sub-dimension can be scored 1 (not ready) to 3 (fully ready). A composite score below 6 typically means the use case should be gated pending data remediation.

**Technical evidence from metadata** — Retrieve the org's AI configuration before scoring Technical Feasibility: agents are `GenAiPlannerBundle` ("a container for all the topics and actions", api_meta 264 L79720-79721), topics are `GenAiPlugin` (L80308), actions are `GenAiFunction` (L78862); Einstein Opportunity Scoring is `OpportunityScoreSettings.enableOpportunityScoring`, default false (L126931-126955); Case Classification lives in `EinsteinAgentSettings` (L117831). Retrieval shows what is configured, not what is licensed.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Assessment probe: retrieve, never deploy. Settings members drop the "Settings" suffix (api_meta 264 L2474-2475). -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>GenAiPlannerBundle</name>
    </types>
    <types>
        <members>*</members>
        <name>GenAiPlugin</name>
    </types>
    <types>
        <members>*</members>
        <name>GenAiFunction</name>
    </types>
    <types>
        <members>OpportunityScore</members>
        <members>EinsteinAgent</members>
        <members>CustomerDataPlatform</members>
        <name>Settings</name>
    </types>
    <version>68.0</version>
</Package>
```

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
1. For each candidate use case, identify the primary data objects it depends on (e.g., Einstein Case Classification needs Case records with populated Subject and Description fields; Einstein Opportunity Scoring needs Opportunity history with stage progressions — UNVERIFIED (2026-10-20): these per-feature field requirements are not in the corpus).
2. Score each data source on the four sub-dimensions (availability, quality, unification, governance) on a 1–3 scale per sub-dimension.
3. Any use case with a composite data readiness score below 6 out of 12 is flagged as **Data Blocked** and removed from the active shortlist until remediation is confirmed.
4. Produce a remediation list: which objects need field completion campaigns, which sources need Data Cloud ingestion, which governance policies need to be documented.

**Why not skipping the data readiness gate:** The most common cause of failed AI projects in Salesforce orgs is activating a feature (e.g., Einstein Lead Scoring) against sparse or dirty data, which produces model outputs with no predictive validity. The business observes no value, trust in AI erodes, and the initiative is cancelled.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is new to AI and has no existing Data Cloud | Start with Low-Hanging Fruit and Quick Wins that do not require Data Cloud (e.g., Einstein Email Insights, Case Classification on clean Case data) | Builds trust and momentum before committing to Data Cloud investment |
| Stakeholders want an ROI estimate before approving | Produce a payback period narrative using a published, dated benchmark the client can cite rather than a custom financial model | Avoids false precision; anchors to published Salesforce customer evidence |
| Data readiness score is below 6 for all top use cases | Prioritize data remediation work and route to `ai-ready-data-architecture` skill before re-running assessment | There is no shortcut: AI on bad data produces bad outputs that destroy stakeholder trust |
| Use case involves autonomous financial or medical decisions | Flag as high-risk; require ethics review and human-in-the-loop design before feasibility is confirmed | Salesforce AI Acceptable Use Policy requires human oversight for high-risk automated decisions |
| Org has Agentforce licenses but no use case shortlist | Run Pattern 1 (Discovery Workshop) against Salesforce's published Agentforce use case library to seed the brainstorm | Prevents blank-slate paralysis and anchors discussion to feasible, productized capabilities |

UNVERIFIED (2026-10-20): three cells above have no corpus line — that Email Insights and Case Classification need no Data Cloud, any handle-time benchmark range, and an Acceptable Use Policy rule on human oversight. Quote a benchmark only with its published source and date; the earlier "20–30% reduction in handle time" figure had none.

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

1. **Einstein feature availability varies by edition AND license add-on** (UNVERIFIED (2026-10-20): licence bundling is not in the corpus) — Enterprise Edition + Sales Cloud does not include Einstein Lead Scoring by default; it requires the Einstein for Sales add-on. Similarly, generative AI features in Service Cloud require the Einstein for Service add-on even if the org has Unlimited Edition. Technical feasibility scores that skip license verification will produce incorrect "go" recommendations.
2. **Data Cloud is required for many Agentforce grounding use cases** — the packaging guide says prompt templates that use RAG, Retrievers or BYO LLM need an org with both GenAI and Data Cloud enabled (pkg2 264 L1459-1460). Agentforce agents that need to retrieve customer context at scale (e.g., "what did this customer buy last quarter") depend on it for unification (UNVERIFIED (2026-10-20): the "real-time" claim is not in the corpus). Assessing these use cases as feasible without confirming Data Cloud is licensed and populated leads to scoped-out implementations that cannot deliver the assessed value.
3. **Model training status affects Einstein predictive feature readiness** — Einstein Lead Scoring and Einstein Opportunity Scoring require a minimum record volume (typically 1,000+ records with sufficient outcome variance) before the model can train. An org may have the correct license but still have a feature stuck in "Gathering Data" state for weeks. UNVERIFIED (2026-10-20): the 1,000-record threshold and the "Gathering Data" status text have no corpus line. This delay is not communicated during purchasing and must be included in the effort score.

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

- `architect/ai-ready-data-architecture` — Use when data readiness gaps are identified; covers Data Cloud ingestion, object schema design, and field quality improvement for AI features
- `agentforce/agentforce-service-ai-setup` — Use when a Service Einstein use case has been approved and implementation is ready to begin; covers prerequisite verification, license activation, and feature sequencing
