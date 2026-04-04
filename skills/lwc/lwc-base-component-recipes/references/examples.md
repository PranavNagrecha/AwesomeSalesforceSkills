# Examples — LWC Base Component Recipes

## Example 1: lightning-record-form for Quick Create Modal

**Context:** A service console app needs a modal to create a new Case without navigating away from the current record. The form must support the standard Case fields and the default page layout.

**Problem:** Without guidance, developers reach for custom Apex + manual input fields, adding unnecessary complexity and bypassing FLS enforcement.

**Solution:**

```html
<!-- quickCaseCreate.html -->
<template>
  <lightning-record-form
    object-api-name="Case"
    fields={caseFields}
    onsuccess={handleSuccess}
    oncancel={handleCancel}
  ></lightning-record-form>
</template>
```

```js
// quickCaseCreate.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import SUBJECT_FIELD from '@salesforce/schema/Case.Subject';
import STATUS_FIELD from '@salesforce/schema/Case.Status';
import PRIORITY_FIELD from '@salesforce/schema/Case.Priority';
import DESCRIPTION_FIELD from '@salesforce/schema/Case.Description';

export default class QuickCaseCreate extends LightningElement {
  caseFields = [SUBJECT_FIELD, STATUS_FIELD, PRIORITY_FIELD, DESCRIPTION_FIELD];

  handleSuccess(event) {
    const caseId = event.detail.id;
    this.dispatchEvent(new ShowToastEvent({
      title: 'Case Created',
      message: `Case ${caseId} created successfully.`,
      variant: 'success',
    }));
    this.dispatchEvent(new CustomEvent('casecreated', { detail: { id: caseId } }));
  }

  handleCancel() {
    this.dispatchEvent(new CustomEvent('cancel'));
  }
}
```

**Why it works:** `lightning-record-form` handles the full create lifecycle — field rendering, FLS, submit, error display — with no Apex. Importing field references via `@salesforce/schema` provides compile-time field name validation.

---

## Example 2: lightning-record-edit-form with Conditional Pre-Save Validation

**Context:** A sales team's Opportunity edit form requires a business rule: the Close Date must not be set to a past date. This check must run before the record reaches the server, with a visible error message near the Close Date field.

**Problem:** `lightning-record-form` provides no `onsubmit` hook to intercept and cancel the save. Server-side validation rules would trigger an error, but the UX delay and generic error message placement frustrates users.

**Solution:**

```html
<!-- opportunityEditForm.html -->
<template>
  <lightning-record-edit-form
    record-id={recordId}
    object-api-name="Opportunity"
    onsubmit={handleSubmit}
    onsuccess={handleSuccess}
  >
    <lightning-messages></lightning-messages>
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-input-field field-name="StageName"></lightning-input-field>
    <lightning-input-field field-name="CloseDate" data-field="CloseDate"></lightning-input-field>
    <lightning-input-field field-name="Amount"></lightning-input-field>
    <div class="slds-m-top_small">
      <lightning-button type="submit" label="Save" variant="brand"></lightning-button>
      <lightning-button label="Cancel" onclick={handleCancel} class="slds-m-left_x-small"></lightning-button>
    </div>
  </lightning-record-edit-form>
</template>
```

```js
// opportunityEditForm.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class OpportunityEditForm extends LightningElement {
  @api recordId;

  handleSubmit(event) {
    event.preventDefault();
    const fields = event.detail.fields;
    const closeDate = fields.CloseDate;
    if (closeDate && new Date(closeDate) < new Date()) {
      this.dispatchEvent(new ShowToastEvent({
        title: 'Validation Error',
        message: 'Close Date cannot be in the past.',
        variant: 'error',
      }));
      return; // block the save
    }
    this.template.querySelector('lightning-record-edit-form').submit(fields);
  }

  handleSuccess() {
    this.dispatchEvent(new ShowToastEvent({
      title: 'Saved',
      message: 'Opportunity updated successfully.',
      variant: 'success',
    }));
  }

  handleCancel() {
    this.dispatchEvent(new CustomEvent('cancel'));
  }
}
```

**Why it works:** `event.preventDefault()` in `onsubmit` stops the UI API call. The form's fields are accessible via `event.detail.fields`, allowing pre-save inspection. Only after validation passes is `submit(fields)` called explicitly.

---

## Example 3: lightning-datatable with Row Actions and Inline Editing

**Context:** An admin dashboard shows a list of Contact records with inline editable Phone and Email fields and a row-level "View" action that navigates to the record detail page.

**Problem:** Developers who set `editable: true` on columns but never wire `draft-values` and `onsave` end up with inline edit UI that appears to work but silently discards changes.

**Solution:**

```html
<!-- contactTable.html -->
<template>
  <lightning-datatable
    key-field="Id"
    data={contacts}
    columns={columns}
    draft-values={draftValues}
    onsave={handleSave}
    onrowaction={handleRowAction}
  ></lightning-datatable>
</template>
```

```js
// contactTable.js
import { LightningElement, wire } from 'lwc';
import { updateRecord } from 'lightning/uiRecordApi';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getContacts from '@salesforce/apex/ContactController.getContacts';

const ACTIONS = [{ label: 'View', name: 'view' }];

export default class ContactTable extends NavigationMixin(LightningElement) {
  contacts = [];
  draftValues = [];

  columns = [
    { label: 'Name', fieldName: 'Name', type: 'text' },
    { label: 'Phone', fieldName: 'Phone', type: 'phone', editable: true },
    { label: 'Email', fieldName: 'Email', type: 'email', editable: true },
    { type: 'action', typeAttributes: { rowActions: ACTIONS } },
  ];

  @wire(getContacts)
  wiredContacts({ data, error }) {
    if (data) this.contacts = data;
    if (error) console.error(error);
  }

  async handleSave(event) {
    const updates = event.detail.draftValues;
    try {
      await Promise.all(
        updates.map(row => updateRecord({ fields: { Id: row.Id, ...row } }))
      );
      this.draftValues = [];
      this.dispatchEvent(new ShowToastEvent({ title: 'Saved', variant: 'success', message: 'Records updated.' }));
    } catch (e) {
      this.dispatchEvent(new ShowToastEvent({ title: 'Error', variant: 'error', message: e.body?.message }));
    }
  }

  handleRowAction(event) {
    const { name } = event.detail.action;
    const row = event.detail.row;
    if (name === 'view') {
      this[NavigationMixin.Navigate]({
        type: 'standard__recordPage',
        attributes: { recordId: row.Id, actionName: 'view' },
      });
    }
  }
}
```

**Why it works:** `draft-values` is the two-way binding that tracks pending edits. Resetting it to `[]` after a successful save dismisses the inline edit toolbar. Row actions are driven by column type `'action'` and handled in `onrowaction`.

---

## Anti-Pattern: Using lightning-record-form When Field Order Matters

**What practitioners do:** They add a `fields` attribute with fields in desired display order, expecting the form to render them in that sequence.

**What goes wrong:** `lightning-record-form` renders fields in the order dictated by the page layout assigned to the running user, not the JavaScript array order. On an org with a custom page layout, fields silently reorder. The issue is often not caught in development (where admins use a permissive layout) but surfaces in production.

**Correct approach:** Switch to `lightning-record-edit-form` with explicit `lightning-input-field` elements in the desired order in the HTML template. This gives deterministic field placement regardless of page layout configuration.
