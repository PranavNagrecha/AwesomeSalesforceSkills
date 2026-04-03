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
