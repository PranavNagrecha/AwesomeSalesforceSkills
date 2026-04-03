# Examples - Component Communication

## Example 1: Parent Provides Context, Child Emits Intent

**Context:** A parent account workspace loads a selected Contact and renders a child editor component.

**Problem:** The first implementation passes the full mutable record object down and expects the child to update parent state directly.

**Solution:**

Pass the record ID and read-only mode down through `@api`, then let the child emit a save request upward.

```js
// parent.html
<c-contact-editor
    record-id={selectedContactId}
    read-only={isLocked}
    onsave={handleSave}>
</c-contact-editor>
```

```js
// child.js
this.dispatchEvent(
    new CustomEvent('save', {
        detail: { recordId: this.recordId, draft: this.buildDraft() }
    })
);
```

**Why it works:** Ownership stays clear. The parent owns selection and persistence. The child owns editing UI and emits intent without mutating parent state directly.

---

## Example 2: Lightning Message Service For Cross-Region Selection

**Context:** A utility-bar component selects a service region, and unrelated workspace components must react to that selection.

**Problem:** The team tries to pass the selection through a chain of intermediate parents that do not actually own the business meaning.

**Solution:**

Use a message channel.

```js
import { LightningElement, wire } from 'lwc';
import { MessageContext, publish } from 'lightning/messageService';
import REGION_CHANNEL from '@salesforce/messageChannel/RegionSelection__c';

export default class RegionPicker extends LightningElement {
    @wire(MessageContext) messageContext;

    handleChange(event) {
        publish(this.messageContext, REGION_CHANNEL, {
            regionCode: event.detail.value
        });
    }
}
```

Subscribers listen only where the cross-region context is genuinely needed.

**Why it works:** The message contract matches the actual scope of the problem. Components remain decoupled from the page hierarchy.

---

## Anti-Pattern: Reaching Into A Child `shadowRoot`

**What practitioners do:** A parent finds `c-child` with `querySelector()` and then drills into `shadowRoot` to click buttons or read private DOM.

**What goes wrong:** The parent now depends on the child's internal structure instead of its public contract. A child refactor breaks the parent even though the public API never changed.

**Correct approach:** Expose a narrow public method for imperative actions, or move the shared behavior up into the parent if the parent truly owns it.
