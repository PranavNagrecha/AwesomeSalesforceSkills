# Gotchas - LWC Accessibility

## Clickable Containers Drift Out Of Compliance Fast

**What happens:** A custom card or tile is made clickable with `onclick`, and then keyboard activation, focus styling, and announcements all need to be re-created manually.

**When it occurs:** Teams optimize for layout freedom before choosing a semantic interactive element.

**How to avoid:** Keep containers presentational and move interaction onto a button, link, or supported Lightning base component.

---

## Icon-Only Actions Need Text Equivalents

**What happens:** A pencil or trash icon is obvious visually but vague to assistive technology.

**When it occurs:** `lightning-icon` or icon buttons are used without `alternative-text` or another accessible label.

**How to avoid:** Give every meaningful icon action a clear text equivalent. Treat icons as decorative only when the adjacent text already names the action.

---

## Focus Loss Often Appears Only After Async Updates

**What happens:** Focus lands correctly on first render but disappears after save, conditional rerender, or modal close.

**When it occurs:** The component changes its template structure or closes an overlay without restoring focus.

**How to avoid:** Define focus targets for open, error, success, and close states and test them with keyboard-only navigation.

---

## Manual ARIA Can Conflict With Built-In Semantics

**What happens:** Developers add extra roles or labels to elements that already expose semantics, creating duplicate or confusing announcements.

**When it occurs:** ARIA is used defensively instead of intentionally.

**How to avoid:** Prefer native semantics first, then add ARIA only when the component truly needs extra context or a supported composite-widget pattern.
