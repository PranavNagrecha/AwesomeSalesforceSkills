---
name: lwc-custom-event-patterns
description: "When and how to design CustomEvent traffic out of an LWC — bubbles / composed / cancelable flag choices, detail payload shape, naming rules, and propagation control. Trigger keywords: 'event not reaching parent', 'composed shadow DOM', 'CustomEvent detail mutation', 'stopPropagation vs stopImmediatePropagation'. NOT for parent-to-child communication (use `@api` — see `lwc/component-communication`), NOT for sibling fan-out (use Lightning Message Service — see `lwc/lightning-message-service`), NOT for wire-service data plumbing."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - lwc
  - custom-events
  - shadow-dom
  - bubbles
  - composed
  - event-naming
  - propagation
triggers:
  - "lwc custom event not firing on parent"
  - "child event not crossing into aura host"
  - "composed true vs false in lwc"
  - "event.detail mutated after dispatch"
  - "stopPropagation versus stopImmediatePropagation in lwc"
  - "naming convention for lwc custom events"
  - "should I use customevent or lightning message service"
inputs:
  - "Component tree shape — parent, child, deeply nested grandchild, sibling, or Aura host"
  - "What payload (if any) the event must carry"
  - "Whether the receiver lives inside the same shadow boundary, an ancestor, or a sibling subtree"
  - "Whether the event needs to be cancelable (preventDefault flow) or fire-and-forget"
outputs:
  - "Recommended dispatch shape — `new CustomEvent(name, { detail, bubbles, composed, cancelable })`"
  - "Bubbles / composed flag choice grounded in the truth table"
  - "Event-naming verdict (single-word lowercase, no `on` prefix, no hyphens)"
  - "Detail-payload shape with a frozen / cloned snapshot policy"
  - "Listener wiring guidance — `addEventListener` placement, propagation control"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# LWC Custom Event Patterns

Activate this skill when a Lightning Web Component needs to emit an event upward — to its parent, an ancestor, an Aura host, or out of a slot — and the question is which combination of `bubbles`, `composed`, and `cancelable` to use, what the `detail` payload should look like, and how to name the event so it actually fires. The four flag combinations behave very differently across light DOM, shadow DOM, and Aura host boundaries, and the wrong combination silently drops the event with no error.

This is NOT the place for parent-to-child data flow (use `@api` properties or `@api` methods — see `lwc/component-communication`), and it is NOT the right hammer for sibling-to-sibling broadcast across unrelated subtrees (use Lightning Message Service — see `lwc/lightning-message-service`). Custom events are for **child → ancestor** intent signalling within a single component tree.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Where does the listener live?** Same component? Direct parent? Grandparent or higher? An Aura host wrapping the LWC? A different page region entirely?
- **Is there a shadow DOM boundary between dispatcher and listener?** Every LWC component is its own shadow root. An event without `composed: true` cannot escape its shadow boundary, so a grandparent never sees it.
- **Does the receiver need to cancel the event?** `cancelable: true` + `event.preventDefault()` is the only way to let an ancestor veto a default action — but only if the dispatcher actually checks `event.defaultPrevented`.
- **Will the payload be mutated by anyone downstream?** `event.detail` is passed by reference; an ancestor that pushes into `event.detail.items` mutates the dispatcher's internal state.
- **Is the receiver actually in another component tree?** If yes, custom events are wrong — switch to Lightning Message Service.

---

## Core Concepts

### Every LWC Lives In Its Own Shadow Root

A Lightning Web Component renders into a closed shadow root. DOM events naturally stop at shadow boundaries unless the event is composed. This is enforced by the browser, not by Salesforce — `composed: false` events are **retargeted** so they appear to originate from the host element, but they cannot be observed from outside that host's shadow tree.

The practical consequence: if `<c-grandparent>` contains `<c-parent>` which contains `<c-child>`, an event dispatched from `<c-child>` with `composed: false` is invisible to `<c-grandparent>`'s listener. The listener never fires. There is no console warning. The event simply doesn't reach the listener.

### The bubbles + composed Truth Table

The two flags interact, and their joint behaviour is the single most-asked LWC interview question:

| `bubbles` | `composed` | Where the event travels |
|---|---|---|
| `false` | `false` | **Default.** Stays on the dispatching element. Only listeners on that exact element fire. |
| `true` | `false` | Bubbles up the DOM tree but **stops at the nearest shadow root boundary**. A direct parent inside the same shadow tree hears it; a grandparent across a shadow boundary does not. |
| `false` | `true` | Crosses shadow boundaries but does **not** bubble — only the host elements along the composed path see it. Rare; usually a mistake. |
| `true` | `true` | Bubbles up the DOM **and** crosses every shadow boundary along the way. The Aura host, the document, and any ancestor LWC can observe it. |

Salesforce's official guidance (Lightning Web Components Developer Guide → Communicate with Events): use `bubbles: false, composed: false` (the default) for most events, and only opt into `bubbles: true, composed: true` when the event genuinely needs to escape the component to reach an Aura container or a non-direct ancestor.

### Event Naming Rules Are Non-Negotiable

- **Lowercase only.** `selectionChange` is wrong; `selectionchange` is right.
- **No `on` prefix.** `onselect` is wrong; `select` is right. The `on` prefix is added by the listener template attribute (`onselect={handler}`), not by the dispatcher.
- **No hyphens.** Despite the kebab-case look of HTML, LWC custom event names are single-token lowercase. `selection-change` will not be picked up by the `onselectionchange` handler attribute.
- **No camelCase, snake_case, or PascalCase.** Anything other than a single lowercase token will silently fail to bind to the `on<eventname>` declarative attribute.
- **Use a verb or verb-phrase as a single word.** `rowclick`, `rowselect`, `valuechange`, `recordsave`. If the noun phrase is unavoidable, concatenate: `recordsavefailure`, not `record-save-failure`.

### `dispatchEvent(new CustomEvent(...))` Is The Only Idiom

The legacy `fireEvent` helper from earlier `pubsub.js` examples is **deprecated and unsupported** in modern LWC. The only sanctioned dispatch is:

```javascript
this.dispatchEvent(new CustomEvent('rowselect', {
    detail: { recordId },
    bubbles: true,      // optional, defaults to false
    composed: true,     // optional, defaults to false
    cancelable: true,   // optional, defaults to false
}));
```

Bare `dispatchEvent('rowselect')` and `dispatchEvent({ type: 'rowselect' })` do not work — the argument must be a `CustomEvent` (or other `Event`) instance constructed with `new`.

### `event.target` Versus `event.currentTarget`

- `event.target` — the element on which the event originated. Inside a parent listener for a bubbled event, this is the **child** element. Across a shadow boundary it is **retargeted** to the nearest enclosing host element, so you may not see the inner element you expected.
- `event.currentTarget` — the element on which the listener was attached. This is what the parent almost always wants when reading `dataset` or `value` from a row.

If a parent reads `event.target.dataset.recordId` to identify which row was clicked, retargeting can give them the wrong element. `event.currentTarget.dataset.recordId` reads from the listener-bound element directly and is always correct in handler code.

---

## Common Patterns

### Pattern A — Direct Parent Listening For A Child Event

**When to use:** parent owns the child in markup; the event does not need to escape to an Aura host.

**How it works:**

```javascript
// childCmp.js
this.dispatchEvent(new CustomEvent('rowselect', {
    detail: { recordId: this.recordId },
    // bubbles + composed left at default (false). The direct parent is
    // inside the same shadow tree and will receive the event.
}));
```

```html
<!-- parentCmp.html -->
<c-child-cmp onrowselect={handleRowSelect}></c-child-cmp>
```

**Why not `bubbles: true, composed: true`:** the receiver is one level up in the same shadow tree, so neither flag is required. Adding them weakens encapsulation and lets the event leak into Aura or the page chrome.

### Pattern B — Cross-Boundary Event To An Aura Host Or Distant Ancestor

**When to use:** an Aura wrapper or a non-direct ancestor LWC must hear the event.

**How it works:**

```javascript
// deeplyNestedChild.js
this.dispatchEvent(new CustomEvent('recordsavefailure', {
    detail: { recordId, errorMessage },
    bubbles: true,
    composed: true,
}));
```

```html
<!-- auraHost.cmp -->
<c:deeplyNestedChild onrecordsavefailure="{!c.handleFailure}" />
```

**Why not omit `composed`:** without `composed: true`, the event never escapes the LWC's shadow root and the Aura `onrecordsavefailure` handler never fires. The Aura host's controller method is never invoked, the user sees nothing, and there is no error in the console. Forgetting `composed: true` is the single most common LWC integration bug.

### Pattern C — Cancelable Event With An Ancestor Veto

**When to use:** the parent must be allowed to prevent a default action — for example, "before close" semantics in a modal.

**How it works:**

```javascript
// modalCmp.js
const closeEvent = new CustomEvent('beforeclose', {
    detail: { reason: 'user-clicked-x' },
    cancelable: true,
});
this.dispatchEvent(closeEvent);
if (closeEvent.defaultPrevented) {
    return; // ancestor vetoed the close
}
this.actuallyClose();
```

```javascript
// parentCmp.js
handleBeforeClose(event) {
    if (this.hasUnsavedChanges) {
        event.preventDefault();
    }
}
```

**Why not skip the `defaultPrevented` check:** `cancelable: true` only opens the door to `preventDefault()`; the dispatcher must actually check `event.defaultPrevented` afterward, otherwise the veto is ignored.

### Pattern D — Detail Payload As An Immutable Snapshot

**When to use:** any time the event detail contains arrays or objects the dispatcher still owns.

**How it works:**

```javascript
// dispatcher
this.dispatchEvent(new CustomEvent('selectionchange', {
    detail: {
        selectedIds: Object.freeze([...this.selectedIds]),
        // OR: structuredClone(this.selectedIds) for nested objects
    },
    bubbles: true,
    composed: true,
}));
```

**Why not pass `this.selectedIds` directly:** parents can `push` into the array, which mutates the dispatcher's internal state through the shared reference. `Object.freeze` plus a shallow copy gives the parent a snapshot they cannot mutate; `structuredClone` is needed when the payload contains nested objects.

---

## Decision Guidance

Choose the communication mechanism by **direction and reach**, not by feel:

| Situation | Recommended approach | Reason |
|---|---|---|
| Parent needs to push data **down** into a child | `@api` property on the child | Declarative, reactive, clearly typed; no event ceremony |
| Parent needs to **call** a child imperative method | `@api` method invoked via `template.querySelector` | Direct contract; no event needed |
| Child must signal intent **up** to a direct parent in the same shadow tree | `new CustomEvent('name')` with `bubbles: false, composed: false` | Default-safe; minimum surface area |
| Deeply nested LWC must reach a higher LWC ancestor | `new CustomEvent('name', { bubbles: true, composed: true })` | Only `composed: true` crosses shadow boundaries |
| LWC inside an Aura wrapper must signal the Aura controller | `new CustomEvent('name', { bubbles: true, composed: true })` | Aura host is across at least one shadow boundary |
| Parent must be able to **veto** a child action | `new CustomEvent('name', { cancelable: true })` + `event.preventDefault()` + `if (event.defaultPrevented) return;` | Standard DOM pattern; LWC supports it natively |
| Sibling LWCs in unrelated subtrees must communicate | **Lightning Message Service** (`lwc/lightning-message-service`) | Custom events cannot reach across detached trees |
| Cross-page or cross-region broadcast | **Lightning Message Service** | LMS is the only sanctioned channel for unrelated regions |
| Legacy `pubsub.js` from older docs | **Do not use** — migrate to LMS or custom events | Deprecated; no longer recommended by Salesforce |

---

## Recommended Workflow

1. **Locate the listener.** Identify exactly which element will call `addEventListener` (or declare `on<eventname>` in markup). Note whether it is in the same shadow tree, in an ancestor LWC, in an Aura host, or in a different region.
2. **Choose the flag combination from the truth table.** Default to `bubbles: false, composed: false`. Promote to `bubbles: true, composed: true` only when the listener is across a shadow boundary, and document why.
3. **Name the event correctly.** Single lowercase word, no `on` prefix, no hyphens, no camelCase. Prefer a verb phrase concatenated as one token.
4. **Design the detail payload defensively.** Snapshot or clone arrays and objects you still own. Document the payload shape (keys, types, optionality) in the component's events catalog using `templates/lwc-custom-event-patterns-template.md`.
5. **Decide on cancelability.** If a parent must be able to veto, set `cancelable: true` AND check `event.defaultPrevented` after dispatch.
6. **Wire the listener.** Use `event.currentTarget` (not `event.target`) to read the element you bound the listener to; `event.target` may be retargeted to a host element.
7. **Validate with the checker.** Run `python3 skills/lwc/lwc-custom-event-patterns/scripts/check_lwc_custom_event_patterns.py <path-to-lwc-folder>` and resolve any flagged dispatches.

---

## Review Checklist

- [ ] Every `dispatchEvent` call passes a `new CustomEvent(...)` (or `new Event(...)`), not a plain string or object literal.
- [ ] Event names are single lowercase words — no hyphens, no `on` prefix, no camelCase.
- [ ] `composed: true` is set on every event whose listener lives outside the dispatcher's shadow root (Aura host, grandparent LWC).
- [ ] `bubbles` is set to `true` whenever the event must travel up the DOM, regardless of shadow boundaries.
- [ ] `cancelable: true` is paired with an `if (event.defaultPrevented) return;` check on the dispatcher side.
- [ ] `detail` arrays and objects are frozen, shallow-copied, or `structuredClone`d before dispatch — no shared mutable references.
- [ ] Listeners read `event.currentTarget` (not `event.target`) when fetching `dataset` / `value` for routing.
- [ ] No event is being used to push data **down** into a child — `@api` is used instead.
- [ ] No event is being used to broadcast across unrelated subtrees — Lightning Message Service is used instead.
- [ ] No legacy `fireEvent` / `pubsub.js` calls remain.

---

## Salesforce-Specific Gotchas

Non-obvious LWC platform behaviours that cause real production problems:

1. **`composed: false` silently drops events at the shadow boundary.** No console warning, no error log, the listener simply never fires. Forgetting this flag on a deeply nested event is the most common LWC bug, and it is invisible until QA notices the missing behaviour.
2. **Hyphenated event names break the declarative `on<name>` attribute.** Dispatching `'selection-change'` while listening for `onselectionchange` matches nothing — the runtime treats `selection-change` and `selectionchange` as different event types. The dispatcher fires; nobody hears.
3. **`event.target` is retargeted across shadow boundaries.** A parent reading `event.target.dataset.id` for a bubbled+composed event sees the **host LWC element**, not the inner row that was clicked. Use `event.currentTarget`, or read the data from `event.detail` on the dispatcher side.
4. **Mutating `event.detail` in the parent leaks back into the child.** Arrays and objects in `detail` are shared references. A parent that does `event.detail.items.push(x)` corrupts the child's internal state. Snapshot or freeze before dispatch.
5. **`stopPropagation()` does not stop sibling listeners on the same element — `stopImmediatePropagation()` does.** If a row component has two listeners for `click`, calling `stopPropagation()` in the first one still lets the second fire. Use `stopImmediatePropagation()` to stop both.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Event dispatch snippet | A `new CustomEvent(name, { detail, bubbles, composed, cancelable })` call with the right flag combination for the listener location |
| Events catalog entry | A row in the component's `events.md` (using `templates/lwc-custom-event-patterns-template.md`) documenting event name, payload shape, flags, and the intended listener |
| Listener wiring | The `on<eventname>` attribute or `addEventListener` call, plus `event.currentTarget` access pattern |
| Checker run | `scripts/check_lwc_custom_event_patterns.py` clean exit on the touched LWC folder |

---

## Related Skills

- `lwc/component-communication` — when to use `@api` vs custom events vs Lightning Message Service at the architecture level (this skill is the deep dive on the custom-event branch of that decision)
- `lwc/lightning-message-service` — sibling and cross-region communication
- `lwc/aura-to-lwc-migration` — bridging custom events across the Aura/LWC boundary
- `lwc/lifecycle-hooks` — when listeners are wired and torn down (`connectedCallback` / `disconnectedCallback`)
- `lwc/lwc-error-boundaries` — handling errors that surface through custom events
