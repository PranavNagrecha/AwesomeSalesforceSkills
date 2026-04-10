---
name: commerce-product-catalog
description: "Use when configuring or troubleshooting the B2B/B2C Commerce product catalog — ProductCatalog, ProductCategory, ProductCategoryProduct, WebStoreCatalog, CommerceEntitlementPolicy, product attributes, and product variants. Trigger keywords: product catalog, product category, commerce catalog, entitlement policy, product variants, product attributes, catalog visibility. NOT for CPQ product catalog (bundles, options, price rules) or for loading standard Product2/Pricebook2 data outside Commerce."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Scalability
triggers:
  - "buyers cannot see products that exist in the catalog even though they are in the right buyer group"
  - "how do I set up product categories and assign products to them in B2B Commerce"
  - "product variants and attributes are not showing correctly on the storefront product detail page"
  - "how do I configure CommerceEntitlementPolicy to control which products different buyer segments see"
  - "the store shows the wrong catalog or products are missing after I associated a new catalog to the store"
tags:
  - commerce-product-catalog
  - b2b-commerce
  - product-category
  - product-attributes
  - entitlement-policy
  - product-variants
  - webstore-catalog
inputs:
  - "B2B or B2C Commerce store name and WebStore record Id"
  - "ProductCatalog Id(s) currently associated to the store via WebStoreCatalog"
  - "List of ProductCategory records and their hierarchy"
  - "CommerceEntitlementPolicy name(s) and associated BuyerGroup(s)"
  - "Product2 records with their attribute set configuration (for variants)"
  - "Whether the store uses search indexing (Salesforce Search or Einstein Search)"
outputs:
  - "Configured ProductCatalog with category hierarchy assigned to the store"
  - "ProductCategoryProduct junction records linking Product2 records to categories"
  - "CommerceEntitlementPolicy records granting buyer groups access to specific products"
  - "Product attribute set and variant configuration guidance"
  - "Validation checklist confirming catalog is search-indexable and buyer-visible"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Commerce Product Catalog

This skill activates when a practitioner needs to create, configure, or troubleshoot the B2B or B2C Commerce product catalog — including category hierarchy setup, product assignment to categories, entitlement policy configuration for buyer visibility, and product attribute/variant modeling. It does not cover CPQ catalog configuration or standard Product2/Pricebook2 data loading outside of a Commerce context.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which WebStore record the work targets and retrieve its Id. A store can be associated with only one ProductCatalog at a time via the WebStoreCatalog junction object.
- Identify how many BuyerGroup records exist and which CommerceEntitlementPolicy records are linked to each. Buyer entitlement per product is capped at 2,000 buyer groups for search indexing — exceeding this silently drops products from search results.
- Confirm whether the store uses Salesforce Search or Einstein Search. Both require a manual search index rebuild after catalog or entitlement changes — changes do not propagate automatically.
- Check if products use attribute sets (for variants). ProductAttributeSet and ProductAttribute records drive the variant model and must be configured before Product2 variant records can be created.

---

## Core Concepts

### ProductCatalog and WebStoreCatalog

`ProductCatalog` is the top-level container for a Commerce catalog. Each store is linked to exactly one `ProductCatalog` through a `WebStoreCatalog` junction record. A single `ProductCatalog` can serve multiple stores, but a store may not reference multiple catalogs simultaneously. Attempting to create a second `WebStoreCatalog` for the same store results in a validation error.

`ProductCategory` records form the navigational and organizational hierarchy within a catalog. Categories are linked to their catalog via the `CatalogId` field on `ProductCategory`. Categories can be nested (parent–child) to arbitrary depth, though very deep hierarchies increase page-load time and are an operational anti-pattern.

Products are assigned to categories through `ProductCategoryProduct` junction records — one per Product2-per-category assignment. A product can belong to multiple categories within the same catalog.

### CommerceEntitlementPolicy and Buyer Visibility

`CommerceEntitlementPolicy` records control which products a buyer group can see and purchase. A policy is linked to a `BuyerGroup` through `CommerceEntitlementPolicyGroup`. Products are explicitly included in a policy via `CommerceEntitlementProduct` records.

The platform limit that causes the most production incidents: a single product can be included in at most **2,000 buyer groups** for search index purposes. If a product is assigned to more than 2,000 buyer groups (via entitlement policies), Salesforce silently excludes it from search results for those buyer groups beyond the cap. There is no error message. The product still appears via direct URL or catalog browsing, but search will not surface it.

### Product Variants and Attribute Sets

Product variants in Commerce are modeled using `ProductAttributeSet` (the set of attributes, e.g., Color, Size) and `ProductAttribute` (individual attribute definitions). A parent product (`Product2` with `IsActive = true`) holds the attribute set reference. Child variant products are separate `Product2` records linked to the parent via the `VariantParentId` field. Each child represents a specific combination of attribute values (e.g., Blue + Large).

Attribute sets must be created and assigned to the parent product before child variants can be created. Attempting to create a variant product without a configured attribute set results in a validation error. Attribute values are stored on `ProductAttributeSetProduct` junction records.

### Search Index Dependency

The Commerce search index is a separate, asynchronous data store derived from the catalog. It must be explicitly rebuilt — via Setup > B2B Commerce > [Store] > Search Index — after any of the following:
- Adding or removing products from categories
- Creating or modifying CommerceEntitlementPolicy records
- Activating or deactivating Product2 records
- Changing WebStoreCatalog associations

Until the index rebuild completes, buyer-facing search results will reflect the previous state.

---

## Common Patterns

### Pattern A: Single Catalog, Flat Category Hierarchy

**When to use:** Stores with fewer than 200 SKUs and a single buyer segment where all buyers see the same products.

**How it works:**
1. Create one `ProductCatalog` record.
2. Create `ProductCategory` records directly under the catalog (no nesting) or with one level of nesting.
3. Create `ProductCategoryProduct` for each Product2 → Category assignment.
4. Create one `WebStoreCatalog` linking the catalog to the store.
5. Create one `CommerceEntitlementPolicy` and one `BuyerGroup`; link all products to the policy.
6. Rebuild the search index.

**Why not the alternative:** Nesting categories deeply (3+ levels) for small catalogs adds configuration overhead and slows storefront category navigation without benefit.

### Pattern B: Single Catalog, Segmented Entitlement Policies

**When to use:** Multiple buyer tiers (e.g., Gold, Silver, Public) need different product visibility within the same store and catalog structure.

**How it works:**
1. Create one `ProductCatalog` and assign it to the store via `WebStoreCatalog`.
2. Create `ProductCategory` records shared across all buyer tiers.
3. Create separate `BuyerGroup` and `CommerceEntitlementPolicy` per tier.
4. Assign products to the appropriate policies via `CommerceEntitlementProduct` records.
5. Monitor total buyer group assignments per product — stay below 2,000.
6. Rebuild the search index after any policy change.

**Why not the alternative:** Separate catalogs per buyer tier requires separate stores (one catalog per store) and multiplies administrative overhead. Segmented entitlement within one catalog is the canonical Commerce approach.

### Pattern C: Variant Products with Attribute Sets

**When to use:** Products that come in multiple configurations (e.g., clothing in multiple sizes and colors, equipment in multiple voltages).

**How it works:**
1. Create a `ProductAttributeSet` record (e.g., "Apparel Attributes").
2. Create `ProductAttribute` records linked to the set (e.g., Color, Size).
3. Create the parent `Product2` record and link the attribute set.
4. Create child `Product2` variant records — one per attribute combination — with `VariantParentId` pointing to the parent.
5. Set attribute values on each child via `ProductAttributeSetProduct`.
6. Add only the parent product to `ProductCategoryProduct`; children are discoverable via the parent on the PDP.
7. Assign the parent and children to `CommerceEntitlementProduct` records as needed.

**Why not the alternative:** Creating separate, unrelated Product2 records for each variant breaks the storefront PDP variant selector and prevents buyers from switching between variants on the same page.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All buyers see the same products | Single BuyerGroup + Single EntitlementPolicy | Simplest setup; fewest records; easiest to maintain |
| Multiple buyer tiers, different product visibility | Multiple BuyerGroups + multiple EntitlementPolicies | Native Commerce entitlement model; stays within one catalog and one store |
| Need separate pricing AND separate product catalogs | Separate stores with separate catalogs | One catalog per store is a platform constraint; pricing differences alone don't require separate catalogs |
| Products in multiple configurations | Variant Products with ProductAttributeSet | Provides storefront variant selector UX; keeps SKU navigation coherent |
| Product visible in admin but missing from buyer search | Rebuild search index; verify entitlement; check 2,000 group cap | Search index is async; entitlement is separate from category assignment |
| Need to move product from one catalog to another | Delete ProductCategoryProduct in old catalog; create new in new catalog; check entitlement policy | Products themselves (Product2) are org-wide; catalog membership is controlled by junction records |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the target store and current catalog.** Query `WebStoreCatalog` for the store's `WebStoreId` to confirm the active `ProductCatalogId`. Note: only one record is allowed per store.
2. **Design the category hierarchy.** Sketch the top-level categories and any sub-categories. Prefer 2 levels maximum for operational simplicity. Create `ProductCategory` records with `CatalogId` pointing to the active catalog.
3. **Assign products to categories.** Create `ProductCategoryProduct` junction records for each Product2 → ProductCategory pairing. A product can belong to multiple categories.
4. **Configure entitlement policies.** For each buyer segment, create or verify a `CommerceEntitlementPolicy` linked to the appropriate `BuyerGroup` via `CommerceEntitlementPolicyGroup`. Create `CommerceEntitlementProduct` records for each product the segment should see. Verify total buyer group assignments per product remain under 2,000.
5. **Configure variant products if applicable.** Ensure `ProductAttributeSet` and `ProductAttribute` records are in place before creating child variant `Product2` records. Set `VariantParentId` on each child.
6. **Rebuild the search index.** Navigate to Setup > B2B Commerce > [Store Name] > Search Index and initiate a full rebuild. Wait for the job to complete before testing buyer-facing search.
7. **Validate buyer visibility end-to-end.** Log in as a buyer user in the appropriate BuyerGroup, search for a product, and confirm it appears. Confirm that products outside the buyer's entitlement policy do not appear.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `WebStoreCatalog` has exactly one record for the target store with the correct `ProductCatalogId`
- [ ] All `ProductCategory` records have a valid `CatalogId` and correct `ParentCategoryId` hierarchy
- [ ] `ProductCategoryProduct` records exist for all products that should appear in at least one category
- [ ] Each buyer group has an active `CommerceEntitlementPolicy` linked via `CommerceEntitlementPolicyGroup`
- [ ] `CommerceEntitlementProduct` records exist for every product the buyer group should see
- [ ] No product is assigned to more than 2,000 buyer groups across all entitlement policies
- [ ] Search index rebuild was initiated and completed successfully after all catalog and entitlement changes
- [ ] Variant products have `VariantParentId` set and all child variants are linked to the parent's attribute set

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **One catalog per store — hard constraint** — A `WebStore` record can have exactly one active `WebStoreCatalog` junction. Attempting to insert a second `WebStoreCatalog` for the same store raises a validation rule error. To switch catalogs, delete the existing `WebStoreCatalog` first, then create the new one.
2. **2,000 buyer group cap is silent** — If a product is included in more than 2,000 `CommerceEntitlementPolicy` records (and thus more than 2,000 buyer groups), it is silently excluded from search index results for buyer groups beyond the 2,000 limit. No error, no warning, no Apex trigger fires. The product still appears via direct navigation but buyers cannot discover it via search.
3. **Search index does not auto-rebuild** — Adding a product to a category or an entitlement policy does not trigger any automatic search reindex. Buyers will not see new products in search until an admin initiates a full or incremental index rebuild from Setup.
4. **Category assignment does not equal buyer visibility** — Assigning a product to a `ProductCategory` makes it organizationally visible in the Commerce admin but does not make it visible to buyers. Buyer visibility requires a `CommerceEntitlementProduct` record in the buyer group's active entitlement policy AND an up-to-date search index.
5. **Variant children require attribute set before creation** — A child variant `Product2` record cannot be saved without an existing, valid `ProductAttributeSet` linked to the parent product. Creating variants before the attribute set is configured results in a validation error that does not always provide a clear field-level message in the UI.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ProductCatalog record | Top-level catalog container associated to the store via WebStoreCatalog |
| ProductCategory records | Hierarchical category structure within the catalog |
| ProductCategoryProduct records | Junction records assigning Product2 to categories |
| WebStoreCatalog record | Junction linking one ProductCatalog to one WebStore |
| CommerceEntitlementPolicy records | Controls which products each buyer group can see and buy |
| CommerceEntitlementProduct records | Junction records listing products visible under a given policy |
| Search Index rebuild confirmation | Setup record showing successful completion of search index rebuild |
| Variant configuration | ProductAttributeSet, ProductAttribute, and child Product2 records with VariantParentId set |

---

## Related Skills

- admin/b2b-commerce-store-setup — Use when setting up the WebStore, BuyerGroup, and storefront configuration before the catalog is populated
- data/product-catalog-data-model — Use when bulk-loading Product2, Pricebook2, and PricebookEntry records outside a Commerce context
