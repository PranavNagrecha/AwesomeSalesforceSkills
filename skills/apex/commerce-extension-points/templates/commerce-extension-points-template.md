# Commerce Extension Points — Work Template

Use this template when building or reviewing a Commerce extension point implementation.

## Scope

**Skill:** `commerce-extension-points`

**Request summary:** (describe what the user or task requires)

## Context Gathered

Answer these before writing any code:

- **Store type:** B2B / B2C / both
- **Store template:** LWR Managed Checkout / Aura Flow Builder Checkout
- **Extension Point Name (EPN):** (e.g., `Commerce_Domain_Pricing_CartCalculator`)
- **External callout needed?** Yes / No — if Yes, confirm it goes in a before hook
- **DML needed?** (must be No inside the hook — use Platform Events to defer if needed)
- **Existing RegisteredExternalService record for this EPN?** Yes / No — if Yes, update it rather than creating a new one

## Approach

Which extension base class applies?

- [ ] `CartExtension.PricingCartCalculator` — custom pricing logic
- [ ] `CartExtension.CartCalculate` (inventory base) — inventory validation
- [ ] Other `CartExtension` base class: ______________

Design decision: synchronous-only logic confirmed? (no `@future`, no `enqueueJob`, no DML)

## Implementation Checklist

- [ ] Apex class extends the correct `CartExtension` base class
- [ ] `calculate()` method override implemented
- [ ] No DML statements anywhere in the class reachable from `calculate()`
- [ ] No async calls (`@future`, `enqueueJob`, `executeBatch`) in the class
- [ ] HTTP callouts (if any) are in before-phase hooks only
- [ ] `RegisteredExternalService` metadata record authored with exact EPN string
- [ ] `ExternalServiceProviderType` set to `CartCalculator` (or appropriate value)
- [ ] `ExternalServiceProvider` field set to the exact Apex class name
- [ ] Test class written that directly invokes `calculate()` with mocked request
- [ ] Both Apex class and metadata record included in same deployment package
- [ ] No duplicate RegisteredExternalService records for the same EPN

## RegisteredExternalService Metadata Template

File name: `<DeveloperName>.RegisteredExternalService-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label><!-- Human-readable label --></label>
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
        <value xsi:type="xsd:string"><!-- Apex class name --></value>
    </values>
</CustomMetadata>
```

## Apex Class Structure Template

```apex
public class MyCartExtension extends CartExtension.PricingCartCalculator {

    // REQUIRED: override the calculate method
    // PROHIBITED: DML, @future, enqueueJob, executeBatch inside this method
    // CALLOUTS: allowed only if this is a before-phase hook
    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        CartExtension.Cart cart = request.getCart();
        CartExtension.CartItemCollection items = cart.getCartItems();

        // Example: iterate items and apply custom pricing
        for (Integer i = 0; i < items.size(); i++) {
            CartExtension.CartItem item = items.get(i);
            // Apply price via setter — no DML
            // item.setUnitAdjustedPrice(customPrice);
        }
    }
}
```

## Test Class Structure Template

```apex
@IsTest
private class MyCartExtensionTest {

    @IsTest
    static void testCalculateAppliesCustomPricing() {
        // Build a mock CartCalculateCalculatorRequest
        // (use CartExtension test factory methods if available in your API version)

        MyCartExtension ext = new MyCartExtension();
        // ext.calculate(mockRequest);

        // Assert expected price values on items
        // System.assertEquals(expectedPrice, item.getUnitAdjustedPrice());
    }
}
```

## Notes

(Record any deviations from the standard pattern and why — e.g., why a before hook was chosen over after, or why a Platform Event is used for side effects instead of direct DML.)
