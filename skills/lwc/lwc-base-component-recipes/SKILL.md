---
name: lwc-base-component-recipes
description: "Use this skill when building record forms or data tables with Salesforce standard base components: lightning-record-form, lightning-record-edit-form, lightning-record-view-form, and lightning-datatable. Covers component selection. NOT for custom forms backed by Apex wire methods or @wire(getRecord) with fully manual f — use lwc/lwc-data-table. Also the base-component-first decision (base component vs raw SLDS blueprint markup vs custom component vs third-party web component) and the everyday composites: lightning-card, lightning-layout / lightning-layout-item, lightning-combobox fed by getPicklistValues, lightning-button-menu, lightning-spinner, lightning-accordion, lightning-tabset, lightning-badge, lightning-button-group."
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
  - "Build a lightning-card with a picklist combobox and a read-only summary panel"
  - "Populate lightning-combobox options from getPicklistValues instead of hardcoding them"
  - "Decide between a lightning base component, raw SLDS blueprint markup, and a custom component"
  - "Lay out a component with lightning-layout and lightning-layout-item instead of slds-grid divs"
  - "Show a lightning-spinner while a wire adapter is still loading"
  - "Jest test asserts on a lightning-combobox but the stub renders no attributes"
  - "lightning-output-field renders nothing when I nest it inside lightning-layout"
  - "Which base components exist for menus, cards, badges, accordions, and tabs"
tags:
  - lwc
  - base-components
  - lightning-record-form
  - lightning-datatable
  - forms
  - data-display
  - lightning-card
  - lightning-combobox
  - lightning-layout
inputs:
  - "Object API name and field API names to display or edit"
  - "Record ID (for edit/view modes)"
  - "Whether the form needs a custom layout, custom buttons, or field-level validation messages"
  - "Whether the table needs inline editing, row actions, or custom cell types"
  - "Which app containers the component must run in (Lightning Experience, LWR site, Salesforce mobile app)"
  - "Which picklist fields the UI must render, and whether the object has multiple record types"
outputs:
  - "Component markup and JS using the correct base component for the use case"
  - "Decision guidance on which form component to choose"
  - "Inline editing wiring pattern for lightning-datatable with draftValues and save handler"
  - "A composite bundle (html / js / js-meta.xml) plus a Jest suite that works with the lightning-stubs"
  - "A base-vs-SLDS-vs-custom-vs-third-party recommendation with the composition or flat-structure pattern named"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# LWC Base Component Recipes

This skill activates when a practitioner needs to build record forms or data tables using Salesforce standard base Lightning components. It covers component selection, required attribute configuration, layout control, inline editing, row actions, and the trade-offs between declarative and custom approaches.

> **Attribute contracts live in the Component Library, not here and not in the LWC Developer Guide.**
> The Lightning Web Components Developer Guide documents *which* base components exist, how they
> compose, how they are styled, and how they behave in containers. It does not publish the
> per-component attribute, event, and method tables — those are on the Specification and
> Documentation tabs of each component in the
> [Component Reference](https://developer.salesforce.com/docs/platform/lightning-component-reference/overview/components)
> ([`lwc_guide base-components-considerations` L4727](https://developer.salesforce.com/docs/platform/lwc/guide/base-components-considerations.html);
> [`base-components-patterns-global` L4804, L4812](https://developer.salesforce.com/docs/platform/lwc/guide/base-components-patterns-global.html)).
> Every attribute named in this package that the guide itself does not print carries an
> `UNVERIFIED (2026-09-05)` marker beside it. Confirm those against the Component Library before
> shipping, and never copy an attribute name out of a generated snippet without checking it.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the object API name and which field API names (not labels) are needed. Field API names drive both `fields` attributes and `lightning-input-field` / `lightning-output-field` children.
- Determine whether the form needs a fully custom layout (field order, sections, custom buttons, field-level messages) or whether a standard layout is acceptable. This is the primary driver for choosing `lightning-record-form` vs `lightning-record-edit-form`.
- For `lightning-datatable`, establish whether inline editing, row actions, or sorting is required before scaffolding — these each add distinct wiring.
- The most common wrong assumption is that `lightning-record-form` supports arbitrary field ordering. `lightning-record-form` has no "Custom Layout for Fields" capability at all — that column belongs to `lightning-record-view-form` and `lightning-record-edit-form` (`lwc_guide data-get-user-input` L5426, L5431).
- Platform constraints: `lightning-record-form`, `lightning-record-edit-form`, and `lightning-record-view-form` work with Salesforce record data only, are limited to the objects User Interface API supports, and go through Lightning Data Service (`lwc_guide base-components-containers` L4710; `data-get-user-input` L5414, L5418). `lightning-datatable` and `lightning-tree-grid` are **not supported on mobile devices** (`lwc_guide data-table-vs-tree-grid` L5600), and datatable performance is best at a maximum of 1,000 rows and 5 columns (`lwc_guide data-table-performance` L6311).
- Establish which containers the component must run in. Base components run in Lightning Experience, Experience Builder sites, and the Salesforce mobile app, but only a subset support server-side rendering on LWR sites, and `lightning/platformShowToastEvent` is not supported in LWR sites at all — use `lightning/toast` (`lwc_guide base-components-containers` L4714; `base-components-all` L4649, L4651; `base-components-patterns` L4773).

---

## Questions to Ask Before Configuring

Ask these before the first `<lightning-*>` tag is typed. Each one traces to a failure documented in `references/gotchas.md` that the component will not raise at compile time.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Name every container this must run in — Lightning Experience, an LWR Experience Cloud site, the mobile app, or a quick action." | Container decides half the component list: `lightning-datatable` and `lightning-tree-grid` are unsupported on mobile (L5600), only a subset of base components server-side render on LWR (L4714), and `lightning/platformShowToastEvent` does not work on LWR (L4773) | The `<supportedFormFactors>` block for the `.js-meta.xml`, and whether the toast import is `lightning/toast` or `lightning/platformShowToastEvent` |
| "Which of these values comes from a picklist, and does the object have more than one record type?" | `getPicklistValues` requires **both** a `recordTypeId` and a `fieldApiName`; picklist values are scoped to record type, and a form must be given `record-type-id` when the object has multiple record types and no default (L14949, L14960, L6362) | Whether the component needs the `getObjectInfo` → `defaultRecordTypeId` → `getPicklistValues` chain, or can pass the master record type `012000000000000AAA` |
| "Is the picklist value being displayed, or saved?" | `label` is translated into the running user's language via Translation Workbench; `value` always returns the untranslated API name (L14963–14964) | An explicit rule that `value` goes to the record and `label` goes on screen — which stops a component that silently writes translated strings into a picklist field |
| "For each thing on this screen, is there a base component, an SLDS blueprint, or neither?" | Salesforce updates base components automatically when SLDS changes a blueprint; a component you built from blueprint markup is yours to maintain forever (L1737) | A per-element verdict — base component, blueprint-derived custom component, or third-party — rather than a page of hand-rolled `slds-*` markup that ages out |
| "Does this composite need slots or an options array?" | Base components use two shapes: composition via slots (`lightning-button-menu` + `lightning-menu-item`) and a flat structure via a configuration attribute (`lightning-combobox` `options`, `lightning-datatable` `columns`) — mixing them up produces markup that renders nothing (L4855–4883) | Which pattern each part of the composite uses, and therefore what the JS has to build versus what the template declares |
| "Which fields are read-only for this audience, and will the labels be visible?" | `lightning-output-field` must be a direct child of `lightning-record-view-form` and must not be nested in `lightning-layout` (L11727); it supports only `standard` and `label-hidden` variants, and hidden labels remain available to assistive technology (L6346–6347) | The exact nesting of the read-only summary, and whether `variant="label-hidden"` is acceptable for the audience |
| "How will this be tested — and what will the Jest stubs actually give the test?" | The `sfdx-lwc-jest` `lightning-stubs` match the API of the real components but fire no events, and base-component properties are not all reflected as DOM attributes (L12622, L12626–12627) | A test plan that sets and reads *properties* on the stub and calls `dispatchEvent()` against it, instead of a suite that asserts `getAttribute()` and passes for the wrong reason |

What a proper base-component composition adds over just doing it: the UI inherits SLDS updates, keyboard behaviour, ARIA state management and WCAG 2.1 AA contrast from Salesforce rather than from your own markup (`lwc_guide base-components-accessibility` L4953–4957), the form path enforces CRUD and FLS through Lightning Data Service instead of a bespoke Apex surface, and every attribute you did use is one the Component Library will keep supporting.

---

## Core Concepts

### The base-component-first decision

Four options, in the order you should try them (`lwc_guide create-components-css-slds-blueprint` L1733–1737, `create-components-accessibility` L3977, `create-use-third-party-components` L4188):

| Option | Choose when | What you inherit | What you own forever |
|---|---|---|---|
| Base component (`lightning-*`) | A component in the catalogue does the job, possibly with a `variant` or an SLDS utility class | SLDS updates, ARIA/keyboard behaviour, contrast, container support | Nothing but your attribute values |
| Base component + styling hooks | Design variations and utility classes are not enough | Same as above | The hook values, and the SLDS 1 fallback |
| Custom component from an SLDS blueprint | No base component exists for the pattern | Nothing automatic — blueprint markup is copied into your bundle | The markup, the a11y behaviour, and every future SLDS change |
| Third-party web component via `lwc:external` | Neither a base component nor an AppExchange package covers it | Nothing; Salesforce does not support third-party web components | Everything, plus the LWS and shadow-DOM caveats |

The load-bearing sentence is `lwc_guide` L1737: *"If SLDS updates the related blueprint, your component code isn't updated automatically … Salesforce automatically updates the base components when SLDS updates the associated blueprint."* That is the whole argument for base-first, and it is also the argument against replacing an SLDS class with your own (L1894–1895) or styling from rendered output (L1890–1891).

### The catalogue, by family

Base components live in the `lightning` namespace, use the `lightning-component-name` form in markup and the `lightning/moduleName` form for JavaScript imports, and are grouped into these categories (`lwc_guide base-components-all` L4546–4690, `base-components-considerations` L4724–4725):

| Family | Members this skill uses most | Guide line |
|---|---|---|
| Actions and menus | `button`, `button-group`, `button-icon`, `button-menu`, `menu-item`, `menu-divider`, `menu-subheader`, `button-stateful` | L4560–4568 |
| Containers | `card`, `accordion` + `accordion-section`, `tabset` + `tab`, `layout` + `layout-item`, `tile`, `carousel`, `modal` (55.0) | L4573–4587 |
| Visuals | `avatar`, `badge`, `icon`, `helptext`, `pill` | L4590–4597 |
| Input | `combobox`, `input` (+ its `type` variants), `checkbox-group`, `radio-group`, `select` (59.0), `dual-listbox`, `record-picker` (59.0), `textarea` | L4600–4629 |
| Forms | `record-form`, `record-edit-form`, `record-view-form`, `input-field`, `output-field` | L4632–4636 |
| Notifications | `lightning/toast` (59.0), `lightning/toastContainer` (58.0), `lightning/platformShowToastEvent`, `lightning/alert`, `lightning/confirm`, `lightning/prompt` (54.0) | L4647–4652 |
| Output | `formatted-text`, `formatted-date-time`, `formatted-number`, `formatted-phone`, `formatted-email`, `formatted-url`, `relative-date-time` | L4655–4666 |
| Progress | `spinner`, `progress-bar`, `progress-indicator` + `progress-step`, `progress-ring` (48.0) | L4669–4673 |
| Tables and trees | `datatable`, `tree`, `tree-grid` | L4676–4678 |

Most base components were first available in Spring '19 (API 45.0), and base components are **not versioned** — lowering your bundle's `apiVersion` does not roll a base component back to older behaviour, and anything below 58.0 is treated as 58.0 (`lwc_guide base-components-all` L4545, `base-components-min-version` L4697, L4701).

### Composition versus flat structure

Two shapes, and picking the wrong one is the single most common markup failure in this domain (`lwc_guide base-components-compose` L4850–4887):

- **Composition (slots).** The parent exposes slots and you nest children: `lightning-accordion` / `-section`, `lightning-button-group` / `lightning-button`, `lightning-button-menu` / `lightning-menu-item`, `lightning-layout` / `-item`, `lightning-tabset` / `lightning-tab`, `lightning-record-edit-form` / `lightning-input-field`, `lightning-record-view-form` / `lightning-output-field`, `lightning-progress-indicator` / `lightning-progress-step` (L4857–4866). Slots are the recommended default (L4914, L4925).
- **Flat structure (a configuration attribute).** The parent renders children internally from an array you pass: `lightning-combobox`, `lightning-select`, `lightning-checkbox-group`, `lightning-radio-group`, `lightning-dual-listbox` (`options`), `lightning-datatable` (`columns` + `data`), `lightning-tree` (`items`), `lightning-pill-container` (`items`), `lightning-map` (`map-markers`) (L4873–4882). Use it when you would otherwise render large numbers of composed elements (L4886).

`lightning-card` is the one you will use most: it has a default slot **and three named slots** (L4909). In LWC — unlike Aura — `title` and `footer` are text-only attributes, and card actions go in a named actions slot rather than an `actions` attribute (L11674).

### Feeding a combobox from picklist metadata

`lightning-combobox` "displays a dropdown list (picklist) of selectable options" and takes `label` / `value` pairs on its `options` attribute (`lwc_guide data-wire-base-components` L6588–6589, `base-components-compose` L4875). The metadata chain is fixed (`lwc_guide reference-wire-adapters-picklist-values` L14949, L14958–14964):

1. `@wire(getObjectInfo, { objectApiName: ACCOUNT_OBJECT })` → read `data.defaultRecordTypeId`.
2. Hold that in a reactive property and pass it to `@wire(getPicklistValues, { recordTypeId: '$recordTypeId', fieldApiName: RATING_FIELD })`. Both parameters are required; `objectApiName` is *not* accepted on this adapter.
3. Map `data.values` to `{ label, value }`. Use `value` for anything written back to Salesforce — `label` is translated into the running user's language through Translation Workbench, `value` is always the untranslated API name.
4. If there is no default record type, the master record type is `012000000000000AAA` (L14949).

For all picklists of a record type at once, use `getPicklistValuesByRecordType` instead (L14959).

### Read-only summaries with `lightning-record-view-form`

`lightning-output-field` **must be a direct child of `lightning-record-view-form`; it must not be nested in another element such as `lightning-layout`** (`lwc_guide migrate-map-aura-lwc-components` L11727). Put the *form* inside a `lightning-layout-item` and keep the output fields directly under the form. The form family adapts to the org's display density by default or with `density="auto"`, and can be overridden with `density="compact"` or `density="comfy"` — `cozy` is not a supported value (L6329–6331). `lightning-output-field` supports two variants, `standard` (default) and `label-hidden`, and a hidden label is still available to assistive technology (L6346–6347).

### Testing base-component composites

The `sfdx-lwc-jest` `lightning-stubs` match the real components' API but implement none of the behaviour. Three consequences drive every test in `references/code-examples.md` (`lwc_guide unit-testing-using-jest-patterns` L12622, L12625–12627):

- **No events fire from a stub — but you can call `dispatchEvent()` against one.** That is how you simulate a combobox change or a menu select.
- **Not every property is reflected as a DOM attribute.** Read the *property* off the queried stub (`el.options`, `el.value`), never `el.getAttribute('options')`.
- **Do not depend on slot render order.** If the expected content is present, the test should pass regardless of which named slot rendered first.

---

## Common Patterns

### Pattern: the everyday composite — card + layout + combobox + menu + spinner + read-only summary

**When to use:** Almost every "panel on a record page" request. It is one card, one responsive grid, one metadata-driven picklist, one action menu, one loading state, and one read-only field summary.

The complete bundle — `.html`, `.js`, `.js-meta.xml`, `package.xml`, the Jest suite, the deploy order and the verification steps — is in **`references/code-examples.md`**. The structural rules it encodes:

```html
<!-- shape only; the full bundle is in references/code-examples.md -->
<lightning-card title="Account Summary" icon-name="standard:account">
  <lightning-button-menu slot="actions" alternative-text="Panel actions" onselect={handleMenuSelect}>
    <lightning-menu-item value="refresh" label="Refresh"></lightning-menu-item>
  </lightning-button-menu>

  <div class="slds-var-p-horizontal_medium">
    <template lwc:if={isLoading}>
      <lightning-spinner alternative-text="Loading" size="small"></lightning-spinner>
    </template>

    <lightning-layout multiple-rows="true">
      <lightning-layout-item size="12" small-device-size="6" padding="around-small">
        <lightning-combobox label="Rating" value={rating} options={ratingOptions}
                            onchange={handleRatingChange}></lightning-combobox>
      </lightning-layout-item>
      <lightning-layout-item size="12" small-device-size="6" padding="around-small">
        <!-- the FORM goes in the layout item; the OUTPUT FIELDS stay directly under the form -->
        <lightning-record-view-form record-id={recordId} object-api-name="Account">
          <lightning-output-field field-name="Industry"></lightning-output-field>
          <lightning-output-field field-name="AnnualRevenue"></lightning-output-field>
        </lightning-record-view-form>
      </lightning-layout-item>
    </lightning-layout>
  </div>
</lightning-card>
```

`size` and `small-device-size` on `lightning-layout-item` are printed by the guide: `small-device-size="9"` gives 75% width at the 480px-and-above breakpoint while `size="12"` takes the full width on mobile (`lwc_guide create-components-css-slds-blueprint` L1768). `slot="actions"` on the menu follows L11674. `multiple-rows`, `padding`, `alternative-text` and `size` on `lightning-spinner`, `icon-name` on `lightning-card`, and `onselect` on `lightning-button-menu` are **UNVERIFIED (2026-09-05): the LWC Developer Guide never prints these attribute names; the guide only records that `lightning-button-menu` does not support `onclick` or `onclose` (L11672) and that `lightning-icon`/`lightning-avatar` expose `alternative-text` (L4964). Confirm each on the Component Library Specification tab.**

### Pattern: Custom Save Button with Field-Level Error Display

**When to use:** The form needs a non-standard button placement, a confirmation step before save, or field-level validation messages shown below specific fields.

> Depth on `lightning-record-edit-form` validation, `reportValidity()`, and file upload lives in **`lwc/lwc-forms-and-validation`**; the create/edit/view selection matrix lives in **`lwc/lwc-lightning-record-forms`**. Use the pattern below only for the composition question — where the buttons and messages go inside the form.

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

`lightning-record-edit-form` fires four custom events — `error`, `load`, `submit`, `success` — and does not provide its own Save and Cancel buttons the way `lightning-record-form` does, so you add `lightning-button` children and include `lightning-messages` for automatic error display (`lwc_guide data-edit-record` L5489–5490, L5500–5504). The record Id is not available on the `submit` event; read it from `success` (`lwc_guide data-considerations` L6376). `event.preventDefault()` on `onsubmit` followed by a manual `submit(fields)` call is **UNVERIFIED (2026-09-05): the guide names the `submit` event but never documents the `submit(fields)` method or the preventDefault-then-resubmit sequence — that contract is in the Component Library.**

**Why not lightning-record-form:** `lightning-record-form` combines the view and edit forms and manages its own buttons; the "Custom Layout for Fields" and "Custom Rendering of Record Data" capabilities belong to `lightning-record-view-form` and `lightning-record-edit-form` (L5424–5431).

### Pattern: lightning-datatable with Inline Editing

**When to use:** A table of records needs in-place cell editing without navigating to a record page.

> **`lwc/lwc-data-table` owns first-time datatable setup and `lwc/lwc-datatable-advanced` owns inline edit, custom cell types and infinite scroll.** Kept here only as the contract summary, because choosing datatable *at all* is a base-component decision — and one with a hard container constraint.

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

The contract facts, all printed by the guide: `key-field` is required and associates each row with a record; `columns` takes `label`, `fieldName` and `type`, and `data` takes the rows; `editable: true` on a column enables inline edit; edits land in `draft-values`; `event.detail.draftValues` carries the edited values and the record Id; and clearing `draftValues` is what hides the Save/Cancel footer (`lwc_guide data-table-inline-edit` L5675, L5678, L5711–5712; `base-components-compose` L4877). Neither datatable nor tree-grid is supported on mobile devices (L5600).

**Why not manual table markup:** rebuilding the table means rebuilding the two-mode keyboard model — navigation mode with `tabindex="-1"` on actionable elements, action mode with `tabindex="0"`, and arrow-key movement between cells — that datatable implements for you (`lwc_guide data-table-a11y` L6215–6233).

---

## Contract Mistakes That Compile Fine

These produce a component that renders, deploys, and silently does the wrong thing.

| Mistake | What actually happens | The rule |
|---|---|---|
| Handling `oninput` on a base input component | Base components document `onchange`; the guide's own example binds `value` on the `change` event, and undocumented global events "may have no effect … or result in events not firing if the components' internals change" (L4822–4824, L5095, L926) | Use `onchange` on `lightning-*` inputs; `oninput` is for the raw `<input>` element (L1184) |
| Passing `checked` where the component wants `value` (or the reverse) | Nothing throws; the control renders in its default state | Look up the property on the Specification tab. `lightning-input type="checkbox"` and `type="toggle"` are checkbox-shaped; `lightning-combobox` is `value`-shaped (L4605, L4618, L4601). **UNVERIFIED (2026-09-05): the guide never prints `checked` or `value` as attribute names on these components.** |
| Inventing a `variant` string | An unsupported `variant` value silently falls back to the default (L1683) | `lightning-button` supports exactly `base`, `neutral`, `brand`, `brand-outline`, `destructive`, `destructive-text`, `inverse`, `success`, defaulting to `neutral` (L1620, L1683). Other components' variant lists are per-component — check before typing one |
| Omitting `label` on an input component | The control ships with no programmatic label, breaking WCAG label techniques; base components associate the `label` you provide with the input automatically (L3987–3988, L3999) | Every `lightning-input`, `lightning-combobox` and friend gets a `label`. Use `aria-label` only where no label is visually present (L3993–3999) |
| Using `title` on `lightning-badge` for icon hover text | `title` applies to the badge wrapper element only, not the icon | Use `icon-alternative-text`, which the component passes down to the icon's `title` (L4794–4801) |
| Using `title` on `lightning-accordion-section` | In LWC that attribute is *reserved for internal use* — the Aura tooltip behaviour did not carry over | Put actions in the section's `actions` slot instead (L11663) |
| Putting other components between `lightning-layout-item` elements | `lightning-layout` does not allow expressions or other components between its items — only HTML tags and text | Everything goes inside a `lightning-layout-item` (L11707) |
| Nesting `lightning-output-field` inside `lightning-layout` | The field is no longer a child of the form and does not render | Nest the *form* in the layout item; keep output fields directly under `lightning-record-view-form` (L11727) |
| Assuming `openSections` on `lightning-accordion` is an array | It returns a **string** unless `allow-multiple-sections-open` is present | Read the type before writing the handler (L11662) |
| Carrying `selectedTabId` or `id` over from Aura | LWC uses `active-tab-value` on `lightning-tabset` and `value` on `lightning-tab` | Translate both when migrating (L11732–11733) |
| Querying a base component by `id` | Rendered `id` values are transformed into globally unique values, and CSS scope tokens are obfuscated from API 59.0 | Use `lwc:ref="uniqueId"` with `this.refs`, or a `data-*` attribute (L4729, L4010, L1917–1920) |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| A UI element exists as a base component | The base component | Salesforce updates it when SLDS changes the blueprint; blueprint-derived markup you own does not update (L1737) |
| No base component; an SLDS blueprint exists | Custom component built from the blueprint, replacing standard HTML with base components wherever possible | The blueprint gives accessible structure; base components inside it keep updating (L1747–1748) |
| Neither exists | Check AppExchange first, then a third-party web component via `lwc:external` | Salesforce does not support third-party web components; LWS, npm, `document.getElementById` and Experience Builder caveats all apply (L4185, L4188, L4208–4211) |
| Simple create/edit/view with standard layout | `lightning-record-form` | Combines and simplifies view and edit forms; handles layout, validation, CRUD changes and error handling (L5428–5429) |
| Custom field order or sections | `lightning-record-edit-form` + `lightning-input-field` | "Custom Layout for Fields" is an edit-form/view-form capability (L5426, L5431) |
| Read-only detail panel | `lightning-record-view-form` + `lightning-output-field` | Read-only rendering with custom layout; output fields must stay direct children (L5450, L11727) |
| Read-only with mixed custom and standard fields | `lightning-record-view-form` + `getRecord` and a `lightning-formatted-*` component for the custom rendering | The guide's own pattern for rendering record data outside an output field (L5454–5459) |
| Intercept submit for confirmation or custom pre-save logic | `lightning-record-edit-form` with `onsubmit` | Only the edit form exposes the submit/success/error/load event set on a custom-layout form (L5500–5504) |
| Tabular record list with inline editing, desktop only | `lightning-datatable` with `editable: true` columns and `onsave` | Built-in draft management and the two-mode keyboard model (L5678, L6215) |
| Tabular data that must work on the mobile app | Not datatable — compose `lightning-layout` / `lightning-tile` / `lightning-card` per row | Datatable and tree-grid are not supported on mobile devices (L5600) |
| Hierarchical rows with expand/collapse | `lightning-tree-grid` | Built on datatable; supports a subset of features and no inline edit, sorting or infinite scroll (L5586–5599) |
| Table requires a fully custom cell renderer | Extend `lightning/datatable` to register a custom type | Class extension is supported for exactly two base components: `lightning/modal` and `lightning/datatable` (L4774–4781) |
| Single-select dropdown of picklist values | `lightning-combobox` fed by `getPicklistValues` | Combobox is the single-selection selector; `lightning-record-picker` is for record lookup, `lightning-dual-listbox` for multi-select (L4601, L4602) |
| A group of related buttons | `lightning-button-group` composing `lightning-button` | Composition, not an options array — the flat shape would need per-button-type metadata (L4928–4929) |
| Toast on an LWR Experience Cloud site | `lightning/toast` | `lightning/platformShowToastEvent` is not supported in LWR sites (L4649, L4773) |
| Form needs Apex-driven default values or cross-field logic | Imperative `lightning/uiRecordApi` functions, or Apex | The guide's escalation path when the record\*form components are not flexible enough (L5550–5551) |

---

## Recommended Workflow

1. **Inventory the screen against the catalogue.** Write down every visual element the request implies, then map each to a family in the catalogue table above. Anything you cannot map is a blueprint or third-party decision — resolve it with the Decision Guidance table before writing markup.
2. **Answer the Questions table.** The container question sets `<supportedFormFactors>` and the toast module; the picklist and record-type questions decide whether you need the `getObjectInfo` → `getPicklistValues` chain.
3. **Pick composition or flat structure per component.** Slots for `card`, `layout`, `button-group`, `button-menu`, `accordion`, `tabset` and the record forms; an `options` / `columns` / `items` array for `combobox`, `select`, `checkbox-group`, `radio-group`, `datatable`, `tree`.
4. **Build from `references/code-examples.md`.** Copy the `accountSummaryPanel` bundle — it already encodes the layout-item nesting, the output-field-must-be-a-direct-child rule, the wire chain, the spinner state and the `.js-meta.xml`. Use `templates/lwc/component-skeleton/` for a component this recipe does not cover, and `templates/lwc/jest.config.js` for the harness.
5. **Verify every attribute you typed against the Component Library.** The guide does not publish attribute tables. Anything not printed in this package with a line cite is an assumption — mark it or check it. `lwc:ref` instead of `id`; `onchange` not `oninput`; a `label` on every input.
6. **Write the Jest suite against the stubs, not against the DOM.** Query the `lightning-*` stub, read properties off it, and `dispatchEvent()` at it. Assertions on `getAttribute()` of a stub pass or fail for reasons unrelated to your component — see `references/gotchas.md`.
7. **Run the checker, then deploy.** `python3 skills/lwc/lwc-base-component-recipes/scripts/check_lwc_base_component_recipes.py --manifest-dir force-app/main/default/lwc` — zero ERRORs before review, `--strict` in CI so the WARNs (raw SLDS button markup, datatable on a mobile form factor, `getAttribute` on a stub, `platformShowToastEvent` in an LWR bundle) also block. Deploy order and the Setup verification steps are at the end of `references/code-examples.md`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every `lightning-*` attribute used was confirmed on the Component Library Specification tab, not inferred from a snippet
- [ ] `object-api-name` uses the API name, not the label (e.g., `Account` not `Accounts`, `Custom_Object__c` not `Custom Object`)
- [ ] `record-id` is bound via `@api recordId` and passed in from the parent or page; not hardcoded
- [ ] `key-field` on `lightning-datatable` is set to a field that is unique across all rows (almost always `Id`)
- [ ] `draft-values` is reset to `[]` after a successful inline edit save to dismiss the save/cancel bar
- [ ] Field-level security: tested with a user who lacks access to one of the listed fields to confirm graceful omission
- [ ] `onsuccess` handler fires a toast or navigates; form is not left in a stale submitted state
- [ ] `lightning-messages` is present inside `lightning-record-edit-form` when using a custom submit button, so server errors surface
- [ ] Every `lightning-input`, `lightning-combobox`, `lightning-select`, `lightning-radio-group` and `lightning-checkbox-group` has a `label`
- [ ] Every `lightning-output-field` is a direct child of its `lightning-record-view-form`, not nested in `lightning-layout`
- [ ] Nothing but `lightning-layout-item` (plus plain HTML and text) sits directly inside `lightning-layout`
- [ ] No `.slds-*` selector is overridden and no CSS targets a base component's rendered internals
- [ ] `.js-meta.xml` declares `<supportedFormFactors>`, and `Small` is absent from any bundle containing `lightning-datatable` or `lightning-tree-grid`
- [ ] Elements are located with `lwc:ref` / `data-*`, never a rendered `id`
- [ ] Jest assertions read properties off the base-component stub and dispatch events at it; no `getAttribute` on a `lightning-*` element

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full write-ups, each with **What happens / When it occurs / How to avoid**, are in `references/gotchas.md`:

1. `lightning-record-form` has no custom-field-layout capability at all — the fix is the edit or view form, not a different `fields` array.
2. Stale `draft-values` on a datatable leave the save bar up and replay edits on the next save.
3. Toggling `lwc:if` around a record-edit form destroys unsaved input.
4. FLS omits fields silently, and an admin never sees it.
5. Rebuilding `columns` on every render resets scroll position.
6. `lightning-output-field` nested in `lightning-layout` renders nothing.
7. `getPicklistValues` returns translated `label`s — saving the label writes the wrong string.
8. `lightning-datatable` and `lightning-tree-grid` do not work on mobile, and nothing warns you at deploy time.
9. Jest stubs fire no events and do not reflect every property as an attribute.
10. `lightning/platformShowToastEvent` is silent on LWR sites.
11. `lightning-accordion-section`'s `title` attribute is reserved for internal use in LWC.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component bundle (HTML / JS / `.js-meta.xml`) | The composite: card, layout, combobox, button-menu, spinner, record-view-form — see `references/code-examples.md` |
| Component controller (JS) | Wire chain (`getObjectInfo` → `getPicklistValues`), event handlers for `onchange`, `onselect`, `onsubmit`, `onsuccess`, `onsave`, `onrowaction` |
| Jest suite | Tests that set properties on the `lightning-stubs` and dispatch events at them |
| Decision recommendation | Base component vs SLDS blueprint vs custom vs third-party, with the composition or flat-structure pattern named |
| Checker report | `check_lwc_base_component_recipes.py --manifest-dir <dir>` output, zero ERRORs |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building: the full `accountSummaryPanel` bundle, `.js-meta.xml`, `package.xml`, the Jest suite that works with the stubs, deploy order, and verification steps |
| `references/gotchas.md` | A composite renders empty, a picklist saves the wrong value, or a test is green for the wrong reason |
| `references/llm-anti-patterns.md` | Reviewing generated LWC markup, or self-checking your own before it ships |
| `references/examples.md` | You want a single scenario — quick create modal, pre-save validation, row actions, a badge-and-button-group card header |
| `references/well-architected.md` | Mapping the choice to pillars, or checking which official source backs a claim |
| `templates/lwc-base-component-recipes-template.md` | Filling in the context-gathering and component-selection worksheet before you write markup |
| `scripts/check_lwc_base_component_recipes.py` | Auditing an existing `lwc/` tree: `--manifest-dir <dir>`, add `--strict` in CI |

## Related Skills

- **lwc/lwc-lightning-record-forms** — owns the record-form vs record-edit-form vs `uiRecordApi` selection matrix in depth.
- **lwc/lwc-forms-and-validation** — owns `reportValidity()`, client-side validation, and file upload flows.
- **lwc/lwc-data-table** — owns first-time datatable setup: columns, `key-field`, sorting, row actions.
- **lwc/lwc-datatable-advanced** — owns inline edit, custom cell types, infinite scroll, row errors.
- **lwc/lwc-modal-and-overlay** — owns `LightningModal`, the one other base component you may extend.
- **lwc/lwc-toast-and-notifications** — owns `ShowToastEvent`, `lightning/toast`, and notification types.
- **lwc/lwc-navigation-mixin** — owns `NavigationMixin` for row actions and menu items that navigate.
- **lwc/lwc-testing** — owns the Jest harness; this skill only adds what the base-component stubs change.
- **lwc/lwc-css-and-styling** — owns scoped CSS and the shadow boundary; read it before styling a base component.
- **lwc/lwc-styling-hooks** — owns `--slds-c-*` / `--slds-g-*` theming and the SLDS 2 transition.
- **lwc/wire-service-patterns** — owns `@wire` mechanics behind the `getObjectInfo` → `getPicklistValues` chain.
- **lwc/lwc-accessibility** — owns the full a11y review; this skill only covers what base components give you for free.
