# Well-Architected Notes — CRM Analytics Dashboard Design

## Relevant Pillars

- **Operational Excellence** — Naming steps descriptively, documenting binding logic in dashboard JSON comments, and explicitly configuring mobile layout reduces maintenance burden when the dashboard is handed off or updated by a different admin.
- **Reliability** — The columnMap fix (replacing static `columnMap` with `"columns": []`) is a correctness requirement for any dashboard that uses dynamic bindings. Missing this fix produces silently incorrect charts — a reliability failure that erodes user trust in analytics data.

## Architectural Tradeoffs

**Faceting vs. bindings:** Faceting is simpler and requires no JSON editing but is limited to single-dataset scenarios. Bindings are more powerful and cross-dataset capable but require JSON editing and careful columnMap management. Design dashboards around a single-dataset where possible to minimize binding complexity. Only introduce bindings when cross-dataset filtering is a genuine requirement.

**Dataset join vs. dashboard binding:** Joining two datasets at the dataflow/recipe level and building a single-dataset dashboard (using faceting) is more performant and simpler than maintaining two separate datasets with binding-based cross-filtering. When datasets are joined in the ETL layer, dashboard logic is simpler. The tradeoff: dataset refresh is heavier; if the datasets have very different refresh schedules, joining them at the ETL level forces both to share one cadence.

## Anti-Patterns

1. **Leaving columnMap static with dynamic bindings** — Any dashboard that uses a binding to change a chart's measure or grouping without updating `columnMap` to `"columns": []` silently renders wrong data. This is the highest-frequency invisible bug in CRM Analytics dashboards.

2. **Using faceting for cross-dataset filtering** — Enabling faceting and expecting it to filter widgets on different datasets. Faceting is dataset-scoped. Cross-dataset filtering requires bindings.

3. **Skipping mobile layout configuration** — Building dashboards for mobile users without configuring the mobile canvas. Mobile users see a zoomed-out desktop layout that is unusable on phone screens.

## Official Sources Used

- CRM Analytics Interactions Developer Guide — Bindings — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_bindings.meta/bi_dev_guide_bindings/bi_bindings_overview.htm
- Visualize Data With Charts — CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_chart_types.htm&type=5
- Filter Dashboard Results with Faceting — https://help.salesforce.com/s/articleView?id=sf.bi_dashboard_filter_faceting.htm&type=5
- CRM Analytics REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
