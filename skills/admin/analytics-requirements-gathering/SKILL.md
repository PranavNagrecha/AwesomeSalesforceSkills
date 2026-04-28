---
name: analytics-requirements-gathering
description: "Use this skill to elicit, document, and validate CRM Analytics requirements — covering data source mapping (Salesforce object sync vs external connector vs Data Cloud), transformation needs, audience-specific lens or dashboard views, and drill-down path specifications — before any dataset or dashboard is built. Trigger keywords: CRM Analytics requirements, analytics data source mapping, CRM Analytics audience requirements, analytics visualization requirements. NOT for standard Salesforce Reports and Dashboards requirements, CRM Analytics implementation, SAQL query development, or KPI formula definition (use analytics-kpi-definition)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "stakeholders have requested CRM Analytics dashboards but no requirements document exists yet"
  - "need to map which Salesforce objects and external sources will feed CRM Analytics datasets"
  - "different user roles need different views of the same data — need to document audience-specific requirements"
  - "analytics project kickoff needs to capture data source types, transformation needs, and drill-down paths"
  - "team needs to know if standard Reports can serve the need or if CRM Analytics is required"
tags:
  - crm-analytics
  - requirements-gathering
  - analytics-requirements
  - data-source-mapping
  - analytics-requirements-gathering
inputs:
  - "List of stakeholder reporting needs and questions the analytics should answer"
  - "User roles and personas who will use the analytics"
  - "Data sources: Salesforce objects, external files, Data Cloud DMOs"
  - "Existing report or dashboard examples that show what stakeholders want"
outputs:
  - "CRM Analytics requirements document with data source inventory"
  - "Audience matrix mapping user roles to specific lens or dashboard views"
  - "Data transformation requirements for dataflow/recipe design"
  - "Decision record: CRM Analytics vs standard Reports"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Analytics Requirements Gathering

This skill activates when a practitioner needs to gather, document, and validate CRM Analytics requirements before any dataset, dataflow, or dashboard is built. It produces a structured requirements package — data source inventory, audience matrix, transformation requirements, and drill-down specifications — that the analytics developer uses as the authoritative spec.

---

## Before Starting

Gather this context before working on anything in this domain:

- The first question to answer: Do stakeholders need CRM Analytics or standard Reports and Dashboards? CRM Analytics is appropriate for cross-object aggregation, predictive insights, and multi-audience views. For simple single-object reports with no cross-object joins, standard Reports are the correct (and license-free) choice.
- CRM Analytics requires Salesforce CRM Analytics Growth or Plus license. Confirm the org has the required license before committing to CRM Analytics.
- The most common wrong assumption: practitioners assume synced Salesforce objects are immediately usable as CRM Analytics data sources without a dataset step. Every data source (Salesforce object sync, external file, Data Cloud Direct) requires a dataflow or recipe to create a dataset before it can be queried.
- Requirements must capture data source type (Salesforce object sync vs external connector vs Data Cloud direct vs CSV/External Data API) — this determines whether a recipe or a dataflow runs the transformation.

---

## Core Concepts

### Data Source Types

CRM Analytics has four distinct data source types with different setup requirements:

| Source type | Setup |
|---|---|
| Salesforce object sync | Direct connection to Salesforce standard and custom objects; configured in Data Manager; requires a dataflow or recipe to create a dataset |
| External connector | Snowflake, AWS S3, Google BigQuery, etc.; requires Named Credential and Connector setup; data pulled via recipe |
| Data Cloud Direct | Real-time query of Data Cloud Data Model Objects (DMOs) without dataset creation; available in Spring '25+ for specific query patterns; does not support all SAQL operations |
| CSV/External Data API | Static file upload; creates a dataset directly; requires manual or API-driven refresh |

Requirements must specify which type each data source is — the implementation path differs significantly.

### Audience-Specific Views

CRM Analytics supports multiple access patterns for different audiences:
- **Sharing inheritance** — Row-level security inherited from Salesforce record sharing
- **Predicate-based row-level security** — Custom SAQL predicates filtering data to the viewing user's role or territory
- **Separate dashboards per audience** — Different dashboard designs for different roles (e.g., VP dashboard vs rep dashboard)

Requirements must document which rows each audience can see and whether they need different visualizations or just different filtered views of the same data.

### Transformation Requirements

Raw Salesforce object data often requires transformation before it is useful in CRM Analytics:
- Field remapping and renaming for consistent naming across datasets
- Computed fields (revenue tiers, fiscal period labels, region groupings)
- Dataset joins (Account + Opportunity joined dataset)
- Date dimension augmentation (fiscal year/quarter derived from CloseDate)

Requirements must specify each transformation explicitly — the developer cannot infer them from field names alone.

---

## Common Patterns

### Pattern: Data Source Mapping Matrix

**When to use:** At the start of every CRM Analytics requirements engagement — before any dataset or recipe is designed.

**How it works:**
1. List all data sources stakeholders need in the analytics
2. For each source: identify the type (Salesforce object / external connector / Data Cloud / CSV), the connection mechanism, and the refresh frequency required
3. For Salesforce objects: list all fields needed (not just the objects) — unnecessary fields increase dataset size and dataflow runtime
4. For external connectors: confirm Named Credential and connector setup exists or is in scope

**Why not the alternative:** Leaving data source type unspecified causes the developer to choose the connection mechanism arbitrarily, which leads to wrong refresh cadence or missing incremental update configuration.

### Pattern: Audience Matrix

**When to use:** When more than one user role will access the analytics and they should see different data or layouts.

**How it works:**
1. List all user roles/personas
2. For each role: document what data rows they can see (all data / own territory / direct reports / etc.)
3. For each role: document whether they need a different dashboard layout or just a filtered view of a shared dashboard
4. Specify the row-level security mechanism: sharing inheritance, SAQL predicate, or separate org-wide defaults

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-object reporting with filters and grouping | Standard Reports and Dashboards | No CRM Analytics license required; covers single-object use cases natively |
| Cross-object aggregation (Opp + Account + Activity) | CRM Analytics | Standard Reports cannot join three or more objects efficiently |
| Predictive scoring or trend analysis | CRM Analytics with Einstein Discovery | Predictive capabilities require CRM Analytics license |
| Data from external databases (Snowflake, BigQuery) | CRM Analytics external connector | External data cannot feed standard Reports |
| Real-time Data Cloud data | Data Cloud Direct connection in CRM Analytics | Spring '25+ feature; check if applicable query patterns are supported |
| Different views for VP vs individual rep | CRM Analytics with audience-specific predicate or separate dashboards | Standard Dashboards have limited row-level security |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Determine whether CRM Analytics is required or if standard Reports can serve the need — document this decision with the rationale.
2. Confirm CRM Analytics license availability in the org before proceeding.
3. List all reporting questions stakeholders need the analytics to answer — these drive the data model.
4. For each reporting question: identify the data source type (Salesforce object sync / external connector / Data Cloud / CSV) and document it in the data source matrix.
5. For each data source: list the specific fields needed (not just the object) — unnecessary fields increase dataflow runtime.
6. Document transformation requirements: joins needed, computed fields, date dimension derivations, and field renames for consistency.
7. Build the audience matrix: list all user roles, what rows each can see, and whether they need different layouts.
8. Specify drill-down paths: for each summary visualization, document what level of detail users should be able to drill into.
9. Review with stakeholders and the developer to confirm the requirements are complete and buildable before dataset design begins.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CRM Analytics vs standard Reports decision documented with rationale
- [ ] CRM Analytics license confirmed
- [ ] All data sources identified with type (object sync / external / Data Cloud / CSV)
- [ ] Field-level requirements documented for each data source (not just object names)
- [ ] Transformation requirements specified (joins, computed fields, date dimensions)
- [ ] Audience matrix complete with row-level security specification
- [ ] Drill-down paths documented for each summary visualization
- [ ] Refresh cadence specified for each data source

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Synced objects are not immediately usable — a dataset step is required** — Enabling Salesforce object sync in CRM Analytics Data Manager does not create a queryable dataset. The sync brings data into the analytics storage layer, but a dataflow or recipe must run to create a dataset from the synced object. Requirements that say "use the Opportunity object" without specifying the dataset creation step leave a gap in the developer's understanding.
2. **Data Cloud Direct query does not support all SAQL operations** — Spring '25+ Data Cloud Direct connection allows real-time queries of Data Cloud DMOs without a dataset, but not all SAQL operations are supported (no recipe transforms, limited GROUP BY patterns). Requirements that specify Data Cloud Direct must confirm that the required query patterns are supported.
3. **External connector data does not support incremental refresh by default** — External connector data sources pull full datasets on each recipe run unless incremental refresh is explicitly configured. Large external tables (millions of rows) run slowly with full refreshes. Requirements must specify whether incremental refresh is needed and whether the external source supports a reliable watermark field.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CRM Analytics requirements document | Data source inventory, transformation needs, audience matrix, drill-down paths |
| Data source mapping matrix | Per-source table of type, connection, fields needed, refresh cadence |
| Audience matrix | User roles mapped to row-level security rules and dashboard view requirements |
| CRM Analytics vs Reports decision record | Documented decision with rationale and license confirmation |

---

## Related Skills

- `admin/analytics-kpi-definition` — use after requirements gathering to define KPI formulas and targets before build
- `data/saql-query-development` — downstream implementation skill using requirements from this document
- `admin/requirements-gathering-for-sf` — general Salesforce requirements gathering companion skill
