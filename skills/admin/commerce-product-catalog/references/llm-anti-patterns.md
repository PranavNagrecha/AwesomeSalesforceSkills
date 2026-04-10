# LLM Anti-Patterns — Commerce Product Catalog

Common mistakes AI coding assistants make when generating or advising on Commerce Product Catalog.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing CommerceEntitlementPolicy with Standard Pricebook2

**What the LLM generates:** Advice to use `Pricebook2` and `PricebookEntry` records to control which products buyers can see, or instructions to set a specific pricebook on the store to limit product visibility.

**Why it happens:** LLMs trained on broad Salesforce data frequently conflate standard e-commerce pricing concepts with Commerce entitlement. `Pricebook2` controls pricing; `CommerceEntitlementPolicy` controls product visibility. The distinction is often blurred in training data because both affect the buyer's product experience.

**Correct pattern:**

```
Buyer product visibility → CommerceEntitlementPolicy + CommerceEntitlementProduct
Buyer pricing → Pricebook2 + PricebookEntry + WebstorePricebook
These are two separate configuration layers; one does not substitute for the other.
```

**Detection hint:** If the generated response uses `Pricebook2` or `PricebookEntry` in the context of "controlling what products buyers can see," flag it as this anti-pattern.

---

## Anti-Pattern 2: Advising Multiple WebStoreCatalog Records for Segmentation

**What the LLM generates:** Instructions to create two or more `WebStoreCatalog` records for the same `WebStore` to give different buyer groups different catalog views, or to "assign multiple catalogs to the store."

**Why it happens:** LLMs generalize from e-commerce platforms (Magento, Shopify) that do support multi-catalog-per-store configurations. Salesforce B2B Commerce enforces a one-catalog-per-store constraint that contradicts this generalization.

**Correct pattern:**

```
One WebStore → one WebStoreCatalog → one ProductCatalog
Buyer segmentation is achieved through CommerceEntitlementPolicy, not through separate catalogs.
If two populations genuinely need different catalogs, they need separate WebStore records (separate stores).
```

**Detection hint:** If the response recommends creating more than one `WebStoreCatalog` for the same store, or suggests that "different buyer groups can see different catalogs" within a single store, flag as this anti-pattern.

---

## Anti-Pattern 3: Treating Category Assignment as Sufficient for Buyer Visibility

**What the LLM generates:** Step-by-step setup instructions that end at creating `ProductCategoryProduct` records, without mentioning `CommerceEntitlementPolicy` or `CommerceEntitlementProduct` configuration. Or, the LLM tells the user that adding a product to a category makes it visible to buyers.

**Why it happens:** Category assignment is a visible, intuitive step that maps to how most product catalogs work (in many systems, category = visibility). The two-layer model (category = structure, entitlement = access) is Commerce-specific and not intuitive from first principles.

**Correct pattern:**

```
ProductCategoryProduct → controls organizational structure (navigation, admin view)
CommerceEntitlementProduct → controls buyer visibility and purchasability
Both are required; neither alone is sufficient for a product to appear in buyer search or category browsing.
```

**Detection hint:** If the workflow for making a product visible to buyers omits any mention of `CommerceEntitlementPolicy` or `CommerceEntitlementProduct`, flag as this anti-pattern.

---

## Anti-Pattern 4: Assuming Search Results Update Immediately After Catalog Changes

**What the LLM generates:** Instructions that tell the user to "save the product, then test in the storefront" immediately after creating `ProductCategoryProduct` or `CommerceEntitlementProduct` records. Or, troubleshooting advice that does not include "rebuild the search index" as a first step for missing-product symptoms.

**Why it happens:** Most Salesforce platform features update near-real-time after DML commits. The Commerce search index is a separately maintained async store that does not follow this pattern. LLMs generalize from the standard Salesforce consistency model.

**Correct pattern:**

```
After any catalog or entitlement change:
1. Commit DML changes
2. Navigate to Setup > B2B Commerce > [Store] > Search Index
3. Initiate a full or incremental rebuild
4. Wait for the rebuild job to complete
5. THEN test buyer-facing storefront search and browsing
```

**Detection hint:** If the generated troubleshooting or setup workflow does not mention search index rebuild as a required step between making catalog changes and testing buyer visibility, flag as this anti-pattern.

---

## Anti-Pattern 5: Confusing B2B Commerce ProductCatalog with CPQ Product Catalog

**What the LLM generates:** References to CPQ objects (`SBQQ__ProductOption__c`, `SBQQ__ProductRule__c`, `SBQQ__Quote__c`) when the user asks about Commerce product catalog setup. Or, instructions to configure CPQ product bundles and options to manage storefront product visibility.

**Why it happens:** "Product catalog" is used in both the CPQ and the B2B Commerce contexts in Salesforce documentation. LLMs frequently conflate these two completely separate product management systems, especially when both terms appear in training data together.

**Correct pattern:**

```
B2B/B2C Commerce product catalog objects:
  ProductCatalog, ProductCategory, ProductCategoryProduct,
  WebStoreCatalog, CommerceEntitlementPolicy, CommerceEntitlementProduct,
  ProductAttributeSet, ProductAttribute (for variants)

CPQ catalog objects (completely separate, NOT used in Commerce):
  SBQQ__ProductOption__c, SBQQ__ProductRule__c, SBQQ__Quote__c, SBQQ__QuoteLine__c

Do not mix these two object sets. Commerce does not use SBQQ__ objects for catalog configuration.
```

**Detection hint:** If any `SBQQ__` prefixed object name appears in a response about Commerce storefront product catalog setup, flag as this anti-pattern.

---

## Anti-Pattern 6: Creating Variant Products Before Configuring the Attribute Set

**What the LLM generates:** Code or instructions that create child variant `Product2` records (with `VariantParentId` set) in the same step or before creating and assigning the `ProductAttributeSet` to the parent product.

**Why it happens:** LLMs generate logically plausible insertion order from their training data without knowing the platform's dependency constraint: the parent must have an attribute set assigned before children with `VariantParentId` can be saved.

**Correct pattern:**

```
Required creation order for variant products:
1. Create ProductAttributeSet
2. Create ProductAttribute records linked to the set
3. Assign the attribute set to the parent Product2 record
4. Create child Product2 records with VariantParentId → parent Id
5. Set attribute values per child via ProductAttributeSetProduct

Skipping steps 1-3 before step 4 causes a validation error on the child Product2 insert.
```

**Detection hint:** If a code example or instructions create a `Product2` with `VariantParentId` before showing `ProductAttributeSet` and `ProductAttribute` creation and assignment to the parent, flag as this anti-pattern.
