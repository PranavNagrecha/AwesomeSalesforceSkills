---
name: lwc-base-component-recipes
description: "Use this skill when building record forms or data tables with Salesforce standard base components: lightning-record-form, lightning-record-edit-form, lightning-record-view-form, and lightning-datatable. Covers component selection, attribute configuration, inline editing, row actions, and the decision matrix for choosing between form components. NOT for custom forms backed by Apex wire methods or @wire(getRecord) with fully manual field rendering (use lwc-forms-and-validation). NOT for LWC fundamentals such as data binding, event handling, or the component lifecycle (use lifecycle-hooks or wire-service-patterns)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
triggers:
  - "I need to display and edit a Salesforce record on a Lightning page without writing Apex"
  - "lightning-record-form is not showing all the fields I specified in the fields attribute"
  - "How do I add a custom Save button to lightning-record-edit-form and intercept form submission"
  - "lightning-datatable inline editing is not persisting changes after the user edits a cell"
  - "Should I use lightning-record-form or lightning-record-edit-form for my create/edit page"
  - "lightning-record-view-form vs lightning-record-edit-form — which one do I pick for a read-only detail card"
tags:
  - lwc
  - base-components
  - lightning-record-form
  - lightning-datatable
  - forms
  - data-display
inputs:
  - "Object API name and field API names to display or edit"
  - "Record ID (for edit/view modes)"
  - "Whether the form needs a custom layout, custom buttons, or field-level validation messages"
  - "Whether the table needs inline editing, row actions, or custom cell types"
outputs:
  - "Component markup and JS using the correct base component for the use case"
  - "Decision guidance on which form component to choose"
  - "Inline editing wiring pattern for lightning-datatable with draftValues and save handler"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# LWC Base Component Recipes

This skill activates when a practitioner needs to build record forms or data tables using Salesforce standard base Lightning components. It covers component selection, required attribute configuration, layout control, inline editing, row actions, and the trade-offs between declarative and custom approaches.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the object API name and which field API names (not labels) are needed. Field API names drive both `fields` attributes and `lightning-input-field` / `lightning-output-field` children.
- Determine whether the form needs a fully custom layout (field order, sections, custom buttons, field-level messages) or whether a standard layout is acceptable. This is the primary driver for choosing `lightning-record-form` vs `lightning-record-edit-form`.
- For `lightning-datatable`, establish whether inline editing, row actions, or sorting is required before scaffolding — these each add distinct wiring.
- The most common wrong assumption is that `lightning-record-form` supports arbitrary field ordering. It respects the page layout assigned to the running user's profile, not a developer-specified field list order.
- Platform constraints: `lightning-record-form` and `lightning-record-edit-form` call the UI API under the hood and respect field-level security. Fields the running user cannot see will be silently omitted. `lightning-datatable` supports up to 1000 rows before performance degrades.

---

## Core Concepts

### lightning-record-form: Declarative, Layout-Driven

`lightning-record-form` is the simplest way to render a record in create, edit, or view mode. Set `object-api-name`, `record-id` (omit for create), and `fields` or `layout-type`. The component manages its own submit button, loading state, and error display.

Key limitation: when using the `fields` attribute, the platform renders fields in page layout order for the assigned layout — not necessarily the order specified in `fields`. If precise field ordering or custom sections are required, use `lightning-record-edit-form` instead.

Available modes via the `mode` attribute: `view` (default when record-id present), `edit`, `readonly`. Switching mode dynamically is supported.

### lightning-record-edit-form: Full Layout Control

`lightning-record-edit-form` gives full control over form layout by accepting `lightning-input-field` children placed anywhere in the markup. Custom Save and Cancel buttons are added as standard `lightning-button` components inside the form. The `onsubmit` handler fires before the record is saved and receives the submitted fields; it can be called with `event.preventDefault()` to cancel and perform custom logic. The `onsuccess` handler fires after a successful save and receives the new record data.

Required attributes: `object-api-name` always. `record-id` for edit; omit for create.

`lightning-record-view-form` with `lightning-output-field` children is the read-only counterpart.

### lightning-datatable: Tabular Data with Interaction

`lightning-datatable` renders a data table with configurable columns, sorting, row selection, inline editing, and row actions.

Critical attributes:
- `key-field`: required, must be a unique field in every row object (typically `Id`).
- `columns`: array of column definition objects with at minimum `label`, `fieldName`, and `type`.
- `data`: array of plain JS objects; must be set reactively on the component.
- `draft-values`: array of edited-but-unsaved row objects; bind this to a tracked property and clear it after save.
- `onsave`: fires when the user clicks Save in inline edit mode; the event detail contains `draftValues`.
- `onrowaction`: fires when a row action (defined in a `type: 'action'` column) is selected.

---

## Common Patterns

### Pattern: Custom Save Button with Field-Level Error Display

**When to use:** The form needs a non-standard button placement, a confirmation step before save, or field-level validation messages shown below specific fields.

**How it works:**

```html
<!-- myForm.html -->
<template>
  <lightning-record-edit-form
    record-id={recordId}
    object-api-name="Contact"
    onsubmit={handleSubmit}
    onsuccess={handleSuccess}
    onerror={handleError}
  >
    <lightning-messages></lightning-messages>
    <lightning-input-field field-name="FirstName"></lightning-input-field>
    <lightning-input-field field-name="LastName"></lightning-input-field>
    <lightning-input-field field-name="Email"></lightning-input-field>
    <lightning-button type="submit" label="Save Contact" variant="brand"></lightning-button>
    <lightning-button label="Cancel" onclick={handleCancel}></lightning-button>
  </lightning-record-edit-form>
</template>
```

```js
// myForm.js
import { LightningElement, api } from 'lwc';
export default class MyForm extends LightningElement {
  @api recordId;

  handleSubmit(event) {
    event.preventDefault();
    const fields = event.detail.fields;
    // Custom pre-save logic here, then:
    this.template.querySelector('lightning-record-edit-form').submit(fields);
  }

  handleSuccess(event) {
    const updatedRecord = event.detail.id;
    // fire toast or navigate
  }

  handleCancel() {
    // navigate away or reset
  }
}
```

**Why not lightning-record-form:** `lightning-record-form` renders its own submit button and does not expose `onsubmit` with `event.preventDefault()` semantics for pre-save interception.

### Pattern: lightning-datatable with Inline Editing

**When to use:** A table of records needs in-place cell editing without navigating to a record page.

**How it works:**

```html
<!-- dataTable.html -->
<template>
  <lightning-datatable
    key-field="Id"
    data={tableData}
    columns={columns}
    draft-values={draftValues}
    onsave={handleSave}
  ></lightning-datatable>
</template>
```

```js
// dataTable.js
import { LightningElement, wire } from 'lwc';
import { updateRecord } from 'lightning/uiRecordApi';
import { refreshApex } from '@salesforce/apex';

export default class DataTable extends LightningElement {
  tableData = [];
  draftValues = [];

  columns = [
    { label: 'Name', fieldName: 'Name', type: 'text' },
    { label: 'Phone', fieldName: 'Phone', type: 'phone', editable: true },
  ];

  async handleSave(event) {
    const updates = event.detail.draftValues;
    const updatePromises = updates.map(row =>
      updateRecord({ fields: { Id: row.Id, ...row } })
    );
    try {
      await Promise.all(updatePromises);
      this.draftValues = []; // clear draft values on success
    } catch (e) {
      // surface error via showToast
    }
  }
}
```

**Why not manual table markup:** Building a table with `<template for:each>` and `<input>` elements requires manual dirty-state tracking, keyboard navigation, and accessibility handling that `lightning-datatable` provides out of the box.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple create/edit/view with standard layout | `lightning-record-form` | Least markup; built-in buttons and error display |
| Custom field order or sections | `lightning-record-edit-form` + `lightning-input-field` | Full layout control with standard UI API backend |
| Read-only detail panel | `lightning-record-view-form` + `lightning-output-field` | No edit affordances; respects FLS automatically |
| Read-only with mixed custom and standard fields | `lightning-record-view-form` + `lightning-output-field` for standard fields | Avoids Apex; respects FLS; mix with computed markup |
| Intercept submit for confirmation or custom pre-save logic | `lightning-record-edit-form` with `onsubmit` + `event.preventDefault()` | Only edit-form exposes this hook |
| Tabular record list with inline editing | `lightning-datatable` with `editable: true` columns and `onsave` | Built-in draft management and keyboard navigation |
| Table requires a fully custom cell renderer | `lightning-datatable` with a custom cell type registered via `customTypes` | Spring '24+ feature; avoids rebuilding table chrome |
| Form needs Apex-driven default values or complex cross-field logic | Custom form with `@wire(getRecord)` and manual `updateRecord` calls | Base components delegate field logic to UI API only |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `object-api-name` uses the API name, not the label (e.g., `Account` not `Accounts`, `Custom_Object__c` not `Custom Object`)
- [ ] `record-id` is bound via `@api recordId` and passed in from the parent or page; not hardcoded
- [ ] `key-field` on `lightning-datatable` is set to a field that is unique across all rows (almost always `Id`)
- [ ] `draft-values` is reset to `[]` after a successful inline edit save to dismiss the save/cancel bar
- [ ] Field-level security: tested with a user who lacks access to one of the listed fields to confirm graceful omission
- [ ] `onsuccess` handler fires a toast or navigates; form is not left in a stale submitted state
- [ ] `lightning-messages` is present inside `lightning-record-edit-form` when using a custom submit button, so server errors surface

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **lightning-record-form ignores fields attribute ordering** — The `fields` attribute controls which fields appear, but rendering order is governed by the page layout assigned to the user's profile and record type. Developers who expect array order to match display order are surprised when fields reorder in production with a different profile. Fix: use `lightning-record-edit-form` with explicit `lightning-input-field` placement when order matters.

2. **draft-values accumulation on datatable** — If `draft-values` is not reset to `[]` after a successful save, the save/cancel toolbar remains visible and the next inline edit appends to the stale array instead of starting fresh. This causes duplicate update calls on the next save. Fix: always set `this.draftValues = []` in the `onsave` success path.

3. **lightning-record-edit-form loses field values on re-render** — If a parent component re-renders and replaces the `lightning-record-edit-form` in the DOM (e.g., due to conditional `if:true` toggling), unsaved field values are discarded. Fix: use CSS `display: none / block` via a class toggle rather than `if:true/if:false` to hide/show the form without destroying it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component markup (HTML) | `lightning-record-form`, `lightning-record-edit-form`, or `lightning-datatable` markup with correct attributes |
| Component controller (JS) | Event handlers for `onsubmit`, `onsuccess`, `onsave`, and `onrowaction` |
| Decision recommendation | Which base component to use and why, given the stated requirements |

---

## Related Skills

- lwc-forms-and-validation — Use when the form requires Apex-backed field logic, cross-field validation, or fully custom field rendering beyond what `lightning-input-field` supports
- wire-service-patterns — Use when the component needs to read record data via `@wire(getRecord)` alongside base components
- lwc-data-table — Extends datatable coverage with advanced features: custom cell types, infinite scrolling, and row-level permissions
- lwc-toast-and-notifications — Use alongside form `onsuccess`/`onerror` handlers to surface save results to the user
