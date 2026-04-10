# Well-Architected Notes — Commerce Product Catalog

## Relevant Pillars

- **Security** — Buyer product visibility is access-controlled through `CommerceEntitlementPolicy`. The policy model enforces that buyers can only see products explicitly granted to their buyer group. Misconfigured or missing entitlement records create security surface area — a product not in a buyer's policy is not returned by the Commerce API or search index for that buyer. Follow least-privilege principles: grant entitlement explicitly rather than using broad "all products" policies unless the store genuinely has no segmentation need.

- **Performance** — Catalog depth, category count, and entitlement policy complexity all affect search index rebuild time and storefront page-load performance. Deep category hierarchies (4+ levels) and very large `ProductCategoryProduct` datasets slow storefront navigation rendering. Large `CommerceEntitlementProduct` datasets with many buyer groups per product increase index build duration and can push products beyond the 2,000-group search cap. Keep hierarchy depth at 2–3 levels maximum and monitor entitlement record volume.

- **Scalability** — The 2,000 buyer group limit per product is the primary scaling constraint in entitlement-heavy implementations. Design entitlement models to consolidate buyer groups wherever possible — use a "base policy" for broadly available products and overlay policies for restricted products — rather than granting each product individually to every buyer group. Catalog record volume (ProductCategoryProduct and CommerceEntitlementProduct) scales linearly with SKU and policy count; plan for periodic archive or cleanup of discontinued product assignments.

- **Reliability** — The search index is the most fragile component of the catalog delivery chain. It is an async, rebuilt artifact and is not immediately consistent with DML changes. Deployments that modify catalog or entitlement configuration without a post-deploy index rebuild leave buyers in a degraded state. Establish a deployment checklist that includes index rebuild as a mandatory post-step. Monitor index build job completion via the Commerce admin or the REST API before marking a release done.

- **Operational Excellence** — Category hierarchy and entitlement policy design should be documented explicitly (not just implied by the data model) so that catalog administrators can maintain them without needing to query junction tables. Use descriptive `Name` fields on `ProductCategory`, `CommerceEntitlementPolicy`, and `BuyerGroup` records. Avoid policy proliferation — consolidate buyer groups when business rules are identical to reduce ongoing maintenance surface.

## Architectural Tradeoffs

**Single catalog vs. multiple stores for segmentation:** Using one catalog with multiple entitlement policies is the recommended pattern for buyer segmentation within a single commerce experience. It minimizes admin overhead and keeps the category hierarchy consistent. However, if two buyer populations genuinely need completely different storefronts (different branding, different flows, different currency), separate stores (each with their own catalog) are appropriate. The tradeoff is operational complexity — each store requires its own category maintenance and index rebuild schedule.

**Flat vs. hierarchical category structure:** Flat hierarchies are operationally simpler and faster to render on the storefront. Deep hierarchies (3+ levels) support complex taxonomies common in industrial or technical product catalogs but require more careful management — adding a product to the wrong level of the hierarchy is a common operational error, and category pages at deeper levels often have lower buyer traffic.

**Explicit entitlement per product vs. catalog-level policies:** Commerce requires per-product entitlement grants via `CommerceEntitlementProduct`. There is no "grant all products in a category" mechanism — each product must be explicitly listed. This is precise but creates high record volume for large catalogs with many buyer groups. The operational tradeoff: precision vs. maintenance burden. For large catalogs, scripted or automated entitlement management (e.g., Apex batch or Data Loader templates) is necessary.

## Anti-Patterns

1. **Using separate catalogs for buyer-tier segmentation within one store** — The platform enforces one catalog per store. Attempting this results in insert failures and architectural confusion. Use entitlement policies for segmentation; use separate stores only when storefront experiences genuinely diverge.

2. **Relying on category assignment alone for buyer visibility** — Category assignment is organizational structure, not access control. A product in a category with no entitlement policy coverage is invisible to buyers on the storefront. Always pair category assignment with explicit entitlement configuration.

3. **Skipping search index rebuild after catalog changes** — Catalog and entitlement DML does not propagate to the search index automatically. Skipping the rebuild leaves buyers in a stale state and produces hard-to-diagnose "product exists but can't be found" support tickets.

4. **Creating variant child products before attribute set configuration** — Out-of-order creation results in validation errors and partially created records that can be difficult to clean up. Always configure the attribute set on the parent product first.

5. **Ignoring the 2,000 buyer group cap** — In large wholesale implementations, this cap is a real operational risk. Monitoring should be established early, before the catalog grows to the point where products silently fall out of search results.

## Official Sources Used

- Product and Catalog Data Model — B2B Commerce Developer Guide: https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/products-and-catalog.html
- Entitlement Data Limits — B2B Commerce Developer Guide: https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/b2b-data-limits.html
- Product Variations and Attributes — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.comm_product_variations.htm
- Commerce Product and Category APIs — B2B Commerce Developer Guide: https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/product-category-api.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — CommerceEntitlementPolicy: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_commerceentitlementpolicy.htm
- Object Reference — ProductCatalog: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_productcatalog.htm
- Object Reference — ProductCategory: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_productcategory.htm
- Object Reference — WebStoreCatalog: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_webstorecatalog.htm
