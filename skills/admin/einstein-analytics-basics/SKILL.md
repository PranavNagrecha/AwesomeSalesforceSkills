---
name: einstein-analytics-basics
description: "Use when deciding whether Salesforce Reports, CRM Analytics, or Tableau should be used for analytics, or when reviewing and troubleshooting basic CRM Analytics designs. Triggers: 'CRM Analytics', 'Einstein Analytics', 'Tableau CRM', 'lens', 'dataset', 'dataflow', 'analytics dashboard', 'license requirement'. NOT for standard report builder questions unless the decision is whether reports are still enough."
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
inputs: ["analytics requirement", "data volume", "license constraints"]
outputs: ["analytics platform recommendation", "analytics design findings", "adoption guidance"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
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

- **Licenses first**: "We will figure out access later" is how pilots die.
- **Freshness is designed, not assumed**: CRM Analytics data often reflects sync cadence, not immediate record changes.
- **Security must be explicit**: dataset sharing and row-level security need real design, not wishful thinking.
- **Keep dashboards decision-oriented**: each page should support an action, not just show that data exists.
- **Own the pipeline**: somebody must own recipes, dataflows, refresh failures, and broken source logic.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **CRM Analytics is not just prettier dashboards**: it introduces datasets, refresh jobs, and a new security surface.
- **Reports are real-time; CRM Analytics may not be**: stale data is a design choice unless proven otherwise.
- **Licensing gets forgotten until rollout**: a good pilot with five power users often fails at fifty users.
- **Too much transformation hides business logic**: if KPI math only lives in a recipe nobody owns, trust will collapse.
- **Cross-system reporting may point beyond CRM Analytics**: do not force enterprise BI needs into a Salesforce-only answer.

## Proactive Triggers

Surface these WITHOUT being asked:
- **Single-object KPI dashboard with ordinary filters** -> Push back toward Reports and Dashboards.
- **No CRM Analytics license inventory exists** -> Flag before any design work.
- **Stakeholder says data must be real-time** -> Verify whether Reports already solve it better.
- **Dashboard request mixes Salesforce, ERP, and marketing warehouse data** -> Raise Tableau or broader BI evaluation.
- **Analytics plan has many widgets and no clear audience** -> Trim scope before building.

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
