# Examples — LWC Lightning Record Forms

## Example 1: One-tag form with `lightning-record-form`

The simplest production form: object, record Id, layout-type. LDS
fills in everything else.

```html
<template>
    <lightning-record-form
        record-id={recordId}
        object-api-name="Account"
        layout-type="Full"
        mode="view"
        onsuccess={handleSuccess}>
    </lightning-record-form>
</template>
```

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class AccountForm extends LightningElement {
    @api recordId;
    handleSuccess() {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Saved', variant: 'success'
        }));
    }
}
```

`mode="view"` shows fields with an Edit button; `"edit"` opens
straight to edit; `"readonly"` removes the Edit button entirely.

---

## Example 2: Custom layout with `lightning-record-edit-form`

When the page-layout-driven shape doesn't fit (you need columns,
conditional sections, or a non-standard button bar):

```html
<template>
    <lightning-record-edit-form
        record-id={recordId}
        object-api-name="Case"
        onsubmit={handleSubmit}
        onsuccess={handleSuccess}
        onerror={handleError}>

        <lightning-messages></lightning-messages>

        <div class="slds-grid slds-gutters">
            <div class="slds-col slds-size_1-of-2">
                <lightning-input-field field-name={subjectField}>
                </lightning-input-field>
                <lightning-input-field field-name={priorityField}>
                </lightning-input-field>
            </div>
            <div class="slds-col slds-size_1-of-2">
                <lightning-input-field field-name={statusField}>
                </lightning-input-field>
            </div>
        </div>

        <div class="slds-m-top_medium">
            <lightning-button
                type="submit" label="Save" variant="brand">
            </lightning-button>
            <lightning-button
                label="Cancel" onclick={handleCancel}>
            </lightning-button>
        </div>
    </lightning-record-edit-form>
</template>
```

```js
import { LightningElement, api } from 'lwc';
import SUBJECT  from '@salesforce/schema/Case.Subject';
import PRIORITY from '@salesforce/schema/Case.Priority';
import STATUS   from '@salesforce/schema/Case.Status';

export default class CaseForm extends LightningElement {
    @api recordId;
    subjectField  = SUBJECT;
    priorityField = PRIORITY;
    statusField   = STATUS;
}
```

Field references imported via `@salesforce/schema` enable LDS to
validate the field exists at compile time and to enforce FLS.

---

## Example 3: Mutating fields in `onsubmit` for conditional defaults

`onsubmit` runs before LDS persists; you can rewrite the payload.

```js
handleSubmit(event) {
    event.preventDefault();
    const fields = event.detail.fields;
    if (!fields.OwnerId) {
        fields.OwnerId = this.defaultOwnerId;
    }
    fields.Source__c = 'LWC Form';
    this.refs.form.submit(fields);
}
```

```html
<lightning-record-edit-form
    lwc:ref="form"
    object-api-name="Case"
    onsubmit={handleSubmit}>
    ...
</lightning-record-edit-form>
```

Calling `this.refs.form.submit(fields)` re-enters the LDS save
path with your modified payload. `event.preventDefault()` is
required — without it, the form submits twice.

---

## Example 4: Read-only view with `lightning-record-view-form`

When you need a custom read-only layout (e.g. a side panel) and
LDS-managed FLS:

```html
<lightning-record-view-form
    record-id={recordId}
    object-api-name="Opportunity">

    <lightning-output-field field-name={nameField}></lightning-output-field>
    <lightning-output-field field-name={amountField}></lightning-output-field>
    <lightning-output-field field-name={stageField}></lightning-output-field>
    <lightning-output-field
        field-name={closeDateField}
        variant="label-hidden">
    </lightning-output-field>
</lightning-record-view-form>
```

`lightning-output-field` respects FLS — if the running user lacks
read on `Amount`, the field renders nothing rather than throwing.
Visual: empty space where the field would be. If you need a
different fallback ("Restricted"), wrap in a wire and conditionally
render.

---

## Example 5: Create form with prepopulated values

```html
<lightning-record-edit-form
    object-api-name="Contact"
    onsuccess={handleCreated}>

    <lightning-input-field
        field-name={firstNameField}
        value={defaultFirstName}>
    </lightning-input-field>
    <lightning-input-field field-name={lastNameField}></lightning-input-field>
    <lightning-input-field field-name={emailField}></lightning-input-field>

    <div class="slds-m-top_medium">
        <lightning-button type="submit" label="Create" variant="brand">
        </lightning-button>
    </div>
</lightning-record-edit-form>
```

Omitting `record-id` puts the form in create mode. The `value`
attribute on `lightning-input-field` provides a default that the
user can override. `onsuccess` fires with `event.detail.id` set
to the new record's Id.
