# Examples - LWC Forms And Validation

## Example 1: Supported Record Edit Form With Server Error Handling

**Context:** A contact editor needs standard field rendering, validation-rule support, and a toast on successful save.

**Problem:** The first version uses custom inputs for every field even though the use case is standard record editing. Error handling becomes repetitive and inconsistent.

**Solution:**

Use `lightning-record-edit-form` with `lightning-messages` and handle save lifecycle events.

```html
<template>
    <lightning-record-edit-form
        object-api-name="Contact"
        record-id={recordId}
        onsuccess={handleSuccess}
        onerror={handleError}
    >
        <lightning-messages></lightning-messages>
        <lightning-input-field field-name="FirstName"></lightning-input-field>
        <lightning-input-field field-name="LastName"></lightning-input-field>
        <lightning-input-field field-name="Email"></lightning-input-field>
        <lightning-button type="submit" label="Save" variant="brand"></lightning-button>
    </lightning-record-edit-form>
</template>
```

```javascript
handleError(event) {
    const fieldErrors = event.detail?.output?.fieldErrors || {};
    this.formErrors = Object.keys(fieldErrors);
}
```

**Why it works:** Lightning Data Service handles the field model and server validation display, while the component keeps only the behavior it actually owns.

---

## Example 2: Custom Form With Explicit Client Validation

**Context:** A registration form collects a preferred contact method and conditionally requires either phone or email.

**Problem:** Required flags alone are not enough because the rule depends on another field's value.

**Solution:**

Use custom inputs with an explicit validity sweep before save.

```javascript
handleSave() {
    const email = this.template.querySelector('[data-id="email"]');
    const phone = this.template.querySelector('[data-id="phone"]');

    email.setCustomValidity(this.preferredContact === 'Email' && !email.value ? 'Email is required.' : '');
    phone.setCustomValidity(this.preferredContact === 'Phone' && !phone.value ? 'Phone is required.' : '');

    const inputs = [...this.template.querySelectorAll('lightning-input')];
    const isValid = inputs.every((input) => input.reportValidity());
    if (!isValid) {
        return;
    }

    this.submitRegistration();
}
```

**Why it works:** The component owns a custom rule, so it also owns the field-level validation contract and blocks save until every control reports cleanly.

---

## Anti-Pattern: Mixing Record-Edit Fields And Manual State Randomly

**What practitioners do:** They use `lightning-input-field` for some fields, custom `lightning-input` for others, and then try to submit everything through one loosely defined save button.

**What goes wrong:** Validation, dirty state, and error handling split across two models. The component becomes hard to reason about and easy to break during future changes.

**Correct approach:** Pick one form ownership model per save path. Use record-edit-form for supported record editing, or go fully custom when the UX truly requires it.
