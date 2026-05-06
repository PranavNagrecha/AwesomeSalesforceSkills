# Gotchas — LWC Drag and Drop

Non-obvious HTML5 drag-and-drop behaviors that bite in LWC.

---

## Gotcha 1: `drop` does not fire without `preventDefault` in `dragover`

The single most common drag bug. Without
`event.preventDefault()` in the `ondragover` handler, the browser
treats the element as a non-drop-target and the `drop` event
never fires. The cursor shows the "no drop" icon throughout.

---

## Gotcha 2: `dataTransfer.getData` returns empty in `dragover`/`dragenter`

For security (preventing a target from inspecting a drag from a
different origin), `getData` returns an empty string in
`dragenter` and `dragover`. Only `drop` sees the real data. To
condition the hover state on the dragged item's type, stash a
flag in component state during `dragstart` instead.

---

## Gotcha 3: Firefox requires non-empty `dataTransfer.setData`

Some Firefox versions refuse to start the drag if `setData` is
not called or is called with empty data. Always call
`e.dataTransfer.setData('text/plain', stableId)` even if you also
set a custom MIME — `text/plain` works as the universal fallback.

---

## Gotcha 4: `dragend` fires whether or not the drop succeeded

User pressed Escape, dropped outside any zone, dropped on a
non-target — all fire `dragend` on the source. Use `dragend` to
reset visual state, not `drop`. `drop` fires only on success.

---

## Gotcha 5: `dragenter`/`dragleave` fire for child elements too

When the cursor moves from a column over a card *inside* that
column, `dragleave` fires on the column. The naive
`overColId = null` is wrong — the cursor is still over the
column, just over a child. Track entry depth or check
`relatedTarget` against the column's bounds before clearing.

---

## Gotcha 6: HTML5 drag has no built-in keyboard equivalent

ARIA `aria-grabbed` was deprecated. There is no native
keyboard-driven HTML5 drag. Keyboard users need a separate code
path (arrow keys, "Move to..." menu) — this is a hard WCAG
requirement, not optional polish.

---

## Gotcha 7: Touch devices have no drag-and-drop by default

Mobile Safari and Chrome on Android only fire drag events for
content the browser already considers draggable (text
selections, images). For your `draggable="true"` divs to work on
touch, you need a touch-aware library (Sortable.js, react-dnd
mobile backend) or polyfill. Mobile users see a static UI.

---

## Gotcha 8: LWC re-renders can interrupt the drag

If a parent component's reactive state changes during a drag
(say, a wire fires), the dragged element may be re-rendered as a
new DOM node. The drag continues on the *old* node, which is
now detached. Avoid wire-driven state changes during an active
drag — toggle a `isDragging` flag and gate updates.

---

## Gotcha 9: Custom MIME types are case-sensitive

`setData('Application/x-Card', ...)` and
`getData('application/x-card')` do not match. Browsers normalize
to lowercase but some inconsistency exists. Stick to lowercase
custom types and define the MIME constant once.
