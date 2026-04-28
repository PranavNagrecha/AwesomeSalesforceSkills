---
name: lwc-focus-management
description: "Use when building LWCs that need to manage focus explicitly — modal dialogs, wizard flows, dynamic inserts, list updates, error summaries, and focus after async work. Covers focus restoration, focus traps, programmatic focus across shadow DOM, and patterns for announcing changes to assistive tech. Does NOT cover general LWC a11y audit (see lwc-accessibility)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Security
triggers:
  - "lwc focus management"
  - "focus trap modal lwc"
  - "restore focus after close lwc"
  - "programmatic focus shadow dom"
  - "lwc focus after async callout"
tags:
  - lwc
  - focus
  - accessibility
  - shadow-dom
  - keyboard
inputs:
  - Component or subtree that manipulates focus
  - Expected keyboard flows
  - Accessibility requirement (WCAG 2.1 AA or stricter)
outputs:
  - Focus map per component state
  - Focus trap and restoration plan
  - Testing approach (keyboard + screen reader)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# LWC Focus Management

## Purpose

Deterministic patterns for LWC focus management — focus restoration, traps, shadow-DOM traversal, and assistive-tech announcements — so keyboard and screen-reader users never get stranded.

## Recommended Workflow

1. **List every state transition that should move focus.** Open, close,
   error, load-complete, row added, row removed, tab switched.
2. **For each transition, specify: focus target, restoration target, and
   announcement.** A focus target alone is not enough — you also must know
   where focus should go when the state ends.
3. **Implement focus with `element.focus()` after the DOM is stable.**
   Use `renderedCallback` or `queueMicrotask` / `setTimeout(0)` to wait for
   the render.
4. **For shadow DOM, walk explicitly.** Use `this.template.querySelector`
   inside the component; if the target lives in a child component, call a
   public `focus()` method you expose on that child.
5. **Trap focus in modals.** Use the first-and-last-tab approach or a
   small helper; return focus to the opener on close.
6. **Announce changes to assistive tech.** `aria-live`, role="status", or
   role="alert" for different urgency levels.
7. **Test keyboard-only and with a screen reader.**

## Common Patterns

### Pattern 1: Modal Focus Trap With Restore

Save the opener, trap Tab between first and last focusable elements, restore on close:

```js
import { LightningElement, api } from 'lwc';

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export default class FocusTrapModal extends LightningElement {
  _opener;
  _isOpen = false;
  _focused = false;

  @api open() {
    this._opener = document.activeElement;
    this._isOpen = true;
  }

  renderedCallback() {
    if (this._isOpen && !this._focused) {
      this.template.querySelector('[data-focus="first"]')?.focus();
      this._focused = true;
    }
  }

  handleKeyDown(event) {
    if (event.key !== 'Tab' || !this._isOpen) return;
    const focusable = [...this.template.querySelectorAll(FOCUSABLE)];
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  handleClose() {
    this._isOpen = false;
    this._focused = false;
    Promise.resolve().then(() => this._opener?.focus?.());
  }
}
```

### Pattern 2: Error Summary With Field Links

Render a focusable error summary (`role="alert"`) after validation; each item focuses its field on click:

```html
<!-- errorSummary.html -->
<template>
  <template if:true={hasErrors}>
    <div role="alert" tabindex="-1" data-focus="error-summary"
         class="slds-notify slds-notify_alert slds-theme_error">
      <h2>Fix {errorCount} errors before saving</h2>
      <ul>
        <template for:each={errors} for:item="err">
          <li key={err.fieldName}>
            <a href="#" data-field={err.fieldName}
               onclick={handleErrorClick}>{err.message}</a>
          </li>
        </template>
      </ul>
    </div>
  </template>
</template>
```

```js
handleSubmit() {
  this.errors = this.validate();
  if (this.errors.length) {
    this._pendingFocus = true;   // triggers renderedCallback guard
  }
}

renderedCallback() {
  if (this._pendingFocus) {
    this._pendingFocus = false;
    this.template.querySelector('[data-focus="error-summary"]')?.focus();
  }
}

handleErrorClick(event) {
  event.preventDefault();
  const fieldName = event.currentTarget.dataset.field;
  this.template.querySelector(`[data-field-input="${fieldName}"]`)?.focus();
}
```

### Pattern 3: Async Load Complete

- After fetch resolves and list renders: move focus to the first list
  heading or a "Loaded N results" announcement region. Do NOT yank focus
  during typing.

### Pattern 4: Row Add / Remove

- Row added: focus the new row or a "row added" status region.
- Row removed: focus the next row; if none, focus the previous row; if
  none, focus the list heading.

## Shadow DOM Specifics

- `this.template.querySelector` pierces this component's shadow only.
- To focus inside a child LWC, expose a public `@api focus()` that calls
  the child's own `this.template.querySelector(...).focus()`.
- Do NOT rely on global `document.activeElement` within shadow boundaries;
  use `this.template.activeElement` where supported.

## Focus After Render

`renderedCallback` fires after each render. Guard against repeated focus
calls with a flag:

```js
renderedCallback() {
  if (this._pendingFocus) {
    this._pendingFocus = false;
    this.template.querySelector('[data-focus="primary"]')?.focus();
  }
}
```

## Testing

- Keyboard-only walk: every state transition exercised.
- Screen reader: NVDA/VoiceOver confirms the right announcement.
- Jest: spy on focus(); assert called with the expected selector.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Focus calls in `connectedCallback` before render.
- `document.querySelector` reaching into another component's shadow.
- Focus trap without restore.
- Firing `focus()` on every render — keystrokes get eaten.

## Official Sources Used

- LWC Documentation — https://developer.salesforce.com/docs/platform/lwc/guide/
- Shadow DOM and LWC — https://developer.salesforce.com/docs/platform/lwc/guide/create-shadow-dom.html
- Salesforce Accessibility — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm
- WCAG 2.1 — Focus Visible, Focus Order — https://www.w3.org/TR/WCAG21/
