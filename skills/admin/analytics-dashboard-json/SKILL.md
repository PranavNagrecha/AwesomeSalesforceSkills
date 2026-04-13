---
name: analytics-dashboard-json
description: "Use this skill when editing CRM Analytics dashboard JSON directly to implement advanced bindings, custom SAQL/SOQL step queries, layout changes, step parameters, or cross-widget interactions. Trigger keywords: dashboard JSON, SAQL step, binding syntax, mustache binding, dashboard REST API, widget layout, step limit, datasetId, datasetVersionId. NOT for standard dashboard builder UI configuration, chart type selection, or dataset design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "I need to edit the dashboard JSON directly to wire a filter from one widget to another using a binding"
  - "My SAQL step is only returning 2000 rows but I need more — how do I raise the limit?"
  - "How do I use the CRM Analytics REST API to GET or PUT the full dashboard body so I can version-control it?"
tags:
  - crm-analytics
  - dashboard
  - json
  - bindings
inputs:
  - "Dashboard JSON body (retrieved via GET /wave/dashboards/{id} or exported from the dashboard editor)"
  - "Target step name(s) and field names required for the binding"
  - "Dataset identifiers: datasetId and datasetVersionId for SAQL steps"
outputs:
  - "Modified dashboard JSON body ready for PUT /wave/dashboards/{id}"
  - "Binding expressions in mustache syntax for cross-widget filtering"
  - "Validated SAQL step definitions with explicit row limits and dataset ID references"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# CRM Analytics Dashboard JSON

This skill activates when a practitioner needs to edit a CRM Analytics dashboard's JSON body directly — covering SAQL/SOQL step construction, binding syntax, layout manipulation, step parameters, and the REST API workflow for GET/PUT operations. It does not cover the standard dashboard builder UI or dataset design.

---

## Before Starting

Gather this context before working on anything in this domain:

- Retrieve the current dashboard JSON via `GET /services/data/vXX.X/wave/dashboards/{dashboardId}` and inspect the `state`, `steps`, and `widgets` top-level keys before making any edits.
- Identify dataset references: practitioners commonly assume dataset name is sufficient — it is not. You need `datasetId` and `datasetVersionId` from `GET /services/data/vXX.X/wave/datasets` to construct portable SAQL steps.
- Know the row limit in play: SAQL steps default to 2,000 rows. If a downstream binding or widget depends on a full population, the default will silently truncate results without any error.

---

## Core Concepts

### Dashboard JSON Structure

Every CRM Analytics dashboard body is a JSON document with three top-level sections:

**`steps`** — A map of named query definitions. Each step runs a SAQL or SOQL query against a dataset and holds its results in memory for widget binding. Steps declare their `query` (SAQL string or SOQL string), `type` (`saql` or `soql`), `datasets` array, and optional `limit` property. The `limit` defaults to 2,000 rows and can be raised to a maximum of 10,000 per step.

**`widgets`** — A map of named visual components. Each widget specifies its `type` (chart, table, filter, text, etc.), its pixel-based `layout` (top, left, width, height in pixels), and its `parameters` object which maps widget inputs (e.g., `measures`, `dimensions`, `filters`) to step results via binding expressions.

**`state`** — A map of global selections, active filters, and interaction state. State carries the current user selection from one widget so that other widgets can read it via bindings. State is modified at runtime by user interaction and can be pre-seeded with default values.

### Binding Syntax

Bindings are mustache-delimited expressions embedded in widget `parameters` values. They read from either step results or selection state at render time.

The canonical cell-level binding form is:

```
{{cell(stepName.selection, 0, "fieldName")}}
```

- `stepName` — the key in the `steps` map
- `.selection` — reads the user's current selection in that step
- `0` — the row index (zero-based)
- `"fieldName"` — the field to extract

An empty binding (when the referenced cell has no value, such as when no selection has been made) returns an empty string, not an error or null. This causes silent suppression: a filter widget whose bound value is empty will produce no filter clause, which may return unintended full-population results rather than an empty result set.

Array bindings for multi-select filters use:

```
{{#arrayToObject}}...{{/arrayToObject}}
```

or the `columnMap` binding form for mapping multiple fields simultaneously.

### Dataset References in SAQL Steps

SAQL steps reference datasets inside the `datasets` array of the step definition. The `name` field in the datasets array is the display alias used in the SAQL query body. The **`id`** and **`label`** fields, however, must use the `datasetId` and `datasetVersionId` obtained from the dataset API — not the human-readable dataset name used in the UI.

Using only the dataset name instead of the `id`/`version` pair causes the step to resolve by name lookup at render time. This works in a single org but breaks silently when the dashboard is migrated, cloned into a sandbox, or deployed via Metadata API — because dataset IDs differ across orgs and the name may not match. The SAQL step returns no results rather than an error.

### REST API Versioning

CRM Analytics dashboards are versioned via the History API. Every `PUT /services/data/vXX.X/wave/dashboards/{dashboardId}` call that modifies the dashboard body automatically creates a new history snapshot. Previous versions are accessible at:

```
GET /services/data/vXX.X/wave/dashboards/{dashboardId}/histories
```

This means every PUT is non-destructive — the prior version is always recoverable. However, there is no built-in diff view; practitioners must compare full JSON bodies manually or via script.

---

## Common Patterns

### Cross-Widget Binding via Selection State

**When to use:** A filter widget (list selector, range slider) in one part of the dashboard should drive the data shown in charts or tables elsewhere, across datasets.

**How it works:**
1. Define a step for the filter source dataset. Set `selectionFields` to the field you want to expose (e.g., `["Account.Industry"]`).
2. In the target chart step's SAQL query, add a `where` clause that reads the binding:
   ```
   | filter 'Industry' in ["{{#each cell(filterStep.selection, 0, "Industry")}}{{this}}{{/each}}"]
   ```
3. In the target widget's `parameters`, bind `filters` to the selection state of the source step.
4. Test with no selection (binding returns empty string) to confirm the default behavior is acceptable.

**Why not hardcode values:** Hardcoded filter values cannot be driven by user interaction. Faceting (automatic cross-filtering) only works within the same dataset; cross-dataset filtering requires explicit bindings in JSON.

### Raising SAQL Step Row Limits

**When to use:** A step backing a table or export widget needs to surface more than 2,000 records, or a step used as a binding source needs a full population to avoid silent truncation.

**How it works:**
Add the `limit` property to the step definition in the `steps` map:

```json
"myStep": {
  "type": "saql",
  "query": "q = load \"datasetId/datasetVersionId\"; q = limit q 10000; q;",
  "datasets": [...],
  "limit": 10000
}
```

Both the `limit` property on the step object and the `limit` clause in the SAQL query string must be set. The platform enforces a hard maximum of 10,000 rows per step regardless of the value set.

**Why not rely on default:** The 2,000-row default is silently applied. There is no UI warning when results are truncated — the widget renders with partial data and no error message.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Filtering across two datasets | Explicit step binding using mustache cell() expression | Faceting only works within a single dataset |
| Dashboard migration across orgs | Use datasetId + datasetVersionId in SAQL step datasets array | Name-based resolution fails silently in target org |
| Need more than 2,000 rows in a step | Set `limit: 10000` on step AND add `limit 10000` in SAQL query | Both must be set; SAQL alone or property alone is insufficient |
| Recovering a prior dashboard version | GET /wave/dashboards/{id}/histories and re-PUT the desired body | PUT auto-creates history; old versions are always accessible |
| Debugging an empty binding result | Check if the source selection step has an active user selection | Empty binding = empty string, not error; no selection = no value |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner editing dashboard JSON:

1. **Retrieve the current dashboard body** via `GET /services/data/vXX.X/wave/dashboards/{dashboardId}`. Save the full JSON response as a working copy before making any changes — the History API preserves versions after PUT, but having a local baseline is essential for diffing.
2. **Resolve dataset identifiers** via `GET /services/data/vXX.X/wave/datasets` before constructing or modifying any SAQL step. Record the `id` (datasetId) and the `currentVersionId` (datasetVersionId) for every dataset the dashboard queries. Do not use display names.
3. **Edit steps first, then widgets, then state.** Steps are referenced by name from widgets; editing in this order avoids forward-reference confusion. When adding a new step, assign it a camelCase key in the `steps` map and verify it is unique.
4. **Construct bindings using the exact mustache syntax** `{{cell(stepName.selection, 0, "fieldName")}}`. Test the empty-binding case: when no selection exists, the binding returns an empty string. Decide explicitly whether an empty binding should produce no filter (full population) or a zero-result filter, and handle accordingly in the SAQL where clause.
5. **Set explicit row limits** on any step where truncation matters. Add both `"limit": 10000` to the step object and `limit 10000` to the SAQL query string. The platform maximum is 10,000 rows per step.
6. **PUT the modified body** via `PUT /services/data/vXX.X/wave/dashboards/{dashboardId}` with `Content-Type: application/json`. The platform automatically creates a history snapshot. Verify the response `id` and `lastModifiedDate` match expectations.
7. **Validate in the dashboard UI** by opening the dashboard, triggering every filter interaction, and confirming that cross-widget bindings resolve correctly and no widgets show empty or unexpected results.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All SAQL steps reference datasets by `datasetId` and `datasetVersionId`, not by display name
- [ ] All mustache binding expressions use the exact form `{{cell(stepName.selection, 0, "fieldName")}}`
- [ ] Empty-binding behavior (no active selection) is explicitly handled for all filter-driven steps
- [ ] Any step returning more than 2,000 rows has `"limit"` set on the step object and in the SAQL query string
- [ ] The dashboard JSON was retrieved via REST API before editing and the full body was PUT back (not a partial update)
- [ ] History API was confirmed to have a new snapshot after the PUT (verify via GET /histories)
- [ ] Cross-widget filter interactions were tested end-to-end in the dashboard UI

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Dataset name resolution fails silently across orgs** — Using the dataset display name instead of `datasetId`/`datasetVersionId` in a SAQL step's datasets array works in the authoring org but resolves by name lookup at render time. When the dashboard is deployed to another org or sandbox, the name may not exist or may point to a different dataset. The step returns no results — no error is thrown, no warning is displayed.
2. **Empty bindings return empty string, not null or error** — When a binding's source step has no active user selection, `{{cell(stepName.selection, 0, "fieldName")}}` returns an empty string. A SAQL `where` clause built around this value may behave differently than intended: some constructs silently drop the filter (returning the full population) while others produce a literal empty-string comparison that returns zero rows.
3. **SAQL step row limit defaults to 2,000 with no UI warning** — Truncation is silent. A step returning exactly 2,000 rows is almost always truncated. Widgets render partial data with no indicator. The maximum is 10,000, and both the step-level `limit` property and the SAQL `limit` clause must be set explicitly.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Modified dashboard JSON body | Full dashboard JSON ready for PUT to /wave/dashboards/{id} |
| SAQL step definitions | Step objects with datasetId/datasetVersionId references, explicit limits, and query strings |
| Binding expressions | Mustache cell() expressions for cross-widget filter wiring |

---

## Related Skills

- admin/analytics-dashboard-design — Design-level decisions (chart type selection, faceting, layout structure) that precede JSON editing
