# Gotchas — Multi-Store Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: One Storefront Catalog Per WebStore — Not One Product Catalog

**What happens:** Developers attempt to associate two storefront catalog records (`WebStoreCatalog` junction records) with the same `WebStore`, expecting each to provide a different navigation view for different buyer groups. The platform raises a validation error and blocks the second assignment.

**When it occurs:** When teams conflate the "one storefront catalog per store" constraint with the product catalog itself. The constraint is on the `WebStoreCatalog` junction — a WebStore can have at most one active storefront catalog. The underlying product catalog can be shared across as many WebStore records as needed.

**How to avoid:** Design the storefront catalog (navigation layer) as a per-store artifact. If multiple buyer groups within one store need different navigation, use entitlement policies and category visibility rules within a single storefront catalog rather than attempting to attach multiple storefront catalogs to one WebStore.

---

## Gotcha 2: Shared Catalog Does Not Enforce Shared or Isolated Pricing

**What happens:** Two WebStore records share the same product catalog. The team assumes that because the catalog is shared, pricing will be consistent across stores. In reality, each store's buyer group is assigned a different price book, and the two stores show different prices for the same SKU. Alternatively, the team assumes shared catalog means shared entitlement — buyers from Store A can access Store B products through direct URL or API if entitlement policies are not configured per store.

**When it occurs:** Whenever pricing or entitlement configuration is done at the catalog level rather than the buyer group / entitlement policy level. The catalog controls what products exist; buyer groups and entitlement policies control what each buyer can see and what price they pay.

**How to avoid:** Always configure entitlement policies and buyer group price book assignments explicitly for every WebStore, even when stores share a product catalog. Validate store isolation by attempting to access Store B products as a Store A buyer account before go-live.

---

## Gotcha 3: Multi-Currency Cannot Be Retroactively Enabled Without Migration Effort

**What happens:** A commerce implementation is built with a single currency. Six months later, the business requires a second regional storefront with a different currency. Org-level multi-currency is not enabled. Enabling it at this stage requires a Salesforce support case for the `currencyType` field to be activated and can require data migration of existing price book entries, order records, and cart records. It is not a simple checkbox toggle.

**When it occurs:** When multi-currency requirements are identified after commerce configuration and data have been established on a single-currency org.

**How to avoid:** If there is any possibility of multi-currency requirements in the future, enable org-level multi-currency before building any price books, carts, or order records. The cost of enabling it early is near zero. The cost of retrofitting it is significant.

---

## Gotcha 4: Carts Are Currency-Locked at Session Start

**What happens:** A buyer begins a session on the North America store (USD) and then navigates to the EMEA store (EUR) in the same browser session or through a shared session token. The existing cart retains USD pricing. The buyer sees USD prices on the EMEA storefront. Checkout proceeds with USD pricing even on the EMEA store.

**When it occurs:** In multi-store implementations where session management is not store-scoped, or where a single storefront is used for multiple currencies with a currency toggle UI element.

**How to avoid:** Design store sessions so that cart creation is tied to a specific WebStore with a fixed currency. If a buyer switches stores, the previous cart should be abandoned or archived and a new cart created in the new store's currency. Do not build UI-level currency toggles that assume the cart currency can change mid-session.

---

## Gotcha 5: SFCC Cross-Realm Catalog Sharing Is Not Natively Supported

**What happens:** An SFCC implementation uses production and UAT environments in different realms. The team assumes that the master catalog defined in the production realm is accessible in the UAT realm. Catalog data must instead be exported from the production realm and imported into the UAT realm through OCAPI or SCAPI catalog import. Changes to the master catalog in production are not automatically reflected in UAT.

**When it occurs:** In SFCC multi-realm deployments, including production/non-production splits and multi-geography deployments where different regions are in different realms.

**How to avoid:** Establish a catalog syndication process (export/import pipeline via OCAPI SCAPI or data feeds) between realms from the start of the implementation. Do not assume Business Manager's shared catalog feature extends across realm boundaries.

---

## Gotcha 6: Storefront Catalog Navigation Structure Is Not Automatically Localized

**What happens:** A shared storefront catalog is linked to both an EN and a DE WebStore. The team expects category names and navigation labels to appear in German on the DE store without additional configuration. The storefront catalog navigation structure uses the default locale's labels and does not auto-translate.

**When it occurs:** When locale-specific translations for category names, navigation labels, and storefront content are not explicitly created as localization records or content assets.

**How to avoid:** Create explicit `CategoryLocalization` records (or equivalent translation workbench entries) for every category name and description that appears in storefront navigation for each locale. Set the WebStore `Language` field to the store's primary locale. Do not assume sharing a catalog implies sharing or inheriting translations.
