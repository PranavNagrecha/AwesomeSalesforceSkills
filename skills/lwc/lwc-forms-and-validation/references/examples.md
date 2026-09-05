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

**What it looks like in markup** — the `Discount__c` control below is orphaned: it is inside the
form, so it looks saved, but `lightning-record-edit-form` only submits the fields it owns unless
the `onsubmit` handler folds the value in, and there is no `onsubmit` here.

```html
<!-- BROKEN: two ownership models, one Save button, no onsubmit -->
<lightning-record-edit-form object-api-name="Opportunity" record-id={recordId}>
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-input-field field-name="Amount"></lightning-input-field>

    <!-- not LDS-wired, never submitted, silently discarded on Save -->
    <lightning-input data-field="Discount" label="Discount %" value={discount}></lightning-input>

    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

**Correct approach:** Pick one form ownership model per save path, and if the hybrid shape is
genuinely needed, make the `onsubmit` handler the single owner of the field map.

| Symptom in review | Which model is leaking | Fix |
|---|---|---|
| A `lightning-input` sits inside the form with no `onsubmit` on the form | Hybrid without an owner | Add `onsubmit`, `preventDefault`, fold the value into `event.detail.fields`, then `submit(fields)` |
| `setCustomValidity()` called on a `lightning-input-field` | Custom rule on an LDS control | Swap that one control to `lightning-input` (`data-edit-record`:5513) |
| `onsuccess` present, `onerror` absent | Form model without its failure path | Add `onerror` and read `event.detail.output.fieldErrors` (`data-edit-record`:5509) |
| Imperative `createRecord` fired from inside a rendered `lightning-record-edit-form` | Two save paths on one screen | Delete one; the form's `submit()` and `createRecord` must not both own the save |
