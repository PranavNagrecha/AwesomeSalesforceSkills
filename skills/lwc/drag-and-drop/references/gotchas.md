# Gotchas — LWC Drag and Drop

---

## 1. LWC has no event modifiers — `ondragover.prevent` is silently ignored

**What happens:** the template declares `ondragover.prevent`. Nothing errors,
nothing warns, and `drop` never fires. The developer concludes drag and drop
does not work in LWC.

**Why:** `.prevent` is a Vue modifier. Angular has `(dragover)="$event.preventDefault()"`.
LWC has neither — every handler is a plain method and cancellation is explicit.

**How to avoid:**

```javascript
handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
}
```

This is the most common cause of "drag and drop doesn't work" in LWC, and its
signature is the total absence of any diagnostic.

---

## 2. Without `preventDefault` on `dragover`, `drop` never fires — by design

**What happens:** `dragstart` fires, `dragenter` fires, `dragover` fires
continuously, and `drop` never does.

**Why:** the HTML5 drag-and-drop model treats "do nothing" as "reject the drop".
Calling `preventDefault()` on `dragover` is how an element declares itself a
valid drop target. The naming is genuinely counterintuitive — you prevent the
default *rejection*.

**How to avoid:** `preventDefault()` on both `dragover` and `dragenter`, and a
Jest assertion that it was called. That test fails loudly on a bug whose only
other symptom is silence.

---

## 3. `dataTransfer` is only valid during the event

**What happens:** the handler stores the event and reads
`this.savedEvent.dataTransfer.getData('text/plain')` later. It returns an empty
string.

**Why:** `dataTransfer` is writable only during `dragstart` and readable only
during `drop`. Outside those windows it is in a protected mode where reads yield
nothing. This is a spec-level privacy protection, not a browser quirk.

**How to avoid:** `setData` synchronously in `dragstart`, `getData`
synchronously in `drop`. If you need the value elsewhere, mirror it into a
component field at the same time — but never rely on reading it back out of the
stashed event.

---

## 4. `dragleave` fires when entering a child element

**What happens:** the drop-target highlight flickers as the pointer crosses text
or an icon inside the zone, and sometimes clears while the pointer is still
inside.

**Why:** `dragenter` and `dragleave` fire per element, including descendants.
Moving from the zone onto its own `<span>` fires `dragleave` on the zone.

**How to avoid:** either counting, or a `relatedTarget` containment check.

```javascript
// Counting — robust and simple.
handleDragEnter() { this._depth += 1; this.isOver = true; }
handleDragLeave() { this._depth -= 1; if (this._depth <= 0) { this._depth = 0; this.isOver = false; } }

// Containment — fine for a single-level target.
handleDragLeave(event) {
    if (event.currentTarget.contains(event.relatedTarget)) return;
    this.isOver = false;
}
```

Reset the counter in `drop` and `dragend`, or an abandoned drag leaves it
non-zero and the highlight sticks.

---

## 5. Cleaning up in `drop` instead of `dragend` leaves stuck state

**What happens:** the user starts a drag and releases outside any valid target.
The "is-dragging" class stays applied until the page is reloaded.

**Why:** `drop` only fires on a successful drop. `dragend` fires on the source
element either way.

**How to avoid:** all visual cleanup goes in `dragend`. `drop` handles the data
transfer; `dragend` handles the state reset. They are different jobs and the
split is not optional.

---

## 6. Touch devices do not fire drag events

**What happens:** the feature works perfectly on desktop and does nothing on
tablets and phones. Nothing errors.

**Why:** HTML5 drag and drop is a mouse-oriented API. Touch produces
`touchstart`/`touchmove`/`touchend`, and browsers do not synthesise drag events
from them.

**How to avoid:** the keyboard path is already the accessibility requirement, and
an explicit "Move up / Move down" control satisfies both touch and keyboard at
once. Build one affordance that serves both rather than a pointer-events polyfill
that serves neither well:

```javascript
get isCoarsePointer() {
    return window.matchMedia('(pointer: coarse)').matches;
}
```

Render the explicit controls always, and treat drag as the enhancement. That
inversion — buttons first, drag second — is what makes the component work
everywhere.

---

## 7. `aria-grabbed` and `aria-dropeffect` are deprecated

**What happens:** an accessibility audit flags the implementation despite the
ARIA attributes being present and correct.

**Why:** both are deprecated in ARIA 1.1. Support was never consistent and
assistive technologies largely ignore them.

**How to avoid:** an `aria-live` region carrying explicit announcements — pick
up, move (with position and total), and cancel. That is what screen-reader users
actually hear.

---

## 8. A live region does not re-announce identical text

**What happens:** the user moves an item down twice. The first move is
announced. The second is silent.

**Why:** `aria-live` fires on text *change*. Setting the same string is not a
change.

**How to avoid:** blank the region, then set it on the next microtask.

```javascript
announce(text) {
    this.announcement = '';
    Promise.resolve().then(() => { this.announcement = text; });
}
```

Include the position and the total in every announcement — "moved down" alone
does not orient a user who cannot see the list.

---

## 9. Binding bare arrow keys breaks the role's navigation contract

**What happens:** in a `role="listbox"`, arrow keys are bound to reorder.
Keyboard users can no longer move between options, and the component is less
accessible than before the accessibility work.

**How to avoid:** a modifier. Alt+Arrow for reorder, bare arrows for navigation.
This is the convention users already know from other reorderable lists, and it
preserves the semantics that `role="listbox"` promises.

Handle Escape too — a keyboard drag with no cancel is a trap.

---

## 10. Mutating the array in place produces no re-render

**What happens:** `this.items.splice(from, 1)` runs, the array is correct in the
debugger, and the DOM does not change.

**Why:** LWC reactivity triggers on property assignment. Deep mutation of an
array's contents is not observed.

**How to avoid:** copy, mutate the copy, reassign.

```javascript
const next = [...this.order];
next.splice(from, 1);
next.splice(to, 0, id);
this.order = next;      // <- the assignment is what re-renders
```

Reordering by *id array* rather than by record array is worth adopting on its
own: it keeps the record data immutable, makes the reorder a pure list
operation, and makes the emitted `detail` a clean `[id, id, id]` payload.

---

## 11. Third-party drag libraries fight shadow DOM and Lightning Web Security

**What happens:** SortableJS is loaded as a static resource and initialised in
`renderedCallback`. It finds no elements, or initialises and then behaves
erratically.

**Why, in two layers:**

- **Shadow DOM.** Code cannot use `document` or `document.body` to reach into a
  component's shadow tree; `document.querySelector()` cannot select nodes inside
  it ([Shadow
  DOM](https://developer.salesforce.com/docs/platform/lwc/guide/create-dom.html)).
  Libraries that query globally find nothing.
- **Lightning Web Security.** Components run in a JavaScript sandbox with
  distortions applied to browser APIs — storage is namespaced, HTML on shared DOM
  elements is sanitised, and a small number of APIs are blocked. Library
  behaviour that depends on manipulating globals is sandboxed to your namespace.
  The [LWS Distortion
  Viewer](https://developer.salesforce.com/tools/lws-distortion-viewer) is the
  live source of truth for any specific API's behaviour, and distortions can
  change between releases.

**How to avoid:** use the native API — it is roughly 80 lines including the
keyboard path. If a library is genuinely necessary (nested trees, cross-window
drag), wrap it in one component, consider light DOM deliberately with its
encapsulation tradeoff understood, verify against the Distortion Viewer, and
test in a real org rather than only in Jest. Jest does not run LWS.

---

## 12. jsdom implements drag events but not `DataTransfer`

**What happens:** a Jest test dispatches `dragstart` and the handler throws on
`event.dataTransfer.setData`.

**How to avoid:** stub it. The component only uses `setData`, `getData`,
`effectAllowed`, and `dropEffect`:

```javascript
function dataTransferStub() {
    const store = {};
    return {
        setData: (t, v) => { store[t] = String(v); },
        getData: (t) => store[t] ?? '',
        effectAllowed: '',
        dropEffect: ''
    };
}
```

Attach it to a `CustomEvent` and dispatch. Also mock `preventDefault` with
`jest.fn()` so you can assert it was called — that assertion is the one that
catches gotcha 1.

---

## 13. A `div` drop zone that replaces the file input is unusable

**What happens:** the file upload UI is a styled `div` with drop handlers and no
`<input type="file">`. Keyboard users cannot upload anything.

**Why:** a `div` is not focusable, not operable, and carries no semantics. The
drop zone is an *enhancement* over the input, never a replacement.

**How to avoid:** keep a real `<input type="file">` with a visible `<label>`, and
layer drop handlers on the surrounding element. Also reset `input.value = null`
after processing, or selecting the same file twice fires no `change` event.

---

## 14. A folder drop yields zero files, and looks like a broken component

**What happens:** a user drags a folder. `dataTransfer.files` is empty. The
component does nothing and appears broken.

**How to avoid:** treat an empty file list as a distinct case with its own
message — "Folders can't be uploaded; drop individual files" — rather than
falling through to the no-op path. Users drag folders often enough that the
silent case is worth spending a branch on.

Also validate size and type client-side for fast feedback while treating it as
UX only. Anything reachable from a browser is bypassable; the server must
re-validate.
