# Gotchas — Pipeline Review Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pipeline Inspection Toggle Absent from Setup Without Qualifying License

**What happens:** When an admin navigates to Setup and searches for "Pipeline Inspection," the section either does not appear or appears without an enable toggle. Granting Customize Application and all related Sales Cloud permissions does not resolve it.

**When it occurs:** Any org that does not have Revenue Intelligence or Sales Cloud Einstein provisioned. The absence is silent — Setup does not display an explanatory message. It is frequently misdiagnosed as a permission problem or a metadata visibility issue.

**How to avoid:** Before attempting Pipeline Inspection enablement, verify the license in Setup > Company Information > Active Salesforce Licenses. Look for "Revenue Intelligence" or "Sales Cloud Einstein" in the list. If neither is present, Pipeline Inspection cannot be enabled. Escalate to the Account Executive for license provisioning rather than spending time debugging permissions.

---

## Gotcha 2: Lookback Window Selection Is Not Persisted Per User

**What happens:** A sales manager sets the Pipeline Inspection lookback window to 14 days during a Monday review meeting. The next time they open Pipeline Inspection — even the same day — it has reverted to the system default (7 days). Managers who standardize their review on a specific window must re-select it every session.

**When it occurs:** Every time the Pipeline Inspection page is loaded. The window selector is a session-level UI control, not a persisted user preference. There is no admin setting to change the default window for individual users or roles as of Spring '25.

**How to avoid:** Document the standard lookback window in the team's pipeline review playbook and include it as the first step in the meeting agenda ("Set window to 14 days before reviewing"). There is no admin configuration workaround for per-user persistent window selection.

---

## Gotcha 3: Split-Based Forecast Type Changes Visible Deal Amounts in Inspection View

**What happens:** An admin associates an Opportunity Splits-based forecast type with Pipeline Inspection. Managers who previously saw full Opportunity Amounts in the inspection view now see split-attributed amounts. A $500,000 deal where the viewing manager's rep owns a 60% split shows as $300,000. Managers believe deal values have changed and escalate to the admin.

**When it occurs:** When a forecast type with Opportunity Splits as its source object is associated with Pipeline Inspection and selected as the active type in the inspection view. The amount displayed reflects the split percentage for the viewing user's subordinates, not the total Opportunity Amount.

**How to avoid:** When associating forecast types with Pipeline Inspection, explicitly communicate to managers what amount basis each type uses. If managers need to see total deal amounts alongside split attribution, associate both an Opportunity-based and a Split-based forecast type. Train managers to toggle between the types and understand what each shows.

---

## Gotcha 4: Omitted-Stage Deals Are Invisible in Pipeline Totals Without the Filter Toggle

**What happens:** A manager asks why a known large deal is not showing in the Pipeline Inspection totals. The deal exists, is active, and the rep is in the manager's forecast hierarchy. The admin verifies permissions are correct and the deal is visible in regular list views. The deal's Stage is mapped to `Omitted` in ForecastCategoryName.

**When it occurs:** Any time a deal is in a Stage whose ForecastCategoryName is `Omitted`. Pipeline Inspection excludes Omitted deals from all metric totals and column groupings by default. The deal is not displayed unless the "Show Omitted" filter toggle is enabled in the inspection view.

**How to avoid:** Audit Stage-to-ForecastCategoryName mappings before configuring Pipeline Inspection. Document which stages are Omitted and why (e.g., "Dead", "On Hold"). Train managers to use the "Show Omitted" toggle when they need to review parked deals. Do not remap legitimate Omitted stages to revenue categories just to surface them in totals — that corrupts forecast rollups.

---

## Gotcha 5: Users Outside the Forecast Hierarchy Cannot Access Pipeline Inspection Data

**What happens:** A sales director with "Modify All Data" and "View All Forecasts" permissions cannot see data for a specific team in Pipeline Inspection. The team's deals are visible in reports and list views but not in the inspection view.

**When it occurs:** Pipeline Inspection uses the Collaborative Forecasts hierarchy to determine visibility. "View All Forecasts" allows seeing all forecast summary data on the Forecasts page, but Pipeline Inspection additionally requires the user to be in the correct position in the hierarchy to see subordinate deal detail. "Modify All Data" does not grant Pipeline Inspection visibility beyond what the forecast hierarchy allows.

**How to avoid:** Confirm that all users who need Pipeline Inspection access are correctly placed in the active forecast hierarchy under Setup > Forecasts > Forecast Settings. Sales directors who need cross-team visibility should be placed at the top of the hierarchy or have an explicit hierarchy position covering the teams they need to review.
