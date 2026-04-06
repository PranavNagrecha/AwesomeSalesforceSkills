---
name: lead-scoring-requirements
description: "Use this skill when designing or documenting a lead scoring model in Salesforce Sales Cloud or Account Engagement: qualifying criteria, MQL/SQL threshold definitions, scoring dimensions (demographic, firmographic, behavioral), and sales handoff SLA. NOT for Einstein Lead Scoring (AI-based predictive scoring) or Account Engagement (Pardot) automation rule configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "How should we define what a marketing-qualified lead looks like in Salesforce?"
  - "We need to score leads based on job title, company size, and website behavior — where do we start?"
  - "Sales and marketing can't agree on when a lead is ready to hand off — help us document the handoff criteria"
  - "What fields and thresholds do we need to configure to route hot leads automatically to reps?"
  - "How do we design a composite lead score using formula fields in Salesforce?"
tags:
  - lead-scoring
  - mql
  - sql
  - lead-qualification
  - handoff-sla
  - formula-fields
  - account-engagement
  - sales-cloud
inputs:
  - "Business definition of an ideal customer profile (ICP): target industries, company size, title/persona"
  - "List of behavioral signals available (form fills, content downloads, page visits, email engagement)"
  - "Current lead volume and source breakdown"
  - "Existing sales process: BANT, MEDDIC, or custom qualification framework"
  - "Agreement on MQL score threshold and SQL acceptance criteria between marketing and sales"
outputs:
  - "Lead scoring dimension matrix with point values per criterion"
  - "MQL and SQL threshold definitions with agreed score ranges"
  - "Field map: custom numeric fields required on the Lead object"
  - "Formula field logic for composite score calculation"
  - "Handoff SLA document: score threshold, required field completeness, max response time, recycle criteria"
  - "Review checklist for validating the implemented model"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Lead Scoring Requirements

This skill activates when a practitioner needs to design, document, or validate a manual or rules-based lead scoring model in Salesforce Sales Cloud — defining the qualifying criteria, score dimensions, MQL/SQL thresholds, and the sales handoff SLA that bridges marketing pipeline to revenue pipeline.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses Account Engagement (Pardot) or native Sales Cloud only. Account Engagement has a built-in prospect scoring engine (0–100 default) and a separate grading system (A–F) that must be mapped to Salesforce Lead fields. Native Sales Cloud requires all scoring logic to live in formula fields or Flow-maintained numeric fields.
- Identify the ICP in concrete, fieldable terms. Vague ICP definitions ("mid-market B2B") produce unmaintainable scoring rules. Push for specific values: `NumberOfEmployees` ranges, `Industry` picklist values, `Title` keyword lists.
- Understand lead volume. If the org receives more than 200 leads/day, avoid score recalculation via record-triggered Flow on every edit — use scheduled Flow or batch Apex to recompute scores on a cadence.
- Confirm what behavioral signals are capturable. Web-to-Lead captures form data only. Page-visit and email-click signals require Account Engagement or a marketing automation integration that writes back to a custom field.

---

## Core Concepts

### Scoring Dimensions

A lead scoring model combines two orthogonal dimensions:

1. **Fit (demographic/firmographic)** — static attributes that describe how closely the lead matches the ICP. Common fields: `Industry`, `NumberOfEmployees`, `AnnualRevenue`, `Title`, `LeadSource`. These change rarely after creation.
2. **Interest/Engagement (behavioral)** — dynamic signals that indicate intent. Examples: number of content downloads, email click count, demo request, pricing page visit. These must be written back to Lead fields from a marketing automation system or tracked via custom Activity-based Flow.

The composite score is the weighted sum of both dimensions. Salesforce's sample formula approach uses separate numeric fields for each dimension and a master formula field that sums them. Source: [Salesforce Help — Sample Scoring Calculation Formulas](https://help.salesforce.com/s/articleView?id=sf.leads_scoring_formula.htm).

### MQL and SQL Thresholds

**MQL (Marketing-Qualified Lead):** A score threshold at which marketing certifies the lead is worth sales attention. The MQL threshold must be agreed upon jointly by marketing and sales ops — not set unilaterally. A typical B2B starting point is a composite score ≥ 50 out of 100, but the right number depends on acceptable false-positive and false-negative rates from historical conversion data.

**SQL (Sales-Qualified Lead):** After a rep reviews an MQL, they apply a structured qualification framework (BANT: Budget, Authority, Need, Timeline; or MEDDIC: Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion). An SQL is a lead the rep has verified meets the minimum threshold for an active sales cycle. SQLs are typically converted to Opportunities.

The boundary between MQL and SQL must be documented with explicit criteria, not left to rep discretion — otherwise recycle and reporting data is unreliable.

### Handoff SLA

The handoff SLA governs what happens at each transition:

- **Score threshold** — the minimum composite score for automatic MQL flag
- **Required field completeness** — minimum set of fields that must be populated before handoff (e.g., `Company`, `Title`, `Phone` or `Email`, `LeadSource`)
- **Max response time** — how long a rep has to accept or recycle an MQL (common: 1 business day for hot MQLs, 3 days for warm)
- **Recycle criteria** — conditions under which a lead is returned to marketing nurture: no response, wrong timing, not a decision-maker

Without a documented SLA, leads fall into a "black hole" and attribution data becomes meaningless.

### Salesforce Field Implementation

Lead scoring in native Sales Cloud uses:

- One or more **numeric custom fields** (e.g., `Fit_Score__c`, `Engagement_Score__c`) maintained by Flow or Apex
- One **formula field** (e.g., `Composite_Score__c`) that sums or weights the dimension fields: `Fit_Score__c + Engagement_Score__c`
- A **picklist or checkbox field** for lead status flags: `Is_MQL__c` (checkbox), `MQL_Date__c` (date/time), `SQL_Date__c`
- Optional: a **Lead Stage** custom picklist: `Raw → Nurture → MQL → Accepted → SQL → Converted/Recycled`

Formula fields cannot be filtered in reports unless you also maintain a mirror numeric field. If MQL routing via Assignment Rules or Flow depends on the score, the score must live in a stored numeric field, not a formula field. Source: [Salesforce Help — Customize Scoring Rules](https://help.salesforce.com/s/articleView?id=sf.leads_scoring.htm).

---

## Common Patterns

### Pattern: Weighted Composite Score with Dimension Fields

**When to use:** Org is Sales Cloud-only (no Account Engagement), or Account Engagement score needs to be supplemented with CRM-side firmographic fit data.

**How it works:**

1. Create `Fit_Score__c` (Number, 0 decimal) — updated by a record-triggered Flow that evaluates `Industry`, `NumberOfEmployees`, `Title` against point tables.
2. Create `Engagement_Score__c` (Number, 0 decimal) — updated by a Flow triggered when marketing writes activity signals back to the Lead (e.g., incrementing a `Content_Downloads__c` counter).
3. Create `Composite_Score__c` as a stored Number field updated by Flow: `Fit_Score__c + Engagement_Score__c`
4. Create `Is_MQL__c` (Checkbox) set to true by an entry-criteria Flow when `Composite_Score__c >= [threshold]` AND required fields are populated.

**Why not a single formula field for everything:** Assignment Rules and Flow entry criteria cannot reference formula fields reliably when the formula depends on other formula fields (cross-object formula restrictions). Storing dimension scores as real number fields keeps the automation reliable and the data reportable.

### Pattern: Account Engagement Score + Salesforce Grade Composite

**When to use:** Account Engagement (Pardot) is the primary marketing automation platform and already maintains a prospect score (0–100) and grade (A–F).

**How it works:**

1. Map the Account Engagement `Score` field to a synced Lead/Contact field (`Pardot_Score__c` or the standard `Score` field if enabled).
2. Map the Account Engagement `Grade` to a numeric field (`Pardot_Grade_Numeric__c`) via a Flow that converts letter grades to numbers: A=5, B=4, C=3, D=2, F=1.
3. Define MQL as: `Pardot_Score__c >= 50 AND Pardot_Grade_Numeric__c >= 4` (score ≥ 50 AND grade B or better).
4. Use a Flow to stamp `MQL_Date__c` and notify the assigned rep when both conditions are met.

**Why not use only Account Engagement score:** A high engagement score without fit (grade) produces false positives — a competitor researching your product or a student writing a paper can score highly. The two-dimensional model filters for genuine prospects.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| No marketing automation, Sales Cloud only | Formula + stored numeric fields, record-triggered Flow for dimension scores | All scoring logic stays in CRM; no sync dependency |
| Account Engagement active, single scoring model | Use AE Score + AE Grade synced to Lead fields, Flow for MQL stamping | Avoids duplicating scoring logic across two systems |
| High lead volume (>200/day) and complex scoring | Scheduled Flow or batch Apex to recalculate scores nightly | Record-triggered Flow on high-volume creates governor limit risk |
| Sales disputes MQL quality regularly | Tighten fit dimension weights, raise threshold, add required field gate | Score threshold and field gate together reduce false positives |
| Score must appear in Assignment Rules | Store composite score in a Number field, not a Formula field | Assignment Rules cannot reliably filter on formula fields |
| Lead recycle must be tracked for attribution | Add `Recycle_Count__c` and `Recycle_Reason__c` fields, update in SLA Flow | Without recycle tracking, nurture re-entry data is lost |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Align on ICP and scoring dimensions.** Run a discovery session with marketing and sales ops to map the ICP to specific Salesforce fields and collect behavioral signal availability. Output: a scoring dimension matrix with draft point values.
2. **Define MQL and SQL thresholds.** Get explicit, documented agreement on the composite score range that constitutes an MQL and the BANT/MEDDIC criteria a rep must confirm for SQL status. Record the thresholds and acceptance criteria in the handoff SLA document.
3. **Map required Salesforce fields.** List every field needed: dimension score fields (numeric), composite score field (formula or numeric), status flags (`Is_MQL__c`, `MQL_Date__c`, `SQL_Date__c`), a Lead Stage picklist, and recycle tracking fields. Confirm none already exist under a different name to avoid duplication.
4. **Design the automation.** Specify whether dimension scores are updated by record-triggered Flow, scheduled Flow, or an external system write-back. Document entry criteria, actions, and exit criteria for each Flow. Confirm the composite score field type (stored vs. formula) based on whether it will be used in Assignment Rules or Flow conditions.
5. **Document the handoff SLA.** Produce a written SLA covering: score threshold for MQL flag, required populated fields before handoff, rep response time target, and recycle process for unaccepted MQLs. Get sign-off from both marketing and sales leadership.
6. **Validate the model with historical data.** Before go-live, back-score a sample of 100–200 closed-won opportunities and 100–200 closed-lost leads using the proposed formula to calibrate thresholds. Adjust weights if the threshold produces too many or too few MQLs relative to historical conversion rate.
7. **Review against the checklist.** Run through the review checklist below and confirm all items pass before handing the model to the build team.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Scoring dimension matrix is complete with a point value for every criterion, and total max score is documented
- [ ] MQL threshold and SQL acceptance criteria are signed off by both marketing and sales leadership
- [ ] All required Lead object fields are identified: dimension score fields (Number), composite score field, `Is_MQL__c`, `MQL_Date__c`, `SQL_Date__c`, Lead Stage picklist, `Recycle_Count__c`, `Recycle_Reason__c`
- [ ] Composite score field type is Number (not Formula) if it will be referenced in Flow conditions or Assignment Rules
- [ ] Automation design specifies trigger type (record-triggered vs. scheduled), entry criteria, and actions
- [ ] Handoff SLA document covers: threshold, required field gate, response time, and recycle process
- [ ] Historical back-scoring or threshold calibration has been performed on a sample of closed records
- [ ] Einstein Lead Scoring is explicitly excluded from scope or documented as a future phase

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Formula fields cannot be used in Flow entry criteria or Assignment Rule conditions** — If the composite score is stored only as a formula field, you cannot reference it in a Flow's entry criteria (`{!Lead.Composite_Score__c} >= 50` will fail with an error or silently not trigger). Store the composite score in a real Number field updated by Flow when either dimension score changes.
2. **Account Engagement sync overwrites CRM-side edits to synced score fields** — AE syncs its prospect score to Salesforce Lead/Contact, but if a Salesforce admin or Flow writes a different value to the synced score field, the next AE sync will overwrite it. Do not build CRM-side scoring logic that writes to the AE-synced score field.
3. **Record-triggered Flows fire on every Lead save, including mass updates** — A Flow that recalculates all dimension scores on every Lead save will fire thousands of times during a data load or list import, consuming Flow interview limits and potentially causing org-wide slowdowns. Use a scheduled Flow for score recalculation on high-volume orgs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Scoring dimension matrix | Table of all scoring criteria with point values per value, organized by dimension (fit vs. engagement) |
| MQL/SQL threshold definition | Written agreement on composite score thresholds, SQL acceptance criteria, and escalation path |
| Lead object field map | List of all custom fields required, with API name, data type, and owning system |
| Handoff SLA document | Written SLA covering threshold, required fields, response time, and recycle rules |
| Automation design spec | Flow or Apex trigger design: entry criteria, actions, exit criteria for each automation |

---

## Related Skills

- `lead-management-and-conversion` — covers the mechanics of converting a Lead to Account/Contact/Opportunity once SQL criteria are met
- `requirements-gathering-for-sf` — upstream skill for structuring the discovery sessions needed to produce a scoring dimension matrix
- `assignment-rules` — governs how MQL-flagged leads are routed to the right rep queue after the score threshold is crossed
