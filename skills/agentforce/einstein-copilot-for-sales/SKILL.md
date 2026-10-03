---
name: einstein-copilot-for-sales
description: "Sales-specific AI features in Sales Cloud: Einstein Opportunity Scoring setup and optimization, Einstein Activity Capture configuration, AI email generation, Pipeline Inspection AI insights, and Einstein Relationship Insights. NOT for the license check and enablement sequence before any of these are turned on — use agentforce/agentforce-sales-ai-setup. NOT for the Service Cloud equivalents such as Case Classification and Work Summaries — use agentforce/einstein-copilot-for-service."
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
  - "check if my org has enough closed opportunities for Einstein Opportunity Scoring"
  - "turn on Einstein Activity Capture with metadata settings"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Einstein Copilot for Sales

This skill activates when a practitioner needs to enable, configure, review, or troubleshoot the sales-specific AI features in Sales Cloud: Opportunity Scoring, Einstein Activity Capture (EAC), AI email generation, Pipeline Inspection AI insights, and Einstein Relationship Insights. Terminology: the Generative AI guide says the default Agentforce agent was formerly known as Einstein Copilot for Salesforce; this skill keeps its older name for search, and covers the Sales Cloud Einstein features rather than the agent. It does NOT cover core Agentforce agent creation, subagent design (subagents were called topics before April 2026), or Einstein Trust Layer setup, use the dedicated skills for those areas.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License type:** Confirm on the Company Information page which entitlements exist. The names are easy to confuse: the Generative AI guide lists the **Einstein for Sales** add-on as one that carries generative AI usage (Einstein Requests), while scoring model factors are documented against a **Sales Cloud Einstein** license (Object Reference). UNVERIFIED (2026-10-03): the earlier per-feature license mapping (which features each SKU includes); it came from Help articles that do not fetch, and its claim that generative email needs a license beyond Einstein for Sales contradicts the Generative AI guide.
- **Data readiness:** Opportunity Scoring requires **at least 200 closed-WON opportunities AND at least 200 closed-LOST opportunities** in the last 24 months, each with a lifespan of at least 2 days, two separate floors, not 200 combined. UNVERIFIED (2026-10-03): these figures rest on a Help article that does not fetch. EAC requires a connected Microsoft Exchange/Office 365 or Google Workspace account.
- **Sandbox limitations:** Einstein Opportunity Scoring does not train in sandboxes. The model trains on production data only. Scores may not appear in sandboxes even when the feature is enabled. UNVERIFIED (2026-10-03): Help-only claim.

---

## Questions to Ask Before Configuring

Ask these before enabling any feature. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which entitlements does the org actually have?" | "Einstein for Sales" and "Sales Cloud Einstein" are different entitlements with different features (Gotcha 3) | A feature-to-entitlement map read from Company Information | No promise that the org cannot deliver |
| "How many closed-won and closed-lost opportunities exist in the last 24 months?" | Scoring needs both floors, counted separately (Gotcha 1) | Two counts from the readiness queries | A go or no-go for scoring before anyone waits for scores |
| "Who should see captured email, and what must never sync?" | Activity Capture shares with everyone by default for new users (Gotcha 8) | Sharing defaults, the sensitive-email filter and exclusion rules | Private-by-default capture that passes a privacy review |
| "Which reports must show captured activity?" | Captured activity may not appear in standard activity reports (Gotcha 2) | The reports that must work and the sync setting to test | A reporting plan validated before rollout |
| "Who needs to see why a deal scores low?" | Model factors need a permission that is off by default (Gotcha 7) | The users to grant View Scoring Model Factors | Explainable scores for the people who coach on them |
| "Will these settings be promoted as metadata?" | Settings members must be named, and settings deploys write every element sent (Gotcha 9) | A settings bundle in source control | The same configuration in every org |

## Core Concepts

### Einstein Opportunity Scoring

Einstein Opportunity Scoring uses a machine learning model trained on your org's historical closed opportunities to predict the likelihood a current open opportunity will close as Won. The score (0–99) appears on the Opportunity record as the `Opportunity Score` field and is accompanied by score factors that explain the top positive and negative influences.

**Setup path:** Setup > Einstein > Sales > Opportunity Scoring > Enable. Salesforce automatically starts model training; initial training completes within 24–72 hours for orgs that meet data requirements. The model retrains weekly. Scores appear on records once the model completes its first training pass.

**Data requirements:** **at least 200 closed-WON opportunities AND at least 200 closed-LOST opportunities** in the last 24 months, each with a lifespan of at least 2 days. "Any mix" is wrong — an org with 350 won and 20 lost fails. Salesforce additionally expects the standard `Stage` field to be in use and at least 12 months of opportunity history with an update in each month. If either floor is unmet, the feature activates but the model defers training and no scores are generated. The scoring model uses standard and custom fields on Opportunity and related objects; adding high-signal custom fields to the model is supported via the Opportunity Scoring configuration screen.

**Score fields:** the standard field is `Opportunity.IqScore` (label Opportunity Score), "the likelihood, measured on a scale of 1 to 99, that an opportunity will be won", available from API 41.0 when Einstein Opportunity Scoring is enabled (Object Reference). Model factors are queryable from `SalesAIScoreModelFactor` with the View Scoring Model Factors permission. The earlier names `Opportunity_Score__c` (0 to 99) and `Opportunity_Score_Change__c` were wrong; UNVERIFIED (2026-10-03): any standard score-change field. Add the score to page layouts and list views.

### Einstein Activity Capture (EAC)

Einstein Activity Capture automatically syncs emails and calendar events between a connected email/calendar account and Salesforce, attaching activities to related contacts and opportunities without rep manual entry. EAC uses a separate data store (not standard Activity/Event/Task objects) for synced activities, which has significant implications for reporting.

**Sync directions:** Email sync is uni-directional (email client to Salesforce) by default for inbound; calendar sync is bi-directional by default but configurable. Admins configure sync settings per Connected Account or via Configuration profiles.

**EAC objects:** Synced emails land on `EmailMessage` linked via `ActivityShare`. Synced events land on `Event` with `IsActivitySyncEnabled = true`. However, the Einstein Activity Capture data is surfaced through the Activity Timeline component on records, not via standard report types — the `Activities` report type does not surface EAC-synced activities unless the org has Enhanced Email enabled and specific report types configured.

**Exclusion rules:** EAC supports exclusion rules at the domain level (exclude emails from/to certain domains), the address level, and via private flags on individual events. Admins should configure exclusion rules before rollout to prevent personal email from syncing into Salesforce records.

### Pipeline Inspection AI Insights

Pipeline Inspection is a Sales Cloud view that surfaces AI-powered insights about deal health and forecast changes alongside the pipeline table. The AI insights highlight opportunities with significant score changes, deals at risk due to inactivity, and gaps between committed forecasts and historical close rates.

**Requirements:** Pipeline Inspection is enabled separately from Opportunity Scoring (`OpportunitySettings.enablePipelineInspection`, which also turns on historical trending; additional Setup configuration is required, per the Metadata API reference). UNVERIFIED (2026-10-03): the earlier license and permission names for Pipeline Inspection, and the claim that its AI insights need a trained scoring model.

**What insights surface:** Deal change indicators (score up/down), activity gaps (no logged activity in N days relative to deal stage), forecast risk flags (committed deals with low scores), and pipeline trend comparisons week-over-week.

### Einstein Email Generation and Email Recommendations

Einstein provides two related email AI capabilities for Sales reps:

1. **Einstein Email Recommendations** (older feature): Surfaces suggested email replies in the activity composer based on the email thread context. Requires Einstein for Sales license and the `Einstein Email Recommendations` permission set.
2. **Einstein Email Composition / Generative Email** (Spring '25+): Uses generative AI to draft full emails from a prompt or from opportunity context. The Spring '26 Generative AI guide lists Einstein Sales Emails as a generative feature and the Einstein for Sales add-on among the add-ons that carry generative AI usage, which contradicts the earlier statement that this is not included in Einstein for Sales. Confirm the entitlement on Company Information. Reps review and customize the emails before sending them.

### Einstein Relationship Insights

Einstein Relationship Insights mines email content and news sources to surface professional relationship connections between contacts, accounts, and leads — showing reps who at their company has a relationship with a target contact. Requires the `Einstein Relationship Insights` permission and the Einstein for Sales license. The feature requires that EAC is enabled and email sync is running; without email data, the relationship graph cannot be built.

---

## Common Patterns

### Mode 1: Enable and Configure from Scratch

**When to use:** Net-new org enabling Einstein Sales AI features for the first time.

**How it works:**

1. Verify license: Confirm Einstein for Sales or Einstein 1 Sales is provisioned (Setup > Company Information > Feature Licenses).
2. Enable Einstein: Setup > Einstein > Sales > toggle each feature on sequentially (Opportunity Scoring first, then EAC, then Pipeline Inspection, then email features).
3. Assign the feature permission sets to target users (UNVERIFIED 2026-10-03: the earlier names `Sales Cloud Einstein` and `Einstein for Sales User`). Grant View Scoring Model Factors to reviewers who need model explanations; it is off by default.
4. Configure EAC: Setup > Einstein > Einstein Activity Capture > Connect Accounts. Create a Configuration profile defining sync direction, object scope (Contacts, Leads, Opportunities), and exclusion domains. Assign the profile to users.
5. Add the score field to layouts: add `Opportunity Score` (`IqScore`) to the Opportunity page layout and list views, and finish the Pipeline Inspection setup steps.
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
| Org has fewer than 200 closed-won **or** fewer than 200 closed-lost opps | Do not enable Opportunity Scoring yet; focus on pipeline growth | Model will not train; feature activates but returns no scores, creating confusion |
| Reps need AI-drafted emails | Verify the generative AI entitlement on Company Information before enabling | The Generative AI guide lists Einstein for Sales among the add-ons with generative AI usage; the earlier "separate SKU" claim is contradicted |
| Pipeline Inspection shows no AI insights | Confirm Opportunity Scoring model is trained and returning scores first | Pipeline Inspection AI insights depend entirely on Opportunity Scoring data |
| EAC emails not relating to opportunities | Check that the configuration profile object scope includes Opportunities and that contact email addresses match | EAC relates by email address match only |
| Einstein Relationship Insights returns no connections | Confirm EAC email sync has been running for 30+ days with sufficient email volume | The relationship graph requires historical email data to mine; it is not instant |
| Sandbox testing of Opportunity Scoring | Test UI configuration and field layout only; do not expect scores in sandbox | Model trains on production data only |

---


## Recommended Workflow

1. **Map entitlements to features.** Read Feature Licenses and Permission Set Licenses on the Company Information page, and record which entitlement each requested feature needs.
2. **Check data readiness.** Run the two closed-opportunity counts in `references/metadata-examples.md`; defer scoring if either floor is unmet.
3. **Deploy settings in order.** `EAC.settings` first with private sharing defaults and the sensitive-email filter, then `OpportunityScore.settings`, then the Pipeline Inspection elements of `Opportunity.settings`; finish the Setup steps each feature still requires.
4. **Grant access.** Assign the feature permission sets and View Scoring Model Factors to the reviewers who need explanations; run `python3 scripts/check_einstein_copilot_for_sales.py --manifest-dir force-app/main/default` against the retrieved metadata.
5. **Verify with data.** Query `IqScore` on open opportunities after training, query active model factors, and confirm a new Activity Capture user defaults to Don't Share.

---

## Review Checklist

Run through these before marking Einstein Sales AI work complete:

- [ ] Einstein for Sales or Einstein 1 Sales license confirmed in Setup > Company Information > Feature Licenses
- [ ] Feature permission sets assigned to all target users (UNVERIFIED 2026-10-03: the earlier set names `Sales Cloud Einstein` and `Einstein for Sales User`)
- [ ] Opportunity Scoring model training status confirmed as complete (not "In Progress" or "Insufficient Data")
- [ ] EAC Connected Accounts show no authentication errors and at least one configuration profile is assigned to users
- [ ] `Opportunity Score` (`IqScore`) added to the Opportunity page layout and list views
- [ ] Pipeline Inspection component added to Forecast page and AI insights visible for at least one deal
- [ ] EAC exclusion domains configured to prevent personal/legal email from syncing
- [ ] If email composition is required: the generative AI entitlement confirmed on Company Information and the feature enabled
- [ ] Einstein Relationship Insights: EAC email sync confirmed running before expecting connection data

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Opportunity Scoring does not train in sandboxes** — Enabling Opportunity Scoring in a full sandbox activates the UI and fields but the model will never produce scores. The ML model trains exclusively on production org data. Do not use sandbox to validate that scoring is working end-to-end.

2. **EAC synced activities may not appear in standard Activity report types**: EAC email and calendar data is surfaced through the Activity Timeline component, and standard reports on `Activities`, `Tasks`, or `Events` may not include it (UNVERIFIED 2026-10-03: Help-only). Test the "Sync Email as Salesforce Activity" setting (`EACSettings.syncEmailToCoreActivity`, API 63.0 and later) before telling managers their dashboards cannot show captured email.

3. **Check the entitlement behind generative email**: the Spring '26 Generative AI guide lists the Einstein for Sales add-on among those carrying generative AI usage and lists Einstein Sales Emails as a generative feature, which contradicts the earlier claim that Einstein for Sales excludes generative email. Confirm on Company Information which entitlement your org holds.

4. **Pipeline Inspection needs its Setup configuration**: the setting alone is not enough ("additional configuration in Setup is required", Metadata API reference). UNVERIFIED (2026-10-03): that its AI insights stay empty until scoring has trained.

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
- `agent-topic-design` — Use when building custom Agentforce subagents for Sales processes beyond the built-in Einstein Sales AI features
- `agentforce-agent-creation` — Use when creating a full custom Agentforce agent for Sales use cases rather than enabling the pre-built Einstein Sales AI features
