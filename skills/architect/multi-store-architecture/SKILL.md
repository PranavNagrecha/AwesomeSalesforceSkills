---
name: multi-store-architecture
description: "Multi-store Commerce architecture: shared catalog, localization, multi-currency, multi-language, and regional storefront design for B2B, D2C, and SFCC deployments. Trigger keywords: multi-store, regional storefronts, shared catalog, multi-currency commerce, localization, multiple WebStores. NOT for single-store setup, store creation basics, or non-Commerce use cases."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
triggers:
  - "How do I set up multiple regional storefronts sharing the same product catalog in B2B Commerce?"
  - "We need separate stores for North America, EMEA, and APAC with different currencies and languages — what is the right architecture?"
  - "Can multiple WebStore records share one catalog, and how do we handle per-store pricing and entitlement?"
  - "What is the correct pattern for multi-currency in a D2C or B2B Commerce deployment where buyers from different regions see local prices?"
  - "How do we support multiple languages per store without duplicating the product catalog?"
tags:
  - commerce-cloud
  - multi-store
  - localization
  - multi-currency
  - B2B
  - D2C
  - WebStore
  - catalog
  - entitlement
inputs:
  - "Number of storefronts and their regional scope (e.g., NA, EMEA, APAC)"
  - "Commerce platform type: org-based B2B Commerce, org-based D2C Commerce, or SFCC (Business Manager)"
  - "Currencies required per store"
  - "Languages and locales required per store"
  - "Buyer segmentation requirements (buyer groups, entitlement policies)"
  - "Whether org-level multi-currency is already enabled"
outputs:
  - Multi-store catalog architecture decision (shared vs. per-store catalog)
  - Entitlement and buyer group configuration guidance per store
  - Multi-currency enablement and price book design guidance
  - Locale and translation configuration approach
  - Store-level configuration checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Multi-Store Architecture

This skill activates when a practitioner needs to design or configure multiple Commerce storefronts — whether org-based B2B/D2C or SFCC — with requirements for shared catalogs, regional pricing, multiple currencies, multiple languages, or buyer-segmented entitlement. It does not cover single-store setup or Commerce basics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Platform identity**: Is this org-based B2B Commerce, org-based D2C Commerce, or SFCC (Salesforce Commerce Cloud / Business Manager)? The catalog and store data models differ materially.
- **Multi-currency status**: For org-based commerce, confirm whether org-level multi-currency (`Setup > Company Information > Currencies`) is already enabled. You cannot enable multi-currency after data exists without a migration effort, and carts do not switch currency mid-session.
- **Number and scope of stores**: How many WebStore records (or SFCC sites) are needed? What are the regional and buyer-segment boundaries that justify separate stores vs. a single store with entitlement segmentation?
- **Common wrong assumption**: Practitioners and LLMs often assume each regional store needs its own separate product catalog. The correct pattern is a single shared product catalog with locale-specific translations and per-store entitlement configuration.
- **Platform constraint**: In org-based commerce, a WebStore record can be associated with only one storefront catalog (via the `WebStoreCatalog` junction object). One storefront catalog can be linked to multiple WebStore records, but each WebStore can have at most one storefront catalog active at a time.

---

## Core Concepts

### Concept 1: Product Catalog vs. Storefront Catalog (Org-Based Commerce)

In org-based B2B and D2C Commerce, two distinct catalog layers exist:

- **Product catalog** (`ProductCatalog`): contains the canonical set of products, categories, and product attributes. This is the master data layer shared across stores.
- **Storefront catalog** (`WebStoreCatalog` junction → `ProductCatalog`): controls which product catalog is exposed to a given WebStore, and the navigation structure buyers see.

A single product catalog can be shared across multiple WebStore records. Each WebStore is associated with one storefront catalog. Sharing the product catalog does not mean sharing pricing, entitlement, or buyer access — those are controlled independently per store.

### Concept 2: Entitlement, Buyer Groups, and Price Books Are Per-Store

Sharing a catalog does not share access rules. Each WebStore independently configures:

- **Entitlement policies** — which products are visible and orderable to which buyers
- **Buyer groups** — collections of accounts granted access to specific products, pricing tiers, and store features
- **Price books** — org-level records, but assigned to buyer groups per store; a regional store uses a regional price book without affecting other stores

This separation is intentional. A North America store and an EMEA store can share the same product catalog but show different prices, different product subsets, and different navigation to their respective buyers.

### Concept 3: Multi-Currency — Org Enablement First, Cart Isolation Always

For org-based commerce, multi-currency requires:

1. Org-level multi-currency must be enabled before building any commerce configuration (Setup > Company Information > Currencies > Enable).
2. Each currency must be activated at the org level.
3. Price books contain currency-specific entries; a buyer's cart uses the currency set at session start.
4. Carts do not auto-switch currency mid-session. If a buyer changes locale mid-session, the existing cart currency is preserved. Re-creation or abandonment is required to switch.

For SFCC (Business Manager), currency is configured per site in Site Preferences and does not depend on org-level Salesforce settings.

### Concept 4: Localization — Translations, Not Catalog Copies

Multi-language support is delivered through locale-specific translations on product attributes, category names, and store content — not through duplicate catalogs. In org-based commerce, `ProductCatalogLocalization` and product attribute translation records carry locale variants. In SFCC, localization is managed through content slots, page designer, and catalog locale assignments within Business Manager.

For org-based commerce, the default store language is set on the WebStore record (`Language` field). Additional languages are delivered via translation workbench or data import into localization objects.

---

## Common Patterns

### Pattern A: Single Shared Catalog, Multiple Regional WebStores

**When to use:** Multiple regional or segment-specific storefronts need the same product universe but different pricing, buyer access, languages, and currencies.

**How it works:**
1. Create one `ProductCatalog` as the master catalog containing all products.
2. Create one storefront catalog (navigation structure) per WebStore, or share a single storefront catalog if navigation is identical across regions.
3. Link each WebStore to its storefront catalog via `WebStoreCatalog`.
4. Create region-specific price books (e.g., `NA_USD_PriceBook`, `EMEA_EUR_PriceBook`).
5. Create buyer groups per store; assign region-specific accounts and price books to each buyer group.
6. Configure entitlement policies per store to control product visibility.
7. Apply locale-specific translations to shared product records.

**Why not the alternative:** Creating a separate product catalog per regional store multiplies catalog maintenance overhead. Every product change (new attribute, price list update, category restructure) must be replicated across all catalogs manually. Shared catalog with per-store entitlement absorbs regional variation without duplication.

### Pattern B: SFCC Multi-Site with Shared Master Catalog

**When to use:** Deploying multiple storefronts on Salesforce Commerce Cloud (Business Manager), each with distinct locale, currency, or brand identity.

**How it works:**
1. Define one master catalog in Business Manager containing all products and attributes.
2. Create a storefront catalog per site that maps a subset of master catalog categories to site-specific navigation.
3. Assign the storefront catalog to each site in Site Preferences.
4. Set per-site currency and primary locale in Site Preferences.
5. Add locale-specific product data (names, descriptions) through catalog import or localization tools.
6. Sites in different realms cannot share master catalog data natively — cross-realm sharing requires API-based data sync.

**Why not the alternative:** Giving each SFCC site its own master catalog fragments product data management and prevents global pricing or attribute governance.

### Pattern C: Entitlement-Only Segmentation Within a Single Store

**When to use:** Multiple buyer segments (e.g., wholesale vs. retail) need different product visibility and pricing but do not require separate branded storefronts.

**How it works:** Use buyer groups and entitlement policies within a single WebStore to segment access. This avoids the operational overhead of running multiple stores when a single store with proper segmentation suffices.

**Why not the alternative:** Creating separate WebStore records for buyer segments that could be served by entitlement policies inside one store inflates infrastructure and session management complexity.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same products, different regional pricing and language | Single shared product catalog, per-store price books and localization | Eliminates catalog duplication; pricing and language are independently configurable |
| Completely separate product lines per brand | Separate product catalogs per brand | Genuine product universe divergence justifies catalog separation |
| Multiple buyer tiers within one region needing different visibility | Single WebStore with buyer groups and entitlement policies | Segmentation inside one store avoids multi-store overhead |
| SFCC sites in the same realm with shared product universe | One master catalog, per-site storefront catalogs | Business Manager native pattern; master catalog is shared by design |
| SFCC sites in different realms | API-based product data sync between realms | Cross-realm catalog sharing is not natively supported in SFCC |
| Multi-currency needed org-wide | Enable org multi-currency before any commerce build | Cannot be enabled retroactively without migration; affects all currency-related data |
| Buyer currency must change mid-session | Not supported natively; cart must be recreated | Commerce carts are currency-locked at session start |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the platform and store count** — Confirm whether the target is org-based B2B/D2C Commerce or SFCC. Determine how many storefronts are required and why (regional brand, currency, buyer segment, or regulatory boundary). Document which separation factors genuinely require separate WebStore records vs. which can be handled by entitlement segmentation within one store.
2. **Verify org-level prerequisites** — For org-based commerce: confirm multi-currency is enabled if multiple currencies are needed; confirm the org is on a Commerce-enabled edition. For SFCC: confirm realm structure, available site slots, and Business Manager access. Do not proceed with catalog or store design until prerequisites are confirmed.
3. **Design the catalog architecture** — Default to a single shared product catalog. Map which store will share it and how the storefront catalog (navigation structure) will be organized per store. Only recommend separate product catalogs if the product universes are genuinely disjoint.
4. **Configure per-store entitlement, buyer groups, and price books** — For each WebStore, define the buyer groups, assign accounts, and link region-appropriate price books. Create entitlement policies that scope product visibility per store. Validate that sharing the product catalog does not inadvertently expose products across stores through direct URL or API access.
5. **Set up localization and currency** — Apply locale-specific translations to product records (name, description, attributes). Set the default language on each WebStore record. Activate required currencies at org level and create currency-specific price book entries. Confirm that each storefront catalog is linked to the correct WebStore via `WebStoreCatalog`.
6. **Validate store isolation** — Test that buyer accounts in Store A cannot access Store B. Confirm that pricing, entitlement, and language are correctly scoped per store. Verify that cart creation locks to the correct currency for the store's locale.
7. **Review against the checklist** — Run through the review checklist below before marking architecture complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform identity confirmed (org-based B2B/D2C vs. SFCC)
- [ ] Org-level multi-currency enabled before any price book or cart configuration
- [ ] Product catalog architecture documented: shared or separate, with justification
- [ ] Each WebStore linked to exactly one storefront catalog via `WebStoreCatalog`
- [ ] Buyer groups and entitlement policies configured per store (not inherited from shared catalog)
- [ ] Region-specific price books created and assigned to the correct buyer groups
- [ ] Locale-specific translations applied to product records; WebStore `Language` field set
- [ ] Store isolation validated: buyer in Store A cannot access Store B products or pricing
- [ ] Cart currency behavior confirmed — no mid-session currency switching expected or designed for
- [ ] SFCC-only: master catalog vs. storefront catalog distinction applied; cross-realm sync strategy defined if applicable

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **One storefront catalog per WebStore** — A `WebStore` record can be associated with only one storefront catalog at a time (one active `WebStoreCatalog` record per store). Attempting to create a second `WebStoreCatalog` for the same store will produce a validation error. The product catalog underneath can be shared; the storefront catalog (navigation layer) is per-store.
2. **Shared catalog does not mean shared pricing or entitlement** — Linking two WebStore records to the same product catalog does not automatically share pricing, product visibility, or buyer access. Entitlement policies, buyer groups, and price books must be configured independently for each store. Omitting this step can expose all products to all buyers across stores.
3. **Multi-currency requires org enablement before commerce build** — Org-level multi-currency cannot be enabled after significant commerce data exists without a migration effort. It must be enabled in Setup > Company Information > Currencies before price books, carts, or orders are created. Retroactive enablement is possible but disruptive.
4. **Carts are currency-locked at session start** — Once a buyer's cart is created in a given currency, the cart does not automatically switch currency if the buyer changes locale or store context mid-session. A new cart must be created to reflect a different currency. Designing multi-store checkout flows that assume automatic currency switching will fail.
5. **SFCC cross-realm catalog sharing is not native** — SFCC sites in different realms (e.g., production and sandbox, or two separate production realms) cannot share master catalog data natively through Business Manager. Cross-realm catalog sync requires API-based data pipelines (OCAPI or SCAPI import/export), not a built-in shared catalog feature.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Multi-store catalog architecture diagram | Shows which WebStore records share which product catalog and storefront catalogs |
| Per-store entitlement and buyer group matrix | Maps buyer accounts → buyer groups → entitlement policies → price books per store |
| Currency enablement checklist | Org-level and store-level currency configuration steps |
| Localization configuration record | Per-store language settings and translation scope |
| Store isolation validation report | Test results confirming buyer accounts cannot cross-access stores |

---

## Related Skills

- `commerce-catalog-strategy` — Catalog data model design, attribute strategy, and catalog vs. entitlement segmentation decisions
- `multi-currency-sales-architecture` — Org-level multi-currency enablement patterns for Sales Cloud and commerce
- `b2b-vs-b2c-requirements` — Choosing between B2B Commerce and D2C Commerce platform models
- `commerce-checkout-flow-design` — Checkout flow design impacted by multi-store and multi-currency configuration

---

## Official Sources Used

- B2B Commerce Developer Guide — Product and Catalog Data Model: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_catalog_data_model.htm
- Support Multiple Currencies in a Commerce Store: https://help.salesforce.com/s/articleView?id=sf.comm_multiple_currencies.htm
- B2C Commerce Architecture and Localization: https://developer.salesforce.com/docs/commerce/sfcc/guide/b2c-localization.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
