# LWC Base Component Recipes — Work Template

Use this template when building or reviewing LWC components built from Lightning base components — the record\*form family, `lightning-datatable`, and the everyday composites (`lightning-card`, `lightning-layout`, `lightning-combobox`, `lightning-button-menu`, `lightning-spinner`, `lightning-accordion`, `lightning-tabset`).

**Before you fill anything in:** the Component Library is the authority for every attribute, event and slot. The LWC Developer Guide does not publish attribute tables. Anything you cannot confirm there goes in the Assumptions list at the bottom, not into the markup unmarked.

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

## Base-Component-First Decision

For each visual element on the screen, record the verdict before writing markup:

| Element | Base component? | If none — blueprint / third-party / custom | Verdict |
|---|---|---|---|
| (e.g., status pill) | `lightning-badge` | — | base |
| | | | |
| | | | |

Rule: prefer a base component; Salesforce updates it when SLDS updates the blueprint, while
blueprint markup copied into your bundle is yours to maintain forever.

**Container check** (decides `<supportedFormFactors>` and the toast module):

- [ ] Lightning Experience  - [ ] LWR Experience Cloud site  - [ ] Salesforce mobile app  - [ ] Quick action
- [ ] No `lightning-datatable` / `lightning-tree-grid` if mobile is in scope (unsupported there)
- [ ] Toast module is `lightning/toast` if any Experience Cloud target is in scope

---

## Composite Skeleton (card + layout + combobox + menu + spinner + read-only summary)

```html
<lightning-card title="TITLE" icon-name="standard:account">
  <lightning-button-menu slot="actions" alternative-text="Actions" onselect={handleMenuSelect}>
    <lightning-menu-item value="refresh" label="Refresh"></lightning-menu-item>
  </lightning-button-menu>

  <div class="slds-var-p-horizontal_medium">
    <template lwc:if={isLoading}>
      <lightning-spinner alternative-text="Loading" size="small"></lightning-spinner>
    </template>

    <lightning-layout multiple-rows="true">
      <lightning-layout-item size="12" small-device-size="6" padding="around-small">
        <lightning-combobox label="LABEL" value={value} options={options}
                            onchange={handleChange}></lightning-combobox>
      </lightning-layout-item>
      <lightning-layout-item size="12" small-device-size="6" padding="around-small">
        <lightning-record-view-form record-id={recordId} object-api-name="OBJECT_API_NAME">
          <lightning-output-field field-name="FIELD_API_NAME"></lightning-output-field>
        </lightning-record-view-form>
      </lightning-layout-item>
    </lightning-layout>
  </div>
</lightning-card>
```

Three nesting rules this skeleton encodes — all three fail silently if broken:

- `lightning-output-field` is a **direct child** of `lightning-record-view-form`. Put the form in the layout item, never the fields.
- Only `lightning-layout-item` (plus plain HTML and text) sits directly inside `lightning-layout`.
- Card actions go in the `actions` **slot**; `title` and `footer` are text-only attributes in LWC.

```js
// picklist chain: getObjectInfo -> defaultRecordTypeId -> getPicklistValues
recordTypeId = '012000000000000AAA'; // master record type fallback

@wire(getObjectInfo, { objectApiName: OBJECT })
wiredInfo({ data }) { if (data) this.recordTypeId = data.defaultRecordTypeId || this.recordTypeId; }

@wire(getPicklistValues, { recordTypeId: '$recordTypeId', fieldApiName: FIELD })
wiredValues({ data }) {
  // save `value` (untranslated API name); display `label` (translated)
  if (data) this.options = data.values.map(v => ({ label: v.label, value: v.value }));
}
```

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
- [ ] Every input component (`lightning-input`, `lightning-combobox`, `lightning-select`, `lightning-radio-group`, `lightning-checkbox-group`) has a `label`
- [ ] Every `lightning-output-field` is a direct child of its `lightning-record-view-form`
- [ ] Only `lightning-layout-item` sits directly inside `lightning-layout`
- [ ] No raw `slds-*` markup where a base component exists; no CSS targeting base-component internals
- [ ] `.js-meta.xml` declares `<supportedFormFactors>`; `Small` absent from any datatable bundle
- [ ] Jest assertions read properties off the base-component stub and dispatch events at it
- [ ] Checker run clean: `python3 scripts/check_lwc_base_component_recipes.py --manifest-dir <dir> --strict`

---

## Assumptions to Verify

Every attribute used that you could not confirm on the Component Library Specification tab:

| Component | Attribute / event | Where used | Confirmed? |
|---|---|---|---|
| | | | |

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Using Apex-backed form instead because field X requires cross-object calculation")
