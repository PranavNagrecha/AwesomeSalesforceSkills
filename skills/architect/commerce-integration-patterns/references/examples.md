# Examples — Commerce Integration Patterns

## Example 1: ERP Real-Time Pricing with PricingCartCalculator

**Context:** A B2B Commerce merchant uses SAP as their ERP and needs customer-specific contract prices displayed in the storefront cart. The SAP pricing API accepts a customer account ID and a list of SKUs and returns negotiated prices per line item.

**Problem:** Without a custom calculator, the store falls back to Salesforce price book prices, which do not reflect ERP contract pricing. Attempts to update `CartItem` prices via a Flow-invoked action fail intermittently with `System.CalloutException` because Flow introduces uncommitted work before the callout window is open.

**Solution:**

```apex
public class SapPricingCalculator extends CartExtension.PricingCartCalculator {

    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartItemCollection items = cart.getCartItems();

        // Collect SKUs — no DML yet, callout window is open
        List<String> skus = new List<String>();
        for (Integer i = 0; i < items.size(); i++) {
            skus.add(items.get(i).getSku());
        }

        // Callout to SAP — safe because no prior DML in this frame
        Map<String, Decimal> sapPrices = SapPricingClient.getContractPrices(
            cart.getAccountId(), skus);

        // Write prices back after callout completes
        for (Integer i = 0; i < items.size(); i++) {
            CartExtension.CartItem item = items.get(i);
            String sku = item.getSku();
            if (sapPrices.containsKey(sku)) {
                item.setSalesPrice(sapPrices.get(sku));
                item.setTotalPrice(sapPrices.get(sku) * item.getQuantity());
            }
        }
    }
}
```

`RegisteredExternalService` custom metadata record:
```
DeveloperName:         SAP_Pricing_Calculator
ExtensionPointName:    CartExtension__Pricing
ExternalServiceProviderType: Extension
MasterLabel:           SAP Pricing Calculator
StoreIntegratedService: (reference to the target store's StoreIntegratedService ID)
```

**Why it works:** All HTTP callout logic is isolated within `calculate()` before any DML or platform-state mutations. The platform's callout window is open at the start of `calculate()` and remains open until the first DML operation. Writing prices back after the callout resolves keeps the method within the safe sequence.

---

## Example 2: PIM Product Sync Using Product2 External ID

**Context:** A D2C Commerce merchant runs Akeneo as their PIM. A nightly delta feed pushes updated product attributes (name, description, images, rich content) from Akeneo to Salesforce via a MuleSoft integration. The feed delivers ~5,000 product records per run.

**Problem:** The initial integration used `insert` for new products and a query-then-update pattern for existing products. Under concurrent sync runs (e.g., retry after a partial failure), the query-then-update logic missed in-flight records and created 2-3 duplicate `Product2` records per product. These duplicates associated with separate `PricebookEntry` records, causing incorrect pricing in the storefront.

**Solution:**

Define the External ID field in metadata:
```xml
<!-- force-app/main/default/objects/Product2/fields/Akeneo_Product_Id__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Akeneo_Product_Id__c</fullName>
    <label>Akeneo Product ID</label>
    <type>Text</type>
    <length>255</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
</CustomField>
```

Upsert job (invoked by the MuleSoft integration via REST Composite API or Apex batch):
```apex
public class AkeneoProductSyncBatch implements Database.Batchable<AkeneoProductDto> {

    public void execute(Database.BatchableContext bc, List<AkeneoProductDto> dtos) {
        List<Product2> toUpsert = new List<Product2>();
        for (AkeneoProductDto dto : dtos) {
            Product2 p = new Product2(
                Akeneo_Product_Id__c  = dto.akeneoId,    // External ID — drives upsert key
                Name                  = dto.name,
                Description           = dto.description,
                StockKeepingUnit      = dto.sku,
                IsActive              = dto.active,
                Family                = 'Product'
            );
            toUpsert.add(p);
        }
        // allOrNone = false — partial success allowed; log failures for retry
        Database.UpsertResult[] results =
            Database.upsert(toUpsert, Product2.Akeneo_Product_Id__c, false);

        for (Database.UpsertResult result : results) {
            if (!result.isSuccess()) {
                // Log to custom error object or Platform Event for monitoring
                ErrorLogger.log('AkeneoProductSync', result.getErrors());
            }
        }
    }
}
```

**Why it works:** `Database.upsert` with an External ID field is idempotent — running the same payload twice produces exactly one `Product2` record per `Akeneo_Product_Id__c` value. Concurrent runs that target the same record hit Salesforce's row-level locking rather than creating a second insert, eliminating the duplicate race condition.

---

## Example 3: Shipping Rate Callout with ShippingCartCalculator

**Context:** A B2B merchant needs real-time FedEx rates displayed as shipping options at checkout. Rates vary by delivery address and total cart weight.

**Problem:** Flat-rate shipping configured in Store Setup does not reflect actual carrier costs. A previous attempt to fetch rates via a custom checkout flow component introduced callout timing issues when the flow ran after the cart recalculation pipeline had already committed cart state.

**Solution:**

```apex
public class FedExShippingCalculator extends CartExtension.ShippingCartCalculator {

    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartDeliveryGroupCollection groups = cart.getCartDeliveryGroups();

        for (Integer i = 0; i < groups.size(); i++) {
            CartExtension.CartDeliveryGroup group = groups.get(i);

            // Build weight and address payload — no DML yet
            Decimal totalWeight = 0;
            CartExtension.CartItemCollection items = cart.getCartItems();
            for (Integer j = 0; j < items.size(); j++) {
                totalWeight += items.get(j).getQuantity()
                    * items.get(j).getProduct().getWeight();
            }

            // Callout within calculate() — safe
            List<FedExRate> rates = FedExRatingClient.getRates(
                group.getDeliverToAddress(), totalWeight);

            // Clear existing methods and add fetched rates
            CartExtension.CartDeliveryGroupMethodCollection methods =
                group.getCartDeliveryGroupMethods();
            methods.clear();
            for (FedExRate rate : rates) {
                CartExtension.CartDeliveryGroupMethod method =
                    new CartExtension.CartDeliveryGroupMethod(
                        rate.serviceName,
                        rate.price,
                        'FedEx');
                method.setCarrier('FedEx');
                methods.add(method);
            }
        }
    }
}
```

**Why it works:** Placing the FedEx callout inside `calculate()` before any DML on cart objects keeps the uncommitted-work state clean. Clearing existing delivery methods before adding new ones prevents stale rate options from prior calculation runs accumulating on the delivery group.

---

## Anti-Pattern: Placing ERP Callout After Cart DML

**What practitioners do:** Some implementations query cart items using SOQL, perform DML to update a staging object or log record, and then attempt the ERP callout later in the `calculate()` method body.

**What goes wrong:** The DML operation (even inserting a log record) marks the transaction as having uncommitted work. Any subsequent HTTP callout in the same synchronous execution context throws `System.CalloutException: You have uncommitted work pending.` The error surfaces as a generic checkout error with no clear attribution in logs.

**Correct approach:** Perform all HTTP callouts before any DML in the `calculate()` method. If logging is needed, use `System.enqueueJob()` to push the log to an async Queueable after the callout, or write to a `@future` method invoked after the calculate() returns.
