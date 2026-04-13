# Examples — CRM Analytics Dashboard Design

## Example 1: Chart Shows Zero Values After Adding a Measure Selector Binding

**Context:** An admin builds a CRM Analytics dashboard for sales managers. The dashboard includes a bar chart showing Opportunity amount by stage, and a toggle widget that lets users switch between "Amount (Sum)" and "Count of Records" as the measure.

**Problem:** After configuring a binding to inject the selected measure into the chart's SAQL step, the chart shows zeros for all stages when the user selects "Count." Switching back to "Amount" also shows zeros. The SAQL step query is correct when executed in isolation.

**Problem cause:** The chart widget's `columnMap` property still maps `amount_sum` to the Y axis — the original hard-coded column name. When the binding changes the SAQL to return `count` instead of `amount_sum`, the chart cannot find the `amount_sum` column in the result set and renders zero.

**Solution:**

Locate the widget definition in dashboard JSON and replace the `columnMap`:

```json
// BEFORE (broken — static columnMap)
"columnMap": {
  "dimension": ["StageName"],
  "measures": ["amount_sum"]
}

// AFTER (correct — let the binding control column mapping)
"columns": []
```

After this change, the chart accepts whatever columns the current SAQL step returns, correctly rendering either `amount_sum` or `count` based on the user's selection.

**Why it works:** `"columns": []` removes the static column expectation from the widget, allowing the runtime to dynamically map the chart's axes to whatever the SAQL step returns.

---

## Example 2: Cross-Dataset Filtering with Selection Bindings

**Context:** A service operations dashboard has two charts: "Open Cases by Region" (from a Case dataset) and "Pipeline by Region" (from an Opportunity dataset). The manager wants clicking a region bar in the Cases chart to filter the Pipeline chart to the same region.

**Problem:** Faceting is enabled on both widgets, but clicking a region bar in the Cases chart has no effect on the Pipeline chart. Faceting only works within the same dataset.

**Solution:**

1. In the dashboard JSON, locate the Cases chart step (named `CasesByRegion`).
2. In the Opportunities chart step (named `PipelineByRegion`), add a filter binding:

```json
"filters": [
  ["Region__c", "{{cell(CasesByRegion.selection, 0, 'Region__c')}}", "=="]
]
```

3. Add a `defaultFilterValues` for the binding to handle the no-selection state:

```json
"filters": [
  ["Region__c", "{{coalesce(cell(CasesByRegion.selection, 0, 'Region__c'), '')}}", "=="]
]
```

When `CasesByRegion` has no selection, the coalesce returns an empty string, which effectively applies no filter.

4. Test: click "West" in the Cases chart — the Pipeline chart should update to show only West region opportunities.

**Why it works:** Selection bindings read the current selection state of any named step and inject the value into another step's SAQL at query time. This crosses dataset boundaries, unlike faceting.

---

## Anti-Pattern: Using Faceting to Filter Across Multiple Datasets

**What practitioners do:** Build a dashboard with widgets from two different datasets (e.g., Cases and Accounts). Enable faceting on all widgets expecting that user clicks will filter the entire dashboard.

**What goes wrong:** Clicking on a Cases widget applies the facet filter only to other widgets using the Cases dataset. Account widgets are unaffected — they do not update. No error is shown. The admin wastes time debugging facet settings, enabling/disabling the facet toggle, and checking dataset names, finding no configuration error because the configuration is correct — faceting simply does not cross datasets.

**Correct approach:** For cross-dataset filtering, use selection bindings. Edit the dashboard JSON to add a binding on the secondary step that reads from the primary step's selection. Document which steps are bound to which in a comment in the JSON — binding relationships are not visible in the visual Designer and are easily forgotten during maintenance.
