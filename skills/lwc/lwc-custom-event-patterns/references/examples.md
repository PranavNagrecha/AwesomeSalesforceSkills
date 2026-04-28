# Examples — LWC Custom Event Patterns

Three realistic worked examples covering the most common dispatch shapes: a direct parent listening for a child, sibling-to-sibling via Lightning Message Service, and event flow through a `<slot>`.

---

## Example 1 — Parent listening for a child event (default flags)

### Context

A `c-row-list` parent renders multiple `c-row-item` children. When the user clicks a row, the row should tell the list which record was selected. The list is the **direct parent** in the same shadow tree, so neither `bubbles` nor `composed` is required.

### Child — `rowItem.js`

```javascript
import { LightningElement, api } from 'lwc';

export default class RowItem extends LightningElement {
    @api recordId;
    @api label;

    handleClick() {
        // Default flags are correct here: the listener lives in the
        // immediate parent, inside the same shadow tree.
        this.dispatchEvent(new CustomEvent('rowselect', {
            detail: { recordId: this.recordId },
        }));
    }
}
```

```html
<!-- rowItem.html -->
<template>
    <button onclick={handleClick} data-record-id={recordId}>
        {label}
    </button>
</template>
```

### Parent — `rowList.html` and `rowList.js`

```html
<!-- rowList.html -->
<template>
    <template for:each={rows} for:item="row">
        <c-row-item
            key={row.Id}
            record-id={row.Id}
            label={row.Name}
            onrowselect={handleRowSelect}>
        </c-row-item>
    </template>
</template>
```

```javascript
// rowList.js
import { LightningElement, track } from 'lwc';

export default class RowList extends LightningElement {
    @track rows = [];
    @track selectedId;

    handleRowSelect(event) {
        // event.currentTarget is the <c-row-item> on which we bound
        // the listener. event.detail carries the payload.
        this.selectedId = event.detail.recordId;
    }
}
```

### Why the flags were chosen this way

- `bubbles: false` — the listener is on the direct parent element, no propagation needed.
- `composed: false` — both elements are in the same shadow tree.
- `cancelable: false` — the parent has no veto right; the row already committed to firing.
- Event name `rowselect` — single lowercase word, matches `onrowselect` declaratively.

If `composed: true` were added "to be safe," the event would also leak into any Aura wrapper, the document root, and any global listeners — wider blast radius for no benefit.

---

## Example 2 — Sibling-to-sibling via Lightning Message Service (custom events would NOT work)

### Context

`c-cart-summary` and `c-product-list` are placed side-by-side on a Lightning App Page. They are **not in the same component subtree** — they are independent regions. A custom event from `c-product-list` cannot reach `c-cart-summary` because there is no shared ancestor LWC to listen at. This is the canonical case for **Lightning Message Service**.

### Message channel — `force-app/main/default/messageChannels/Cart_Updated.messageChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Cart Updated</masterLabel>
    <isExposed>true</isExposed>
    <description>Fired when the cart contents change.</description>
    <lightningMessageFields>
        <description>Total cart amount in USD</description>
        <fieldName>totalAmount</fieldName>
    </lightningMessageFields>
    <lightningMessageFields>
        <description>Number of items in the cart</description>
        <fieldName>itemCount</fieldName>
    </lightningMessageFields>
</LightningMessageChannel>
```

### Publisher — `productList.js`

```javascript
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import CART_UPDATED from '@salesforce/messageChannel/Cart_Updated__c';

export default class ProductList extends LightningElement {
    @wire(MessageContext) messageContext;

    handleAddToCart(event) {
        const payload = {
            totalAmount: event.detail.newTotal,
            itemCount: event.detail.newCount,
        };
        // LMS — not a CustomEvent. The receiver lives in another region.
        publish(this.messageContext, CART_UPDATED, payload);
    }
}
```

### Subscriber — `cartSummary.js`

```javascript
import { LightningElement, wire } from 'lwc';
import { subscribe, unsubscribe, MessageContext } from 'lightning/messageService';
import CART_UPDATED from '@salesforce/messageChannel/Cart_Updated__c';

export default class CartSummary extends LightningElement {
    @wire(MessageContext) messageContext;
    subscription = null;
    totalAmount = 0;
    itemCount = 0;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            CART_UPDATED,
            (msg) => {
                this.totalAmount = msg.totalAmount;
                this.itemCount = msg.itemCount;
            },
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
}
```

### Why a CustomEvent would NOT work here

- The two components are siblings on the page with **no shared LWC ancestor** that could host an `onevent={...}` listener. A bubbled+composed event from `c-product-list` propagates up to the document, but there is no LWC there to receive it.
- Even if a wrapper LWC were added, every consumer of the cart total would need to listen on it and re-broadcast — that is exactly the noise LMS is designed to avoid.

---

## Example 3 — Event flow through a `<slot>` from slotted content to the slot host

### Context

`c-modal` uses a `<slot>` to project caller-provided content into its body. The slotted content (a `c-confirmation-form`) needs to tell the modal to close. The slotted content is **not a child of the modal in the LWC tree** — slot projection is a render concept, not a parenthood concept. The modal must listen on the slot itself, AND the event must be `composed: true` to escape the form's shadow root.

### Slotted content — `confirmationForm.js`

```javascript
import { LightningElement } from 'lwc';

export default class ConfirmationForm extends LightningElement {
    handleConfirm() {
        // Must bubble AND be composed. Without composed:true, the event
        // never escapes confirmationForm's shadow root and the modal
        // never hears it.
        this.dispatchEvent(new CustomEvent('formconfirm', {
            detail: { result: 'ok' },
            bubbles: true,
            composed: true,
        }));
    }
}
```

### Modal host — `modal.html` and `modal.js`

```html
<!-- modal.html -->
<template>
    <section class="modal-body" onformconfirm={handleFormConfirm}>
        <slot></slot>
    </section>
</template>
```

```javascript
// modal.js
import { LightningElement, api } from 'lwc';

export default class Modal extends LightningElement {
    @api close() {
        // imperative close API
    }

    handleFormConfirm(event) {
        // event.target is the slotted form element retargeted to the
        // host (c-confirmation-form). event.detail is the safe place to
        // read the actual payload.
        if (event.detail.result === 'ok') {
            this.close();
        }
    }
}
```

### Caller — `recordPage.html`

```html
<c-modal>
    <c-confirmation-form></c-confirmation-form>
</c-modal>
```

### Why both flags are required

- `bubbles: true` — needed because the listener is on a parent element (`<section>`), not on the form itself.
- `composed: true` — needed because the form lives in its own shadow root. Without this flag, the bubbling stops at `c-confirmation-form`'s host element and never reaches the `<section>` inside `c-modal`.
- The detail payload (`{ result: 'ok' }`) is a primitive object, so no freezing or cloning is required — strings are immutable in JavaScript.

---

## Anti-Pattern: using a CustomEvent to push data DOWN into a child

### What practitioners do

```javascript
// parentCmp.js — WRONG
this.template.querySelector('c-child').dispatchEvent(
    new CustomEvent('configure', { detail: { mode: 'compact' } })
);
```

### What goes wrong

- The child must add a listener in `connectedCallback` for an event coming **from itself**, which is unnatural and easy to forget.
- The configuration is invisible in markup — a future reader cannot tell the child is "compact" by looking at `parentCmp.html`.
- Reactivity is lost: changing `mode` later requires re-firing the event manually instead of just rebinding the property.

### Correct approach

```html
<!-- parentCmp.html -->
<c-child mode="compact"></c-child>
```

```javascript
// childCmp.js
import { LightningElement, api } from 'lwc';
export default class Child extends LightningElement {
    @api mode = 'expanded';
}
```

`@api` properties are the sanctioned way for parents to push data down. Custom events are for the opposite direction.
