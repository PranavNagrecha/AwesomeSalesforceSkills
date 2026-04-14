# Well-Architected Notes — Analytics KPI Definition

## Relevant Pillars

- **Reliability** — A signed KPI register prevents formula disputes from invalidating delivered dashboards; KPI definitions that were built without stakeholder sign-off are frequently rejected and rebuilt at cost.
- **Operational Excellence** — The KPI register is the living documentation for all analytics metric definitions; without it, every future dashboard rebuild requires re-discovery of formulas that were never written down.
- **Security** — KPI definitions that use Opportunity or financial data must note data access and row-level security requirements; a KPI accessible to all users when it should be restricted by role hierarchy is a security misconfiguration.
- **Performance** — SAQL queries that aggregate over large datasets without proper filters are a performance risk; KPI formulas should specify filter criteria to limit dataset scan scope.
- **Scalability** — Target datasets must be designed for the reporting period cadence; a targets dataset that must be fully rebuilt for each update does not scale to long reporting histories.

## Architectural Tradeoffs

**Inline calculation vs recipe pre-aggregation:** KPI formulas can be applied at query time in SAQL (flexible but repeated per lens) or pre-aggregated in the dataset recipe (faster for fixed KPIs, less flexible). For KPIs that are queried frequently, recipe pre-aggregation is the better choice. For KPIs that vary by user-selected dimensions, SAQL query-time calculation is required.

**Fixed targets vs dimension-specific targets:** Fixed targets (one target value for the whole org) can be hardcoded in SAQL. Dimension-specific targets (targets per Owner, Region, Quarter) require a separate targets dataset joined at query time. The design choice affects how targets are maintained and updated.

## Anti-Patterns

1. **Building lenses before KPI register sign-off** — Building CRM Analytics lenses before stakeholders agree on metric formulas leads to mid-project formula changes that require complete lens rebuilds. The KPI register must be signed off before development.

2. **Storing targets inline in actuals dataset** — Adding target value columns to the actuals dataset instead of a separate targets dataset creates data model debt. Updates to targets require re-running the full actuals recipe. Separate targets datasets are the correct pattern.

3. **Confusing KPI definition with dashboard tile configuration** — KPI definition is a pre-build BA task (formula, dimensions, targets). Dashboard tile configuration (widget type, color, layout) is a development task. These must not be conflated.

## Official Sources Used

- Calculate Key Performance Indicators Using CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_kpis.htm
- CRM Analytics Design Principles — https://trailhead.salesforce.com/content/learn/modules/wave_analytics_design_principles
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `admin/analytics-requirements-gathering` — upstream requirements skill that should complete before KPI definition
- `data/saql-query-development` — downstream implementation skill using formulas from KPI register
