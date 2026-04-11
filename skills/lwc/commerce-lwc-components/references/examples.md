# Examples — Commerce LWC Components

## Example 1: Custom Product Price Display with Negotiated Pricing

**Context:** A B2B Commerce LWR store needs a custom product detail page widget that shows both the list price and the buyer's negotiated price. The standard store component does not visually distinguish the two, but the business requirement is to show savings prominently.

**Problem:** A developer scaffolds the component using `@wire(getRecord, { recordId: '$recordId', fields: ['Pricebook2.UnitPrice'] })` from `lightning/uiRecordApi`, which works in a sandbox App Builder context but shows nothing in the live B2B store because LDS is unavailable in the LWR storefront runtime.

**Solution:**

```javascript
// negotiatedPriceDisplay.js
import { LightningElement, api, wire } from 'lwc';
import { getProductPrice } from 'commerce/productApi';

export default class NegotiatedPriceDisplay extends LightningElement {
    @api recordId; // product ID — injected by store page context

    @wire(getProductPrice, { productId: '$recordId' })
    priceResult;

    get listPrice() {
        return this.priceResult?.data?.listPrice;
    }

    get negotiatedPrice() {
        return this.priceResult?.data?.negotiatedPrice;
    }

    get hasSavings() {
        const list = parseFloat(this.listPrice);
        const neg = parseFloat(this.negotiatedPrice);
        return !isNaN(list) && !isNaN(neg) && neg < list;
    }

    get savingsAmount() {
        return (parseFloat(this.listPrice) - parseFloat(this.negotiatedPrice)).toFixed(2);
    }
}
```

```html
<!-- negotiatedPriceDisplay.html -->
<template>
    <template if:true={priceResult.data}>
        <div class="price-block">
            <span class="list-price">List: {listPrice}</span>
            <span class="negotiated-price">Your Price: {negotiatedPrice}</span>
            <template if:true={hasSavings}>
                <span class="savings">You save: {savingsAmount}</span>
            </template>
        </div>
    </template>
</template>
```

```xml
<!-- negotiatedPriceDisplay.js-meta.xml -->
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

**Why it works:** `getProductPrice` from `commerce/productApi` is the Commerce Storefront wire adapter designed for buyer-scoped pricing. It resolves the buyer's account-level negotiated price directly from the storefront context without requiring a record ID lookup against Pricebook2. The `lightningCommunity__RelaxedCSP` capability ensures the component renders correctly on live store pages where LWS is disabled.

---

## Example 2: Custom Add-to-Wishlist Button

**Context:** A D2C LWR store wants a custom heart icon button on the product listing page that toggles the product in the buyer's wishlist. The standard wishlist button styling does not match the store's brand guidelines.

**Problem:** A developer attempts to use `@wire(getRecord)` to check wishlist membership or calls a custom Apex method to read and write wishlist data. Custom Apex is unnecessary because Commerce provides first-class wishlist APIs, and `getRecord` cannot resolve wishlist membership state.

**Solution:**

```javascript
// wishlistToggle.js
import { LightningElement, api, wire, track } from 'lwc';
import { getWishlist, addToWishlist, removeFromWishlist } from 'commerce/wishlistApi';

export default class WishlistToggle extends LightningElement {
    @api productId;
    @track isWishlisted = false;
    wishlistItemId = null;

    @wire(getWishlist)
    handleWishlist({ data, error }) {
        if (data) {
            const match = data.items?.find(item => item.productId === this.productId);
            this.isWishlisted = !!match;
            this.wishlistItemId = match?.id ?? null;
        }
    }

    async handleToggle() {
        try {
            if (this.isWishlisted && this.wishlistItemId) {
                await removeFromWishlist({ wishlistItemId: this.wishlistItemId });
                this.isWishlisted = false;
                this.wishlistItemId = null;
            } else {
                const result = await addToWishlist({ productId: this.productId });
                this.isWishlisted = true;
                this.wishlistItemId = result.id;
            }
        } catch (e) {
            console.error('Wishlist toggle failed', e);
        }
    }

    get iconName() {
        return this.isWishlisted ? 'utility:heart_filled' : 'utility:heart';
    }
}
```

```html
<!-- wishlistToggle.html -->
<template>
    <lightning-button-icon
        icon-name={iconName}
        alternative-text="Toggle Wishlist"
        onclick={handleToggle}
        variant="bare"
    ></lightning-button-icon>
</template>
```

**Why it works:** `getWishlist` from `commerce/wishlistApi` is a wire adapter that returns the buyer's full wishlist for the current store session. `addToWishlist` and `removeFromWishlist` are imperative functions called inside the click handler. This pattern avoids Apex entirely for standard wishlist operations and keeps the buyer session state correct. The component correctly stores the `wishlistItemId` returned by `addToWishlist` so that the subsequent remove call has the right item identifier.

---

## Anti-Pattern: Using Standard `lightning/uiRecordApi` Inside a Store Component

**What practitioners do:** Copy a working product display component from an App Builder page into the LWR store without changing the wire adapter imports. The component uses `@wire(getRecord, { recordId: '$recordId', fields: ['Name', 'Description'] })` from `lightning/uiRecordApi`.

**What goes wrong:** In the LWR storefront rendering context, `lightning/uiRecordApi` is not loaded. The wire adapter import resolves at compile time but the adapter never delivers data at runtime. The component renders an empty state with no JavaScript error in the console, making the bug extremely hard to diagnose. The developer typically suspects a CSP issue or a permissions problem before discovering the root cause is the wrong adapter module.

**Correct approach:** Replace `lightning/uiRecordApi` with the appropriate `commerce/productApi` adapter. Use `getProduct` with the `fields` parameter to request specific product field values, and ensure `recordId` is renamed to `productId` in the wire parameters since the Commerce adapter uses a different parameter name.
</content>
</invoke>