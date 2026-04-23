# Gotchas — LWC Conditional Rendering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `lwc:if` Unmounts — It Does Not Hide

**What happens:** Flipping `lwc:if` from true to false removes the entire subtree from the DOM. Every child component is destroyed, `disconnectedCallback` fires on each, internal state (`@track` properties, form-input values, scroll position) is discarded, and references from the parent into that subtree become stale. When the branch flips back to true, a brand-new instance tree is created — the old state is not recovered.

**When it occurs:** Any time a panel, drawer, modal, wizard step, or tab-like region is toggled with `lwc:if` and the child contains state the user expects to survive the toggle (partial input, expanded rows, focused cell, accumulated selection).

**How to avoid:** Decide up front whether the toggle should "reset" or "preserve." For reset, `lwc:if` is correct. For preserve, keep the subtree mounted and hide it with CSS (`display:none` via a class getter) or lift the state into the parent so the child can be safely re-mounted.

---

## Gotcha 2: `renderedCallback` Fires Again On Every Re-Entry

**What happens:** Because the branch re-mounts, `renderedCallback` fires from scratch each time `lwc:if` flips back to true. Code that was intended to run "once" — initializing a third-party JS library, calling `.focus()`, measuring layout, registering a listener — runs again on every re-entry, causing duplicate listeners, focus stealing, or double-initialization.

**When it occurs:** Any component whose `renderedCallback` assumes a single invocation and is placed inside a `lwc:if` subtree that toggles during the page's life.

**How to avoid:** Guard every side-effect in `renderedCallback` with idempotency — a `this._rendered` flag reset when the side-effect is invalidated, or a check that the DOM is not already initialized. Where possible, move one-time init to `connectedCallback`, which fires once per component instance.

---

## Gotcha 3: `lwc:ref` To An Element Inside A False Branch Is Undefined

**What happens:** `this.refs.myInput` resolves only when the referenced element is currently in the DOM. If the element lives inside a `lwc:if` branch that is currently false, the ref is `undefined`. Calling `this.refs.myInput.focus()` throws `TypeError: Cannot read properties of undefined`.

**When it occurs:** Common pattern: a parent wants to focus a field "when the user opens the panel." The author calls `this.refs.input.focus()` immediately after setting `isOpen = true`, but the DOM has not yet rendered the new branch.

**How to avoid:** Null-check the ref, and defer focus-style side-effects to the child's `renderedCallback` or to a `setTimeout(..., 0)` / microtask after the state change. Better: let the child manage its own focus via its own `renderedCallback`.

---

## Gotcha 4: `lwc:else` Takes No Expression

**What happens:** Writing `<template lwc:else={foo}>` produces a template compile-time error. `lwc:else` is the catch-all branch and takes no value — if you have a condition to express, it should be `lwc:elseif={foo}` instead.

**When it occurs:** Authors migrating from other frameworks (or from `if:true` / `if:false` where the "else" was written as `if:false={sameProp}`) intuitively try to parameterize `lwc:else`.

**How to avoid:** Remember the rule: `lwc:if={expr}`, `lwc:elseif={expr}`, `lwc:else` (bare). The checker script flags any `lwc:else=` occurrence.

---

## Gotcha 5: `lwc:elseif` Must Immediately Follow A Sibling `lwc:if` Or `lwc:elseif`

**What happens:** The chain breaks at compile time if there is any intervening sibling element between a `lwc:if` (or `lwc:elseif`) and its follow-up `lwc:elseif` / `lwc:else`. Wrapping the `lwc:if` block in a `<div>` for layout and putting the `lwc:elseif` outside that `<div>` orphans the `lwc:elseif`.

**When it occurs:** Authors add a wrapping `<div>` for CSS reasons and forget to also move the chained branches inside, or they interleave an unrelated element between two branches of the chain.

**How to avoid:** Keep all chained branches as immediate siblings with no other elements between them. If layout requires a wrapper, wrap the whole chain — not just one branch.

---

## Gotcha 6: `lwc:if` Inside `for:each` Cannot Share Keyed-Iteration Scope

**What happens:** Using `lwc:if` inside a `for:each` is allowed, but the conditional element does not carry its own stable key for the iteration — the `key` directive lives on the iterated element, not the conditional one. Putting a `key` on a `template lwc:if` is invalid. Complex nestings can cause subtle rerender issues where the conditional subtree re-mounts even when the iteration item is stable.

**When it occurs:** Templates that mix row-level conditionals with `for:each`, especially when the conditional element is itself the iterated element.

**How to avoid:** Keep `key={item.Id}` on the iterated root and place `lwc:if` on a child element inside that root. For row-level hide/show where state matters, prefer a computed class on the iterated element over re-mounting.

---

## Gotcha 7: Complex Boolean Expressions Belong In Getters, Not The Template

**What happens:** `lwc:if={a && b}`, `lwc:if={items.length > 0}`, `lwc:if={status !== 'error'}` — none of these compile. LWC template expressions are intentionally limited to property access, member access, and function-less identifiers.

**When it occurs:** Authors coming from React/Vue where richer in-template expressions are allowed.

**How to avoid:** Move every computed boolean into a JS getter with an intention-revealing name (`isReady`, `hasItems`, `canEdit`) and reference the getter from the template. The checker flags any `&&`, `||`, `!==`, `>`, or `<` found inside `lwc:if={...}`.
