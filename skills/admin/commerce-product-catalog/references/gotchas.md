# Gotchas — Commerce Product Catalog

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: One Catalog Per Store Is a Hard Platform Constraint

**What happens:** A `WebStore` can be linked to exactly one `ProductCatalog` via the `WebStoreCatalog` junction object. Attempting to insert a second `WebStoreCatalog` record for the same store triggers a validation error and the insert is rejected.

**When it occurs:** Practitioners try to model buyer-tier segmentation by associating multiple catalogs to a single store (e.g., one catalog for standard buyers, one for premium buyers). This pattern works in some e-commerce platforms but is not supported in Salesforce B2B Commerce.

**How to avoid:** Design buyer-tier segmentation using `CommerceEntitlementPolicy` records — not separate catalogs. All buyers on a store share the same `ProductCatalog` and `ProductCategory` hierarchy. Entitlement policies control which individual products each buyer group can see. If two stores genuinely need completely separate product sets with no overlap, use two separate stores each with their own catalog.

---

## Gotcha 2: The 2,000 Buyer Group Cap Is Silent and Produces No Error

**What happens:** Salesforce B2B Commerce limits the number of buyer groups (via `CommerceEntitlementPolicy`) that a single product can belong to for search indexing purposes to 2,000. If a product is added to more than 2,000 buyer groups, the excess buyer groups' members silently cannot discover the product through storefront search. The product is still accessible via direct URL or category browsing, but it does not appear in search results.

**When it occurs:** Large catalogs with many buyer segments — common in distributor or wholesale commerce implementations — can cross this threshold when a product (like a best-selling SKU) is included in nearly every entitlement policy. There is no validation error, no failed DML, no platform notification, and no search error log entry.

**How to avoid:** Monitor buyer group assignments per product as the entitlement model grows. Query `CommerceEntitlementProduct` grouped by `ProductId` and count distinct linked policies. If a product is approaching 2,000 buyer group assignments, consider consolidating buyer groups using the broadest-common-entitlement pattern — where a base "All Buyers" policy covers shared products, and overlay policies handle exceptions.

---

## Gotcha 3: Search Index Does Not Rebuild Automatically After Catalog or Entitlement Changes

**What happens:** Adding a product to a `ProductCategory`, creating a new `CommerceEntitlementProduct`, or activating a `Product2` record does not trigger any automatic search reindex. Buyers searching the storefront continue to see the previous index state until an admin manually initiates a rebuild.

**When it occurs:** Every catalog or entitlement change requires a manual index rebuild. This surprises teams that expect near-real-time propagation analogous to other Salesforce platform features.

**How to avoid:** After any catalog configuration change (category assignments, entitlement records, product activation/deactivation), navigate to Setup > B2B Commerce > [Store Name] > Search Index and initiate a rebuild. In automated deployment pipelines, include a post-deploy step to trigger a search index rebuild via the Commerce REST API (`POST /webstores/{webStoreId}/search/indexes`). Monitor index job status before declaring a deployment complete.

---

## Gotcha 4: Category Assignment Does Not Grant Buyer Access — Entitlement Does

**What happens:** A product assigned to a `ProductCategory` via `ProductCategoryProduct` appears correctly in the Commerce admin product list and category view. However, a buyer who browses that category on the storefront will not see the product unless the product is also included in the buyer's active `CommerceEntitlementPolicy` via a `CommerceEntitlementProduct` record.

**When it occurs:** Admins new to B2B Commerce often treat category assignment as the sole visibility mechanism — they add a product to a category and expect buyers to see it. The category is the organizational structure; the entitlement policy is the access control layer. Both must be configured independently.

**How to avoid:** Always complete two steps: (1) assign the product to a category, and (2) add the product to the relevant entitlement policy. After both steps, rebuild the search index. Verify buyer access by logging in as a buyer user in the expected buyer group.

---

## Gotcha 5: Variant Parent Must Have an Attribute Set Before Children Can Be Created

**What happens:** Attempting to create a child variant `Product2` record (with `VariantParentId` set) before the parent `Product2` has a valid `ProductAttributeSet` assigned results in a validation error. The error message in the UI is sometimes generic and does not clearly identify that the missing attribute set on the parent is the cause.

**When it occurs:** Practitioners build parent products first and plan to add attribute configuration later, then try to create variant records ahead of attribute set setup — a common data migration or scripted insert ordering mistake.

**How to avoid:** Always follow this creation order: (1) create `ProductAttributeSet`, (2) create `ProductAttribute` records, (3) assign the attribute set to the parent `Product2`, (4) create child variant `Product2` records with `VariantParentId`. In data migrations, enforce this ordering in load scripts rather than relying on the platform to handle out-of-order inserts gracefully.

---

## Gotcha 6: Deactivating a Product Does Not Remove It from Entitlement Policies or Category Assignments

**What happens:** Setting `IsActive = false` on a `Product2` removes it from buyer-facing storefront browsing and ordering (after the next index rebuild), but the `ProductCategoryProduct` and `CommerceEntitlementProduct` junction records remain in place. If the product is later reactivated, it immediately regains full catalog and entitlement visibility (again, after a rebuild) without any additional configuration work.

**When it occurs:** Catalog managers who deactivate products for seasonal holds or stock-outs may not expect that the associated entitlement and category records are preserved. This can cause confusion when diagnosing catalog configurations — a product appears in category and entitlement query results even when it is inactive.

**How to avoid:** When performing a deactivation audit, query `Product2` with `IsActive = false` cross-referenced against `ProductCategoryProduct` and `CommerceEntitlementProduct`. For permanently discontinued products, explicitly delete the junction records. For temporary deactivations, leaving junction records in place is intentional — it preserves configuration for reactivation without manual re-setup.
