# Well-Architected Notes — CRM Analytics App Creation

## Relevant Pillars

- **Security** — CRM Analytics has three independent security layers (permission set, app sharing, row-level predicate) none of which inherit from Salesforce OWD. All three must be explicitly configured. Skipping the row-level security predicate gives all app Viewers access to all dataset rows regardless of Salesforce object-level sharing.
- **Performance** — Dataset refresh schedules and recipe/dataflow run times directly affect how current the data is and how long dashboard loads take. Large datasets with no column pruning or excessive row counts slow query times. Use aggregation in recipes rather than pushing raw row-level data to lenses. Index dataset dimensions used frequently in dashboard filters.
- **Operational Excellence** — Scheduling dataset refresh (recipe/dataflow) after each data sync and monitoring for failed refresh jobs prevents stale data from silently persisting in dashboards. Prune unused template app assets to reduce scheduler load.

## Architectural Tradeoffs

**Template app vs. blank app:** Template apps provide pre-built datasets and dashboards for common use cases (Sales, Service) but include unused assets that consume dataflow/recipe run quota. Blank apps require more initial setup but produce a leaner, purpose-built analytics solution. For proof-of-concept or standard use cases, templates are faster; for custom or complex reporting, blank apps with hand-crafted recipes are more maintainable.

**Recipe vs. dataflow:** Data Prep recipes are admin-friendly with a visual canvas but have fewer node types than dataflows. Dataflows (JSON) support more transformation types and are required for complex multi-object joins or computeRelative expressions. Recipes are the preferred starting point; escalate to dataflows only when recipes cannot achieve the required transformation.

## Anti-Patterns

1. **Stopping at permission set assignment** — Granting a CRM Analytics permission set without also configuring app sharing and row-level security produces blank apps from the user's perspective. All three security layers must be configured.

2. **Using connected objects as datasets** — Connecting Data Sync to a Salesforce object produces a connected object (staging replica), not a dataset. Attempting to create a lens or dashboard step directly on a connected object fails. Connected objects must be materialized into a registered dataset via a recipe or dataflow.

3. **Relying on faceting for cross-dataset filtering** — Building dashboards that mix datasets and expecting faceting to propagate filters across them. Faceting is dataset-scoped. Cross-dataset filtering requires bindings.

## Official Sources Used

- CRM Analytics REST API Developer Guide Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Trailhead Quick Start: Create an App and a Lens — https://trailhead.salesforce.com/content/learn/projects/quickstart-analytics-studio
- Connect and Sync Your Data to CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_connecting_to_salesforce.htm&type=5
- Add Row-Level Security with a Security Predicate — https://help.salesforce.com/s/articleView?id=sf.bi_security_dataset_predicate.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
