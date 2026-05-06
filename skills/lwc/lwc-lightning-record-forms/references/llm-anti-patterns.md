# LLM Anti-Patterns — LWC Lightning Record Forms

Common mistakes AI coding assistants make when generating LDS form code.

---

## Anti-Pattern 1: Hand-rolled form with `@wire(getRecord)` + custom DML

**What the LLM generates.**

```js
import { getRecord, updateRecord } from 'lightning/uiRecordApi';
@wire(getRecord, { recordId: '$recordId', fields: FIELDS }) record;
async save() {
    await updateRecord({ fields: { Id: this.recordId, ... } });
}
```

**Correct pattern.** Use `lightning-record-edit-form` — it gives
you the wire, the save, FLS enforcement, and inline error UI for
free. Reach for `uiRecordApi` only when you need create-without-Id
+ post-create navigation in one transaction.

**Detection hint.** Any LWC that imports both `getRecord` and
`updateRecord` AND renders form-shaped HTML is reinventing
`lightning-record-edit-form`.

---

## Anti-Pattern 2: String-literal `field-name`

**What the LLM generates.**

```html
<lightning-input-field field-name="Subject"></lightning-input-field>
```

**Correct pattern.**

```js
import SUBJECT from '@salesforce/schema/Case.Subject';
// in template:
// <lightning-input-field field-name={subjectField}></lightning-input-field>
```

The string form is accepted but loses compile-time validation,
FLS enforcement, and safe refactoring.

**Detection hint.** Any `field-name="..."` (literal string) in a
`lightning-record-edit-form` / `-view-form` template.

---

## Anti-Pattern 3: Setting both `layout-type` and `fields`

**What the LLM generates.**

```html
<lightning-record-form
    layout-type="Full"
    fields={fieldsArray}>
</lightning-record-form>
```

**Correct pattern.** Pick one: `layout-type` for admin-editable
shape, `fields` for fixed shape. Both is a runtime error.

**Detection hint.** Any `lightning-record-form` element with both
attributes set.

---

## Anti-Pattern 4: Calling `apex` save inside `lightning-record-edit-form`

**What the LLM generates.**

```js
async handleSubmit(event) {
    event.preventDefault();
    await saveCaseApex({ fields: event.detail.fields });
}
```

**Correct pattern.** Either use the form's native LDS save
(remove the Apex call entirely), or use a custom form (no
`lightning-record-edit-form`). Mixing is fragile — you lose the
LDS validation UX and re-implement everything.

**Detection hint.** Any `@AuraEnabled` Apex call inside a
`handleSubmit` for a `lightning-record-edit-form`.

---

## Anti-Pattern 5: Using `aura:recordEditForm` in new components

**What the LLM generates.** A `<aura:component>` with
`<lightning:recordEditForm>` and `<aura:if>` blocks.

**Correct pattern.** Aura is deprecated for new development.
Build LWC with `lightning-record-edit-form`. Same component,
modern shell.

**Detection hint.** Any `.cmp` file with `lightning:recordEditForm`
in a project that targets Spring '25 or later.

---

## Anti-Pattern 6: Catching FLS denials with try/catch

**What the LLM generates.**

```js
try {
    this.refs.form.submit();
} catch (err) {
    if (err.message.includes('FLS')) { /* hide field */ }
}
```

**Correct pattern.** FLS denials don't throw — `lightning-input-field`
renders empty or read-only. To detect, query
`getObjectInfo`/`getRecord` and inspect the `fields[X].editable`
boolean.

**Detection hint.** Any `try/catch` around `this.refs.form.submit()`
that pattern-matches on field-level error strings.

---

## Anti-Pattern 7: Forgetting `<lightning-messages>` slot

**What the LLM generates.** A `lightning-record-edit-form` with
custom buttons and no `<lightning-messages>` element.

**Correct pattern.** `<lightning-messages></lightning-messages>`
inside the form is where validation rule errors render. Without
it, the user clicks Save, the form does nothing, and there's no
visible feedback.

**Detection hint.** Any `lightning-record-edit-form` with a
`type="submit"` button but no `lightning-messages` child element.
