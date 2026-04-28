# Gotchas — LWC Shadow vs Light DOM Decision

Subtle traps where the render-mode choice has consequences that do not surface in unit tests, in Storybook, or in code review — only in production or in accessibility audits.

---

## 1. CSS that "works" in Light DOM is silently a no-op in Shadow DOM (and vice versa for `:host`)

**What happens:** a developer copies a working stylesheet from a Light DOM component into a Shadow DOM component. Selectors like `body { ... }` or `.global-utility { ... }` no longer apply because the shadow root scopes them out — but no warning is emitted. Going the other way, a `:host { ... }` rule moved into a Light DOM component is silently dropped (there is no host shadow root to target).

**When it occurs:** during render-mode migration in either direction, or when a junior dev is told "make this look like that other component" and copies CSS without the surrounding render-mode context.

**How to avoid:** treat the render-mode choice as binding the CSS strategy:
- Shadow DOM → component CSS is auto-scoped, theme via `--slds-*` tokens on `:host`, no global selectors.
- Light DOM → component CSS is global, rename to `*.scoped.css` for component-local rules, drop every `:host` rule.

The skill-local checker flags both drifts.

---

## 2. `aria-describedby` and `aria-labelledby` do not cross shadow roots

**What happens:** a developer writes a form where an input inside a Shadow DOM LWC has `aria-describedby="error-msg"` and the error message lives in a sibling LWC (different shadow root). DevTools shows the attribute. Lighthouse passes. NVDA / VoiceOver silently skip the description because the IDREF resolves only within the same root.

**When it occurs:** any time an ARIA cross-reference attribute (`aria-describedby`, `aria-labelledby`, `aria-controls`, `aria-owns`, `aria-flowto`) points from inside one shadow root to an ID in another shadow root or in the document root.

**How to avoid:** either (a) put both endpoints in the same root by colocating them in the same component or by switching that component to Light DOM, or (b) restructure the markup so the description lives inside the same component as the input. There is no JavaScript fix — the spec is by-design.

---

## 3. `composed: false` on a Light DOM event is dead configuration that confuses readers

**What happens:** a component is migrated from Shadow DOM to Light DOM, and the event-dispatching code still reads `new CustomEvent('save', { bubbles: true, composed: false })`. The event still works (Light DOM has no shadow boundary to traverse, so `composed` is irrelevant for it), but the next reader assumes the explicit `composed: false` means something and tries to "fix" it.

**When it occurs:** during a Shadow → Light migration where the events were not swept.

**How to avoid:** during a render-mode migration, walk every `dispatchEvent` and:
- Light DOM: omit `composed` entirely (default is fine).
- Shadow DOM with external listeners: explicitly set `composed: true`.

The checker flags `composed: false` in a Light DOM component as P2.

---

## 4. Slotted-content lifecycle order differs between modes

**What happens:** a Shadow DOM component reads `this.querySelector('[slot="header"]')` from `connectedCallback` and gets `null`. The same code in a Light DOM component finds the slotted element. The Shadow DOM lifecycle distributes slotted children later, after `connectedCallback`, so the assumption is wrong even though it works in Light DOM by accident.

**When it occurs:** when a developer assumes "I have my slotted children when connectedCallback fires" — true in plain HTML and Light DOM, false under Shadow DOM until `slotchange` fires or `renderedCallback` runs.

**How to avoid:** for slotted content, always wire to the `slot`'s `slotchange` event or read children inside `renderedCallback`, not `connectedCallback`. The pattern works under both render modes.

---

## 5. Migrating a Shadow DOM component to Light DOM in a managed package fails at packaging time

**What happens:** an ISV partner converts a component to Light DOM mid-development to solve a CSS-bleed-in problem. The unit tests pass. The org runs fine in scratch. The packaging command fails with a Light-DOM-not-allowed error, weeks of CSS rework already invested.

**When it occurs:** any time a component destined for AppExchange distribution is opted into Light DOM.

**How to avoid:** identify managed-package candidacy in step 1 of the workflow (the runtime question). If yes, Shadow DOM is mandatory regardless of any other input. Theme via `--slds-*` tokens; do not waste cycles on a Light DOM design that will be rejected at packaging.

---

## 6. `lwc:dom="manual"` is an element-level escape hatch, not a render-mode toggle

**What happens:** a developer reaches for `lwc:dom="manual"` on a `<div>` to "let the chart library work" and assumes the rest of the component is now Light-DOM-like. It is not — only that one element is excluded from LWC's diffing. The surrounding component is still whatever render mode the class declared.

**When it occurs:** when a third-party JS library needs a target node and the developer conflates two different mechanisms.

**How to avoid:** `lwc:dom="manual"` for a single integration point inside a Shadow DOM component is the correct pattern when the rest of the component does not need Light DOM. Reach for whole-component `static renderMode = 'light'` only when host-page CSS or external DOM access is needed across the whole component.

---

## 7. A parent component theming a child must use design tokens, not selectors

**What happens:** parent CSS like `.parent c-child .button { background: red }` does not bite — the `.button` is inside a different shadow root. The developer concludes "shadow DOM doesn't let parents style children" and migrates the child to Light DOM.

**When it occurs:** when the developer treats CSS like plain HTML and reaches for descendant selectors instead of the design-tokens contract.

**How to avoid:** parent → child theming under Shadow DOM is the canonical use case for CSS custom properties. The child exposes contract tokens on `:host` (`--slds-c-button-color-background`), the parent sets them at any ancestor level, and the boundary is preserved while theming works. Migrating to Light DOM here is overkill.

---

## 8. Light DOM components ARE still subject to Lightning Web Security (LWS)

**What happens:** a developer assumes "Light DOM = no encapsulation = can do anything in JS" and writes code that pokes at `window.parent` or attempts cross-origin `postMessage` patterns. LWS sandboxes them anyway.

**When it occurs:** when a developer conflates DOM-level encapsulation (Shadow DOM) with JavaScript-level sandboxing (LWS). They are independent.

**How to avoid:** treat LWS as in scope regardless of render mode. Light DOM only opens up the DOM boundary; the JavaScript runtime is still sandboxed.
