# Well-Architected Notes — CRM Analytics Dashboard JSON

## Relevant Pillars

### Performance

Dashboard JSON editing directly governs query performance. SAQL step limits, query complexity, and the number of steps in a dashboard all affect render time. Steps with limits at or near 10,000 rows impose higher compute cost than steps bounded to what the widget actually needs. Poorly structured SAQL (e.g., ungrouped loads, missing projections, overly broad filters) causes slow step execution. The Well-Architected Performance pillar applies directly: right-size step limits for each widget's actual data needs rather than defaulting to the maximum.

### Reliability

Dashboard reliability depends on portable dataset references. Dashboards that reference datasets by display name instead of `datasetId`/`datasetVersionId` are unreliable across orgs and sandbox refreshes — they silently return empty data rather than failing with an observable error. Reliable dashboards use ID-based references, have explicit row limits to prevent silent truncation, and handle the empty-binding case explicitly so user-facing data is always deterministic.

### Operational Excellence

The REST API's History API provides automatic version snapshots on every PUT. This enables rollback and audit, which are core Operational Excellence capabilities. Treating dashboard JSON as a version-controlled artifact — retrieving via GET, editing, and PUTting the full body — aligns with the Operational Excellence principle of treating infrastructure as code. CI/CD pipelines that PUT dashboard JSON programmatically should record PUT response metadata (id, lastModifiedDate) to an external change log.

## Architectural Tradeoffs

**Step count vs. widget count:** Every step in a dashboard runs at render time regardless of whether a widget is visible. A dashboard with many steps and few visible widgets wastes compute. Prefer fewer, broader steps with widget-level filtering over many narrow steps when the data volume allows.

**Row limit vs. render time:** Increasing a step's `limit` from 2,000 to 10,000 rows increases the data transferred and rendered. For summary charts, 2,000 rows is usually sufficient and faster. For detailed tables or export widgets, the higher limit is necessary. Apply higher limits only to steps that need them.

**Binding complexity vs. debuggability:** Deep binding chains (a widget binding to a step that is itself filtered by another binding) are hard to debug because empty-string propagation is silent. Prefer shallow binding trees (one level of selection driving one or two downstream steps) unless the use case requires otherwise.

## Anti-Patterns

1. **Dataset name references in SAQL steps** — Using the human-readable dataset name as the dataset identifier in the `datasets` array or in the SAQL `load` statement produces dashboards that appear to work in the authoring org but fail silently in any other org. Always use `datasetId` and `datasetVersionId` obtained from the Datasets API. This is both a reliability and operational excellence failure.

2. **Partial PUT of dashboard JSON** — Constructing a PUT payload from a subset of the dashboard body (e.g., only the modified step or widget) silently removes all other dashboard elements. Reliable JSON editing always follows the GET-modify-PUT full-body cycle.

3. **Unhandled empty binding state** — Bindings that can return empty strings (because no user selection is active) produce unpredictable SAQL behavior depending on the filter construct used. Failing to test and handle the empty-binding case is an operational reliability gap that manifests as either full-population data leakage or zero-row charts on first load.

## Official Sources Used

- CRM Analytics Dashboard JSON Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_json.meta/bi_dev_guide_json/bi_dbjson_intro.htm
- CRM Analytics Bindings Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_bindings.meta/bi_dev_guide_bindings/bi_bindings_overview.htm
- CRM Analytics REST API Developer Guide (Dashboards resource) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_dashboards.htm
- CRM Analytics REST API Developer Guide (Dashboard Histories resource) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_dashboard_histories.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
