# Examples — Multi-Store Architecture

## Example 1: Three Regional B2B Stores Sharing One Product Catalog

**Context:** A global manufacturing company sells industrial components through three regional B2B Commerce storefronts: North America (USD), EMEA (EUR), and APAC (AUD). They want a single source of truth for product data but need region-specific pricing, buyer access, and language.

**Problem:** Without a shared catalog architecture, each regional catalog must be updated separately whenever a product attribute changes, a new product is launched, or a category is restructured. With 12,000 SKUs and quarterly product launches, this triples maintenance cost and introduces data inconsistencies between regions.

**Solution:**

```
Catalog architecture:
  ProductCatalog: "Global Industrial Components Catalog" (shared)
    └─ WebStoreCatalog → WebStore: "NA_B2B_Store" (storefront catalog: "NA Navigation")
    └─ WebStoreCatalog → WebStore: "EMEA_B2B_Store" (storefront catalog: "EMEA Navigation")
    └─ WebStoreCatalog → WebStore: "APAC_B2B_Store" (storefront catalog: "APAC Navigation")

Per-store configuration:
  NA_B2B_Store:
    - BuyerGroup: "NA_Distributors" → PriceBook: "NA_USD_2025"
    - EntitlementPolicy: "NA_Full_Catalog"
    - Language: en_US, Currency: USD

  EMEA_B2B_Store:
    - BuyerGroup: "EMEA_Partners" → PriceBook: "EMEA_EUR_2025"
    - EntitlementPolicy: "EMEA_Catalog" (excludes products not CE-certified)
    - Language: de / fr / en_GB (translations via ProductLocalization records)
    - Currency: EUR

  APAC_B2B_Store:
    - BuyerGroup: "APAC_Resellers" → PriceBook: "APAC_AUD_2025"
    - EntitlementPolicy: "APAC_Catalog"
    - Language: en_AU, Currency: AUD
```

**Why it works:** The single `ProductCatalog` record contains all 12,000 SKUs. Each WebStore's entitlement policy independently restricts which SKUs are visible and orderable for that region. Price books carry region- and currency-specific list prices. Product attribute translations (name, description, specs) are stored as localization records on the shared product, not as duplicate products. A product record update (new attribute, corrected description) propagates to all three stores immediately.

---

## Example 2: D2C Multi-Language Storefront with Currency Segmentation

**Context:** A consumer goods brand runs a D2C Commerce store for North America and wants to expand to a UK-facing storefront with GBP pricing and en_GB locale, while sharing the same product catalog.

**Problem:** The team initially tries to add GBP as a secondary currency to the existing NA WebStore and serve UK buyers from the same storefront. This creates conflicting price book entries and confuses the checkout flow because the cart currency is locked at session start based on the store's primary currency.

**Solution:**

```
Step 1: Enable org multi-currency
  Setup > Company Information > Currencies > Enable Multiple Currencies
  Activate: USD, GBP

Step 2: Create UK WebStore
  WebStore: "UK_D2C_Store"
    - Language: en_GB
    - DefaultCurrency: GBP
    - WebStoreCatalog → same ProductCatalog as NA store

Step 3: Create GBP price book
  PriceBook: "UK_GBP_Standard_2025"
    - CurrencyIsoCode: GBP
    - PriceBookEntries: all active UK SKUs with GBP list prices

Step 4: Assign UK buyer group
  BuyerGroup: "UK_Consumers"
    - Assigned to UK_D2C_Store
    - PriceBook: UK_GBP_Standard_2025

Step 5: Apply en_GB translations
  ProductLocalization records for product names and descriptions
  WebStore.Language = en_GB
```

**Why it works:** The UK store creates a completely isolated session context. UK buyers land on `UK_D2C_Store`, their cart is initialized in GBP, and they see en_GB product text. NA buyers on the original store continue to see USD pricing and en_US content. No mid-session currency switching is needed because store selection happens at login/entry, not mid-checkout.

---

## Example 3: SFCC Multi-Site with Shared Master Catalog

**Context:** A fashion retailer runs three SFCC storefronts in the same realm: US (en-US, USD), UK (en-GB, GBP), and Germany (de-DE, EUR). They want a single master catalog for product management but separate storefront catalogs for regional navigation.

**Solution:**

```
Business Manager configuration:
  Master Catalog: "Global Fashion Master Catalog"
    - All products and attributes defined here
    - Localized attributes: product name, description, size guide (en-US, en-GB, de-DE)

  Storefront Catalog: "US Storefront Navigation"
    - Assigned to Site: "US_Site"
    - Maps master catalog categories to US navigation taxonomy

  Storefront Catalog: "UK Storefront Navigation"
    - Assigned to Site: "UK_Site"
    - Maps master catalog categories to UK navigation (same taxonomy, different labels)

  Storefront Catalog: "DE Storefront Navigation"
    - Assigned to Site: "DE_Site"
    - Includes only products with EU regulatory compliance flag = true

  Per-site preferences:
    US_Site: Currency = USD, Default Locale = en-US
    UK_Site: Currency = GBP, Default Locale = en-GB
    DE_Site: Currency = EUR, Default Locale = de-DE
```

**Why it works:** Product data is authored once in the master catalog. Locale-specific descriptions and the German regulatory filter are applied at the storefront catalog and site preference layer. Updates to a product in the master catalog propagate to all three sites without manual replication.

---

## Anti-Pattern: Separate Product Catalog Per Regional Store

**What practitioners do:** Create a distinct `ProductCatalog` record for each regional WebStore (e.g., "NA Catalog", "EMEA Catalog", "APAC Catalog") to give each region its own products and navigation.

**What goes wrong:** Product launches, attribute changes, and category restructures must be replicated manually across all catalogs. The three catalogs drift over time — EMEA has an outdated attribute taxonomy, APAC is missing 200 SKUs launched last quarter. The maintenance burden scales with the number of stores and SKUs. Entitlement-level controls (which are per-store regardless of catalog structure) can achieve the same regional product scoping without catalog duplication.

**Correct approach:** Use a single shared `ProductCatalog` for all stores. Apply entitlement policies per store to restrict product visibility to region-appropriate SKUs. Apply locale-specific translations to product records. Only create separate product catalogs when the product universes are genuinely and permanently distinct (e.g., a manufacturing division that sells a completely different product line under a different brand with no shared SKUs).
