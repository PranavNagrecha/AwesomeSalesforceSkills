# LLM Anti-Patterns — LWC Base Component Recipes

Common mistakes AI coding assistants make when generating or advising on lightning-record-form, lightning-record-edit-form, lightning-record-view-form, and lightning-datatable.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using lightning-record-edit-form when lightning-record-form would suffice

**What the LLM generates:**

```html
<lightning-record-edit-form record-id={recordId} object-api-name="Account">
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-input-field field-name="Phone"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

**Why it happens:** LLMs default to `lightning-record-edit-form` because it appears in more training examples. For simple view/edit with standard layout and no custom submit logic, `lightning-record-form` with `mode="edit"` handles both modes with less markup.

**Correct pattern:**

```html
<lightning-record-form
    record-id={recordId}
    object-api-name="Account"
    fields={fields}
    mode="edit">
</lightning-record-form>
```

Use `lightning-record-edit-form` only when you need custom layout, custom buttons, or field-level validation control.

**Detection hint:** `lightning-record-edit-form` with only `lightning-input-field` children and a standard submit button, no custom handlers.

---

## Anti-Pattern 2: Hardcoding field API names as strings instead of importing them

**What the LLM generates:**

```javascript
fields = ['Name', 'Phone', 'Industry'];
```

**Why it happens:** String literals are simpler and appear in quick-start guides. LLMs prefer brevity over the import-based approach that provides compile-time validation and namespace awareness.

**Correct pattern:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
import PHONE_FIELD from '@salesforce/schema/Account.Phone';
import INDUSTRY_FIELD from '@salesforce/schema/Account.Industry';

fields = [NAME_FIELD, PHONE_FIELD, INDUSTRY_FIELD];
```

**Detection hint:** `fields` array or `field-name` attribute containing bare string literals instead of imported schema references.

---

## Anti-Pattern 3: Using lightning-record-view-form without lightning-output-field children

**What the LLM generates:**

```html
<lightning-record-view-form record-id={recordId} object-api-name="Account">
    <div class="slds-grid">
        <p>{record.fields.Name.value}</p>
    </div>
</lightning-record-view-form>
```

**Why it happens:** LLMs wrap manual field rendering inside `lightning-record-view-form` without understanding that the component provides its value through `lightning-output-field` children, not through JavaScript record references.

**Correct pattern:**

```html
<lightning-record-view-form record-id={recordId} object-api-name="Account">
    <div class="slds-grid">
        <lightning-output-field field-name="Name"></lightning-output-field>
    </div>
</lightning-record-view-form>
```

**Detection hint:** `lightning-record-view-form` that contains no `lightning-output-field` elements.

---

## Anti-Pattern 4: Not handling the onsuccess event to show user feedback after save

**What the LLM generates:**

```html
<lightning-record-edit-form record-id={recordId} object-api-name="Account">
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
<!-- No onsuccess, onerror, or onsubmit handlers -->
```

**Why it happens:** The form submits and saves without explicit handlers, so LLMs treat them as optional. Users get no visual confirmation of success or failure.

**Correct pattern:**

```html
<lightning-record-edit-form
    record-id={recordId}
    object-api-name="Account"
    onsuccess={handleSuccess}
    onerror={handleError}>
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

```javascript
handleSuccess() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Success', message: 'Record saved.', variant: 'success'
    }));
}
```

**Detection hint:** `lightning-record-edit-form` without `onsuccess` or `onerror` attributes.

---

## Anti-Pattern 5: Using lightning-datatable without a stable key-field

**What the LLM generates:**

```html
<lightning-datatable
    data={records}
    columns={columns}
    key-field="index">
</lightning-datatable>
```

**Why it happens:** LLMs sometimes use array index or a non-unique field as the key. This causes row identity issues with selection, inline editing, and sorting.

**Correct pattern:**

```html
<lightning-datatable
    data={records}
    columns={columns}
    key-field="Id">
</lightning-datatable>
```

Always use a stable, unique identifier like the Salesforce `Id` field.

**Detection hint:** `key-field` set to `"index"`, `"name"`, or any field that is not guaranteed unique per row.

---

## Anti-Pattern 6: Overriding onsubmit without calling event.preventDefault() and submitting manually

**What the LLM generates:**

```javascript
handleSubmit(event) {
    // Tries to modify fields but does not prevent default submission
    const fields = event.detail.fields;
    fields.Status__c = 'Submitted';
    // Form submits twice — once from default, once from manual call
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

**Why it happens:** LLMs know that `onsubmit` provides access to field values but forget that the form will auto-submit unless `preventDefault()` is called first.

**Correct pattern:**

```javascript
handleSubmit(event) {
    event.preventDefault();
    const fields = event.detail.fields;
    fields.Status__c = 'Submitted';
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

**Detection hint:** `onsubmit` handler that calls `.submit()` without a preceding `event.preventDefault()`.
