# Collaborative Forecasts — Work Template

Use this template when configuring, auditing, or troubleshooting Collaborative Forecasts in a Salesforce org.

## Scope

**Skill:** `collaborative-forecasts`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Org edition:** (Enterprise / Performance / Unlimited)
- **Collaborative Forecasts enabled?** (yes / no / unknown — check Setup > Forecasts Settings)
- **Number of existing active Forecast Types:** (0–4+)
- **Sales motions in scope:** (direct revenue / overlay splits / product family / territory / other)
- **Hierarchy type in use:** (role hierarchy / territory hierarchy / both)
- **Quotas required?** (yes / no — affects ForecastingQuota load step)
- **Rollup method preference:** (cumulative / single-category / not yet decided)
- **Known constraints:** (e.g., existing adjustments that must be preserved, specific fiscal year calendar)

## Forecast Types to Configure

For each Forecast Type needed, document:

| Forecast Type Name | Source Object | Measurement Field | Hierarchy | Period Type | Rollup Method |
|---|---|---|---|---|---|
| (e.g. AE Direct Revenue) | Opportunity | Amount | Role | Monthly | Cumulative |
| (e.g. SE Overlay) | Opportunity Splits | Amount | Role | Monthly | Cumulative |

## Stage-to-Category Mapping Review

List all active opportunity stages and their intended category:

| Stage Name | Forecast Category | Intentional? |
|---|---|---|
| Prospecting | Pipeline | Yes |
| Qualification | Pipeline | Yes |
| (add all stages) | | |
| Closed Won | Closed | Yes |
| Closed Lost | Omitted | Yes |

Flag any stages that look revenue-generating but are mapped to Omitted.

## Forecast User Enablement

List users who must appear in the forecast hierarchy:

| User Name | Role | ForecastEnabled | Action Needed |
|---|---|---|---|
| (name) | (role) | true / false | Set ForecastEnabled = true if false |

## Quota Load Plan (if applicable)

- **Forecast Type(s) requiring quotas:**
- **Period type (monthly / quarterly):**
- **Period start dates to load:**
- **Load method:** Data Loader / Import Wizard / API
- **ForecastingTypeId to use:** (query `SELECT Id, Name FROM ForecastingType` to retrieve)

## Approach

Which mode from SKILL.md applies?

- [ ] Mode 1 — Configure from scratch
- [ ] Mode 2 — Audit existing configuration
- [ ] Mode 3 — Troubleshoot data issues

Which patterns are in use and why:

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Collaborative Forecasts is enabled in Setup > Forecasts Settings
- [ ] All active opportunity stages are mapped to a forecast category (no unmapped stages)
- [ ] Omitted stage mapping is intentional
- [ ] Rollup method is documented and matches stakeholder requirements
- [ ] All active Forecast Types are within the 4-type default limit
- [ ] All expected forecast users have ForecastEnabled = true
- [ ] Each forecast user has the correct role or territory membership
- [ ] Quotas are loaded for the current period (if attainment display is required)
- [ ] Split-based types have Opportunity Splits enabled and splits populated
- [ ] Forecast adjustments are intentionally configured per stakeholder preference
- [ ] Manager adjustment availability communicated to managers (not available for split-based types)

## Notes

Record any deviations from the standard pattern and why.

- Rollup method change risk communicated to: (name / date)
- Adjustment export completed before any rollup method change: (yes / N/A)
- Quota period boundary dates validated against ForecastingPeriod object: (yes / N/A)
