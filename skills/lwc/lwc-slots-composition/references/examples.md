# Examples — LWC Slots Composition

## Example 1: Reusable Card With Named Slots And Default Body

**Context:** A team is building a dashboard with multiple cards. Each card has the same chrome (border, padding, shadow), but headers, footers, and body content vary per caller.

**Problem:** Exposing `@api title`, `@api subtitle`, `@api footerText`, and `@api bodyHtml` forces callers to stringify markup, loses nested-component behavior, and blocks icons or buttons in the header.

**Solution:**

Child — `c-ui-card` (shadow DOM by default):

```html
<!-- uiCard.html -->
<template>
    <article class="card">
        <header class="card__header">
            <slot name="header">
                <span class="card__header-fallback">Untitled</span>
            </slot>
        </header>

        <section class="card__body">
            <slot></slot>
        </section>

        <footer class="card__footer">
            <slot name="footer"></slot>
        </footer>
    </article>
</template>
```

Parent composing the card:

```html
<!-- accountSummary.html -->
<template>
    <c-ui-card>
        <lightning-icon slot="header" icon-name="standard:account" size="small"></lightning-icon>
        <h2 slot="header">{account.Name}</h2>

        <p>Industry: {account.Industry}</p>
        <p>Owner: {account.Owner.Name}</p>

        <lightning-button slot="footer" label="View" onclick={handleView}></lightning-button>
    </c-ui-card>
</template>
```

**Why it works:** Named slots let the parent fill the header and footer regions independently while any remaining children (the two `<p>` tags) fall into the default body slot. Because slot assignment happens in the parent's scope, the parent's CSS continues to style the `<h2>` and `<p>` elements and the `lightning-button` retains its normal event behavior.

---

## Example 2: Conditional Wrapper Based On Slot Emptiness

**Context:** A modal LWC has an optional actions bar. When the parent provides buttons, the actions bar should render with its divider and spacing. When the parent provides nothing, the whole actions region should collapse — no empty strip, no divider.

**Problem:** Always rendering the actions wrapper leaves a visibly empty band. Gating it with an `@api hasActions` property forces every caller to pass a boolean that duplicates what the markup already says.

**Solution:**

Child — `c-ui-modal`:

```html
<!-- uiModal.html -->
<template>
    <div class="modal">
        <div class="modal__body">
            <slot></slot>
        </div>

        <template lwc:if={hasActions}>
            <div class="modal__actions">
                <slot name="actions" lwc:ref="actionsSlot" onslotchange={handleActionsSlotChange}></slot>
            </div>
        </template>

        <!-- Keep the slot mounted so slotchange can still observe assignment even when hasActions is false.
             Render it in a hidden container and move it into place via the conditional wrapper above once populated. -->
        <template lwc:if={!hasActions}>
            <div hidden>
                <slot name="actions" lwc:ref="actionsSlot" onslotchange={handleActionsSlotChange}></slot>
            </div>
        </template>
    </div>
</template>
```

```javascript
// uiModal.js
import { LightningElement } from 'lwc';

export default class UiModal extends LightningElement {
    hasActions = false;

    handleActionsSlotChange() {
        const slot = this.refs.actionsSlot;
        if (!slot) {
            return;
        }
        const assigned = slot.assignedNodes({ flatten: true }).filter(
            (node) => node.nodeType !== Node.TEXT_NODE || node.textContent.trim().length > 0
        );
        this.hasActions = assigned.length > 0;
    }
}
```

Parent with actions:

```html
<c-ui-modal>
    <p>Are you sure you want to delete this record?</p>
    <lightning-button slot="actions" variant="neutral" label="Cancel" onclick={handleCancel}></lightning-button>
    <lightning-button slot="actions" variant="destructive" label="Delete" onclick={handleDelete}></lightning-button>
</c-ui-modal>
```

Parent without actions (wrapper collapses automatically):

```html
<c-ui-modal>
    <p>Saved successfully.</p>
</c-ui-modal>
```

**Why it works:** The `slotchange` event fires on initial render and whenever the assigned nodes change, so `hasActions` stays in sync without polling. Filtering out whitespace-only text nodes prevents false positives from stray newlines in the parent template. Using `lwc:ref` is the supported way to access the live `<slot>` element and call `assignedNodes()`.

---

## Anti-Pattern: Passing Markup Through `@api` Instead Of A Slot

**What practitioners do:** They expose `@api headerHtml` or `@api footerContent` on the child and have the parent assemble a string or DOM blob to inject. Sometimes this is paired with `lwc:dom="manual"` in the child to write the string into an element.

**What goes wrong:**
- LWC components inside the injected markup are not instantiated — the framework only processes markup declared in templates.
- Scoped styles stop applying; events do not bubble through LWC's synthetic-event boundary the way they do with real child elements.
- Accessibility metadata and attribute reactivity are lost because the payload is a string, not a reactive tree.
- `lwc:dom="manual"` is itself a narrow escape hatch and does not compose.

**Correct approach:** Declare `<slot>` (or named slots) in the child and have the parent pass real markup between the custom-element tags. The parent keeps ownership of the injected elements, including their components, styles, and events; the child keeps ownership of the surrounding chrome. See Example 1.
