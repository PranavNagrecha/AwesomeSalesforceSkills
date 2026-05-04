# Well-Architected Notes — Salesforce Maps Setup

## Relevant Pillars

- **Reliability** — Maps depends on background services (Geocoding, Routing, Live Tracking) that fail silently when address data is malformed. Reliable rollouts validate geocoding success rates in sandbox, build address-quality alerting, and gate go-live on a measured failure-rate threshold rather than "the package installed cleanly."
- **Operational Excellence** — Package install is one step; the program is the post-install configuration (geocode batches, real-time triggers, permission-set assignments, layer authoring, polygon imports). Treat each as its own change with a rollback path. Sandbox-first is the operational hallmark.
- **Performance** — Maps queries scale linearly with the number of plotted records and the polygon complexity. A `MapsLayer__c` with no filter against a 250k-Account org times out the Lightning Maps component. Filter scope and use saved list views as the layer source.

## Architectural Tradeoffs

- **Real-time vs batch geocoding.** Real-time gives reps immediate feedback ("the account I just created is on the map") but adds a synchronous callout per insert/update. In high-volume orgs, batch is safer for governor-limit headroom; real-time is mandatory for outside-sales personas where stale geocodes break the workflow. Per-object choice; not org-wide.
- **Polygon vs ZIP territories.** Polygons handle custom boundaries (e.g., "the eastern half of New Jersey except the Trenton corridor") but the polygon data is package-internal and hard to export to Tableau or other BI. ZIP territories are simpler, fully queryable, but cannot model boundaries that don't align to ZIP3/ZIP5. Pick by reporting requirements, not by visual appeal.
- **Live Tracking ping interval.** Lower interval (e.g., 1 min) produces high-fidelity breadcrumb trails but generates 4× the data volume of a 5-min interval. Most use cases need only "approximate location every 15 min" — pick the longest interval that satisfies the actual operational question.
- **Maps vs FSL boundary.** Maps is for outside-sales / general field-rep coverage; FSL is for work-order dispatch to scheduled resources. Customers occasionally try to use Maps to dispatch service techs, which always ends in a re-architect to FSL. Honor the persona boundary up front.

## Anti-Patterns

1. **Installing in production before sandbox validation.** Geocode batches can run for hours; failure rates surprise everyone the first time. Validate in sandbox; promote to production only after measuring failure rate on real data.
2. **Skipping the permission-set assignment step.** Package install creates the permission sets but assigns them to no one. Reps log in to a missing Maps tab and the admin reports "the package didn't install correctly." It did; the runbook missed step 2.
3. **Conflating Maps and FSL territories in a unification effort.** Different object models, different licensing, different personas. Customers who try to merge them end up rebuilding both products' configurations.
4. **Enabling Live Tracking without HR/legal approval and an archival plan.** Privacy and storage are both binding constraints. Enabling live tracking org-wide without these is a compliance and platform-limit risk.

## Official Sources Used

- Salesforce Maps Implementation Guide (Help & Training) — https://help.salesforce.com/s/articleView?id=sf.maps_implementation_overview.htm — used for package install order, base data services, and Geocoding configuration mechanics
- Salesforce Maps Object Reference (managed-package documentation) — https://help.salesforce.com/s/articleView?id=sf.maps_objects.htm — used for `MapsTerritoryPlan__c`, `MapsTerritory__c`, `MapsLayer__c`, `MapsLayerProperty__c`, `MapsAdvancedRoute__c` semantics
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html — used for the live-tracking volume / archival pattern (Big Object archival as the canonical pattern for high-volume telemetry)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — used for the Reliability / Operational Excellence framing of sandbox-first, gated rollout
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm — used for the export-to-Tableau pattern in Gotcha 6 (REST is the export pipeline mechanism)
