---
name: lwc-chart-and-visualization
description: "Charts and visualization in LWC: Chart.js, D3, Plotly via Static Resources; Lightning chart components; performance patterns for 10k+ data points; accessibility; SLDS theming. NOT for CRM Analytics embedding (use crm-analytics-foundation). NOT for Tableau embedding (use tableau-salesforce-connector)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - lwc
  - chart-js
  - d3
  - visualization
  - static-resource
  - lightning-chart
  - accessibility
triggers:
  - "how do we render chart.js inside a lightning web component"
  - "lwc d3 visualization pattern with static resource"
  - "best chart library for lwc performance accessibility"
  - "lightning web component pie chart bar chart line chart"
  - "lwc chart with large dataset 10000 points"
  - "lwc visualization lightning chart vs third party"
inputs:
  - Data source (Apex, UI API, Platform Events, Data Cloud)
  - Volume (dozens, hundreds, thousands, tens of thousands of points)
  - Chart type (bar, line, pie, scatter, map, custom)
  - Theming and accessibility requirements
outputs:
  - Library selection (Chart.js, D3, Plotly, Lightning Chart, custom)
  - Static Resource bundling plan
  - Data pipeline pattern (paginated, streamed, preaggregated)
  - Accessibility and SLDS theming checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# LWC Chart and Visualization

Activate when building or reviewing a data visualization inside a Lightning Web Component: dashboards, record-page charts, drill-through widgets. LWC has no native chart primitive; the decision between Chart.js, D3, Plotly, and Salesforce's own charting components comes down to volume, interactivity, and theming.

## Before Starting

- **Quantify the data volume.** A 20-point pie chart and a 10,000-point time series have completely different implications.
- **Classify interactivity.** Static display, tooltip-on-hover, drill-through, brush / pan / zoom — each ratchets up library complexity.
- **Verify accessibility requirements.** Salesforce apps must meet accessibility guidelines; charts require screen-reader fallbacks and keyboard navigation.
- **Consider the alternative.** Sometimes a Lightning Table is the right answer — not every data display needs a chart.

## Core Concepts

### Static Resource + Chart library

The canonical pattern: bundle Chart.js / D3 / Plotly as a Static Resource, load via `loadScript`, render into a canvas or SVG element inside the LWC template.

### Lightning chart components

Salesforce ships limited charting primitives (e.g., Lightning charts in Experience Cloud, Report charts). Minimal customization; easy wins for standard use.

### Canvas vs SVG

Canvas (Chart.js, Plotly) scales to more data points; SVG (D3) is inspectable and accessible but slower past a few thousand elements.

### Data flow

Apex returns data → LWC passes to chart library → chart renders. For large datasets: preaggregate in Apex, paginate on demand, or stream via Platform Events for live dashboards.

### Accessibility patterns

Provide a hidden data table under the chart for screen readers; `aria-describedby` on the chart; ensure color choices meet contrast and are not the sole differentiator.

## Common Patterns

### Pattern: Chart.js with Static Resource + loadScript

`loadScript(this, chartJsStatic)` in connectedCallback, create Chart instance in renderedCallback once. Destroy on disconnectedCallback. Data binding via `chart.data.datasets[0].data = newData; chart.update()`.

### Pattern: D3 for bespoke visualization

Static Resource bundles D3. LWC renders an empty `<svg>`; in renderedCallback D3 selects it and draws. Use `this.template.querySelector` to get the SVG inside shadow DOM.

### Pattern: Preaggregated Apex + Chart.js for large datasets

Apex returns bucketed data (e.g., daily aggregates instead of row-level). Chart renders 365 points, not 300,000. SOQL aggregate + GROUP BY is your friend.

### Pattern: Streaming dashboard via Platform Events

Platform Event subscription in LWC pushes new datapoint → chart updates without reload. Works for live KPI displays.

## Decision Guidance

| Situation | Library | Reason |
|---|---|---|
| Standard bar/line/pie, <1k points | Chart.js | Easy, SLDS-friendly |
| Bespoke custom viz | D3 | Flexibility |
| Scientific / statistical plots | Plotly | Rich defaults |
| Reports-style chart on Experience Cloud | Lightning chart component | Native |
| 10k+ live points | Preaggregate + Chart.js canvas | Performance |
| Full interactivity (pan, zoom, brush) | D3 or Plotly | Feature coverage |

## Recommended Workflow

1. Quantify data volume, interactivity, accessibility, theming requirements.
2. Pick the library per decision guidance.
3. Bundle library as Static Resource; add licensing attribution if required.
4. Build a prototype LWC with the simplest chart; verify SLDS theme compatibility.
5. Measure render time with realistic data; optimize data pipeline first, rendering second.
6. Add accessibility layer: hidden data table, aria attributes, keyboard navigation.
7. Write jest tests mocking the library and asserting data transformation.

## Review Checklist

- [ ] Library choice matched to volume + interactivity
- [ ] Static Resource bundle updated and sized
- [ ] Chart destroyed on disconnectedCallback (no memory leak)
- [ ] Accessibility fallback (hidden table + aria) present
- [ ] SLDS theme compatibility verified
- [ ] Data pipeline efficient (aggregation where possible)
- [ ] jest test covers data-to-config transformation

## Salesforce-Specific Gotchas

1. **renderedCallback fires on every render, not once.** Chart libraries that are re-instantiated every render produce memory leaks and flicker — guard with a `this._chart` reference.
2. **Shadow DOM isolates CSS.** Chart.js tooltips and legends respect shadow DOM in Chart.js 3+; earlier versions had quirks.
3. **Static Resource cache.** Browser caches aggressively; when upgrading the library, version the Static Resource name or bust the cache explicitly.

## Output Artifacts

| Artifact | Description |
|---|---|
| Library decision record | Why Chart.js / D3 / Plotly |
| Static Resource bundle | Library + licensing attribution |
| Chart LWC template | JS / HTML / CSS with accessibility layer |
| Performance measurement | Render time vs data volume |

## Related Skills

- `lwc/lwc-performance-optimization` — render + reactive perf
- `lwc/lwc-web-components-interop` — third-party component integration
- `data/crm-analytics-foundation` — alternative analytics path
