# Gotchas — LWC Base Component Recipes

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: lightning-record-form Field Order Is Controlled by Page Layout, Not the fields Attribute

**What happens:** Developers specify a `fields` array in a particular order expecting the form to render fields in that sequence. The form renders correctly in the scratch org or sandbox, but in production (or with different profiles) the field order differs.

**When it occurs:** Whenever `lightning-record-form` uses the `fields` attribute (as opposed to `layout-type="Full"`). The platform resolves the page layout for the running user's profile and record type, then renders fields that exist in the `fields` array in page layout order. Fields not on the page layout may be omitted or moved.

**How to avoid:** Use `lightning-record-edit-form` with `lightning-input-field` children placed in the exact desired order in the HTML template. This is the only way to guarantee rendering order independent of page layout configuration.

---

## Gotcha 2: draftValues Not Reset After Save Leaves Datatable in a Broken State

**What happens:** After a successful inline edit save on `lightning-datatable`, the save/cancel toolbar remains visible and subsequent inline edits append new changes to the stale `draftValues` array. On the next save, the stale entries trigger additional `updateRecord` calls for rows the user did not intend to change, causing unexpected field overwrites.

**When it occurs:** Any time the `onsave` handler calls `updateRecord` but does not reset the component's `draftValues` property back to `[]` after the promises resolve.

**How to avoid:** Always include `this.draftValues = [];` immediately after the `await Promise.all(...)` resolves in the success path. Also add a `finally` block or separate reset in the error path so the toolbar clears even when some saves fail:

```js
async handleSave(event) {
  const updates = event.detail.draftValues;
  try {
    await Promise.all(updates.map(row => updateRecord({ fields: { Id: row.Id, ...row } })));
  } finally {
    this.draftValues = []; // always clear, even on partial failure
  }
}
```

---

## Gotcha 3: Destroying lightning-record-edit-form with if:true Discards Unsaved Input

**What happens:** A common pattern is to wrap `lightning-record-edit-form` in `<template if:true={showForm}>` so it can be conditionally shown. When `showForm` flips to `false` and back to `true`, the DOM element is destroyed and re-created. Any unsaved values the user typed into `lightning-input-field` children are lost, and the form resets to its initial server state.

**When it occurs:** Any component that toggles form visibility with `if:true/if:false` — typically a "Show Form / Hide Form" toggle, a cancel button that hides the form, or a conditional modal that is rendered inside `if:true`.

**How to avoid:** Use a CSS class toggle to show and hide the form without removing it from the DOM:

```html
<!-- use a class to visually hide, not if:true -->
<div class={formContainerClass}>
  <lightning-record-edit-form ...>...</lightning-record-edit-form>
</div>
```

```js
get formContainerClass() {
  return this.showForm ? '' : 'slds-hide';
}
```

This preserves the component instance and all in-progress field values.

---

## Gotcha 4: FLS Silently Omits Fields — No Warning Is Shown

**What happens:** A `lightning-record-form`, `lightning-record-edit-form`, or `lightning-record-view-form` that specifies a field the running user cannot read due to field-level security silently omits that field. No error is thrown and no visual indicator shows the user that a field is missing. Developers who test as System Administrator (who bypasses FLS) never see the issue.

**When it occurs:** Any base form component used in a community, portal, or with a permission set configuration that restricts specific fields. Often discovered when internal users with restricted profiles or Experience Cloud guests report "missing" form fields.

**How to avoid:** Test form components with a user whose profile matches the intended audience, not as System Administrator. Add a manual verification step in the review checklist that confirms expected fields are visible with the minimum-permission profile.

---

## Gotcha 5: lightning-datatable columns Must Be Defined Outside the Template or as a Reactive Property

**What happens:** If the `columns` array is defined inline in the HTML template (e.g., as a hard-coded expression), or if it is reassigned on every render cycle, `lightning-datatable` re-renders all rows on every reactive update, causing scroll position to reset and brief visual flicker.

**When it occurs:** Components where `columns` is computed in a getter with side effects, or where it is rebuilt in `connectedCallback` in a way that creates a new array reference on each reactive property change.

**How to avoid:** Define `columns` as a class field initialized once (not in a getter that runs on every access), or use `@track` carefully to ensure the array reference only changes when the column definitions genuinely change.
