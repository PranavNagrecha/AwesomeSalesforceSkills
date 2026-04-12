# Examples — Commerce Search Customization

## Example 1: Adding a Custom Attribute as a Searchable Facet

**Scenario:** A B2B electrical equipment distributor has added a `Voltage_Rating__c` custom field to their product model. Buyers need to filter search results by voltage rating, but the field does not appear in the facet sidebar and keywords like "240V" return no results.

**Problem:** The custom field was added to the `ProductAttribute` object and is visible in the product detail page, but Commerce search has its own attribute index that is not automatically synchronized with org field metadata. Neither keyword search nor facet filtering will use the field until it is explicitly declared in both the `searchableAttributes` and `facetableAttributes` arrays of the search index configuration.

**Solution:**

Step 1 — Retrieve the current index configuration to avoid overwriting existing settings:

```http
GET /services/data/v63.0/commerce/webstores/{webstoreId}/search/indexes
Authorization: Bearer {sessionId}
```

Step 2 — Build the updated configuration payload, adding `Voltage_Rating__c` to both attribute sets:

```json
{
  "searchableAttributes": [
    { "fieldName": "Name", "priority": 1 },
    { "fieldName": "Description", "priority": 2 },
    { "fieldName": "Voltage_Rating__c", "priority": 3 }
  ],
  "facetableAttributes": [
    {
      "fieldName": "Brand__c",
      "displayType": "SINGLE_SELECT",
      "displayRank": 1
    },
    {
      "fieldName": "Voltage_Rating__c",
      "displayType": "MULTI_SELECT",
      "displayRank": 2
    }
  ],
  "sortRules": [
    { "fieldName": "Name", "sortOrder": "Ascending", "priority": 1 }
  ]
}
```

Step 3 — POST the updated configuration:

```http
POST /services/data/v63.0/commerce/webstores/{webstoreId}/search/indexes
Authorization: Bearer {sessionId}
Content-Type: application/json
```

Step 4 — Trigger the index rebuild:

```http
POST /services/data/v63.0/commerce/webstores/{webstoreId}/search/indexes/rebuild
Authorization: Bearer {sessionId}
```

Step 5 — Poll until the rebuild completes:

```http
GET /services/data/v63.0/commerce/webstores/{webstoreId}/search/indexes
```

Check the `status` field in the response. Wait until `"status": "COMPLETED"` before testing.

**Why it works:** Commerce search maintains its own inverted index separate from platform search. The explicit `searchableAttributes` declaration tells the indexer to extract and tokenize the field value during rebuild. The `facetableAttributes` declaration instructs the search API to include aggregated facet counts for that field in every search response, which the storefront LWC reads to render the filter sidebar. Both declarations are needed independently — being searchable does not make a field facetable.

---

## Example 2: Diagnosing Silent Product Disappearance Due to BuyerGroup Entitlement Gap

**Scenario:** A D2C apparel storefront has 500 products indexed. After a BuyerGroup restructuring that consolidated three existing groups into one, 47 products stopped appearing in search results for buyers in the newly merged group. The products are visible in Salesforce admin and appear in catalog management. No errors appear in logs.

**Problem:** The BuyerGroup restructuring removed the old BuyerGroup assignments from the entitlement policies covering those 47 products but did not assign the new consolidated BuyerGroup. Commerce search enforces entitlement visibility at query time — if a product's entitlement policy does not cover the requesting buyer's BuyerGroup, the product is silently excluded from results. The index is not the problem; the entitlement configuration is.

**Solution:**

Step 1 — Identify the affected buyer's BuyerGroup ID from their BuyerAccount record.

Step 2 — Query the entitlement policy assignments for the 47 affected products:

```soql
SELECT Id, Name, BuyerGroupId, CommerceEntitlementProductId
FROM CommerceEntitlementBuyerGroup
WHERE CommerceEntitlementProduct.Product2Id IN (
    'product_id_1', 'product_id_2'
)
ORDER BY BuyerGroupId
```

Step 3 — Confirm the new consolidated BuyerGroup ID is absent from the results for the affected products.

Step 4 — Insert `CommerceEntitlementBuyerGroup` records to assign the new BuyerGroup to the relevant `CommerceEntitlementPolicy`:

```apex
List<CommerceEntitlementBuyerGroup> assignments = new List<CommerceEntitlementBuyerGroup>();
for (Id policyId : affectedPolicyIds) {
    assignments.add(new CommerceEntitlementBuyerGroup(
        CommerceEntitlementPolicyId = policyId,
        BuyerGroupId = newConsolidatedBuyerGroupId
    ));
}
insert assignments;
```

Step 5 — No index rebuild is required. Entitlement enforcement is applied at query time against live entitlement data, not baked into the index.

**Why it works:** The Commerce search engine evaluates buyer entitlement in real time during each search query, joining the buyer's BuyerGroup membership against the active entitlement policies. The index only stores product content; access control is a separate runtime filter. This means entitlement fixes take effect immediately without a rebuild, but also means that entitlement gaps are invisible in catalog management UI — they only manifest as missing search results.

---

## Anti-Pattern: Sorting Search Results Client-Side in an LWC Component

**What practitioners do:** When buyers report that search results are in the wrong order, developers intercept the search response in a custom LWC wire adapter handler and sort the result array in JavaScript before rendering.

**What goes wrong:** Commerce search returns paginated results. The first page is re-sorted client-side correctly. When the buyer clicks to page 2, the server responds with the next page of results ranked by the server's sort order — which is different from the client-side sort the buyer just saw on page 1. The buyer sees results jump and the apparent ranking becomes incoherent. Additionally, items that should be on page 1 under the desired ranking may be on page 3 of the server response — client-side sorting of individual pages cannot surface them.

**Correct approach:** Define explicit sort rules in the search index configuration via the Connect REST API. Use `sortRules` with `fieldName`, `sortOrder`, and `priority` to declare the desired ranking server-side. Trigger a rebuild after updating sort rules. Client-side components should only pass the selected `sortOrder` parameter to the Commerce search API — not re-sort the returned array.
