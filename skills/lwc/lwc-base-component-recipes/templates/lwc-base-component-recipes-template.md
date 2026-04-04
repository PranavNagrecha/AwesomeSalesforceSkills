# LWC Base Component Recipes — Work Template

Use this template when building or reviewing LWC components that use `lightning-record-form`, `lightning-record-edit-form`, `lightning-record-view-form`, or `lightning-datatable`.

---

## Scope

**Skill:** `lwc-base-component-recipes`

**Request summary:** (fill in what the user asked for — e.g., "build an edit form for Contact with custom Save button")

---

## Context Gathered

Answer these before writing any markup:

- **Object API name:** (e.g., `Contact`, `Opportunity`, `Custom_Object__c`)
- **Fields required (API names):** (e.g., `FirstName`, `LastName`, `Email`)
- **Record ID source:** (e.g., `@api recordId` from page, parent component, navigation state)
- **Mode:** create / edit / view / table
- **Custom layout needed?** (custom field order, custom buttons, pre-save validation) — Yes / No
- **Table interactions needed?** (inline editing, row actions, sorting, infinite scroll) — Yes / No
- **FLS-sensitive fields?** (fields that differ by profile) — Yes / No

---

## Component Selection

Based on the context above, choose the base component:

| Requirement | Component |
|---|---|
| Standard layout, no custom buttons | `lightning-record-form` |
| Custom field order or custom Save button | `lightning-record-edit-form` |
| Read-only detail display | `lightning-record-view-form` |
| Tabular data with sorting/editing | `lightning-datatable` |

**Selected component:** _______________

**Reason:** _______________

---

## Markup Skeleton

### For lightning-record-form

```html
<lightning-record-form
  object-api-name="OBJECT_API_NAME"
  record-id={recordId}
  fields={fields}
  mode="edit"
  onsuccess={handleSuccess}
  oncancel={handleCancel}
></lightning-record-form>
```

```js
import FIELD_ONE from '@salesforce/schema/Object.FieldOne';
import FIELD_TWO from '@salesforce/schema/Object.FieldTwo';

fields = [FIELD_ONE, FIELD_TWO];
```

### For lightning-record-edit-form

```html
<lightning-record-edit-form
  object-api-name="OBJECT_API_NAME"
  record-id={recordId}
  onsubmit={handleSubmit}
  onsuccess={handleSuccess}
  onerror={handleError}
>
  <lightning-messages></lightning-messages>
  <lightning-input-field field-name="FieldOne__c"></lightning-input-field>
  <lightning-input-field field-name="FieldTwo__c"></lightning-input-field>
  <lightning-button type="submit" label="Save" variant="brand"></lightning-button>
  <lightning-button label="Cancel" onclick={handleCancel}></lightning-button>
</lightning-record-edit-form>
```

### For lightning-datatable

```html
<lightning-datatable
  key-field="Id"
  data={tableData}
  columns={columns}
  draft-values={draftValues}
  onsave={handleSave}
  onrowaction={handleRowAction}
></lightning-datatable>
```

```js
draftValues = [];
columns = [
  { label: 'Name', fieldName: 'Name', type: 'text' },
  { label: 'Phone', fieldName: 'Phone', type: 'phone', editable: true },
  { type: 'action', typeAttributes: { rowActions: [{ label: 'View', name: 'view' }] } },
];

async handleSave(event) {
  const updates = event.detail.draftValues;
  try {
    await Promise.all(updates.map(row => updateRecord({ fields: { Id: row.Id, ...row } })));
  } finally {
    this.draftValues = []; // always reset
  }
}
```

---

## Review Checklist

Copy from SKILL.md and tick items as you complete them:

- [ ] `object-api-name` uses the API name, not the label
- [ ] `record-id` is bound via `@api recordId`, not hardcoded
- [ ] `key-field` on `lightning-datatable` is set (must be unique across all rows)
- [ ] `draft-values` is reset to `[]` after a successful inline edit save
- [ ] FLS tested with a restricted profile user, not as System Administrator
- [ ] `onsuccess` handler fires a toast or navigates; form is not left in stale state
- [ ] `lightning-messages` present inside `lightning-record-edit-form` when using custom submit button
- [ ] Form visibility toggled via CSS class (`slds-hide`), not `if:true`, to preserve unsaved state

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Using Apex-backed form instead because field X requires cross-object calculation")
