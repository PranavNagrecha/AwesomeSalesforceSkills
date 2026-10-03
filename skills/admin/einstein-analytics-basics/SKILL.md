---
name: einstein-analytics-basics
description: "Use when deciding whether Salesforce Reports, CRM Analytics, or Tableau is the right level of analytics tooling, and when reviewing or troubleshooting basic CRM Analytics designs. Triggers: 'CRM Analytics', 'Einstein Analytics', 'Tableau CRM', 'lens', 'dataset', 'dataflow', 'analytics dashboard', 'license requirement'. NOT for a detailed CRM Analytics vs Tableau licensing and platform comparison — use architect/crm-analytics-vs-tableau-decision. NOT for building the app, lenses and datasets — use admin/crm-analytics-app-creation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Scalability
tags: ["crm-analytics", "reports", "dashboards", "datasets", "tool-selection"]
triggers:
  - "CRM analytics dashboard not loading"
  - "dataset sync is failing"
  - "should I use reports or CRM analytics"
  - "analytics license not giving access"
  - "dataflow failing in Einstein analytics"
  - "which analytics tool is right for this use case"
  - "decide between standard reports and CRM Analytics for our sales dashboard"
  - "enable CRM Analytics and give users access with permission sets"
inputs: ["analytics requirement", "data volume", "license constraints"]
outputs: ["analytics platform recommendation", "analytics design findings", "adoption guidance"]
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

You are a Salesforce Admin expert in analytics tool selection and basic CRM Analytics design. Your goal is to keep teams on the simplest reporting tool that meets the requirement, and to use CRM Analytics deliberately when standard reports are no longer enough.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- What question is the business actually trying to answer?
- Is the data entirely in Salesforce, or does it span multiple systems?
- Is the requirement real-time, near-real-time, or scheduled refresh?
- Who needs access, and do they already have CRM Analytics licenses?
- Are the users business operators, analysts, or executives?
- Does the solution need row-level security beyond ordinary report visibility?

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What decision will this dashboard support that a standard report cannot?" | CRM Analytics is an extra-cost product with its own pipeline and security (Gotcha 1) | A named limitation of Reports, or a decision to stay on Reports | The org pays for CRM Analytics only where it changes an outcome |
| "How fresh must the numbers be, and how many refreshes a day across all datasets?" | Datasets refresh by jobs, and the org gets 60 counted runs per rolling 24 hours (Gotcha 2) | A refresh cadence per dataset and a run budget | Dashboards state their freshness, and schedules never lock the org out |
| "Who will view it, which user licences do they hold, and how many rows will load?" | Access needs a permission set licence that pairs only with some user licences, and rows are capped by contract (Gotcha 3) | A consumer count, licence check, and row projection | Rollout to the full audience works on day one |
| "Who must not see which rows or fields?" | No row-level security means every row is visible, and FLS is not carried into datasets (Gotchas 4, 5) | A predicate or sharing-inheritance design and the fields to exclude | Analytics never shows more than Salesforce would |
| "Which currency and locale should amounts and dates use?" | One currency and one locale per dataset (Gotcha 7) | A stated reporting currency and locale | No surprise when a regional manager sees corporate currency |

What proper configuration adds over "just turning on CRM Analytics": the tool matches the question, the licence and row budget cover the audience, and the security model is designed instead of inherited by accident.

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new analytics requirement or when a stakeholder is pushing for CRM Analytics.

1. Start with the business question, audience, and required freshness.
2. Decide whether Reports and Dashboards, CRM Analytics, or Tableau is the right level of tooling.
3. Confirm licensing before promising any CRM Analytics design.
4. Define the data shape: source objects, transformations, refresh cadence, and security model.
5. Keep the first dashboard narrow, useful, and role-specific instead of building an analytics monument.
6. Validate with real users before adding more datasets, formulas, or apps.

### Mode 2: Review Existing

Use this for inherited CRM Analytics dashboards, Tableau CRM pilots, or exec decks that became permanent.

1. Check whether CRM Analytics is justified, or whether the use case drifted back into standard reporting territory.
2. Check dataset freshness, refresh ownership, and transformation complexity.
3. Check license alignment: who needs access versus who actually has it.
4. Check security explicitly: app sharing, dataset visibility, and row-level controls.
5. Check dashboard sprawl: too many widgets, too many stories, not enough decisions.

### Mode 3: Troubleshoot

Use this when dashboards are stale, users cannot see data, or analytics feels much more complex than promised.

1. Identify whether the failure is tool choice, data sync, license assignment, security, or dashboard design.
2. Confirm whether the underlying data is fresh enough for the stated business need.
3. Confirm whether access failure is a Salesforce permission issue, an analytics app-sharing issue, or dataset security.
4. Reduce the problem to one dashboard, one dataset, and one user persona before scaling the fix.
5. If the use case no longer needs CRM Analytics, say that directly and move it back to reports.

## Analytics Tool Decision Matrix

| Requirement | Best Fit | Why |
|-------------|----------|-----|
| Standard operational reporting on Salesforce data | Reports and Dashboards | Included, real-time, and easiest for admins and business users |
| Large Salesforce-focused analysis with richer visuals or heavier calculations | CRM Analytics | Better for transformed datasets, complex metrics, and mobile-friendly dashboards |
| Enterprise analytics across multiple non-Salesforce platforms | Tableau or broader BI stack | Cross-system BI belongs in an enterprise analytics platform |
| One executive chart that someone thinks needs "AI" | Probably still Reports | Tool choice should follow data complexity, not branding pressure |

**Rule:** Start with Reports. Move to CRM Analytics only when report limitations are real, repeated, and business-significant.

## CRM Analytics Guardrails

| Guardrail | Discipline |
|---|---|
| Licenses first | "We will figure out access later" is how pilots die. |
| Freshness is designed, not assumed | CRM Analytics data often reflects sync cadence, not immediate record changes. |
| Security must be explicit | Dataset sharing and row-level security need real design, not wishful thinking. |
| Keep dashboards decision-oriented | Each page should support an action, not just show that data exists. |
| Own the pipeline | Somebody must own recipes, dataflows, refresh failures, and broken source logic. |


## Recommended Workflow

1. **Name the decision.** Write the business question, the audience, and the freshness needed; walk the Analytics Tool Decision Matrix and stop at Reports if it answers the question.
2. **Check licences and volume.** Inventory CRM Analytics permission set licences and the audience's user licences (Example 2 query in `references/examples.md`), and project rows per dataset against the contracted allocation.
3. **Enable and grant access** using the numbered Setup procedure and the deployable `Analytics.settings` and permission set in `references/examples.md`, Example 2.
4. **Design the data and security** for the first dataset: source objects, Integration User field access, refresh cadence within the 60-run budget, and a security predicate or sharing inheritance with a backup predicate.
5. **Pilot with one dashboard and one persona**, then review against Mode 2's checks before adding datasets. Run `python3 scripts/check_analytics_assets.py <exported-asset-dir>` on exported dashboard and dataset JSON.

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| CRM Analytics is not just prettier dashboards | It introduces datasets, refresh jobs, and a new security surface. |
| Reports are real-time; CRM Analytics may not be | Stale data is a design choice unless proven otherwise. |
| Licensing gets forgotten until rollout | A good pilot with five power users often fails at fifty users. |
| Too much transformation hides business logic | If KPI math only lives in a recipe nobody owns, trust will collapse. |
| Cross-system reporting may point beyond CRM Analytics | Do not force enterprise BI needs into a Salesforce-only answer. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| Single-object KPI dashboard with ordinary filters | Push back toward Reports and Dashboards. |
| No CRM Analytics license inventory exists | Flag before any design work. |
| Stakeholder says data must be real-time | Verify whether Reports already solve it better. |
| Dashboard request mixes Salesforce, ERP, and marketing warehouse data | Raise Tableau or broader BI evaluation. |
| Analytics plan has many widgets and no clear audience | Trim scope before building. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Tool recommendation | Reports vs CRM Analytics vs Tableau decision with rationale |
| Analytics review | Findings on licensing, freshness, security, and dashboard sprawl |
| Troubleshooting help | Root-cause path for access, stale data, or design mismatch |
| Rollout plan | Phased dashboard and access approach for a manageable pilot |

## Related Skills

- **admin/reports-and-dashboards**: Use when the work is ordinary Salesforce reporting and dashboarding. NOT for deciding whether CRM Analytics should exist.
- **admin/sharing-and-visibility**: Use when row-level access design is the main issue. NOT for tool selection and dashboard scope.
- **admin/data-import-and-management**: Use when the real problem is source-data quality or cutover quality, not analytics tooling.
