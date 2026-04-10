# Examples — CPQ Architecture Patterns

## Example 1: Telecommunications Bundle with Hidden Sub-Components

**Context:** A telco provider sells internet service bundles where each bundle includes a base service, a CPE (customer premises equipment) hardware item, and an optional managed WiFi add-on. Without architecture guidance, the team configured all three as visible quote lines per bundle. A quote with 10 bundles produced 30+ quote lines, and a quote with 50 bundles reliably failed to save.

**Problem:** The team hit the QLE 200-line reliability limit at ~70 bundles (210 lines) and encountered intermittent save failures. The root cause was that each bundle component appeared as a separate QLE row, triggering a recalculation cycle per row on save.

**Solution:**

```text
Bundle Design:
  Parent: Internet Service Bundle (SBQQ__Hidden__c = false — user sees this)
    Component: CPE Hardware (SBQQ__Hidden__c = true — priced but not shown)
    Component: Managed WiFi (SBQQ__Hidden__c = true, SBQQ__Optional__c = true)

Result:
  - User sees 1 line per bundle in QLE
  - CPE and WiFi prices roll up to the bundle parent via
    SBQQ__BundledQuantity__c and price roll-up configuration
  - 50-bundle quote = 50 visible lines, well below QLE limit
  - Sub-components still appear on the generated Quote Document
    via separate Quote Template line item section
```

**Why it works:** Setting `SBQQ__Hidden__c = true` on components removes them from QLE rendering while preserving their contribution to the parent bundle price. The pricing engine still calculates them; they just do not appear as editable rows in the browser UI. This reduces both browser payload and SOQL operations per save.

---

## Example 2: Static Resource QCP for Complex Ramp Pricing

**Context:** A SaaS company required a QCP that calculated multi-year ramp pricing based on a custom escalation schedule stored in a custom object. The initial inline QCP implementation reached 95,000 characters and began failing silently after the field limit truncated the closing function statements.

**Problem:** `SBQQ__Code__c` was silently truncated at 131,072 characters. The plugin appeared valid in the UI but executed broken JavaScript. Pricing callbacks returned `undefined` instead of the modified quote lines, causing the QLE to display stale prices with no error message.

**Solution:**

```javascript
// Content of SBQQ__Code__c (loader only — ~300 chars):
(function() {
  var req = new XMLHttpRequest();
  req.open('GET', '/resource/CPQRampPricingPlugin', false);
  req.send(null);
  if (req.status === 200) {
    eval(req.responseText);
  } else {
    console.error('CPQ Plugin load failed: ' + req.status);
  }
})();

// Static Resource: CPQRampPricingPlugin (StaticResource metadata)
// Contains full plugin implementation:
// export function onBeforeCalculate(quote, lines, conn) { ... }
// export function onAfterCalculate(quote, lines, conn) { ... }
// Full implementation: ~110,000 chars — safely in Static Resource
```

```xml
<!-- CPQRampPricingPlugin.resource-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<StaticResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <cacheControl>Private</cacheControl>
    <contentType>application/javascript</contentType>
    <description>CPQ Quote Calculator Plugin - Ramp Pricing Logic</description>
</StaticResource>
```

**Why it works:** The Static Resource is not subject to the 131,072-character field limit. The loader in `SBQQ__Code__c` is minimal and well within limits. The Static Resource is version-controlled as a metadata file and deployed via standard Salesforce DX pipeline. When the plugin logic changes, only the Static Resource is redeployed — no manual copy-paste into the custom script field required.

---

## Example 3: ERP Integration via ServiceRouter

**Context:** An order management ERP needed to create CPQ quotes on behalf of inside sales reps as part of a configure-price-quote flow initiated in the ERP. The integration team initially wrote quotes directly via Salesforce REST API by POSTing to `/services/data/vXX.0/sobjects/SBQQ__Quote__c`.

**Problem:** Direct DML on `SBQQ__Quote__c` does not invoke CPQ managed package triggers. Quote lines created via direct API had zero net prices, missing `SBQQ__PricebookEntryId__c` lookups, and could not be activated. The pricing engine was entirely bypassed.

**Solution:**

```http
POST /services/apexrest/SBQQ/ServiceRouter HTTP/1.1
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "saver": "SBQQ.QuoteService.save",
  "model": {
    "record": {
      "SBQQ__Account__c": "0011800001XYZ",
      "SBQQ__PricebookId__c": "01s1800000ABC",
      "SBQQ__Status__c": "Draft",
      "CurrencyIsoCode": "USD"
    },
    "lineItems": [
      {
        "record": {
          "SBQQ__Product__c": "01t1800000DEF",
          "SBQQ__Quantity__c": 5,
          "SBQQ__PricebookEntryId__c": "01u1800000GHI"
        }
      }
    ]
  }
}
```

**Why it works:** `ServiceRouter` routes the request through the CPQ managed package's internal save logic. The pricing engine runs the full waterfall (List → Contracted → Block → Discount Schedules → Price Rules → Net), all required fields are populated, and the resulting quote is in a consistent state that can be presented in the QLE or activated.

---

## Anti-Pattern: Nested Bundles to Represent Product Families

**What practitioners do:** Create a 3-level bundle where the top-level product is a "Product Family" bundle, second-level products are product lines, and third-level products are individual SKUs. This mirrors the product catalog taxonomy.

**What goes wrong:** Each nesting level multiplies the number of SOQL queries the pricing engine must execute per calculation. A 3-level bundle with 5 sub-bundles and 10 SKUs per sub-bundle generates a quote with 55+ lines and triggers 300+ SOQL queries on save — approaching Apex governor limits. Calculation timeouts become common. Large Quotes Mode helps but does not eliminate the root cause.

**Correct approach:** Flatten to at most 2 levels (parent + components). Use Option Constraints to handle conditional SKU inclusion. Use `SBQQ__FeatureName__c` on Product Options to visually group components in the QLE without creating additional nesting. Reserve nested bundles for genuine hierarchical product structures where the sub-bundle is itself sold independently.
