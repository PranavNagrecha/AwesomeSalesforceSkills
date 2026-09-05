# Gotchas — LWC Base Component Recipes

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: lightning-record-form Field Order Is Controlled by Page Layout, Not the fields Attribute

**What happens:** Developers specify a `fields` array in a particular order expecting the form to render fields in that sequence. The form renders correctly in the scratch org or sandbox, but in production (or with different profiles) the field order differs.

**When it occurs:** Whenever `lightning-record-form` uses the `fields` attribute (as opposed to `layout-type="Full"`). The platform resolves the page layout for the running user's profile and record type, then renders fields that exist in the `fields` array in page layout order. Fields not on the page layout may be omitted or moved.

**How to avoid:** Use `lightning-record-edit-form` with `lightning-input-field` children placed in the exact desired order in the HTML template. This is the only way to guarantee rendering order independent of page layout configuration.

**UNVERIFIED (2026-09-05):** the *mechanism* stated above — that the platform resolves the running user's page layout and re-orders the `fields` array against it — is not printed anywhere in the LWC Developer Guide. What the guide does state is that `lightning-record-form` has no "Custom Layout for Fields" capability, that custom field layouts require `lightning-record-view-form` or `lightning-record-edit-form` (`lwc_guide data-get-user-input` L5424–L5426, L5431), and that you should specify `fields` rather than a layout unless you want the administrator, not the component, to control which fields are provisioned (L5430, L5447). The remedy is grounded; the causal explanation is not. Treat the ordering behaviour as observed, not as documented, and verify against the `lightning-record-form` page in the Component Reference.

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

---

## Gotcha 6: lightning-output-field Nested Inside lightning-layout Renders Nothing

**What happens:** A developer builds a two-column read-only summary by wrapping each
`lightning-output-field` in a `lightning-layout-item` for spacing. The markup deploys, the page
loads, and the field area is simply empty — no error in the console, no error in the form.

**When it occurs:** Any time `lightning-output-field` is placed inside another element between
itself and its `lightning-record-view-form` parent. It is a real behavioural difference from Aura:
`lightning:outputField` tolerated the extra nesting, the LWC version does not. The guide states it
directly — *"lightning-output-field must be a child of lightning-record-view-form. Don't nest
lightning-output-field in another element like lightning-layout"*
(`lwc_guide migrate-map-aura-lwc-components` L11727).

**How to avoid:** Invert the nesting. Put the *form* inside the `lightning-layout-item` and keep the
output fields as direct children of the form. For multi-column layouts, use the form's own density
setting (`density="compact"`) or `slds-grid` markup *inside* the form rather than a layout wrapper
around each field. Note the asymmetry: `lightning-input-field` **can** be nested in HTML tags or in
another base component such as `lightning-layout` inside `lightning-record-edit-form` — but never in
a custom component (L11725). The two halves of the record-form family do not follow the same rule.

---

## Gotcha 7: getPicklistValues Returns Translated Labels — Saving the Label Corrupts the Field

**What happens:** A combobox built from `getPicklistValues` works perfectly in an English-only
sandbox. In production, users running Salesforce in another language save a record and the picklist
field ends up holding a value that is not one of the field's API names. Validation rules keyed on the
API name stop matching, reports segment wrongly, and integrations reject the record.

**When it occurs:** Whenever the handler writes `event.detail.label`, or maps the wire result into
options as `{ label: v.label, value: v.label }`, and the org has Translation Workbench enabled with
translations supplied for that picklist. The guide is explicit: *"The label property returns the
picklist label translated into the running user's language … The value property always returns the
untranslated API name. Use value to save the user's selection back to Salesforce, and use label only
for display"* (`lwc_guide reference-wire-adapters-picklist-values` L14963–L14964).

**How to avoid:** Map exactly one way — `{ label: item.label, value: item.value }` — and write only
`value` back through `updateRecord` or a form field. Two related traps sit next to it: both
`recordTypeId` and `fieldApiName` are required parameters and `objectApiName` is *not* accepted on
this adapter (L14955, L14960); and picklist values are scoped to a record type, so a component that
hardcodes the master record type `012000000000000AAA` shows the wrong option set on any object with
multiple record types (L14949, L14958). Feed `recordTypeId` from `getObjectInfo`'s
`defaultRecordTypeId` on a reactive property, and supply `record-type-id` to a record form when the
object has multiple record types and no default (`lwc_guide data-considerations` L6362).

---

## Gotcha 8: lightning-datatable Is Not Supported on Mobile, and Nothing Warns You

**What happens:** A component using `lightning-datatable` is added to a record page whose
`.js-meta.xml` declares `<supportedFormFactor type="Small"/>`. It deploys cleanly, passes review, and
then field users on phones report a blank or broken region.

**When it occurs:** Any bundle containing `lightning-datatable` or `lightning-tree-grid` that is
exposed to the phone form factor. The guide states plainly that *"lightning-datatable and
lightning-tree-grid aren't supported on mobile devices"*
(`lwc_guide data-table-vs-tree-grid` L5600), and separately warns that although base components
implement SLDS styling, not all of them are supported for mobile screens — the Data Table blueprint
is adaptive but the base component is not mobile-ready, and `lightning-tabset` does not implement the
blueprint's stacked mobile behaviour either (`lwc_guide create-components-css-slds-blueprint` L1740–L1741).

**How to avoid:** Treat form factor as a design input, not a deployment detail. Declare
`<supportedFormFactors>` on every `targetConfig` — Salesforce strongly recommends it, and the valid
types are `Large` (desktop) and `Small` (phone)
(`lwc_guide targets-lightning-record-page` L19373–L19376). If the requirement includes mobile, do not
choose datatable at all: compose a card or tile list from `lightning-layout` and
`lightning-formatted-*` components instead. If it is desktop-only, drop `Small` from the manifest so
App Builder does not offer it for a phone layout.

---

## Gotcha 9: Jest Passes Against a Base Component Stub That Does Nothing

**What happens:** A suite queries `element.shadowRoot.querySelector('lightning-combobox')`, asserts
`combobox.getAttribute('options')` or waits for the component's `onchange` handler to fire from a
simulated click, and reports green. The production component is broken; the test could never have
caught it.

**When it occurs:** In every LWC Jest suite, because the base components are replaced by mocks from
the `lightning-stubs` directory of `sfdx-lwc-jest`. Those mocks *"match the API of the actual
components but don't have all the functionality"*, **fire no events at all**, and — critically —
base components have properties that are not reflected as attributes in the DOM: the guide's own
example is `iconPosition` on `lightning-button`, which decides an SLDS class and is never rendered
(`lwc_guide unit-testing-using-jest-patterns` L12622, L12626–L12627).

**How to avoid:** Three rules. Read **properties** off the queried stub (`el.options`, `el.value`,
`el.recordId`), never `getAttribute`. Simulate interaction by calling `dispatchEvent()` against the
stub yourself — the guide confirms *"No events are fired from these mocks but you can call
dispatchEvent() against them"* (L12627). And do not assert on the order in which slots rendered; the
guide recommends tests pass regardless of whether the mock or the real component swaps named-slot
order (L12625). When you need richer behaviour than a stub provides, register a custom mock through
`moduleNameMapper` in `jest.config.js` (L12637).

---

## Gotcha 10: platformShowToastEvent Is Silent on LWR Experience Cloud Sites

**What happens:** A component that shows a success toast after save works in Lightning Experience.
The same component, deployed to an LWR Experience Cloud site, saves the record and shows nothing.
No console error identifies the cause.

**When it occurs:** Whenever `lightning/platformShowToastEvent` is used outside Lightning Experience.
The guide records it twice: in the notification catalogue —
*"lightning/platformShowToastEvent isn't supported in LWR sites"* (`lwc_guide base-components-all`
L4649) — and in the usage patterns page, which explains why: `platformShowToastEvent` uses an
**event-based** mechanism rather than a module method, *"and it's not supported in environments like
LWR sites for Experience Cloud or standalone apps. We recommend that you use lightning/toast
instead"* (`lwc_guide base-components-patterns` L4773).

**How to avoid:** Default to `lightning/toast` (API 59.0) with `lightning/toastContainer` (58.0) to
control position and stacking (L4651–L4652). Reach for `lightning/alert`, `lightning/confirm` or
`lightning/prompt` (54.0) when you need a blocking response — unlike the `window.*()` APIs they do
not halt page execution and each returns a promise, so `await` or `.then()` anything that must run
after the modal closes (L4767–L4769). A second styling trap rides along: the
`--slds-c-toast-*` custom properties are **not** supported on `platformShowToastEvent`, only on
`lightning/toast` and `lightning/toastContainer` (`lwc_guide create-components-css-custom-properties`
L1721).

---

## Gotcha 11: Aura Attribute Names That Look Right and Do Nothing in LWC

**What happens:** Markup migrated from Aura, or generated by a model trained on Aura examples,
deploys without complaint and behaves incorrectly: an accordion section shows no tooltip, a tabset
opens the wrong tab, a card's action buttons never appear, a badge's icon has no hover text.

**When it occurs:** On the base components whose LWC contract diverged from their Aura counterpart.
The Aura-to-LWC mapping table records each one
(`lwc_guide migrate-map-aura-lwc-components` L11660–L11740):

| Component | Aura | LWC | Line |
|---|---|---|---|
| `accordion-section` | `title` gives tooltip text; `actions` attribute takes a `lightning:buttonMenu` | `title` is **reserved for internal use**; actions go in an `actions` **slot** | L11663 |
| `accordion` | `openSections` always returns an array | `openSections` returns a **string** unless `allow-multiple-sections-open` is set | L11662 |
| `card` | `title` / `footer` accept objects, so components can be passed; `actions` is an attribute | `title` / `footer` are **text only**; markup goes in named slots and actions in the action named slot | L11674 |
| `tabset` / `tab` | `selectedTabId`; `id` identifies a tab | `active-tab-value`; `value` identifies a tab | L11732–L11733 |
| `button-menu` | supports `onclick` and `onclose`… | …the Aura component does *not*; check the LWC specification before wiring either | L11672 |
| `button-icon` | supports `iconClass` | `lightning-button-icon` does **not** support `iconClass` | L11670 |
| `formatted-number` | `style` selects the number type | `format-style` | L11692 |
| `pill` | `media` attribute; no `variant` | avatars and icons are **nested components** | L11718 |
| `layout` | expressions and components allowed between `layoutItem`s | only HTML tags and text between `lightning-layout-item`s | L11707 |

**How to avoid:** When migrating or when reviewing generated markup, run the component name through
that table before trusting an attribute. Two general rules cover the rest: an attribute marked
*"Reserved for internal use"* on the Specification tab must not be used because it can change in any
release (`lwc_guide base-components-considerations` L4727); and a global HTML attribute may be
surfaced under a different public name — `title` on `lightning-badge` applies only to the wrapper
element, and `icon-alternative-text` is what reaches the icon
(`lwc_guide base-components-patterns-global` L4794–L4801).
