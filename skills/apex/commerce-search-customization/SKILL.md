---
name: commerce-search-customization
description: "Use this skill to configure and tune search in B2B Commerce or D2C Commerce storefronts: searchable attributes, facetable attributes, sort rules, search index rebuilds, Einstein product recommendations, and BuyerGroup entitlement visibility. Trigger keywords: commerce search ranking, faceted navigation commerce, search index rebuild, Einstein recommendations storefront, product not appearing in search. NOT for SOSL query development, Experience Cloud federated search, Salesforce Search for non-commerce objects, or Einstein Search for Service Cloud."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "Products are disappearing from storefront search results even though they exist in the catalog"
  - "How do I add a custom product attribute as a search filter or facet in B2B Commerce?"
  - "Search results are not ordered the way buyers expect — how do I adjust ranking or sort rules?"
  - "Einstein product recommendations are not showing up on the product detail page"
  - "How do I trigger a search index rebuild after changing searchable attribute configuration?"
tags:
  - commerce-search
  - b2b-commerce
  - d2c-commerce
  - faceted-navigation
  - search-ranking
  - einstein-recommendations
  - search-index
  - buyergroup-entitlement
inputs:
  - WebStore ID for the target storefront
  - List of product attributes to make searchable or facetable
  - Desired sort rule priorities (field name, ascending/descending, weight)
  - Whether Einstein Activity Tracking is already instrumented on the storefront
  - BuyerGroup and entitlement policy configuration for the catalog
outputs:
  - Connect REST API payloads for configuring searchable attributes, facetable attributes, and sort rules
  - Step-by-step index rebuild procedure including rate-limit awareness
  - Einstein Activity Tracking instrumentation checklist
  - BuyerGroup entitlement visibility audit checklist
  - Completed work template documenting all changes made
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Commerce Search Customization

This skill activates when a practitioner needs to configure, tune, or troubleshoot search behavior in a B2B Commerce or D2C Commerce storefront — including attribute-level search and facet configuration, result ranking, search index rebuilds, Einstein product recommendations, or silent product disappearance caused by BuyerGroup entitlement policy. It does not cover SOSL, Experience Cloud federated search, or Einstein Search outside the Commerce context.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the storefront is B2B Commerce or D2C Commerce — both use the same Connect REST Search Indexes API surface, but recommender behavior differs (B2B recommenders auto-resolve anchor type; D2C requires explicit anchor configuration).
- Identify the WebStore ID for the target storefront; all Search Indexes API calls are scoped to `/commerce/webstores/{webstoreId}/search/indexes`.
- Check whether Einstein Activity Tracking is already instrumented on the storefront. Einstein product recommendations will return empty or low-quality results until buyer interaction data has been collected through the Activity Tracking API.
- Confirm the number of index rebuilds already triggered in the current hour. The platform enforces a hard cap of 60 search index rebuilds per hour per store. Hitting this cap blocks all further rebuilds until the window rolls over.
- Audit the BuyerGroup and entitlement policy configuration. Products without a matching entitlement policy for the buyer's BuyerGroup are silently excluded from search results at query time — they do not generate an error or warning.

---

## Core Concepts

### Three Attribute Sets That Control Search Behavior

B2B and D2C Commerce search is governed by three independent attribute sets that must be explicitly configured via the Connect REST API. They are not derived automatically from product field metadata.

**Searchable Attributes** determine which product fields the full-text search engine indexes and matches against when a buyer enters a keyword. Only attributes included in this set contribute to keyword matching. Adding a new product field to your product model does not automatically make it searchable.

**Facetable Attributes** determine which fields are surfaced as filterable facets in the search results sidebar (e.g., Brand, Color, Size). A field must be independently declared in the facetable set — being searchable does not make a field facetable. Each facetable attribute requires a `displayType` (SINGLE_SELECT or MULTI_SELECT) and an optional `displayRank` integer to control ordering.

**Sort Rules** determine the available sort options presented to the buyer and the default sort order on page load. Sort rules reference field API names and accept `sortOrder` (Ascending or Descending) and a `priority` integer. Without explicit sort rules, search results fall back to platform default relevance scoring, which buyers often find unpredictable.

All three sets are managed through `POST /commerce/webstores/{webstoreId}/search/indexes` — a single endpoint that accepts all three attribute sets in one payload.

### Index Rebuild Is Required After Every Configuration Change

Changing searchable attributes, facetable attributes, or sort rules does not take effect immediately. An explicit index rebuild must be triggered via `POST /commerce/webstores/{webstoreId}/search/indexes/rebuild`. Until the rebuild completes, the storefront continues serving results based on the previous index configuration.

The platform enforces a hard cap of **60 index rebuilds per hour per store**. This limit is easy to hit during iterative testing or CI/CD pipelines that apply and rebuild on every deployment. Rebuilds must be spaced deliberately; there is no way to queue a rebuild — if the cap is reached, the rebuild call returns an error and the index is not updated.

Index rebuild time scales with catalog size. Large catalogs (tens of thousands of SKUs) can take several minutes. Rebuilds run asynchronously; poll the index status endpoint to confirm completion before testing search behavior.

### BuyerGroup Entitlement Enforcement at Query Time

Commerce search enforces BuyerGroup entitlement visibility at query time, not at indexing time. Products that exist in the catalog and are correctly indexed may still be silently absent from a buyer's search results if the buyer's BuyerGroup does not have an entitlement policy covering those products.

This is the most common cause of unexpected product disappearance in production. The platform does not return an error — the product simply does not appear. There is a hard limit of **2,000 BuyerGroups per product** per entitlement policy. Products assigned to more than 2,000 BuyerGroups require a re-architecture of entitlement policy grouping.

### Einstein Activity Tracking Is a Prerequisite for Recommendations

Einstein product recommendations (collaborative filtering, trending, frequently bought together) depend on buyer interaction data collected through the **Activity Tracking API**. The storefront must instrument page views, product views, add-to-cart events, and purchases via the Activity Tracking API before Einstein can generate recommendations. Recommendations will return empty or generic fallback content until sufficient interaction data exists. On B2B storefronts, Einstein recommenders auto-detect the anchor type from context; on D2C storefronts, the anchor type must be specified in the recommendation request.

---

## Common Patterns

### Pattern: Configure Faceted Navigation for a Custom Product Attribute

**When to use:** A new product attribute (e.g., Material, Voltage Rating, Lead Time) has been added to the product model and the merchandising team wants it available as a filter in the storefront search results sidebar.

**How it works:**
1. Identify the field API name of the custom attribute on the `ProductAttribute` or `Product2` object.
2. `GET /commerce/webstores/{webstoreId}/search/indexes` to retrieve the current index configuration.
3. Add the field to both the `searchableAttributes` array (so it contributes to keyword matching) and the `facetableAttributes` array (so it appears as a filter).
4. Set `displayType` to `SINGLE_SELECT` or `MULTI_SELECT` depending on whether buyers should be able to select multiple values.
5. Assign a `displayRank` integer to control where the facet appears relative to other facets.
6. `POST /commerce/webstores/{webstoreId}/search/indexes` with the updated payload.
7. `POST /commerce/webstores/{webstoreId}/search/indexes/rebuild` to apply the change.
8. Poll the index status until the rebuild status is `COMPLETED`.

**Why not the alternative:** Setting field-level search indexes on Salesforce objects directly (e.g., marking a custom field as indexed in Setup) has no effect on Commerce search. Commerce search uses its own attribute-set-driven index separate from the platform search index.

### Pattern: Adjust Search Result Ranking with Sort Rules

**When to use:** Buyers are getting results in an unexpected order and the team wants to promote in-stock items, highest margin products, or recently added items to the top of search results.

**How it works:**
1. Retrieve the current sort rule configuration with `GET /commerce/webstores/{webstoreId}/search/indexes`.
2. Identify the field API names to use for ranking (e.g., `StockKeepingUnit`, `LastModifiedDate`, a custom `MarginScore__c` field).
3. Build a `sortRules` array with objects containing `fieldName`, `sortOrder` (`Ascending` or `Descending`), and `priority` (lower integer = evaluated first).
4. Include the updated `sortRules` array in the `POST /commerce/webstores/{webstoreId}/search/indexes` payload alongside the existing `searchableAttributes` and `facetableAttributes` (omitting either will reset them to empty).
5. Trigger an index rebuild and wait for completion.

**Why not the alternative:** Attempting to override search result order client-side (in an LWC component that re-sorts the result array) produces inconsistent behavior when buyers paginate — page 2 is served from the server with the original ranking, so re-sorted page 1 and server-ranked page 2 present contradictory result sets.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Buyer types a keyword and a product is missing from results | Verify product is in a searchable attribute and has an entitlement policy for the buyer's BuyerGroup | Two distinct causes: indexing gap or entitlement gap — check both before rebuilding |
| Custom product field needs to appear as a filter in the sidebar | Add to `facetableAttributes` in the search index configuration and rebuild | Facetable attributes are opt-in; field visibility in org setup does not propagate |
| Einstein recommendations return empty on product detail page | Confirm Activity Tracking API is instrumented and sufficient interaction events have been collected | Recommendations require a training data seed; empty results are expected on a fresh storefront |
| Too many index rebuilds hitting the 60/hour cap during CI/CD | Batch all attribute set changes into a single index configuration update before triggering one rebuild | Each POST to the indexes endpoint can carry all three attribute sets; rebuild once per deployment |
| Products assigned to more than 2,000 BuyerGroups | Refactor entitlement policy grouping to reduce per-product BuyerGroup count below 2,000 | Platform hard cap; exceeding it causes silent entitlement failures with no error returned |
| Sort order is inconsistent across pages | Define explicit sort rules in the index configuration rather than sorting client-side | Server-side pagination uses server-side sort order; client-side re-sorting breaks multi-page consistency |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather context**: Confirm the WebStore ID, storefront type (B2B or D2C), the specific search behavior goal (new facet, ranking change, recommendation setup, or product visibility fix), and the current index rebuild count for this hour.
2. **Retrieve current index configuration**: `GET /commerce/webstores/{webstoreId}/search/indexes` and read the existing `searchableAttributes`, `facetableAttributes`, and `sortRules` arrays before making any changes — a `POST` that omits an array resets it to empty.
3. **Audit entitlement policy if products are missing**: Before touching index configuration, verify the affected products have an entitlement policy covering the buyer's BuyerGroup. Check the 2,000 BuyerGroup-per-product limit if the catalog uses broad entitlement assignment.
4. **Build and POST the updated index configuration**: Include all three attribute sets (searchable, facetable, sort rules) in a single `POST /commerce/webstores/{webstoreId}/search/indexes` payload. Batch all changes into one request to minimize rebuild count.
5. **Trigger a single index rebuild**: `POST /commerce/webstores/{webstoreId}/search/indexes/rebuild`. Verify you have rebuild budget (fewer than 60 rebuilds in the current hour). Poll the index status endpoint until status is `COMPLETED`.
6. **Instrument Einstein Activity Tracking if recommendations are in scope**: Confirm the LWC components on the storefront fire page-view, product-view, add-to-cart, and purchase events through the Activity Tracking API before enabling recommendation components. On D2C, verify the anchor type is explicitly specified in each recommendation request.
7. **Test and document**: Verify search results, facet rendering, sort behavior, and recommendation output against the intended configuration. Record the final `POST` payload and rebuild timestamp in the work template for audit trail.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All three attribute sets (searchable, facetable, sort rules) are present in the POST payload — none were accidentally omitted, which would reset them to empty
- [ ] Index rebuild was triggered after configuration changes and polled to `COMPLETED` status before testing
- [ ] Rebuild count for the current hour was verified to be below 60 before triggering the rebuild
- [ ] Products reported as missing were audited against BuyerGroup entitlement policy — not just index configuration
- [ ] Einstein Activity Tracking API events are instrumented on the storefront before recommendation components are enabled
- [ ] For D2C storefronts, Einstein recommendation anchor type is explicitly specified in all recommendation API calls
- [ ] The 2,000 BuyerGroup-per-product limit was checked for any products with broad entitlement assignment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **POST to search/indexes resets omitted attribute sets** — The `POST /commerce/webstores/{webstoreId}/search/indexes` endpoint treats the absence of an attribute set in the payload as an intent to clear it. If you POST only an updated `facetableAttributes` array without including the existing `searchableAttributes` and `sortRules`, those sets are erased from the index configuration. Always read the current configuration first and include all three sets in every POST.

2. **60-rebuild-per-hour cap has no queue** — When the cap is reached, the rebuild API call returns an error immediately. There is no automatic retry or queue. CI/CD pipelines that call rebuild on every metadata deployment will exhaust the budget within minutes on an active development day. Design deployments to batch all search configuration changes and trigger exactly one rebuild per deployment.

3. **Entitlement policy gaps produce silent product omissions** — A product correctly indexed and visible in catalog management can be completely absent from a buyer's search results if the buyer's BuyerGroup lacks an entitlement policy for that product. No error is thrown, no warning is logged in the storefront. This is the most common cause of production escalations about "missing products" that are not actually missing from the catalog.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search index configuration payload | JSON body for `POST /commerce/webstores/{webstoreId}/search/indexes` documenting all searchable attributes, facetable attributes, and sort rules for the storefront |
| Index rebuild log | Timestamp, rebuild trigger call, and status poll result confirming `COMPLETED` — required for deployment audit trail |
| Einstein Activity Tracking instrumentation checklist | Per-page event list (page view, product view, add-to-cart, purchase) with confirmation that each LWC component fires the correct Activity Tracking API call |
| BuyerGroup entitlement audit | Table of affected products with entitlement policy assignment status per BuyerGroup |
| Completed work template | Filled-in `commerce-search-customization-template.md` documenting scope, decisions, and deviations |

---

## Related Skills

- lwc/experience-cloud-search-customization — Use this for Experience Cloud site search (federated search, search scope, search bar LWC customization) rather than Commerce storefront search
- apex/commerce-integration-patterns — Use when Commerce search must be extended via custom Apex search provider override or external search engine integration
- architect/b2b-vs-b2c-architecture — Use when deciding which Commerce platform to build on and understanding how entitlement and catalog architecture differ between the two models
