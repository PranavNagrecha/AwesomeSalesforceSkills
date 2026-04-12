# LLM Anti-Patterns — Commerce Search Customization

Common mistakes AI coding assistants make when generating or advising on Commerce Search Customization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending SOSL or SOQL to Implement Commerce Storefront Search

**What the LLM generates:** Code like `List<List<SObject>> results = [FIND :searchTerm IN ALL FIELDS RETURNING Product2(Id, Name)]` and advice to wire this to a custom LWC search component on the Commerce storefront.

**Why it happens:** LLMs associate "search" in a Salesforce context with SOSL, which is the standard Salesforce full-text search mechanism. Training data has far more SOSL examples than Connect REST search index API examples. The LLM correctly identifies that SOSL can search `Product2` records and assumes this is the right mechanism for storefront search.

**Correct pattern:**

```
Commerce storefront search is powered by a dedicated search index maintained via the
Connect REST API at /commerce/webstores/{webstoreId}/search/indexes.
Storefront search queries run through the Commerce Search API, not SOSL.
SOSL does not enforce BuyerGroup entitlement visibility.
SOSL results do not use the searchableAttributes, facetableAttributes, or sortRules
configuration that governs storefront behavior.
Implement storefront search by configuring the Commerce search index and using the
ConnectApi.CommerceSearch class or the Commerce Search Connect REST endpoint for queries.
```

**Detection hint:** If generated code contains `[FIND ... RETURNING Product2` in the context of a Commerce storefront search feature, flag as incorrect.

---

## Anti-Pattern 2: Treating Commerce Search Configuration as Experience Cloud Search Configuration

**What the LLM generates:** Instructions to configure search in the Experience Builder Site Configuration panel, add `c-search-results` LWC components from the Experience Cloud search component library, or modify the `SearchManager` component settings to control which fields appear in results.

**Why it happens:** Both B2B Commerce and Experience Cloud run on Salesforce and can be co-deployed. LLMs conflate the two search systems because both involve "storefront-like" experiences. Experience Cloud search customization is a separate skill with different APIs, different configuration surfaces, and different limitations.

**Correct pattern:**

```
B2B Commerce and D2C Commerce search is configured via the Connect REST Search Indexes API,
not via Experience Builder or Experience Cloud search settings.
Commerce search uses its own inverted index with explicit searchableAttributes,
facetableAttributes, and sortRules — none of which are configurable through the
Experience Builder UI or the SearchManager component.
Experience Cloud search customization applies to non-commerce Experience Cloud sites.
```

**Detection hint:** If advice references "Experience Builder search settings", "federated search", or `SearchManager` in the context of a Commerce storefront, flag as incorrect.

---

## Anti-Pattern 3: Skipping the Index Rebuild After Configuration Changes

**What the LLM generates:** Instructions to POST the updated search index configuration and then immediately test search results in the storefront, with no mention of triggering or waiting for an index rebuild.

**Why it happens:** Most Salesforce configuration changes (field updates, permission sets, flows) take effect immediately. LLMs generalize this pattern to search index configuration and assume that POSTing the updated configuration is sufficient for changes to be visible in the storefront.

**Correct pattern:**

```
After every POST to /commerce/webstores/{webstoreId}/search/indexes,
a separate rebuild must be triggered:
  POST /commerce/webstores/{webstoreId}/search/indexes/rebuild

The rebuild runs asynchronously. Poll:
  GET /commerce/webstores/{webstoreId}/search/indexes
and wait for "status": "COMPLETED" before testing.

The 60-rebuild/hour limit per store must be verified before triggering.
```

**Detection hint:** If generated instructions update the search index configuration without including a rebuild step, or if they include testing search immediately after configuration without a poll-for-completion step, flag as incomplete.

---

## Anti-Pattern 4: Assuming Einstein Recommendations Work on a Fresh Storefront

**What the LLM generates:** Deployment instructions that add an Einstein `frequentlyBoughtTogether` or `trending` recommendation component to a product detail page as part of the initial storefront launch, with no mention of Activity Tracking API instrumentation or a data collection period.

**Why it happens:** LLMs treat feature deployment and feature availability as the same event. Recommendation components render successfully (the component code is valid) but return empty results until training data exists, which the LLM does not model as a prerequisite distinct from deployment.

**Correct pattern:**

```
Einstein product recommendations require:
1. Activity Tracking API instrumented on every key page (product list, product detail,
   cart, purchase confirmation) to collect interaction events.
2. A sufficient volume of buyer interaction data — typically 2-4 weeks of live traffic
   before recommendations become non-generic.
3. On D2C storefronts, explicit anchor type specification in every recommendation API call.
4. On B2B storefronts, Einstein recommendation license provisioning confirmed in org setup.

Deploy Activity Tracking instrumentation first. Enable recommendation components only
after the data collection period. Communicate to stakeholders that initial recommendation
quality will be low.
```

**Detection hint:** If a deployment plan includes Einstein recommendation components without a prior Activity Tracking instrumentation step, flag as missing a prerequisite.

---

## Anti-Pattern 5: Diagnosing Missing Products Exclusively Through Index Configuration

**What the LLM generates:** When a practitioner reports that specific products are missing from storefront search results, the LLM immediately recommends updating the search index configuration and triggering a rebuild — without investigating BuyerGroup entitlement policy assignment.

**Why it happens:** Index configuration is the visible, API-accessible part of Commerce search. Entitlement policy is a separate data model (CommerceEntitlementPolicy, CommerceEntitlementProduct, CommerceEntitlementBuyerGroup) that the LLM is less likely to surface as a root cause because it involves a data gap rather than a configuration error. The LLM pattern-matches "search not returning products" to "search configuration" rather than "access control gap."

**Correct pattern:**

```
When products are missing from storefront search results, diagnose in this order:
1. FIRST: Verify BuyerGroup entitlement policy assignment.
   Query CommerceEntitlementBuyerGroup for the affected products and the buyer's BuyerGroup.
   Check the 2,000 BuyerGroup-per-product limit.
   Entitlement gaps cause silent omissions with no error message.
2. SECOND: Verify the product fields are declared in searchableAttributes in the index config.
3. ONLY THEN: Trigger a rebuild if configuration changes are needed.

A rebuild will not fix an entitlement policy gap.
```

**Detection hint:** If a missing-product diagnosis jumps directly to index rebuild without a prior entitlement policy audit step, flag as missing root cause analysis.

---

## Anti-Pattern 6: Sorting Search Results Client-Side in LWC

**What the LLM generates:** JavaScript code in a custom LWC component that intercepts the Commerce search wire adapter result and calls `.sort()` on the products array before passing it to the template renderer.

**Why it happens:** Client-side array sorting is a common JavaScript pattern that LLMs apply readily. The LLM knows that search results come back as an array and knows how to sort arrays in JavaScript. It does not model the multi-page pagination behavior that makes client-side sorting semantically incorrect for paginated server-side result sets.

**Correct pattern:**

```
Define sort behavior server-side using sortRules in the search index configuration:
POST /commerce/webstores/{webstoreId}/search/indexes
{
  "sortRules": [
    { "fieldName": "StockKeepingUnit", "sortOrder": "Ascending", "priority": 1 }
  ]
}

Pass the buyer's selected sort option as a parameter to the Commerce Search API call.
Do not sort the returned results array client-side — this breaks multi-page consistency
because pages 2+ are returned in server-side sort order regardless of client-side sorting
applied to page 1.
```

**Detection hint:** If generated LWC code contains `.sort()` applied to a Commerce search results array, flag as an incorrect pattern that breaks paginated search.
