# LLM Anti-Patterns — LWC Forms and Validation

Common mistakes AI coding assistants make when generating or advising on LWC form design and validation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Calling reportValidity() on the form instead of individual inputs

**What the LLM generates:**

```javascript
handleSave() {
    const form = this.template.querySelector('lightning-record-edit-form');
    if (form.reportValidity()) { // reportValidity is not a method on the form
        form.submit();
    }
}
```

**Why it happens:** LLMs assume `reportValidity()` exists on the form wrapper. It is actually a method on individual `lightning-input`, `lightning-combobox`, and similar input components.

**Correct pattern:**

```javascript
handleSave() {
    const inputs = this.template.querySelectorAll('lightning-input, lightning-combobox');
    const allValid = [...inputs].reduce((valid, input) => {
        input.reportValidity();
        return valid && input.checkValidity();
    }, true);

    if (allValid) {
        this.template.querySelector('lightning-record-edit-form').submit();
    }
}
```

**Detection hint:** `reportValidity()` called on `lightning-record-edit-form` or a non-input element.

---

## Anti-Pattern 2: Using setCustomValidity without calling reportValidity afterward

**What the LLM generates:**

```javascript
handleValidate() {
    const input = this.template.querySelector('lightning-input');
    if (this.isDuplicate) {
        input.setCustomValidity('Duplicate value detected.');
        // Missing reportValidity() — error message never shows
    }
}
```

**Why it happens:** LLMs know `setCustomValidity` sets the message but forget that `reportValidity()` must be called afterward to display it. Without the second call, the UI shows no error.

**Correct pattern:**

```javascript
handleValidate() {
    const input = this.template.querySelector('lightning-input');
    if (this.isDuplicate) {
        input.setCustomValidity('Duplicate value detected.');
    } else {
        input.setCustomValidity(''); // Clear previous error
    }
    input.reportValidity();
}
```

**Detection hint:** `setCustomValidity(` without a following `reportValidity()` call on the same element.

---

## Anti-Pattern 3: Not clearing custom validity before re-validation

**What the LLM generates:**

```javascript
handleBlur() {
    const input = this.template.querySelector('[data-id="email"]');
    if (!this.isValidEmail(input.value)) {
        input.setCustomValidity('Enter a valid email.');
        input.reportValidity();
    }
    // Never clears validity — once invalid, always invalid
}
```

**Why it happens:** LLMs set the error state but never reset it. Once `setCustomValidity` is called with a non-empty string, the input stays invalid even after the user corrects the value.

**Correct pattern:**

```javascript
handleBlur() {
    const input = this.template.querySelector('[data-id="email"]');
    if (!this.isValidEmail(input.value)) {
        input.setCustomValidity('Enter a valid email.');
    } else {
        input.setCustomValidity('');
    }
    input.reportValidity();
}
```

**Detection hint:** `setCustomValidity` with a non-empty message and no matching `setCustomValidity('')` in an else branch or prior reset.

---

## Anti-Pattern 4: Bypassing lightning-record-edit-form error handling by using imperative Apex for save

**What the LLM generates:**

```html
<lightning-record-edit-form object-api-name="Account">
    <lightning-input-field field-name="Name"></lightning-input-field>
</lightning-record-edit-form>
```

```javascript
handleSave() {
    // Ignores the form entirely and calls Apex
    createAccount({ name: this.name });
}
```

**Why it happens:** LLMs sometimes scaffold the form for layout but wire the save to imperative Apex, losing built-in FLS enforcement, validation rule error surfacing, and duplicate rule handling.

**Correct pattern:**

Let `lightning-record-edit-form` handle the save via its `submit()` method, and use `onerror` to display server-side errors:

```html
<lightning-record-edit-form
    object-api-name="Account"
    onsuccess={handleSuccess}
    onerror={handleError}>
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

**Detection hint:** `lightning-record-edit-form` in the template combined with an imperative Apex save call in the JS that writes to the same object.

---

## Anti-Pattern 5: Using required attribute on every lightning-input-field indiscriminately

**What the LLM generates:**

```html
<lightning-input-field field-name="Name" required></lightning-input-field>
<lightning-input-field field-name="Description" required></lightning-input-field>
<lightning-input-field field-name="Phone" required></lightning-input-field>
```

**Why it happens:** LLMs add `required` to every `lightning-input-field` for "safety." But `lightning-input-field` inherits required state from the field's metadata. Adding it everywhere creates mismatch between UI and server enforcement.

**Correct pattern:**

For `lightning-input-field`, rely on the field metadata for required behavior. Only add `required` when you intentionally need the UI to be stricter than the schema:

```html
<lightning-input-field field-name="Name"></lightning-input-field>
<lightning-input-field field-name="Description"></lightning-input-field>
<lightning-input-field field-name="Custom_Required__c" required></lightning-input-field>
```

**Detection hint:** `required` on every `lightning-input-field` without consideration of which fields are actually required in the object schema.

---

## Anti-Pattern 6: Not surfacing server-side validation rule errors to the user

**What the LLM generates:**

```javascript
handleError(event) {
    console.error('Save failed', event.detail);
    // User sees nothing
}
```

**Why it happens:** LLMs log errors to the console but do not display them. Validation rule messages, duplicate rule messages, and trigger exceptions from `onerror` need to be shown to the user.

**Correct pattern:**

```javascript
handleError(event) {
    const message = event.detail?.message || 'An error occurred.';
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: message,
        variant: 'error'
    }));
}
```

**Detection hint:** `onerror` handler that only calls `console.error` or `console.log` with no user-visible feedback.

---

## Anti-Pattern 7: An onsubmit handler that augments fields but never calls preventDefault()

**What the LLM generates:**

```javascript
handleSubmit(event) {
    const fields = event.detail.fields;
    fields.Email = fields.Email.trim().toLowerCase();
    // No event.preventDefault() — the form already submitted the raw values
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

**Why it happens:** The handler reads like ordinary JavaScript, so the model assumes mutating
`event.detail.fields` mutates what gets saved. It does not — the guide's instruction is to
validate and update the fields *in the handler and submit the record data through it*
(`data-edit-record`:5516), which only works when the default submission is stopped first. The
symptom is nasty: the record saves, so nothing looks broken, but the normalisation, the derived
field, and any blocked-save logic are all silently ignored.

**Correct pattern:**

```javascript
handleSubmit(event) {
    event.preventDefault();
    const fields = { ...event.detail.fields };
    fields.Email = (fields.Email || '').trim().toLowerCase();
    if (!this.validateConfirmEmail(fields.Email)) {
        return; // no submit() call, no save
    }
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

UNVERIFIED (2026-09-05): `preventDefault()` on the form's submit event and the `submit(fields)`
method are Component Library facts; the Developer Guide describes the handler's job
(`data-edit-record`:5516) but not these two API details.

**Detection hint:** `onsubmit={handler}` in the template where the handler body references
`detail.fields` or assigns a `fields` object, with no `preventDefault()` call. Implemented as
check C3 in `scripts/check_lwc_forms_and_validation.py`.

---

## Anti-Pattern 8: Reusing a read-error reducer on a write rejection

**What the LLM generates:**

```javascript
async handleCreate() {
    try {
        const record = await createRecord(this.recordInput);
        this.recordId = record.id;
    } catch (error) {
        // Written for a getRecord wire error, where body is an ARRAY
        this.message = error.body.map((e) => e.message).join(', ');
    }
}
```

**Why it happens:** The same `reduceErrors()` helper is copied across every component in a repo,
and it was originally written against a wire adapter. UI API **read** operations return
`error.body` as an array of objects; UI API **write** operations such as `createRecord` return
`error.body` as an object, often carrying object-level and field-level errors
(`data-error`:6568–6569). The array method throws or yields `undefined`, so the user gets a blank
or generic failure while the server was returning a precise reason.

**Correct pattern:**

```javascript
catch (error) {
    const body = (error && error.body) || {};
    if (Array.isArray(body)) {
        this.message = body.map((e) => e.message).join(', ');
    } else {
        const fieldErrors = (body.output && body.output.fieldErrors) || {};
        Object.keys(fieldErrors).forEach((field) => {
            const input = this.template.querySelector(`[data-field="${field}"]`);
            if (input) {
                input.setCustomValidity(fieldErrors[field].map((e) => e.message).join(' '));
                input.reportValidity();
            }
        });
        this.message = body.message || 'Save failed.';
    }
}
```

**Detection hint:** `error.body.map(` or `error.body.forEach(` in a `catch` that follows a
`createRecord` / `updateRecord` / `deleteRecord` call, with no `Array.isArray` branch. Related
checker rule: C5 flags the harder failure — an LDS write with no `catch` at all.
