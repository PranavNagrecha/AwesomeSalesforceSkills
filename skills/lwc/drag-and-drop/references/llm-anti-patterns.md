# LLM Anti-Patterns — LWC Drag and Drop

---

## Anti-Pattern 1: Framework event modifiers that LWC does not have

**What the LLM generates:**

```html
<li ondragover.prevent ondrop={handleDrop}>
```

or `@dragover.prevent`, or `(dragover)="$event.preventDefault()"`.

**Why it happens:** Vue's `.prevent` and Angular's inline expression syntax are
enormously represented in drag-and-drop tutorials, and LWC's `on<event>` binding
looks close enough to Vue's that the modifier grafts on without friction. The
model is completing a familiar template idiom.

**Correct pattern:** LWC has no event modifiers and no inline expressions. Every
handler is a method, and `preventDefault()` is called inside it.

**Detection hint:** a dot or an `$event` in an `on*` attribute. This produces no
error, no warning, and a drop that never fires — the single most common cause of
"LWC drag and drop doesn't work."

---

## Anti-Pattern 2: Omitting `preventDefault` on `dragover` altogether

**What the LLM generates:** `dragstart` and `drop` handlers with no `dragover`
handler at all.

**Why it happens:** the drag starts and the drop is where the work happens, so
those two look like the complete pair. `dragover` reads as an intermediate event
you would only handle for visual feedback, and the fact that it *gates* the drop
is counterintuitive.

**Correct pattern:** `preventDefault()` on `dragover` is what declares the
element a valid drop target. Without it the browser rejects the drop by default.
Assert it in a Jest test — it is the cheapest guard against a silent failure.

**Detection hint:** no `ondragover` binding in a template that has `ondrop`.

---

## Anti-Pattern 3: Reading `dataTransfer` outside the event

**What the LLM generates:**

```javascript
handleDragStart(event) { this.dragEvent = event; }
handleDrop() { const id = this.dragEvent.dataTransfer.getData('text/plain'); }
```

**Why it happens:** stashing an event object for later is a normal JavaScript
pattern and works for almost every other event type. `DataTransfer`'s protected
mode is a spec detail with no analogue elsewhere.

**Correct pattern:** `setData` synchronously in `dragstart`, `getData`
synchronously in `drop`. Outside those windows reads return an empty string
silently.

**Detection hint:** any `dataTransfer` access on a stored event reference rather
than on the handler's own parameter.

---

## Anti-Pattern 4: No keyboard path

**What the LLM generates:** a complete, working pointer implementation and
nothing else.

**Why it happens:** the request is "drag and drop", drag is a pointer gesture,
and the model delivers the gesture. Accessibility is an adjacent requirement
that was not stated.

**Correct pattern:** a keyboard alternative is not optional — HTML5 drag events
do not fire on touch either, so the keyboard path serves mobile as well. Alt+Up /
Alt+Down to move, Home/End to jump, Escape to cancel, with focus following the
moved item. Roughly 30 lines.

**Detection hint:** no `onkeydown` in a template with `draggable="true"`.

---

## Anti-Pattern 5: `aria-grabbed` / `aria-dropeffect`

**What the LLM generates:**

```html
<li draggable="true" aria-grabbed={item.isDragging}>
```

**Why it happens:** these are the ARIA attributes *named for* drag and drop, so
they are the obvious answer, and older accessibility guidance recommends them.

**Correct pattern:** both are deprecated in ARIA 1.1 with inconsistent support.
Use an `aria-live` region announcing pick-up, each move (with position and
total), and cancellation. That is what screen-reader users actually receive.

**Detection hint:** either attribute anywhere.

---

## Anti-Pattern 6: A live region with no reset

**What the LLM generates:**

```javascript
this.announcement = `Moved to position ${index + 1}.`;
```

**Why it happens:** assigning the message is the complete implementation of
"announce it", and the requirement that the *text must change* to trigger an
announcement is a screen-reader behaviour rather than a DOM one.

**Correct pattern:** blank the region, then set on the next microtask. Two
consecutive moves producing identical text would otherwise announce once.

**Detection hint:** a direct assignment to a live-region property with no
intermediate reset.

---

## Anti-Pattern 7: Bare arrow keys for reorder

**What the LLM generates:** `if (event.key === 'ArrowUp') this.moveUp(id);`
with no modifier check, inside a `role="listbox"`.

**Why it happens:** arrows are the intuitive movement keys, and the conflict with
the role's navigation semantics requires knowing what `listbox` promises.

**Correct pattern:** Alt+Arrow to reorder, bare arrows to navigate. Binding bare
arrows removes the navigation the role advertises, which makes the component less
accessible than it was before the accessibility work started.

**Detection hint:** an arrow-key handler with no `altKey` / `shiftKey` /
`ctrlKey` guard in a component with a `listbox` or `grid` role.

---

## Anti-Pattern 8: Reaching for a drag library

**What the LLM generates:** `import Sortable from '@salesforce/resourceUrl/sortablejs'`
plus `loadScript` and initialisation in `renderedCallback`.

**Why it happens:** "use a battle-tested library" is correct advice in most web
contexts and is strongly represented. The model has no representation of shadow
DOM boundaries or the Lightning Web Security sandbox as things that change the
calculus.

**Correct pattern:** the native API is about 80 lines including keyboard support.
A library must contend with shadow DOM (global queries cannot reach into the
shadow tree), with LWS distortions, with owning the DOM that LWC also owns, and
with bundle weight — and most such libraries ship no keyboard path anyway, so the
accessibility work remains yours.

**Detection hint:** `loadScript` with a drag library in a component doing simple
list reordering.

---

## Anti-Pattern 9: Cleanup in `drop` only

**What the LLM generates:** the "is-dragging" class removed in the `drop`
handler, with no `dragend`.

**Why it happens:** drop is the successful completion, and cleanup naturally
attaches to completion. Abandoned drags — release outside a target, press
Escape — are an edge case the model does not enumerate.

**Correct pattern:** `dragend` fires on the source whether or not a drop
occurred, and is the only reliable cleanup hook. `drop` handles the data;
`dragend` handles the state.

**Detection hint:** no `ondragend` binding in a component that sets a dragging
class.

---

## Anti-Pattern 10: In-place array mutation

**What the LLM generates:**

```javascript
this.items.splice(fromIndex, 1);
this.items.splice(toIndex, 0, dragged);
```

**Why it happens:** it is the textbook array reorder and works in frameworks with
deep reactivity or explicit change detection.

**Correct pattern:** copy, mutate the copy, reassign. LWC reactivity triggers on
property assignment, not on mutation of the referenced object.

**Detection hint:** `splice`, `push`, or `sort` called directly on a reactive
property with no subsequent assignment.

---

## Anti-Pattern 11: A `div` drop zone with no file input

**What the LLM generates:** a styled `<div>` with drop handlers, presented as the
complete upload UI.

**Why it happens:** the request is "file drop zone" and a drop zone is a region.
The input element is not part of what was asked for.

**Correct pattern:** the drop zone enhances a real `<input type="file">` with a
visible label. A `div` is not focusable, not operable by keyboard, and carries no
semantics — an upload UI built from one is unusable without a mouse.

**Detection hint:** a file-drop component with no `<input type="file">`.

---

## Anti-Pattern 12: Client-side file validation described as security

**What the LLM generates:** size and MIME-type checks in the drop handler,
framed as preventing unwanted uploads.

**Why it happens:** the validation is genuinely useful and the code is correct.
The framing is what is wrong, and framing is not something a code sample carries.

**Correct pattern:** client-side checks are UX — they stop a doomed upload before
it starts. Everything in the browser is bypassable, so the server must
re-validate size, type, and content. State which one you are doing so the next
reader does not assume the server side exists.

**Detection hint:** validation code with no accompanying note that the server
must repeat it.
