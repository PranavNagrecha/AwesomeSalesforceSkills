# Gotchas — Collaborative Forecasts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Switching Rollup Method Permanently Deletes All Adjustments

**What happens:** When an admin changes the rollup method setting on a Forecast Type (from single-category to cumulative, or vice versa), Salesforce deletes every `ForecastingAdjustment` record associated with that Forecast Type. The deletion is immediate, silent, and permanent. No confirmation dialog is shown, no notification is sent to affected managers, and the records cannot be recovered through any standard mechanism.

**When it occurs:** Any time the rollup method setting on a Forecast Type is changed in Setup > Forecasts Settings, regardless of whether adjustments currently exist. If the type has zero adjustments, there is no visible impact — but the behavior is the same.

**How to avoid:** Decide on rollup method before the Forecast Type is used in production. If a change is truly required post-launch, export all `ForecastingAdjustment` and `ForecastingOwnerAdjustment` records via Data Loader before making the change, communicate the data loss to affected managers, and plan the switch at the start of a new forecast period when prior-period adjustments are no longer operationally relevant.

UNVERIFIED (2026-09-05): the Metadata API Developer Guide and Object Reference do not state that a rollup-method switch deletes adjustments. What they *do* state, and what makes the precaution worth keeping regardless, is Gotcha 9 — three neighbouring settings on the same screen each purge adjustment data. In metadata terms the switch is a change to `forecastedCategoryApiNames`: "Changing from one set of four values to the other changes the organization setting for Enable Cumulative Forecast Rollups in Setup" (`api_meta` ForecastingTypeSettings, line 117655). Verify the deletion behaviour in a sandbox before promising a manager their adjustments survive.

---

## Gotcha 2: Newly Created Opportunity Stages Default to Omitted

**What happens:** When a new opportunity stage is added to the picklist, Salesforce maps it to the Omitted forecast category by default. Opportunities in that stage are immediately excluded from all forecast rollup totals — including the Pipeline column. This exclusion is silent: there is no warning in Setup, no error on the forecast page, and no indicator on the opportunity record itself.

**When it occurs:** Every time a new stage is added to the Opportunity Stage picklist without immediately updating the stage-to-category mapping in Forecasts Settings. Common in orgs that manage stage lists through change sets or metadata deployments, where the deployer handles the stage picklist but does not also update forecast mappings.

**How to avoid:** Immediately after creating or deploying any new opportunity stage, navigate to Setup > Forecasts Settings > Opportunity Stages in Forecasts and explicitly map the new stage to the correct forecast category. Include a stage mapping review as a required step in any release checklist that modifies opportunity stages.

---

## Gotcha 3: ForecastEnabled Must Be Set Per User — Role Alone Is Not Sufficient

**What happens:** A user assigned to the correct role in the role hierarchy is completely invisible in the forecast rollup unless their `ForecastEnabled` field is set to `true`. The user's opportunities exist and are included in totals, but the user row does not appear in the forecast hierarchy table, and managers cannot view or adjust forecasts for that user.

**When it occurs:** When new users are created, when users change roles, or when users are migrated from another system. New users are not automatically enabled as forecast users even if their role is already in the forecast hierarchy. User management workflows that only handle profile, role, and permission set assignments routinely miss this field.

**How to avoid:** Include `ForecastEnabled = true` in every user provisioning workflow and onboarding checklist for roles that should appear in the forecast. For bulk fixes, use Data Loader to update the User object's `ForecastEnabled` field. For users who should never appear in the forecast hierarchy (support staff, admins), leave `ForecastEnabled = false` intentionally.

---

## Gotcha 4: Manager Judgment Is Not Available for Split-Based Forecast Types

**What happens:** For Forecast Types sourced from Opportunity Splits or Product Splits, the Manager Judgment feature (where a manager can adjust a subordinate's forecast total) is silently unavailable. The adjustment UI element is not shown, and any configuration referencing manager adjustments for these types has no effect. Managers accustomed to adjusting role-based forecast types may not realize this limitation exists on split-based types.

**When it occurs:** Any time a split-based Forecast Type is configured and managers expect the same adjustment capabilities as Opportunity-based types. This is a platform limitation, not a configuration error.

**How to avoid:** Communicate explicitly to forecast managers during rollout that split-based Forecast Types do not support manager-level adjustments. If manager override capability is a hard requirement for split-based motions, consider whether a separate Opportunity-based type can provide the necessary override surface.

---

## Gotcha 5: A Quota Load Breaks on Read-Only Columns, Not on the Date

**What happens:** A `ForecastingQuota` load is rejected, or loads and then shows no attainment, because the CSV carries fields the platform derives rather than accepts. `PeriodId` is documented "Period ID for the quota. **Read only**" and has only Filter/Group/Nillable/Sort properties — no Create, no Update (`object_reference` ForecastingQuota, grep -n "^ *ForecastingQuota *$" 5th hit at line 147887; field at 147978). `IsAmount` and `IsQuantity` are "Defaulted on create" with no Create property (lines 147946 and 147955) and are derived from the forecast type's measure. Loading a `QuotaAmount` against a quantity type, or both `QuotaAmount` and `QuotaQuantity`, produces a row the forecast cannot use.

The date is *not* the fragile part, contrary to a widely repeated claim. The Object Reference is explicit: `StartDate` is "the start of the quota, expressed as month and year. **The date can include any day in a given month. Stored using the first date of the month**" (line 148027). A quota dated the 14th lands in that month's period.

**When it occurs:** When a quota template is built by exporting an existing `ForecastingQuota` record and re-importing it — the export carries `PeriodId`, `IsAmount` and `IsQuantity`, and nothing in the export marks them read-only. Also when finance supplies one file for an amount type and a quantity type together, so a single `QuotaAmount` column is mapped for both.

**How to avoid:** Load exactly these columns — `QuotaOwnerId`, `ForecastingTypeId`, `StartDate`, one of `QuotaAmount` / `QuotaQuantity`, and `CurrencyIsoCode` where multi-currency is on; add `ProductFamily`, `Territory2Id` or `ForecastingGroupItemId` only for types that have them. Resolve the type ids first with `SELECT Id, DeveloperName, IsAmount, IsQuantity, CanDisplayQuotas FROM ForecastingType` and split the file per type. If you do want the org's real period boundaries, query `Period` — `SELECT Id, StartDate, EndDate, Type FROM Period WHERE IsForecastPeriod = TRUE` (`object_reference` Period, line 216930; `IsForecastPeriod` at 216985) — not `ForecastingPeriod`, which is not an object in the Object Reference at all. The load user needs **Managed Quotas**, and "users can only edit their subordinates' or child territories' quotas, not their own" (line 147888).

---

## Gotcha 6: Territory-Based Forecast Types Require an Active ETM Territory Model

**What happens:** If you attempt to configure a Forecast Type with the territory hierarchy option and Enterprise Territory Management does not have an active Territory Model, the territory hierarchy option is not available in Forecasts Settings. Even if ETM is enabled at the feature level, a territory-based Forecast Type cannot be fully configured until a `Territory2Model` with `State = Active` exists.

**When it occurs:** When admins try to set up a territory forecast type during an ETM implementation before the territory model has been activated — common in phased rollout projects.

**How to avoid:** Activate the ETM territory model first, then configure the territory-based Forecast Type. In phased projects, sequence the ETM model activation before the forecast type creation task. See the enterprise-territory-management skill for guidance on model activation.

---

## Gotcha 7: A Role With No Forecast Manager Drops That Role and Every Role Beneath It

**What happens:** The forecast hierarchy is not an independently editable tree. Per the Pipeline Forecasting Implementation Guide, "The role-based forecasts hierarchy is generated from your user role hierarchy and specifies which users are forecast managers in the role-based forecasts hierarchy." The only per-node actions on the Forecasts Hierarchy page are **Enable Users** and **Assign Manager** / **Edit Manager** on a role — you cannot add, delete, or reorder nodes. Leave a role node without a forecast manager and Salesforce Help states the consequence directly: "If no forecast manager is assigned to a role in the forecast hierarchy, neither this role nor its subordinate roles are included in the forecasts." An entire branch of pipeline disappears with no error message. For a role-based Forecast Type, a user with no role has no node at all and cannot forecast (territory-based types roll up through the territory hierarchy instead, so they are unaffected by role removal).

**When it occurs:** After a re-org inserts a new management role between existing levels; when a forecast manager leaves and the role is left vacant; or when an admin removes a role from a heavy-owning sales ops user to keep skewed pipeline out of a role-based rollup — which also removes that user from role-based forecasting entirely.

**How to avoid:** Walk the forecast hierarchy after every role-hierarchy change and confirm each role that should roll up has an assigned forecast manager, including intermediate roles that hold no reps of their own. Never solve a rollup-distortion or sharing problem by stripping the role from a user who must appear in a role-based forecast; exclude their opportunities through stage mapping or a separate Forecast Type instead.

---

## Gotcha 8: The Forecasts Tab Needs "View Roles and Role Hierarchy", Not Just "Allow Forecasting"

**What happens:** A user has `ForecastEnabled = true` (labelled **Allow Forecasting** under General Information on the user record) and a role in the forecast hierarchy, but role-based forecasts still do not open in Lightning Experience. Salesforce Help: "Users need the View Roles and Role Hierarchy permission to access role-based forecasts in Lightning Experience." The permission is assigned to all forecast users by default, so it surfaces only where that default has been narrowed — which makes it hard to recognise when it happens.

**When it occurs:** On custom profiles or permission sets built by subtracting from a minimal baseline, and on external user types — the permission is enabled for all Standard user types (full CRM licence, user type S) on standard and custom profiles, but for Power Customer Success (type C) and Power Portal User (type P) it must be enabled deliberately. It is also automatically enabled by any of View Setup and Configuration, View All Forecasts, Override Forecasts, or Delegated External Portal User — so admins and forecast managers, who usually hold at least one of those, rarely reproduce the failure themselves.

**How to avoid:** When a forecast user reports an empty or inaccessible Forecasts tab, check View Roles and Role Hierarchy before re-checking Allow Forecasting or the hierarchy. The two are easy to conflate because both are commonly granted together, but they are independent: Allow Forecasting decides whether the user is *in* the forecast, View Roles and Role Hierarchy decides whether they can *open* a role-based forecast in Lightning Experience.

---

## Gotcha 9: Three Settings on the Forecasts Screen Purge Data, and the Guide Says So Only in Field Descriptions

**What happens:** Forecast configuration has no soft-delete. Three separate `ForecastingSettings` changes destroy quota and adjustment data, and each warning lives inside a field description rather than a confirmation dialog:

| Change | Documented consequence | `api_meta` line |
|---|---|---|
| `forecastingTypeSettings/active` set to `false` | "Setting the `active` field to `false` purges all forecasting data, adjustments, and quotas for the forecast type." | 117607 |
| A previously enabled `forecastingTypeSettings` block simply **omitted** from the XML | "if the forecast type was available in the release specified by the XML package version, that forecast type is deactivated and its quota and adjustment data are deleted" | 117602 |
| `enableAdjustments` or `enableOwnerAdjustments` set to `false` | "Disabling adjustments results in adjustment data being purged." | 117837, 117852 |

The middle row is the dangerous one, because it fires on an *absence*. A developer who hand-writes a trimmed `Forecasting.settings` containing only the type they are changing has, from the platform's point of view, asked for every other type to be deactivated and its history deleted.

**When it occurs:** Whenever `Forecasting.settings` is authored rather than retrieved — a hand-built settings file in a change set, a partial file copied from a blog post, or a merge that resolves a conflict by keeping one side's `forecastingTypeSettings` block. Also on the "we'll just turn adjustments off for a quarter" request, which reads as reversible and is not.

**How to avoid:** Never deploy a `Forecasting.settings` you did not first retrieve from the target org: `sf project retrieve start --metadata "Settings:Forecasting"`, edit, deploy. Treat every `active`, `enableAdjustments` and `enableOwnerAdjustments` flip as a data-migration step with an export in front of it (`ForecastingAdjustment`, `ForecastingOwnerAdjustment`, `ForecastingQuota`). In review, diff the count of `forecastingTypeSettings` blocks between the retrieved file and the file being deployed; a smaller number is a deletion, not a cleanup.

---

## Gotcha 10: The Deployable Forecast Category for Commit Is Spelled `Forecast`

**What happens:** Stage-to-category mapping is not a separate metadata type — it is the `forecastCategory` element on each opportunity stage value in `StandardValueSet: OpportunityStage`. Its enum is `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed` (`api_meta` CustomValue, line 47578, repeated for GlobalPicklistValue at 79289). `Forecast` is the value that the UI, the Object Reference and every business conversation call **Commit**. Deploying `<forecastCategory>Commit</forecastCategory>` fails; there is no `MostLikely` in this enum at all.

The same split runs through the query layer. `OpportunityStage.ForecastCategory` returns the no-space legacy words — `BestCase`, `Closed`, `Forecast`, `MostLikely`, `Omitted`, `Pipeline` — while `OpportunityStage.ForecastCategoryName` returns the spaced labels `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` (`object_reference` OpportunityStage, line 195434; the two field entries at 195466 and 195492). A validation rule, report filter or Apex comparison written against one vocabulary silently matches nothing when pointed at the other field.

**When it occurs:** On any release that adds or renames an opportunity stage through metadata rather than Setup — the stage deploys, the mapping does not, and the new stage arrives unmapped. And on every integration or Flow that hard-codes `'Commit'` while reading `ForecastCategory`, or `'Forecast'` while reading `ForecastCategoryName`.

**How to avoid:** Deploy the stage and its `forecastCategory` in the same `StandardValueSet` change, retrieving the org's full value set first — "When you deploy a StandardValueSet, this array must contain at least one picklist value. Otherwise, you receive an error" (`api_meta` line 130771), and a partial set is a destructive edit for the same reason as Gotcha 9. Grep the codebase for the literals `'Commit'` and `'Forecast'` near `ForecastCategory` before any stage change, and standardise on `ForecastCategoryName` for anything a human reads.

---

## Gotcha 11: A New Forecast Type Deploys Inactive; a Legacy One Cannot Be Activated at All

**What happens:** Two opposite rules apply depending on when the forecast type was introduced, and neither produces a deploy error:

- Types available only in API 52.0 and later: "If the forecast type doesn't exist, it's created in the inactive state. If the forecast type exists, the active flag is updated. **Deploy the zip file twice to create and activate the forecast type**" (`api_meta` ForecastingType Usage, line 75362; identical wording under ForecastingSourceDefinition at 75168).
- Legacy types available before API 52.0: they "can be deactivated but not activated, created, or deleted" through `ForecastingType` (`api_meta` line 75360). Their switch is `forecastingTypeSettings/active` inside `Forecasting.settings`, using one of the guide's fixed `name` strings.

So a single successful deploy of a brand-new type leaves an inactive type and a green pipeline, and an attempt to activate a legacy type through a `.forecastingType` file leaves it untouched.

Deploy order is fixed — "ForecastingSettings, ForecastingType, ForecastingSourceDefinition, and then ForecastingTypeSource. If all are specified in the package file, the sequence is followed automatically" (`api_meta` line 75364) — which is a reason to keep all four in one package rather than four sequential jobs.

**When it occurs:** On the first release that introduces a custom forecast type in a CI pipeline that deploys once and asserts on the deploy result. `ForecastingType.IsPlatformType` "indicates a legacy forecast type that wasn't available before Summer '21" (`object_reference` line 148811), and nothing in the deploy output says which rule applied.

**How to avoid:** Run the deploy twice for any release that creates forecast types, and gate the release on data rather than on the deploy status: `SELECT DeveloperName, IsActive, IsPlatformType, LastActivatedDate FROM ForecastingType`. Classify every type in the change as legacy or new before writing the package, using `IsPlatformType` from the target org.

---

## Gotcha 12: `ForecastCategoryName` Goes Null the Moment the Org Switches to Cumulative Rollups

**What happens:** `ForecastingItem.ForecastCategoryName` "represents the forecast category of the underlying opportunities rolling up to forecast amounts. **In organizations using cumulative forecast rollups, the `ForecastCategoryName` field can be null** because the cumulative forecast amounts include opportunities from multiple forecast categories" (`object_reference` ForecastingItem, line 147423). The replacement is `ForecastingItemCategory`, which "represents the type of rollup a forecast amount or adjustment is from" and carries `OpenPipeline` / `BestCaseForecast` / `MostLikelyForecast` / `CommitForecast` / `ClosedOnly` under cumulative rollups and `PipelineOnly` / `BestCaseOnly` / `MostLikelyOnly` / `CommitOnly` / `ClosedOnly` under individual ones (from line 147384).

The same guide text also corrects the usual mental model of what cumulative columns contain: `BestCaseForecast` is Best Case **+ Most Likely** + Commit + Closed, and `OpenPipeline` is Pipeline + Best Case + Most Likely + Commit and does **not** include Closed.

**When it occurs:** At the exact deploy that changes `forecastedCategoryApiNames` from the individual set to the cumulative set. Every report, dashboard filter, Apex query and integration that groups or filters `ForecastingItem` on `ForecastCategoryName` starts returning nulls or empty groups, with no error anywhere — the field still exists and is still queryable.

**How to avoid:** Before the switch, inventory the consumers: search reports and code for `ForecastCategoryName` used against `ForecastingItem`, `ForecastingFact`, `ForecastingAdjustment` or `ForecastingOwnerAdjustment`, and repoint them to `ForecastingItemCategory`. Then re-derive any "expected revenue" number from the corrected definitions above rather than from the pre-switch column meanings — the Best Case column changes composition even for organisations that were already summing categories by hand.

---

## Gotcha 13: The Forecast Objects Are Not Readable by an Ordinary Admin Query

**What happens:** `ForecastingItem`, `ForecastingFact`, `ForecastingQuota`, `ForecastingAdjustment`, `ForecastingOwnerAdjustment`, `ForecastingType`, `ForecastingShare` and `ForecastingUserPreference` all carry the same Special Access Rule: "As of Spring '20 and later, only standard users with the **View All Forecasts** or **Allow Forecasting** permission or delegated forecast manager status can access this object" (`object_reference` Special Access Rules blocks, e.g. ForecastingItem at line 147278, ForecastingOwnerAdjustment at 147641, ForecastingQuota at 147899, ForecastingType at 148681). `ForecastingSettings.forecastingCategoryMappings` carries the same restriction on the metadata side (`api_meta` line 117530).

Worse for verification, `ForecastingItem` narrows silently rather than erroring: "Other users can see the ForecastingItem object, but not its records… Users with the 'View All Forecasts' permission have access to all ForecastingItem fields. Users without the 'View All Forecasts' permission have access to all fields for their own subordinates and child territories" (line 147269).

**When it occurs:** When an admin, an integration user, or an automated health check queries forecast objects to verify a rollout. A System Administrator profile without Allow Forecasting or View All Forecasts gets zero rows for a correctly configured forecast, and a forecast manager gets only their own branch — both of which read as "the configuration is broken" rather than "you cannot see it."

**How to avoid:** Grant **View All Forecasts** to the identity doing the verification (an admin permission set, or the integration user), and record which identity a verification query ran as alongside its result. A zero-row result from a forecast object is not evidence of a configuration problem until the querying user's forecast permissions have been checked. Note the corollary for reporting integrations: a service account that scrapes `ForecastingItem` needs this permission permanently, not just during rollout.
