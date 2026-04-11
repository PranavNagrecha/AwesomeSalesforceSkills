---
name: agentforce-sales-ai-setup
description: "Step-by-step setup and configuration of Einstein for Sales AI features: Opportunity Scoring, Pipeline Inspection AI insights, Einstein email insights and composition, and Forecasting AI. Covers prerequisites, license checks, feature sequencing, and data readiness validation. NOT for core Agentforce agent creation, agent topic design, Einstein Trust Layer configuration, or Einstein Activity Capture troubleshooting."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - User Experience
triggers:
  - "How do I set up Einstein for Sales from scratch in a new org?"
  - "What are the prerequisites before enabling Opportunity Scoring in Sales Cloud?"
  - "Pipeline Inspection AI insights are not appearing even though Einstein is enabled — what must be configured first?"
  - "Do I need a separate license to use Einstein email composition with generative AI for sales reps?"
  - "Einstein Opportunity Scoring says insufficient data — how many opportunities do I need and over what time range?"
  - "How do I sequence Einstein for Sales feature enablement to avoid broken dependencies?"
tags:
  - einstein-for-sales
  - opportunity-scoring
  - pipeline-inspection
  - einstein-email
  - forecasting-ai
  - sales-cloud
  - einstein-setup
  - license-management
inputs:
  - Sales Cloud org with Einstein for Sales add-on license or Einstein 1 Sales edition
  - Current org closed opportunity volume and date range
  - List of Einstein Sales features to enable (Opportunity Scoring, Pipeline Inspection, email composition, forecasting AI)
  - Whether Collaborative Forecasting is already enabled
  - Whether an Einstein Generative AI (Einstein GPT) license is provisioned
outputs:
  - Ordered enablement sequence with explicit prerequisite gates
  - License verification checklist
  - Data readiness assessment for Opportunity Scoring model training
  - Enabled and validated Einstein for Sales features
  - Permission set assignments for sales reps and forecast managers
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Agentforce Sales AI Setup

This skill activates when a practitioner needs to set up or configure the Einstein for Sales AI feature stack from scratch: Opportunity Scoring, Pipeline Inspection AI insights, Einstein email insights and composition, and Forecasting AI. It focuses on prerequisites, sequencing, license tiers, and data readiness — not feature troubleshooting after setup. It does NOT cover core Agentforce agent creation, agent topic design, Einstein Trust Layer setup, or Einstein Activity Capture configuration — use the dedicated skills for those areas.

The most common source of Einstein for Sales failures is skipping prerequisites: enablement steps have hard dependencies that Salesforce does not always surface clearly in Setup UI, and missing a dependency silently disables downstream features.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License tier:** Einstein for Sales is an add-on to Sales Cloud. It includes Opportunity Scoring, Einstein Activity Capture, and Pipeline Inspection. Einstein email *composition* (generative AI draft emails) requires a separate Einstein Generative AI license tier (previously Einstein GPT) beyond the base Einstein for Sales add-on. These are distinct SKUs — confirm both are provisioned before attempting to enable email composition.
- **Opportunity data volume:** Opportunity Scoring requires a minimum of 200 closed opportunities (Won + Lost combined) with a Closed Date within the last 24 months. The model will not train — and scores will not appear — if this threshold is not met. Verify in the org before enabling.
- **Forecasting configuration:** Pipeline Inspection AI insights depend on Collaborative Forecasting being enabled. If Collaborative Forecasting is not active, Pipeline Inspection will display data but AI insights (the predictive deal change signals) will be absent, with no clear error.
- **Sandbox limitations:** Einstein Opportunity Scoring does not train in sandboxes. Model training only runs against production org data. Do not attempt to validate score generation in a sandbox — use a developer org with real production-like data, or test only the enablement flow in sandbox.

---

## Core Concepts

### Opportunity Scoring Prerequisites and Model Training

Einstein Opportunity Scoring trains a machine learning model on your org's historical closed-won and closed-lost opportunities. The model outputs a 0–99 score on open opportunities plus score factors (top positive and negative drivers).

**Data gate:** The minimum is 200 closed opportunities with a Closed Date in the last 24 months. Salesforce evaluates this gate at training time. If data is insufficient, the model status shows "Insufficient Data" in Setup > Einstein > Opportunity Scoring. The feature toggle appears active, but no scores are generated — this is the most common "Einstein is enabled but scores are not showing" scenario.

**Training timeline:** Initial model training completes within 24–72 hours for qualifying orgs. The model retrains weekly. Scores appear on Opportunity records only after the first successful training pass.

**Sandbox behavior:** Training does not occur in sandboxes — this is a documented Salesforce platform constraint, not a configuration error. Never tell a practitioner that sandbox score absence indicates a setup problem; it is expected behavior.

### Pipeline Inspection AI Insights Dependency Chain

Pipeline Inspection is a Sales Cloud feature that shows deal movement signals, engagement data, and predictive AI insights for forecast managers. The AI insights layer within Pipeline Inspection has a strict prerequisite chain:

1. Einstein for Sales license must be active.
2. Opportunity Scoring model must reach "Active" (trained) status.
3. **Collaborative Forecasting must be enabled** — this is a hard dependency that is not enforced or communicated in the Pipeline Inspection enablement UI.

If Collaborative Forecasting is disabled, Pipeline Inspection shows deal activity and engagement data but the AI-driven insights column (predictive deal change signals, commit risk flags) does not appear. Admins frequently conclude Pipeline Inspection AI is broken when the real fix is enabling Collaborative Forecasting.

### License Tiers: Einstein for Sales vs. Einstein Generative AI

Einstein for Sales (the add-on or Einstein 1 Sales edition) includes:
- Opportunity Scoring
- Einstein Activity Capture
- Pipeline Inspection (with AI insights when Collaborative Forecasting is enabled)
- Einstein Relationship Insights
- Einstein Deal Insights (basic)

Einstein email **composition** — where a sales rep clicks "Generate Email" and a generative AI model drafts the email body — is a distinct feature requiring the **Einstein Generative AI license** (also called Einstein GPT in older documentation). This is a separate license tier that must be separately provisioned in Setup > Company Information > Feature Licenses.

**Key mistake:** Do not assume that enabling "Einstein for Sales" enables generative email composition. Assigning the Einstein for Sales permission set to a rep will not unlock AI email drafting if the org does not have the Einstein Generative AI add-on.

---

## Common Patterns

### Sequential Feature Enablement

**When to use:** Any new Einstein for Sales deployment where multiple features need to be enabled.

**How it works:** Follow this strict enablement order to prevent missing dependencies:

1. Verify Einstein for Sales license is provisioned (Setup > Company Information > Feature Licenses).
2. Enable Opportunity Scoring (Setup > Einstein > Sales > Opportunity Scoring). Wait for model training to complete (24–72 hours).
3. If email composition is needed: verify Einstein Generative AI license is provisioned, then enable Einstein Email (Setup > Einstein > Sales > Email).
4. Enable Collaborative Forecasting if not already active (Setup > Forecasts Settings).
5. Enable Pipeline Inspection (Setup > Pipeline Inspection). AI insights now appear because Opportunity Scoring is Active and Collaborative Forecasting is enabled.
6. Assign Einstein for Sales permission set to relevant users.

**Why not enable all at once:** Enabling Pipeline Inspection before Opportunity Scoring is Active results in the AI insights column never populating. Enabling before Collaborative Forecasting is on results in a silently partial Pipeline Inspection with no error message.

### Pre-Enablement Data Readiness Check

**When to use:** Before enabling Opportunity Scoring in any org, especially recently deployed or thinly-loaded orgs.

**How it works:** Run a SOQL query to check opportunity data volume before enabling the feature:

```sql
SELECT COUNT(Id)
FROM Opportunity
WHERE IsClosed = true
AND CloseDate = LAST_N_DAYS:730
```

If the count is below 200, the Opportunity Scoring model will not train. Options: (1) wait until the org accumulates more data, (2) import historical closed opportunities from a legacy system, or (3) document the limitation and set expectations with stakeholders that scores will not appear until the threshold is reached.

**Why not rely on Setup UI feedback:** The Setup UI enables the feature regardless of data volume. The "Insufficient Data" status only appears after the training pass fails — not before enablement.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fewer than 200 closed opportunities in last 2 years | Do not enable Opportunity Scoring yet | Model will not train; scores will never appear; creates false "broken" perception |
| Enabling Pipeline Inspection AI insights | Enable Collaborative Forecasting first | Hard dependency; no AI insights appear without it |
| Rep needs AI-drafted email composition | Verify Einstein Generative AI license separately | Distinct from Einstein for Sales add-on; not included by default |
| Testing Einstein for Sales in sandbox | Validate enablement flow only; do not expect scores | Opportunity Scoring model does not train in sandboxes |
| Org has Einstein for Sales but scores are missing after 72 hours | Check Setup > Einstein > Opportunity Scoring > Model Status | "Insufficient Data" means data gate not met; "Training" means wait; "Active" means check page layout |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring Einstein for Sales from scratch:

1. **Verify licenses** — In Setup > Company Information > Feature Licenses, confirm Einstein for Sales (or Einstein 1 Sales edition) is provisioned and seats are available. If email composition is in scope, confirm Einstein Generative AI license is also present. Document which licenses are confirmed before proceeding.
2. **Check Opportunity data readiness** — Run `SELECT COUNT(Id) FROM Opportunity WHERE IsClosed = true AND CloseDate = LAST_N_DAYS:730` in Developer Console or Workbench. If count is below 200, stop and align with the org owner on a data readiness timeline before enabling Opportunity Scoring.
3. **Enable Opportunity Scoring** — Setup > Einstein > Sales > Opportunity Scoring > toggle on. Note the timestamp. Monitor Setup > Einstein > Opportunity Scoring for model status every 24 hours until status shows "Active". Do not enable Pipeline Inspection until this step is complete and model is Active.
4. **Enable Collaborative Forecasting** — Setup > Forecasts Settings > Enable Forecasting. Configure at least one forecast type. This is required for Pipeline Inspection AI insights.
5. **Enable Pipeline Inspection** — Setup > Pipeline Inspection > Enable. Confirm that AI insights column is visible to forecast managers. If not visible, recheck Opportunity Scoring model status and Collaborative Forecasting state.
6. **Enable Einstein Email (if licensed)** — If Einstein Generative AI license is confirmed, go to Setup > Einstein for Sales > Email > Enable. Assign the Einstein for Sales Email permission set to relevant users. Test AI email generation from an Opportunity or Contact record.
7. **Assign permission sets and validate** — Assign Einstein for Sales permission set to pilot users. Verify Opportunity Score field appears on Opportunity page layout. Verify Pipeline Inspection is accessible from the Sales Cloud navigation. Collect feedback from 2–3 reps within 72 hours of model going Active.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Einstein for Sales license confirmed as provisioned in Setup > Company Information > Feature Licenses
- [ ] Einstein Generative AI license confirmed if email composition is in scope (separate from Einstein for Sales)
- [ ] Closed opportunity count verified >= 200 with Closed Date in last 24 months
- [ ] Opportunity Scoring model status is "Active" (not "Training" or "Insufficient Data")
- [ ] Collaborative Forecasting is enabled before Pipeline Inspection AI insights are expected
- [ ] Pipeline Inspection AI insights column visible to at least one forecast manager in the org
- [ ] Einstein for Sales permission set assigned to relevant users
- [ ] Opportunity Score field is on the Opportunity page layout for sales reps

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Opportunity Scoring silently skips training with insufficient data** — If the org has fewer than 200 closed opportunities in the last 24 months, the Opportunity Scoring model enters "Insufficient Data" status. The feature appears enabled in Setup, but no scores ever appear on records. There is no proactive warning — admins only discover the issue after checking model status.
2. **Pipeline Inspection AI insights require Collaborative Forecasting, not just Einstein for Sales** — Enabling Pipeline Inspection without Collaborative Forecasting active results in a functional Pipeline Inspection view with deal movement data but no AI-driven insights. There is no error or warning in the UI. This dependency is documented in Salesforce Help but not surfaced in the enablement wizard.
3. **Einstein email composition is a separate license, not included in Einstein for Sales** — Enabling Einstein for Sales and assigning its permission set to reps does not unlock AI email drafting. The generative email feature requires the Einstein Generative AI add-on license (distinct SKU). Orgs on Einstein 1 Sales may have it bundled, but standalone Einstein for Sales add-on customers must purchase it separately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| License verification checklist | Confirms Einstein for Sales and (if applicable) Einstein Generative AI licenses are provisioned before setup begins |
| Opportunity data readiness query result | COUNT of closed opportunities in last 24 months; gates Opportunity Scoring enablement |
| Enablement sequence log | Ordered record of which features were enabled, in what sequence, and model status timestamps |
| Permission set assignment confirmation | List of users assigned the Einstein for Sales permission set and (if applicable) Einstein Email permission set |

---

## Related Skills

- `einstein-copilot-for-sales` — Troubleshooting and optimization of Einstein Sales AI features after initial setup; covers EAC configuration, score factor analysis, and Einstein Relationship Insights
- `agentforce-agent-creation` — Core Agentforce agent creation; not covered by this skill
- `agentforce-guardrails` — Einstein Trust Layer and guardrail configuration for Agentforce agents
