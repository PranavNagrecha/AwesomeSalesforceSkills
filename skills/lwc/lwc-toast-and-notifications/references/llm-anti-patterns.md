# LLM Anti-Patterns — LWC Toast and Notifications

Common mistakes AI coding assistants make when generating or advising on toast messages and notification patterns in LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using ShowToastEvent in Experience Cloud without a fallback

**What the LLM generates:**

```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

handleSave() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Success',
        message: 'Record saved.',
        variant: 'success'
    }));
}
```

**Why it happens:** `ShowToastEvent` is the most common notification pattern in LWC training data. LLMs use it universally, but it does not work in LWR-based Experience Cloud sites.

**Correct pattern:**

```javascript
handleSave() {
    if (this._isExperienceCloud) {
        // Use a custom notification component or inline message
        this.successMessage = 'Record saved.';
    } else {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: 'Record saved.',
            variant: 'success'
        }));
    }
}
```

Or use `lightning-alert` which works across contexts.

**Detection hint:** `ShowToastEvent` in a component with `lightning__CommunityPage` or `lightningCommunity__Page` target but no fallback.

---

## Anti-Pattern 2: Using sticky mode for every error toast

**What the LLM generates:**

```javascript
this.dispatchEvent(new ShowToastEvent({
    title: 'Error',
    message: error.body.message,
    variant: 'error',
    mode: 'sticky'
}));
```

**Why it happens:** LLMs default to `mode: 'sticky'` for errors to ensure users see them. But most errors are transient and dismissable — sticky toasts accumulate and clutter the UI when multiple operations fail.

**Correct pattern:**

```javascript
// Default mode is 'dismissable' — appropriate for most errors
this.dispatchEvent(new ShowToastEvent({
    title: 'Error',
    message: error.body.message,
    variant: 'error'
    // mode defaults to 'dismissable'
}));
```

Reserve `mode: 'sticky'` for critical, non-recoverable errors only.

**Detection hint:** `mode: 'sticky'` on error toasts without a comment explaining why sticky is justified.

---

## Anti-Pattern 3: Showing a toast for every successful action without user value

**What the LLM generates:**

```javascript
handleFieldChange() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Updated',
        message: 'Field value changed successfully.',
        variant: 'success'
    }));
}
```

**Why it happens:** LLMs add success toasts after every operation for "completeness." Frequent toasts for routine actions (field changes, filter selections, tab switches) create notification fatigue.

**Correct pattern:**

Show toasts only for significant state changes (record save, delete, batch completion):

```javascript
handleSave() {
    await saveRecord(this.record);
    this.dispatchEvent(new ShowToastEvent({
        title: 'Saved',
        message: 'Account updated successfully.',
        variant: 'success'
    }));
}

handleFieldChange() {
    // No toast — inline visual feedback is sufficient
    this.hasUnsavedChanges = true;
}
```

**Detection hint:** `ShowToastEvent` with `variant: 'success'` in handlers for minor interactions like change, blur, or toggle events.

---

## Anti-Pattern 4: Not extracting useful error messages from the error object

**What the LLM generates:**

```javascript
handleError(error) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: JSON.stringify(error), // Raw error object — unreadable
        variant: 'error'
    }));
}
```

**Why it happens:** LLMs do not know the shape of the error object at generation time, so they stringify the whole thing. This produces unreadable JSON in the toast.

**Correct pattern:**

```javascript
// Utility function to extract meaningful messages
reduceErrors(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message);
    }
    if (error.body?.message) {
        return [error.body.message];
    }
    if (typeof error.message === 'string') {
        return [error.message];
    }
    return ['Unknown error'];
}

handleError(error) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: this.reduceErrors(error).join('; '),
        variant: 'error'
    }));
}
```

**Detection hint:** `JSON.stringify(error)` or `error.toString()` passed as the toast message.

---

## Anti-Pattern 5: Confusing lightning-alert / lightning-confirm with ShowToastEvent

**What the LLM generates:**

```javascript
import LightningAlert from 'lightning/alert';

// Uses alert for a success notification — blocks the user unnecessarily
await LightningAlert.open({
    message: 'Record saved successfully.',
    label: 'Success',
    theme: 'success'
});
```

**Why it happens:** LLMs know both APIs exist and sometimes swap them. Alerts block the user until dismissed — they should not be used for routine success messages.

**Correct pattern:**

- **Toast** for non-blocking, transient feedback (success, info, minor errors)
- **Alert** for important messages that require explicit acknowledgment
- **Confirm** for yes/no decisions before destructive actions

```javascript
// Success: use toast (non-blocking)
this.dispatchEvent(new ShowToastEvent({
    title: 'Success', message: 'Record saved.', variant: 'success'
}));

// Destructive confirmation: use confirm (blocking)
const proceed = await LightningConfirm.open({
    message: 'Delete this record?', label: 'Confirm', theme: 'warning'
});
```

**Detection hint:** `LightningAlert.open` with `theme: 'success'` for routine success feedback.

---

## Anti-Pattern 6: Dispatching ShowToastEvent from a child component that is not connected to the app container

**What the LLM generates:**

```javascript
// Deep nested child component
this.dispatchEvent(new ShowToastEvent({
    title: 'Error', message: 'Validation failed', variant: 'error'
}));
// Toast never appears — ShowToastEvent must reach the app container
```

**Why it happens:** LLMs dispatch `ShowToastEvent` from any component. The event must bubble up to the Lightning app container, but `ShowToastEvent` uses default bubbling (`bubbles: false`). In deeply nested components or components inside modals, the event may not reach the container.

**Correct pattern:**

Dispatch from the top-level component, or re-dispatch from a component that is directly in the app hierarchy:

```javascript
// Child dispatches a custom event
this.dispatchEvent(new CustomEvent('showerror', {
    detail: { message: 'Validation failed' },
    bubbles: true, composed: true
}));

// Parent catches and shows the toast
handleShowError(event) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error', message: event.detail.message, variant: 'error'
    }));
}
```

**Detection hint:** `ShowToastEvent` dispatched from a component that is inside a `LightningModal` or a deeply nested slot.
