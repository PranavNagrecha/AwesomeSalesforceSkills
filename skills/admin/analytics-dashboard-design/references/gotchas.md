# Gotchas — CRM Analytics Dashboard Design

## Gotcha 1: Static columnMap Breaks Dynamic Binding Output Silently

**What happens:** After adding a binding that changes a chart's measure or grouping dynamically (e.g., a toggle between Amount and Count), the chart renders zero values or blank data for all elements. The SAQL query executed in isolation returns correct results. The chart appears to work but shows wrong numbers.

**When it occurs:** Any chart widget that has a binding injecting a dynamic measure name or grouping field, where the widget's `columnMap` property still references the original hard-coded column names from the initial chart build. This is the most common invisible correctness bug in CRM Analytics dashboards using dynamic bindings.

**How to avoid:** Whenever a binding changes what columns a SAQL step returns (different measure name, different grouping), remove the `columnMap` from the widget definition in dashboard JSON and replace it with `"columns": []`. The chart renderer will then dynamically map axes to whatever columns the current query returns. Always check `columnMap` when debugging a chart that shows zeros or blanks after a binding is added.

---

## Gotcha 2: Faceting Has No Effect on Widgets Using a Different Dataset

**What happens:** Faceting is enabled on multiple widgets on the same dashboard. Clicking a bar in Chart A appears to apply a selection (the bar highlights), but Chart B does not update its data. No error is shown. Multiple attempts to re-enable faceting, change widget order, or refresh the dashboard produce no change.

**When it occurs:** When Chart A and Chart B query different datasets. Faceting is entirely dataset-scoped — it propagates the filter only to other widgets that use the same dataset as the clicked widget.

**How to avoid:** Before enabling faceting, confirm all widgets that should participate in cross-widget filtering query the same dataset. For cross-dataset filtering, use selection bindings instead. If cross-dataset filtering is a requirement discovered mid-build, consider joining the datasets at the ETL layer (recipe or dataflow) to produce a single unified dataset, then use faceting on the unified dataset.

---

## Gotcha 3: Mobile Layout Is Not Inherited from Desktop

**What happens:** An admin builds a fully designed desktop dashboard and deploys it. Mobile users open the dashboard on their phones and see a scaled-down version of the desktop grid — widgets are tiny, text is unreadable, and filter controls are too small to interact with. No mobile-specific layout was ever configured.

**When it occurs:** Any dashboard deployed to users who access Salesforce on mobile devices when the Mobile Designer mode was never used. The mobile layout canvas is completely separate from the desktop canvas and must be explicitly configured.

**How to avoid:** If mobile is a target platform, switch the Designer to Mobile mode (phone icon in the toolbar) after completing the desktop layout. Arrange widgets in a single-column stack appropriate for phone screen width. Prioritize the most important KPI widgets at the top. Reduce the number of visible widgets on mobile — not all desktop widgets need to be on mobile. Test on an actual mobile device before sign-off.
