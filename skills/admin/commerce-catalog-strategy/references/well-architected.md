# Well-Architected Notes — Commerce Catalog Strategy

## Relevant Pillars

### Performance

The 50 searchable field limit directly governs search index rebuild performance and ongoing query performance. A catalog designed without this constraint produces an index that silently degrades — rebuild jobs stall, incremental updates stop propagating, and search latency increases as the platform attempts to process over-limit configurations. Attribute classification (searchable vs. filterable vs. display-only) is a performance architecture decision, not a data modeling decision.

Full-token-only search also has performance implications: if buyers resort to browsing instead of searching because search does not return useful results, page load patterns shift toward category browsing with deeper pagination, increasing backend query load on category-product join queries.

### Scalability

Taxonomy depth and breadth decisions determine the scalability of the catalog over the product lifecycle. A flat taxonomy (too few categories) forces more products into each category, degrading faceted navigation response time as product counts per category grow. A taxonomy that is too deep (5+ levels) requires more storefront catalog maintenance as the product line evolves and creates navigation complexity that increases with catalog size.

Multi-storefront architectures scale more predictably when the product catalog is designed for system-of-record stability and storefront catalogs are treated as lightweight views. This separation means a growing product catalog does not force storefront navigation redesigns.

### Operational Excellence

The separation between product catalog taxonomy (system-of-record) and storefront catalog (navigation view) is the primary operational excellence concern in this domain. Teams that conflate the two create maintenance burdens where every product catalog change requires coordinated storefront navigation updates, increasing change risk and deployment complexity.

Attribute classification documentation (the output of this skill) is an operational artifact. Without it, teams accumulate searchable fields incrementally until the limit is reached, at which point remediation requires bulk data changes and re-indexing — an operationally expensive recovery.

### Security

Product catalog visibility is not scoped by default. Any product in the product catalog is technically reachable from any storefront until explicitly restricted through entitlement policies. Catalog strategy must include a visibility and entitlement design step so that product-storefront isolation requirements are addressed before configuration begins, not discovered during UAT.

For B2B Commerce, account-level product visibility (account entitlement policies, buyer group assignments) is a catalog strategy concern — which products are visible to which buyer segments — not only a configuration concern.

### Reliability

Search index reliability depends on the catalog staying within the 50-field searchable limit. Because the failure mode is silent (job completes with success status, results degrade without error), a catalog that drifts over the limit will produce unreliable search results that are difficult to diagnose. Designing to a conservative internal limit (≤45 searchable fields) and enforcing that limit through the attribute classification governance process improves search reliability over the catalog lifecycle.

---

## Architectural Tradeoffs

**Taxonomy stability vs. storefront flexibility:** A stable product catalog taxonomy (optimized for system-of-record integrity) provides a reliable foundation for storefront catalogs but may not align with how buyers conceptualize navigation. Storefront catalogs provide flexibility to present buyer-facing vocabulary and structures without touching the product catalog, but they require explicit maintenance. The tradeoff is additional storefront catalog maintenance overhead in exchange for product catalog stability.

**Searchable field depth vs. search accuracy:** Maximizing the number of searchable fields improves the chance that any buyer search term matches a product, but pushes the catalog closer to the 50-field limit. Being selective about searchable fields reduces discovery surface but keeps the catalog far from the limit and reduces index rebuild time.

**Flat taxonomy vs. deep taxonomy:** A flatter taxonomy is easier to maintain and keeps storefront navigation shallow, but puts more products per category which increases faceted filter response time. A deeper taxonomy organizes products more precisely but increases maintenance burden and navigation depth.

---

## Anti-Patterns

1. **Designing one taxonomy to serve both product catalog and storefront navigation** — Attempting to build a single category hierarchy that works as both the system-of-record product taxonomy and the buyer-facing navigation structure produces a hierarchy optimized for neither. Product catalog categories are reorganized when buyer navigation needs change (and vice versa), creating perpetual taxonomy instability. Correct approach: design the product catalog taxonomy for system-of-record longevity; design the storefront catalog independently as a buyer-facing view.

2. **Deferring attribute classification until post-migration** — Importing products without first classifying attributes as searchable / filterable / display-only allows searchable field count to accumulate unchecked. The platform does not warn at import time — the failure surfaces at the first index rebuild after the limit is exceeded. At that point, remediation requires bulk field updates across thousands of product records and a full re-index. Correct approach: classify attributes before the first product is imported.

3. **Assuming product visibility is scoped to storefront catalog membership** — Omitting a product from a storefront catalog does not restrict buyer access to that product through direct URL or API. Entitlement policies must be explicitly designed and configured. Treating catalog strategy as only a navigation design problem, without addressing visibility and entitlement requirements, creates security gaps in multi-storefront and B2B deployments.

---

## Official Sources Used

- B2C Commerce Catalogs and Navigation (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/cc-digital-merchandising/cc-digital-merchandising-catalogs
- Optimize Your Online Store for Search (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/b2c-commerce-search-and-einstein/b2c-commerce-search-optimize-your-store
- Product Attributes Data Model — B2B Commerce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_comm_dev.meta/b2b_comm_dev/b2b_comm_dev_product_attributes_data_model.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B Commerce Developer Guide (Salesforce Help) — https://developer.salesforce.com/docs/atlas.en-us.b2b_comm_dev.meta/b2b_comm_dev/b2b_comm_dev_intro.htm
