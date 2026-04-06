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
        theme: 'warning'
    });
    if (confirmed) {
        this.deleteRecord();
    }
}
```

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
