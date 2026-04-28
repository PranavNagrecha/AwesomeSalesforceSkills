# Gotchas — LWC Custom Event Patterns

Subtle traps when designing CustomEvent traffic in Lightning Web Components. Each one has been observed in production code and silently broken behaviour with no console error.

---

## 1. `composed: false` on a deeply nested event silently drops it at the shadow boundary

**What happens:** a grandchild dispatches `new CustomEvent('save')` with default flags. The grandparent listener never fires. There is no error, no console warning, no Lightning runtime log — the event simply never reaches the listener.

**When it occurs:** any time the dispatcher and the listener are separated by one or more LWC component boundaries (each LWC is its own shadow root), and the dispatcher forgot `composed: true`.

**How to avoid:** every event whose listener lives outside the dispatcher's own shadow root must be dispatched with `bubbles: true, composed: true`. The decision rule is mechanical: "is the listener inside my template, on my host, or one element up in the same template? If no, set `composed: true`." The skill-local checker scans for nested LWCs that dispatch events without `composed: true` and flags them as a P1 finding.

---

## 2. Hyphenated event names break the declarative `on<eventname>` attribute

**What happens:** the dispatcher fires `'selection-change'`. The listener template declares `onselectionchange={handler}`. The handler never runs because LWC matches `on<lowercase token>` against the literal event type, and `selection-change` ≠ `selectionchange`.

**When it occurs:** when authors apply the kebab-case convention from HTML attributes to event names, or when an LLM imports the convention from web-components tutorials that target standard custom elements (where kebab-case is fine).

**How to avoid:** event names are **single lowercase tokens, no hyphens**. `selectionchange`, `rowclick`, `recordsavefailure`. If the noun phrase is unreadable as one word, that is a hint that the event is doing too much — split it. Lowercase concatenation is the LWC convention; kebab-case is wrong here.

---

## 3. Mutating `event.detail` in the parent corrupts the dispatcher's state

**What happens:** child dispatches `new CustomEvent('selectionchange', { detail: { items: this.selectedItems } })`. Parent does `event.detail.items.push({ id: 'x' })`. The push mutates the child's internal `selectedItems` array because both sides share the same reference.

**When it occurs:** any time the detail payload contains arrays, objects, or class instances and the parent treats them as scratch space.

**How to avoid:** the **dispatcher** is responsible for snapshotting. Three options, in increasing strictness:

```javascript
// Option A — shallow copy (works for primitive arrays)
detail: { items: [...this.selectedItems] }

// Option B — Object.freeze on the snapshot (parent gets a runtime error if it tries to mutate)
detail: { items: Object.freeze([...this.selectedItems]) }

// Option C — structuredClone (works for nested objects, dates, maps, etc.)
detail: { items: structuredClone(this.selectedItems) }
```

Strings, numbers, and booleans are immutable, so a primitive in `detail` is always safe.

---

## 4. `event.target` is retargeted across shadow boundaries — `event.currentTarget` is what you usually want

**What happens:** parent does `event.target.dataset.recordId` to know which row was clicked. For a bubbled+composed event, `event.target` is **retargeted to the nearest enclosing LWC host element**, not the inner button or row. The parent reads `undefined` (or worse, the wrong element's dataset).

**When it occurs:** any handler reading `event.target.*` for a bubbled event that crossed a shadow boundary.

**How to avoid:** prefer `event.currentTarget` (the element on which the listener was bound) for `dataset` and DOM access, and read the actual payload from `event.detail` (which the dispatcher controls and which is never retargeted).

---

## 5. Naming an event with `on` prefix or camelCase silently breaks template binding

**What happens:** dispatcher fires `'onselect'` or `'rowSelect'`. Template attribute `onrowselect={handler}` matches neither — the runtime is looking for an event named `rowselect` (lowercase, no `on` prefix). Handler never runs.

**When it occurs:** when an author imports the React `onClick` mental model (where the prefix lives on the prop) or thinks the dispatcher mirrors the listener attribute.

**How to avoid:** memorise the rule: **dispatcher fires the bare lowercase token; the template adds `on` as the listener attribute prefix**. So `dispatchEvent(new CustomEvent('select'))` ↔ `<c-child onselect={handler}>`. Anything else is wrong.

---

## 6. `stopPropagation()` does NOT stop other listeners on the same element — `stopImmediatePropagation()` does

**What happens:** a row component has two `click` listeners — one for analytics, one for selection. The selection handler calls `event.stopPropagation()` to prevent the click bubbling to the page-level handler. The analytics handler **still fires**, because `stopPropagation` only stops propagation to **other elements**, not to other listeners on the same element.

**When it occurs:** complex components with multiple handlers on the same element, or when a third-party library adds its own listeners.

**How to avoid:**

- `event.stopPropagation()` — stops the event bubbling to ancestor elements. Sibling listeners on the same element still fire.
- `event.stopImmediatePropagation()` — stops the event bubbling AND prevents any other listeners on the same element from running.

Use `stopImmediatePropagation` when you genuinely need to short-circuit everything; use `stopPropagation` when you only want to keep the event local.

---

## 7. `cancelable: true` without `defaultPrevented` check is a silent no-op

**What happens:** a modal dispatches a `'beforeclose'` event with `cancelable: true`, the parent calls `event.preventDefault()` to veto the close, and the modal closes anyway because it never inspected `event.defaultPrevented` after dispatch.

**When it occurs:** when the dispatcher pattern is copied from MDN's `CustomEvent` reference (which mentions `cancelable` but not the dispatcher-side check) without reading the LWC-specific guidance.

**How to avoid:** the cancelable pattern is **two-sided**. Set the flag, dispatch, then immediately check:

```javascript
const ev = new CustomEvent('beforeclose', { cancelable: true });
this.dispatchEvent(ev);
if (ev.defaultPrevented) return;  // honour the veto
this.actuallyClose();
```

If the dispatcher does not check, `cancelable: true` is dead weight.

---

## 8. Dispatching a CustomEvent from a wire callback can fire before `connectedCallback` finishes

**What happens:** an `@wire` adapter delivers data, the wire callback dispatches a `'dataready'` event, but the parent's `addEventListener` was attached in its own `connectedCallback`, which runs **after** the child's wire fires in some scenarios. The event is dispatched before anyone is listening.

**When it occurs:** components that fire events synchronously inside `wire` callbacks during initial render.

**How to avoid:** either wait for `renderedCallback` (which runs after the parent has had a chance to bind), or use the declarative `on<eventname>` markup attribute (which is wired before any component code runs). The `addEventListener`-in-`connectedCallback` pattern is the source of most timing bugs.
