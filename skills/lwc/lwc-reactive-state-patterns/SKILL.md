---
name: lwc-reactive-state-patterns
description: "How LWC reactivity actually works after Spring '20 (API v48+) — every class field is reactive on reassignment, but @track is still required for in-place mutation of plain object/array contents, and Date / Set / Map mutations are NEVER observed. Covers the renderedCallback infinite-loop trap, reactive-getter caching rules, and when @track is genuinely needed today. NOT for @wire reactive parameters (see lwc/wire-adapters), NOT for Lightning Data Service caching (see lwc/ldws-and-uirecordapi), NOT for cross-component reactive state (see lwc/message-channel-patterns and lwc/state-management-with-modules)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - "do I still need @track in modern lwc"
  - "lwc property changed but template did not rerender"
  - "lwc array push or object property mutation not reactive"
  - "lwc renderedCallback infinite rerender loop"
  - "lwc reactive Date Map Set not updating"
  - "lwc state management modern reactivity rules"
tags:
  - lwc
  - reactivity
  - track
  - rendered-callback
  - state-management
  - api-v48
inputs:
  - "Whether the component currently uses @track and on which fields"
  - "Whether reactive state involves Date, Set, Map, or proxied 3rd-party objects"
  - "Whether renderedCallback in the component reads or writes reactive properties"
  - "API version pinned in <componentName>.js-meta.xml"
outputs:
  - "Decision: keep, add, or remove @track on each reactive field"
  - "Refactor plan: replace in-place mutations with reassignments"
  - "Guarded renderedCallback to break re-render loops"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-01
---

# LWC Reactive State Patterns

LWC reactivity has had two eras. Before Spring '20 (API v48), every reactive
field needed `@track`. Since Spring '20, **all class fields are reactive on
reassignment** — `@track` is no longer needed for primitives or for fields
that are reassigned. But `@track` is still required for **deep observation
of plain object properties and array elements** when the field is mutated
in place. And no decorator at all makes Date, Set, or Map reactive — those
need a re-create-and-reassign discipline.

This skill teaches the contract: when reassignment is enough, when `@track`
is genuinely needed, when neither works (Date/Set/Map), and how to avoid
the canonical `renderedCallback` infinite-loop trap. It does **not** cover
`@wire` reactive parameters or Lightning Data Service — those are separate
reactivity surfaces handled by `lwc/wire-adapters` and `lwc/ldws-and-uirecordapi`.

---

## Before Starting

- Verify the component's `apiVersion` in `<componentName>.js-meta.xml`. The reactivity-on-reassignment behavior is API v48+ (Spring '20). Components pinned to v47 or earlier still need `@track` on every reactive field.
- Check whether reactive state involves **Date, Set, or Map**. None of them participate in reactivity even with `@track`. The fix is always re-create-and-reassign, not "add @track".
- Audit `renderedCallback`. Setting a reactive field inside `renderedCallback` without a guard creates an infinite re-render loop — every render fires `renderedCallback`, the new write triggers a re-render, and the hook fires again.
- Confirm whether the goal is component-local state (this skill) or cross-component shared state. Cross-component lives elsewhere (`lwc/state-management-with-modules`, `lwc/message-channel-patterns`).

---

## Core Concepts

### 1. The post–Spring '20 reactivity contract

Every class field declared on a component (without any decorator) is
reactive **when reassigned**. The template re-renders when the right-hand
side of an assignment to a referenced field changes:

```javascript
// Reactive: reassignment triggers rerender
this.count = this.count + 1;
this.user = { ...this.user, name: 'Ada' };
this.items = [...this.items, newItem];
```

No `@track` needed. The runtime detects the assignment via the underlying
reactive proxy and schedules a re-render.

### 2. When `@track` is still required

`@track` enables **deep observation** of object properties and array
elements. Without `@track`, mutating an object's property in place does
not trigger a re-render — even though the field is "reactive":

```javascript
// NOT reactive without @track
this.user.name = 'Ada';        // template does NOT rerender
this.items[0].selected = true; // template does NOT rerender
this.items.push(newItem);      // template does NOT rerender

// With @track on user and items, all three become reactive
@track user = { name: '' };
@track items = [];
```

The simple rule: **if you reassign the field reference, you do not need
`@track`. If you mutate its contents in place, you do.** Reassignment is
the recommended pattern (it composes with immutable-update libraries and
plays nicely with redux-style reducers); `@track` is the legacy escape
hatch.

### 3. What reactivity does NOT cover

The reactive proxy only tracks plain objects and arrays. The following
are silently NOT observed even with `@track`:

- **Date** — `this.lastUpdated.setHours(13)` does nothing visible. Fix: build a fresh Date and reassign.
- **Set** — `this.tags.add('vip')` does nothing visible. Fix: `this.tags = new Set([...this.tags, 'vip']);`
- **Map** — `this.cache.set(key, value)` does nothing visible. Fix: `this.cache = new Map([...this.cache, [key, value]]);`
- **3rd-party class instances** with their own internal mutability (Moment.js, RxJS Subjects, MobX observables, custom classes with setters). The framework cannot proxy them.

### 4. The `renderedCallback` infinite-loop trap

`renderedCallback` fires after every render. Writing a reactive property
inside it without a guard creates an infinite loop:

```javascript
renderedCallback() {
  this.measuredHeight = this.template.querySelector('.box').offsetHeight;
  // BUG: assignment triggers rerender → renderedCallback fires again
}
```

Two correct patterns:

```javascript
// (a) Guard with a hasRendered flag (most common)
renderedCallback() {
  if (this._hasRenderedOnce) return;
  this._hasRenderedOnce = true;
  this.measuredHeight = this.template.querySelector('.box').offsetHeight;
}

// (b) Compare-then-set (when you do need to react to layout changes)
renderedCallback() {
  const height = this.template.querySelector('.box').offsetHeight;
  if (this.measuredHeight !== height) {
    this.measuredHeight = height;
  }
}
```

The second is needed when the component must rerender on real layout
changes (e.g., responsive containers). The first is right when the
write is one-time setup.

### 5. Reactive getter caching rules

Getters that derive state from reactive fields **recompute on every
access during a render**. They are not memoized by the framework. If a
getter is expensive, cache via a setter on the source field:

```javascript
// Recomputed on every render — only cheap getters belong here
get filteredItems() {
  return this.items.filter(i => i.selected);
}

// For expensive derivations: compute once per write
set items(value) {
  this._items = value;
  this._filteredItems = value.filter(i => i.selected);
}
get items() { return this._items; }
get filteredItems() { return this._filteredItems; }
```

---

## Common Patterns

### Pattern A — Reassignment over in-place mutation (the default)

**When to use:** Any time you would write `this.x.y = z` or
`this.arr.push(x)`. This is the modern, decorator-free path.

**How it works:**

```javascript
// Object update
this.user = { ...this.user, name: 'Ada' };

// Array append
this.items = [...this.items, newItem];

// Array remove by id
this.items = this.items.filter(i => i.id !== removedId);

// Nested update — use spread chains, NOT mutation
this.form = {
  ...this.form,
  address: { ...this.form.address, city: 'Boston' },
};
```

**Why not the alternative:** In-place mutation requires `@track`,
inhibits structural sharing, and breaks if the value is later passed to
a child as `@api` (children should not see "the same reference, but
different contents now"). Reassignment communicates intent — "this is a
new value" — to both the framework and the team.

### Pattern B — `@track` only for legacy edges or genuine in-place needs

**When to use:** Three real cases.

1. The component is pinned to API v47 or earlier and cannot move.
2. A third-party library (or nested form pattern) requires in-place mutation and cannot be refactored.
3. A bound input on a deeply nested object literal needs to update in place without spreading every parent — common in form-heavy code where readability of nested updates is the constraint.

**How it works:**

```javascript
import { LightningElement, track } from 'lwc';
export default class FormComponent extends LightningElement {
  @track form = {
    address: { city: '', zip: '' },
    contact: { email: '', phone: '' },
  };

  handleChange(event) {
    // In-place mutation IS reactive because of @track
    this.form.address.city = event.target.value;
  }
}
```

**Why not the alternative:** Outside the three cases above, `@track`
is noise. It is not "safer" — adding `@track` to every field is a smell
that reads as "I do not understand the reactivity rules", and it can
mask the Date/Set/Map issue (the developer assumes `@track` covers
"everything", which it does not).

### Pattern C — Guarded `renderedCallback`

**When to use:** Anytime `renderedCallback` measures the DOM, sets up a
third-party library, or writes to a reactive field.

**How it works:** Use the `_hasRenderedOnce` guard for one-time setup;
use the compare-then-set pattern for layout-driven re-renders. Never
write a reactive field unconditionally.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update a primitive field | Plain reassignment | Reactive since Spring '20 |
| Update a property of an object field | Spread + reassign | Avoid `@track`; cleanest |
| Append/remove from an array | Spread + reassign | Same reason |
| Deeply nested form state with many bindings | `@track` on the root field | Readability beats `@track` cleanliness |
| Date / Set / Map field | Re-create + reassign | Decorator does not help |
| Read DOM in `renderedCallback` | Guarded with `_hasRenderedOnce` | Prevent infinite loop |
| Expensive getter in template | Cache via setter | Getters recompute every render |
| API version v47 or earlier | `@track` everywhere | Reactivity rules differ pre-v48 |

---

## Recommended Workflow

1. **Read the component's API version** in `js-meta.xml`. If < 48, the rules below do not apply — use `@track` on everything reactive.
2. **List the reactive fields** and classify each: primitive, object, array, Date/Set/Map, or external class instance.
3. **Replace in-place mutations** with spread-and-reassign for object/array fields. Drop `@track` from those fields if it was added defensively.
4. **For Date/Set/Map fields**, replace `.setX(...)`, `.add(...)`, `.set(k,v)` with re-create-and-reassign.
5. **Audit every `renderedCallback`** for unguarded writes to reactive fields. Add the `_hasRenderedOnce` guard or compare-then-set.
6. **Profile expensive getters** used in the template. Cache via setter where the input changes far less often than the render frequency.
7. **Re-test** with the existing Jest specs; reactivity changes are the most common silent regression.

---

## Review Checklist

- [ ] All `@track` decorators on the component are justified by one of the three Pattern B cases (legacy API, third-party constraint, deeply nested form).
- [ ] No in-place mutation of object properties or array elements outside `@track`-decorated fields.
- [ ] No `.setX()` / `.add()` / `.set(k,v)` calls on Date / Set / Map fields without a follow-up reassignment.
- [ ] Every `renderedCallback` either does not write reactive fields, or has a one-time-guard or compare-then-set pattern.
- [ ] Expensive getters used in the template are cached or moved into setter-based backing fields.
- [ ] Component's `apiVersion` is set explicitly in `js-meta.xml` (do not rely on the org-default).
- [ ] Cross-component shared state is not faked with reactive class fields — use Lightning Message Service, a custom event, or a shared module instead.

---

## Salesforce-Specific Gotchas

1. **`@track` plus `@api` on the same field is not supported.** The compiler accepts the syntax but the reactivity behavior is undefined. Pick one: a public input field is `@api` only; reactivity on internal state belongs in a separate field.
2. **Reactive proxies break `instanceof` checks.** `this.someClassInstance instanceof MyClass` may return `false` when the field is wrapped by the reactive proxy. Avoid `instanceof` on reactive-tracked references; tag the type with a string field instead.
3. **Spread-and-reassign on a 100k-item array is not free.** `this.items = [...this.items, newItem]` is O(n) per append. For genuinely large arrays, accept `@track` and `push`, or move the data behind an `@wire` adapter that does paging.
4. **`structuredClone` does not preserve reactivity.** A deep-cloned reactive object is no longer proxied. This rarely matters but bites if you clone, mutate the clone in place, then assign back — the assignment IS reactive, but intermediate steps are not what they look like.
5. **`renderedCallback` fires on every prop change**, not just initial render. Aura's `afterRender` fired only once; LWC's hook is more aggressive. Migrating Aura code that initializes a chart library inside `afterRender` will create duplicate charts in LWC.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Reactivity audit | Per-field classification (primitive / object / array / Date-Set-Map / external) and the chosen update pattern |
| Refactor plan | Specific lines/files to change to remove unnecessary `@track` and replace in-place mutations |
| `renderedCallback` guard checklist | Each `renderedCallback` in the component, marked safe / needs-guard / needs-compare-then-set |

---

## Related Skills

- `lwc/wire-adapters` — `@wire` reactive parameters (different surface, related concept).
- `lwc/ldws-and-uirecordapi` — Lightning Data Service caching; what NOT to put in component-local state.
- `lwc/state-management-with-modules` — cross-component shared state via shared ES modules.
- `lwc/message-channel-patterns` — cross-component event-based state via LMS.
- `lwc/common-lwc-runtime-errors` — sibling skill for the symptom-based debugging cousin of these issues.
- `lwc/aura-to-lwc-migration` — explains why `renderedCallback` fires more aggressively than Aura's `afterRender`.
