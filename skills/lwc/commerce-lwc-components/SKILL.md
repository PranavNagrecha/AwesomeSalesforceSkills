---
name: commerce-lwc-components
description: "Use this skill when building or customizing Lightning Web Components for B2B Commerce or D2C LWR storefronts — product display tiles, cart line-item components, checkout step components, wishlist buttons, and product comparison widgets. NOT for standard LWC outside a Commerce store or Aura Community Builder components — use lwc/experience-cloud-lwc-components."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Operational Excellence
triggers:
  - "How do I build a custom product card component for my B2B Commerce LWR store?"
  - "Wire adapter for cart data in a custom LWC inside Experience Cloud commerce store"
  - "Custom checkout step component not receiving product or cart state in D2C storefront"
  - "lightningCommunity__RelaxedCSP capability required for commerce LWC component"
  - "How to display wishlist state in a custom LWC in Salesforce Commerce storefront"
tags:
  - commerce-lwc-components
  - b2b-commerce
  - d2c-commerce
  - lwr-storefront
  - wire-adapters
  - commerce-namespace
  - storefront-api
  - experience-cloud
inputs:
  - "Store type: B2B Commerce or D2C (determines available wire adapters)"
  - "Component role: product display, cart, checkout step, wishlist, or comparison"
  - "Target LWR store template name and Experience Builder slot where component will be placed"
  - "Org Salesforce version (wire adapter availability varies by release)"
outputs:
  - "LWC component bundle (JS, HTML, meta XML) with correct commerce namespace wire adapter imports"
  - "Component meta XML with lightningCommunity__RelaxedCSP capability declared where needed"
  - "Guidance on registering the component in Experience Builder and exposing design properties"
  - "Validation checklist confirming adapter usage, CSP declaration, and deployment path"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Commerce LWC Components

Use this skill when an LWC component must read or mutate product, cart, wishlist, or checkout data inside a B2B Commerce or D2C LWR storefront. It covers Commerce Storefront wire adapters (`commerce/*` modules), CSP capability requirements, Experience Builder registration, and SFDX deployment of storefront components.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Store type and template name.** B2B Commerce and D2C stores expose overlapping but non-identical wire adapters. Confirm which store template is in use (`b2b` vs `b2c`/`d2c`) before choosing adapters.
- **Salesforce release.** Commerce Storefront wire adapters have been expanded across releases. Adapters like `getCartItems` (from `commerce/cartApi`) and `getProduct` (from `commerce/productApi`) have had breaking changes between Winter and Summer releases. Always confirm adapter availability for the target org version.
- **LWS vs Locker status.** LWR-based store templates run with both Lightning Web Security (LWS) and Lightning Locker disabled. Components behave differently from App Builder LWC: `eval`, cross-origin iframes, and some DOM globals that are blocked in standard LWC contexts may be available — but security must be implemented explicitly rather than relying on the framework enforcing it.
- **Deployment path.** Commerce storefront components are deployed via SFDX metadata (not Change Sets). The component must be in `force-app/main/default/lwc/` and surfaced in Experience Builder via the component meta XML.

---

## Core Concepts

### Commerce Storefront Wire Adapters (`commerce/*`)

Custom LWC components in B2B/D2C LWR stores bind to product, cart, and wishlist data using wire adapters imported from the `commerce` namespace — for example `commerce/productApi`, `commerce/cartApi`, `commerce/wishlistApi`. These are NOT the same as `lightning/uiRecordApi` or `lightning/uiObjectInfoApi`. Using standard LDS adapters inside a store component will either silently return no data or throw import errors at runtime, because LDS is not available in the LWR storefront rendering context.

Wire adapters from the `commerce` namespace resolve store context automatically: the component does not need to pass a store ID or buyer group ID — these come from the runtime storefront context injected by the LWR framework.

Key adapters:
- `getProduct` from `commerce/productApi` — resolves product fields, pricing, and media for a given product ID.
- `getCartItems` and `addItemToCart` from `commerce/cartApi` — reads cart line items and mutates the active cart.
- `getWishlist` and `addToWishlist` from `commerce/wishlistApi` — reads and modifies the buyer's wishlist.
- `getProductPrice` from `commerce/productApi` — resolves negotiated and list prices for a buyer's account.

### lightningCommunity__RelaxedCSP Capability

LWR storefront templates disable both Lightning Locker and Lightning Web Security. The `lightningCommunity__RelaxedCSP` capability, declared in the `capabilities` array of the `.js-meta.xml`, signals that a component was authored knowing those sandbox protections are absent.

**Know the documented scope, because it is narrower than commonly stated.** Salesforce's rule is: "Lightning web components **in a managed package** that aren't configured with the `lightningCommunity__RelaxedCSP` tag are disabled in the Components panel in Experience Builder for any site with Lightning Locker disabled." So:

- It is a hard requirement for components **distributed in a managed package**. Without it, an admin cannot drag them onto a page at all.
- The documented symptom is **absence from the Experience Builder Components panel** — not inconsistent rendering, not silent page-type-specific failure at runtime. If a component is on the page and rendering wrongly, `RelaxedCSP` is the wrong hypothesis and chasing it will burn a debugging session.
- For a component in the org's **own namespace**, it is not a documented requirement. Declaring it anyway is harmless and is a reasonable house convention for storefront work — just do not describe it as mandatory or attribute unrelated runtime failures to its absence.

### Experience Builder Registration and Design Properties

A component must be exposed in Experience Builder to be drag-and-droppable onto store pages. This requires:
1. Setting `isExposed: true` in the `.js-meta.xml`.
2. Declaring at least one target inside `<targets>` — typically `lightningCommunity__Page` or a specific Commerce store page target.
3. Optionally declaring `<targetConfigs>` to expose design-time properties (e.g., product tile image size) that store admins can configure per page.

Components registered without the correct `<targets>` entries will not appear in the Experience Builder component panel even if the metadata deployment succeeds.

---

## Common Patterns

### Pattern 1: Product Display Tile with Storefront Wire Adapter

**When to use:** Building a custom product card that shows product name, image, description, and negotiated price inside a B2B or D2C LWR store product list page.

**How it works:**

```javascript
// productTile.js
import { LightningElement, api, wire } from 'lwc';
import { getProduct } from 'commerce/productApi';
import { getProductPrice } from 'commerce/productApi';

export default class ProductTile extends LightningElement {
    @api recordId; // product ID passed by the store page

    @wire(getProduct, { productId: '$recordId', fields: ['ProductCode', 'Description', 'Name'] })
    product;

    @wire(getProductPrice, { productId: '$recordId' })
    price;

    get productName() {
        return this.product?.data?.fields?.Name?.value;
    }

    get negotiatedPrice() {
        return this.price?.data?.negotiatedPrice;
    }
}
```

The `.js-meta.xml` must include:
```xml
<capabilities>
    <capability>lightningCommunity__RelaxedCSP</capability>
</capabilities>
<targets>
    <target>lightningCommunity__Page</target>
</targets>
```

**Why not the alternative:** Using `@wire(getRecord, { recordId: '$recordId', fields: [...] })` from `lightning/uiRecordApi` will not work. The LWR storefront runtime does not load LDS modules, so the adapter returns no data and no error, silently breaking the component.

### Pattern 2: Cart Mutation with Imperative Call

**When to use:** Building an "Add to Cart" button that adds a product and quantity to the active buyer cart.

**How it works:**

```javascript
// addToCartButton.js
import { LightningElement, api } from 'lwc';
import { addItemToCart } from 'commerce/cartApi';

export default class AddToCartButton extends LightningElement {
    @api productId;
    @api quantity = 1;

    async handleAddToCart() {
        try {
            await addItemToCart({ productId: this.productId, quantity: this.quantity });
            this.dispatchEvent(new CustomEvent('cartupdate'));
        } catch (e) {
            // surface error to buyer UI
            console.error('Add to cart failed', e);
        }
    }
}
```

`addItemToCart` is an imperative function, not a wire adapter. It returns a Promise and must be called inside a user-interaction handler. Do not call it during `connectedCallback` or a wire handler — cart mutations triggered outside user gestures may be blocked by the storefront security context.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Reading product data for display | `@wire(getProduct, ...)` from `commerce/productApi` | Declarative binding; store context auto-injected |
| Reading negotiated price for a buyer | `@wire(getProductPrice, ...)` from `commerce/productApi` | Price depends on buyer account; standard LDS has no price concept |
| Adding or removing cart items | Imperative `addItemToCart` / `removeItemFromCart` from `commerce/cartApi` | Mutations must be user-triggered; wire is read-only |
| Displaying wishlist state | `@wire(getWishlist, ...)` from `commerce/wishlistApi` | Wishlist is buyer-scoped; standard LDS cannot resolve it |
| Component not showing in Experience Builder | Verify `isExposed: true` and correct `<targets>` in `.js-meta.xml` | Registration issue, not a code issue |
| Managed-package component missing from the Experience Builder Components panel | Add `lightningCommunity__RelaxedCSP` capability to meta XML | Documented: managed-package LWCs without the tag are disabled in the panel on any site with Locker disabled |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm store type and target page.** Identify whether the store is B2B Commerce or D2C, and which page type the component will be placed on (product detail page, cart page, checkout step, etc.). This determines which `commerce/*` adapters are available and which Experience Builder page targets to register.
2. **Select the correct Commerce wire adapters.** Import from `commerce/productApi`, `commerce/cartApi`, or `commerce/wishlistApi` as appropriate. Do not use `lightning/uiRecordApi` or `lightning/uiObjectInfoApi` — these modules are unavailable in the LWR storefront runtime.
3. **Scaffold the LWC bundle.** Create the `.html`, `.js`, and `.js-meta.xml` files. In the JS, wire or import from the correct `commerce/*` module. Expose reactive getters for template binding rather than accessing `.data` directly in the template.
4. **Configure the meta XML correctly.** Set `isExposed: true`, add `lightningCommunity__RelaxedCSP` to `<capabilities>`, and add the correct `<targets>` entry. Expose design-time properties via `<targetConfigs>` if store admins need to configure the component.
5. **Deploy via SFDX.** Run `sfdx force:source:push` or `sf project deploy start` targeting the store org. Verify the component appears in Experience Builder under Custom Components.
6. **Test in Experience Builder preview and live store.** CSP and adapter behavior can differ between Builder preview mode and live store rendering. Always test in both contexts before release.
7. **Validate and review.** Run `python3 scripts/check_commerce_lwc_components.py --manifest-dir force-app/main/default/lwc/` to catch missing CSP declarations and incorrect adapter imports.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All wire adapters imported from `commerce/*` modules, not `lightning/uiRecordApi` or `lightning/uiObjectInfoApi`
- [ ] `.js-meta.xml` includes `<capability>lightningCommunity__RelaxedCSP</capability>`
- [ ] `.js-meta.xml` has `isExposed: true` and at least one valid `<target>` entry
- [ ] Cart and wishlist mutations are imperative function calls inside user-interaction handlers, not wire reactive properties
- [ ] Component tested in both Experience Builder preview and live store page
- [ ] No hardcoded store IDs, buyer group IDs, or catalog IDs — context is injected by the LWR runtime

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing `lightningCommunity__RelaxedCSP` hides managed-package components from the Components panel** — the documented consequence is that managed-package LWCs without the tag are *disabled in the Experience Builder Components panel* on any site with Locker disabled, so an admin cannot place them at all. It is not a runtime rendering failure, and the distinction matters for triage: if the component is already on the page, this capability is not your bug. Declaring it on org-local storefront components is harmless convention, not a documented requirement.
2. **`getProduct` fields list is not free-form** — The `fields` parameter for `getProduct` must use field names in the exact format expected by the Commerce Product API, not the same format as `lightning/uiRecordApi`. For example, `Name` works but `Product2.Name` does not. Passing unsupported field names silently returns `undefined` for those fields rather than throwing an error.
3. **LDS is unavailable; `@wire(getRecord)` returns no data and no error** — In the LWR storefront runtime, `lightning/uiRecordApi` adapters are not loaded. A wire adapter imported from `lightning/uiRecordApi` will resolve its import successfully at compile time but never deliver data at runtime, producing no JavaScript error. This means a developer testing in App Builder will see data but a buyer in the store will see a blank component.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `<componentName>.js` | LWC controller with `commerce/*` wire adapter imports and reactive getters |
| `<componentName>.html` | Template referencing reactive getter properties, not raw `.data` access |
| `<componentName>.js-meta.xml` | Meta XML with `lightningCommunity__RelaxedCSP`, `isExposed: true`, and correct `<targets>` |
| Deployment confirmation | Output of `sf project deploy start` confirming component is registered in the store org |

---

## Related Skills

- `lwc/wire-service-patterns` — use for standard LWC wire service patterns outside the Commerce storefront context
- `admin/b2c-commerce-store-setup` — use when setting up the B2C store configuration before building custom components
- `integration/commerce-order-api` — use when a custom component must trigger order placement or order management operations beyond cart mutations