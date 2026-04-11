---
name: commerce-extension-points
description: "Use this skill when extending Salesforce B2B/B2C Commerce Cloud behavior through Apex: building custom cart calculators, implementing pricing hooks, integrating inventory checks, or registering custom checkout extensions via the CartExtension Apex namespace and RegisteredExternalService metadata. NOT for standard LWC Commerce components, declarative store configuration, or Experience Builder page layouts — use admin/commerce-checkout-configuration for those."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - commerce
  - b2b-commerce
  - cart-calculator
  - CartExtension
  - pricing-hook
  - checkout-extension
  - RegisteredExternalService
triggers:
  - "custom cart calculator not applying pricing during checkout"
  - "how to extend Commerce Cloud pricing with Apex"
  - "RegisteredExternalService metadata for commerce extension point"
  - "cart recalculation extension DML not allowed error"
  - "B2B Commerce checkout extension point Apex class"
inputs:
  - Store type (B2B or B2C) and store template (LWR Managed Checkout vs. Aura Flow Builder Checkout)
  - Extension Point Name (EPN) the custom class must satisfy (e.g., Commerce_Domain_Pricing_CartCalculator)
  - Whether the extension needs to call an external system (determines before vs. after hook placement)
  - Current RegisteredExternalService metadata for the target store
  - Org API version and whether the CartExtension namespace classes are available
outputs:
  - Custom Apex class extending the correct CartExtension base class
  - RegisteredExternalService metadata record wiring the class to the correct EPN
  - Test class validating the extension without live cart recalculation
  - Deployment checklist for activating the extension in the target store
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Commerce Extension Points

Use this skill when you need to write Apex that customizes Salesforce Commerce Cloud cart calculation, pricing, or checkout behavior by implementing a class in the `CartExtension` namespace and registering it as a `RegisteredExternalService` metadata record. This skill covers the full lifecycle: selecting the correct extension point, implementing the synchronous Apex class, registering it, and validating it without triggering governor-limit failures in tests.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the store template.** LWR stores use the Managed Checkout model with extension points; Aura stores use Flow Builder checkout. Extension point Apex applies to LWR Managed Checkout only. Mixing the two causes the extension to be ignored at runtime with no explicit error.
- **Identify the exact Extension Point Name (EPN).** Each extension point has a specific string identifier (e.g., `Commerce_Domain_Pricing_CartCalculator`). Using an incorrect EPN string means the RegisteredExternalService record is created but never invoked.
- **Determine whether an external callout is needed.** Callouts are only permitted in `before`-phase hooks. If the extension needs to call an external system, it must run in a before hook. After hooks are callout-prohibited at the platform level; attempting one throws a `System.CalloutException` at runtime.
- **Confirm DML is not required inside the extension.** Cart extensions execute synchronously inline during cart recalculation. DML inside any cart extension hook triggers a `System.DmlException` with the message "DML not allowed during cart recalculation." All data changes must be deferred outside the extension call.
- **Check whether another extension is already registered for the same EPN and store.** Only one class can be registered per EPN per store. Registering a second one does not produce a conflict error at deploy time — the last deployed record silently wins, overriding the previous extension.

---

## Core Concepts

### CartExtension Apex Namespace

All B2B/B2C Commerce extension point classes live in the `CartExtension` Apex namespace, which is a platform-provided namespace — not a managed package. The core base class for pricing customization is `CartExtension.PricingCartCalculator`. To implement a custom pricing calculator, extend this class and override the `calculate` method:

```apex
public class MyPricingCalculator extends CartExtension.PricingCartCalculator {
    public override void calculate(CartExtension.CartCalculateCalculatorRequest request) {
        // custom pricing logic here — synchronous only, no DML, no @future
    }
}
```

Other extension points follow the same pattern: extend the appropriate `CartExtension` base class and override the lifecycle method. The namespace provides base classes for inventory, promotions, shipping, and taxes.

### Extension Registration via RegisteredExternalService Metadata

The link between an Apex class and the Commerce engine is established through `RegisteredExternalService` custom metadata. Each record specifies:

- **ExternalServiceProviderType**: the category of the extension (e.g., `CartCalculator`)
- **ExtensionPointName**: the EPN string that identifies the specific hook (e.g., `Commerce_Domain_Pricing_CartCalculator`)
- **ExternalServiceProvider**: the Apex class name implementing the extension

The metadata record is deployed as part of the org metadata, not configured through Admin UI. If the class name in `ExternalServiceProvider` does not match an existing Apex class that extends the correct base, the extension is silently skipped during cart recalculation.

### Synchronous Execution and Prohibited Operations

Cart extensions run synchronously and inline during the platform-managed cart recalculation pipeline. Two operations are categorically prohibited:

1. **DML inside extension hooks** — Any insert, update, delete, or upsert inside the `calculate` method or equivalent hook method throws `System.DmlException` immediately. This prohibition includes `Database.insert()` with `allOrNone=false`. Data writes must happen outside the extension, in a separate transaction.

2. **Asynchronous Apex** — Any call to `@future` methods, `System.enqueueJob()`, `Database.executeBatch()`, or `Messaging.sendEmail()` inside an extension hook triggers a `System.AsyncException` at runtime. The async call cannot be deferred to complete after the synchronous extension returns; the platform detects it immediately.

### Before Hooks vs. After Hooks

Extension points have lifecycle phases. Callouts to external HTTP endpoints are only permitted in before hooks — those that run before the platform writes the calculated values to the cart. After hooks execute in a context where the HTTP callout stack is closed. The distinction is enforced at runtime, not at compile time: code that calls `Http.send()` inside an after hook compiles and deploys successfully but throws `System.CalloutException` when the cart recalculates.

---

## Common Patterns

### Pattern: Custom Pricing Calculator

**When to use:** A business rule requires overriding or supplementing the default Commerce pricing logic — for example, applying customer-segment-specific prices from an external price list not managed in Salesforce price books.

**How it works:**
1. Create an Apex class extending `CartExtension.PricingCartCalculator`.
2. Override the `calculate(CartExtension.CartCalculateCalculatorRequest request)` method.
3. Access cart items via `request.getCart().getCartItems()`.
4. Set adjusted prices directly on each `CartExtension.CartItem` object using the provided setter methods — do not attempt DML.
5. Create a `RegisteredExternalService` metadata record pointing to the class with EPN `Commerce_Domain_Pricing_CartCalculator`.
6. Deploy both the class and the metadata record together.

**Why not the alternative:** Price book rules alone cannot model complex B2B pricing tiers or external price feed lookups. Standard Commerce pricing is a good fallback but cannot call an external system or apply conditional logic that depends on runtime cart state.

### Pattern: Inventory Check Before Checkout

**When to use:** Real-time inventory validation against an external warehouse management system is required before allowing the buyer to proceed to checkout.

**How it works:**
1. Create an Apex class extending the appropriate `CartExtension` inventory base class.
2. In the before hook method, perform an HTTP callout to the external WMS. Callouts are permitted in before hooks.
3. For each cart item, evaluate the inventory response and update the item's `CartValidationOutput` collection to report insufficient stock as a validation failure.
4. The Commerce engine reads the validation outputs and prevents checkout progress if failures are present. No DML is needed; all state changes go through the provided request/response objects.
5. Register via `RegisteredExternalService` with the inventory EPN.

**Why not the alternative:** Platform-side inventory (Salesforce Order Management stock) does not always reflect real-time WMS state, especially in high-velocity or multi-channel scenarios. The extension point is the only supported path for blocking checkout based on live external data.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Custom pricing from external system | Extend `CartExtension.PricingCartCalculator`, callout in before hook | Only supported pattern; callout permitted in before phase |
| Need to write records when cart recalculates | Defer DML to a separate transaction outside the extension | DML inside extension hooks throws `System.DmlException` |
| Need async processing during cart calculation | Not possible; all extension logic must be synchronous | `@future` and `enqueueJob` throw `System.AsyncException` inside hooks |
| Inventory check against external WMS | Use before hook with HTTP callout; report failures via `CartValidationOutput` | After hooks prohibit callouts; before hook is the correct phase |
| Multiple extensions needed for same EPN | Only one class per EPN per store is supported | Last deployed record wins; chain logic within a single class |
| Testing cart extension logic | Instantiate the class and call `calculate()` directly in test with a mock `CartCalculateCalculatorRequest` | Never trigger live cart recalculation in test context |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm store type and EPN** — Verify the store is LWR Managed Checkout. Identify the exact EPN string for the required extension (pricing, inventory, promotions, shipping, or tax). Check whether a `RegisteredExternalService` record already exists for this EPN and store.
2. **Design for synchronous constraints** — Map out every operation the extension will perform. Flag any DML, async calls, or after-hook callouts. Redesign the flow to eliminate them: push DML to a separate process, use before-hook phase for any HTTP callouts.
3. **Implement the Apex class** — Extend the correct `CartExtension` base class. Override the required lifecycle method. Use only the provided `CartExtension` API objects to read cart state and write results. Do not use SOQL queries inside the hot path if performance matters; cache lookups via static maps if the cart has many items.
4. **Create the RegisteredExternalService metadata** — Author the `.md-meta.xml` file specifying `ExternalServiceProviderType`, `ExtensionPointName`, and `ExternalServiceProvider` (the class name). Double-check spelling — EPN mismatches are silent at deploy time.
5. **Write test classes** — Instantiate the extension class in a test and invoke `calculate()` directly with a mocked request. Use `@TestVisible` private constructors on any helper if needed. Do not rely on a live cart to trigger the extension in tests.
6. **Deploy both artifacts together** — Include the Apex class and the `RegisteredExternalService` metadata in the same deployment. Deploying the metadata without the class results in a silent skip; deploying the class without the metadata means the extension is never invoked.
7. **Validate post-deployment** — Add a test item to a cart in the target store and confirm the extension fires. Check debug logs for the class name. Confirm no unhandled exceptions occur during the first real cart recalculation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Extension class extends the correct `CartExtension` base class for the target EPN
- [ ] No DML statements (insert/update/delete/upsert) inside any hook method
- [ ] No `@future`, `System.enqueueJob()`, `Database.executeBatch()`, or other async calls inside hook methods
- [ ] Callouts (if any) are in before-phase hooks only — none in after-phase hooks
- [ ] `RegisteredExternalService` metadata EPN string exactly matches the platform-defined constant (no typos)
- [ ] Test class invokes `calculate()` directly — does not rely on a live cart recalculation
- [ ] Both the Apex class and `RegisteredExternalService` metadata deployed in the same package/changeset
- [ ] Only one `RegisteredExternalService` record per EPN per store (no silent override conflicts)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **DML Inside Extension Causes Immediate Runtime Exception** — Any DML statement inside a cart calculator hook throws `System.DmlException` at runtime with the message "DML not allowed during cart recalculation." This does not appear at compile time or deploy time. Tests that bypass the live cart also bypass this check. The first indication of the problem is a failed cart recalculation in a live store or integration test that actually triggers the pipeline.
2. **EPN String Typo Is Silent** — If the `ExtensionPointName` field in the `RegisteredExternalService` record contains a typo or uses incorrect casing, the platform does not throw an error at deploy time and does not log a warning at runtime. The extension is simply never called. The correct EPN for pricing is exactly `Commerce_Domain_Pricing_CartCalculator`. Always copy the EPN from the official documentation rather than typing it manually.
3. **After-Hook Callout Exception** — HTTP callouts are permitted in before hooks but prohibited in after hooks. Code that calls `new Http().send()` in an after hook compiles and deploys successfully. The `System.CalloutException` only surfaces at runtime during cart recalculation. Moving the callout to the before hook phase resolves it.
4. **One Extension Per EPN Per Store** — Only one `RegisteredExternalService` record can be active per EPN per store. When a second record is deployed for the same EPN, the last deployed record silently wins. No error is raised, and the previously active extension stops firing without any notification. This is particularly dangerous during incremental deployments where a new version of the extension is deployed as a separate record rather than updating the existing one.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom `CartExtension` Apex class | Synchronous implementation of the target extension point with no DML and no async calls |
| `RegisteredExternalService` metadata | Custom metadata record linking the Apex class to the correct EPN and store |
| Extension test class | Unit test that invokes `calculate()` directly with mocked `CartExtension` API objects |

---

## Related Skills

- admin/commerce-checkout-configuration — declarative LWR store checkout configuration, managed checkout setup, and non-Apex extension setup; use before writing Apex to confirm the store template and extension model
- apex/callouts-and-http-integrations — HTTP callout patterns and error handling; relevant when the cart extension must call an external pricing or inventory API in a before hook
- admin/commerce-pricing-and-promotions — declarative price book and promotions setup; use to confirm whether the pricing requirement can be met declaratively before building a custom calculator
