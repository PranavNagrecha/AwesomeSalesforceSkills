# LWC Focus Management — Gotchas

## 1. `connectedCallback` Runs Before Render

Calling `.focus()` there finds no DOM. Use `renderedCallback` with a
one-time flag.

## 2. Shadow DOM Silently Blocks `document.querySelector`

Cross-shadow selection either fails or is strongly discouraged. Use
`this.template.querySelector` and public `@api` methods on children.

## 3. `lightning-input` Is A Child LWC

Calling `.focus()` on a `lightning-input` element may call its host focus,
not the internal input. Confirm with `activeElement` after.

## 4. Focus Traps Need Return Path

A modal that traps focus but never restores creates a keyboard dead end.
Always save and restore.

## 5. `aria-live` Without Content Swap Does Nothing

Live regions announce when their text CHANGES. Toggling visibility alone is
not enough.

## 6. Every Render Re-Runs `renderedCallback`

Without a guard flag, focus calls run on every re-render and eat keystrokes.
