# LLM Anti-Patterns — LWC Custom Datatable Types

Common mistakes AI coding assistants make when generating or advising on custom `lightning-datatable` types. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: `this.fireAction()` Inside A Custom Cell Template

**What the LLM generates:** An `onclick={this.handleAction}` inside the `customPill.html` template, with a companion handler "attached" to the template, or a `renderedCallback` in the `.html`.

**Why it happens:** LLMs pattern-match on regular LWC components where `this` is always available. The fact that custom datatable templates are fragments with a fixed binding surface (no `this`, no lifecycle) is not in the model's default prior.

**Correct pattern:**

```html
<!-- customCell.html — no `this`, no handlers; render a child LWC for interactivity -->
<template>
    <c-custom-cell-action
        row-value={value}
        variant={typeAttributes.variant}>
    </c-custom-cell-action>
</template>
```

**Detection hint:** Grep the custom cell `.html` files for `this\.`, `onclick={this`, `renderedCallback`, `connectedCallback`, or `@wire` — none of these belong in a cell template.

---

## Anti-Pattern 2: Missing `typeAttributes` Array On `customTypes`

**What the LLM generates:**

```javascript
static customTypes = {
    statusPill: {
        template: statusPillTpl,
        standardCellLayout: true
        // typeAttributes array missing
    }
};
```

**Why it happens:** The `typeAttributes` concept has two meanings (the array on the subclass that declares which keys are legal, and the object on the column that supplies values), and LLMs often conflate them. They generate the column-side binding and skip the declaration.

**Correct pattern:**

```javascript
static customTypes = {
    statusPill: {
        template: statusPillTpl,
        standardCellLayout: true,
        typeAttributes: ['variant', 'label', 'iconName']   // every key the template reads
    }
};
```

**Detection hint:** For every `customTypes.<name>` entry, verify a `typeAttributes` array exists and that every `{typeAttributes.xxx}` in the template has a matching string entry.

---

## Anti-Pattern 3: Embedding `<lightning-record-edit-form>` In A Cell

**What the LLM generates:** A custom template that contains a full record-edit form ("so the user can edit all the fields right in the grid"), often with three or four `lightning-input-field` children.

**Why it happens:** LLMs optimize for feature richness per component and do not weigh virtualization cost. They treat each row as an isolated component.

**Correct pattern:** Keep the cell template minimal — text, icon, maybe a single input. If per-row multi-field edit is required, render a summary in the cell and a sub-LWC detail panel (modal, side sheet, row-expanded region) on demand.

```html
<!-- Cell stays trivial -->
<template>
    <span>{typeAttributes.summary}</span>
    <lightning-button-icon
        icon-name="utility:edit"
        alternative-text="Edit"
        variant="bare">
    </lightning-button-icon>
</template>
```

**Detection hint:** Search the custom cell templates for `lightning-record-edit-form`, nested `lightning-datatable`, or three-or-more `lightning-input-field` elements in one template.

---

## Anti-Pattern 4: Mutating `column.typeAttributes` After Mount And Expecting Live Re-render

**What the LLM generates:** Code that pushes into `this.columns[2].typeAttributes.options` after the datatable has rendered, assuming the grid will pick up the change.

**Why it happens:** LLMs conflate LWC reactivity (which sees assignment) with the datatable's column metadata, which it caches internally once columns are attached.

**Correct pattern:**

```javascript
// Re-assign the whole columns array so the datatable diff picks up the change.
const updated = [...this.columns];
updated[2] = {
    ...updated[2],
    typeAttributes: { ...updated[2].typeAttributes, options: newOptions }
};
this.columns = updated;
```

**Detection hint:** Look for in-place mutation of column objects (`this.columns[i].typeAttributes.x = ...`, `this.columns[i].typeAttributes.options.push(...)`).

---

## Anti-Pattern 5: Hand-Writing A `<table>` Instead Of Extending `lightning-datatable`

**What the LLM generates:** A full `<table><thead>...</thead><tbody><template for:each=...>` implementation with manual sort toggles and manual checkbox selection, reinvented from scratch.

**Why it happens:** LLMs default to generic HTML when they cannot immediately recall the subclass extension API. The output "works" for a demo dataset and loses selection, sort, inline edit, virtualization, and keyboard accessibility silently.

**Correct pattern:**

```javascript
import LightningDatatable from 'lightning/datatable';
import pillTpl from './customPill.html';

export default class CustomDatatable extends LightningDatatable {
    static customTypes = {
        statusPill: { template: pillTpl, typeAttributes: ['variant', 'label'] }
    };
}
```

**Detection hint:** If the solution includes a literal `<table>`, `<thead>`, `<tbody>`, or a hand-rolled `for:each` over `<tr>` elements, reject the approach and route the task back to extending `LightningDatatable`.
