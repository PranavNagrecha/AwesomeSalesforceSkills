---
name: einstein-copilot-for-sales
description: "Sales-specific AI features in Sales Cloud: Einstein Opportunity Scoring setup and optimization, Einstein Activity Capture configuration, AI email generation, Pipeline Inspection AI insights, and Einstein Relationship Insights. NOT for core Agentforce setup, agent topic design, or Einstein Trust Layer configuration."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "How do I enable Einstein Opportunity Scoring and why are my scores not showing up?"
  - "Einstein Activity Capture is not syncing emails or calendar events to Salesforce — how do I fix it?"
  - "How do I set up AI email generation for Sales reps in Sales Cloud?"
  - "Pipeline Inspection AI insights are not appearing for my forecast — what do I need to configure?"
  - "Einstein Relationship Insights is enabled but showing no connections — what are the requirements?"
tags:
  - einstein
  - copilot
  - sales-ai
  - opportunity-scoring
  - activity-capture
  - pipeline-inspection
  - email-generation
  - einstein-relationship-insights
inputs:
  - Sales Cloud org with Einstein for Sales add-on license or Einstein 1 Sales edition
  - List of Einstein Sales features to enable or troubleshoot
  - Current org data volume (opportunity count, closed date range, email sync status)
  - Permission sets and user assignments already in place
outputs:
  - Enabled and configured Einstein Sales AI features
  - Opportunity Scoring field populated and model trained
  - EAC sync running with correct exclusion rules
  - Pipeline Inspection AI insights visible to forecast managers
  - Email recommendations and composition enabled for reps
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Einstein Copilot for Sales

This skill activates when a practitioner needs to enable, configure, review, or troubleshoot the sales-specific AI features in Sales Cloud: Opportunity Scoring, Einstein Activity Capture (EAC), AI email generation, Pipeline Inspection AI insights, and Einstein Relationship Insights. It does NOT cover core Agentforce agent creation, agent topic design, or Einstein Trust Layer setup — use the dedicated skills for those areas.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License type:** Confirm whether the org has Einstein for Sales (add-on), Einstein 1 Sales edition, or only core Sales Cloud. Different features require different licenses — Opportunity Scoring and EAC are included in Einstein for Sales; Pipeline Inspection requires Sales Cloud Einstein specifically; Einstein email generation requires the Einstein Generative AI (Einstein GPT) license layer on top of Einstein for Sales.
- **Data readiness:** Opportunity Scoring requires a minimum of 200 closed opportunities (Won + Lost) with a Closed Date within the last two years. EAC requires a connected Microsoft Exchange/Office 365 or Google Workspace account.
- **Sandbox limitations:** Einstein Opportunity Scoring does not train in sandboxes. The model trains on production data only. Scores may not appear in sandboxes even when the feature is enabled.

---

## Core Concepts

### Einstein Opportunity Scoring

Einstein Opportunity Scoring uses a machine learning model trained on your org's historical closed opportunities to predict the likelihood a current open opportunity will close as Won. The score (0–99) appears on the Opportunity record as the `Opportunity Score` field and is accompanied by score factors that explain the top positive and negative influences.

**Setup path:** Setup > Einstein > Sales > Opportunity Scoring > Enable. Salesforce automatically starts model training; initial training completes within 24–72 hours for orgs that meet data requirements. The model retrains weekly. Scores appear on records once the model completes its first training pass.

**Data requirements:** A minimum of 200 closed opportunities (any mix of Won and Lost) with a Closed Date in the last 24 months. If fewer than 200 exist, the feature activates but the model defers training and no scores are generated. The scoring model uses standard and custom fields on Opportunity and related objects; adding high-signal custom fields to the model is supported via the Opportunity Scoring configuration screen.

**Score fields:** `Opportunity_Score__c` (numeric 0–99), `Opportunity_Score_Change__c` (direction of change since last scoring run), and score factor fields that surface top positive/negative drivers. These are standard Einstein fields added to page layouts by the admin.

### Einstein Activity Capture (EAC)

Einstein Activity Capture automatically syncs emails and calendar events between a connected email/calendar account and Salesforce, attaching activities to related contacts and opportunities without rep manual entry. EAC uses a separate data store (not standard Activity/Event/Task objects) for synced activities, which has significant implications for reporting.

**Sync directions:** Email sync is uni-directional (email client to Salesforce) by default for inbound; calendar sync is bi-directional by default but configurable. Admins configure sync settings per Connected Account or via Configuration profiles.

**EAC objects:** Synced emails land on `EmailMessage` linked via `ActivityShare`. Synced events land on `Event` with `IsActivitySyncEnabled = true`. However, the Einstein Activity Capture data is surfaced through the Activity Timeline component on records, not via standard report types — the `Activities` report type does not surface EAC-synced activities unless the org has Enhanced Email enabled and specific report types configured.

**Exclusion rules:** EAC supports exclusion rules at the domain level (exclude emails from/to certain domains), the address level, and via private flags on individual events. Admins should configure exclusion rules before rollout to prevent personal email from syncing into Salesforce records.

### Pipeline Inspection AI Insights

Pipeline Inspection is a Sales Cloud view that surfaces AI-powered insights about deal health and forecast changes alongside the pipeline table. The AI insights highlight opportunities with significant score changes, deals at risk due to inactivity, and gaps between committed forecasts and historical close rates.

**Requirements:** Pipeline Inspection requires Sales Cloud Einstein or the Einstein for Sales add-on and must be enabled separately from Opportunity Scoring (Setup > Sales > Pipeline Inspection). Users need the `Sales Cloud Einstein` or `Einstein Analytics for Sales` permission. Pipeline Inspection AI insights draw on Opportunity Scoring data — Opportunity Scoring must be trained and returning scores before insights appear.

**What insights surface:** Deal change indicators (score up/down), activity gaps (no logged activity in N days relative to deal stage), forecast risk flags (committed deals with low scores), and pipeline trend comparisons week-over-week.

### Einstein Email Generation and Email Recommendations

Einstein provides two related email AI capabilities for Sales reps:

1. **Einstein Email Recommendations** (older feature): Surfaces suggested email replies in the activity composer based on the email thread context. Requires Einstein for Sales license and the `Einstein Email Recommendations` permission set.
2. **Einstein Email Composition / Generative Email** (Spring '25+): Uses generative AI to draft full emails from a prompt or from opportunity context. Requires an Einstein Generative AI (Einstein GPT) license — this is NOT included in the base Einstein for Sales add-on and must be purchased separately or included with Einstein 1 Sales. Drafts are grounded through the Einstein Trust Layer before being shown to the rep.

### Einstein Relationship Insights

Einstein Relationship Insights mines email content and news sources to surface professional relationship connections between contacts, accounts, and leads — showing reps who at their company has a relationship with a target contact. Requires the `Einstein Relationship Insights` permission and the Einstein for Sales license. The feature requires that EAC is enabled and email sync is running; without email data, the relationship graph cannot be built.

---

## Common Patterns

### Mode 1: Enable and Configure from Scratch

**When to use:** Net-new org enabling Einstein Sales AI features for the first time.

**How it works:**

1. Verify license: Confirm Einstein for Sales or Einstein 1 Sales is provisioned (Setup > Company Information > Feature Licenses).
2. Enable Einstein: Setup > Einstein > Sales > toggle each feature on sequentially (Opportunity Scoring first, then EAC, then Pipeline Inspection, then email features).
3. Assign permission sets: Assign `Sales Cloud Einstein` or `Einstein for Sales User` permission sets to target users. Do not use profiles alone — Einstein features are permission-set gated.
4. Configure EAC: Setup > Einstein > Einstein Activity Capture > Connect Accounts. Create a Configuration profile defining sync direction, object scope (Contacts, Leads, Opportunities), and exclusion domains. Assign the profile to users.
5. Add score fields to layouts: Add `Opportunity Score` and `Score Change` fields to the Opportunity page layout and add the Pipeline Inspection component to the Forecast page.
6. Wait for model training: Opportunity Scoring training is asynchronous. Monitor Setup > Einstein > Opportunity Scoring for training status. Scores appear only after the first training pass completes (24–72 hours).

**Why not enabling all at once without verification:** Enabling Pipeline Inspection before Opportunity Scoring is trained results in the AI insights panel showing no data, which users perceive as a bug rather than a training lag.

### Mode 2: Review and Optimize Scoring Quality

**When to use:** Scoring is running but reps or managers question score accuracy; model has been live for 30+ days.

**How it works:**

1. Check model stats: Setup > Einstein > Opportunity Scoring > View Model. Salesforce surfaces overall model accuracy (AUC score) and the top fields the model weighted. An AUC below 0.7 indicates poor signal.
2. Identify low-signal fields: If reps do not fill in Stage, Close Date, or Amount consistently, the model has poor training data. Run a data quality report to quantify completeness on key Opportunity fields.
3. Add high-signal custom fields: If your sales process has custom qualification fields (e.g., `Competitor__c`, `Budget_Confirmed__c`), add them to the scoring model via the Opportunity Scoring field selector. The model retrains weekly and will incorporate new fields on the next training pass.
4. Tune score visibility: Add score change indicators to list views and report charts so managers can act on deals whose score drops significantly week-over-week.

### Mode 3: Troubleshoot EAC Not Syncing

**When to use:** Reps report emails or calendar events not appearing in the Activity Timeline after EAC is enabled.

**How it works:**

1. Check Connected Account status: Setup > Einstein > Einstein Activity Capture > Connected Accounts. Look for authentication errors or expired tokens. Re-authorize if needed.
2. Verify configuration profile assignment: Confirm the user is assigned to an EAC configuration profile. Users without a profile assignment do not sync.
3. Check exclusion rules: If the email address or domain is on an exclusion list, emails from that sender are silently skipped.
4. Check object mapping: Ensure the configuration profile includes the correct objects (e.g., Opportunities). If only Contacts is enabled, opportunity-related emails will not relate to opportunity records.
5. Validate email matching: EAC matches emails to Salesforce records by email address. If a contact's email address in Salesforce does not match the sender/recipient in the email, no automatic relation is created.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has fewer than 200 closed opps | Do not enable Opportunity Scoring yet; focus on pipeline growth | Model will not train; feature activates but returns no scores, creating confusion |
| Reps need AI-drafted emails | Verify Einstein Generative AI license before enabling; do not assume Einstein for Sales covers it | Email composition is a separate SKU (Einstein 1 Sales or Einstein GPT add-on) |
| Pipeline Inspection shows no AI insights | Confirm Opportunity Scoring model is trained and returning scores first | Pipeline Inspection AI insights depend entirely on Opportunity Scoring data |
| EAC emails not relating to opportunities | Check that the configuration profile object scope includes Opportunities and that contact email addresses match | EAC relates by email address match only |
| Einstein Relationship Insights returns no connections | Confirm EAC email sync has been running for 30+ days with sufficient email volume | The relationship graph requires historical email data to mine; it is not instant |
| Sandbox testing of Opportunity Scoring | Test UI configuration and field layout only; do not expect scores in sandbox | Model trains on production data only |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking Einstein Sales AI work complete:

- [ ] Einstein for Sales or Einstein 1 Sales license confirmed in Setup > Company Information > Feature Licenses
- [ ] Correct permission sets (`Sales Cloud Einstein` or `Einstein for Sales User`) assigned to all target users
- [ ] Opportunity Scoring model training status confirmed as complete (not "In Progress" or "Insufficient Data")
- [ ] EAC Connected Accounts show no authentication errors and at least one configuration profile is assigned to users
- [ ] `Opportunity Score` and `Score Change` fields added to Opportunity page layout and list views
- [ ] Pipeline Inspection component added to Forecast page and AI insights visible for at least one deal
- [ ] EAC exclusion domains configured to prevent personal/legal email from syncing
- [ ] If email composition is required: Einstein Generative AI (Einstein GPT) license confirmed and feature enabled
- [ ] Einstein Relationship Insights: EAC email sync confirmed running before expecting connection data

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Opportunity Scoring does not train in sandboxes** — Enabling Opportunity Scoring in a full sandbox activates the UI and fields but the model will never produce scores. The ML model trains exclusively on production org data. Do not use sandbox to validate that scoring is working end-to-end.

2. **EAC synced activities are NOT in standard Activity report types** — EAC email and calendar data is stored in a specialized data store and surfaced through the Activity Timeline component. Standard reports on `Activities`, `Tasks`, or `Events` do NOT include EAC-synced items unless the org uses specific Einstein Activity Capture report types. This surprises managers who expect EAC data to appear in their existing activity dashboards.

3. **Einstein email composition requires Einstein Generative AI license, not just Einstein for Sales** — Einstein for Sales includes Opportunity Scoring, EAC, Pipeline Inspection, and Email Recommendations. It does NOT include generative email drafting (Einstein Generative Email). That feature requires the Einstein 1 Sales edition or the separate Einstein Generative AI add-on. Orgs that purchase only Einstein for Sales will see no email composition button.

4. **Pipeline Inspection AI insights require Opportunity Scoring to be trained** — Pipeline Inspection can be enabled independently of Opportunity Scoring but its AI insights panel will show no data until Opportunity Scoring has completed model training. The feature does not display an explicit dependency warning; it simply shows an empty insights panel, which looks like a bug.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Einstein Opportunity Scoring | Model trained, score fields on layout, score factors visible on opportunity records |
| EAC configuration profile | Sync direction, object scope, and exclusion rules defined and assigned to users |
| Pipeline Inspection setup | AI insights panel visible on Forecast page with deal health indicators |
| Email generation enabled | Einstein Generative Email or Email Recommendations active for target users |
| Einstein Sales AI checklist | Completed review checklist confirming all prerequisites met |

---

## Related Skills

- `einstein-trust-layer` — Configure data masking, toxicity filters, and audit trails for all Einstein generative features before enabling email generation
- `agent-topic-design` — Use when building custom Agentforce agent topics for Sales processes beyond the built-in Einstein Sales AI features
- `agentforce-agent-creation` — Use when creating a full custom Agentforce agent for Sales use cases rather than enabling the pre-built Einstein Sales AI features
