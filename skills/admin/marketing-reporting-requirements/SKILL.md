---
name: marketing-reporting-requirements
description: "Use this skill when gathering and documenting Salesforce marketing reporting requirements: defining KPIs, choosing an attribution model (First Touch / Last Touch / Even Distribution / Multi-Touch), selecting the correct Campaign Influence configuration, and mapping business questions to Salesforce report types and dashboard features. NOT for building the dashboards themselves, configuring CRM Analytics datasets, writing SOQL for marketing reports, or setting up Marketing Cloud Engagement journeys."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "What attribution model should we use — first touch, last touch, or multi-touch — and what does that mean for our Salesforce setup?"
  - "How do we report on marketing-sourced pipeline versus marketing-influenced pipeline?"
  - "Stakeholders want to see campaign ROI and cost per lead — which Salesforce report types support that?"
  - "We need to understand what KPIs marketing can report on natively in Salesforce versus what requires MCAE B2B Marketing Analytics Plus"
  - "Our marketing team wants Campaign Intelligence dashboards — what settings need to be in place before we can use them?"
  - "How do we configure Campaign Influence to give revenue credit to the right campaigns?"
tags:
  - campaign-influence
  - attribution
  - marketing-reporting
  - campaign-performance-report
  - kpi
  - marketing-sourced-pipeline
  - marketing-influenced-pipeline
  - mcae
  - b2b-marketing-analytics
inputs:
  - "Business questions marketing wants answered (e.g., ROI, sourced vs influenced pipeline, email engagement)"
  - "Attribution model preference: First Touch, Last Touch, Even Distribution, or Multi-Touch"
  - "Salesforce edition and whether Campaign Influence and/or MCAE / B2B Marketing Analytics Plus is licensed"
  - "Whether Opportunities use Contact Roles consistently (required for standard Campaign Influence auto-association)"
  - "Stakeholder list and reporting frequency (operational daily reports vs executive monthly dashboards)"
  - "Current campaign hierarchy structure and campaign type taxonomy"
outputs:
  - "Attribution model decision record with business rationale and feature requirements"
  - "KPI definition register: metric name, Salesforce source field/object, calculation method, report type"
  - "Campaign Influence configuration checklist (standard vs Customizable Campaign Influence)"
  - "Report type selection matrix: which native Salesforce report types cover which KPIs"
  - "Gap analysis: KPIs that require MCAE B2B Marketing Analytics Plus or Multi-Touch Attribution App vs native reports"
  - "Requirements document ready for dashboard build handoff"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Reporting Requirements

This skill activates when a practitioner needs to gather, document, and validate Salesforce marketing reporting requirements — specifically the attribution model decision, KPI definitions, and the mapping of business questions to Salesforce features. It does not cover building dashboards, configuring CRM Analytics datasets, or writing SOQL queries.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Attribution model is a prerequisite, not an afterthought.** The choice of First Touch, Last Touch, Even Distribution, or Multi-Touch determines which Salesforce features must be licensed and configured. Choosing after dashboards are built forces a full rebuild. Lock this decision before any configuration or reporting design begins.
- **Campaign Influence must be enabled before attribution model selection can be meaningful.** Standard Campaign Influence (enabled in Setup > Campaign Influence) auto-associates campaigns to opportunities via Opportunity Contact Roles. If Contact Roles are not populated on Opportunities, no associations are created and attribution metrics will be blank. This is the most common cause of zero-value attribution reports.
- **Marketing-sourced pipeline and marketing-influenced pipeline are materially different metrics.** They require different report types and different Campaign Influence settings. Conflating them in requirements produces misleading executive dashboards and incorrect ROI calculations.
- **License constraints drive feature availability.** Standard Campaign Influence is available in Salesforce Professional and above. Customizable Campaign Influence (CCI) requires Enterprise or above. MCAE B2B Marketing Analytics Plus and the Multi-Touch Attribution App are separately licensed add-ons.

---

## Core Concepts

### Attribution Models and What They Require

The attribution model determines how revenue credit is distributed across campaigns that touched a prospect before the opportunity was won. Each model maps to a different Salesforce feature:

- **First Touch (marketing-sourced pipeline):** Full revenue credit goes to the campaign with the earliest Campaign Member created date before opportunity creation. Available via standard Campaign Influence with the Primary Campaign Source field on Opportunity. No additional license required.
- **Last Touch:** Full credit goes to the campaign with the most recent touchpoint. Available via standard Campaign Influence with a custom model. Requires Customizable Campaign Influence.
- **Even Distribution:** Revenue credit is split equally across all associated campaigns. Requires Customizable Campaign Influence (Enterprise or above).
- **Multi-Touch (time-decay or position-based):** Credit is weighted by position or recency across all touchpoints. Requires either MCAE B2B Marketing Analytics Plus (Einstein Analytics-based, supports time-decay and U-shaped/position-based models) or the Multi-Touch Attribution App (separate AppExchange managed package).

Standard Campaign Influence uses automatic association: when an Opportunity is created, Salesforce looks back at all Campaign Members on Contacts linked to the Opportunity via Opportunity Contact Roles. Customizable Campaign Influence (CCI) adds explicit credit models with configurable time-decay windows and percentage allocation rules.

Source: Salesforce Help — Campaign Influence Overview (https://help.salesforce.com/s/articleView?id=sf.campaigns_influence_about.htm)

### Marketing-Sourced vs Marketing-Influenced Pipeline

These two metrics answer different business questions and require different configurations:

- **Marketing-sourced pipeline:** Counts only opportunities where marketing was the first touch — that is, the Primary Campaign Source field is populated on the Opportunity. This uses the standard Campaign Influence auto-association with a 30-day (configurable) lookback window. It answers "how much pipeline did marketing generate?"
- **Marketing-influenced pipeline:** Counts all opportunities where any campaign touched any contact on the opportunity at any point before or during the sales cycle. This requires Campaign Influence to be enabled and Contact Roles to be populated. It answers "how much pipeline did marketing touch?"

The sum of marketing-influenced pipeline will always be greater than or equal to marketing-sourced pipeline. Reporting both as the same metric in the same report produces numbers that are neither, and neither stakeholder group trusts the output.

The Campaign Performance Report (Leads, Contacts, Opportunities, Won Opportunities, Value Won) operates at the campaign level and is available natively. It does not split sourced vs influenced — that distinction requires Campaign Influence configuration.

Source: Salesforce Help — Campaign Performance Report (https://help.salesforce.com/s/articleView?id=sf.campaigns_reports_campaign_performance.htm)

### Key KPIs and Their Salesforce Source

Marketing reporting requirements must map each KPI to a specific Salesforce source. Common KPIs and their backing:

| KPI | Salesforce Source | Notes |
|---|---|---|
| Cost per Lead | Campaign Cost field / Campaign Member count | Requires campaign cost to be entered on Campaign record |
| Cost per Opportunity | Campaign Cost / Campaign Influence Opportunity count | Requires CCI or standard influence |
| Marketing-Sourced Pipeline % | Primary Campaign Source opportunities / Total open pipeline | Requires Contact Roles on Opportunities |
| Marketing-Influenced Pipeline % | Campaign Influence opportunities / Total open pipeline | Requires Campaign Influence enabled |
| Campaign ROI | (Value Won – Campaign Cost) / Campaign Cost | Available in Campaign Performance Report |
| Email Open Rate | Campaign Member status counts (Opened) | Native for MCAE-connected campaigns; requires status setup |
| Email Click Rate | Campaign Member status counts (Clicked) | Same requirement as open rate |
| Revenue Influenced | CampaignInfluence.Revenue on Opportunity | Requires CCI enabled and Contact Roles populated |

MCAE B2B Marketing Analytics Plus adds time-decay revenue influenced, engagement score trends, and multi-touch attribution dashboards powered by Einstein Analytics. These metrics are not available in native Salesforce reports.

Source: Salesforce Help — B2B Marketing Analytics (https://help.salesforce.com/s/articleView?id=sf.pardot_b2b_marketing_analytics.htm)

### Marketing Campaign Intelligence Dashboards (MC Next)

Marketing Campaign Intelligence Dashboards (available in Marketing Cloud Next / MC Growth) provide open rates, click rates, conversion rates, and revenue influenced metrics through a dedicated analytics interface. These are separate from standard Salesforce dashboards and require MC Next provisioning. Key distinction: these are read-only dashboards driven by MC Next's own data pipeline, not by the Salesforce Campaign Influence model.

If the org uses standard Salesforce Campaigns (not MC Next), the equivalent intelligence must be assembled from Campaign Performance Reports, Campaign Member status-based reports, and CCI-backed Opportunity reports.

---

## Common Patterns

### Pattern: Attribution Model Decision Workshop

**When to use:** At the start of any marketing reporting project before any dashboard or report is built.

**How it works:**
1. Document the business question: "Does leadership want to hold marketing accountable for sourced pipeline, influenced pipeline, or full multi-touch ROI?"
2. Map each answer to the required Salesforce feature using the attribution model table above.
3. Check license availability (CCI requires Enterprise; B2B Marketing Analytics Plus is a separate SKU).
4. Check whether Opportunity Contact Roles are consistently populated — if not, standard Campaign Influence will return zero values.
5. Record the decision with the business rationale, required feature, and any prerequisite configuration work (enabling CCI, populating Contact Roles, etc.).

**Why not skip this:** Choosing the attribution model after dashboards are built is the single most common and costly mistake in marketing reporting projects. Changing from First Touch to Even Distribution after go-live requires reconfiguring Campaign Influence models, rebuilding reports, and retraining stakeholders.

### Pattern: KPI Definition Register Before Report Build

**When to use:** Before any report type is selected or dashboard component is specified.

**How it works:**
1. Collect all KPIs stakeholders mention (even informally).
2. For each KPI, document: definition, calculation method, Salesforce source object and field, required configuration, and whether it is available natively or requires an add-on.
3. Identify KPIs that cannot be delivered natively and present the gap analysis to stakeholders before committing to a dashboard scope.
4. Prioritize KPIs by business impact and implementation complexity.

**Why not the alternative:** Building reports first and then mapping KPIs to whatever the report produces results in KPIs that are technically available but do not match the business definition. For example, "Value Won" in the Campaign Performance Report is opportunity value, not influenced revenue — a critical distinction for attribution reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Leadership wants to know which campaigns generated pipeline (first touch only) | Standard Campaign Influence + Primary Campaign Source on Opportunity | No additional license needed; works with correct Contact Role population |
| Marketing wants to claim credit for any touched pipeline | Customizable Campaign Influence with Even Distribution model | CCI allows multiple campaigns to share credit; requires Enterprise license |
| Demand gen team wants time-decay attribution across the full funnel | MCAE B2B Marketing Analytics Plus | Provides position-based and time-decay models via Einstein Analytics |
| Org cannot license CCI or B2B MA Plus | Standard Campaign Influence for sourced; manual Campaign Performance Report for influenced | Clearly document the limitation in requirements |
| Email engagement KPIs (open rate, click rate) are required | Campaign Member status-based reports with MCAE campaign connector | Requires consistent Campaign Member status values (Sent, Opened, Clicked) |
| Multi-product or multi-channel attribution is required | Multi-Touch Attribution App (AppExchange) | Separate managed package; evaluate against B2B MA Plus for cost and complexity |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather stakeholder business questions.** Collect the specific questions marketing and leadership want answered. Do not start with KPI names — start with the decision each number will drive (e.g., "We need to justify marketing headcount increase" vs "We need to optimize campaign spend allocation").
2. **Confirm license and feature availability.** Check whether Campaign Influence, Customizable Campaign Influence, MCAE B2B Marketing Analytics Plus, or the Multi-Touch Attribution App are licensed. Check whether Opportunity Contact Roles are consistently populated in the org.
3. **Run the attribution model decision.** Present the four attribution model options (First Touch, Last Touch, Even Distribution, Multi-Touch) with their Salesforce feature requirements and license implications. Get an explicit decision documented with business rationale.
4. **Build the KPI definition register.** For each KPI: name, plain-English definition, calculation, Salesforce source object/field, required configuration (e.g., Campaign Influence must be enabled, Contact Roles must be populated), and whether it is native or requires an add-on.
5. **Identify report types and feature gaps.** Map each KPI to the appropriate Salesforce report type. Flag KPIs that require add-on licenses and document the gap.
6. **Produce the requirements document.** Consolidate attribution decision, KPI register, report type mapping, and gap analysis into a single document suitable for handoff to whoever will build the reports and dashboards.
7. **Validate prerequisites are met before handoff.** Confirm Campaign Influence is enabled (if required), Contact Roles are populated, Campaign Member statuses are configured, and any required packages are installed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Attribution model is explicitly chosen (First Touch / Last Touch / Even Distribution / Multi-Touch) and documented with business rationale
- [ ] Required Salesforce features for the chosen attribution model are confirmed as licensed and enabled
- [ ] Opportunity Contact Roles population is confirmed (if using any Campaign Influence model)
- [ ] Marketing-sourced pipeline and marketing-influenced pipeline are defined separately with distinct report type mappings
- [ ] Every KPI in the register has a named Salesforce source field/object
- [ ] KPIs requiring add-on licenses (CCI, B2B MA Plus, Multi-Touch App) are flagged with a gap note
- [ ] Campaign Member statuses are confirmed as configured for email engagement KPIs (Sent, Opened, Clicked, Unsubscribed)
- [ ] Requirements document is validated with a marketing stakeholder before dashboard build begins

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Campaign Influence requires Contact Roles, not just campaign membership.** Campaign Influence auto-association works by finding Campaign Members on Contacts linked to the Opportunity via Opportunity Contact Roles. If Opportunities do not have Contact Roles populated, Campaign Influence returns zero influenced opportunities even if Contacts are Campaign Members. This is the most common reason attribution dashboards show blank or zero values after setup.
2. **The 30-day Campaign Influence lookback window is often too short.** The default Campaign Influence lookback window is 30 days before opportunity creation. B2B sales cycles often span 90–180 days, meaning early-funnel campaigns are excluded from influence calculations. The lookback window is configurable in Setup > Campaign Influence Settings, but changing it after initial data is collected does not backfill historical associations.
3. **Primary Campaign Source and Campaign Influence are separate, independent mechanisms.** The Primary Campaign Source field on Opportunity is populated automatically from the most recent Campaign Membership on a Contact when an Opportunity is created. Campaign Influence associations are calculated separately using the lookback window. These two mechanisms can contradict each other — Primary Campaign Source may point to a different campaign than what Campaign Influence credits as primary.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Attribution model decision record | Chosen model, business rationale, required Salesforce feature, prerequisites, and sign-off |
| KPI definition register | Table of KPIs with definition, calculation, Salesforce source, and native/add-on flag |
| Report type selection matrix | Maps each KPI to its Salesforce report type and required configuration |
| Gap analysis | KPIs not deliverable natively with license/feature requirements and estimated effort |
| Marketing reporting requirements document | Consolidated handoff-ready document for dashboard build phase |

---

## Related Skills

- mcae-pardot-setup — Configure MCAE connector and Campaign Member statuses required for email engagement KPIs
- einstein-analytics-basics — Understand CRM Analytics licensing and dataset concepts before committing to B2B Marketing Analytics Plus
- pipeline-review-design — Complement marketing-sourced pipeline reporting with sales pipeline inspection design
