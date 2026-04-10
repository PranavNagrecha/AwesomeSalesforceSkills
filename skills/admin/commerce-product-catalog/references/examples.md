# Examples — Commerce Product Catalog

## Example 1: Setting Up a Two-Tier Catalog with Separate Buyer Entitlements

**Context:** A manufacturer runs a B2B Commerce store with two buyer segments: Distributors (see full catalog including clearance items) and Retailers (see standard catalog only). Both segments browse the same category hierarchy but need different product visibility.

**Problem:** Without distinct entitlement policies, either all buyers see all products or none see any. The category structure alone does not control buyer visibility — entitlement policies are required in addition to category assignment.

**Solution:**

```
Step 1: Create the shared ProductCatalog
  - Name: "Manufacturer B2B Catalog"
  - Link to store: WebStoreCatalog (CatalogId → store's WebStoreId)

Step 2: Create the category hierarchy (shared by both segments)
  ProductCategory: "Industrial Equipment" (CatalogId → catalog above, ParentCategoryId = null)
  ProductCategory: "Power Tools" (ParentCategoryId → "Industrial Equipment")
  ProductCategory: "Clearance" (CatalogId → catalog above, ParentCategoryId = null)

Step 3: Assign products to categories via ProductCategoryProduct
  ProductCategoryProduct: Product2 "Drill Pro 3000" → "Power Tools"
  ProductCategoryProduct: Product2 "Drill Pro 2000 Refurb" → "Clearance"

Step 4: Create Distributor entitlement
  BuyerGroup: "Distributor Group"
  CommerceEntitlementPolicy: "Distributor Policy" (IsActive = true)
  CommerceEntitlementPolicyGroup: links "Distributor Policy" → "Distributor Group"
  CommerceEntitlementProduct: "Drill Pro 3000" → "Distributor Policy"
  CommerceEntitlementProduct: "Drill Pro 2000 Refurb" → "Distributor Policy"

Step 5: Create Retailer entitlement (standard catalog only)
  BuyerGroup: "Retailer Group"
  CommerceEntitlementPolicy: "Retailer Policy" (IsActive = true)
  CommerceEntitlementPolicyGroup: links "Retailer Policy" → "Retailer Group"
  CommerceEntitlementProduct: "Drill Pro 3000" → "Retailer Policy"
  (No clearance products added to Retailer Policy)

Step 6: Rebuild search index from Setup > B2B Commerce > [Store] > Search Index
```

**Why it works:** Category assignment controls the navigation structure. Entitlement policies independently control search visibility and purchase access. A Retailer buyer can navigate to the "Industrial Equipment" category and see "Power Tools" products they are entitled to, but the "Clearance" category will appear empty (or hidden if category visibility rules are configured) because no clearance products are in their policy.

---

## Example 2: Configuring Product Variants for a Clothing Line

**Context:** A B2B apparel company sells t-shirts that come in three sizes (S, M, L) and two colors (Black, White). Each size-color combination is a separate SKU that must be orderable individually, but buyers should see one product listing on the storefront with a variant selector.

**Problem:** Creating six separate, unrelated Product2 records (one per size-color combo) and listing them all independently in the category results in a fragmented storefront experience — buyers see six separate listings instead of one product with options, and there is no variant selector on the product detail page.

**Solution:**

```
Step 1: Create the ProductAttributeSet
  Name: "Apparel Size-Color Set"

Step 2: Create ProductAttribute records linked to the set
  ProductAttribute: Name="Size", DataType="Text", ProductAttributeSetId → above set
  ProductAttribute: Name="Color", DataType="Text", ProductAttributeSetId → above set

Step 3: Create the parent Product2
  Name: "Classic Tee"
  IsActive: true
  ProductAttributeSetId → "Apparel Size-Color Set"

Step 4: Create child Product2 variant records
  For each size-color combination:
    Product2: Name="Classic Tee - S/Black", VariantParentId → "Classic Tee" parent Id
    Product2: Name="Classic Tee - S/White", VariantParentId → "Classic Tee" parent Id
    Product2: Name="Classic Tee - M/Black", VariantParentId → "Classic Tee" parent Id
    ... (repeat for all 6 combinations)

Step 5: Set attribute values per variant via ProductAttributeSetProduct
  Classic Tee - S/Black: Size="S", Color="Black"
  Classic Tee - S/White: Size="S", Color="White"
  ... etc.

Step 6: Assign ONLY the parent product to ProductCategoryProduct
  ProductCategoryProduct: "Classic Tee" (parent) → "Apparel" category

Step 7: Add parent and all child variants to CommerceEntitlementProduct
  (Buyers must be entitled to both parent and variant children to order)

Step 8: Rebuild search index
```

**Why it works:** The storefront Commerce PDP reads the `VariantParentId` relationship to render the variant selector widget. Only the parent needs a category assignment — the platform discovers variants automatically through the parent-child relationship. Entitlement must cover both parent and child records because buyers can add children directly to the cart.

---

## Anti-Pattern: Using Multiple WebStoreCatalog Records for Catalog Segmentation

**What practitioners do:** Attempt to create two `WebStoreCatalog` records for the same store — one for standard products and one for premium products — to support buyer-tier segmentation at the catalog level.

**What goes wrong:** Salesforce enforces a one-catalog-per-store constraint via a validation rule on `WebStoreCatalog`. The second insert fails with a validation error. Even if somehow bypassed in a sandbox, the search index build behavior is undefined for multi-catalog stores, leading to inconsistent buyer results.

**Correct approach:** Use a single `ProductCatalog` containing all products. Use `CommerceEntitlementPolicy` records to segment which products each buyer tier can see. This is the canonical Commerce multi-tier catalog architecture — category structure is shared, buyer visibility is controlled entirely by entitlement policies, not by separate catalogs.
