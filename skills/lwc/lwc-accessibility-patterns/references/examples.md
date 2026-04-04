# Examples — LWC Accessibility Patterns

## Example 1: Live Region Announcing Async Search Results

**Context:** A component provides an account search field. Results load asynchronously after the user types. Mouse users see results appear, but screen reader users receive no announcement.

**Problem:** Without a live region, JAWS and VoiceOver users must manually navigate to discover that the list changed. They have no way of knowing results loaded or how many are available.

**Solution:**

Add a visually hidden `aria-live="polite"` div. Update its text after the wire or imperative Apex call resolves. The region must exist in the DOM before the text changes — do not conditionally render it.

```html
<!-- accountSearch.html -->
<template>
    <lightning-input
        label="Search accounts"
        placeholder="Type to search..."
        onchange={handleInput}
    ></lightning-input>

    <!-- Live region: always in DOM, empty until results load -->
    <span class="slds-assistive-text" aria-live="polite" aria-atomic="true">
        {statusMessage}
    </span>

    <ul aria-label="Search results">
        <template for:each={results} for:item="acct">
            <li key={acct.Id}>
                <lightning-button
                    label={acct.Name}
                    variant="base"
                    data-id={acct.Id}
                    onclick={handleSelect}
                ></lightning-button>
            </li>
        </template>
    </ul>
</template>
```

```javascript
// accountSearch.js
import { LightningElement, track } from 'lwc';
import searchAccounts from '@salesforce/apex/AccountSearchController.search';

export default class AccountSearch extends LightningElement {
    @track results = [];
    statusMessage = '';

    async handleInput(event) {
        const term = event.target.value;
        if (term.length < 2) return;
        this.statusMessage = '';           // clear before new search
        this.results = await searchAccounts({ searchTerm: term });
        this.statusMessage = this.results.length
            ? `${this.results.length} accounts found`
            : 'No accounts found';
    }
}
```

**Why it works:** The live region is always in the DOM so the browser has already registered it as a speech target. Updating the text after results load triggers an announcement on the next speech pause. Setting `aria-atomic="true"` ensures the entire message is read rather than just the changed characters.

---

## Example 2: Arrow Key Navigation In A Custom Option List

**Context:** A requirement forces a custom styled listbox for record type selection. The `lightning-combobox` cannot be themed to match the design specification.

**Problem:** The component wraps options in `div` elements. Mouse users click to select, but keyboard users have no way to navigate between options. Screen readers announce a generic container rather than a list of selectable options.

**Solution:**

Implement the WAI-ARIA listbox pattern. Place `role="listbox"` on the container and `role="option"` on each item. Use `aria-activedescendant` to track the highlighted option without moving DOM focus away from the container. Handle Arrow, Home, End, Enter, and Escape in a `keydown` handler.

```html
<!-- recordTypePicker.html -->
<template>
    <div
        id="listbox-container"
        role="listbox"
        tabindex="0"
        aria-label="Select record type"
        aria-activedescendant={activeId}
        onkeydown={handleKeydown}
        class="custom-listbox"
    >
        <template for:each={options} for:item="opt">
            <div
                key={opt.value}
                id={opt.id}
                role="option"
                aria-selected={opt.isSelected}
                data-value={opt.value}
                onclick={handleClick}
                class={opt.cssClass}
            >
                {opt.label}
            </div>
        </template>
    </div>
</template>
```

```javascript
// recordTypePicker.js
import { LightningElement, api, track } from 'lwc';

export default class RecordTypePicker extends LightningElement {
    @track activeIndex = 0;

    options = [
        { value: 'business', id: 'opt-0', label: 'Business Account', isSelected: false },
        { value: 'person', id: 'opt-1', label: 'Person Account', isSelected: false },
        { value: 'partner', id: 'opt-2', label: 'Partner Account', isSelected: false },
    ];

    get activeId() {
        return this.options[this.activeIndex]?.id ?? '';
    }

    handleKeydown(event) {
        const { key } = event;
        if (!['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', 'Escape', ' '].includes(key)) {
            return;
        }
        event.preventDefault();

        if (key === 'ArrowDown') {
            this.activeIndex = Math.min(this.activeIndex + 1, this.options.length - 1);
        } else if (key === 'ArrowUp') {
            this.activeIndex = Math.max(this.activeIndex - 1, 0);
        } else if (key === 'Home') {
            this.activeIndex = 0;
        } else if (key === 'End') {
            this.activeIndex = this.options.length - 1;
        } else if (key === 'Enter' || key === ' ') {
            this.selectOption(this.activeIndex);
        } else if (key === 'Escape') {
            this.dispatchEvent(new CustomEvent('close'));
        }
    }

    handleClick(event) {
        const idx = this.options.findIndex(o => o.value === event.currentTarget.dataset.value);
        if (idx >= 0) {
            this.activeIndex = idx;
            this.selectOption(idx);
        }
    }

    selectOption(index) {
        this.options = this.options.map((o, i) => ({ ...o, isSelected: i === index }));
        this.dispatchEvent(new CustomEvent('select', { detail: this.options[index].value }));
    }
}
```

**Why it works:** `aria-activedescendant` tells screen readers which option is currently highlighted without moving real DOM focus, which means the keyboard handler on the listbox container remains active throughout navigation. All IDREF values (`id` attributes) are in the same component shadow, so the attribute resolves correctly.

---

## Anti-Pattern: Using aria-controls Across Component Boundaries

**What practitioners do:** They build a disclosure button in a parent component that should expand a panel inside a child component. They add `aria-controls="panel-id"` on the button, assuming the browser will wire them together.

```html
<!-- parent.html — BROKEN -->
<button aria-controls="child-panel" onclick={toggle}>Toggle</button>
<c-child-panel></c-child-panel>
```

```html
<!-- childPanel.html -->
<div id="child-panel" role="region">...</div>
```

**What goes wrong:** LWC shadow DOM means the `id="child-panel"` in `c-child-panel`'s shadow is invisible to the parent's shadow. The browser resolves `aria-controls="child-panel"` against the parent's shadow scope, finds nothing, and the relationship is silently broken. Screen readers announce the button as having no associated panel.

**Correct approach:** Move both the button and the panel into the same component template so the IDREF resolves within one shadow scope. If the expanded content must live in a child component, expose an `@api open()` method on the child and call it from the parent. Manage `aria-expanded` state on the button in the parent based on the child's reported state.

```html
<!-- parent.html — correct -->
<button
    aria-expanded={isOpen}
    onclick={handleToggle}
>Toggle</button>
<c-child-panel lwc:ref="panel"></c-child-panel>
```

```javascript
// parent.js
handleToggle() {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
        this.refs.panel.open();   // @api method on child
    } else {
        this.refs.panel.close();
    }
}
```
