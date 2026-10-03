---
name: crm-analytics-app-creation
description: "Use when creating or configuring a CRM Analytics (Einstein Analytics) app — including app containers, lenses, datasets, data source connections, app sharing, and the row-level security that gates whether users see any data. NOT for choosing Reports vs CRM Analytics vs Tableau — use admin/einstein-analytics-basics. NOT for security predicate syntax, sharing inheritance or Analytics license assignment — use admin/analytics-permission-and-sharing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "How do I create a new CRM Analytics app and set up my first dashboard?"
  - "Users can see the CRM Analytics app but cannot see any data — what is wrong?"
  - "How do I share a CRM Analytics app with a specific team or profile?"
  - "What is the difference between a lens and a dashboard in CRM Analytics?"
  - "How do I connect Salesforce object data to a CRM Analytics dataset?"
  - "deploy a CRM Analytics app with its dashboards and recipes from sandbox to production"
  - "set up a blank CRM Analytics app, recipe, and dashboard for the sales team"
tags:
  - crm-analytics
  - analytics-studio
  - datasets
  - lenses
  - dashboards
  - einstein-analytics
  - analytics-app
  - crm-analytics-app-creation
  - dataset
  - lens
  - sharing
inputs:
  - "CRM Analytics license type (Growth, Plus, or Einstein Analytics)"
  - "Data sources: Salesforce objects, CSV files, or external connectors"
  - "Target audience: internal users, partner community, or executives"
  - "Permission sets assigned to target users"
outputs:
  - "CRM Analytics app container with configured sharing roles"
  - "Dataset connected to Salesforce object data via dataflow or recipe"
  - "Lens exploring the dataset"
  - "Dashboard assembling lenses with filters and faceting"
  - "Row-level security configuration guidance"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
runtime_orphan: true
runtime_orphan_reason: "No run-time agent covers CRM Analytics / Einstein Discovery. This skill was previously listed in audit-router's Mandatory Reads, but no audit-router classifier routes to it and report_dashboard's own scope excludes CRM Analytics migration, so the citation was decorative rather than load-bearing. Removed 2026-08-14 rather than left as a citation an agent never honoured. Re-wire when a CRM Analytics agent exists."
---

# CRM Analytics App Creation

This skill activates when a practitioner needs to create a CRM Analytics (formerly Einstein Analytics) application — setting up the app container, connecting data sources, creating lenses and dashboards, and configuring app sharing and row-level security. It covers the foundational creation workflow and the critical security gap between permission set assignment and actual data access.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License is required**: CRM Analytics features require a CRM Analytics Growth, Plus, or Einstein Analytics license assigned to the user. Confirm the license is provisioned before attempting to access Analytics Studio.
- **Most common wrong assumption**: Assigning a CRM Analytics permission set is not sufficient to give users access to data. Users also need explicit Viewer, Editor, or Manager access on the specific app AND row-level security must be configured independently of Salesforce object-level sharing (OWD, role hierarchy, sharing rules). All three layers must be configured.
- **Data is not queried live**: CRM Analytics datasets are materialized copies of Salesforce data. Data must be refreshed via a scheduled dataflow or recipe run. Practitioners expecting real-time data will see stale results until the next scheduled run.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which groups need to open the app, and which need to edit or manage it?" | A permission set opens Analytics Studio; app sharing opens the app (Gotcha 1) | A sharing table: group, access level (View, EditAllContents, Manage) | Users see the dashboards on day one, and only a few can change them |
| "Which rows may each audience see, and does Salesforce sharing already express it?" | No row-level security shows every row; inheritance is slower and needs a backup predicate (Gotchas 5, 8) | A predicate or inheritance-plus-backup per dataset | The app never shows more than Salesforce would |
| "How fresh must each dataset be, and how many other recipes already run?" | Runs share a 60-per-day budget and low concurrency (Gotcha 2) | A refresh cadence per dataset inside the org's run budget | Schedules never block each other or lock out data sync |
| "Must widgets on different datasets filter each other?" | Faceting crosses datasets only through connected data sources or bindings (Gotcha 3) | The shared fields to link, or a binding design | Click-to-filter works across the whole dashboard |
| "Will this start from a template, and how far will it be extended?" | Sales and Service Analytics templates cap custom objects at 10 by contract (Gotcha 7) | A template or blank-app decision with the extension plan | The app does not hit a contractual wall mid-project |
| "How will the app move between orgs?" | Hand-edited `.wdash` files fail, datasets deploy without rows, and recipe wildcards miss dataflows (Gotcha 6) | A retrieve-and-deploy manifest and a post-deploy run list | Promotion is repeatable and the target app has data before users arrive |

What proper configuration adds over "just creating an app": access at three layers (permission set, app share, row-level security) that match the audience, refresh schedules that fit the org's budget, and a deployment path that carries the app intact.

## Core Concepts

### App Structure: Apps, Lenses, and Dashboards

A CRM Analytics app is a named container created in Analytics Studio. It holds:

- **Datasets**: Materialized tabular data structures loaded from Salesforce objects, CSV files, or external connectors. Datasets are versioned — lenses and dashboards query a specific dataset version.
- **Lenses**: A saved single-dataset exploration. A lens is a query with groupings, measures, and chart type selected. Lenses are used as the building blocks of dashboard steps.
- **Dashboards**: Multi-lens views that assemble multiple lenses/steps with filters, faceting, and cross-widget interactions. Dashboards support user-controlled filtering and are the primary end-user interface.

Lenses query exactly one dataset. Dashboards can reference steps from multiple datasets. Faceting filters steps on the same dataset by default; across datasets it needs connected data sources (`dataSourceLinks`) or bindings. (Corrected: the earlier text said faceting only works within one dataset.)

### Data Ingestion: Dataflows and Recipes

Data flows into CRM Analytics datasets through:

- **Dataflows**: JSON-defined ETL pipelines. More powerful but more complex. The primary mechanism for joining multiple Salesforce objects into a single dataset.
- **Recipes (Data Prep)**: Visual node-based transformation canvas. Easier for admins; supports join, filter, bucket, and aggregate operations. The recommended starting point for most admin-authored datasets.

Both require **Data Sync** (connected objects) to replicate Salesforce object data into the CRM Analytics staging layer first. Connected objects "can't be visualized directly, but are used like a cache" (REST Guide), so they must feed a dataflow or recipe first. UNVERIFIED (2026-10-03): the earlier statement that connected objects do not count against dataset row limits was not confirmed.

### Three-Layer Security Architecture

CRM Analytics security is independent of Salesforce object-level security and has three distinct layers:

1. **Permission Set / License**: The user must have a CRM Analytics permission set assigned (e.g., CRM Analytics Plus User).
2. **App Access**: The user must have Viewer, Editor, or Manager access on the specific app. Assigned in Analytics Studio > App > Share.
3. **Row-Level Security**: If the dataset contains data the user should not see all of, a security predicate (SAQL filter string) or sharing inheritance must be configured on the dataset.

None of these layers inherit from Salesforce OWD or role hierarchy automatically. All three must be explicitly configured.

---

## Common Patterns

### Creating a Sales Pipeline Dashboard

**When to use:** Building a pipeline visibility dashboard for sales managers using Opportunity, Account, and User data from Salesforce.

**How it works:**
1. In Analytics Studio, select Create > App > Blank App. Name the app and save.
2. Enable Data Sync for Opportunity, Account, and User objects (Data Manager > Connected Objects).
3. Create a recipe (Data Prep) that loads the Opportunity connected object, joins Account on AccountId, and outputs to a registered dataset named "SalesPipeline."
4. Schedule the recipe to run daily after data sync.
5. Create a lens: open the SalesPipeline dataset, group by StageName, measure SUM(Amount), select bar chart, save as a lens.
6. Create a dashboard: add a step linked to the lens, add a date filter widget, configure faceting for the StageName chart, save.
7. Configure sharing: App > Share, add the sales manager group as Viewer.

**Why not standard reports:** Standard Salesforce reports cannot perform multi-source joins or the kind of cross-object aggregations CRM Analytics datasets support at millions of records.

### Template App Creation

**When to use:** Creating a standardized app for a common use case (Sales Cloud, Service Cloud) rather than building from scratch.

**How it works:**
1. In Analytics Studio, select Create > App > Use a Template.
2. Choose the appropriate template (e.g., Sales Analytics, Service Analytics).
3. Walk through the configuration wizard: select Salesforce objects, configure field mapping, set refresh schedule.
4. Template apps auto-create connected objects, recipes/dataflows, datasets, and pre-built dashboards.
5. After creation, customize dashboards and configure app sharing.

Template apps reduce initial setup time significantly but may include unused assets. Prune unused datasets and dashboards to reduce dataflow runtime and storage consumption.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First CRM Analytics app for a team | Template App (if available for use case) | Pre-built dataflows, datasets, and dashboards reduce setup time |
| Custom multi-object dataset | Data Prep Recipe (admin) or Dataflow (developer) | Recipe is admin-friendly; Dataflow handles complex joins |
| Users see app but no data | Check app sharing + row-level security | Permission set alone does not grant row access |
| Real-time data requirement | Not natively supported — use Direct Data for specific cases | Datasets refresh on schedule, not on query |
| Data restricted by user | Add security predicate to dataset | Without predicate, Viewers see all dataset rows regardless of Salesforce sharing |
| Cross-dataset dashboard filtering | Connected data sources for faceting on a shared field; bindings otherwise | Default faceting stays within one dataset (Gotcha 3) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify license and permission** — Confirm the admin user has CRM Analytics Plus User or equivalent permission set. Navigate to Analytics Studio to confirm access. If inaccessible, the license may not be provisioned.
2. **Create the app container** — In Analytics Studio, select Create > App. Choose Blank App for custom builds or Use a Template for standard use cases. Assign an app name and save.
3. **Enable Data Sync for required objects** — In Analytics Studio > Data Manager > Connected Objects, enable sync for each Salesforce object needed. Schedule sync to run before the dataflow/recipe.
4. **Build the dataset via recipe or dataflow** — Create a Data Prep Recipe or Dataflow that loads connected objects, applies joins and transformations, and outputs to a registered dataset. Schedule to run after each data sync.
5. **Create a lens** — Open the dataset, select groupings and measures, apply a chart type, and save as a lens within the app.
6. **Build the dashboard**: Create a new dashboard in the app. Add steps referencing lenses or write inline SAQL. Add filter widgets and configure faceting for same-dataset interactions. Use connected data sources or bindings for cross-dataset filtering.
7. **Configure app sharing and row-level security, then make it deployable**: In App Settings > Share, assign Viewer/Editor/Manager to target users or groups. Separately, configure a security predicate on the dataset if users should see only a restricted subset of rows. Retrieve the app's metadata with the manifest in `references/examples.md`, Example 3.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CRM Analytics license confirmed for all target users
- [ ] Permission set (CRM Analytics Plus User or equivalent) assigned to target users
- [ ] App sharing configured: target users have Viewer or higher access on the app
- [ ] Dataset created and scheduled to refresh on appropriate cadence
- [ ] Row-level security predicate or sharing inheritance configured if users should see restricted data
- [ ] Dashboard filters and faceting tested with a non-admin test user
- [ ] Connected objects not referenced directly in dashboards (only registered datasets)

---

## Salesforce-Specific Gotchas

The full list with sources is in `references/gotchas.md`. The ones that most often leave a new app empty:

| Gotcha | Consequence |
|---|---|
| Permission set is not app access (Gotcha 1) | Users open Analytics Studio but see no data until the app is shared |
| Connected objects are a cache (Gotcha 4) | They feed recipes; lenses and dashboards need a registered dataset |
| Cross-dataset faceting needs connected data sources or bindings (Gotcha 3) | Click-to-filter silently stops at the dataset boundary |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CRM Analytics app | Named container with Viewer/Editor/Manager sharing configuration |
| Dataset | Materialized data from Salesforce objects, scheduled for refresh |
| Lens | Single-dataset exploration saved as a reusable component |
| Dashboard | Multi-lens view with filters, faceting, and user interactions |
| Row-level security predicate | SAQL filter string limiting which rows each user sees |

---

## Related Skills

- analytics-dashboard-design — Deep guidance on dashboard bindings, faceting, and chart configuration
- analytics-permission-and-sharing — In-depth row-level security predicate design and sharing inheritance
