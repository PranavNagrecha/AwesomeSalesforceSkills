# LLM Anti-Patterns — LWC Modal and Overlay

Common mistakes AI coding assistants make when generating or advising on modal and overlay patterns in LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Building a custom modal from SLDS markup instead of using LightningModal

**What the LLM generates:**

```html
<template lwc:if={isOpen}>
    <section class="slds-modal slds-fade-in-open" role="dialog">
        <div class="slds-modal__container">
            <header class="slds-modal__header">
                <h2>My Modal</h2>
            </header>
            <div class="slds-modal__content">
                <slot></slot>
            </div>
        </div>
    </section>
    <div class="slds-backdrop slds-backdrop_open"></div>
</template>
```

**Why it happens:** Training data is full of pre-LightningModal SLDS examples. LLMs reproduce them because the markup looks complete, but it lacks focus trapping, Escape key handling, and proper lifecycle.

**Correct pattern:**

```javascript
// Default import - `import { LightningModal }` yields undefined and
// `extends undefined` throws (use-dialog-modal, L10375, L10377).
import LightningModal from 'lightning/modal';

export default class MyModal extends LightningModal {
    handleClose() {
        this.close('result');
    }
}
```

```javascript
// Calling component
const result = await MyModal.open({
    size: 'small',
    description: 'Modal description',
    label: 'My Modal'
});
```

**Detection hint:** `slds-modal` class in HTML template. Any LWC modal should extend `LightningModal` unless there is a documented reason not to.

---

## Anti-Pattern 2: Not returning a result from LightningModal.close()

**What the LLM generates:**

```javascript
handleSave() {
    // Performs save then closes with no return value
    this.close();
}
```

**Why it happens:** LLMs call `this.close()` without arguments, which resolves the caller's `await` with `undefined`. The parent has no way to know what happened.

**Correct pattern:**

```javascript
handleSave() {
    this.close({ saved: true, recordId: this.recordId });
}

handleCancel() {
    this.close({ saved: false });
}
```

```javascript
// Caller
const result = await MyModal.open({ /* ... */ });
if (result?.saved) {
    this.refreshData();
}
```

**Detection hint:** `this.close()` with no arguments in a modal that performs an action the caller needs to know about.

---

## Anti-Pattern 3: Using a modal for simple confirmations instead of lightning-confirm

**What the LLM generates:**

```javascript
// Builds a full LightningModal subclass just to ask "Are you sure?"
export default class ConfirmDeleteModal extends LightningModal {
    handleYes() { this.close(true); }
    handleNo() { this.close(false); }
}
```

**Why it happens:** LLMs default to the most powerful tool. For simple yes/no confirmations, `LightningConfirm` is a one-line alternative that requires no separate component.

**Correct pattern:**

```javascript
import LightningConfirm from 'lightning/confirm';

async handleDelete() {
    const confirmed = await LightningConfirm.open({
        message: 'Are you sure you want to delete this record?',
        label: 'Confirm Deletion',
        variant: 'header'
    });
    if (confirmed) {
        this.deleteRecord();
    }
}
```

**Watch the attribute name.** `lightning/confirm` takes `message`, `variant`, and `label`; `lightning/alert` and `lightning/prompt` take `theme` instead of `variant` (`use-dialog-confirm`, L10418; `use-dialog-alert`, L10404; `use-dialog-prompt`, L10432). An LLM that has seen all three pages will mix them, and an unsupported key is simply ignored - there is no error to tell you.

**Detection hint:** A dedicated LWC component file whose only purpose is a yes/no confirmation with two buttons.

---

## Anti-Pattern 4: Using ShowToastEvent for errors that require user acknowledgment

**What the LLM generates:**

```javascript
handleError(error) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Critical Error',
        message: 'Data was not saved. Please contact support.',
        variant: 'error',
        mode: 'sticky'
    }));
}
```

**Why it happens:** Toasts are the most common notification mechanism in training data. But sticky toasts are easily dismissed and do not block the user workflow when acknowledgment is truly required.

**Correct pattern:**

```javascript
import LightningAlert from 'lightning/alert';

async handleError(error) {
    await LightningAlert.open({
        message: 'Data was not saved. Please contact support.',
        label: 'Critical Error',
        theme: 'error'
    });
    // Execution continues only after user clicks OK
}
```

**Detection hint:** `mode: 'sticky'` on a toast that communicates a blocking error or data loss scenario.

---

## Anti-Pattern 5: Opening a modal from inside renderedCallback or connectedCallback

**What the LLM generates:**

```javascript
connectedCallback() {
    MyModal.open({ size: 'medium' });
    // Opens every time the component connects, including re-inserts
}
```

**Why it happens:** LLMs place initialization logic in lifecycle hooks. Auto-opening modals on connect creates surprising UX and can loop if the modal's close triggers a re-render.

**Correct pattern:**

Open modals in response to explicit user actions:

```javascript
handleOpenModal() {
    MyModal.open({ size: 'medium' });
}
```

**Detection hint:** `Modal.open(` or `LightningConfirm.open(` inside `connectedCallback` or `renderedCallback`.

---

## Anti-Pattern 6: Not setting the label attribute on LightningModal for accessibility

**What the LLM generates:**

```javascript
const result = await MyModal.open({
    size: 'medium',
    description: 'Edit account details'
    // Missing label — no accessible dialog title
});
```

**Why it happens:** LLMs focus on `description` and `size` but skip `label`, which sets the modal's `aria-label` for screen readers.

**Correct pattern:**

```javascript
const result = await MyModal.open({
    size: 'medium',
    label: 'Edit Account',
    description: 'Edit account details'
});
```

**Detection hint:** `Modal.open(` call without a `label` property in the configuration object.

---

## Anti-Pattern 7: Applying NavigationMixin to the LightningModal subclass

**What the LLM generates:**

```javascript
import { NavigationMixin } from 'lightning/navigation';
import LightningModal from 'lightning/modal';

export default class RecordPickerModal extends NavigationMixin(LightningModal) {
    handleGo(recordId) {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: { recordId, actionName: 'view' }
        });
    }
}
```

**Why it happens:** `NavigationMixin(LightningElement)` is one of the most common LWC snippets in
training data, so the model substitutes the base class and keeps the shape. It compiles. The guide
forbids it: "Use `NavigationMixin` only with a Lightning web component that extends
`LightningElement`. You can't use the `NavigationMixin` function directly in a custom component that
extends `LightningModal`" (`use-navigate-modal`, L10258-L10259).

**Correct pattern:**

```javascript
// In the modal: return the PageReference instead of navigating.
handleGo(recordId) {
    this.close({
        status: 'navigate',
        pageReference: {
            type: 'standard__recordPage',
            attributes: { recordId, actionName: 'view' }
        }
    });
}

// In the launcher, which extends NavigationMixin(LightningElement):
const result = await RecordPickerModal.open({ label: 'Pick a record' });
if (result?.status === 'navigate') {
    this[NavigationMixin.Navigate](result.pageReference);
}
```

**Detection hint:** `NavigationMixin(` and `LightningModal` in the same `extends` clause, or any
`this[NavigationMixin.Navigate]` inside a file that also imports `lightning/modal`.

---

## Anti-Pattern 8: Fire-and-forget open(), or a close() path that never runs

**What the LLM generates:**

```javascript
handleEdit() {
    // No await, no .then - the resolved value is thrown away
    EditModal.open({ label: 'Edit', recordId: this.recordId });
    this.refreshData();   // runs immediately, before the user has typed anything
}
```

**Why it happens:** `open()` reads like a void UI command, so the model treats it as one and puts the
follow-up work on the next line. But `open()` returns a promise that resolves only when the modal
closes, carrying the `close()` argument (`use-dialog-modal`, L10379, L10387), so the refresh fires
against unchanged data and the user sees a stale view behind the open modal.

The mirror-image failure is a modal with an exit path that never calls `close()` at all - typically
an error branch:

```javascript
async handleSave() {
    try {
        await saveRecord(this.draft);
        this.close({ saved: true });
    } catch (e) {
        this.error = e.body.message;   // modal stays open, caller stays awaiting - forever
    }
}
```

**Correct pattern:** `await` the open, and give the modal a terminating path for every outcome,
including failure - either close with the error tagged, or leave the modal open only when the user
still has a working Cancel button to reach.

```javascript
const result = await EditModal.open({ label: 'Edit', recordId: this.recordId });
if (result?.saved) {
    this.refreshData();
}
```

**Detection hint:** a `.open(` call whose result is not assigned, awaited, or `.then`-ed; and a
`catch` block inside a `LightningModal` subclass that neither calls `close()` nor re-enables a
control that does.
