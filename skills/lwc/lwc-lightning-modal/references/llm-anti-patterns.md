# LLM Anti-Patterns — LWC LightningModal

Common mistakes AI coding assistants make with LightningModal.

## Anti-Pattern 1: Extending LightningElement for a modal

**What the LLM generates:**

```
import { LightningElement } from 'lwc';
export default class MyConfirm extends LightningElement { ... }
```

**Why it happens:** Model defaults to LightningElement.

**Correct pattern:**

```
import LightningModal from 'lightning/modal';
export default class MyConfirm extends LightningModal { ... }

Only LightningModal gives you .open() / this.close(), focus trap,
and the modal slots.
```

**Detection hint:** LWC component with `modal` in its name extending LightningElement.

---

## Anti-Pattern 2: Rendering the modal in parent template

**What the LLM generates:** Parent template contains `<c-my-confirm if:true={showConfirm}>`.

**Why it happens:** Model treats the modal like any other component.

**Correct pattern:**

```
LightningModal components are invoked via static .open():

import MyConfirm from 'c/myConfirm';
const result = await MyConfirm.open({ label: 'Confirm?' });

They don't render in parent templates. The framework manages
the DOM insertion, focus, and portal logic.
```

**Detection hint:** Parent template tag referencing a class that extends LightningModal.

---

## Anti-Pattern 3: Not handling undefined result (dismiss)

**What the LLM generates:**

```
const result = await MyConfirm.open();
if (result === 'ok') doThing();
```

**Why it happens:** Model focuses on the happy path.

**Correct pattern:**

```
Dismissing via Esc or outside click resolves with undefined.
Handle explicitly:

const result = await MyConfirm.open();
if (result === 'ok') doThing();
else if (result === undefined) { /* user dismissed */ }
```

**Detection hint:** Modal consumer with result comparison but no undefined / falsy branch.

---

## Anti-Pattern 4: Missing accessibility label

**What the LLM generates:** Modal with body text but no `label` / header content.

**Why it happens:** Model focuses on visual design.

**Correct pattern:**

```
Set label (passed in options) or fill the <lightning-modal-header>
slot. Screen readers announce the label when the modal opens.
Without it, the modal is anonymous in assistive tech.
```

**Detection hint:** LightningModal `.open()` call without a `label` option and the modal template has empty `<lightning-modal-header>`.

---

## Anti-Pattern 5: Using a CSS overlay instead of LightningModal

**What the LLM generates:** Custom div with `position: fixed` and a backdrop, no LightningModal.

**Why it happens:** Model rolls its own without knowing about the primitive.

**Correct pattern:**

```
LightningModal handles:
- Focus trap (Tab cycles within the modal)
- Esc to close
- z-index layering with toast/notif stack
- SLDS styling that matches Lightning chrome
- Portal rendering so it escapes scroll containers

A hand-rolled overlay has none of that. Use LightningModal for any
true modal; use SLDS popover for lightweight anchored overlays.
```

**Detection hint:** LWC template with div having `slds-modal` classes or `position: fixed` backdrop and no LightningModal import.
