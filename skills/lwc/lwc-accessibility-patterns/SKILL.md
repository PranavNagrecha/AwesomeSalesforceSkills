---
name: lwc-accessibility-patterns
description: "Use when implementing specific ARIA attributes, keyboard navigation patterns, screen reader live regions, WCAG 2.1 compliance, focus management, or accessible data tables in Lightning Web Components. Trigger keywords: ARIA, aria-live, aria-label, aria-labelledby, role=grid, tabindex, keydown handler, WCAG AA, focus trap, accessible datatable, shadow DOM ARIA boundary. NOT for general LWC styling, visual design, SLDS theming, or CSS that does not affect assistive-technology behavior."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Security
tags:
  - aria
  - keyboard-navigation
  - wcag
  - focus-management
  - screen-reader
  - accessible-datatable
triggers:
  - "how do I add aria-label or aria-labelledby to an LWC component"
  - "keyboard navigation not working in custom listbox or menu"
  - "screen reader is not announcing async search results in my lwc"
  - "aria-controls across components is not working in Lightning"
  - "how do I implement a focus trap inside an LWC custom modal"
  - "WCAG 2.1 AA compliance for AppExchange app in lwc"
  - "custom data table in lwc needs accessible row and cell roles"
inputs:
  - "the interactive HTML structure of the component (template markup)"
  - "which ARIA attributes or keyboard interactions are needed"
  - "whether the component crosses shadow DOM boundaries to child components"
  - "whether the use case needs a live region, focus trap, or custom table"
outputs:
  - "corrected template markup with ARIA attributes and keyboard handlers"
  - "focus-management pattern using template.querySelector() or @api methods"
  - "accessible data table structure using lightning-datatable or role=grid"
  - "WCAG 2.1 AA compliance checklist for the component"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when a Lightning Web Component requires precise ARIA attribute usage, keyboard interaction models, screen reader live regions, or accessible data table structure. The companion skill `lwc/lwc-accessibility` covers posture and design decisions; this skill covers the concrete implementation patterns that practitioners get wrong in LWC's shadow DOM environment.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which ARIA pattern is needed: labeling, live region, custom widget role, or table structure?
- Does the component need to reference an element in a different component's shadow tree? If so, aria-controls and aria-owns will not work across the boundary.
- Is the component part of an AppExchange managed package? If yes, WCAG 2.1 AA is a hard requirement, not a preference.

---

## Core Concepts

### Shadow DOM Blocks Cross-Component ARIA Relationships

Lightning Locker and Lightning Web Security both enforce shadow DOM boundaries. ARIA relationship attributes — `aria-controls`, `aria-owns`, `aria-activedescendant` — rely on IDREF values that must resolve within the same DOM scope. When the controlling element and the controlled element live in different LWC component shadows, the browser cannot resolve the reference and the ARIA relationship silently breaks.

The practical implication: custom comboboxes, disclosure buttons, or tabpanels that span two LWC components cannot use `aria-controls` to wire them together unless both the trigger and the target are in the same component's template. When a cross-component relationship is unavoidable, expose `@api` methods on the child so the parent can call `focus()` or manage state directly rather than relying on broken IDREF wiring.

### WCAG 2.1 AA Is The AppExchange Accessibility Standard

Salesforce requires WCAG 2.1 Level AA compliance for all AppExchange-listed apps. Key criteria that LWC patterns directly affect:

- **1.3.1 Info and Relationships** — roles, labels, and structure must be programmatic, not only visual
- **1.4.1 Use of Color** — error states cannot be communicated by color alone
- **2.1.1 Keyboard** — all functionality must be reachable via keyboard
- **2.4.3 Focus Order** — focus sequence must be logical relative to content order
- **4.1.2 Name, Role, Value** — interactive elements must expose name, role, and state to assistive technology

### Keyboard Interaction Models For Custom Widgets

Native HTML interactive elements handle keyboard automatically. Any element that departs from native semantics needs an explicit keyboard contract. The WAI-ARIA Authoring Practices Guide defines interaction models per widget type:

- **Listbox / combobox:** Arrow Up/Down move between options; Enter or Space select; Escape closes; Home/End jump to first/last option.
- **Menu / menubar:** Arrow keys navigate items; Escape closes; Tab moves focus out of the menu entirely.
- **Tab panel:** Arrow keys switch tabs; Tab moves into the tab panel content.
- **Grid / data table:** Arrow keys navigate cells; Tab exits the grid.

In LWC, implement these by attaching a `keydown` handler in the template and dispatching or calling the appropriate logic based on `event.key`. The handler must call `event.preventDefault()` for any key that would otherwise cause page scroll (Arrow keys, Space, Enter on custom controls).

### Focus Management Is An Explicit Responsibility

The LWC rendering engine does not restore focus after rerenders, conditional template swaps, or async state changes. Every interaction that removes an element from the DOM — closing a modal, collapsing a section, saving a form — must include deliberate focus placement.

Within a single component, use `this.template.querySelector('[data-focus-target]')` to reach elements and call `.focus()`. To focus an element inside a child component, the child must expose an `@api` method that calls `.focus()` on its internal element; the parent then calls `childComponent.focusMethod()` after the interaction completes.

### aria-label vs aria-labelledby

- Use `aria-label` when there is no visible text that labels the control, or when you need to override the visible text with a more descriptive string.
- Use `aria-labelledby` when a visible text element already describes the control and you want to reference it programmatically. Point the value to the `id` of the visible label element.
- Do not use both on the same element — `aria-labelledby` wins and `aria-label` is ignored.
- `aria-describedby` supplements the label with additional context (error messages, help text) and does not replace the label.

---

## Common Patterns

### Live Region For Async Announcements

**When to use:** The component loads data asynchronously and users need to know when results are ready (search, filtering, record counts, save confirmation).

**How it works:** Add a container with `aria-live="polite"` to the template. Update its text content after the async operation completes. Screen readers announce the updated text at the next pause in the user's activity.

```html
<!-- template -->
<template>
    <lightning-input
        label="Search accounts"
        onchange={handleSearch}
    ></lightning-input>
    <div class="slds-assistive-text" aria-live="polite" aria-atomic="true">
        {searchStatusMessage}
    </div>
    <template if:true={results.length}>
        <!-- results list -->
    </template>
</template>
```

```javascript
// component JS
async handleSearch(event) {
    this.searchStatusMessage = '';
    this.results = await searchAccounts({ term: event.target.value });
    this.searchStatusMessage = `${this.results.length} results loaded`;
}
```

Use `aria-live="assertive"` only for urgent errors that must interrupt the user immediately. Polite is the correct default for informational updates.

**Why not the alternative:** Without a live region, screen reader users receive no announcement that results have changed. They must navigate to find the new content manually.

### Custom Listbox With Arrow Key Navigation

**When to use:** A business requirement forces a custom listbox, combobox, or menu that cannot be replaced by `lightning-combobox`.

**How it works:** Mark the container with `role="listbox"`, options with `role="option"`, and use `aria-activedescendant` on the listbox to point to the currently highlighted option. Handle Arrow keys in the `keydown` handler to update the active descendant. Because `aria-activedescendant` only uses the `id` of an element in the same shadow scope, all options must be in the same component template.

```html
<template>
    <ul
        role="listbox"
        aria-label="Select an account type"
        aria-activedescendant={activeOptionId}
        tabindex="0"
        onkeydown={handleKeydown}
    >
        <template for:each={options} for:item="opt">
            <li
                key={opt.value}
                id={opt.id}
                role="option"
                aria-selected={opt.selected}
                data-value={opt.value}
                onclick={handleSelect}
            >{opt.label}</li>
        </template>
    </ul>
</template>
```

```javascript
handleKeydown(event) {
    const keys = ['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', 'Escape'];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    // update this.activeIndex based on event.key
}
```

**Why not the alternative:** Using `tabindex` on every `li` and Tab to navigate between them violates the WAI-ARIA listbox pattern and creates a confusing tab stop count for keyboard users.

### Accessible Data Table With Custom Markup

**When to use:** `lightning-datatable` cannot meet the layout or interaction requirements, and a custom table is unavoidable.

**How it works:** Add `role="grid"` on the wrapping element with `aria-rowcount` and `aria-colcount`. Each row gets `role="row"`, header cells get `role="columnheader"`, data cells get `role="gridcell"`. Interactive cells must be keyboard reachable.

```html
<table role="grid" aria-label="Opportunities" aria-rowcount={totalRows} aria-colcount="4">
    <thead>
        <tr role="row">
            <th role="columnheader" scope="col" aria-sort="ascending">Name</th>
            <th role="columnheader" scope="col">Amount</th>
            <th role="columnheader" scope="col">Stage</th>
            <th role="columnheader" scope="col">Close Date</th>
        </tr>
    </thead>
    <tbody>
        <template for:each={rows} for:item="row">
            <tr key={row.Id} role="row">
                <td role="gridcell">{row.Name}</td>
                <td role="gridcell">{row.Amount}</td>
                <td role="gridcell">{row.StageName}</td>
                <td role="gridcell">{row.CloseDate}</td>
            </tr>
        </template>
    </tbody>
</table>
```

Prefer `lightning-datatable` when it can meet the requirements. It provides built-in sorting announcements, row selection, and keyboard navigation at no additional cost.

**Why not the alternative:** A plain `<table>` without ARIA grid semantics announces correctly for static tables but does not expose interactive grid navigation to screen readers when cells contain interactive controls.

### Making A div Button Accessible (Last Resort)

**When to use:** Only when a styled container genuinely cannot be replaced with a semantic button and must remain interactive.

**How it works:** Add `role="button"`, `tabindex="0"`, and both `onclick` and `onkeydown` handlers that respond to Enter and Space.

```html
<div
    role="button"
    tabindex="0"
    aria-pressed={isActive}
    onclick={handleClick}
    onkeydown={handleKeydown}
    class="custom-toggle"
>
    {label}
</div>
```

```javascript
handleKeydown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        this.handleClick();
    }
}
```

**Why not the alternative:** A `role="button"` div without `tabindex="0"` is not reachable by keyboard. A div with `onclick` only will activate on mouse but not on Enter/Space. Both gaps fail WCAG 2.1.1.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard button, input, or select | Use `lightning-button`, `lightning-input`, `lightning-combobox` | Built-in keyboard and ARIA behavior, no custom code needed |
| Async result count or save confirmation | `aria-live="polite"` container updated by JS | Only reliable way to announce changes to screen reader users |
| Custom listbox in a single component | `role="listbox"` + `aria-activedescendant` in same shadow | IDREF-based attributes only work within one shadow scope |
| aria-controls from component A to component B | Expose `@api focus()` on the child, call it from the parent | Cross-shadow IDREF attributes silently fail in LWC |
| Sortable data table with row selection | `lightning-datatable` | Built-in aria-sort, aria-selected, and keyboard grid navigation |
| Custom table unavoidable | `role="grid"`, `role="row"`, `role="gridcell"`, `aria-rowcount` | Required for screen readers to understand grid structure |
| Focus management after async save | `this.template.querySelector('[data-focus-target]').focus()` | LWC does not restore focus after rerender automatically |
| Label for a standalone control | `aria-label` | No visible label element to reference |
| Label referencing visible heading text | `aria-labelledby` pointing to the heading's `id` | Reuses visible text, avoids duplication |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner implementing accessibility patterns in LWC:

1. **Identify the accessibility need** — determine whether the gap is labeling, keyboard interaction, live region, focus management, or data table structure. Confirm whether the component crosses shadow boundaries that will block ARIA IDREF attributes.
2. **Choose the right base component** — check whether `lightning-datatable`, `lightning-combobox`, `lightning-button`, or another base component already covers the requirement. Prefer base components over custom ARIA implementations.
3. **Implement the pattern** — apply the appropriate pattern from the Common Patterns section: add `aria-label`/`aria-labelledby`, wire a `aria-live` region, implement the WAI-ARIA keyboard model for the widget type, or add grid roles to the custom table.
4. **Add keyboard handlers** — for any custom widget, attach a `keydown` handler that implements the full interaction model for the role. Call `event.preventDefault()` on keys that control navigation so the browser default (scroll, tab) does not interfere.
5. **Manage focus explicitly** — for every open/close/save/error transition, identify the focus target and call `.focus()` on it after the DOM settles (use `Promise.resolve().then()` or `renderedCallback` if needed after conditional rerender).
6. **Test with keyboard and screen reader** — walk through all interactive states using Tab, Shift+Tab, Arrow keys, Enter, Escape. Verify screen reader announcements with VoiceOver (macOS/iOS) or NVDA (Windows). Confirm the Review Checklist below passes.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All ARIA IDREF attributes (`aria-controls`, `aria-owns`, `aria-activedescendant`) reference IDs within the same component template.
- [ ] Custom interactive elements with `role="button"` or other widget roles have `tabindex="0"` and `onkeydown` handlers for Enter/Space.
- [ ] Custom listboxes or menus implement Arrow key navigation, Home/End, Enter for selection, and Escape for close.
- [ ] Live regions (`aria-live`) are present for all async updates that users need to know about.
- [ ] Focus is explicitly placed after every open, close, save, and error state transition.
- [ ] Custom data tables use `role="grid"`, `aria-rowcount`, `aria-colcount`, `role="row"`, and `role="gridcell"` (or `lightning-datatable` is used instead).
- [ ] `aria-label` is used for standalone labels; `aria-labelledby` references a visible element's `id`.
- [ ] WCAG 2.1 AA criteria 1.3.1, 2.1.1, 2.4.3, and 4.1.2 are verifiably met for interactive elements.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`aria-controls` silently fails across LWC shadow boundaries** — both Lightning Locker and Lightning Web Security enforce shadow DOM, so IDREF attributes that point outside the current component's shadow tree resolve to nothing. No browser warning is shown; the ARIA relationship simply does not exist. Always keep the controlling element and the target in the same component template.
2. **`this.template.querySelector()` cannot reach into a child component's shadow** — you can query elements in the current component's template, but child LWC component internals are behind their own shadow root. To focus an element inside a child, the child must expose a public `@api` method that calls `.focus()` internally.
3. **`renderedCallback` fires on every rerender, not just first render** — placing `focus()` calls directly in `renderedCallback` without a guard causes focus to jump on every state change. Guard with a flag (`this._focusPending`) and clear it after the call.
4. **`aria-live` regions must exist in the DOM before content changes** — if you conditionally render the live region with `if:true`, the initial insertion is not announced. The region must be present (possibly empty) in the DOM before the announcement text is updated.
5. **`role="button"` on a `div` requires both `tabindex="0"` and a `keydown` handler for Enter AND Space** — browsers do not fire `click` events for Space on non-native buttons. An `onclick`-only handler means keyboard users who press Space get no response.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected template markup | HTML template with proper ARIA attributes, roles, and tabindex values applied |
| Keyboard handler implementation | `keydown` JS handler implementing the full WAI-ARIA interaction model for the widget type |
| Focus management code | `@api` focus methods and `template.querySelector().focus()` calls for all state transitions |
| WCAG 2.1 AA checklist | Component-specific checklist against the criteria most relevant to LWC interactive patterns |

---

## Related Skills

- `lwc/lwc-accessibility` — use for overall accessibility posture, design decisions, and the base-component-first principle before reaching for custom ARIA.
- `lwc/lwc-modal-and-overlay` — use when the main challenge is modal dialog lifecycle and focus trapping within LightningModal.
- `lwc/lwc-data-table` — use when the accessibility requirement is specifically tied to data table sort, row selection, and inline edit behavior.
- `lwc/lwc-testing` — use alongside this skill to write Jest or manual tests that verify keyboard and screen reader behavior.
