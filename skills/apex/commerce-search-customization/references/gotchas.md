# Gotchas — Commerce Search Customization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: POST to search/indexes Silently Resets Omitted Attribute Sets

**What happens:** The `POST /commerce/webstores/{webstoreId}/search/indexes` endpoint uses a full-replacement model, not a merge model. If you POST a payload that includes only `facetableAttributes` and omits `searchableAttributes` and `sortRules`, the platform replaces the entire index configuration with your payload — meaning `searchableAttributes` and `sortRules` are set to empty. Keyword search stops working entirely (no fields are indexed for text matching) and sort options disappear from the storefront. No warning or confirmation is returned in the API response.

**When it occurs:** Most commonly during iterative development when a developer PATCHes a single attribute set using a minimal payload, or when a code change generates the POST body from a partial data structure that does not include all three attribute set keys. Also occurs when an LWC admin tool or custom integration only reads and updates one attribute set at a time.

**How to avoid:** Always `GET /commerce/webstores/{webstoreId}/search/indexes` first to retrieve the full current configuration. Merge your changes into the complete payload and POST all three attribute sets — `searchableAttributes`, `facetableAttributes`, and `sortRules` — every time. Treat the index configuration as an atomic document, not an updateable record with individual fields.

---

## Gotcha 2: 60 Rebuild/Hour Cap Has No Queue and No Warning Before Failure

**What happens:** The platform allows a maximum of 60 search index rebuild operations per storefront per hour. When the 60th rebuild is triggered, subsequent rebuild calls return an error response immediately. There is no automatic queue, no retry, and no proactive warning when the budget is running low. The error does not indicate how many rebuilds remain or when the window resets.

**When it occurs:** Most dangerous during active sprint development when multiple developers or CI/CD pipeline runs trigger rebuilds independently throughout the day. A four-person team each triggering 15–20 test rebuilds per hour can exhaust the budget before noon. It also occurs during data migration events where a script bulk-updates product attributes and triggers a rebuild after each batch.

**How to avoid:** Treat the rebuild as a scarce shared resource. Batch all attribute configuration changes into a single `POST /commerce/webstores/{webstoreId}/search/indexes` call before triggering one rebuild. In CI/CD, gate the rebuild trigger on the last step of the deployment pipeline, not on each individual configuration change. Track the rebuild count in a shared deployment log. For bulk migration scripts, trigger one rebuild at the end of the full migration run rather than after each batch.

---

## Gotcha 3: BuyerGroup Entitlement Gaps Produce Silent Product Omissions in Search

**What happens:** Products that are correctly indexed and visible in catalog management can be completely absent from a buyer's search results if the buyer's BuyerGroup does not have an active `CommerceEntitlementBuyerGroup` record linking it to the product's entitlement policy. The platform returns no error, no partial result, and no indication that products were filtered out. From the buyer's perspective, the product simply does not exist. From an admin perspective, the product appears healthy in all standard views.

**When it occurs:** Most commonly after BuyerGroup restructuring (merges, splits, or renames) where entitlement policy assignments are not updated to reflect the new group structure. Also occurs during initial storefront setup when the catalog is populated before entitlement policies are fully configured, and during bulk product imports where new products are added to the catalog without corresponding entitlement policy records.

**How to avoid:** After any BuyerGroup change, run a SOQL audit across `CommerceEntitlementBuyerGroup` to verify all products have entitlement policy assignments covering every active BuyerGroup. When diagnosing missing product reports, always check entitlement policy assignment before investigating index configuration — this is the more common root cause. Note the hard limit of 2,000 BuyerGroups per product per entitlement policy; catalogs with very broad entitlement assignment must group BuyerGroups to stay within this limit, or products will silently lose visibility for BuyerGroups beyond the cap.

---

## Gotcha 4: Index Rebuild Runs Asynchronously — Changes Are Not Immediate

**What happens:** After triggering an index rebuild with `POST /commerce/webstores/{webstoreId}/search/indexes/rebuild`, the API returns a `200 OK` immediately but the rebuild runs asynchronously in the background. The storefront continues serving search results from the previous index until the rebuild completes. Developers who test search behavior immediately after triggering the rebuild see stale results and incorrectly conclude their configuration change had no effect. They then trigger another rebuild, consuming rebuild budget unnecessarily.

**When it occurs:** Any time a developer triggers a rebuild and immediately tests search behavior in the storefront. Large catalogs with tens of thousands of SKUs can take several minutes to fully rebuild.

**How to avoid:** After triggering a rebuild, poll `GET /commerce/webstores/{webstoreId}/search/indexes` and check the `status` field. Wait until the response contains `"status": "COMPLETED"` before testing search behavior. Do not assume the rebuild is complete because the trigger API call returned a success response.

---

## Gotcha 5: Einstein Recommendations Return Empty Until Activity Tracking Data Exists

**What happens:** Einstein product recommendation components (e.g., `frequentlyBoughtTogether`, `recentlyViewed`, `trending`) return empty result sets on a freshly deployed storefront or after a storefront URL change that resets the activity tracking context. The component renders with no products and no error. This is frequently misdiagnosed as a configuration error or broken integration, triggering unnecessary debugging effort.

**When it occurs:** On any storefront that has not yet accumulated buyer interaction data through the Activity Tracking API. Also occurs on storefronts that have the recommendation component deployed but are missing the Activity Tracking API instrumentation on product list pages, product detail pages, cart pages, or checkout confirmation pages.

**How to avoid:** Before enabling Einstein recommendation components on any page, verify that the Activity Tracking API is instrumented to fire events for: page views, product views, add-to-cart actions, and purchase completions. On B2B storefronts, confirm Einstein recommendation licenses are provisioned for the org. Communicate to stakeholders that recommendation quality improves over time as the activity dataset grows — empty or generic recommendations during the initial launch period are expected and not a defect.
