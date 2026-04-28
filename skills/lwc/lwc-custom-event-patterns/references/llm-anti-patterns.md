# LLM Anti-Patterns — LWC Custom Event Patterns

Common mistakes AI coding assistants make when generating or advising on LWC custom event traffic. Use these to self-check generated code before it lands.

---

## Anti-Pattern 1: Forgetting `composed: true` on a deeply nested event

**What the LLM generates:**

```javascript
// grandchildCmp.js
this.dispatchEvent(new CustomEvent('save', {
    detail: { recordId: this.recordId },
    bubbles: true,
    // composed missing — defaults to false
}));
```

…and a grandparent template that listens with `<c-grandchild onsave={handle}>`. The handler never fires.

**Why it happens:** training data is full of standard web-component examples where `bubbles: true` is enough because the components share a single shadow root. LWC enforces a shadow root **per component**, so `composed: true` is required to escape the dispatcher's shadow tree. The LLM also tends to omit "default-false" flags rather than spell them out.

**Correct pattern:**

```javascript
this.dispatchEvent(new CustomEvent('save', {
    detail: { recordId: this.recordId },
    bubbles: true,
    composed: true,   // explicit — required to cross shadow DOM boundaries
}));
```

**Detection hint:** the skill-local checker grep-scans for nested LWCs (folders under `lwc/*/lwc/*/`) where a `dispatchEvent(new CustomEvent(...))` call sets `bubbles: true` but does not set `composed: true`. Manual hint: any time the listener is more than one element away from the dispatcher in the rendered DOM, suspect the flag.

---

## Anti-Pattern 2: Naming events with hyphens or camelCase

**What the LLM generates:**

```javascript
this.dispatchEvent(new CustomEvent('selection-change', { detail }));
// or
this.dispatchEvent(new CustomEvent('selectionChange', { detail }));
```

…paired with `<c-child onselectionchange={handle}>` in the listener template. The handler never fires because LWC matches event types literally.

**Why it happens:** the LLM imports kebab-case from HTML attribute conventions or camelCase from React `onClick`-style props. LWC's `on<eventname>` attribute requires the dispatcher fire a single lowercase token.

**Correct pattern:**

```javascript
this.dispatchEvent(new CustomEvent('selectionchange', { detail }));
```

**Detection hint:** grep for `new CustomEvent\(['"][^'"]*[-A-Z]` — any uppercase letter or hyphen in the event-name string is a red flag. The skill-local checker reports these as P0 findings.

---

## Anti-Pattern 3: Mutating `event.detail` directly in the listener

**What the LLM generates:**

```javascript
// parentCmp.js
handleSelectionChange(event) {
    event.detail.items.push({ id: 'extra' });   // mutates child state!
    this.selection = event.detail.items;
}
```

**Why it happens:** the LLM treats `event.detail` like a return value from a pure function. In JavaScript, objects are shared references, so the parent is silently mutating the child's `selectedItems` array.

**Correct pattern:**

The dispatcher snapshots before dispatch, so the parent cannot mutate even if it tries:

```javascript
// childCmp.js
this.dispatchEvent(new CustomEvent('selectionchange', {
    detail: { items: Object.freeze([...this.selectedItems]) },
}));
```

If the LLM is writing the parent (and cannot change the dispatcher), it should still treat `event.detail` as read-only:

```javascript
handleSelectionChange(event) {
    this.selection = [...event.detail.items, { id: 'extra' }];   // copy, don't mutate
}
```

**Detection hint:** grep for `event\.detail\.[a-zA-Z]+\.(push|pop|shift|unshift|splice|sort|reverse|fill)\(` and any `event.detail.X = ` assignment.

---

## Anti-Pattern 4: Using `dispatchEvent` to push data DOWN into a child

**What the LLM generates:**

```javascript
// parentCmp.js — WRONG
this.template.querySelector('c-child').dispatchEvent(
    new CustomEvent('configure', { detail: { mode: 'compact' } })
);
```

…and a child that listens for `'configure'` events on itself in `connectedCallback`.

**Why it happens:** the LLM reaches for events as the universal communication primitive (Java Swing / DOM event background) and forgets that LWC has dedicated parent-to-child plumbing via `@api` properties.

**Correct pattern:**

```html
<!-- parentCmp.html -->
<c-child mode="compact"></c-child>
```

```javascript
// childCmp.js
import { LightningElement, api } from 'lwc';
export default class Child extends LightningElement {
    @api mode = 'expanded';   // declarative, reactive
}
```

**Detection hint:** any `template.querySelector(...).dispatchEvent(...)` call. The dispatcher should always be `this`, not a found child.

---

## Anti-Pattern 5: Calling `dispatchEvent` with a string instead of a `CustomEvent` instance

**What the LLM generates:**

```javascript
this.dispatchEvent('rowselect');                            // string — wrong
this.dispatchEvent({ type: 'rowselect', detail: { id } });  // plain object — wrong
fireEvent(this.pageRef, 'rowselect', { id });               // legacy pubsub — deprecated
```

**Why it happens:** the LLM has seen Node.js EventEmitter (`emit('event', payload)`) or AngularJS (`$broadcast('event', payload)`) APIs and assumes LWC follows the same shape. Older Salesforce blog posts also reference `pubsub.js`.

**Correct pattern:**

```javascript
this.dispatchEvent(new CustomEvent('rowselect', { detail: { id } }));
```

The argument must be an `Event` instance (usually `CustomEvent`) constructed with `new`. Plain strings and object literals do nothing — the runtime expects an `Event` and gets a `TypeError` at best, a silent no-op at worst.

**Detection hint:** the skill-local checker scans for `dispatchEvent\(` calls whose first argument does not start with `new CustomEvent(` or `new Event(`.

---

## Anti-Pattern 6: Using `event.target.dataset` for routing across shadow boundaries

**What the LLM generates:**

```javascript
// parentCmp.js
handleRowClick(event) {
    const id = event.target.dataset.recordId;   // undefined or wrong element
    this.selectedId = id;
}
```

**Why it happens:** the LLM imports the standard DOM idiom of reading `event.target.dataset` for click handlers. In LWC, when the event bubbled+composed across a shadow boundary, `event.target` is **retargeted** to the host element — not the inner button or row — so `dataset.recordId` reads from the wrong element.

**Correct pattern (one of two):**

```javascript
// Option A — read from the listener-bound element
handleRowClick(event) {
    const id = event.currentTarget.dataset.recordId;
    this.selectedId = id;
}

// Option B — put the ID in event.detail so retargeting cannot hide it
handleRowClick(event) {
    this.selectedId = event.detail.recordId;
}
```

**Detection hint:** grep for `event\.target\.dataset` in any handler attached to a custom element (`onsomething={handler}`). Switch to `event.currentTarget` or read from `event.detail`.

---

## Anti-Pattern 7: Setting `cancelable: true` without checking `event.defaultPrevented`

**What the LLM generates:**

```javascript
// modalCmp.js
this.dispatchEvent(new CustomEvent('beforeclose', { cancelable: true }));
this.actuallyClose();   // closes regardless of preventDefault()
```

**Why it happens:** the LLM remembers that `cancelable: true` enables `preventDefault()`, but copies the dispatch line without the follow-up check. The `cancelable` flag becomes decorative.

**Correct pattern:**

```javascript
const ev = new CustomEvent('beforeclose', { cancelable: true });
this.dispatchEvent(ev);
if (ev.defaultPrevented) {
    return;   // honour the parent's veto
}
this.actuallyClose();
```

**Detection hint:** any `new CustomEvent(...{ cancelable: true ...})` whose enclosing function does not subsequently reference `defaultPrevented`.

---

## Anti-Pattern 8: Reaching for `bubbles: true, composed: true` "to be safe"

**What the LLM generates:** every event in the file dispatches with `{ bubbles: true, composed: true }`, even when the listener is the immediate parent in the same shadow tree.

**Why it happens:** the LLM has been burned by the `composed: false` silent failure once and over-corrects by enabling both flags everywhere.

**Correct pattern:** start with the defaults (`bubbles: false, composed: false`). Promote to `bubbles: true, composed: true` **only** when the listener is unreachable otherwise. The reasoning should be documented in the events catalog (`templates/lwc-custom-event-patterns-template.md`).

**Detection hint:** any internal-use event (one whose listener is in the same component file or the immediate parent template) that dispatches with `composed: true`. If the events catalog doesn't justify it, the flag is over-broad.
