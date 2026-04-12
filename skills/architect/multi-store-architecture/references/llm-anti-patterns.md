# LLM Anti-Patterns — Multi-Store Architecture

Common mistakes AI coding assistants make when generating or advising on Multi-Store Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Separate Product Catalog Per Regional Store

**What the LLM generates:** Instructions to create a distinct `ProductCatalog` record for each regional storefront (e.g., "Create NA_Catalog, EMEA_Catalog, and APAC_Catalog, then assign each to its respective WebStore").

**Why it happens:** LLMs trained on general e-commerce content associate "regional store" with "regional data isolation" and apply a naive one-catalog-per-store mapping. They do not distinguish between the product catalog (shared master data) and the storefront catalog (per-store navigation layer) in Salesforce Commerce's two-layer catalog model.

**Correct pattern:**

```
Correct:
  ProductCatalog: "Global Master Catalog" (one, shared)
    → WebStoreCatalog → WebStore: "NA_Store"
    → WebStoreCatalog → WebStore: "EMEA_Store"
    → WebStoreCatalog → WebStore: "APAC_Store"

  Per-store isolation via:
    - EntitlementPolicy per WebStore
    - BuyerGroup → PriceBook assignment per WebStore
    - ProductLocalization records for locale-specific attributes

Wrong:
  ProductCatalog: "NA_Catalog" → WebStore: "NA_Store"
  ProductCatalog: "EMEA_Catalog" → WebStore: "EMEA_Store"
  ProductCatalog: "APAC_Catalog" → WebStore: "APAC_Store"
```

**Detection hint:** Look for multiple `ProductCatalog` records in any multi-store design where the stores sell the same product universe. If the LLM output shows a catalog-per-store mapping without justifying disjoint product universes, flag it.

---

## Anti-Pattern 2: Assuming a Currency Toggle Updates the Active Cart

**What the LLM generates:** A storefront UI component or flow that lets the buyer select a different currency from a dropdown, then calls a cart update API to change the cart's `CurrencyIsoCode` field mid-session.

**Why it happens:** LLMs model currency selection as a simple state change, similar to updating a preference field. They are unaware of the Salesforce Commerce platform constraint that carts are currency-locked at creation time and do not support mid-session currency changes.

**Correct pattern:**

```
Correct:
  - Currency is determined at WebStore level (DefaultCurrency)
  - Buyer selects the correct store/locale at entry
  - Cart is created in the store's currency
  - To change currency: abandon or archive existing cart, create new cart in new store

Wrong:
  // Attempting to update cart currency mid-session
  CartController.updateCartCurrency(cartId, 'EUR'); // Will fail or produce inconsistent state
```

**Detection hint:** Any code or flow that calls a cart update with a currency field change after the cart has been created should be flagged. Also flag UI designs that show a currency dropdown without a store-switch or cart-recreate flow.

---

## Anti-Pattern 3: Treating Shared Catalog as Implying Shared Entitlement

**What the LLM generates:** Advice to link multiple WebStore records to a single product catalog and then stop — with no mention of entitlement policy or buyer group configuration for each store, because "they share the same products."

**Why it happens:** LLMs conflate catalog sharing (product data access) with access control (which buyers can see and order which products). In Salesforce Commerce, entitlement policies and buyer groups are the access control layer; the catalog is the data layer. Sharing the catalog does not restrict or replicate access control.

**Correct pattern:**

```
Correct:
  After linking stores to shared ProductCatalog:
    Store A: EntitlementPolicy "Store_A_Policy" → scopes products visible in Store A
    Store B: EntitlementPolicy "Store_B_Policy" → scopes products visible in Store B

Wrong:
  Link both stores to the catalog.
  Assume products are isolated per store because they "share the catalog."
  (No entitlement policies configured → all catalog products visible in all stores)
```

**Detection hint:** Any multi-store design that mentions shared catalog without explicitly mentioning entitlement policy configuration per store is incomplete. Flag outputs that say "the stores will share the catalog" without follow-up entitlement steps.

---

## Anti-Pattern 4: Advising Multi-Currency Enablement After Commerce Build

**What the LLM generates:** A phased implementation plan where single-currency commerce is built first, and multi-currency is added as a "Phase 2 enhancement" after go-live.

**Why it happens:** LLMs follow a "minimum viable product first" reasoning pattern and treat multi-currency as an optional feature that can be added later, not as an org-level infrastructure decision that affects all commerce data at rest.

**Correct pattern:**

```
Correct:
  Step 0 (before any price books or carts):
    Setup > Company Information > Currencies > Enable Multiple Currencies
    Activate required currencies: USD, EUR, GBP, etc.

Wrong:
  Build single-currency commerce → go live → open support case for multi-currency enablement
  → migrate existing PricebookEntry, CartItem, Order records → high risk data migration
```

**Detection hint:** Any implementation plan that defers multi-currency enablement to a phase after commerce build when future currency requirements are known or possible. Flag "Phase 2: add multi-currency" in any plan where the business has expressed interest in multi-region commerce.

---

## Anti-Pattern 5: Recommending SFCC Cross-Realm Catalog Sharing as a Native Feature

**What the LLM generates:** Instructions to "share the master catalog across your production and UAT SFCC realms through Business Manager's shared catalog feature" or "configure the master catalog to replicate automatically to your other realm."

**Why it happens:** LLMs know that SFCC supports shared catalogs within Business Manager (multiple sites in the same realm share one master catalog) and incorrectly generalize this to cross-realm scenarios. Cross-realm catalog sharing is not a Business Manager native feature.

**Correct pattern:**

```
Correct:
  Same-realm multi-site: Business Manager shared master catalog works natively.
  
  Cross-realm catalog sync:
    - Export catalog from realm A using OCAPI Data API (catalog export endpoint)
      or SCAPI Catalogs API
    - Import into realm B via catalog import pipeline
    - Automate with a CI/CD pipeline or scheduled data job

Wrong:
  "In Business Manager > Catalog > Sharing, enable cross-realm catalog sharing."
  (This feature does not exist for cross-realm scenarios.)
```

**Detection hint:** Any advice that uses the phrase "cross-realm catalog sharing" as a native Business Manager feature, or instructs users to find a cross-realm catalog sharing setting in Business Manager, is incorrect. Flag it and replace with an API-based sync approach.

---

## Anti-Pattern 6: Configuring Multiple WebStoreCatalog Records for One WebStore

**What the LLM generates:** Instructions to create two `WebStoreCatalog` junction records pointing to the same `WebStore` but different storefront catalogs, in order to give different buyer groups different navigation structures within the same store.

**Why it happens:** LLMs reason that buyer group segmentation inside a single store should map to catalog segmentation, and model it as multiple catalog assignments to one store. The platform enforces a one-active-storefront-catalog-per-store constraint and will reject the second `WebStoreCatalog` record.

**Correct pattern:**

```
Correct:
  One WebStoreCatalog per WebStore.
  Buyer group navigation differences handled via:
    - Category visibility rules within the storefront catalog
    - Entitlement policies that scope which categories/products each buyer group sees

Wrong:
  INSERT INTO WebStoreCatalog (WebStoreId, CatalogId, IsActive)
  VALUES ('WebStore_001', 'Catalog_A', true);  -- OK
  
  INSERT INTO WebStoreCatalog (WebStoreId, CatalogId, IsActive)
  VALUES ('WebStore_001', 'Catalog_B', true);  -- VALIDATION ERROR
```

**Detection hint:** Any design or data loading script that inserts more than one active `WebStoreCatalog` record for the same `WebStoreId`. Also flag any design that proposes "catalog A for buyer group X, catalog B for buyer group Y, both on the same WebStore."
