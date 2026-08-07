# Gotchas — Commerce LWC Components

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LDS Wire Adapters Silently Return No Data in LWR Storefront Runtime

**What happens:** A component using `@wire(getRecord, ...)` or `@wire(getRelatedListRecords, ...)` from `lightning/uiRecordApi` compiles and deploys without errors. In Experience Builder preview the component may even show data if the previewer falls back to a non-LWR rendering context. In the live store, the wire adapter never fires `data` or `error` — the component simply renders its empty/loading state indefinitely.

**When it occurs:** Any time a standard LDS adapter is imported in an LWC deployed to a B2B Commerce or D2C LWR store template. This affects all `lightning/uiRecordApi`, `lightning/uiObjectInfoApi`, `lightning/uiListsApi`, and `lightning/uiRelatedListApi` adapters.

**How to avoid:** Use only `commerce/*` wire adapters for product, pricing, cart, and wishlist data. For any data that does not have a Commerce Storefront adapter (e.g., custom object records), use an imperative Apex call with `@AuraEnabled(cacheable=true)` rather than an LDS wire adapter.

---

## Gotcha 2: Missing `lightningCommunity__RelaxedCSP` Disables Managed-Package Components in the Components Panel

**What happens:** A custom component renders correctly on the product list page and product detail page but fails to render on the cart page or checkout page. There is no JavaScript error in the browser console. The component simply does not appear in the page DOM.

**When it occurs:** When a **managed-package** LWC's `.js-meta.xml` does not include `lightningCommunity__RelaxedCSP` in the `<capabilities>` element and the target site has Lightning Locker disabled — which every B2B/D2C store template does. Salesforce documents the effect as the component being *disabled in the Components panel in Experience Builder*: it never reaches a page, so there is nothing to render. Components in the org's own namespace are not covered by this documented rule.

**How to avoid:** Declare `<capability>lightningCommunity__RelaxedCSP</capability>` in the `.js-meta.xml` of any LWC distributed in a managed package for Commerce stores — there it is mandatory. For org-local components it is a harmless house convention rather than a documented requirement, so declare it for consistency but do not treat its absence as the explanation for a runtime failure. The capability is a design-time registration signal, not a permission grant.

---

## Gotcha 3: `getProduct` `fields` Parameter Uses Non-Standard Field Name Format

**What happens:** A developer passes field names in the `Product2.FieldName` format (the format required by `lightning/uiRecordApi`) to the `fields` parameter of `getProduct` from `commerce/productApi`. The wire adapter resolves without error but returns `undefined` for the requested fields. Debugging is difficult because the wire `data` object is not null — it just lacks the expected field values.

**When it occurs:** When copying a `getRecord` pattern and adapting it to `getProduct` without consulting the Commerce Product API field name format. The Commerce adapter expects plain field API names (`Name`, `ProductCode`, `Description`, `StockKeepingUnit`) without the object prefix.

**How to avoid:** Use bare field API names with `getProduct`. Consult the B2B Commerce Developer Guide's product field reference for the exact supported field list for a given store type. Note that some standard Product2 fields are not surfaced through the Commerce wire adapter at all — they require a separate Apex call if they are truly needed.

---

## Gotcha 4: Cart and Wishlist Mutations Called Outside User Gesture Handlers Are Blocked

**What happens:** A component attempts to call `addItemToCart` or `addToWishlist` during `connectedCallback`, inside a wire handler, or in a `setTimeout` callback. The call either silently fails or throws a runtime error in the storefront security context.

**When it occurs:** When a developer treats Commerce mutation functions like standard async utilities rather than user-initiated operations. The LWR storefront runtime enforces that certain cart and wishlist mutations originate from a synchronous user gesture (click, keypress) to prevent automated cart manipulation.

**How to avoid:** Always call `addItemToCart`, `removeItemFromCart`, `addToWishlist`, and `removeFromWishlist` inside event handlers that are directly invoked by user interaction (e.g., `onclick`, `onkeydown`). Do not wrap them in `setTimeout`, call them from lifecycle hooks, or trigger them from wire handler callbacks.

---

## Gotcha 5: Component Deployed via Change Set Is Not Visible in Experience Builder

**What happens:** A Commerce LWC component deployed through a Change Set does not appear in the Experience Builder component panel, even after clearing browser cache and waiting for site publish.

**When it occurs:** When the developer uses a Change Set deployment workflow instead of SFDX metadata deployment. Commerce LWR storefront component registration requires the full SFDX metadata deployment pipeline (`sf project deploy start`) to correctly process the `.js-meta.xml` targets and update the component registry for the store.

**How to avoid:** Deploy Commerce storefront components using SFDX CLI (`sf project deploy start`) targeting the store org. Verify the deployment output confirms the LightningComponentBundle was processed. After deployment, open Experience Builder and check the Custom Components section — if the component is still absent, verify that `isExposed: true` is set and the `<targets>` include `lightningCommunity__Page` or the specific store page target.