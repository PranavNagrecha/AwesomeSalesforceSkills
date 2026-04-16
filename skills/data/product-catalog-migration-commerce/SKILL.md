---
name: product-catalog-migration-commerce
description: "Use when migrating product catalog data into Salesforce B2B Commerce — covers category hierarchy, product attributes, images, pricing, and variant structure using the Commerce Import API. NOT for CPQ product catalog migration, post-migration catalog configuration, or commerce catalog taxonomy planning."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I migrate product catalog data into B2B Commerce including categories and variants?"
  - "Commerce Import API vs Data Loader for loading product records into B2B Commerce"
  - "Category assignments missing after importing Product2 records to B2B Commerce store"
  - "How to load product images and pricing into Salesforce B2B Commerce during catalog migration"
  - "What is the required load order for B2B Commerce product catalog migration?"
tags:
  - commerce
  - product-catalog
  - migration
  - B2B-Commerce
  - Import-API
inputs:
  - "Source product catalog data: categories, products, variants, attributes, images, pricing"
  - "Target Commerce store ID and catalog ID"
  - "Product volume and variant depth (max 200 variants per parent, max 9 images per product)"
outputs:
  - "Ordered load plan: ProductCatalog > ProductCategory > Product2 > ProductCategoryProduct > WebStoreCatalog > Pricebook2/PricebookEntry"
  - "Commerce Import API job specification and CSV column structure"
  - "Validation queries to confirm category assignments and pricing after import"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Product Catalog Migration — Commerce

This skill activates when a practitioner needs to migrate product catalog data into Salesforce B2B Commerce, including category hierarchy, product attributes, variant structure, images, and pricing. It provides the required load order and the correct import mechanism (Commerce Import API), and prevents the most common error of using Data Loader for objects that require Commerce-specific import tooling.

---

## Before Starting

Gather this context before working on anything in this domain:

- The recommended import path for B2B Commerce product catalog data is the **Commerce Import API** (`/commerce/management/import/product/jobs`), which accepts async CSV uploads. The synchronous Connect REST import was deprecated at API version 63.0.
- Strict load order is mandatory: ProductCatalog → ProductCategory → Product2 → ProductCategoryProduct → WebStoreCatalog → Pricebook2/PricebookEntry. Each step has foreign key dependencies on the previous.
- Hard platform limits: 3 million products per catalog, 200 variants per parent product, 9 images per product.
- Category assignments require a separate `ProductCategoryProduct` junction record — categories are NOT assigned by a field on Product2.

---

## Core Concepts

### Commerce Import API vs. Data Loader

The Commerce Import API is an asynchronous REST endpoint (`POST /commerce/management/import/product/jobs`) that accepts CSV files and processes them in a managed import job. It handles Commerce-specific validation, relationship integrity, and indexing that Data Loader cannot perform.

Data Loader can insert `Product2` records directly into the Salesforce object model, but it bypasses Commerce-specific processing:
- Category assignments via ProductCategoryProduct require explicit junction records
- Image associations use MediaObject and ContentAsset, not a simple field
- Commerce indexing (search, store availability) does not update from raw object inserts

The synchronous Connect REST import (`/commerce/sale/product`) was deprecated at API v63.0. Do not reference it in new implementations.

### Required Load Order

The catalog load order enforces referential integrity across Commerce objects:

1. **ProductCatalog** — The top-level catalog container. Referenced by all category and product records.
2. **ProductCategory** — Category hierarchy nodes. Parent category must exist before child category.
3. **Product2** — Product records with attributes. References no Commerce-specific objects but must exist before assignments.
4. **ProductCategoryProduct** — Junction: assigns Product2 to ProductCategory. Both Product2 and ProductCategory must exist.
5. **WebStoreCatalog** — Associates ProductCatalog with a WebStore (the storefront). Required for store availability.
6. **Pricebook2 / PricebookEntry** — Price book and line-item pricing per product/currency. Product2 must exist before PricebookEntry.

Loading in any other order produces foreign key constraint errors that terminate the import job.

### Variant Structure

Variants in B2B Commerce are Product2 records with a `ProductClass = Variation` linked to a parent `Product2` with `ProductClass = VariationParent` via the `ProductRelatedComponent` junction object. Limits:
- Maximum 200 variants per parent product
- Maximum 9 images per product (parent or variant)
- Variant attribute values are defined via `ProductAttribute` and `ProductAttributeSet`

---

## Common Patterns

### Pattern 1: Bulk Catalog Migration Using Commerce Import API

**When to use:** Migrating a full product catalog from a legacy PIM or ERP into a new B2B Commerce store.

**How it works:**
1. Export source catalog to CSV files structured per the Commerce Import API column specification
2. Create an import job via `POST /commerce/management/import/product/jobs` with catalog and store context
3. Upload CSV files for each object type in dependency order
4. Poll the job status endpoint until job is complete
5. Validate: query ProductCategory count, ProductCategoryProduct count, PricebookEntry count

**Why not Data Loader:** Data Loader inserts Product2 records to the org but does not associate them with the catalog, categories, or store. Category assignments, image indexing, and store availability require Commerce Import API processing.

### Pattern 2: Incremental Catalog Update

**When to use:** Adding new products or updating pricing in an existing B2B Commerce catalog post-go-live.

**How it works:**
1. Identify delta records (new or modified since last sync)
2. Run incremental Commerce Import API job for the delta CSV only
3. For price changes, update PricebookEntry records via Bulk API (PricebookEntry supports direct updates post-initial-load)
4. Trigger Commerce catalog reindex if search results do not reflect updates within 15 minutes

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Full catalog migration | Commerce Import API (async CSV) | Only supported bulk path for category hierarchy and indexing |
| Price-only updates post-migration | Bulk API to PricebookEntry | PricebookEntry supports direct DML updates for existing records |
| Category hierarchy changes | Commerce Import API for ProductCategory and ProductCategoryProduct | Category junction records require Commerce processing |
| Image upload | ContentAsset + MediaObject via Commerce API | Commerce Import API handles image association; Data Loader does not |
| > 200 variants per parent needed | Architecture review required | 200 variant limit is a hard platform constraint; redesign required |
| CPQ product migration | Use data/product-catalog-migration-cpq skill | CPQ uses SBQQ objects, not Commerce Import API |

---

## Recommended Workflow

1. **Audit source catalog** — Count categories, products, variants, images, and price book entries. Confirm variant depth does not exceed 200 per parent. Identify any product with > 9 images for remediation.
2. **Map source fields to Commerce Import API CSV format** — Document column names for each object in the load order. Obtain the Commerce API CSV specification for the target API version.
3. **Load ProductCatalog and ProductCategory first** — Use Commerce Import API. Validate category hierarchy is correct before proceeding.
4. **Load Product2 records** — Ensure ProductClass is set correctly: VariationParent for parent products, Variation for variants.
5. **Load ProductCategoryProduct junction records** — Associates each product to its category. Both foreign keys must be valid.
6. **Load WebStoreCatalog** — Associates catalog to the store. Required for store visibility.
7. **Load Pricebook2 and PricebookEntry** — Pricing data. Validate currency and quantity schedules.
8. **Validate and reindex** — Run validation SOQL for counts. If search results are stale, trigger catalog reindex via Commerce Setup.

---

## Review Checklist

- [ ] Commerce Import API used, not Data Loader for initial catalog load
- [ ] Load order followed: Catalog > Category > Product2 > CategoryProduct > WebStoreCatalog > Pricebook
- [ ] Variant count per parent confirmed ≤ 200
- [ ] Image count per product confirmed ≤ 9
- [ ] ProductCategoryProduct junction records created for every category assignment
- [ ] WebStoreCatalog record created linking catalog to store
- [ ] Validation SOQL confirms product, category, and pricing counts match source

---

## Salesforce-Specific Gotchas

1. **Category assignments require a separate junction record** — Product2 has no category field. Category assignments are created via `ProductCategoryProduct` records that link Product2 to ProductCategory. Data Loader imports that skip this junction step result in products that are in the org but invisible in any category navigation.
2. **Synchronous Connect REST import is deprecated at API v63.0** — Any tooling or documentation referencing `/commerce/sale/product` synchronous import is using a deprecated endpoint. It may still work in older API versions but should not be used for new implementations.
3. **200 variant limit per parent is a hard catalog constraint** — Attempting to load more than 200 variants per VariationParent product causes the import job to fail for that product. Source catalog products with large variant matrices (e.g., color × size × material) must be redesigned before migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Load order plan | Ordered list of Commerce objects to load with dependency documentation |
| Commerce Import API CSV specs | Column specifications for each object in the load sequence |
| Validation SOQL set | Queries to verify category, product, pricing, and variant counts post-import |

---

## Related Skills

- `data/product-catalog-migration-cpq` — For CPQ-specific product catalog migration using SBQQ objects
- `admin/commerce-product-catalog` — For post-migration catalog configuration and store assignment
- `admin/commerce-catalog-strategy` — For taxonomy planning and category hierarchy design before migration
