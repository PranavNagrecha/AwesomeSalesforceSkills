---
name: analytics-dashboard-design
description: "Use when designing or troubleshooting CRM Analytics dashboards — chart types, bindings, faceting, dashboard interactions, mobile layout, and filters. NOT for standard Salesforce reports and dashboards."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "CRM Analytics dashboard chart is showing wrong data after I change the grouping field"
  - "How do I make one widget filter another widget on a different dataset in CRM Analytics?"
  - "What chart types are available in CRM Analytics and when should I use each one?"
  - "How do I configure faceting on a CRM Analytics dashboard?"
  - "CRM Analytics mobile layout looks different from the desktop view — how do I fix it?"
tags:
  - crm-analytics
  - analytics-dashboard-design
  - bindings
  - faceting
  - chart-types
  - mobile-layout
  - dashboard
inputs:
  - "Dashboard purpose and target audience (executive, operational, self-service)"
  - "Datasets used in the dashboard (one or multiple)"
  - "Interaction requirements: does user selection need to filter other widgets?"
  - "Mobile access requirement: yes or no"
outputs:
  - "Dashboard design with chart type recommendations"
  - "Faceting or binding configuration for cross-widget filtering"
  - "Mobile layout configuration guidance"
  - "columnMap correction for dynamic binding scenarios"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# CRM Analytics Dashboard Design

This skill activates when a practitioner needs to design, configure, or troubleshoot CRM Analytics dashboards — including chart type selection, cross-widget filtering via faceting or bindings, dynamic measure/grouping changes, and mobile layout. It specifically covers the columnMap issue that causes charts to silently show wrong data when bindings are used.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify datasets in use**: Know whether the dashboard will reference one dataset or multiple. Single-dataset dashboards can use faceting for filtering. Cross-dataset dashboards must use bindings. This is a fundamental design decision that affects the entire dashboard architecture.
- **Most critical anti-pattern**: When using a binding to dynamically change the measure or grouping field of a chart, the static `columnMap` in the dashboard JSON must be replaced with an empty `columns` array. If the `columnMap` remains static, the chart silently renders data mapped to the old column names regardless of what the binding changes. This is the most common invisible bug in dynamic CRM Analytics dashboards.
- **Mobile layout is separate**: Mobile layout in CRM Analytics is a distinct Designer mode that must be explicitly configured. Widgets do not automatically reflow for mobile — the admin must switch to mobile mode and re-arrange the canvas.

---

## Core Concepts

### Two Interaction Mechanisms: Faceting vs. Bindings

CRM Analytics dashboards have two mechanisms for connecting widget interactions:

- **Faceting**: When a user clicks on a chart element (a bar, a pie slice, etc.), faceting automatically applies that selection as a filter to all other widgets on the dashboard that share the same dataset. Faceting is configured per-widget (enable facet) and works entirely within a single dataset — it cannot cross dataset boundaries. Faceting is simple to set up and covers most single-dataset dashboard use cases.

- **Bindings**: Bindings are explicit connections written in mustache syntax in the dashboard JSON. They pull a value from one query (step) and inject it into another step's SAQL query. Two binding types exist:
  - **Selection bindings**: `{{cell(stepName.selection, 0, "FieldName")}}` — reads the user's currently selected chart element value and injects it into another step's filter, grouping, measure, or limit.
  - **Results bindings**: `{{cell(stepName.result, 0, "FieldName")}}` — reads the computed output value of one step (e.g., a metric or computed field) and uses it to parameterize another step.

Bindings can cross datasets. They enable sophisticated multi-dataset dashboard interactions but require editing the dashboard JSON.

### Chart Types and When to Use Each

| Chart Type | Best For | Key Limitation |
|---|---|---|
| Bar (vertical/horizontal) | Comparing categorical values | Clutter with 15+ categories |
| Line | Trends over time | Requires a date/time dimension |
| Donut/Pie | Part-to-whole proportions | Useless with 6+ segments |
| Scatter | Correlation between two measures | Requires two measures |
| Bubble | Correlation with size dimension | Requires three measures |
| Combo | Trend + volume on same axis | Dual axis can mislead |
| Waterfall | Cumulative changes | Requires ordered sequence |
| Funnel | Stage-based conversion | Ordered stages required |
| Map (geo) | Geographic distribution | Requires lat/long or region |
| Metric | Single KPI display | Single value only |
| Table | Multi-dimensional data grids | Performance intensive with 10K+ rows |

### The columnMap Issue with Dynamic Bindings

When a chart is first built in the designer, its `columnMap` property in the dashboard JSON maps measure and dimension fields to specific column names from the current SAQL query. If a binding later changes which measure or grouping field is returned by the query, the chart's `columnMap` still references the original column names — causing it to silently render incorrect data (often blank or zero values) without any error.

The fix: when using bindings to dynamically change the measure or grouping of a chart, delete the `columnMap` property from the widget definition in dashboard JSON and replace it with an empty `columns` array. This tells the chart renderer to accept whatever column names the current query returns, rather than expecting the originally mapped names.

### Mobile Layout Configuration

CRM Analytics dashboards have two layout modes: Desktop and Mobile. The desktop layout is the default — it uses a pixel-based grid where widgets are positioned absolutely. Mobile layout is a separate canvas that must be explicitly configured by switching the Designer to Mobile mode (the phone icon in the toolbar). Widgets do not automatically reflow from desktop to mobile. Each widget must be repositioned and resized on the mobile canvas separately. If mobile layout is never configured, mobile users see the desktop layout scaled down, which is typically unusable.

---

## Common Patterns

### Single-Dataset Dashboard with Faceting

**When to use:** Dashboard uses one dataset, and clicking on one chart should filter all other charts.

**How it works:**
1. Create the dashboard with all steps querying the same dataset.
2. For each widget that should participate in filtering, enable the facet option in the widget properties.
3. Test: clicking a bar in Chart A should filter Charts B and C to the same dimension value.

**Why not bindings:** Faceting is simpler and requires no JSON editing for same-dataset scenarios. Use bindings only when crossing dataset boundaries or when more complex injection logic is needed.

### Cross-Dataset Filtering with Selection Bindings

**When to use:** Dashboard uses two datasets (e.g., Cases and Opportunities) and user selection in one widget should filter the other.

**How it works:**
1. In the dashboard JSON, find the step that the user will interact with (Step A: Cases by Region).
2. In Step B (Opportunities by Region), add a filter clause driven by a binding:
```
"filters": [["Region__c", "{{cell(stepA.selection, 0, 'Region__c')}}", "=="]]
```
3. When the user clicks "West" in the Cases chart, Step B's query re-runs with `filter by Region__c == "West"`, updating the Opportunities chart.

### Dynamic Measure Selector with columnMap Fix

**When to use:** Dashboard includes a toggle that lets the user switch the chart between different measures (e.g., Amount vs. Count vs. Win Rate).

**How it works:**
1. Create a selector step with options matching the measure field names.
2. In the chart step's SAQL, bind the measure: `foreach q generate 'StageName' as 'StageName', {{cell(measureSelector.selection, 0, 'value')}} as 'measure'`
3. In the dashboard JSON for the chart widget, delete `columnMap` and replace with `"columns": []`.
4. The chart now renders whatever measure the binding returns rather than the hard-coded original.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All widgets on same dataset, user click should filter | Faceting | Simple, no JSON editing, dataset-scoped |
| Widgets on different datasets, need cross-filtering | Selection bindings | Faceting cannot cross dataset boundaries |
| Chart shows wrong data after adding a binding | Check and fix columnMap → columns: [] | Static columnMap ignores dynamic binding output |
| Mobile users need a usable layout | Explicitly configure Mobile Designer mode | Desktop layout does not automatically reflow |
| Part-to-whole proportion of 4–5 categories | Donut chart | Pie/donut works for small segment counts |
| Trend over time | Line chart | Requires date/time dimension |
| Single executive KPI | Metric widget | Purpose-built for single value display |
| User needs to switch between measures | Dynamic binding + selector step + columns: [] fix | Allows runtime measure selection |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify datasets and interaction requirements** — Determine how many datasets the dashboard uses. If one dataset, faceting handles filtering. If multiple datasets, bindings are required for cross-filtering. Document these decisions before building.
2. **Select chart types for each KPI or dimension** — Match each metric to the appropriate chart type based on the data shape: trends → line, comparisons → bar, proportions → donut, single KPI → metric. Avoid donut/pie with 6+ categories.
3. **Build steps (SAQL queries)** — Create one SAQL step per distinct query. Steps are the data source for widgets. Name steps descriptively (e.g., `CasesByPriority`, not `step1`).
4. **Configure faceting (same-dataset dashboards)** — For each widget that should participate in cross-widget filtering, enable the facet option. Test by clicking a chart element and confirming other widgets filter correctly.
5. **Configure bindings (cross-dataset or dynamic dashboards)** — Edit the dashboard JSON to add selection or results bindings between steps. For any binding that changes a chart's measure or grouping, locate the widget's `columnMap` and replace it with `"columns": []`.
6. **Configure mobile layout** — Switch the Designer to Mobile mode. Drag and resize widgets on the mobile canvas to create a usable single-column layout. Save the mobile layout separately.
7. **Test as a non-admin user** — Faceting and bindings behave the same across users, but test that the row-level security predicate still filters data correctly when the user selects a chart element.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All widgets reference named steps (not anonymous inline queries)
- [ ] Faceting configured and tested for same-dataset cross-widget filtering
- [ ] Bindings configured and tested for cross-dataset filtering (if applicable)
- [ ] columnMap replaced with columns: [] for any widget using dynamic measure/grouping bindings
- [ ] Mobile layout explicitly configured (not just relying on desktop layout rescaling)
- [ ] Chart types match the data shape and user intent
- [ ] Dashboard tested with a non-admin user to confirm security predicates work correctly

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Static columnMap breaks dynamic binding output silently** — When a binding changes the measure or grouping of a chart, the chart's `columnMap` still expects the original column names. The chart renders zero or blank values without any error. The fix is always to remove `columnMap` and set `"columns": []` in the widget definition. This is the most common invisible bug in dynamic dashboards.
2. **Faceting ignores widgets on different datasets** — Clicking on a widget that is facet-enabled applies the filter only to other widgets sharing the same dataset. Widgets on a different dataset are not affected — they do not update, and no error is shown. Teams that build multi-dataset dashboards and enable faceting expecting cross-dataset filtering will see no effect and spend time debugging facet configuration.
3. **Mobile layout is not inherited from desktop** — If the mobile canvas is never configured, mobile users see the desktop layout zoomed out to fit the phone screen. Widgets become too small to interact with. Mobile layout must be explicitly set in Designer > Mobile mode for every widget the mobile user will need.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dashboard design document | Chart type decisions, interaction pattern (faceting vs. bindings), mobile layout plan |
| Binding configuration | Mustache binding syntax for cross-dataset or dynamic measure filtering |
| columnMap fix | JSON snippet replacing columnMap with columns: [] for dynamic binding widgets |
| Mobile layout guide | Recommended widget arrangement for mobile canvas |

---

## Related Skills

- crm-analytics-app-creation — Create the app container and dataset before building dashboards
- analytics-permission-and-sharing — Row-level security predicates that affect what dashboard data each user sees
- saql-query-development — Writing SAQL steps that power dashboard widgets
