---
name: collaborative-forecasts
description: "Set up, configure or troubleshoot Salesforce Collaborative Forecasts: forecast types, forecast categories, rollup methods, quota management, forecast hierarchy, manager adjustments, pipeline inspection integration. Trigger keywords: forecast type, forecast category, cumulative rollup, individual rollup, quota, forecast adjustment, forecast hierarchy, opportunity splits forecasting, pipeline forecast. NOT for configuring the opportunity stages, sales processes or split types themselves — use admin/opportunity-management. NOT for territory-based forecasting setup — use admin/enterprise-territory-management. NOT for Classic/Customizable Forecasting."
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
  - "deployed a new forecast type but it is still inactive in the org"
  - "quota records loaded fine but the percent of quota column is blank"
  - "ForecastCategoryName is null on my forecast report after enabling cumulative rollups"
  - "which forecastCategory value do I deploy on the opportunity stage picklist"
  - "a whole branch of the sales org vanished from the forecast after a re-org"
  - "deactivating a forecast type purged our quotas and adjustments"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Collaborative Forecasts

This skill activates when a practitioner needs to design, configure, audit, or troubleshoot Salesforce Collaborative Forecasts. It covers forecast type configuration, forecast category mapping, rollup method selection, manager and owner adjustments, quota management, forecast hierarchy, and pipeline inspection integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Collaborative Forecasts must be enabled in the org.** Navigate to Setup > Forecasts Settings and confirm the feature is enabled; in metadata this is `ForecastingSettings.enableForecasts` (Metadata API Developer Guide, `api_meta` grep -n "^ *ForecastingSettings *$" 2nd hit, line 117436; field table from 117469; the data-loss warning at 117488). The guide warns "Disabling Forecasts can result in data loss." UNVERIFIED (2026-09-05): the edition list "Enterprise, Performance, Unlimited only" is not stated in the Metadata API guide or the Object Reference — and the Object Reference contradicts the exclusion of Professional, listing the API 57.0+ custom-date forecast types as available "in Performance, Professional, Enterprise, and Unlimited Edition with the Sales Cloud" (`object_reference` ForecastingType.DateType, from line 148700). Confirm the edition in the org, not from this list.
- **The maximum number of forecast types is four.** Grounded: "The maximum number of forecast types is four" on `ForecastingSettings.forecastingTypeSettings` (`api_meta` line 117503). Each type is independent with its own source, hierarchy and adjustable categories. UNVERIFIED (2026-09-05): the "raise the limit through a Salesforce Support case" route is not in either guide.
- **Three grounded events purge forecast data — plan around all three.** Setting `active` to `false` on a forecast type "purges all forecasting data, adjustments, and quotas for the forecast type" (`api_meta` line 117607); omitting a previously enabled type from the XML deactivates it and "its quota and adjustment data are deleted from the org" (`api_meta` line 117602); and setting `enableAdjustments` or `enableOwnerAdjustments` to `false` "results in adjustment data being purged" (`api_meta` lines 117837 and 117852). See `references/gotchas.md` Gotcha 9.
- **Standard forecast categories:** Pipeline, Best Case, Commit, Omitted, and Closed — "You can add a Most Likely category and can customize forecast category names in single category rollups" (`object_reference` ForecastingOwnerAdjustment.ForecastCategoryName, line 147671). Omitted opportunities are excluded from all forecast rollups. UNVERIFIED (2026-09-05): "Manager Judgment is unavailable for split-based forecast types" is not stated in either guide; `ForecastingType.HasAdjustments` (`object_reference` line 148759) carries no split carve-out. Verify in the target org before telling managers.

---

## Questions to Ask Before Configuring

Ask these before creating a single forecast type. Every row here exists because a documented behaviour punishes the wrong answer later, and several of the answers cannot be changed afterwards without purging data.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Cumulative columns or individual category columns — and who signs off before anyone adjusts?" | The choice is the *set of four values* in `forecastedCategoryApiNames`; swapping sets flips Enable Cumulative Forecast Rollups org-wide, and cumulative Best Case silently includes Most Likely | The four `forecastedCategoryApiNames` / `displayedCategoryApiNames` values to deploy, and a named owner for a one-way decision |
| "How many forecast types must be live at once, and are any of them pre-Summer '21 types?" | Four is the hard maximum; legacy types "can be deactivated but not activated, created, or deleted" through `ForecastingType` | A type inventory that separates what you can author in metadata from what you must switch on in Setup |
| "Role-based or territory-based — and is a `Territory2Model` already Active?" | `roleType` is `R` or `Y`; a territory type also needs `territory2Model` and `territory2Field` | The `roleType` value per type, and whether ETM activation blocks the forecast task (see `admin/enterprise-territory-management`) |
| "Amount or quantity, and which field is the measure?" | `amount` and `quantity` are mutually exclusive on `ForecastingType`, and `measureField` on the source definition decides whether a custom currency field is legal | The exact `measureField` (`Opportunity.Amount`, `OpportunitySplit.SplitAmount`, a `Megawatts__c`-style custom field) |
| "Do quotas come from finance, and in what grain — per user, per product family, per territory?" | Decides `QuotaAmount` vs `QuotaQuantity`, and whether `ProductFamily` / `Territory2Id` / `ForecastingGroupItemId` belong in the load file | A quota CSV column list with `PeriodId` deliberately absent (it is read-only) |
| "Who owns the Opportunity stage picklist, and does the release pipeline deploy `StandardValueSet: OpportunityStage`?" | Stage→category mapping ships as `forecastCategory` on each standard value, whose enum says `Forecast` where the UI says Commit | A stage mapping owned by the same release that changes stages, instead of a Setup click someone forgets |
| "Which reports and integrations read `ForecastCategoryName`?" | Under cumulative rollups that field "can be null because the cumulative forecast amounts include opportunities from multiple forecast categories" | A list of consumers to re-point at `ForecastingItemCategory` before the switch |

What a proper configuration adds over just doing it: the four category API names, the measure field, the hierarchy type and the quota grain are all decided and deployable *before* the first type goes active, so the org never has to reach the settings that purge forecasting data, adjustments and quotas to fix a wrong guess.

---

## Core Concepts

### Forecast Types

A Forecast Type defines what a forecast measures and how it is organized. Each Forecast Type has three independent configuration dimensions:

1. **Source object** — what data the forecast rolls up:

| Source object | What it rolls up |
|---|---|
| Opportunity | The Amount field (or a custom currency field) from opportunities |
| Opportunity Product (Product Family) | Revenue by product family from opportunity line items |
| Opportunity Splits | Split percentages credited to each rep from Opportunity Revenue Splits |
| Product Splits | Product-level overlay splits from Opportunity Product Splits |
| Line Item Schedule (Schedule Date) | Revenue by schedule date from opportunity product schedules |

2. **Forecast hierarchy** — the organizational dimension:

| Hierarchy | Notes |
|---|---|
| Role hierarchy | The standard Salesforce role tree; most orgs use this |
| Territory hierarchy | Uses the active Enterprise Territory Management model; requires ETM to be active |

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

There is no `rollupType` element. The rollup method is expressed by *which set of four values* you put in `forecastedCategoryApiNames` — "Changing from one set of four values to the other changes the organization setting for Enable Cumulative Forecast Rollups in Setup. If this field is omitted, the setting isn't changed" (`api_meta` line 117655).

| Rollup | `forecastedCategoryApiNames` set | What each column sums (`object_reference` ForecastingItem.ForecastingItemCategory, from line 147384) |
|---|---|---|
| Individual (single category) | `pipelineonly`, `bestcaseonly`, `commitonly`, `closedonly` | `PipelineOnly` = Pipeline only. `BestCaseOnly` = Best Case only (adjustable). `CommitOnly` = Commit only (adjustable). `ClosedOnly` = Closed only. |
| Cumulative | `openpipeline`, `bestcaseforecast`, `commitforecast`, `closedonly` | `OpenPipeline` = Pipeline + Best Case + Most Likely + Commit. `BestCaseForecast` = Best Case + Most Likely + Commit + Closed (adjustable). `CommitForecast` = Commit + Closed (adjustable). `ClosedOnly` = Closed only. |

Note what the guide adds that the usual summary drops: cumulative **Best Case** includes **Most Likely** as well as Commit and Closed, and cumulative **OpenPipeline** does *not* include Closed. `MostLikelyOnly` / `MostLikelyForecast` exist as a fifth category only where Most Likely has been added.

Cumulative rollup gives managers expected revenue (committed pipeline plus won deals). Single-category rollup is useful when reps need distinct stage breakdowns; forecast category names can be customised only in single-category rollups (`object_reference` line 147671).

**Critical constraint:** treat the rollup method as a one-way decision before go-live. The rollup switch's effect on existing adjustments is UNVERIFIED (2026-09-05) — neither guide documents it — but the three purge events listed under Before Starting are documented, so export `ForecastingAdjustment` and `ForecastingOwnerAdjustment` before touching forecast-type settings regardless.

### Quotas

Quotas are per-user, per-period revenue targets loaded against a specific Forecast Type. Quotas enable the "% of Quota" attainment column on the forecast page.

Quotas are enabled by `globalQuotasSettings/showQuotas` (`api_meta` line 117513; QuotasSettings subtype at 117948, `showQuotas` at 117958) and loaded via Data Loader / API against `ForecastingQuota`, or the Manage Quotas import in Setup.

`ForecastingQuota` field behaviour, from `object_reference` (grep -n "^ *ForecastingQuota *$" 5th hit, line 147887):

| Field | Properties | What it means for a load |
|---|---|---|
| `QuotaOwnerId` | Create, Update | The quota owner. "The Managed Quotas user permission is required for creating, updating, or deleting quotas. (Users can only edit their subordinates' or child territories' quotas, not their own.)" (line 147888) |
| `ForecastingTypeId` | Create | Required in practice — quotas are per forecast type; one user can hold several. |
| `StartDate` | Create, Update | "The start of the quota, expressed as month and year. **The date can include any day in a given month. Stored using the first date of the month.**" (line 148027) |
| `PeriodId` | Filter, Group, Sort — **no Create/Update** | "Period ID for the quota. **Read only.**" (line 147978) Never put it in a load file. |
| `QuotaAmount` / `QuotaQuantity` | Create, Update | Load exactly one, matching the type's measure. |
| `IsAmount` / `IsQuantity` | Defaulted on create — **no Create** | Derived, not settable: "If `true`, then the adjustment is made in a revenue amount. If `false`, then `IsQuantity` must be `true`." (lines 147946 and 147955) |
| `ProductFamily`, `Territory2Id`, `ForecastingGroupItemId` | Create | Only for types that have product families, a Territory2 model, or a forecast group. |

Retrieve the type ids first — `ForecastingType.DeveloperName` "is called `name` in the Metadata API and Forecasting Type in custom reports" (`object_reference` line 148741), so the metadata `name` and the queryable `DeveloperName` are the same string.

### Forecast Adjustments

Two types of adjustments exist on the forecast:

The two adjustment layers are two different objects, and the naming in the UI is easy to invert:

| Object | Who adjusts what | Toggle | Source |
|---|---|---|---|
| `ForecastingAdjustment` | "an individual forecast manager's adjustment for a **subordinate's or child territory's** forecast via a ForecastingItem" | `globalAdjustmentsSettings/enableAdjustments` | `object_reference` line 145555; `api_meta` line 117834 |
| `ForecastingOwnerAdjustment` | "an individual forecast user's adjustment of **their own** forecast, including territory forecasts they own" | `globalAdjustmentsSettings/enableOwnerAdjustments` | `object_reference` line 147630; `api_meta` line 117848 |

Both toggles are org-wide from API 53.0 on ("All forecast types must contain the same `enableAdjustments` value"), and both carry the same warning: "Disabling adjustments results in adjustment data being purged."

Which columns are adjustable is set by `managerAdjustableCategoryApiNames` and `ownerAdjustableCategoryApiNames` — each read-only, each appearing exactly twice, each restricted to `bestcaseforecast`/`commitforecast` (cumulative) or `bestcaseonly`/`commitonly` (individual), and "if both … fields are being used, they must contain the same two values" (`api_meta` lines 117703 and 117799). `ForecastingAdjustment.AdjustmentNote` is capped at 255 characters and "doesn't appear in reports" (`object_reference` line 145600).

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

**Step 4 — Activate the type.** In metadata this is the *second* deploy, not a separate screen: a type created through `ForecastingType` lands inactive and the same package must be deployed again to set `active`. Then confirm the four `displayedCategoryApiNames` values match the four `forecastedCategoryApiNames` values — "Always use the same 4 values for both" (`api_meta` line 117617).

**Step 5 — Enable Forecast Users and Assign Forecast Managers.** Go to each user's detail page (or bulk-configure via API) and set `ForecastEnabled = true` — labelled **Allow Forecasting** under General Information. Without this flag, a user is invisible in the forecast rollup even if they have the correct role; role assignment alone never sets it. The same enablement is also reachable from Setup > Forecasts Hierarchy > **Enable Users**, moving users between Available Users and Enabled Users — a second path to the same flag, not a substitute for it. Then, on the same Forecasts Hierarchy page, click **Assign Manager** / **Edit Manager** on every role that should roll up: if no forecast manager is assigned to a role, neither that role nor its subordinate roles are included in forecasts. Forecast users also need **View Roles and Role Hierarchy** to access role-based forecasts in Lightning Experience — assigned to all forecast users by default, so only verify it when a user cannot open the tab.

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
| Active Forecast Type count | `SELECT Id, DeveloperName, MasterLabel, IsActive, IsPlatformType FROM ForecastingType WHERE IsActive = true` | More than 4 active (`IsPlatformType = true` marks a legacy pre-Summer '21 type you cannot recreate) |
| Unmapped stages | Setup > Forecasts Settings > Stage Mapping | Any active stage has no category |
| Unenabled forecast users | `SELECT Id, Name, UserRoleId FROM User WHERE ForecastEnabled = false AND IsActive = true AND UserRoleId != null` | A user in a forecasting role is not enabled |
| Roles with no forecast manager | `SELECT Id, Name, ParentRoleId FROM UserRole WHERE ForecastUserId = null` | Any role that should roll up — the branch below it drops out too |
| Missing quotas | `SELECT ForecastingTypeId, COUNT(Id) FROM ForecastingQuota WHERE StartDate = THIS_FISCAL_QUARTER GROUP BY ForecastingTypeId` — resolve ids with `SELECT Id, DeveloperName, IsActive FROM ForecastingType` | Any active type with zero quota rows for the current period |

---

## Mode 3 — Troubleshoot Forecast Data Issues

Use this mode when forecast rollups show unexpected amounts, users are missing from the hierarchy, or adjustments behave unexpectedly.

**Users missing from forecast hierarchy:**
- Confirm `ForecastEnabled = true` (Allow Forecasting) on the user record.
- Confirm the user has a role assigned and the role is in the forecast hierarchy. For a role-based Forecast Type, a user with no role has no node in the hierarchy and cannot forecast at all.
- Confirm the role — and every role above it — has a forecast manager assigned. If no forecast manager is assigned to a role, neither that role nor its subordinate roles are included in forecasts.
- For territory-based forecast types: confirm the user is a territory member in the active territory model. Territory-based types roll up through the territory hierarchy, so a role-less user can still appear there.

**Forecasts tab blank or inaccessible in Lightning Experience:**
- Check the `View Roles and Role Hierarchy` permission — it is required to access role-based forecasts in Lightning Experience. It is assigned to all forecast users by default and is automatically enabled by View Setup and Configuration, View All Forecasts, Override Forecasts, or Delegated External Portal User, so admins rarely reproduce the failure.
- Confirm the Forecasts tab itself is in the app's navigation items or set to Default On.

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

1. **Answer the seven questions above and retrieve what already exists.** `sf project retrieve start --metadata "Settings:Forecasting" ForecastingType ForecastingSourceDefinition ForecastingTypeSource "StandardValueSet:OpportunityStage" --target-org <sandbox>`. The settings land in `settings/Forecasting.settings-meta.xml` — not `ForecastingSettings.settings`. Fill in `templates/collaborative-forecasts-template.md` as you go.
2. **Write the org-wide block first.** `enableForecasts`, all eight `forecastingCategoryMappings`, `globalAdjustmentsSettings`, `globalForecastRangeSettings`, `globalQuotasSettings` — copy the shapes from `references/metadata-examples.md` § "Two forecast types in one Forecasting.settings". Orgs using either rollup style "must include all eight occurrences of this subtype".
3. **Deploy the stage→category mapping in the same change as the stages.** `StandardValueSet: OpportunityStage`, one `forecastCategory` per `standardValue`, using the metadata enum (`Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`) — `Forecast` is the value the UI labels Commit. See `references/gotchas.md` Gotcha 10.
4. **Author the forecast types, then run the checker.** For legacy types, a `forecastingTypeSettings` block with the exact `name` from the guide's enum; for anything new, a `.forecastingType` plus `.forecastingSourceDefinition` plus `.forecastingTypeSource` triple. Then: `python3 skills/admin/collaborative-forecasts/scripts/check_collaborative_forecasts.py --manifest-dir force-app/main/default`, which enforces the category-enum, date-type, amount/quantity and quota-CSV rules the platform will otherwise fail on silently.
5. **Deploy twice.** `sf project deploy validate` then `sf project deploy start`, then run the same deploy again: a new forecast type "is created in the inactive state" on the first pass and only the second pass flips `active`. Order is `ForecastingSettings → ForecastingType → ForecastingSourceDefinition → ForecastingTypeSource`, applied automatically when all four are in one package.
6. **Enable the people, not just the metadata.** Set `User.ForecastEnabled = true` for every forecast user and `UserRole.ForecastUserId` for every role that must roll up; both are updateable via API, so this is a Data Loader step, not a click-through. Verify with the two SOQL queries in `references/metadata-examples.md` § Verification.
7. **Load quotas, then verify the numbers, not the record count.** Load `ForecastingQuota` with `QuotaOwnerId`, `ForecastingTypeId`, `StartDate`, and exactly one of `QuotaAmount` / `QuotaQuantity`; omit `PeriodId` and `IsAmount`/`IsQuantity`. Then query `ForecastingItem` as a manager and reconcile against a pipeline report before handing the tab to sales.

---

## Review Checklist

Run through these before marking Collaborative Forecasts setup complete:

- [ ] Collaborative Forecasts is enabled in Setup > Forecasts Settings
- [ ] All active opportunity stages are mapped to a forecast category (no unmapped stages)
- [ ] Omitted stage mapping is intentional — no revenue-generating stages mapped to Omitted
- [ ] Rollup method (cumulative vs single-category) is documented and matches stakeholder requirements
- [ ] All active Forecast Types are within the four-type maximum
- [ ] All expected forecast users have `ForecastEnabled = true` on their user record
- [ ] Each forecast user has the correct role in the role hierarchy (or territory membership for territory types)
- [ ] Every role that should roll up has a forecast manager assigned — an unassigned role node drops that role and all its subordinate roles from forecasts
- [ ] Quotas are loaded for the current period if attainment display is required, with `PeriodId`, `IsAmount` and `IsQuantity` absent from the load file
- [ ] The package was deployed twice, and `SELECT DeveloperName, IsActive, LastActivatedDate FROM ForecastingType` confirms every new type is actually active
- [ ] `Forecasting.settings` was retrieved from the target org before editing — the deployed file has no fewer `forecastingTypeSettings` blocks than the retrieved one
- [ ] Every opportunity stage in `StandardValueSet: OpportunityStage` carries a `forecastCategory`, using the metadata enum (`Forecast`, not `Commit`)
- [ ] Consumers of `ForecastCategoryName` were inventoried before any switch to cumulative rollups
- [ ] `python3 skills/admin/collaborative-forecasts/scripts/check_collaborative_forecasts.py --manifest-dir <dir>` exits 0
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

5. **A quota load fails on the columns you added, not the date you feared** — `ForecastingQuota.StartDate` accepts any day in the target month and is stored as the first of the month, so a date shift is *not* the usual cause of blank attainment. The real load-breakers are read-only and derived fields: `PeriodId` is read-only, and `IsAmount`/`IsQuantity` have no Create property. See `references/gotchas.md` Gotcha 5.

6. **A new forecast type deploys inactive — the first deploy never turns it on** — Types available only in API 52.0 and later are created in the inactive state; the guide's instruction is to deploy the zip file twice. Legacy pre-Summer '21 types are the inverse: they can be deactivated but not activated, created, or deleted through `ForecastingType`. See `references/gotchas.md` Gotcha 11.

7. **`ForecastCategoryName` goes null under cumulative rollups** — Cumulative forecast amounts span multiple forecast categories, so the field that identifies a single category has nothing to hold. Reports and integrations that group on it break at the moment the org switches. See `references/gotchas.md` Gotcha 12.

8. **The metadata enum for the Commit category is spelled `Forecast`** — On `StandardValueSet: OpportunityStage`, the deployable `forecastCategory` values are `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`. Deploying `Commit` fails; deploying nothing leaves the stage unmapped. See `references/gotchas.md` Gotcha 10.

---

## Output Artifacts

| Artifact | File / object | Notes |
|---|---|---|
| `ForecastingSettings` | `settings/Forecasting.settings-meta.xml`; package.xml member `Forecasting` under `<name>Settings</name>` | Org-wide: `enableForecasts`, eight `forecastingCategoryMappings`, global adjustment / range / quota settings, and one `forecastingTypeSettings` block per legacy type. API 28.0+, restructured at 30.0 and 53.0. |
| `ForecastingType` | `forecastingTypes/<name>.forecastingType-meta.xml` | API 52.0+. `active`, `amount`/`quantity`, `dateType`, `developerName`, `masterLabel`, `roleType` (`R`/`Y`), `territory2Model`, `opportunitySplitType`, `opptyLineItemSplitType`. |
| `ForecastingSourceDefinition` | `forecastingSourceDefinitions/<name>.forecastingSourceDefinition-meta.xml` | API 52.0+. `sourceObject`, `measureField`, `dateField`, `userField`, `categoryField`, `familyField`, `territory2Field`. |
| `ForecastingTypeSource` | `ForecastingTypeSources/<name>.forecastingTypeSource-meta.xml` | API 52.0+. Joins a source definition to a type; `parentSourceDefinition` + `relationField` for non-Opportunity sources. |
| `ForecastingFilter` / `ForecastingFilterCondition` | `forecastingFilters/` and `ForecastingFilterConditions/` | API 55.0+. Filter logic supports `AND` only; "a forecast type can contain up to three filter conditions". |
| `StandardValueSet: OpportunityStage` | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` | Carries `forecastCategory` per stage — the deployable stage-to-category mapping. |
| `ForecastingQuota` | data records | Per-user or per-territory, per-period quota. Loaded via Data Loader; requires the Managed Quotas permission. |
| `ForecastingAdjustment` / `ForecastingOwnerAdjustment` | data records | Manager and owner adjustments. Export both before any settings change that can purge them. |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are about to write or deploy XML — two-type `Forecasting.settings`, a custom `ForecastingType` + source definition + type source, the stage `StandardValueSet`, the quota CSV, package.xml, deploy order, and the verification queries |
| `references/gotchas.md` | Something works in Setup but not in metadata, or a deploy/load succeeded and the forecast is still wrong — 13 grounded platform behaviours |
| `references/examples.md` | You want a worked end-to-end scenario: two forecast types for a direct + overlay motion, and a diagnosis of revenue that vanished after a stage change |
| `references/well-architected.md` | You are choosing between forecast types, hierarchies, or rollup styles and need the tradeoff framing plus the source list |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated forecast configuration or guidance before it reaches an org |

---

## Related Skills

- `admin/enterprise-territory-management` — use when the org needs territory-based forecast types; `roleType` `Y` requires an active `Territory2Model`, and `Territory2.ForecastUserId` names the territory forecast manager
- `admin/opportunity-management` — owns opportunity stage design, forecast category vocabulary, splits configuration, and the product/schedule setup that feeds forecast source definitions
- `admin/sales-process-mapping` — owns which stages exist per sales process before you map any of them to a forecast category
- `admin/pipeline-review-design` — owns the review cadence and the reports the forecast tab is reconciled against; read it before deciding what the Commit column must mean to the business
- `admin/user-management` — owns `User.ForecastEnabled` and role assignment in provisioning; the forecast hierarchy is generated from the role hierarchy, so role design is decided there
- `admin/sharing-and-visibility` — use for role hierarchy design; role structure directly determines which users appear in a role-based forecast hierarchy
