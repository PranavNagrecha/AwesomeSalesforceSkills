---
name: revenue-intelligence-setup
description: "Revenue Intelligence setup: pipeline inspection, deal insights, forecast accuracy analytics, Einstein analytics for sales leaders. NOT for CRM Analytics platform admin (use analytics-studio-admin). NOT for forecasting category setup only (use forecasting-and-quotas)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
tags:
  - revenue-intelligence
  - pipeline-inspection
  - einstein
  - forecasting
  - sales-analytics
  - sales-cloud
  - deal-insights
triggers:
  - "how do i set up revenue intelligence in salesforce"
  - "pipeline inspection for sales leaders"
  - "einstein deal insights and forecast accuracy"
  - "opportunity changes waterfall dashboard"
  - "revenue intelligence dashboards configuration"
  - "deploy revenue intelligence to sales managers"
inputs:
  - Sales Cloud edition and Revenue Intelligence license
  - Forecasting setup (categories, hierarchy, custom fiscal)
  - Opportunity field usage (amount, close date, stage, amount at risk)
  - Sales management hierarchy and coaching cadence
outputs:
  - Revenue Intelligence app activation plan
  - Pipeline Inspection configuration (filters, kpis)
  - Dashboard deployment plan (leader, manager, rep views)
  - Adoption rollout and coaching-meeting integration
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Revenue Intelligence Setup

Activate when standing up Salesforce Revenue Intelligence (RI) for a sales organization: pipeline inspection for managers, deal-change waterfall for leaders, forecast accuracy analytics, and Einstein-powered deal insights. RI rides on top of Sales Cloud + CRM Analytics and depends on clean Opportunity discipline to work.

## Before Starting

- **Confirm Revenue Intelligence license.** Distinct from base Sales Cloud; the shipped app and its CRM Analytics assets only appear when enabled.
- **Audit Opportunity hygiene.** RI surfaces deal deltas and coaching signals; if Opportunities have stale close dates, zero amounts, or skipped stages, the intelligence is garbage in, garbage out.
- **Decide the forecasting model.** Collaborative Forecasts must be enabled, with revenue types and hierarchy confirmed — RI dashboards filter and segment by these.

## Core Concepts

### Pipeline Inspection

The headline UI for sales managers. Shows all team Opportunities with deal-change deltas: stage changes, amount changes, close-date slips, new deals, closed-won/lost. Driven by a nightly Opportunity History snapshot the RI package builds.

### Deal Insights

Einstein-generated insights per Opportunity — sentiment from emails, activity gaps, champion turnover warnings, similar-deal outcomes. Requires Einstein Activity Capture (EAC) for emails and Sales Engagement signals.

### Forecast Accuracy

RI dashboards compare forecasted revenue to actual closed revenue, broken down by manager, rep, product, segment. Requires historical forecast snapshots — if you just turned on Collaborative Forecasts, there is no history to analyze yet.

### Underlying data: Opportunity History

RI pivots on `OpportunityFieldHistory` and `OpportunityHistory`. Field History tracking on Amount, Close Date, Stage, Forecast Category is mandatory; without it the waterfall is empty.

## Common Patterns

### Pattern: Weekly forecast call with Pipeline Inspection

Manager opens Pipeline Inspection Monday morning, filters to "Deals Slipped This Week" + "Amount Changed Last 7 Days". Review list with each rep; coaching notes captured on the Opportunity.

### Pattern: Quarter-end deal review with waterfall

Sales leader opens the shipped dashboard showing starting pipeline → won → lost → slipped → added. Used for the quarterly business review conversation.

### Pattern: Forecast accuracy trend

Head of sales reviews forecast vs actual across the last four quarters per segment. Informs where coaching investment drives forecast quality.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Manager needs deal-change visibility | Pipeline Inspection | Shipped view, no rebuild |
| Leader quarterly review | Shipped RI dashboards | Don't hand-build |
| AI deal scoring | Einstein Opportunity Scoring | Native, no custom ML |
| Activity-based insights | Einstein Activity Capture | Feeds RI insights |
| Custom metric not shipped | CRM Analytics recipe extending RI dataset | Reuses existing dataset |

## Recommended Workflow

1. Enable Revenue Intelligence license; install the RI app from AppExchange if not auto-provisioned.
2. Turn on Collaborative Forecasts with the organization's forecast categories and hierarchy.
3. Enable Opportunity Field History tracking on Amount, Close Date, Stage, Forecast Category (minimum).
4. Deploy Einstein Activity Capture for emails/events to power deal insights.
5. Grant the Revenue Intelligence permission set group to managers and leaders; validate Pipeline Inspection loads.
6. Customize dashboards: change defaults on filters, drill-down, and saved views per leadership segment.
7. Plan rollout: 30-minute manager training, weekly coaching cadence tied to Pipeline Inspection filters.

## Review Checklist

- [ ] RI license enabled and app visible
- [ ] Collaborative Forecasts set up with correct hierarchy
- [ ] Opportunity Field History tracking on all pivot fields
- [ ] Einstein Activity Capture deployed to sales org
- [ ] Pipeline Inspection loads for a test manager with expected data
- [ ] Shipped dashboards render with no zero/empty sections
- [ ] Manager coaching cadence documented and trained

## Salesforce-Specific Gotchas

1. **Opportunity History tracking limits fields.** You can only track 20 fields per object; choose wisely — removing history later loses the pre-removal data.
2. **Einstein Activity Capture is sticky.** Once deployed with Exchange sync, migrating off is painful; pilot carefully with a small group first.
3. **RI dashboards are partitioned by forecast hierarchy.** If forecast hierarchy and role hierarchy diverge, managers may not see their own team's data.

## Output Artifacts

| Artifact | Description |
|---|---|
| RI activation runbook | License, field history, EAC, dashboards |
| Adoption plan | Training, cadence, coaching integration |
| Dashboard customization guide | Saved views per leader segment |
| Forecast accuracy baseline | First snapshot to measure improvement |

## Related Skills

- `admin/forecasting-and-quotas` — upstream setup requirement
- `admin/einstein-activity-capture-setup` — insight source
- `admin/analytics-dashboard-design` — custom extensions
