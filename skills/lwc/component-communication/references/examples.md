# Examples - Component Communication

## Example 1: Parent Provides Context, Child Emits Intent

**Context:** A parent account workspace loads a selected Contact and renders a child editor component.

**Problem:** The first implementation passes the full mutable record object down and expects the child to update parent state directly.

**Solution:**

Pass the record ID and read-only mode down through `@api`, then let the child emit a save request upward.

```html
<!-- parent.html -->
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

## Example 3: Reading The Flattened Tree Before Choosing `bubbles` And `composed`

**Context:** `c-child` sits inside `div.wrapper` inside `c-parent`, which sits inside
`c-app`. A button inside `c-child` must tell `c-parent` that it was clicked.

**Problem:** The team cannot agree on the propagation settings, so they set
`bubbles: true, composed: true` "to be safe" and the event now reaches `body`.

**Solution:**

Trace where the event can be handled for each configuration before choosing. Reading down
the flattened tree, `|` marks a shadow boundary crossing:

```text
body
└─ c-app                         composed:true  + bubbles:true  reaches here and further
   │ #shadow-root                ─────────────── shadow boundary
   └─ c-parent                   composed:true  + bubbles:true  reaches here
      │ #shadow-root             ─────────────── shadow boundary
      └─ div.wrapper             bubbles:true   + composed:false reaches here
         └─ c-child   <-- host   bubbles:false  + composed:false stops here  <== default
            │ #shadow-root       ─────────────── shadow boundary
            └─ button            dispatchEvent() called in the child's JS

Event.target seen by a listener on...
  c-child .......... c-child   (retargeted at the boundary)
  div.wrapper ...... c-child
  c-parent ......... c-parent  (retargeted again)
```

The listener `c-parent` actually needs is `<c-child onbuttonclick={handle}>` — attached to
the `c-child` host element inside `c-parent`'s own template, which is *below* the first
shadow boundary. The default configuration already reaches it.

**Why it works:** The only configuration that had to be widened here was none of them.
`bubbles: true, composed: false` becomes necessary one level further out — when `c-child`
is passed into a `<slot>` and must reach the template that contains it. `composed: true`
buys nothing except a public event name that every ancestor now owns.

---

## Anti-Pattern: Reaching Into A Child `shadowRoot`

**What practitioners do:** A parent finds `c-child` with `querySelector()` and then drills into `shadowRoot` to click buttons or read private DOM.

**What goes wrong:** The parent now depends on the child's internal structure instead of its public contract. A child refactor breaks the parent even though the public API never changed.

**Correct approach:** Expose a narrow public method for imperative actions, or move the shared behavior up into the parent if the parent truly owns it.
