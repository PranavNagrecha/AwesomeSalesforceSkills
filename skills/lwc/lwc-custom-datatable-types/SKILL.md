---
name: lwc-custom-datatable-types
description: "Use when you need to extend `lightning-datatable` with custom cell renderings: status pills, progress bars, image thumbnails, action cells, editable pickliststo, rich-text, or any column that `lightning-datatable` does not ship out of the box. Triggers: 'custom cell type lightning datatable', 'progress bar column', 'image column', 'inline edit picklist in datatable', 'rich text column'. NOT for basic datatable usage (see `lwc-data-table`) and NOT for tree-grid or large-dataset virtualization (see `virtualized-lists`)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
  - Reliability
triggers:
  - "how to add progress bar column lightning datatable"
  - "custom cell type lightning datatable"
  - "image column datatable lwc"
  - "inline edit custom type datatable"
  - "datatable picklist edit template"
  - "lightning datatable rich text column"
tags:
  - lwc-custom-datatable-types
  - lightning-datatable
  - custom-cell-type
  - edit-template
  - type-attributes
inputs:
  - "target column data shape (scalar value, object with status, url + label, etc.)"
  - "desired rendering (pill, bar, image, button group, combobox)"
  - "edit behavior (read-only, inline-editable via draft-values, or modal edit)"
  - "expected dataset size (affects virtualization budget and custom template cost)"
outputs:
  - "custom datatable subclass (.js + meta) with `customTypes` static registration"
  - "display and edit template `.html` files per custom type"
  - "guidance for wiring sortable/filterable behavior and propagating `draft-values`"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC Custom Datatable Types

Use this skill when `lightning-datatable` is the right shell for your grid but the built-in cell types (`text`, `number`, `url`, `email`, `button`, `boolean`, `date`, `currency`, `percent`, `phone`) cannot render or edit the column the way the feature demands. This skill covers subclassing the base datatable, registering `customTypes`, writing display and edit templates, integrating with sorting and inline edit, and avoiding the traps that silently break the extension.

---

## Before Starting

Gather this context before cutting code:

- Is the cell purely presentational (pill, bar, icon), or must it be inline-editable through the datatable's draft-values flow?
- What primitive value represents the cell for sorting purposes? Sorting compares the column's `value`, not the rendered DOM.
- How many rows will render at once? `lightning-datatable` virtualizes rows internally, but an expensive custom template multiplies that cost every scroll.
- Is the column safe to render (no raw HTML) or does it need sanitization before display?
- Will this extension be packaged? `customTypes` are defined per-subclass, so two downstream skills that each need a different custom type cannot be combined without building a merged subclass.

---

## Core Concepts

Custom cell types in `lightning-datatable` are a subclassing mechanism, not a slot API. The subclass registers types by name and points each one at a template `.html` file that sits next to the component. The base datatable then uses those templates when a column's `type` matches a registered custom type.

### Subclass `LightningDatatable` And Declare `customTypes`

The extension pattern is fixed by the platform: import the base class, extend it, and declare a static `customTypes` object whose keys are the new type names.

```javascript
import LightningDatatable from 'lightning/datatable';
import customPill from './customPill.html';
import customPillEdit from './customPillEdit.html';

export default class CustomDatatable extends LightningDatatable {
    static customTypes = {
        statusPill: {
            template: customPill,
            editTemplate: customPillEdit,        // optional — only if inline-editable
            standardCellLayout: true,            // reuse built-in padding, focus, edit icon
            typeAttributes: ['variant', 'label'] // MUST list every key you want to read
        }
    };
}
```

The `typeAttributes` array is the most important and the most missed piece. It names the keys the template is allowed to read out of the column's `typeAttributes` binding. If a key is not in that array, the datatable silently strips it, the template sees `undefined`, and nothing visibly fails — the cell just renders blank or default.

### Templates Are Data-Bound, Not Component Instances

The `template` and `editTemplate` HTML files are ordinary LWC template fragments, but they are evaluated against a fixed binding surface — `{value, typeAttributes, editable, context, keyField}` and the edit-template's editing equivalents. They have no `this`, no lifecycle hooks, no imperative handlers. A template cannot call `connectedCallback`, dispatch events from JavaScript, or hold state. If the cell needs interactive state (a multi-step toggle, debounced search, rich validation), the template must render a child LWC and delegate.

### Edit Templates Must Wire To `value` For Draft-Values

`lightning-datatable` emits `draft-values` when an inline edit is saved, and it discovers the new cell value by reading the input element's `value` property inside the edit template. An `editTemplate` that uses, for example, `lightning-combobox` must bind `value={typeAttributes.options}` for choices and set `value={value}` for the current cell value so the datatable's harness can capture the draft. Miss this wiring and the cell appears editable, but the Save button never lights up.

### Sorting Uses `value`, Not Rendered Output

The base datatable sorts by the column's primitive `value`, not by what the template paints. A status pill rendered from `{color: 'red', label: 'Hot'}` needs either a flat scalar in `value` or an explicit `sortBy` on the column so sort order matches the displayed order. Filtering through `lightning-datatable` itself does not ship — filtering is the consumer's job — but the same principle applies: whatever you filter against should be a stable scalar on the row.

### Custom Templates Compete For The Virtualization Budget

`lightning-datatable` virtualizes rows so that only visible rows are in the DOM. That budget is small. A lightweight template (a span with an SLDS class) is cheap; a `lightning-record-edit-form` or a nested datatable inside a cell multiplies per-row cost and breaks smooth scrolling at a few hundred rows. For any cell beyond a few SLDS-decorated elements, extract it into a child LWC and keep the template itself trivial.

---

## Common Patterns

### Status Pill / Badge Column

**When to use:** A column displays a categorical state (open/closed, healthy/warning/error) and needs color coding.

**How it works:** Register a `statusPill` custom type whose template renders `<span class={pillClass}>{typeAttributes.label}</span>`, driving `pillClass` from `typeAttributes.variant`. Keep the primitive `value` on the column as the sortable string so the built-in sort behaves sensibly.

**Why not the alternative:** Using `type: 'text'` and dumping a status word into the cell loses the visual affordance; wrapping every row in a child LWC that ingests the full record is heavier than the SLDS badge markup needs.

### Progress Bar Column

**When to use:** A numeric cell benefits from a bar (percent complete, score, SLA remaining).

**How it works:** Register a `progress` custom type whose template renders `<lightning-progress-bar value={value} variant={typeAttributes.variant}>`. Keep `value` as the numeric percent so sorting works without extra config.

**Why not the alternative:** Writing the percent as text hides scale; computing the bar width by hand in the template without `lightning-progress-bar` skips the accessibility attributes that SLDS ships.

### Editable Picklist Column

**When to use:** A column needs a dropdown edit without opening a row-level modal.

**How it works:** Register `editPicklist` with both `template` (read-only text span) and `editTemplate` (`lightning-combobox` whose `options` come from `typeAttributes.options` and whose `value` is bound to `value`). The datatable harness picks up the draft on blur or change and emits `draft-values`; the consumer saves them.

**Why not the alternative:** Navigating to a separate edit screen for a single-field change is slow and breaks the datatable's bulk-edit story.

### Action Cell With Multiple Buttons

**When to use:** Each row needs more than one action and the built-in `type: 'action'` menu is too limiting.

**How it works:** Register an `actionRow` type with a template that renders a horizontal stack of `lightning-button` elements. Dispatch a row event via a small child LWC if state (e.g., loading spinner) matters.

**Why not the alternative:** Embedding a full `lightning-button-group` with dynamic children inline in the template is fine; embedding a full form is not — that pattern belongs in a row-detail sub-LWC.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Categorical status badge or pill | Custom type with SLDS badge classes, driven by `typeAttributes.variant` | Cheap template, preserves virtualization budget |
| Numeric progress indicator | Custom type wrapping `lightning-progress-bar` | Accessible and consistent with platform UI |
| Per-row action buttons | `customTypes` with an actions array surfaced through `typeAttributes` | Keeps action logic row-scoped and event-driven |
| Full row-level edit form | Extract to a sub-LWC detail view, not a custom cell | A cell that hosts a form kills the virtualization budget |
| Editable picklist with known options | `editTemplate` using `lightning-combobox` wired to `value` | Integrates with built-in `draft-values` save flow |
| Column needs to sort on a computed key | Keep `value` as the comparable scalar; put display data in `typeAttributes` | Datatable sorts on `value`, not rendered DOM |

---

## Recommended Workflow

1. Confirm the column cannot be expressed as a built-in datatable type (re-read the base `lightning-datatable` type list).
2. Design the row shape: what scalar goes on `value`, what goes on `typeAttributes`, and whether the column is editable.
3. Scaffold the subclass: `extends LightningDatatable`, declare `static customTypes`, import each template, and list every key in `typeAttributes`.
4. Build the display template first, verify rendering on a small dataset, then add the `editTemplate` and wire `value` so `draft-values` flows correctly.
5. Profile with 200 and 1,000 rows; if scrolling lags, move interactive content into a child LWC and keep the template trivial.
6. Add sort and filter behavior by keeping `value` comparable and documenting any `sortBy` override.
7. Run `scripts/check_lwc_custom_datatable_types.py` against the component source to catch missing `typeAttributes` arrays and orphaned template filenames.

---

## Review Checklist

- [ ] The component `extends LightningDatatable` and declares `static customTypes`.
- [ ] Every registered custom type has a `typeAttributes` array listing every key its template reads.
- [ ] Each `template` and `editTemplate` points to a real sibling `.html` file next to the `.js`.
- [ ] The `editTemplate` binds the editable control's `value` to `value` so draft-values fire.
- [ ] The column's `value` is a stable scalar suitable for sorting and filtering.
- [ ] No template contains a `<lightning-record-edit-form>`, nested datatable, or heavy child tree.
- [ ] Scrolling on a representative dataset does not drop frames in a production-like org.

---

## Salesforce-Specific Gotchas

1. **`typeAttributes` names not listed are silently dropped** — a typo in the array or forgetting the array entirely makes the binding `undefined` with no console warning.
2. **Templates have no `this` and no lifecycle** — imperative handlers, `renderedCallback`, and `LightningElement` lifecycle APIs do not exist in the binding surface.
3. **Sorting ignores rendered DOM** — the column's primitive `value` drives sort order, so two rows with different pills but the same `value` appear equal.
4. **`draft-values` requires the `value` binding on the edit control** — using `selected-value` on a combobox or writing to a local proxy breaks the save path.
5. **Custom types are per-subclass** — two separate extensions cannot be mixed in one datatable instance; you must build a merged subclass that registers both.
6. **Overriding base datatable CSS is brittle** — prefer SLDS Styling Hooks where available; direct `.slds-table` overrides can break on minor-release DOM changes.
7. **Managed-package compatibility** — a subclass declared in a managed namespace renders fine, but consumers cannot add new custom types on top without a new subclass in their own namespace.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom datatable subclass (.js + .js-meta.xml) | The `extends LightningDatatable` component with `static customTypes` and template imports |
| Display / edit template `.html` files | One per custom type for render; one more per editable type for inline edit |
| Column configuration guidance | Sample column array showing `type`, `typeAttributes`, and `editable` wiring for the host component |
| Checker output | Findings from `check_lwc_custom_datatable_types.py`: missing `typeAttributes`, orphaned templates, non-subclass usage |

---

## Related Skills

- `lwc/lwc-data-table` — use when the column set fits the built-in types and you do not need a subclass.
- `lwc/virtualized-lists` — use when the dataset is large enough that even a well-behaved datatable is the wrong tool.
- `lwc/lwc-forms-and-validation` — use when the edit story is form-shaped rather than cell-shaped (per-row modal or record-edit-form).
