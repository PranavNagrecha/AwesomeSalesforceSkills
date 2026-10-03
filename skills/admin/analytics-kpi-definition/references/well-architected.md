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

Read for this revision (2026-10-03):

- Analytics SAQL Developer Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_saql.pdf. Basic Elements (case-sensitive identifiers and keywords), Comparison Operators (case-sensitive `==`, `matches`), cogroup (inner, left, right, full; quota attainment example with `coalesce()`), Aggregate Functions (`avg()`, `sum()`, `count()`, `unique()`), String Functions (`lower()`), SAQL Null Measures and Dimensions.
- Analytics Dashboard JSON Developer Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_json.pdf. `measureField` formulas and the unique-count behaviour of dimension counts.
- Analytics Platform Setup Guide (Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf. Dataset Field Limits (precision and overflow), Trending Data Limits, Localization and Internationalization (currency).
- Analytics External Data API Developer Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_ext_data.pdf. Metadata JSON example and field keys, CSV format, `InsightsExternalData.Operation` values.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. AnalyticsSettings (`enableWaveCustomFiscal`, `enableWaveMulticurrency`).
- Einstein Discovery REST API Developer Guide (Spring '26), local corpus: `knowledge/imports/bi-dev-guide-rest-sdd.md`. Searched for fill-rate rules; none found.

Listed in the original version and not re-read:

- Salesforce Help: Calculate Key Performance Indicators Using CRM Analytics, https://help.salesforce.com/s/articleView?id=sf.bi_kpis.htm (Salesforce Help does not fetch).
- CRM Analytics Design Principles, https://trailhead.salesforce.com/ (page retired).
- Salesforce Well-Architected Overview, https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `admin/analytics-requirements-gathering` — upstream requirements skill that should complete before KPI definition
- `admin/saql-query-development` — downstream implementation skill using formulas from KPI register
