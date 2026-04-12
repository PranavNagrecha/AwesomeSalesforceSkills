---
name: commerce-integration-patterns
description: "Use this skill when designing or diagnosing end-to-end integration between Salesforce B2B or D2C Commerce and external systems — including ERP pricing/inventory, PIM product sync, payment gateways, shipping providers, tax engines, and order management systems (OMS). Covers CartExtension Apex namespace (PricingCartCalculator, ShippingCartCalculator, InventoryCartCalculator), RegisteredExternalService custom metadata, payment gateway architecture, and Product2 External ID patterns. NOT for generic Salesforce integration (platform events, Mulesoft, REST APIs unrelated to commerce), NOT for CommercePayments adapter implementation details (see apex/commerce-payment-integration), NOT for storefront UI or LWC development."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I connect my ERP to Salesforce Commerce for real-time pricing and inventory lookups during checkout?"
  - "I need to integrate a third-party tax engine or shipping rate provider into the Commerce cart calculate pipeline"
  - "My PIM system needs to sync product data into Salesforce Commerce without creating duplicate Product2 records"
  - "How do I register a custom CartExtension class for shipping calculation in a B2B or D2C store?"
  - "What is the correct way to make callouts from a CartExtension calculator without getting a System.CalloutException?"
  - "I need to design an OMS integration pattern for Salesforce Commerce order capture and fulfillment handoff"
tags:
  - commerce-cloud
  - CartExtension
  - payment-gateway
  - ERP
  - PIM
  - OMS
  - B2B-commerce
  - D2C-commerce
  - architect
  - RegisteredExternalService
inputs:
  - "Store type (B2B Commerce or D2C Commerce) and API version"
  - "Which external systems are in scope: ERP, PIM, payment gateway, shipping provider, tax engine, OMS"
  - "Whether real-time callouts are required or batch sync is acceptable for each integration point"
  - "Existing Apex codebase and any currently registered CartExtension classes"
  - "Whether Salesforce Order Management (SOM) is licensed for capture/refund handling"
outputs:
  - "Architecture decision record mapping each external system to the correct Commerce extension point"
  - "CartExtension Apex class stubs for pricing, shipping, or inventory calculators with callout phase guidance"
  - "RegisteredExternalService custom metadata record configuration for each extension point"
  - "Product2 External ID strategy for PIM sync and duplicate prevention"
  - "Payment gateway integration path recommendation (Salesforce Payments, AppExchange package, or custom adapter)"
  - "Recommended Workflow checklist for safe end-to-end integration design"
dependencies:
  - apex/commerce-payment-integration
  - admin/commerce-checkout-configuration
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Commerce Integration Patterns

This skill activates when an architect or developer needs to design or diagnose integration between Salesforce B2B or D2C Commerce and external systems. It covers the CartExtension Apex namespace that powers real-time pricing, shipping, inventory, and tax lookups during checkout, the payment gateway architecture pattern that keeps raw card data off Salesforce servers, and the Product2 External ID strategy for safe PIM synchronization.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm store type (B2B Commerce or D2C Commerce) and the API version — CartExtension namespace requires v55.0+.
- Identify which external systems are in scope for this engagement: ERP (pricing/inventory), PIM (product catalog), payment gateway, shipping carrier, tax engine, OMS/fulfillment.
- For each integration point, determine whether real-time synchronous callouts are acceptable or batch async sync is preferred. Synchronous callouts are only permitted in CartExtension before-phase hooks; after-phase callouts throw `System.CalloutException` at runtime.
- Verify whether Salesforce Order Management (SOM) is licensed. SOM handles payment capture and refund orchestration post-authorization; without it, the custom payment adapter or a third-party order system must own that lifecycle.
- Check whether any CartExtension classes are already registered for the store via `RegisteredExternalService` custom metadata — only one class per Extension Point Name (EPN) per store is permitted.

---

## Core Concepts

### CartExtension Apex Namespace and the Calculator Pipeline

The `CartExtension` Apex namespace is the primary integration surface for commerce checkout calculations. It provides abstract base classes that a developer extends to inject external pricing, shipping, inventory, or tax logic into the cart calculation pipeline:

| Base Class | Extension Point Name (EPN) | Purpose |
|---|---|---|
| `CartExtension.PricingCartCalculator` | `CartExtension__Pricing` | Override or supplement storefront price book pricing with ERP prices |
| `CartExtension.ShippingCartCalculator` | `CartExtension__Shipping` | Fetch real-time shipping rates from a carrier API |
| `CartExtension.InventoryCartCalculator` | `CartExtension__Inventory` | Check real-time stock availability from an ERP or WMS |
| `CartExtension.TaxCartCalculator` | `CartExtension__Taxes` | Calculate tax using an external tax engine (e.g., Avalara, Vertex) |

Each calculator class overrides a `calculate(CartExtension.CartCalculateCalculatorRequest request)` method. The platform invokes registered calculators in sequence during the cart calculation pipeline (triggered on cart page load, quantity changes, and checkout progression).

### RegisteredExternalService Custom Metadata

Connecting a CartExtension class to a store requires a `RegisteredExternalService` custom metadata record. This record ties a specific Apex class to an Extension Point Name (EPN) and a specific store. Critical constraint: **only one class may be registered per EPN per store**. Attempting to register a second class for the same EPN and store results in the second registration silently not being invoked. Always audit existing registrations before scaffolding a new calculator class.

The metadata record fields are:
- `DeveloperName` — unique API name for the registration
- `ExternalServiceProviderType` — set to `Extension`
- `ExtensionPointName` — one of the EPN constants (e.g., `CartExtension__Pricing`)
- `MasterLabel` — human-readable label
- `StoreIntegratedService` (relationship) — links to the specific store

### Callout Phase Constraint: Before vs After Hooks

CartExtension calculators expose two lifecycle hooks: `calculate()` (before-phase) and a post-calculation hook. **HTTP callouts to external systems are only permitted within the `calculate()` method (before-phase)**. If callout code executes in the after-phase hook, Salesforce throws `System.CalloutException: You have uncommitted work pending.` at runtime. This is one of the most common production incidents in Commerce integrations.

The pattern for safe callout placement:
1. Perform all external callouts in `calculate()` before any DML or SOQL that creates uncommitted work.
2. Store results in local variables within the method.
3. Write back to cart line items or delivery group records after callouts are complete and all HTTP responses are resolved.

### Payment Gateway Architecture

Salesforce Commerce does not accept raw card data. The payment flow is:
1. The storefront renders a provider-hosted iframe or redirect (owned by the payment gateway) that captures card details client-side.
2. The provider returns an opaque token or nonce.
3. The Commerce checkout passes the token to an Apex class — either implementing `sfdc_checkout.CartPaymentAuthorize` (legacy Aura B2B) or `CommercePayments.PaymentGatewayAdapter` (modern LWR stores) — which uses the token to call the gateway API.
4. Raw card data (PAN, CVV, expiry) never transits Salesforce servers at any point in this flow.

For modern LWR-based B2B and D2C stores, the full payment adapter implementation is covered by the `apex/commerce-payment-integration` skill. This skill covers the gateway selection decision and the SOM integration handoff.

### PIM Sync to Product2: No Native Connector

Salesforce Commerce has no out-of-the-box connector to an external Product Information Management (PIM) system. Product catalog data lives in the `Product2` standard object. The canonical pattern for safe PIM sync is:

1. **Define External IDs on Product2** — add a custom External ID field (e.g., `PIM_Product_Id__c`, type `Text`, marked as `External ID` and `Unique`) that holds the PIM system's canonical product identifier.
2. **Upsert using External ID** — when syncing from the PIM (via Apex, integration middleware, or Data Loader), use `upsert Product2 PIM_Product_Id__c` in Apex or the Upsert DML operation with the external ID field specified. This prevents duplicate `Product2` records when the same product is synced multiple times.
3. **Sync related objects** — `ProductCatalog`, `ProductCategory`, `ProductCategoryProduct`, and `PricebookEntry` records must be maintained in sync alongside `Product2`. A partial sync that updates `Product2` but not price book entries will result in stale storefront prices.

---

## Common Patterns

### Pattern: ERP Real-Time Pricing via PricingCartCalculator

**When to use:** The store must display ERP contract prices or customer-specific pricing during checkout rather than Salesforce price book prices.

**How it works:**

```apex
public class ErpPricingCalculator extends CartExtension.PricingCartCalculator {

    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartItemCollection items = cart.getCartItems();

        // Build the list of SKUs to look up
        List<String> skus = new List<String>();
        for (Integer i = 0; i < items.size(); i++) {
            skus.add(items.get(i).getSku());
        }

        // Callout is safe here — before any DML, inside calculate()
        Map<String, Decimal> erpPrices = ErpPricingService.getPrices(
            skus, cart.getAccountId());

        // Write prices back — after callout, before method exit
        for (Integer i = 0; i < items.size(); i++) {
            CartExtension.CartItem item = items.get(i);
            if (erpPrices.containsKey(item.getSku())) {
                item.setSalesPrice(erpPrices.get(item.getSku()));
            }
        }
    }
}
```

**Why not the alternative:** Using a Flow-invoked Apex action or a trigger on `CartItem` to fetch ERP prices introduces uncommitted-work DML before the callout window, causing `System.CalloutException` in many checkout sequences.

### Pattern: Shipping Rate Lookup via ShippingCartCalculator

**When to use:** The store must display real carrier rates (FedEx, UPS, DHL) rather than flat-rate or free-shipping options configured in Setup.

**How it works:**

```apex
public class CarrierShippingCalculator extends CartExtension.ShippingCartCalculator {

    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartDeliveryGroupCollection deliveryGroups =
            cart.getCartDeliveryGroups();

        for (Integer i = 0; i < deliveryGroups.size(); i++) {
            CartExtension.CartDeliveryGroup group = deliveryGroups.get(i);

            // Callout is safe here — within calculate(), before DML
            List<CarrierRate> rates = CarrierApiService.getRates(
                group.getDeliverToAddress(),
                cart.getCartItems());

            // Populate shipping options on the delivery group
            CartExtension.CartDeliveryGroupMethodCollection methods =
                group.getCartDeliveryGroupMethods();
            methods.clear();
            for (CarrierRate rate : rates) {
                CartExtension.CartDeliveryGroupMethod method =
                    new CartExtension.CartDeliveryGroupMethod(
                        rate.name, rate.price, rate.carrier);
                methods.add(method);
            }
        }
    }
}
```

**Why not the alternative:** Storing shipping rates in a custom object and querying it from checkout bypasses real-time carrier accuracy and requires a separate batch job to keep rates current — unworkable for weight- and zone-based pricing.

### Pattern: PIM Upsert Using External ID

**When to use:** A PIM system is the master for product data and must push updates into Salesforce Commerce without creating duplicates.

**How it works:**

```apex
// In a batch job or Platform Event handler receiving PIM delta feeds
List<Product2> toUpsert = new List<Product2>();
for (PimProductDto dto : incomingProducts) {
    Product2 p = new Product2(
        PIM_Product_Id__c = dto.pimId,   // External ID field
        Name              = dto.name,
        Description       = dto.description,
        StockKeepingUnit  = dto.sku,
        IsActive          = dto.active
    );
    toUpsert.add(p);
}
// Upsert on the External ID — inserts new, updates existing, no duplicates
Database.upsert(toUpsert, Product2.PIM_Product_Id__c, false);
```

**Why not the alternative:** Querying by SKU then deciding to insert or update in a trigger context introduces race conditions under high-volume parallel syncs and produces duplicate records when the query misses an in-flight insert.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Real-time ERP pricing during checkout | `CartExtension.PricingCartCalculator` with callout in `calculate()` | Only safe callout window in the cart pipeline |
| Real-time carrier shipping rates | `CartExtension.ShippingCartCalculator` with callout in `calculate()` | Same pipeline; one class per store per EPN |
| Real-time inventory during cart/checkout | `CartExtension.InventoryCartCalculator` with callout in `calculate()` | Prevents oversell; same EPN constraint applies |
| External tax engine (Avalara, Vertex) | `CartExtension.TaxCartCalculator` or tax provider AppExchange package | Custom calculator if no package available |
| PIM product sync | `Database.upsert` with External ID on Product2 | No native PIM connector; External ID prevents duplicates |
| Payment gateway (modern LWR store) | `CommercePayments.PaymentGatewayAdapter` (see `apex/commerce-payment-integration`) | Correct interface for LWR-based B2B/D2C stores |
| Payment gateway (legacy Aura B2B store) | `sfdc_checkout.CartPaymentAuthorize` (see `admin/commerce-checkout-configuration`) | Legacy interface — different extension model |
| Post-order capture/refund orchestration | Salesforce Order Management (SOM) if licensed; else custom OMS callout | SOM provides pre-built fulfillment workflow nodes |
| Batch product/price sync with no real-time requirement | Scheduled Apex or Data Loader upsert via External ID | Simpler and more reliable than event-driven sync for large catalogs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map external systems to extension points** — For each external system in scope (ERP, PIM, payment, shipping, tax, OMS), identify the correct Commerce extension point. Confirm which systems require synchronous real-time callouts during checkout vs. batch or async sync. Document the mapping before writing any code.
2. **Audit existing RegisteredExternalService registrations** — Query `RegisteredExternalService` custom metadata for the target store and confirm which EPNs already have registered classes. There is exactly one slot per EPN per store — do not scaffold a new class until you know whether you are replacing or extending existing logic.
3. **Scaffold CartExtension calculator classes** — For each EPN requiring a custom class, extend the appropriate base class (`PricingCartCalculator`, `ShippingCartCalculator`, `InventoryCartCalculator`, `TaxCartCalculator`). Stub the `calculate()` method to return safely before adding callout logic. Confirm the class compiles and the stub version can be registered without breaking checkout.
4. **Implement callouts within the before-phase only** — Add HTTP callout logic exclusively inside the `calculate()` method, before any DML or platform interactions that create uncommitted work. Use Named Credentials for all external endpoints. Test the callout in isolation with a mock before wiring to checkout.
5. **Create or update RegisteredExternalService records** — Deploy a `RegisteredExternalService` custom metadata record for each new calculator, linking it to the target store's `StoreIntegratedService`. Validate that the EPN is correctly specified — a typo in the EPN value silently disables the calculator.
6. **Implement PIM sync with External ID upsert** — Define External ID fields on `Product2` (and related catalog objects as needed). Implement the upsert job using `Database.upsert()` with the External ID field specified. Test with duplicate inputs to confirm idempotency.
7. **Validate end-to-end through a test order** — Walk a test order through the complete checkout flow: add to cart, pricing recalculation, shipping rate fetch, inventory check, tax calculation, payment authorization, and (if SOM is licensed) capture. Confirm each registered calculator is invoked and that no `System.CalloutException` or silent failures occur in the cart pipeline.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each CartExtension calculator class extends the correct base class for its EPN
- [ ] All HTTP callouts are placed within the `calculate()` method before any DML or uncommitted-work operations
- [ ] No more than one class is registered per EPN per store in `RegisteredExternalService` custom metadata
- [ ] All external credentials (ERP, shipping, tax engine APIs) are stored in Named Credentials — no hardcoded endpoints or keys
- [ ] Product2 External ID field is defined and upsert operations use it — no insert-after-query patterns that risk duplicates
- [ ] Raw card data never appears in Apex code, debug logs, or custom storage at any point in the payment flow
- [ ] Salesforce Order Management licensing is confirmed or a custom post-capture pattern is documented
- [ ] End-to-end test order completes without `System.CalloutException` or silent calculator failures

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **After-phase callouts throw System.CalloutException** — Placing HTTP callouts in any cart pipeline hook after the `calculate()` method (or after any DML that creates uncommitted work within `calculate()`) causes the platform to throw `System.CalloutException: You have uncommitted work pending.` This error can be intermittent depending on execution order, making it hard to reproduce in sandbox. Always perform all callouts before the first DML write in a `calculate()` invocation.
2. **One class per EPN per store — no exceptions** — Only one `RegisteredExternalService` record per Extension Point Name per store is honored. If a second class is registered for the same EPN and store, only one will be called (behavior is not guaranteed and may vary by release). This means a single calculator class must handle all logic for that EPN, including combining internal price book lookups with ERP callout results.
3. **Raw card data must never transit Salesforce** — The payment framework is built on the assumption that card capture happens entirely client-side via a provider-hosted iframe. Any design that routes PANs, CVVs, or expiry dates through Apex — even for logging or validation — violates PCI DSS scope and may trigger Salesforce compliance review. The Apex layer must only ever receive opaque tokens or nonces from the storefront.
4. **No native PIM connector — missing External ID causes duplicate Product2 records** — Salesforce Commerce has no built-in PIM integration. If PIM sync jobs use `insert` instead of `upsert` with an External ID field, each sync run creates new `Product2` records for existing products. Stale duplicates accumulate in the catalog, causing incorrect search results and pricing associations. Always define and populate an External ID on `Product2` before the first sync run.
5. **RegisteredExternalService EPN value is case-sensitive and must exactly match the platform constant** — A common scaffolding error is setting `ExtensionPointName` to a human-readable label (e.g., `Pricing`) instead of the correct platform constant (e.g., `CartExtension__Pricing`). The calculator silently never fires with no error surface in the UI.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration architecture decision record | Maps each external system (ERP, PIM, shipping, tax, OMS) to its Commerce extension point with rationale |
| CartExtension calculator Apex classes | One class per EPN, extending the correct base class, with callout logic in the before-phase only |
| RegisteredExternalService custom metadata records | One record per EPN per store, linking calculator class to the store via StoreIntegratedService |
| Product2 External ID field definition | Custom field definition and upsert job pattern for safe PIM synchronization |
| Named Credential configurations | Secure endpoint and credential storage for each external system API |
| Payment gateway integration recommendation | Decision between Salesforce Payments, AppExchange package, or custom CommercePayments adapter |

---

## Related Skills

- `apex/commerce-payment-integration` — for building custom `CommercePayments.PaymentGatewayAdapter` classes for modern LWR-based B2B and D2C stores
- `admin/commerce-checkout-configuration` — for legacy `sfdc_checkout.CartPaymentAuthorize` pattern, store checkout setup, and Payment Gateway Provider registration in Setup UI
- `apex/callouts-and-http-integrations` — for Named Credential configuration, callout patterns, and HTTP mock testing
- `architect/integration-admin-connected-apps` — for OAuth and connected app setup required for ERP/PIM integration authentication
