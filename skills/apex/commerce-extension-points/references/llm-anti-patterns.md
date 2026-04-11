# LLM Anti-Patterns — Commerce Extension Points

Common mistakes AI coding assistants make when generating or advising on Commerce Extension Points.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using @future or enqueueJob Inside a Cart Calculator

**What the LLM generates:** An `@future` method call or `System.enqueueJob()` inside `calculate()` to offload slow logic such as an ERP lookup or audit log write.

```apex
// WRONG — will throw System.AsyncException at runtime
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    doExpensiveWork(request.getCart().getCartId()); // calls @future method
}

@future(callout=true)
private static void doExpensiveWork(String cartId) { ... }
```

**Why it happens:** LLMs trained on trigger-based Apex code associate "expensive logic that shouldn't block the transaction" with `@future` methods and queueable chains. The same pattern is valid in trigger handlers but categorically invalid inside Commerce extensions.

**Correct pattern:**

```apex
// CORRECT — all logic must be synchronous inside calculate()
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    // Do synchronous work only.
    // To defer non-critical side effects, publish a Platform Event here —
    // that is permitted and the subscriber executes asynchronously outside the pipeline.
}
```

**Detection hint:** Any occurrence of `@future`, `System.enqueueJob(`, `Database.executeBatch(`, or `Messaging.sendEmail(` inside a method that is called (directly or transitively) from `calculate()`.

---

## Anti-Pattern 2: DML Inside a Hook Method

**What the LLM generates:** An insert or update statement inside `calculate()` to persist audit data, update a cart-adjacent object, or populate a custom reporting record.

```apex
// WRONG — throws System.DmlException at runtime
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    CartExtension.Cart cart = request.getCart();
    // ... pricing logic ...
    insert new PricingAuditLog__c(CartId__c = cart.getCartId(), ...);
}
```

**Why it happens:** In most Apex contexts (triggers, batch, queueable), DML is the standard way to persist data. LLMs generalize this to Commerce extension contexts without recognizing the pipeline restriction.

**Correct pattern:**

```apex
// CORRECT — use Platform Events to defer DML outside the extension lifecycle
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    CartExtension.Cart cart = request.getCart();
    // ... pricing logic ...
    // Publish Platform Event — permitted; subscriber handles DML asynchronously
    EventBus.publish(new PricingCalculated__e(CartId__c = cart.getCartId()));
}
```

**Detection hint:** Any `insert`, `update`, `delete`, `upsert`, `Database.insert(`, `Database.update(`, or `Database.upsert(` statement inside a method reachable from `calculate()`.

---

## Anti-Pattern 3: Placing a Callout in an After Hook

**What the LLM generates:** An HTTP callout inside an after-phase hook to validate or log data after pricing has been written, without distinguishing between before and after hook lifecycle phases.

```apex
// WRONG — after hook, callout will throw System.CalloutException at runtime
public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
    // This method is an after-phase hook
    HttpRequest req = new HttpRequest();
    req.setEndpoint(callout:ExternalSystem/validate);
    ...
    new Http().send(req); // throws CalloutException
}
```

**Why it happens:** LLMs may not distinguish between before and after lifecycle phases within the Commerce extension model, treating all `calculate()` methods as equivalent entry points.

**Correct pattern:**

Identify whether the base class method is a before or after hook by consulting the `CartExtension` Apex namespace documentation. Place all callouts in before-phase methods only. Redesign after-phase logic to avoid callouts — use the data already available in the `CartCalculateCalculatorRequest` object.

**Detection hint:** Any `new Http().send(`, `HttpRequest`, or `callout:` Named Credential reference inside a method identified in the CartExtension documentation as an after-phase hook.

---

## Anti-Pattern 4: Incorrect or Approximate EPN String

**What the LLM generates:** A `RegisteredExternalService` metadata record with an EPN string that is close but not exact — for example, using a human-readable variant or a string from a different release.

```xml
<!-- WRONG — EPN is not a valid platform string -->
<values>
    <field>ExtensionPointName</field>
    <value xsi:type="xsd:string">CommercePricingCartCalculator</value>
</values>

<!-- ALSO WRONG — lowercase, hyphenated variant -->
<values>
    <field>ExtensionPointName</field>
    <value xsi:type="xsd:string">commerce-domain-pricing-cart-calculator</value>
</values>
```

**Why it happens:** LLMs infer EPN strings from naming conventions or partial training data rather than using the exact documented constant. Because there is no deploy-time validation of the EPN value, the error never surfaces explicitly.

**Correct pattern:**

```xml
<!-- CORRECT — exact EPN string from official documentation -->
<values>
    <field>ExtensionPointName</field>
    <value xsi:type="xsd:string">Commerce_Domain_Pricing_CartCalculator</value>
</values>
```

**Detection hint:** Any `ExtensionPointName` value that uses hyphens, camelCase, or does not start with `Commerce_Domain_`.

---

## Anti-Pattern 5: Extending the Wrong CartExtension Base Class

**What the LLM generates:** A pricing calculator that extends `CartExtension.CartCalculate` (the generic base) instead of `CartExtension.PricingCartCalculator`, or vice versa — or extends a non-existent class name hallucinated from the `CartExtension` namespace.

```apex
// WRONG — generic base class for pricing work; EPN may not wire correctly
public class MyCalculator extends CartExtension.CartCalculate { ... }

// ALSO WRONG — hallucinated class name
public class MyCalculator extends CartExtension.PricingExtension { ... }
```

**Why it happens:** LLMs conflate the generic `CartExtension.CartCalculate` base class with the specialized `CartExtension.PricingCartCalculator`, or hallucinate class names based on namespace conventions. In some cases, the code compiles if the generic base is used, but the `RegisteredExternalService` EPN mapping does not wire correctly and the extension fires in the wrong pipeline phase.

**Correct pattern:**

```apex
// CORRECT — extend the specific base class that matches the EPN
public class MyPricingCalculator extends CartExtension.PricingCartCalculator {
    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        // pricing logic
    }
}
```

**Detection hint:** Verify the extended class name against the official `CartExtension` Apex namespace reference. For pricing, the correct base class is `CartExtension.PricingCartCalculator`. Cross-check that the base class used in the Apex matches the `ExternalServiceProviderType` in the `RegisteredExternalService` record.

---

## Anti-Pattern 6: Missing or Mismatched ExternalServiceProviderType

**What the LLM generates:** A `RegisteredExternalService` record with `ExternalServiceProviderType` omitted, set to a generic value like `Apex`, or set to a value that does not match the extension category.

```xml
<!-- WRONG — incorrect provider type for a cart calculator -->
<values>
    <field>ExternalServiceProviderType</field>
    <value xsi:type="xsd:string">Apex</value>
</values>
```

**Why it happens:** LLMs may not have precise knowledge of the allowed values for `ExternalServiceProviderType` and default to a generic or invented value.

**Correct pattern:**

```xml
<!-- CORRECT — ExternalServiceProviderType for a cart calculator extension -->
<values>
    <field>ExternalServiceProviderType</field>
    <value xsi:type="xsd:string">CartCalculator</value>
</values>
```

**Detection hint:** `ExternalServiceProviderType` must use a platform-defined allowed value. For cart calculators the correct value is `CartCalculator`. Any other value results in the extension not firing.
