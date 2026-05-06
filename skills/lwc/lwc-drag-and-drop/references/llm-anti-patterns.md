# LLM Anti-Patterns — LWC Drag and Drop

Common mistakes AI coding assistants make when building LWC drag-and-drop.

---

## Anti-Pattern 1: `ondragover` without `preventDefault`

**What the LLM generates.**

```js
handleDragOver(event) {
    event.dataTransfer.dropEffect = 'move';
}
```

**Correct pattern.**

```js
handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
}
```

Without `preventDefault`, the element is not a valid drop target
and `drop` never fires. Universal first bug.

**Detection hint.** Any `ondragover` handler whose body does not
contain `event.preventDefault()` (or `e.preventDefault()`).

---

## Anti-Pattern 2: Reading `dataTransfer.getData` in `dragover`

**What the LLM generates.**

```js
handleDragOver(event) {
    event.preventDefault();
    const id = event.dataTransfer.getData('text/plain');
    if (id.startsWith('card-')) { /* highlight */ }
}
```

**Correct pattern.** `getData` returns empty in `dragover` for
security. Track the dragged item's metadata in component state
during `dragstart`, then read it from state in `dragover`.

**Detection hint.** Any `getData(` call inside `ondragover`,
`ondragenter`, or `ondragleave` handlers.

---

## Anti-Pattern 3: No keyboard alternative

**What the LLM generates.** A drag-and-drop component with no
arrow-key handler, no "Move to..." menu, no
`aria-describedby="drag-instructions"`.

**Correct pattern.** Provide arrow-key reordering and a "Move
to..." button menu. WCAG 2.1 SC 2.1.1 (keyboard) is mandatory;
HTML5 drag has no native keyboard support.

**Detection hint.** Any LWC with `draggable="true"` and no
`onkeydown` handler, no `lightning-button-menu`, and no
`tabindex` on the draggable elements.

---

## Anti-Pattern 4: Resetting state in `drop`, not `dragend`

**What the LLM generates.**

```js
handleDrop(e) {
    this.move(...);
    this.draggedId = null;          // wrong place
    this.overColId = null;
}
```

**Correct pattern.** Reset in `dragend` — it fires whether the
drop succeeded, was cancelled, or dropped outside a target.
`drop` is for the move logic only.

**Detection hint.** Any `drop` handler that resets
`this.draggedId`/`this.overColId` without an equivalent
`dragend` handler.

---

## Anti-Pattern 5: `setData` only on a custom MIME

**What the LLM generates.**

```js
handleDragStart(e) {
    e.dataTransfer.setData('application/x-card', JSON.stringify(payload));
}
```

**Correct pattern.** Also set `text/plain` for cross-browser
reliability:

```js
e.dataTransfer.setData('application/x-card', JSON.stringify(payload));
e.dataTransfer.setData('text/plain', payload.id);
```

Some Firefox versions reject `dragstart` without a `text/plain`
entry.

**Detection hint.** Any `setData(` call in `dragstart` that uses
a custom MIME and no `text/plain` companion.

---

## Anti-Pattern 6: Class toggling in `dragover`

**What the LLM generates.**

```js
handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('over-target');
}
```

**Correct pattern.** `dragover` fires every ~50ms during the
drag. Toggling a class on every fire is wasteful and visually
flickery if combined with transitions. Use `dragenter`/
`dragleave` for state, `dragover` only for `preventDefault` and
`dropEffect`.

**Detection hint.** Any DOM mutation (`classList.add/remove`,
`style.x = y`) inside an `ondragover` handler.

---

## Anti-Pattern 7: Mutating `data` array while dragging

**What the LLM generates.**

```js
@wire(getCards) wired({ data }) { this.cards = data; }
// during drag, wire fires again, this.cards is replaced
```

**Correct pattern.** Gate wire-driven updates on
`!this.draggedId`. Replacing the array while the user is
dragging detaches the dragged DOM node.

**Detection hint.** Any wire handler that assigns to a `@track`
array used as the source of `draggable` items, with no guard for
an active drag.
