# Examples — LWC Custom Datatable Types

## Example 1: Status Pill Column Colored By Variant

**Context:** A case-triage datatable needs a `Priority` column rendered as a colored pill (`new`, `warning`, `error`, `success`) so agents can scan severity at a glance.

**Problem:** `lightning-datatable` has no pill/badge cell type. Dumping the status as plain text loses the color affordance; hacking the cell through a `formatter` does not exist on the base datatable.

**Solution:**

```javascript
// customDatatable.js
import LightningDatatable from 'lightning/datatable';
import statusPillTpl from './customPill.html';

export default class CustomDatatable extends LightningDatatable {
    static customTypes = {
        statusPill: {
            template: statusPillTpl,
            standardCellLayout: true,
            typeAttributes: ['variant', 'label']
        }
    };
}
```

```html
<!-- customPill.html -->
<template>
    <span class={pillClass}>
        <lightning-icon
            icon-name={typeAttributes.iconName}
            size="xx-small"
            class="slds-m-right_xx-small">
        </lightning-icon>
        {typeAttributes.label}
    </span>
</template>
```

Host column config on the consumer side:

```javascript
columns = [
    { label: 'Case', fieldName: 'caseNumber', type: 'text' },
    {
        label: 'Priority',
        fieldName: 'priority',           // primitive string — used for sorting
        type: 'statusPill',
        sortable: true,
        typeAttributes: {
            variant: { fieldName: 'priorityVariant' }, // e.g. 'error', 'warning'
            label:   { fieldName: 'priorityLabel' },
            iconName:{ fieldName: 'priorityIcon'  }    // NOT in typeAttributes array → silently dropped
        }
    }
];
```

**Why it works:** The subclass registers the type once, the template is a trivial SLDS span, and the column's `fieldName` stays a scalar so built-in sorting behaves. The `iconName` example also shows the exact failure mode the checker flags: the column binds `iconName`, but it is missing from `customTypes.typeAttributes`, so the template sees `undefined` and the icon never renders. Adding `'iconName'` to the array fixes it.

---

## Example 2: Inline Editable Picklist Via `editTemplate`

**Context:** An opportunity grid needs the `Stage` column editable without opening a record modal — agents should change stage inline and save all edits with a single Save button.

**Problem:** The built-in `editable: true` works for text/number/date, but not for picklists. Without a custom `editTemplate`, the double-click-to-edit affordance renders a text box, and the user can type in any string.

**Solution:**

```javascript
// customDatatable.js
import LightningDatatable from 'lightning/datatable';
import picklistTpl     from './editPicklist.html';
import picklistEditTpl from './editPicklistEdit.html';

export default class CustomDatatable extends LightningDatatable {
    static customTypes = {
        editPicklist: {
            template: picklistTpl,
            editTemplate: picklistEditTpl,
            standardCellLayout: true,
            typeAttributes: ['options', 'placeholder', 'context']
        }
    };
}
```

```html
<!-- editPicklist.html (read-only) -->
<template>
    <span>{value}</span>
</template>
```

```html
<!-- editPicklistEdit.html (inline edit) -->
<template>
    <lightning-combobox
        name="stage"
        label="Stage"
        variant="label-hidden"
        value={value}
        placeholder={typeAttributes.placeholder}
        options={typeAttributes.options}>
    </lightning-combobox>
</template>
```

Consumer column config:

```javascript
columns = [
    { label: 'Name', fieldName: 'name', type: 'text' },
    {
        label: 'Stage',
        fieldName: 'stage',
        type: 'editPicklist',
        editable: true,
        typeAttributes: {
            options: { fieldName: 'stageOptions' },
            placeholder: 'Select stage'
        }
    }
];
```

Host component handles the save:

```javascript
handleSave(event) {
    const drafts = event.detail.draftValues; // [{ Id, stage: 'Negotiation' }, ...]
    // call Apex / UI API update, then clear drafts
}
```

**Why it works:** The `editTemplate` binds `value={value}`, which is the hook the datatable uses to capture the draft. Combined with `editable: true` on the column, the datatable renders the pencil icon, surfaces the combobox on double-click, captures the draft into `event.detail.draftValues`, and lets the host component save all drafts at once.

---

## Anti-Pattern: Embedding A Full Form Or Toolbar Inside A Custom Cell

**What practitioners do:** Drop a `<lightning-record-edit-form>` with four or five fields inside the custom cell template, or render a six-button action toolbar with icons and menus per row to "keep everything in the grid."

**What goes wrong:** `lightning-datatable` virtualizes rows, but every visible row now instantiates a full record-edit form (which itself wires layout metadata, field-level security, and child inputs) or a heavyweight button group. Scrolling drops frames after ~100 rows, memory balloons, and focus management inside the nested form fights the datatable's own focus handling. Inline edit via `draft-values` also breaks because the nested form owns its own save cycle.

**Correct approach:** Keep the custom cell template trivial — one or two SLDS-decorated elements at most. If the feature truly needs a form per row, render a summary in the cell and open a detail sub-LWC (panel, modal, or row-expanded detail) on demand. If the feature needs multiple actions, either use the built-in `type: 'action'` menu or register an `actionRow` custom type with a small button group and keep the state in the host component, not the template.
