# Gotchas — Product Catalog Migration Commerce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Category Assignments Are Not a Field on Product2

There is no `CategoryId` or similar field on the Product2 object. Category assignments are stored exclusively in the `ProductCategoryProduct` junction object. This surprises most practitioners who expect a simpler field-based relationship. Data Loader imports that insert Product2 records without accompanying ProductCategoryProduct records result in products that are in the Salesforce org but invisible in any Commerce storefront category navigation.

**Fix:** Always create ProductCategoryProduct junction records as a separate step in the load plan, after both ProductCategory and Product2 records exist.

---

## Gotcha 2: Synchronous Connect REST Import Endpoint Deprecated at API v63.0

Documentation before API v63.0 references a synchronous product import endpoint (`/commerce/sale/product`). This endpoint is deprecated in API v63.0+ and should not be used for new implementations. The Commerce Import API (`/commerce/management/import/product/jobs`) is the only supported async import path going forward.

**Fix:** Use the async Commerce Import API exclusively. If legacy tooling uses the synchronous endpoint, plan a migration to the async API before the endpoint is removed.

---

## Gotcha 3: 200 Variant Limit Per Parent Is a Hard Platform Constraint

The limit of 200 variants per VariationParent is a hard catalog platform constraint, not a configurable setting. It cannot be raised by enabling a permission or opening a Salesforce case. Products with more than 200 variants at any level of the attribute matrix require catalog redesign before migration.

**Fix:** Audit source catalog for any product family with large variant matrices (color × size × material combinations can easily exceed 200). Redesign the variant hierarchy to split into multiple parent products before beginning the import.

---

## Gotcha 4: WebStoreCatalog Record Is Required for Store Visibility

Products loaded via Commerce Import API are associated with a ProductCatalog. But products only become visible in a storefront when a WebStoreCatalog record links the ProductCatalog to the WebStore. If this record is missing, products exist in Salesforce and appear in SOQL but are not visible in the Commerce store UI.

**Fix:** Include WebStoreCatalog creation in the load plan after ProductCatalog is loaded. Verify: `SELECT Id FROM WebStoreCatalog WHERE WebStoreId = '<store_id>' AND ProductCatalogId = '<catalog_id>'`.

---

## Gotcha 5: Image Count Limit of 9 Applies Per Product Record, Not Per Family

The 9-image limit applies per Product2 record independently — it is not shared across a variant family. Source systems often store images at the family level and share them across variants. When migrating, image association must be explicitly mapped per product record, not assumed to inherit from parent.

**Fix:** During catalog audit, count images per product in the source system. Build an explicit image-to-product mapping before import, specifying which images attach to the parent and which attach to specific variants.
