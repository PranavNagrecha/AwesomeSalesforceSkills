# Examples — Commerce Extension Points

## Example 1: Custom Pricing Calculator with External Price Feed

**Context:** A B2B store needs to apply customer-segment pricing fetched from an external ERP. The ERP exposes a REST endpoint that accepts a list of product SKUs and customer account IDs and returns adjusted unit prices. Standard Salesforce price books cannot model this per-account dynamic pricing.

**Problem:** Without a custom cart calculator, Commerce applies the default price book price. The business requirement is for Price Tier A customers to receive a 15% discount on all items during checkout, sourced live from the ERP.

**Solution:**

```apex
public class ErpPricingCalculator extends CartExtension.PricingCartCalculator {

    // Called synchronously during cart recalculation — no DML, no async
    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartItemCollection items = cart.getCartItems();

        // Build the list of SKUs to price
        List<String> skus = new List<String>();
        for (Integer i = 0; i < items.size(); i++) {
            skus.add(items.get(i).getSku());
        }

        // Callout is allowed here because this is a before-phase hook
        Map<String, Decimal> erpPrices = fetchPricesFromErp(skus, cart.getAccountId());

        // Apply ERP prices to each cart item — no DML, set via API objects
        for (Integer i = 0; i < items.size(); i++) {
            CartExtension.CartItem item = items.get(i);
            Decimal erpPrice = erpPrices.get(item.getSku());
            if (erpPrice != null) {
                item.setUnitAdjustedPrice(erpPrice);
                item.setTotalAdjustedPrice(erpPrice * item.getQuantity());
            }
        }
    }

    private Map<String, Decimal> fetchPricesFromErp(List<String> skus, String accountId) {
        // Build and send the HTTP callout — permitted in before hook
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP_Price_Service/prices');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'skus'      => skus,
            'accountId' => accountId
        }));

        HttpResponse res = new Http().send(req);
        Map<String, Decimal> prices = new Map<String, Decimal>();

        if (res.getStatusCode() == 200) {
            Map<String, Object> parsed =
                (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            Map<String, Object> raw = (Map<String, Object>) parsed.get('prices');
            for (String sku : raw.keySet()) {
                prices.put(sku, (Decimal) raw.get(sku));
            }
        }
        return prices;
    }
}
```

`RegisteredExternalService` metadata (`ErpPricingCalculator.md-meta.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>ERP Pricing Calculator</label>
    <protected>false</protected>
    <values>
        <field>ExternalServiceProviderType</field>
        <value xsi:type="xsd:string">CartCalculator</value>
    </values>
    <values>
        <field>ExtensionPointName</field>
        <value xsi:type="xsd:string">Commerce_Domain_Pricing_CartCalculator</value>
    </values>
    <values>
        <field>ExternalServiceProvider</field>
        <value xsi:type="xsd:string">ErpPricingCalculator</value>
    </values>
</CustomMetadata>
```

**Why it works:** `ErpPricingCalculator` extends the platform-provided `CartExtension.PricingCartCalculator` base class and overrides `calculate()`. All price changes are written through the `CartExtension.CartItem` setter API — no DML is needed. The HTTP callout runs in a before-phase hook, which is the only lifecycle phase where callouts are permitted. The `RegisteredExternalService` metadata record uses the exact EPN string `Commerce_Domain_Pricing_CartCalculator` to wire the class into the Commerce recalculation pipeline.

---

## Example 2: Real-Time Inventory Validation Hook

**Context:** A B2B store with high-velocity ordering must prevent over-ordering by checking live warehouse stock before allowing cart checkout. The warehouse management system (WMS) exposes a REST API that returns available quantity per SKU.

**Problem:** Salesforce product inventory fields are updated nightly from the WMS but can be stale by the time a buyer submits a large order. Without a real-time check, over-ordered items reach the order management system and require manual cancellation.

**Solution:**

```apex
public class WmsInventoryChecker extends CartExtension.CartCalculate {

    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartItemCollection items = cart.getCartItems();

        // Collect SKUs and quantities to check
        Map<String, Decimal> requestedQty = new Map<String, Decimal>();
        for (Integer i = 0; i < items.size(); i++) {
            CartExtension.CartItem item = items.get(i);
            requestedQty.put(item.getSku(), item.getQuantity());
        }

        // HTTP callout to WMS — allowed in before-phase hook only
        Map<String, Decimal> availableQty = fetchAvailableStock(requestedQty.keySet());

        // Write validation failures — no DML required
        CartExtension.CartValidationOutputCollection validations =
            cart.getCartValidationOutputs();

        for (String sku : requestedQty.keySet()) {
            Decimal requested = requestedQty.get(sku);
            Decimal available = availableQty.containsKey(sku) ? availableQty.get(sku) : 0;
            if (requested > available) {
                CartExtension.CartValidationOutput cvo =
                    new CartExtension.CartValidationOutput(
                        CartExtension.CartValidationOutputTypeEnum.INVENTORY,
                        CartExtension.CartValidationOutputLevelEnum.ERROR
                    );
                cvo.setMessage('Insufficient stock for SKU ' + sku +
                    '. Requested: ' + requested + ', Available: ' + available);
                validations.add(cvo);
            }
        }
    }

    private Map<String, Decimal> fetchAvailableStock(Set<String> skus) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:WMS_Inventory/stock');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{ 'skus' => new List<String>(skus) }));
        HttpResponse res = new Http().send(req);

        Map<String, Decimal> stock = new Map<String, Decimal>();
        if (res.getStatusCode() == 200) {
            Map<String, Object> parsed =
                (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            Map<String, Object> raw = (Map<String, Object>) parsed.get('stock');
            for (String sku : raw.keySet()) {
                stock.put(sku, (Decimal) raw.get(sku));
            }
        }
        return stock;
    }
}
```

**Why it works:** Inventory failures are communicated through the platform's `CartValidationOutput` API, not through DML on order records. The Commerce engine reads the validation outputs and blocks checkout progression when ERROR-level outputs are present. Because this is a before hook, the HTTP callout to the WMS is permitted. No records are modified; the extension only reads cart state and writes validation results through the provided API objects.

---

## Anti-Pattern: DML Inside a Cart Calculator

**What practitioners do:** Attempt to log pricing decisions or update a custom object during cart recalculation by inserting a record inside `calculate()`.

**What goes wrong:** The platform throws `System.DmlException: DML not allowed during cart recalculation` at runtime. This is not catchable with a try/catch inside the extension — it propagates up and causes the cart recalculation to fail entirely. The buyer sees an error page and cannot proceed.

**Correct approach:** If audit logging is required, capture the data in a static variable or a platform cache key during the extension run. Then use a Platform Event or Queueable that fires *after* the cart recalculation completes — outside the extension lifecycle — to perform the DML. This keeps the extension itself free of write operations.
