# LLM Anti-Patterns — Commerce LWC Components

Common mistakes AI coding assistants make when generating or advising on Commerce LWC components for B2B/D2C LWR storefronts.

## Anti-Pattern 1: Using `lightning/uiRecordApi` Instead of Commerce Storefront Adapters

**What the LLM generates:**
```javascript
import { getRecord } from 'lightning/uiRecordApi';
import NAME_FIELD from '@salesforce/schema/Product2.Name';
import PRICE_FIELD from '@salesforce/schema/Product2.UnitPrice';

@wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD, PRICE_FIELD] })
product;
```

**Why it happens:** LLMs are trained on large volumes of standard LWC tutorials and documentation where `lightning/uiRecordApi` is the canonical data access pattern. The LWR Commerce storefront context is a specialized runtime that the LLM treats as equivalent to standard Experience Cloud, leading it to apply the general-purpose LDS pattern.

**Correct pattern:**
```javascript
import { getProduct } from 'commerce/productApi';
import { getProductPrice } from 'commerce/productApi';

@wire(getProduct, { productId: '$recordId', fields: ['Name', 'Description'] })
product;

@wire(getProductPrice, { productId: '$recordId' })
price;
```

**Detection hint:** Look for any import from `lightning/uiRecordApi`, `lightning/uiObjectInfoApi`, or `lightning/uiListsApi` inside a component that also has `commerce/` imports or is described as a store component. These two namespaces should not coexist in a storefront component.

---

## Anti-Pattern 2: Omitting `lightningCommunity__RelaxedCSP` from Meta XML

**What the LLM generates:**
```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Page</target>
    </targets>
</LightningComponentBundle>
```

**Why it happens:** LLMs generate meta XML templates from standard Experience Cloud examples where `lightningCommunity__RelaxedCSP` is not required. The capability is a Commerce-specific requirement that appears infrequently in general LWC training data, so it is consistently omitted.

**Correct pattern:**
```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <capabilities>
        <capability>lightningCommunity__RelaxedCSP</capability>
    </capabilities>
    <targets>
        <target>lightningCommunity__Page</target>
    </targets>
</LightningComponentBundle>
```

**Detection hint:** Check every `.js-meta.xml` for a `<capabilities>` block containing `lightningCommunity__RelaxedCSP`. Its absence is a **defect for managed-package components** (Salesforce documents that those are disabled in the Experience Builder Components panel on any site with Locker disabled) and a **style finding for org-local components** — do not report the latter as a runtime failure, and do not attribute a component that renders incorrectly to this capability, since the documented symptom is the component being unavailable to place at all.

---

## Anti-Pattern 3: Calling Cart or Wishlist Mutations in Lifecycle Hooks

**What the LLM generates:**
```javascript
connectedCallback() {
    // pre-load cart on component mount
    addItemToCart({ productId: this.productId, quantity: 1 });
}
```
or:
```javascript
@wire(getProduct, { productId: '$recordId' })
handleProduct({ data }) {
    if (data) {
        addToWishlist({ productId: this.productId }); // auto-wishlist on data load
    }
}
```

**Why it happens:** LLMs apply general async JavaScript patterns where any async function can be called at any point in the component lifecycle. They do not model the storefront runtime's requirement that cart and wishlist mutations originate from synchronous user gesture handlers.

**Correct pattern:**
```javascript
// Mutations must be in user-interaction handlers
async handleAddToCart(event) {
    try {
        await addItemToCart({ productId: this.productId, quantity: this.quantity });
    } catch (e) {
        console.error('Cart mutation failed', e);
    }
}
```

**Detection hint:** Any call to `addItemToCart`, `removeItemFromCart`, `addToWishlist`, or `removeFromWishlist` outside a method that is directly bound to an `onclick`, `onkeydown`, or similar DOM event handler is suspect.

---

## Anti-Pattern 4: Using `Product2.FieldName` Format in `getProduct` Fields Parameter

**What the LLM generates:**
```javascript
@wire(getProduct, {
    productId: '$recordId',
    fields: ['Product2.Name', 'Product2.Description', 'Product2.StockKeepingUnit']
})
product;
```

**Why it happens:** LLMs learn the `ObjectName.FieldName` format from `lightning/uiRecordApi` usage patterns, where it is required. They apply this format to `getProduct` because the two adapters appear superficially similar — both take a record identifier and a list of fields to fetch.

**Correct pattern:**
```javascript
@wire(getProduct, {
    productId: '$recordId',
    fields: ['Name', 'Description', 'StockKeepingUnit']
})
product;
```

**Detection hint:** Any string in the `fields` array that contains a period (`.`) when passed to `commerce/productApi` adapters is using the wrong format. The Commerce Product API uses bare field API names without the object prefix.

---

## Anti-Pattern 5: Assuming Normal Locker / LWS Security Rules Apply

**What the LLM generates:** Code that relies on Locker-enforced DOM isolation (e.g., assuming `querySelector` cannot cross component boundaries, or that `eval` is blocked):
```javascript
// "Safe" because Locker blocks cross-component DOM access... except it doesn't in LWR
const siblingEl = document.querySelector('.product-price'); // works across component boundaries
```
Or conversely, code that assumes Locker's protections guard against XSS:
```javascript
// "Safe" because Locker sanitizes innerHTML... except it doesn't in LWR
this.template.querySelector('.description').innerHTML = this.product.data.fields.Description.value;
```

**Why it happens:** LLMs are trained predominantly on standard App Builder LWC examples where Locker or LWS is active. They apply Locker security assumptions to store components without recognizing that LWR storefronts run without these protections.

**Correct pattern:**
```javascript
// Explicit sanitization when rendering any untrusted content
import { sanitizeHtml } from 'your-sanitizer-util'; // use a vetted sanitization utility
get safeDescription() {
    return sanitizeHtml(this.product?.data?.fields?.Description?.value ?? '');
}
```
And never rely on DOM isolation: treat the storefront DOM as globally accessible by any component on the page.

**Detection hint:** Look for `innerHTML` assignment with data from wire adapters or `@api` properties without explicit sanitization. Also flag any comments or code that invokes Locker or LWS behavior as a security guarantee in a component deployed to a Commerce store.

---

## Anti-Pattern 6: Using Apex for Cart and Wishlist Operations That Have Commerce API Coverage

**What the LLM generates:**
```javascript
import addToCartApex from '@salesforce/apex/CartController.addItemToCart';

async handleAddToCart() {
    await addToCartApex({ productId: this.productId, quantity: this.quantity });
}
```

**Why it happens:** LLMs default to Apex for any data mutation because it is the general-purpose Salesforce data modification mechanism. They are not aware that Commerce provides first-class JavaScript APIs for cart and wishlist operations that are session-aware and do not require custom Apex.

**Correct pattern:**
```javascript
import { addItemToCart } from 'commerce/cartApi';

async handleAddToCart() {
    await addItemToCart({ productId: this.productId, quantity: this.quantity });
}
```

**Detection hint:** Any Apex import in a Commerce storefront component that handles cart operations (`addItem`, `removeItem`, `updateQuantity`) or wishlist operations (`addToWishlist`, `removeFromWishlist`) should be replaced with the equivalent `commerce/cartApi` or `commerce/wishlistApi` function. Custom Apex is only appropriate for operations with no Commerce API equivalent.

---

## Anti-Pattern: Over-scoping `lightningCommunity__RelaxedCSP` and inventing its failure mode

**What the LLM generates:**

> "Every custom LWC deployed to a Commerce store must declare `lightningCommunity__RelaxedCSP`. This is not optional. Without it the component may render inconsistently across store pages or fail silently on cart and checkout pages — the LWR runtime enforces the capability check differently per page type."

**Why it happens:** The capability is real, the LWS/Locker framing around it is right, and only the **scope** and the **symptom** are invented — which is why it reads so convincingly. Two pressures produce it. First, safety inflation: "required for managed packages" is weaker and more conditional than "required, not optional," and guidance drifts toward the stronger form because the stronger form is never *wrong* to follow. Second, symptom invention: a rule needs a consequence to be memorable, and "renders inconsistently on cart and checkout pages" is a far more vivid consequence than the real one, so it gets filled in. The per-page-type enforcement mechanism is pure confabulation — there is no such thing.

**Correct version:** Salesforce documents exactly one effect: *"Lightning web components in a managed package that aren't configured with the `lightningCommunity__RelaxedCSP` tag are disabled in the Components panel in Experience Builder for any site with Lightning Locker disabled."* Managed-package components only; the symptom is **unavailability at design time**, not misbehaviour at runtime. Declaring it on org-local components is harmless and fine as a house convention — just do not call it mandatory, and never diagnose a rendering bug as a missing `RelaxedCSP`, because a component missing this tag never gets onto the page to render badly.

**Detection hint:** grep for `RelaxedCSP` near `render`, `runtime`, `checkout`, or `silently` — the documented symptom is about the **Components panel**, so any runtime symptom attached to it is invented. Generalisable pair: (1) **"this is not optional" without a quoted source** usually marks a conditional requirement that has been hardened; (2) when guidance names a failure mode that varies by page type, environment, or record type without citing the rule that varies, treat the variation as fabricated — invented symptoms are more often *specific* than vague, because specificity is what makes them feel remembered.
