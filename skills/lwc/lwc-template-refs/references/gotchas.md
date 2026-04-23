# Gotchas — LWC Template Refs

Non-obvious platform behaviors that cause real production problems when using `lwc:ref`.

## Gotcha 1: `this.refs` is undefined in `connectedCallback`

**What happens:** Accessing `this.refs.<name>` in `connectedCallback` throws `TypeError: Cannot read properties of undefined (reading '<name>')`.

**When it occurs:** Any code that tries to focus an input, read a value, or call an `@api` child method on mount. LWC populates `this.refs` during the first render pass, and `connectedCallback` runs before that pass completes.

**How to avoid:** Move DOM work to `renderedCallback` (or a later user-event handler) and guard one-shot actions with a boolean flag. If you need the side effect to happen as early as possible, `renderedCallback` still fires on the first render.

---

## Gotcha 2: Refs inside `for:each` do not work

**What happens:** A ref declared inside an iterator either fails at compile time or produces an unpredictable single-element lookup because the name is reused on every iteration.

**When it occurs:** Any template with `<template for:each=... for:item=...>` or `iterator:`. The docs explicitly state that `lwc:ref` must not be used inside these constructs.

**How to avoid:** Use `data-*` attributes on the iterated element and resolve per-row identity with `event.target.closest('[data-*]')` inside a delegated event handler. For bulk reads use `this.template.querySelectorAll` on the container.

---

## Gotcha 3: Refs inside `lwc:if` are undefined when the branch is false

**What happens:** `this.refs.<name>` returns `undefined` — not `null`, not an element — whenever the enclosing `lwc:if` evaluates to false, because the element is not in the DOM.

**When it occurs:** Conditionally rendered modals, tabs, error panels, disclosure sections. Code that always calls `this.refs.x.focus()` throws the first time the branch is collapsed.

**How to avoid:** Use optional chaining (`this.refs.emailInput?.focus()`) or an explicit guard (`if (this.refs.emailInput) { ... }`). Remember that when the branch becomes true again, the next `renderedCallback` is the first moment the ref resolves.

---

## Gotcha 4: Refs stop at the child custom element boundary

**What happens:** If you put `lwc:ref="chart"` on `<c-chart>`, `this.refs.chart` resolves to the child's host element — but you cannot drill further into the child's internal DOM, read its private state, or call methods that are not marked `@api`.

**When it occurs:** Any attempt to `this.refs.chart.template.querySelector(...)` or to reach into a child library component to tweak its internals.

**How to avoid:** Treat the shadow boundary as intentional. Add `@api` methods or dispatch events from the child to expose the behavior you need. If you own the child, that is the right refactor. If you don't, there is no supported workaround — and LWS will harden this further.

---

## Gotcha 5: `this.refs` is a fresh lookup, not a cached reference

**What happens:** `this.refs` resolves against the current render tree on every access. Stashing `this._emailInput = this.refs.emailInput` in `connectedCallback` (or even `renderedCallback`) and reusing it later across rerenders can leave you holding a stale node — or `undefined`.

**When it occurs:** Components that try to "cache" ref lookups for performance or convenience, especially across conditional re-renders.

**How to avoid:** Re-read `this.refs.<name>` at the point of use. The lookup is already cheap. If you genuinely need to cache across a single logical operation (e.g., within one submit handler), assign to a local `const` inside that function and let it die at function scope.

---

## Gotcha 6: `this.template.querySelector` is still valid and sometimes required

**What happens:** Migration plans that try to replace every `querySelector` with `lwc:ref` hit walls at list rendering, dynamic children, and complex selectors — none of which refs cover.

**When it occurs:** Mechanical migrations driven by codemods that do not distinguish single-element lookups from list lookups.

**How to avoid:** Keep `this.template.querySelector` and `querySelectorAll` for iterator children, attribute-based selections (`[data-id="..."]`), and any case where you need a collection. Refs and selectors coexist cleanly.

---

## Gotcha 7: Name collisions across templates are fine, collisions within one template are not

**What happens:** A component that returns different templates from `render()` can reuse the same ref name in each template safely — refs are scoped per template root. But two elements in the same template with the same `lwc:ref` value produce undefined behavior.

**When it occurs:** Components that branch on `render()` for A/B tests or feature flags, or copy-paste refactors that duplicate a ref name accidentally.

**How to avoid:** Within a single template, audit for duplicate `lwc:ref="<name>"` values — the checker script flags this. Across templates, reusing a short, meaningful name is actually the recommended idiom.
