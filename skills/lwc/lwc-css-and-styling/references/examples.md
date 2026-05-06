# Examples — LWC CSS and Styling

## Example 1: Restyling `lightning-button` via SLDS styling hook

The current, supported way to change a base-component color.

```css
/* myComponent.css */
.danger-button {
    --slds-c-button-color-background: #c23934;
    --slds-c-button-color-border: #c23934;
    --slds-c-button-text-color: #ffffff;
}
```

```html
<template>
    <lightning-button
        class="danger-button"
        label="Delete"
        onclick={handleDelete}>
    </lightning-button>
</template>
```

The base component consumes these CSS custom properties from the
cascade. Set them on a parent class (or `:host`) and they apply
to every nested base component that supports them.

---

## Example 2: Using design tokens for theme-aware colors

```css
.summary-banner {
    background-color: var(--slds-g-color-brand-base-50, #1589ee);
    color: var(--slds-g-color-neutral-100, #ffffff);
    padding: var(--slds-g-spacing-medium, 1rem);
    border-radius: var(--slds-g-radius-border-2, 0.25rem);
}
```

The fallback after the comma is the value when the token is not
yet defined (e.g. running outside Lightning Experience). With the
fallback, the same component works in standalone Lightning, in
Experience Cloud sites, and in unauthenticated previews.

---

## Example 3: Light DOM for a small layout component

```js
import { LightningElement } from 'lwc';

export default class TwoColumnLayout extends LightningElement {
    static renderMode = 'light';
}
```

```html
<template lwc:render-mode='light'>
    <div class="row">
        <div class="col"><slot name="left"></slot></div>
        <div class="col"><slot name="right"></slot></div>
    </div>
</template>
```

```css
/* twoColumnLayout.css */
.row { display: flex; gap: 1rem; }
.col { flex: 1; }
```

In light DOM, `.row` and `.col` participate in the consumer's
CSS scope. Global CSS reaches them, and the consumer can
override. Trade: forfeit shadow encapsulation.

---

## Example 4: `::part()` to style an internal element

```css
.invoice-row::part(button-icon) {
    color: var(--slds-g-color-error, #c23934);
}
```

`::part()` only works on parts the base component explicitly
exposes via the `part="..."` attribute on its internal elements.
Check the component's documentation — most base components do
not expose parts, but newer ones (`lightning-tile`, some
Salesforce-shipped LWCs) do.

---

## Example 5: Slotted custom rendering

When neither hooks nor parts are sufficient, use a slot to let
the consumer render their own element.

```html
<!-- card.html (the base component) -->
<template>
    <article class="slds-card">
        <header class="slds-card__header">
            <slot name="header">
                <h2>{title}</h2>
            </slot>
        </header>
        <div class="slds-card__body">
            <slot></slot>
        </div>
    </article>
</template>
```

```html
<!-- consumer.html -->
<c-card title="Default title">
    <h2 slot="header" class="my-custom-header">
        <span class="slds-icon">⚡</span>
        Custom
    </h2>
    <p>Body content</p>
</c-card>
```

Slotted content lives in the consumer's shadow DOM, so the
consumer's CSS styles it normally.

---

## Example 6: `:host` to style the component's own root

```css
:host {
    display: block;
    border-left: 4px solid var(--slds-g-color-accent, #1589ee);
}

:host(.danger) {
    border-color: var(--slds-g-color-error, #c23934);
}
```

`:host` is the styling hook for the component's own root
element. `:host(.danger)` matches when the consumer adds
`class="danger"` on the component tag. This is how you let the
consumer drive theme variants without exposing internal classes.
