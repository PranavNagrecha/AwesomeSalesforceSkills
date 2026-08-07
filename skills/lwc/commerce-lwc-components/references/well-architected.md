# Well-Architected Notes — Commerce LWC Components

## Relevant Pillars

- **Security** — LWR storefront templates disable Lightning Locker and Lightning Web Security. Without these sandboxes, a custom component has broader DOM access than standard LWC. The `lightningCommunity__RelaxedCSP` capability is a design-time declaration acknowledging this expanded context (required for managed-package components, conventional for org-local ones). Developers must sanitize any data rendered via `innerHTML` or injected into the DOM dynamically, since the framework no longer enforces it. Never expose internal buyer pricing, cart tokens, or session identifiers through public `@api` properties that could be accessed by third-party components on the same page.
- **Performance** — Commerce wire adapters cache data for the buyer session, but each additional wire adapter on a page adds a network round-trip on first load. Product tile components rendered in a grid should request only the minimum required fields through the `fields` parameter of `getProduct` to reduce payload size. Avoid chaining multiple wire adapters where a single adapter can serve the data need.
- **Operational Excellence** — Commerce LWC components are deployed via SFDX metadata and must be tracked in version control. Do not use declarative deployment (Change Sets) for storefront components. The component meta XML is the authoritative source for Experience Builder registration; changes to `isExposed`, `targets`, and `targetConfigs` must be committed and deployed together with the JS/HTML changes to avoid registry drift.

## Architectural Tradeoffs

**Commerce wire adapters vs. Apex calls:** Commerce Storefront wire adapters (`commerce/productApi`, `commerce/cartApi`, etc.) are the preferred data access pattern because they are session-aware, buyer-account-scoped, and managed by the platform. However, they only expose product, pricing, cart, and wishlist entities. Custom object data or complex cross-object queries still require Apex. When mixing Apex and Commerce adapters in a single component, ensure error states from both sources are handled independently — an Apex failure should not mask a Commerce adapter error.

**Wire adapters vs. imperative Commerce functions:** Use wire adapters for read operations (product data, cart state, wishlist state) and imperative calls for mutations (add to cart, remove wishlist item). Attempting to trigger mutations through wire adapter reactive properties causes unexpected behavior because wire adapters are designed for idempotent reads, not state-changing writes.

**Single-purpose components vs. monolithic store widgets:** Prefer composing small, single-purpose components (price display, add-to-cart button, wishlist toggle) over building a single large product detail component that handles all concerns. The LWR component composition model is well-suited to this pattern, and it makes Experience Builder configuration more granular for store admins.

## Anti-Patterns

1. **Using LDS wire adapters in storefront components** — Importing from `lightning/uiRecordApi` inside a Commerce LWC produces silent data failures in the live store. This is an architectural mismatch: LDS is a CRM data layer; Commerce Storefront wire adapters are the correct buyer-context data layer. Treat any use of `lightning/uiRecordApi` inside a store component as an automatic red flag.

2. **Shipping a managed-package storefront component without `lightningCommunity__RelaxedCSP`** — the component is disabled in the Experience Builder Components panel on any site with Locker disabled, so subscribers cannot place it and the failure surfaces as a support ticket rather than a build error. The architectural principle is: managed-package Commerce components declare it unconditionally, and org-local ones declare it for consistency — but neither should be blamed for a runtime rendering bug, which is a different failure class.

3. **Embedding store-specific IDs (store IDs, catalog IDs, buyer group IDs) as hardcoded constants** — The LWR storefront runtime injects store context automatically into Commerce wire adapters. Hardcoding IDs creates a maintenance burden and breaks when the component is reused across multiple stores or when a sandbox is refreshed. Design components to be context-agnostic and receive all store-specific configuration through `@api` properties or design-time `targetConfigs`.

## Official Sources Used

- Build Custom Components — B2B Commerce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_commerce_dev.meta/b2b_commerce_dev/b2b_comm_custom_components.htm
- Storefront APIs for Custom LWC — https://developer.salesforce.com/docs/atlas.en-us.b2b_commerce_dev.meta/b2b_commerce_dev/b2b_comm_storefront_apis.htm
- Commerce Cart and Wishlist APIs — https://developer.salesforce.com/docs/atlas.en-us.b2b_commerce_dev.meta/b2b_commerce_dev/b2b_comm_api_cart.htm
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- LWC Developer Guide — Configure a Component for Experience Builder (`lightningCommunity__RelaxedCSP` applies to managed-package components; symptom is being disabled in the Components panel; verified 2026-08-01) — https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-community-builder.html
- Lightning Web Security in LWR Sites — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/template_differences_locker.htm
