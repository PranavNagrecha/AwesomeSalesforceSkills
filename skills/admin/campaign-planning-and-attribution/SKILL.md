---
name: campaign-planning-and-attribution
description: "Use this skill when designing Campaign Hierarchy structures for program-level ROI tracking, configuring Customizable Campaign Influence (CCI) attribution models, or interpreting multi-touch attribution data from MCAE B2B Marketing Analytics. Trigger keywords: campaign ROI, attribution model, campaign hierarchy, first-touch, last-touch, multi-touch, CCI, campaign influence, revenue attribution, campaign member status. NOT for campaign record creation, campaign member import, email send execution, or MCAE connector provisioning (use mcae-pardot-setup instead)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Scalability
triggers:
  - "How do I roll up campaign revenue from child campaigns to a parent program in Salesforce?"
  - "We need to give multiple campaigns attribution credit on the same opportunity — how do we configure that?"
  - "What is the difference between standard Campaign Influence and Customizable Campaign Influence in Salesforce?"
  - "Campaign ROI is not calculating correctly on the parent campaign — child totals are missing"
  - "How do I set up time-decay or U-shaped attribution models for Salesforce campaigns?"
  - "We want first-touch and last-touch attribution reporting on opportunities — where do we start?"
  - "Campaign member status values are not mapping to funnel stages correctly — how should these be structured?"
tags:
  - campaigns
  - campaign-hierarchy
  - attribution
  - campaign-influence
  - multi-touch-attribution
  - MCAE
  - ROI
  - B2B-marketing-analytics
  - campaign-member-status
inputs:
  - "Campaign Hierarchy design intent (program structure, depth, program vs. tactic distinction)"
  - "Attribution model requirements (first-touch, last-touch, even, time-decay, position-based)"
  - "Whether MCAE (Pardot) B2B Marketing Analytics Plus is licensed"
  - "Whether Customizable Campaign Influence is already enabled in org Setup"
  - "Existing Campaign Member Status picklist values per campaign type"
outputs:
  - "Campaign Hierarchy design recommendation with level mapping"
  - "Customizable Campaign Influence configuration plan (model type, influence rules)"
  - "Campaign Member Status structure aligned to funnel stages"
  - "Decision guidance for native CCI vs. MCAE Multi-Touch Attribution App"
  - "Completed campaign-planning-and-attribution-template.md for handoff"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Campaign Planning And Attribution

This skill activates when a practitioner needs to design Campaign Hierarchy structures for program-level ROI aggregation, configure Customizable Campaign Influence (CCI) attribution models in Salesforce, or interpret multi-touch revenue attribution data from MCAE B2B Marketing Analytics. It covers architecture decisions and configuration — not execution of individual campaigns or MCAE connector provisioning.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether Customizable Campaign Influence is enabled: Setup > Campaign Influence > enable "Customizable Campaign Influence". This is org-level and cannot be reversed without data impact.
- Confirm whether MCAE B2B Marketing Analytics Plus is licensed — this is required for time-decay and position-based (U-shaped) attribution models.
- Determine the maximum hierarchy depth needed. Salesforce supports up to 5 levels. Deeper planning hierarchies require restructuring.
- The most common wrong assumption: practitioners believe "Campaign Influence" and "Customizable Campaign Influence" are the same feature. They are not. Standard Campaign Influence uses auto-association rules; CCI requires explicit model configuration and cannot coexist cleanly with the standard version.
- Campaign Hierarchy revenue rollups (Expected Revenue, Actual Cost, Num Leads, etc.) are updated on a schedule — they are NOT real-time. Do not treat parent campaign totals as live during active campaigns.

---

## Core Concepts

### Campaign Hierarchy and Revenue Rollup

Campaign Hierarchy allows up to 5 levels of parent-child Campaign records. A "Program" sits at or near the top; individual "Tactics" (webinars, emails, ads) sit at lower levels. When a child Campaign has Actual Cost, Expected Revenue, or member count populated, Salesforce automatically rolls these up to every ancestor via scheduled batch processing. Rollup fields on the parent Campaign include:

- `NumberOfLeads` / `NumberOfConvertedLeads`
- `NumberOfContacts` / `NumberOfResponses`
- `AmountAllOpportunities` / `AmountWonOpportunities`
- `ActualCost` (summed from children)

ROI is surfaced as a formula: `(AmountWonOpportunities - ActualCost) / ActualCost`. Because rollups are batch-computed, dashboards that read parent Campaign fields can lag behind actual child campaign activity.

### Customizable Campaign Influence (CCI)

CCI allows multiple campaigns to receive attribution credit on a single Opportunity via CampaignInfluence junction records. It must be explicitly enabled in Setup. Once enabled, you configure one or more Campaign Influence Models. Built-in model types:

- **First Touch** — 100% credit to the first campaign that touched the contact associated with the opportunity.
- **Last Touch** — 100% credit to the most recent campaign before opportunity close.
- **Even Distribution** — credit split equally across all influencing campaigns.
- **Custom** — you define a scoring algorithm via Apex or configuration rules.

Each CampaignInfluence record links one Campaign, one Opportunity, and optionally one Contact. The `Influence` field (percentage) sums to 100% across all records for a given model on a given Opportunity.

CCI requires: (1) Campaign Influence enabled, (2) at least one model configured, and (3) contact roles on the Opportunity to link back to campaign members. Without Contact Roles, CCI has nothing to associate.

### Campaign Member Status and Funnel Tracking

Each Campaign has a Member Status picklist that drives funnel stage tracking. Statuses are Campaign-type-specific and must be configured per Campaign Type in Setup. The `Responded` flag on a status value determines whether that member counts in the "Responded" rollup on the Campaign. Well-structured statuses map directly to marketing funnel stages: Sent → Opened → Clicked → Registered → Attended → Responded. MCAE writes Campaign Member records with these statuses when prospects engage with assets — if statuses are missing, MCAE silently drops engagement data.

### MCAE Multi-Touch Attribution App (B2B Marketing Analytics Plus)

For orgs with MCAE and B2B Marketing Analytics Plus, the Multi-Touch Attribution App extends CCI reporting with additional model types not available natively:

- **Time-Decay** — more credit to campaigns closer to the opportunity close date.
- **Position-Based (U-Shaped)** — first and last touches each receive 40%; middle touches split the remaining 20%.

These models surface in CRM Analytics dashboards and do not modify the underlying CampaignInfluence records — they are reporting-layer constructs only. Underlying data still flows through the CCI framework.

---

## Common Patterns

### Pattern: Program/Tactic Hierarchy with Rolled-Up ROI Dashboard

**When to use:** A marketing team runs multiple channels (email, webinar, paid) under a single program and needs a unified ROI view at the program level for executive reporting.

**How it works:**
1. Create a parent Campaign of Type "Program" at Level 1. Set Budgeted Cost and Expected Revenue here.
2. Create child Campaigns (Type = Email, Event, etc.) at Level 2 or below. Link them via the `ParentId` field.
3. Populate `ActualCost` on each child campaign as spend is confirmed.
4. Build a dashboard using parent Campaign rollup fields (`AmountWonOpportunities`, `ActualCost`) to display ROI.
5. Refresh cadence: rollups update within hours; avoid querying rollup fields in real-time triggers.

**Why not the alternative:** Without hierarchy, teams must manually aggregate per-channel costs into a spreadsheet. This breaks when campaigns are added mid-program and creates reconciliation debt.

### Pattern: CCI First-Touch + Last-Touch Dual-Model Configuration

**When to use:** Revenue operations needs to attribute pipeline credit to both the awareness channel (first touch) and the conversion channel (last touch) simultaneously — a common demand-gen requirement.

**How it works:**
1. Enable Customizable Campaign Influence in Setup.
2. Create Model 1: First Touch. Set the primary model flag if this is the default for reports.
3. Create Model 2: Last Touch.
4. Ensure all Opportunities have Contact Roles populated (either via automation or manual entry).
5. Run the influence calculation. CampaignInfluence records are created per model.
6. Build separate report types for each model using the CampaignInfluence object.

**Why not the alternative:** Standard Campaign Influence (non-customizable) only supports one model at a time and cannot produce side-by-side first-touch vs. last-touch comparison reports in native Salesforce.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need program-level ROI across multiple campaign tactics | Campaign Hierarchy (up to 5 levels) with rollup field dashboard | Native rollup fields aggregate cost and revenue automatically |
| Need multiple campaigns to share credit on one opportunity | Enable CCI; configure first-touch, last-touch, or even model | Only CCI supports multiple attribution records per opportunity per model |
| Need time-decay or U-shaped attribution models | MCAE B2B Marketing Analytics Plus — Multi-Touch Attribution App | These model types are not available in native CCI; require MCAE license |
| CCI and standard Campaign Influence are both partially configured | Disable standard Campaign Influence before configuring CCI | The two frameworks conflict; CCI supersedes standard influence |
| Opportunity pipeline is not appearing in Campaign Hierarchy rollups | Confirm Contact Roles exist on Opportunities | CCI and hierarchy revenue rollups require Contact Role association |
| Need real-time campaign spend reporting | Build reports on child Campaign `ActualCost` directly, not parent rollup | Parent rollup fields update on a batch schedule, not in real time |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org capabilities** — check whether CCI is enabled (Setup > Campaign Influence) and whether MCAE B2B Marketing Analytics Plus is licensed. Record which attribution models are in scope.
2. **Design Campaign Hierarchy** — map program/sub-program/tactic levels to Salesforce Campaign records (max 5 levels). Assign Campaign Types and set Budgeted Cost and Expected Revenue on parent records.
3. **Configure Campaign Member Statuses** — per Campaign Type, define statuses that map to funnel stages. Mark the appropriate statuses as `Responded = true`. Confirm MCAE required statuses (Sent, Opened, Clicked, Responded) are present if MCAE is in use.
4. **Configure CCI models** — in Setup, create the required attribution models (first-touch, last-touch, even, or custom). Designate a primary model. Confirm Contact Role population rules exist on Opportunities.
5. **Validate CampaignInfluence records** — after opportunity creation, query CampaignInfluence to confirm records are created per model. Check that `Revenue` and `Influence` fields are populated.
6. **Build reporting layer** — create Campaign Hierarchy reports using parent rollup fields for ROI. Create CampaignInfluence reports per model for attribution analysis. If MCAE Multi-Touch App is in scope, configure the CRM Analytics dashboard datasets.
7. **Document model choices and refresh cadence** — record which attribution models are active, why they were chosen, and the expected lag on hierarchy rollup fields. Share with the revenue operations team.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Campaign Hierarchy does not exceed 5 levels
- [ ] Budgeted Cost and Expected Revenue are set on parent Campaign records, not only on child records
- [ ] Customizable Campaign Influence is enabled in Setup before any CCI model is referenced
- [ ] At least one CCI model is fully configured if CCI is in scope
- [ ] Contact Roles are populated on Opportunities for CCI to produce influence records
- [ ] Campaign Member Status picklist values include `Responded = true` on at least one status per Campaign Type
- [ ] Rollup field refresh lag is documented and stakeholders understand it is not real-time

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hierarchy rollup fields are batch-computed, not real-time** — Fields like `AmountWonOpportunities` on a parent Campaign do not update the moment a child campaign's linked opportunity closes. They refresh via a scheduled Salesforce background job. During active campaigns this can cause dashboards to show stale totals for hours. Never build automation that depends on a parent Campaign rollup field reacting immediately to a child record change.

2. **CCI and standard Campaign Influence conflict — only one can be the authority** — If standard Campaign Influence (non-customizable) is active alongside CCI, double-counting and conflicting attribution records can appear. Disable standard Campaign Influence auto-association rules before relying on CCI models for reporting. The Setup UI allows both to coexist, but the resulting data is unreliable.

3. **CampaignInfluence records require Contact Roles on Opportunities** — CCI links campaigns to opportunities via contact membership. If an opportunity has no Contact Roles, no CampaignInfluence records are created — the attribution is silently skipped. This is the most common cause of "attribution model configured but no data appearing" issues.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Campaign Hierarchy design doc | Level mapping, Campaign Types, rollup field strategy |
| CCI model configuration plan | Model types, primary model designation, Contact Role requirements |
| Campaign Member Status table | Per-Campaign-Type status values with funnel stage and Responded flag mapping |
| Attribution reporting design | Report types and dashboard components for each active model |

---

## Related Skills

- `mcae-pardot-setup` — use for MCAE connector provisioning, BU configuration, and campaign connector setup that feeds attribution data into Salesforce
