---
name: crm-analytics-app-creation
description: "Use when creating or configuring a CRM Analytics (Einstein Analytics) app — including app containers, lenses, datasets, data source connections, and app sharing. NOT for standard Salesforce reports and dashboards or Tableau."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
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

## Core Concepts

### App Structure: Apps, Lenses, and Dashboards

A CRM Analytics app is a named container created in Analytics Studio. It holds:

- **Datasets**: Materialized tabular data structures loaded from Salesforce objects, CSV files, or external connectors. Datasets are versioned — lenses and dashboards query a specific dataset version.
- **Lenses**: A saved single-dataset exploration. A lens is a query with groupings, measures, and chart type selected. Lenses are used as the building blocks of dashboard steps.
- **Dashboards**: Multi-lens views that assemble multiple lenses/steps with filters, faceting, and cross-widget interactions. Dashboards support user-controlled filtering and are the primary end-user interface.

Lenses query exactly one dataset. Dashboards can reference steps from multiple datasets, but cross-dataset filtering requires bindings rather than faceting (faceting only works within the same dataset).

### Data Ingestion: Dataflows and Recipes

Data flows into CRM Analytics datasets through:

- **Dataflows**: JSON-defined ETL pipelines. More powerful but more complex. The primary mechanism for joining multiple Salesforce objects into a single dataset.
- **Recipes (Data Prep)**: Visual node-based transformation canvas. Easier for admins; supports join, filter, bucket, and aggregate operations. The recommended starting point for most admin-authored datasets.

Both require **Data Sync** (connected objects) to replicate Salesforce object data into the CRM Analytics staging layer first. Connected objects do not count against dataset row limits but cannot be queried directly — they must feed a dataflow or recipe first.

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
| Cross-dataset dashboard filtering | Use bindings, not faceting | Faceting only works within a single dataset |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify license and permission** — Confirm the admin user has CRM Analytics Plus User or equivalent permission set. Navigate to Analytics Studio to confirm access. If inaccessible, the license may not be provisioned.
2. **Create the app container** — In Analytics Studio, select Create > App. Choose Blank App for custom builds or Use a Template for standard use cases. Assign an app name and save.
3. **Enable Data Sync for required objects** — In Analytics Studio > Data Manager > Connected Objects, enable sync for each Salesforce object needed. Schedule sync to run before the dataflow/recipe.
4. **Build the dataset via recipe or dataflow** — Create a Data Prep Recipe or Dataflow that loads connected objects, applies joins and transformations, and outputs to a registered dataset. Schedule to run after each data sync.
5. **Create a lens** — Open the dataset, select groupings and measures, apply a chart type, and save as a lens within the app.
6. **Build the dashboard** — Create a new dashboard in the app. Add steps referencing lenses or write inline SAQL. Add filter widgets and configure faceting for same-dataset interactions. Use bindings for cross-dataset filtering.
7. **Configure app sharing and row-level security** — In App Settings > Share, assign Viewer/Editor/Manager to target users or groups. Separately, configure a security predicate on the dataset if users should see only a restricted subset of rows.

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

Non-obvious platform behaviors that cause real production problems:

1. **Permission set assignment does not grant data access** — Assigning the CRM Analytics Plus User permission set enables Analytics Studio access and app visibility. It does NOT grant access to data in any specific app or dataset. Users must also be added to the app with Viewer access AND a row-level security predicate must be configured if they should not see all rows. Stopping after permission set assignment produces blank apps with no data visible.
2. **Connected objects cannot be queried directly in dashboards** — Connected objects (created by Data Sync) are intermediate staging-layer replicas. They do not appear as selectable datasets in the lens explorer or dashboard step query. They must first be processed by a recipe or dataflow that outputs to a registered dataset.
3. **Faceting only works within a single dataset** — Faceting automatically filters all widgets sharing the same dataset on user click. It cannot cross datasets. If two dashboard widgets reference different datasets and filtering them together is needed, bindings must be configured. Faceting across datasets silently produces no cross-widget filtering.

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
