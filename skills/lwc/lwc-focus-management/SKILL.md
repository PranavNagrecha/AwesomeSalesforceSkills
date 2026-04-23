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
updated: 2026-04-23
---

# LWC Focus Management

## Purpose

Most accessibility bugs in LWC are not missing labels — they are lost or
stolen focus. A modal opens and focus stays on the button behind it. A
validation error appears and focus stays on the submit button. Re-rendering
a list erases the user's position. Shadow DOM makes it worse because naive
`querySelector` calls fail silently. This skill gives deterministic patterns
for focus management across the common LWC cases.

## When To Use

- Building a modal, dialog, or sheet.
- Rendering a multi-step wizard in a single component.
- Asynchronously loading data and needing to direct attention afterwards.
- A validation flow where errors must be announced and actionable.
- Any component where a keyboard-only user can currently get stuck.

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

### Pattern 1: Modal Open / Close

- On open: save `document.activeElement`, move focus to the first focusable
  element in the modal (or a wrapping `dialog` heading).
- While open: trap Tab within the modal.
- On close: restore focus to the saved element if still in the DOM, else a
  sensible fallback.

### Pattern 2: Error Summary

- On submit with errors: render an error summary with a role="alert" and
  focus it.
- Each error item links to its field; clicking focuses the field.

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
