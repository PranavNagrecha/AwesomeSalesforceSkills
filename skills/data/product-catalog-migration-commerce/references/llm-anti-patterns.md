# LLM Anti-Patterns — Product Catalog Migration Commerce

Common mistakes AI coding assistants make when generating or advising on B2B Commerce product catalog migrations.

---

## Anti-Pattern 1: Using Data Loader to Insert Product2 Records Without ProductCategoryProduct Junction Records

**What the LLM generates:** Instructions to export product data to CSV and load into the `Product2` object using Data Loader, treating it like a standard object migration.

**Why it happens:** LLMs know that Product2 is a standard Salesforce object and Data Loader is the standard bulk insert tool. They do not model the Commerce-specific junction object that creates category assignments.

**Correct pattern:** Product2 records loaded without corresponding ProductCategoryProduct junction records will not appear in any Commerce storefront category. Category assignment requires a separate junction record (ProductCategory ↔ Product2). Use Commerce Import API which handles this relationship in the same import job, or create ProductCategoryProduct records explicitly as a separate load step.

**Detection hint:** If instructions insert Product2 records but do not mention ProductCategoryProduct, category assignments will be missing.

---

## Anti-Pattern 2: Referencing the Deprecated Synchronous Connect REST Import Endpoint

**What the LLM generates:** Code or instructions referencing `/commerce/sale/product` for product import.

**Why it happens:** Older Salesforce Commerce documentation and community posts referenced the synchronous endpoint. LLMs trained on this corpus continue to reference it.

**Correct pattern:** The synchronous import endpoint (`/commerce/sale/product`) was deprecated at API v63.0. The correct endpoint for new implementations is the async Commerce Import API: `POST /commerce/management/import/product/jobs`. Use the async job pattern with status polling.

**Detection hint:** Any reference to `/commerce/sale/product` is using a deprecated endpoint.

---

## Anti-Pattern 3: Assuming Products Are Visible in the Store After ProductCategory Import Without WebStoreCatalog

**What the LLM generates:** A load plan that ends with ProductCategoryProduct creation without a WebStoreCatalog step, assuming products are now visible in the storefront.

**Why it happens:** LLMs do not model the separate WebStoreCatalog record that links a catalog to a storefront. They conflate "product is in Salesforce" with "product is visible in the Commerce store."

**Correct pattern:** A WebStoreCatalog record associating the ProductCatalog with the WebStore is required for store visibility. Without it, products exist in Salesforce and are queryable via SOQL but do not appear in the storefront.

**Detection hint:** If the load plan does not include a WebStoreCatalog step, store visibility cannot be confirmed.

---

## Anti-Pattern 4: Treating 200 Variant Limit as Configurable

**What the LLM generates:** "To exceed the 200 variant limit, enable the extended catalog feature in Setup or contact Salesforce support to increase the limit."

**Why it happens:** LLMs generalize from other configurable limits (API request limits, storage limits) and assume variant limits are similarly adjustable.

**Correct pattern:** The 200 variant limit per VariationParent is a hard platform constraint with no configuration option. Products exceeding this limit require catalog redesign — splitting large variant families into multiple parent records before migration.

**Detection hint:** If instructions suggest increasing or bypassing the 200-variant limit through any configuration path, the claim is incorrect.

---

## Anti-Pattern 5: Using CPQ SBQQ Objects or Logic for Commerce Product Migration

**What the LLM generates:** Instructions referencing `SBQQ__Product__c`, `SBQQ__PricingMethod__c`, or CPQ price rule objects when the target is B2B Commerce, because the task mentions "product catalog" and "pricing."

**Why it happens:** Both CPQ and Commerce involve product catalogs and pricing. LLMs conflate the two product data models when context is ambiguous.

**Correct pattern:** B2B Commerce uses `Product2`, `ProductCatalog`, `ProductCategory`, `Pricebook2`, and `PricebookEntry` from the standard Salesforce object model — not CPQ SBQQ namespace objects. CPQ product migration uses the `data/product-catalog-migration-cpq` skill.

**Detection hint:** If SBQQ-prefixed objects appear in a Commerce migration plan, the skill has crossed into CPQ territory incorrectly.
