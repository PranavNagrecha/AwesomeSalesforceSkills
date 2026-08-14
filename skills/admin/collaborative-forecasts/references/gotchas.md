# Gotchas — Collaborative Forecasts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Switching Rollup Method Permanently Deletes All Adjustments

**What happens:** When an admin changes the rollup method setting on a Forecast Type (from single-category to cumulative, or vice versa), Salesforce deletes every `ForecastingAdjustment` record associated with that Forecast Type. The deletion is immediate, silent, and permanent. No confirmation dialog is shown, no notification is sent to affected managers, and the records cannot be recovered through any standard mechanism.

**When it occurs:** Any time the rollup method setting on a Forecast Type is changed in Setup > Forecasts Settings, regardless of whether adjustments currently exist. If the type has zero adjustments, there is no visible impact — but the behavior is the same.

**How to avoid:** Decide on rollup method before the Forecast Type is used in production. If a change is truly required post-launch, export all `ForecastingAdjustment` records via Data Loader before making the change, communicate the data loss to affected managers, and plan the switch at the start of a new forecast period when prior-period adjustments are no longer operationally relevant.

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

## Gotcha 5: Quota StartDate Must Match Forecast Period Boundary Exactly

**What happens:** When loading `ForecastingQuota` records via Data Loader or API, the `StartDate` field must exactly match the first day of the target forecast period (e.g., `2025-01-01` for a January monthly period). If the date is off by even one day (e.g., `2025-01-02`), the quota record is created without error, but it is not associated with any forecast period. The attainment column on the forecast page shows 0% or blank even though the `ForecastingQuota` record exists and can be queried via SOQL.

**When it occurs:** Most commonly in bulk quota load processes where dates are generated programmatically or copied from a finance system that uses non-Salesforce-standard period boundaries.

**How to avoid:** Before loading quotas, query `ForecastingPeriod` to retrieve the exact `StartDate` values Salesforce uses for each period in the relevant Forecast Type. Use those values verbatim in the `ForecastingQuota` StartDate field. Do not derive period boundaries independently.

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
