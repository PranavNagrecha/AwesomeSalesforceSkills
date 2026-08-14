# Examples — Media Cloud Setup

## Example 1: Where a Digital Flight's Detail Actually Lives

**Scenario:** A two-week connected-TV flight, 300×250 and 728×90 creative, serving weekdays only, with a hiatus over a public holiday.

**Problem:** Every one of those attributes reads like a field on the order line. None of them is. They are separate child records, and the prefix flips between `AdOrderItem…` and `AdOrderLine…` depending on which one you need.

**Solution:** Model the line as a parent with a family of children, and copy each API name rather than inferring it:

```
AdOrderItem                       "the advertisement campaign specific details of an ad order item"
├── AdOrderItemAdSpaceSpec        junction to the ad space specification
├── AdOrderItemCreativeSizeType   "a junction between ad order line and an ad creative
│                                  size, including information about companion creative
│                                  sizes for each ad creative size and the number of
│                                  times each parent creative must be served"
├── AdOrderItemDeliveryFrequency  "the frequency at which an ad order item must be served"
├── AdOrderItemDeliverySchedule   "the time period and the days on which the ad order
│                                  item must be served"
├── AdOrderItemUnitsSplit         "the split interval of the required units for an ad order line"
├── AdOrderLineHiatus             "the hiatus details of the media placement in an order line"
├── AdOrderLineAdTarget           "selections made by users against a specific Ad Order Line
│                                  item for a particular category"
├── AdOrderLineTargetExpression   "the expression that decides the targeting criteria"
└── AdOrderLineTargetValue        "target values that are part of the targeting criteria"
```

In Apex, reference them through type tokens so a wrong prefix fails at compile time rather than at run time:

```apex
// Compiles only if the object exists. AdOrderItemAdTarget would fail here --
// the targeting children use the AdOrderLine prefix.
Schema.SObjectType targetType   = AdOrderLineAdTarget.SObjectType;
Schema.SObjectType scheduleType = AdOrderItemDeliverySchedule.SObjectType;

System.debug(targetType.getDescribe().getName());
System.debug(scheduleType.getDescribe().getName());
```

**Why it works:** A compile-time token turns the most common failure in this domain — a plausible but nonexistent object name — into a deployment error instead of a silent gap in a Flow. Confirm the field API names on each child against the Media Cloud object reference before building; the structure above is the part that is hard to guess.

---

## Example 2: Reconciling Delivery Without Loading the Impression Log

**Scenario:** Invoices bill delivered impressions at contracted CPM. Finance wants every invoice traceable to delivery evidence.

**Problem:** "Traceable" gets read as "stored in Salesforce". A single connected-TV flight can serve more impression rows in a day than the org holds records in total, and the reconciliation job's queries slow past their window within weeks.

**Solution:** Aggregate upstream and land one rollup row per order line per day, carrying the pointer back to the granular source:

```json
{
  "reportDate": "2026-03-14",
  "source": "gam-reporting-api",
  "sourceReportId": "rpt_2026-03-14_ctv_v2",
  "lines": [
    {
      "adOrderItemExternalId": "AOI-2026-Q1-00417",
      "impressionsDelivered": 1284350,
      "clicks": 3120,
      "viewableImpressions": 1109882,
      "currencyIsoCode": "USD"
    },
    {
      "adOrderItemExternalId": "AOI-2026-Q1-00418",
      "impressionsDelivered": 402117,
      "clicks": 890,
      "viewableImpressions": 351044,
      "currencyIsoCode": "USD"
    }
  ]
}
```

Push it on the shipped path rather than a bespoke callout. The AdTech Integration API is the supported route to "external adtech systems", and on deployment "Salesforce creates a named credential for the integration instance" that specifies "the URL of a callout endpoint and its required authentication parameters" — so the endpoint and its secrets already exist:

```apex
// Use the generated named credential. Never re-declare the endpoint or
// embed a token; secrets never appear in logs or agent output.
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Media_AdTech_Integration/delivery/daily');
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
req.setBody(JSON.serialize(dailyRollup));

HttpResponse res = new Http().send(req);
if (res.getStatusCode() != 200) {
    // Log the status and the source report id -- never the request body.
    throw new CalloutException('Delivery sync failed: ' + res.getStatusCode()
        + ' for report ' + dailyRollup.sourceReportId);
}
```

**Why it works:** `sourceReportId` is the audit trail. A disputed invoice is answered by pulling that report from the ad server, which already stores it, rather than by holding a second copy in Salesforce that must be kept consistent forever. Storage stays proportional to order lines, not to impressions.

---

## Anti-Pattern: Building `Media_Deal__c`, `Media_Contract__c`, and `Media_Placement__c`

**What practitioners do:** Model ad sales from first principles, because the objects are not visible in Object Manager before the licence is provisioned and the product is called Media Cloud:

```xml
<!-- WRONG. None of this exists in the shipped model, and none of it
     is what the AdTech integration or the shipped components read. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Media_Placement__c</fullName>
    <label>Media Placement</label>
</CustomObject>
```

**What goes wrong:** The prefix is `Ad`, not `Media`, and the objects are standard. The shipped ASM integration, the revenue rules, and the packaged UI all read `AdOpportunity`, `AdQuote`, `AdQuoteLine`, and `AdOrderItem`. A parallel custom model has to be kept in sync with the real one by hand, forever, or thrown away and re-migrated once the licence lands.

**Correct approach:** Provision first, then model against what shipped:

```
AdOpportunity          "ad sales specific details of an advertisement campaign opportunity"
  └── AdOpportunityLineItem   "a line item in an advertisement opportunity"

AdQuote                "the details of a quote for an advertisement campaign"
  ├── AdQuoteLine      "the details of a line item in an advertisement campaign quote"
  └── AdQuoteMediaTypeProperty  "information associated with the media type for an ad quote"

AdOrderItem            "the advertisement campaign specific details of an ad order item"
```

Every `AdQuoteLine…` child has an order-side mirror, and the two families are separate — configuration written to one is not visible on the other. Test the quote-to-order transition with every child populated before go-live.
