# LLM Anti-Patterns — Commerce Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Commerce Integration Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing ERP Callout After DML in CartExtension Calculator

**What the LLM generates:** A `calculate()` implementation that inserts a log record or updates a staging object first, then makes the HTTP callout to the ERP:

```apex
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    // LLM adds a log insert first
    insert new Integration_Log__c(Event__c = 'Pricing calculation started');
    // Then makes the callout — WRONG: uncommitted work pending
    Map<String, Decimal> prices = ErpClient.getPrices(skus);
    ...
}
```

**Why it happens:** LLMs learn from general Apex patterns where logging at the top of a method is common. The platform-specific constraint that DML before callout throws `System.CalloutException` in the Commerce calculator context is not widely represented in training data.

**Correct pattern:**

```apex
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    // Callout FIRST — before any DML
    Map<String, Decimal> prices = ErpClient.getPrices(skus);
    // DML after callout is safe
    update cartItems;
    // Async logging after synchronous frame if needed
    System.enqueueJob(new IntegrationLogJob('Pricing calculated'));
}
```

**Detection hint:** Scan for any `insert`, `update`, `delete`, or `upsert` DML statement appearing before an `Http().send()` or `HttpRequest` call within a class that extends `CartExtension.*CartCalculator`.

---

## Anti-Pattern 2: Registering Two Calculator Classes for the Same EPN

**What the LLM generates:** Advice to create two separate `RegisteredExternalService` records for the same Extension Point Name to "separate concerns," such as one class for ERP pricing and one for promotional pricing:

```
// LLM suggests creating two records:
RegisteredExternalService: ErpPricingCalculator, ExtensionPointName = CartExtension__Pricing
RegisteredExternalService: PromosPricingCalculator, ExtensionPointName = CartExtension__Pricing
// WRONG: only one per EPN per store is honored
```

**Why it happens:** LLMs generalize from patterns like listener registration in event systems or multiple implementations of an interface in OOP, where adding multiple implementations is valid. The one-per-EPN constraint is Commerce-specific and not intuitive from general Apex knowledge.

**Correct pattern:**

```apex
// One registered class acts as a dispatcher
public class CompositePricingCalculator extends CartExtension.PricingCartCalculator {
    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        // Delegate to each concern in sequence
        new ErpPricingDelegate().apply(request.getCart());
        new PromotionPricingDelegate().apply(request.getCart());
    }
}
```

**Detection hint:** Look for two `RegisteredExternalService` metadata records targeting the same store with matching `ExtensionPointName` values.

---

## Anti-Pattern 3: Routing Raw Card Data Through Apex

**What the LLM generates:** A custom LWC payment form with card input fields that posts the card number, CVV, and expiry to an Apex REST endpoint for "server-side validation" before tokenizing:

```javascript
// LWC component — WRONG
const payload = {
    cardNumber: this.cardNumber,
    cvv: this.cvv,
    expiry: this.expiry
};
await fetch('/services/apexrest/PaymentValidation', {
    method: 'POST',
    body: JSON.stringify(payload)
});
```

**Why it happens:** LLMs trained on general web development patterns apply server-side validation patterns from non-PCI contexts. The PCI DSS requirement for client-side-only card capture through provider-hosted iframes is domain-specific and not generally represented in web dev training data.

**Correct pattern:**

```javascript
// LWC component — correct
// Card fields are rendered in gateway-hosted iframe; LWC only handles the token
handlePaymentAuthorization(event) {
    const { token } = event.detail; // Opaque token from provider iframe
    this.dispatchEvent(new CustomEvent('paymenttokenreceived', {
        detail: { token }
    }));
}
```

**Detection hint:** Look for LWC components with input fields named `cardNumber`, `cvv`, `pan`, `creditCard`, or similar that `@wire` or `callApex` to a payment-related Apex method. Raw card field names in any Apex method body are a red flag.

---

## Anti-Pattern 4: Using insert Instead of upsert for PIM Product Sync

**What the LLM generates:** A PIM sync batch that queries existing products by SKU and inserts new ones for any that were not found:

```apex
// WRONG — race condition, creates duplicates
List<Product2> existing = [SELECT Id, StockKeepingUnit FROM Product2
                           WHERE StockKeepingUnit IN :skus];
Map<String, Id> skuToId = new Map<String, Id>();
for (Product2 p : existing) skuToId.put(p.StockKeepingUnit, p.Id);

List<Product2> toInsert = new List<Product2>();
for (PimDto dto : incoming) {
    if (!skuToId.containsKey(dto.sku)) {
        toInsert.add(new Product2(Name = dto.name, StockKeepingUnit = dto.sku));
    }
}
insert toInsert; // Race: concurrent runs each miss the other's in-flight inserts
```

**Why it happens:** LLMs default to query-then-insert as the idiomatic deduplication pattern from general programming. The `Database.upsert()` with External ID pattern is Salesforce-specific and requires prior schema setup (defining the External ID field) that LLMs don't always assume.

**Correct pattern:**

```apex
// Correct — idempotent upsert on External ID
List<Product2> toUpsert = new List<Product2>();
for (PimDto dto : incoming) {
    toUpsert.add(new Product2(
        PIM_Product_Id__c = dto.pimId,   // External ID field
        Name              = dto.name,
        StockKeepingUnit  = dto.sku
    ));
}
Database.upsert(toUpsert, Product2.PIM_Product_Id__c, false);
```

**Detection hint:** Look for `insert Product2` statements in batch or integration code that are preceded by SOQL queries on `StockKeepingUnit`, `Name`, or other non-External-ID fields used as deduplication keys.

---

## Anti-Pattern 5: Assuming sfdc_checkout.CartPaymentAuthorize Is the Current Interface for LWR Stores

**What the LLM generates:** Apex that implements `sfdc_checkout.CartPaymentAuthorize` as the payment adapter for a modern B2B Commerce or D2C Commerce store built on the LWR runtime:

```apex
// WRONG for modern LWR-based stores
global class MyPaymentAdapter implements sfdc_checkout.CartPaymentAuthorize {
    global sfdc_checkout.IntegrationStatus startCartProcessAsync(
        sfdc_checkout.IntegrationInfo integInfo, Id cartId) {
        // ...
    }
}
```

**Why it happens:** `sfdc_checkout.CartPaymentAuthorize` has a long history in B2B Commerce documentation and many tutorials. LLMs trained on older documentation or blog posts about Aura-based B2B stores propose this interface for all Commerce payment integrations without distinguishing store runtime.

**Correct pattern:**

```apex
// Correct for modern LWR-based B2B and D2C stores
global class MyPaymentAdapter implements CommercePayments.PaymentGatewayAdapter {
    global CommercePayments.GatewayResponse processRequest(
            CommercePayments.PaymentGatewayContext context) {
        // Dispatch on context.getPaymentRequestType()
    }
}
```

**Detection hint:** Any new Apex class implementing `sfdc_checkout.CartPaymentAuthorize` in a project that describes a modern LWR-based B2B or D2C Commerce store should be flagged and redirected to `CommercePayments.PaymentGatewayAdapter`. The legacy interface is only correct for Aura-based B2B stores.

---

## Anti-Pattern 6: Hardcoding ERP or Tax Engine Credentials in Apex or Custom Settings

**What the LLM generates:** Apex callout code with credentials embedded as string constants, or instructions to store API keys in a Custom Setting field:

```apex
// WRONG — hardcoded credentials
String apiKey = 'sk_live_abc123xyz';
HttpRequest req = new HttpRequest();
req.setEndpoint('https://erp.example.com/api/prices');
req.setHeader('Authorization', 'Bearer ' + apiKey);
```

**Why it happens:** LLMs learn credential patterns from general REST API tutorials where hardcoding or environment variable patterns are common. Named Credentials are Salesforce-specific and their use in callouts requires knowing the `callout:` endpoint prefix pattern.

**Correct pattern:**

```apex
// Correct — Named Credential
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ERP_System/api/prices');
req.setMethod('POST');
// Credentials are managed in Setup > Named Credentials — not in code
```

**Detection hint:** Look for string literals that match API key patterns (long alphanumeric tokens, `Bearer`, `Basic`, or `api_key` in header values) in Apex files, or Custom Settings fields with names like `Api_Key__c`, `Secret__c`, `Password__c` used in callout setup.
