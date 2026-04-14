# Well-Architected Notes — Embedded Analytics Architecture

## Relevant Pillars

- **Performance** — Embedded dashboards add page load weight; lazy loading and pre-filtering strategies are required for pages with multiple embedded dashboards.
- **Reliability** — Hard-coded dashboardDevName values create fragile deployments that break silently on rename; runtime resolution via Custom Metadata is required for production-grade architectures.
- **Security** — Guest User access to embedded analytics requires explicit permission configuration; dashboards shared to public sites expose all embedded data to unauthenticated users if sharing is not correctly scoped.
- **Operational Excellence** — Dashboard state architecture (how filters are applied and propagated) must be documented before development; undocumented state management creates maintenance debt.
- **Scalability** — Cross-dashboard context propagation via getState/setState is more scalable than full page re-renders for complex multi-dashboard pages.

## Architectural Tradeoffs

**LWC state vs Aura filter:** The LWC `wave-wave-dashboard` component's `state` attribute replaces the full dashboard state (all filters reset). The Aura `wave:waveDashboard` `filter` attribute adds incremental selections to existing state. For record-context pages, the LWC state approach is correct. For Visualforce, Aura is required.

**Eager vs lazy dashboard loading:** Embedding multiple dashboards on one page with eager loading causes significant page load delay (each dashboard makes multiple API calls on load). Lazy loading (load on scroll or user action) is required for pages with 2+ embedded dashboards.

**dashboardId vs dashboardDevName:** `dashboardId` (18-char 0FK) is stable within an org but breaks on metadata promotion. `dashboardDevName` is portable across environments but must be managed to avoid renames. Architecture should use `dashboardDevName` with a runtime resolution mechanism.

## Anti-Patterns

1. **Using `filter` attribute on LWC component** — The `filter` attribute is a legacy Aura property; using it on the LWC `wave-wave-dashboard` silently produces no effect. All filtering must use the `state` attribute with Filter and Selection Syntax JSON.

2. **Hard-coded dashboardDevName in component markup** — Hard-coded dev names break when dashboards are renamed or when different environments use different dashboard names. Store dev names in Custom Metadata and resolve at runtime.

3. **No Experience Cloud permission audit for embedded analytics** — Embedding a dashboard on an Experience Cloud page without confirming guest user analytics permissions results in either a blank component (permission denied, no error) or unauthorized data exposure.

## Official Sources Used

- Analytics Dashboard Component Developer Guide — LWC Attributes — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_ext_data.meta/bi_dev_guide_ext_data/bi_api_embed_dashboard_lwc.htm
- Aura Component for Analytics Dashboards — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_ext_data.meta/bi_dev_guide_ext_data/bi_api_embed_dashboard_aura.htm
- Filter and Selection Syntax for Embedded Dashboards — https://help.salesforce.com/s/articleView?id=sf.bi_embed_filter_selection_syntax.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `admin/analytics-requirements-gathering` — upstream requirements skill
- `admin/analytics-kpi-definition` — KPI definition before dashboard design
