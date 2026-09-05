# Examples - LWC Accessibility

## Example 1: Replace A Clickable Card With Real Button Semantics

**Context:** A custom record card uses a `div` with `onclick` to open details. It looks fine in the browser and passes casual mouse testing.

**Problem:** Keyboard users cannot reliably activate it, and screen readers announce a generic container instead of a button.

**Solution:**

Move the interaction onto a semantic button and keep the rest of the card presentational.

```html
<template>
    <article class="slds-card">
        <div class="slds-card__body slds-card__body_inner">
            <h2 class="slds-text-heading_small">{record.Name}</h2>
            <p>{record.Status__c}</p>
            <lightning-button
                label="Open record details"
                variant="brand"
                onclick={handleOpen}
            ></lightning-button>
        </div>
    </article>
</template>
```

**Why it works:** The control now carries native button behavior, keyboard activation, and a clear accessible name instead of relying on custom ARIA repairs.

---

## Example 2: Focus Return After Closing A Modal

**Context:** An action button opens a custom details modal from a data row.

**Problem:** After the modal closes, focus returns to the top of the page. Keyboard users lose context and must tab through the page again.

**Solution:**

Store a reference to the launcher and restore focus after the modal promise resolves.

```javascript
import { LightningElement } from 'lwc';
import DetailsModal from 'c/detailsModal';

export default class CaseRowActions extends LightningElement {
    async handleDetailsClick(event) {
        this.lastTrigger = event.target;
        await DetailsModal.open({
            label: 'Case details',
            size: 'small',
            caseId: event.target.dataset.caseId
        });
        this.lastTrigger?.focus();
    }
}
```

**Why it works:** Focus becomes part of the interaction contract instead of an accidental browser side effect.

---

## Anti-Pattern: ARIA On Top Of Non-Semantic Click Targets

**What practitioners do:** They keep a clickable `span` or `div`, then add `role="button"` and `tabindex="0"` as a late fix.

**What goes wrong:** The element still needs custom key handling, clear focus styling, and predictable assistive-tech announcements. Teams often miss one of those pieces.

**Correct approach:** Use native buttons, links, or Lightning base components first. Add ARIA only when a real semantic gap remains.

---

## Example 3: A Label That Never Reaches Its Input Across Two Components

**Context:** A design-system team splits a form field into `c-field-label` and `c-field-input` so the
label can be restyled independently. The markup looks textbook-correct.

**Problem:** The screen reader announces "edit, blank" with no label. Nothing errors. `for` and `id`
are both present in the DOM, but they are in different shadow trees, and ids are scoped per template.

**Broken:**

```html
<!-- fieldLabel.html -->
<template>
    <label for="amount-input">Amount</label>
</template>

<!-- fieldInput.html -->
<template>
    <input id="amount-input" type="text" />
</template>
```

**Fix A — keep them in one template (preferred).** This is what
`references/code-examples.md` does: the label, the control, the help text, and the error text are one
component, so the framework links them automatically after id transformation.

**Fix B — light DOM, when the split is genuinely required.** Light DOM does not scope ids, so the
two components share one shadow root and the reference resolves:

```js
// fieldLabel.js and fieldInput.js — both components
import { LightningElement } from 'lwc';

export default class FieldLabel extends LightningElement {
    static renderMode = 'light';
}
```

```html
<!-- fieldLabel.html — lwc:render-mode is required for light DOM -->
<template lwc:render-mode="light">
    <label for="amount-input">Amount</label>
</template>
```

**Why it works:** `create-components-accessibility-attributes` L4034–L4036 — ids and ARIA attributes
in the same template link automatically, attributes in different templates must be linked manually,
and in native shadow DOM cross-template linking is not possible; the guide's stated remedy is to use
light DOM so both elements sit in the same shadow root (`create-light-dom` L3188, L3242).

**What Fix B costs:** light DOM exposes the component to DOM scraping and is not protected by
Lightning Locker or LWS at the top level (`create-light-dom` L3190, L3204). Nest both components
inside a shadow DOM ancestor, and do not use this pattern for sensitive data.

---

## Anti-Pattern: Selecting Or Asserting On A Literal Template `id`

**What practitioners do:** They write `this.template.querySelector('#amount-input')` in JavaScript, or
`#amount-input { }` in CSS, or `expect(input.id).toBe('amount-input')` in a Jest test.

**What goes wrong:** Template `id` values may be transformed into globally unique values when the
template renders (`create-components-accessibility-attributes` L4010,
`create-components-dom-work` L3063). The JavaScript selector returns `null`, the CSS rule never
matches, and the test either fails immediately or — worse — passes in jsdom and misrepresents what
happens in the org.

**Correct approach:** Reserve `id` for `for` / `aria-*` associations only, and reach elements with
`lwc:ref` + `this.refs` or a `data-*` attribute. In tests, assert the relationship rather than the
value:

```js
const label = element.shadowRoot.querySelector('label');
const input = element.shadowRoot.querySelector('input');
expect(label.getAttribute('for')).toBe(input.getAttribute('id')); // relationship, not literal
```
