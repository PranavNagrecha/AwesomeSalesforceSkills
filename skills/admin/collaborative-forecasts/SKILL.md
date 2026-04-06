---
name: collaborative-forecasts
description: "Use this skill when setting up, configuring, or troubleshooting Salesforce Collaborative Forecasts: forecast types, forecast categories, rollup methods, quota management, forecast hierarchy, manager adjustments, and pipeline inspection integration. Trigger keywords: forecast type, forecast category, cumulative rollup, individual rollup, quota, forecast adjustment, forecast hierarchy, opportunity splits forecasting, pipeline forecast. NOT for custom report-based forecasting. NOT for Classic Forecasts (Customizable Forecasting). NOT for Territory Management setup (use enterprise-territory-management skill)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I set up Collaborative Forecasting in Salesforce for my sales team"
  - "forecast categories are not mapping to the right stages in our pipeline"
  - "I need to configure multiple forecast types for different sales motions"
  - "manager adjustments are missing or not rolling up correctly in the forecast"
  - "switching to cumulative rollup deleted all my existing forecast adjustments"
  - "how do I load quotas for users and show forecast attainment percentage"
  - "my opportunity splits are not appearing in the overlay forecast view"
tags:
  - collaborative-forecasts
  - forecast-types
  - forecast-categories
  - quota-management
  - forecast-adjustments
  - cumulative-rollup
  - opportunity-splits
inputs:
  - org edition (Enterprise, Performance, or Unlimited — required for Collaborative Forecasts)
  - number of distinct forecast motions in use (by revenue, product, overlay, territory)
  - opportunity stage-to-forecast-category mapping requirements
  - rollup method preference (cumulative vs single-category)
  - whether quotas need to be loaded and displayed
  - hierarchy type (role-based vs territory-based)
outputs:
  - configured forecast types with source object and hierarchy settings
  - stage-to-forecast-category mapping documentation
  - rollup method recommendation with impact analysis
  - quota load guidance and attainment display configuration
  - manager adjustment configuration guidance
  - forecast user enablement checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Collaborative Forecasts

This skill activates when a practitioner needs to design, configure, audit, or troubleshoot Salesforce Collaborative Forecasts. It covers forecast type configuration, forecast category mapping, rollup method selection, manager and owner adjustments, quota management, forecast hierarchy, and pipeline inspection integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Collaborative Forecasts must be enabled in the org.** Navigate to Setup > Forecasts Settings and confirm the feature is enabled. The org must be Enterprise, Performance, or Unlimited edition. Essentials and Professional editions do not support Collaborative Forecasts.
- **Up to 4 active Forecast Types are allowed by default.** Additional types can be requested via a Salesforce Support case. Each type is completely independent with its own hierarchy, rollup settings, and adjustments.
- **Switching the rollup method (cumulative vs single-category) permanently deletes all existing adjustments for that Forecast Type.** This is irreversible. Plan rollup method selection before going live and before any adjustments exist.
- **Five fixed forecast categories exist:** Pipeline, Best Case, Commit, Most Likely (optional), Closed, and Omitted. Categories map to opportunity stages. Omitted opportunities are excluded from all forecast rollups. Manager Judgment (owner-only adjustments) is not available for split-based forecast types.

---

## Core Concepts

### Forecast Types

A Forecast Type defines what a forecast measures and how it is organized. Each Forecast Type has three independent configuration dimensions:

1. **Source object** — what data the forecast rolls up:
   - **Opportunity** — rolls up the Amount field (or a custom currency field) from opportunities
   - **Opportunity Product (Product Family)** — rolls up revenue by product family from opportunity line items
   - **Opportunity Splits** — rolls up split percentages credited to each rep from Opportunity Revenue Splits
   - **Product Splits** — rolls up product-level overlay splits from Opportunity Product Splits
   - **Line Item Schedule (Schedule Date)** — rolls up revenue by schedule date from opportunity product schedules

2. **Forecast hierarchy** — the organizational dimension:
   - **Role hierarchy** — the standard Salesforce role tree; most orgs use this
   - **Territory hierarchy** — uses the active Enterprise Territory Management model; requires ETM to be active

3. **Measurement field** — the currency field used for rollup (Amount, Expected Revenue, or a custom field).

Up to 4 active Forecast Types are permitted by default. Each type appears as a separate tab on the Forecasts page.

### Forecast Categories

Five standard forecast categories map opportunity stages to forecast buckets. The mapping is configured per org and applies globally to all Forecast Types.

| Category | Typical Stage Examples | Included in Rollups |
|---|---|---|
| Pipeline | Prospecting, Qualification, Needs Analysis | Yes (pipeline and below) |
| Best Case | Value Proposition, Id. Decision Makers | Yes |
| Commit | Perception Analysis, Proposal/Price Quote | Yes |
| Most Likely | (optional, configurable) | Yes |
| Closed | Closed Won | Yes |
| Omitted | Closed Lost, Disqualified | No — excluded from all rollups |

Each opportunity stage must map to exactly one forecast category. Stages mapped to Omitted do not appear in any forecast view. There is no limit on how many stages map to each category.

**Manager Judgment:** An additional adjustment layer that managers can apply on top of subordinate-submitted forecasts. Not available for split-based forecast types (Opportunity Splits, Product Splits).

### Rollup Methods

The rollup method controls which forecast category values are shown in each column on the forecast page:

- **Single-Category Rollup (Individual):** Each column shows only the opportunities in that exact forecast category. The Commit column includes only Commit-stage opportunities; it does not include Closed deals.
- **Cumulative Rollup:** Each column accumulates the current category plus all higher-probability categories. For example, the Commit column includes Commit + Closed deals. The Best Case column includes Best Case + Commit + Closed deals.

Cumulative rollup gives managers an accurate picture of expected revenue (committed pipeline plus won deals). Single-category rollup is useful when reps need to see distinct stage breakdowns.

**Critical constraint:** Switching the rollup method deletes all existing adjustments for that Forecast Type with no recovery path. Configure rollup method before going live.

### Quotas

Quotas are per-user, per-period revenue targets loaded against a specific Forecast Type. Quotas enable the "% of Quota" attainment column on the forecast page.

Quotas are loaded via:
- **Data Loader / API** against the `ForecastingQuota` object (ForecastingTypeId must be referenced)
- **Import wizard** in Setup > Forecasts Settings > Manage Quotas

Key quota behaviors:
- Quotas are period-specific (monthly or quarterly depending on forecast period type).
- Each `ForecastingQuota` record references a user, a period (start date), and a quota amount.
- When quotas are loaded, the forecast page shows Amount / Quota (% attainment) for each user.
- The `StartDate` must exactly match the forecast period boundary — off-by-one-day dates cause quotas to be created but not associated with any period.

### Forecast Adjustments

Two types of adjustments exist on the forecast:

1. **Owner Adjustments (Manager Judgment on subordinate's forecast):** A manager can increase or decrease the forecast value for any subordinate user. The adjustment is stored independently of the underlying opportunity amounts.
2. **Revenue Adjustments (My Forecast adjustments):** A rep can adjust their own forecast total within a category. Enabled via the "Enable Forecast Adjustments" toggle in Forecasts Settings.

Both adjustment types are wiped when the rollup method is changed.

---

## Mode 1 — Configure Collaborative Forecasting From Scratch

Use this mode when enabling and setting up Collaborative Forecasts for the first time or adding a new Forecast Type.

**Step 1 — Enable Collaborative Forecasts.** Navigate to Setup > Forecasts Settings. Enable Collaborative Forecasts for the org. Select the default forecast currency (single currency org) or confirm multi-currency settings if applicable.

**Step 2 — Configure Forecast Categories.** In Setup > Forecasts Settings, review the stage-to-category mapping. Map every opportunity stage to a forecast category. Confirm which stages are Omitted (Closed Lost, disqualified stages, etc.). Omitted opportunities are excluded from all rollups.

**Step 3 — Create Forecast Types.** For each distinct sales motion (e.g., AE Revenue by Role, SE Overlay Splits, Product Family Revenue), create a Forecast Type with:
- Source object (Opportunity, Opportunity Product, Opportunity Splits, etc.)
- Measurement field (Amount, Expected Revenue, or custom currency field)
- Hierarchy type (role vs territory)
- Period type (monthly vs quarterly)
- Rollup method (cumulative vs single-category) — decide before enabling; cannot be changed without losing adjustments

**Step 4 — Add Forecast Type to the Forecasts Tab.** After creation, the type must be added to the visible columns on the forecasts page. Enable it in Forecasts Settings.

**Step 5 — Enable Forecast Users.** Go to each user's detail page (or bulk-configure via API) and set `ForecastEnabled = true`. Users must be enabled as forecast users to appear in the forecast hierarchy. Without this flag, a user is invisible in the forecast rollup even if they have the correct role.

**Step 6 — Load Quotas (if needed).** Use Data Loader or the quota import wizard to upload `ForecastingQuota` records for each user, period, and forecast type. Verify attainment column appears on the forecast page after load.

**Step 7 — Validate.** Navigate to the Forecasts tab as a manager role. Confirm subordinate users appear in the hierarchy. Confirm stage mapping produces expected rollup totals. Check that cumulative/single-category behavior matches expectation.

---

## Mode 2 — Audit an Existing Forecast Configuration

Use this mode when reviewing an existing setup for correctness, investigating missing data, or preparing for a change.

**Check active Forecast Type count.** Navigate to Setup > Forecasts Settings. Confirm the number of active types is 4 or fewer (default limit). Flag if the org is approaching the limit.

**Review stage-to-category mapping.** Confirm all active opportunity stages are mapped. Flag any stages mapped to Omitted that should be in the pipeline. Unintentionally-Omitted stages will silently exclude revenue from all forecasts.

**Check rollup method per Forecast Type.** Document the rollup method (cumulative vs single-category) for each type before making any changes. Verify method matches stakeholder reporting expectations.

**Audit forecast user enablement.** Query `SELECT Id, Name FROM User WHERE ForecastEnabled = true AND IsActive = true`. Compare against expected forecast users.

**Check quota coverage.** Query `ForecastingQuota` for coverage across expected users and periods. Flag missing quotas for active forecast users.

| Check | Navigation / SOQL | Flag If |
|---|---|---|
| Active Forecast Type count | Setup > Forecasts Settings | More than 4 types active |
| Unmapped stages | Setup > Forecasts Settings > Stage Mapping | Any active stage has no category |
| Unenabled forecast users | `SELECT Id, Name FROM User WHERE ForecastEnabled = false AND IsActive = true` | Sales managers missing |
| Missing quotas | `SELECT COUNT() FROM ForecastingQuota WHERE ForecastingType.DeveloperName = '<type>'` | Zero records for active periods |

---

## Mode 3 — Troubleshoot Forecast Data Issues

Use this mode when forecast rollups show unexpected amounts, users are missing from the hierarchy, or adjustments behave unexpectedly.

**Users missing from forecast hierarchy:**
- Confirm `ForecastEnabled = true` on the user record.
- Confirm the user has a role assigned and the role is in the forecast hierarchy.
- For territory-based forecast types: confirm the user is a territory member in the active territory model.

**Opportunities not appearing in forecast:**
- Check the opportunity stage — stages mapped to Omitted are excluded by design.
- For split-based types: confirm splits are populated on the opportunity.
- For product-based types: confirm opportunity line items exist with expected product families.
- For schedule-based types: confirm revenue schedules exist with dates in the current forecast period.

**Adjustment missing after rollup method change:**
- Adjustments are permanently deleted when the rollup method is switched. There is no recovery. Rebuild adjustments if needed.

**Quota attainment not showing:**
- Confirm `ForecastingQuota` records exist for the user, period, and specific `ForecastingTypeId`.
- Confirm the quota period start date matches the forecast period boundary exactly.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Sales team covers one product and one hierarchy | Single Opportunity Forecast Type with role hierarchy | Simplest configuration; easiest for reps to understand |
| Multiple sales motions (AE direct + SE overlay) | Separate Forecast Types: Opportunity Splits for AE, Product Splits for SE overlay | Each motion needs independent rollup and hierarchy |
| Managers need to see total expected revenue (Commit + Closed) in one column | Use cumulative rollup | Cumulative Commit column = Commit + Closed; accurate expected-revenue view |
| Finance team needs stage-by-stage pipeline view | Use single-category rollup | Each column shows exactly one stage bucket; no accumulation |
| Switching rollup method on a live type | Export adjustments first; communicate to managers; schedule off-peak | Adjustment deletion is irreversible |
| Quotas for 500+ users | Use Data Loader against ForecastingQuota object; reference ForecastingTypeId | Import wizard has volume limitations |
| Territory-based forecasting alongside role-based | Add a second Forecast Type with territory hierarchy selected | Completely independent of the role-based type; both coexist within 4-type limit |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Confirm org edition and feature enablement — verify Collaborative Forecasts is on, confirm edition supports it, and identify how many active Forecast Types already exist.
2. Map requirements to Forecast Types — for each distinct sales motion, determine source object, hierarchy type, measurement field, period type, and rollup method before creating anything.
3. Configure stage-to-category mapping — review all opportunity stages and confirm each maps to the correct forecast category; treat Omitted carefully to avoid silent revenue exclusion.
4. Create Forecast Types and enable forecast users — create types in Forecasts Settings, then set `ForecastEnabled = true` for all expected forecast users.
5. Load quotas if required — upload ForecastingQuota records via Data Loader or import wizard and verify attainment column populates.
6. Validate the configuration — navigate the Forecasts tab as a manager, confirm hierarchy, rollup totals, and adjustment behavior; cross-check amounts against a pipeline report.
7. Document rollup method and adjustment policy — record the rollup method chosen for each type before going live to prevent accidental data loss from future changes.

---

## Review Checklist

Run through these before marking Collaborative Forecasts setup complete:

- [ ] Collaborative Forecasts is enabled in Setup > Forecasts Settings
- [ ] All active opportunity stages are mapped to a forecast category (no unmapped stages)
- [ ] Omitted stage mapping is intentional — no revenue-generating stages mapped to Omitted
- [ ] Rollup method (cumulative vs single-category) is documented and matches stakeholder requirements
- [ ] All active Forecast Types are within the 4-type default limit
- [ ] All expected forecast users have `ForecastEnabled = true` on their user record
- [ ] Each forecast user has the correct role in the role hierarchy (or territory membership for territory types)
- [ ] Quotas are loaded for the current period if attainment display is required
- [ ] Split-based types have Opportunity Splits enabled and splits populated on opportunities
- [ ] Forecast adjustments are intentionally configured (enabled/disabled) per stakeholder preference
- [ ] Manager adjustment availability communicated to managers (not available for split-based types)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Switching rollup method deletes all adjustments permanently** — When you change a Forecast Type from single-category to cumulative rollup (or vice versa), Salesforce deletes all existing manager adjustments and owner adjustments for that type with no warning and no recovery path. Always capture adjustment values via Data Loader before making the change if they need to be preserved.

2. **ForecastEnabled must be set per user — role alone is not enough** — A user with the correct role in the role hierarchy will be completely invisible in the forecast rollup unless their `ForecastEnabled` field is set to `true`. New users are not automatically enabled. Include `ForecastEnabled = true` in every user provisioning workflow.

3. **Manager Judgment is not available for split-based Forecast Types** — For Forecast Types sourced from Opportunity Splits or Product Splits, Manager Judgment is silently unavailable. Managers cannot adjust subordinate forecast totals on these types. Communicate this to sales managers before rollout.

4. **Omitted stages are silently excluded from every rollup** — Any opportunity stage mapped to Omitted is excluded from all forecast rollup totals, including Pipeline. A revenue-generating stage mistakenly mapped to Omitted causes revenue to disappear from forecasts with no error message. Audit stage mapping carefully and re-audit whenever stage picklists change.

5. **Quota period start dates must match forecast period boundaries exactly** — The `StartDate` field on `ForecastingQuota` must exactly match the first day of a forecast period. Off-by-one-day dates cause quota records to be created without error but not associated with any period, so attainment shows as 0% or blank.

6. **The 4-Forecast-Type limit applies to active types only** — Inactive Forecast Types do not count toward the limit. If an additional active type is needed beyond 4, a Salesforce Support case is required to raise the limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ForecastingType (metadata) | Defines each active Forecast Type; partially deployable via ForecastingSettings metadata |
| ForecastingSettings (metadata) | Umbrella metadata type covering rollup method, forecast period type, and enabled types |
| ForecastingQuota (data record) | Per-user, per-period quota amounts; loaded via Data Loader or import wizard |
| ForecastingAdjustment (data record) | Manager and owner adjustments stored per user, period, and forecast type |
| Stage-to-Category Mapping (setup config) | Maps each opportunity stage to Pipeline/Best Case/Commit/Closed/Omitted |

---

## Related Skills

- enterprise-territory-management — use when the org needs territory-based Forecast Types; ETM must be active before a territory hierarchy can be selected in a Forecast Type
- opportunity-management — covers opportunity stage design, splits configuration, and opportunity product/schedule setup that feeds into forecast types
- sharing-and-visibility — use for role hierarchy design; role hierarchy structure directly affects which users appear in a role-based forecast hierarchy
