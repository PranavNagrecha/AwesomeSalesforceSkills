# Examples — Product Catalog Migration Commerce

## Example 1: Missing Category Assignments After Data Loader Product Import

**Scenario:** A B2B manufacturer used Data Loader to insert 15,000 Product2 records into Salesforce after migrating their legacy PIM. Products appeared in the org but were not visible in any category in the B2B Commerce storefront.

**Problem:** Data Loader inserts Product2 records as standard Salesforce objects but does not create `ProductCategoryProduct` junction records. Without these junction records, products are not assigned to any category and do not appear in category navigation in the store.

**Solution:**
1. Prepare a ProductCategoryProduct CSV with columns: `ProductCategoryId`, `ProductId`, `IsPrimaryCategory`
2. Load via Data Loader using the `ProductCategoryProduct` API name (this object supports direct insert)
3. Alternatively, re-run the full catalog import using Commerce Import API which handles category assignment in the same job

**Why this works:** Category assignment in B2B Commerce is a first-class relationship managed through a junction object, not a field on Product2. Both the junction record and the WebStoreCatalog association must exist for a product to be visible in a storefront.

---

## Example 2: Import Job Failure Due to Incorrect Load Order

**Scenario:** A digital-native retailer attempted to load ProductCategoryProduct junction records before Product2 records were in Salesforce. The Commerce Import API job failed with a foreign key constraint error.

**Problem:** ProductCategoryProduct requires both ProductCategory and Product2 to exist as valid records before the junction record can be created. Loading junction records before their parents violates referential integrity.

**Solution:** Follow the strict load order:
1. ProductCatalog
2. ProductCategory (full hierarchy — parent categories before child categories)
3. Product2 (including VariationParent and Variation products)
4. ProductCategoryProduct (after both sides of the junction exist)
5. WebStoreCatalog
6. Pricebook2 / PricebookEntry

**Why this works:** Commerce Import API validates foreign keys before inserting records. Loading in dependency order eliminates constraint violations and allows the job to complete in a single pass.

---

## Example 3: Variant Limit Exceeded for Product Family

**Scenario:** A clothing retailer needed to migrate a product with 350 color/size/material combination variants. The Commerce Import API job partially completed and reported errors for all variants beyond 200.

**Problem:** The hard platform limit of 200 variants per VariationParent product is enforced by the Commerce Import API. Any import job that specifies more than 200 child variants for a single parent will fail for those variant records.

**Solution:**
1. Identify the variant dimensionality driving the 350-variant count
2. Restructure the catalog: split the single parent into multiple parents (e.g., one VariationParent per color group, each with ≤200 size/material variants)
3. Create a top-level unifying product record for display purposes if needed
4. Re-import with the restructured variant hierarchy

**Why this works:** The 200-variant limit is a Commerce platform constraint and cannot be bypassed. Catalog redesign before migration is the only solution.
