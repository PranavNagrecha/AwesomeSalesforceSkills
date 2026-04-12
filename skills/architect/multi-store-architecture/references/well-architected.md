# Well-Architected Notes — Multi-Store Architecture

## Relevant Pillars

- **Adaptability** — Multi-store architecture is primarily an adaptability concern. The shared catalog pattern ensures that product data model changes, new attributes, and new SKUs propagate to all storefronts without per-store rework. Per-store entitlement policies and price books allow each store to adapt independently to regional pricing changes, regulatory requirements, or buyer segment shifts without affecting other stores. Avoid tightly coupling catalog structure to store structure; that coupling makes future regional expansion expensive.

- **Performance** — Shared catalogs reduce the indexing and cache invalidation surface. When a product is updated in one catalog, only one set of search indexes and product cache entries must be invalidated across all stores. Separate catalogs per store multiply cache complexity. For SFCC, the master catalog is the single source for product data that feeds all site indexes; keeping it authoritative avoids redundant indexing work.

- **Security** — Entitlement policies and buyer groups are the primary security controls for product and pricing isolation between stores. Sharing a product catalog does not share access — but only if entitlement policies are explicitly configured per store. The security risk of a shared catalog is that a misconfigured or missing entitlement policy can expose all catalog products to all stores. Store isolation must be validated end-to-end before go-live.

- **Scalability** — As the number of stores grows, the shared catalog pattern scales linearly: add a new WebStore, configure its buyer groups and entitlement, link to the shared catalog. The per-store catalog anti-pattern scales as O(stores × SKUs) for maintenance. Large catalogs (10,000+ SKUs) amplify this difference significantly.

- **Operational Excellence** — Multi-store architecture with shared catalogs centralizes product data governance. Product launches, attribute changes, and catalog restructures are single operations that propagate to all stores. Per-store catalogs fragment governance and create synchronization risk. Well-Architected operational excellence favors single sources of truth over synchronized copies.

---

## Architectural Tradeoffs

**Shared catalog vs. per-store catalog:**
- Shared catalog is the correct default for any multi-store architecture where stores sell overlapping or identical products. The maintenance and governance benefits dominate.
- Separate catalogs are justified only when product universes are genuinely disjoint and the brands or business units have independent product governance processes.

**Multiple WebStores vs. entitlement segmentation within one store:**
- Multiple WebStores are appropriate when stores have distinct regional branding, separate URLs, different currencies, different default languages, or different buyer audiences requiring separate session contexts.
- Entitlement segmentation within one store is appropriate when the only differentiation is product visibility or pricing tier for different buyer groups accessing the same branded storefront.

**Currency enablement timing:**
- Enabling multi-currency early (before any commerce data) has near-zero cost and eliminates the risk of a painful retroactive migration. This is a clear Well-Architected decision: accept minor upfront configuration cost to avoid significant future rework.

**SFCC same-realm vs. multi-realm:**
- Same-realm multi-site shares a master catalog natively through Business Manager. Cross-realm architectures require explicit catalog syndication pipelines. Design for same-realm when possible; document cross-realm catalog sync requirements explicitly when they are unavoidable.

---

## Anti-Patterns

1. **Separate product catalog per regional store** — Creates O(stores × SKUs) maintenance overhead. Every product change must be replicated across all regional catalogs. Use a shared product catalog with per-store entitlement policies instead. This pattern is documented extensively in the B2B Commerce Developer Guide catalog data model section.

2. **Currency toggle UI without cart recreation** — Building a currency switcher on a storefront that attempts to update the existing cart's currency mid-session violates the platform constraint that carts are currency-locked at creation. The result is a broken checkout experience where displayed prices and cart totals disagree. Correct pattern: scope cart to store currency, require store re-selection to change currency.

3. **Skipping entitlement configuration when sharing a catalog** — Linking a product catalog to multiple WebStore records without configuring entitlement policies per store can expose all products to all buyers across all stores. Shared catalog is not shared access restriction. Entitlement policies must be configured explicitly for each WebStore.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B Commerce Developer Guide — Product and Catalog Data Model — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_catalog_data_model.htm
- Support Multiple Currencies in a Commerce Store — https://help.salesforce.com/s/articleView?id=sf.comm_multiple_currencies.htm
- B2C Commerce Architecture and Localization — https://developer.salesforce.com/docs/commerce/sfcc/guide/b2c-localization.html
