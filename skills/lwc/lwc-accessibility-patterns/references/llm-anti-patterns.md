# LLM Anti-Patterns — LWC Accessibility Patterns

Common mistakes AI coding assistants make when generating or advising on LWC accessibility patterns. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using aria-controls To Link Elements Across LWC Component Boundaries

**What the LLM generates:** A disclosure button in a parent component with `aria-controls="child-panel-id"` pointing at an `id` inside a child component's template. The code looks syntactically correct.

**Why it happens:** LLMs are trained on standard HTML and plain-DOM examples where `aria-controls` works globally. They do not have reliable knowledge of LWC shadow DOM IDREF resolution rules.

**Correct pattern:**

Do not use IDREF-based ARIA attributes across component boundaries. Manage the relationship through `@api` methods and `aria-expanded` state:

```javascript
// parent — correct
handleToggle() {
    this.isExpanded = !this.isExpanded;
    if (this.isExpanded) {
        this.template.querySelector('c-expandable-panel').open();
    } else {
        this.template.querySelector('c-expandable-panel').close();
    }
}
```

```html
<!-- parent button — correct -->
<button aria-expanded={isExpanded} onclick={handleToggle}>Details</button>
```

**Detection hint:** Search the generated code for `aria-controls`, `aria-owns`, or `aria-activedescendant` where the referenced `id` string appears in a different `*.html` file than the element carrying the attribute.

---

## Anti-Pattern 2: Omitting tabindex="0" From Custom Role="button" Elements

**What the LLM generates:** A `div` or `span` with `role="button"` and an `onclick` handler but no `tabindex` attribute.

**Why it happens:** LLMs often fix the semantic role correctly but pattern-match from clickable-element examples that only add `onclick`. The tabindex requirement is a separate concern that gets dropped.

**Correct pattern:**

```html
<!-- correct: role + tabindex + both activation events -->
<div
    role="button"
    tabindex="0"
    onclick={handleAction}
    onkeydown={handleButtonKey}
    class="custom-action"
>
    Activate
</div>
```

```javascript
handleButtonKey(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        this.handleAction();
    }
}
```

**Detection hint:** Any element with `role="button"` that does not also have `tabindex="0"` is missing keyboard reachability. Also check that `onkeydown` is present alongside `onclick`.

---

## Anti-Pattern 3: Conditionally Rendering the aria-live Container

**What the LLM generates:** An `aria-live` region wrapped in `<template if:true={hasResults}>` or a `v-if` directive, so it only exists in the DOM when results are present.

**Why it happens:** LLMs optimize for clean conditional rendering without understanding the browser requirement that a live region must already be observed before content changes take effect.

**Correct pattern:**

```html
<!-- correct: live region always present, text updated dynamically -->
<span class="slds-assistive-text" aria-live="polite" aria-atomic="true">
    {statusMessage}
</span>

<template if:true={results.length}>
    <!-- results content here -->
</template>
```

The `statusMessage` property starts as an empty string and is set to a descriptive value after the async operation completes.

**Detection hint:** Look for `aria-live` inside a `<template if:true>` or `<template if:false>` block. Any conditional wrapper on a live region is likely incorrect.

---

## Anti-Pattern 4: Putting .focus() Directly In renderedCallback Without A Guard

**What the LLM generates:** Focus management code placed unconditionally in `renderedCallback`, which runs on every reactive property update.

**Why it happens:** LLMs know `renderedCallback` is the LWC hook that fires after DOM updates and assume it is the right place for post-render focus calls. They do not flag the repeated-firing issue.

**Correct pattern:**

Use a boolean flag to limit focus to the specific interaction that warrants it:

```javascript
openModal() {
    this._moveFocusToModal = true;
    this.isModalOpen = true;
}

renderedCallback() {
    if (this._moveFocusToModal) {
        this._moveFocusToModal = false;
        const firstFocusable = this.template.querySelector('[data-modal-first]');
        if (firstFocusable) firstFocusable.focus();
    }
}
```

**Detection hint:** Any `this.template.querySelector(...).focus()` call inside `renderedCallback` without a preceding boolean guard is a focus-on-every-rerender bug.

---

## Anti-Pattern 5: Applying aria-label And aria-labelledby Together On The Same Element

**What the LLM generates:** An input or button with both `aria-label="Search"` and `aria-labelledby="search-heading"` applied simultaneously, assuming they stack.

**Why it happens:** LLMs may add both in an attempt to be thorough or to handle both the standalone and referenced label cases. The actual browser behavior — `aria-labelledby` wins and `aria-label` is ignored — is a spec detail that gets missed.

**Correct pattern:**

Choose one:
- Use `aria-label` when there is no visible label element on screen that describes the control.
- Use `aria-labelledby` when a visible heading or label already names the control and you want to programmatically associate it.

```html
<!-- standalone input with no visible label — use aria-label -->
<input type="search" aria-label="Search accounts" />

<!-- input near a visible heading — use aria-labelledby -->
<h2 id="filter-heading">Filter opportunities</h2>
<input type="text" aria-labelledby="filter-heading" />
```

Use `aria-describedby` (not `aria-label`) when you need to add supplemental help text or error messages alongside an already-labeled control.

**Detection hint:** Search for elements that have both `aria-label` and `aria-labelledby` attributes. Also check for `aria-describedby` being used where `aria-labelledby` was intended (describedby supplements; it does not replace the label).

---

## Anti-Pattern 6: Using Tab For Navigation Inside A Custom Listbox Or Menu

**What the LLM generates:** A custom listbox that puts `tabindex="0"` on every option and expects users to Tab between them.

**Why it happens:** Tab is the most recognizable keyboard navigation key, so LLMs default to it for "make this keyboard accessible". The WAI-ARIA roving tabindex and `aria-activedescendant` patterns are less well-known.

**Correct pattern:**

Listboxes and menus use Arrow keys for internal navigation. Only the container (the listbox itself) is in the tab order. Arrow keys move the active descendant or the roving tabindex within the widget. Tab exits the widget entirely.

```html
<ul role="listbox" tabindex="0" aria-activedescendant={activeId} onkeydown={handleKeys}>
    <template for:each={options} for:item="opt">
        <li key={opt.value} id={opt.id} role="option" aria-selected={opt.selected}>
            {opt.label}
        </li>
    </template>
</ul>
```

Each `li` has no `tabindex`. Arrow keys move `activeId` to the next/previous option id. Tab on the listbox moves focus to the next widget on the page.

**Detection hint:** Any custom listbox, combobox dropdown, or menu where individual items carry `tabindex="0"` or `tabindex="-1"` set dynamically is implementing the (more complex) roving tabindex pattern — verify the full pattern is implemented, not just partial tabindex manipulation.
