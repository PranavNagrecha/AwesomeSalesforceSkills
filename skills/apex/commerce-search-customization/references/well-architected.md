# Well-Architected Notes — Commerce Search Customization

## Relevant Pillars

- **Performance** — Search index configuration directly determines query latency and relevance. Poorly prioritized searchable attributes cause the search engine to score irrelevant fields equally with high-signal fields like product name and description, degrading result quality and increasing sort overhead. Sort rules evaluated server-side are more efficient than client-side result re-ordering, which degrades on paginated result sets. Rebuild scheduling must account for catalog size — large catalogs with tens of thousands of SKUs can have multi-minute rebuild windows that affect live storefront behavior if triggered during peak hours.

- **Security** — BuyerGroup entitlement enforcement is a security control, not a UI feature. Entitlement policy gaps that cause silent product omissions represent a data access failure: products that should be restricted to specific buyer groups may become visible if entitlement policies are misconfigured in the other direction. Entitlement must be audited after any BuyerGroup structural change. The 2,000 BuyerGroup-per-product cap on entitlement policies means that overly broad entitlement designs can create both security gaps (products disappear for buyers who should see them) and access control complexity.

- **Reliability** — The 60 rebuild/hour cap creates a reliability risk for CI/CD pipelines and active development workflows. A deployment that requires more rebuilds than the remaining hourly budget will fail silently — the deployment appears to succeed (configuration POSTed successfully), but the storefront index is not updated. Reliable deployment patterns must batch configuration changes and treat the rebuild as a single, final pipeline step with budget verification.

- **Operational Excellence** — Commerce search configuration is invisible in standard Salesforce Setup UI. There is no declarative admin panel for searchable attributes, facetable attributes, or sort rules — all configuration is managed via Connect REST APIs. This creates an operational gap: the current index configuration is not auditable through standard admin tooling. Teams must maintain external documentation or a configuration-as-code approach (checked-in JSON payloads for each storefront) to track and reproduce the current search configuration state.

## Architectural Tradeoffs

**Facet granularity vs. rebuild frequency:** Adding more product attributes as facetable fields improves buyer filtering options but increases the rebuild time for large catalogs. Each additional facetable attribute requires the indexer to compute aggregated value counts across all products. Teams should prioritize facets by buyer usage data rather than adding all available fields speculatively.

**Rebuild scheduling in CI/CD vs. live environment:** Triggering search index rebuilds as part of every deployment pipeline is operationally clean but can exhaust the 60-rebuild/hour budget on active development days. Teams should weigh the tradeoff between deployment automation purity and rebuild budget conservation. A practical pattern is to gate rebuild triggers on a deployment environment variable so rebuilds run automatically in production but are manually triggered in sandbox.

**Entitlement policy breadth vs. per-product BuyerGroup count:** Assigning products to many BuyerGroups through broad entitlement policies is operationally simple but scales toward the 2,000 BuyerGroup-per-product hard limit. Teams with large B2B catalogs should model entitlement policy groupings to keep per-product BuyerGroup counts well below the limit, using hierarchical grouping patterns (e.g., grouping dealers by region into a single BuyerGroup) rather than individual buyer-level assignments.

## Anti-Patterns

1. **Managing search configuration without version control** — Because Commerce search configuration is API-only with no Setup UI, teams that do not check in their index configuration payloads have no way to audit what changed, roll back a bad configuration, or reproduce the configuration in a new sandbox. Every `POST /commerce/webstores/{webstoreId}/search/indexes` payload should be stored in source control alongside the metadata deployment it accompanies. This is especially critical because a misconfigured POST can silently erase existing attribute sets.

2. **Triggering a rebuild without verifying entitlement policy first** — When diagnosing missing products, many teams reflexively trigger an index rebuild assuming the index is stale. If the root cause is an entitlement policy gap (the most common cause), the rebuild wastes precious hourly rebuild budget without fixing the problem. Always audit entitlement policy assignment before triggering a rebuild in response to a missing-product report.

3. **Enabling Einstein recommendations before Activity Tracking instrumentation** — Deploying recommendation components to the storefront before the Activity Tracking API is instrumented and has collected sufficient data results in empty recommendation slots that erode buyer trust in the storefront. Recommendation enablement should be gated behind an explicit Activity Tracking readiness check, with a data collection period of at least 2–4 weeks of live buyer traffic before recommendations are surfaced.

## Official Sources Used

- B2B Commerce Search Settings APIs — Salesforce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_commerce_search.htm
- Commerce Einstein APIs — Salesforce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_commerce_einstein.htm
- Adjust Criteria for Ranking Storefront Search Results — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.comm_search_ranking.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B and D2C Commerce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_dev.htm
