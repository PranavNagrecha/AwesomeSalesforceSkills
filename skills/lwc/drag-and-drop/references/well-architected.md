# Well-Architected Notes — LWC Drag and Drop

## Relevant Pillars

### User Experience (Accessibility)

Drag is a **pointer gesture with no fallback**. HTML5 drag events do not fire on
touch, and they are unreachable by keyboard. A drag-only implementation is
therefore unusable by three distinct populations at once: keyboard users, screen
reader users, and every mobile and tablet user in the org.

That makes the keyboard path a functional requirement rather than a compliance
add-on, and it changes the build order. The correct sequence is:

1. **Explicit controls first** — Move up / Move down, or Alt+Arrow on a focusable
   row. These work everywhere.
2. **Announcements second** — an `aria-live` region carrying pick-up, each move
   with position *and* total, and cancellation. `aria-grabbed` and
   `aria-dropeffect` are deprecated and do not substitute.
3. **Drag last, as an enhancement** over a component that already works.

Built in that order, the component is correct on every device from the first
commit. Built drag-first, the keyboard path is retrofitted onto state machines
designed around pointer events, and it shows.

One semantic constraint worth internalising: inside `role="listbox"` or
`role="grid"`, bare arrow keys belong to navigation. Reorder must take a
modifier, or the accessibility work makes the component less accessible than it
was.

### Reliability

The HTML5 drag API has three properties that produce silent failures, and all
three are counterintuitive:

| Behaviour | Failure signature |
|---|---|
| `dragover` must call `preventDefault()` or the drop is rejected | Nothing happens; no error |
| `dataTransfer` is only valid during `dragstart` / `drop` | Empty string; no error |
| `dragleave` fires when entering descendants | Flickering highlight |

None of these throws. That means the Jest test asserting `preventDefault` was
called is not belt-and-braces — it is the only automated detector for the most
common defect in the domain.

`dragend` versus `drop` is the reliability distinction that decides whether
abandoned drags leave stuck state. `drop` fires only on success; `dragend` fires
either way. Data goes in `drop`, cleanup goes in `dragend`, and conflating them
guarantees a class stuck on an abandoned row.

### Security

Two boundaries matter here:

- **Client-side file validation is UX, not enforcement.** Size and type checks in
  the drop handler give fast feedback and are trivially bypassable. The server
  must re-validate. Say which one you are doing, so the next reader does not
  assume the other exists.
- **Lightning Web Security changes third-party library behaviour.** Components
  run in a JavaScript sandbox with distortions applied to browser APIs — storage
  namespaced per namespace, HTML on shared DOM elements sanitised, and a small
  set of escape-capable APIs blocked. A drag library that manipulates globals is
  sandboxed to your namespace, which is the intended protection and also the
  reason its documented behaviour may not be what you observe. The [LWS
  Distortion Viewer](https://developer.salesforce.com/tools/lws-distortion-viewer)
  is the live source of truth, and distortions change between releases.

### Performance

Reordering by **id array** rather than by record array is the structural choice
that keeps this cheap. The records stay immutable, the reorder is a pure list
operation on short strings, and the emitted event payload is a clean
`[id, id, id]` that a parent can persist without diffing objects.

`dragover` fires continuously — many times per second — so the handler must stay
trivial. `preventDefault()` and a `dropEffect` assignment, nothing else. Any
recomputation, DOM query, or state assignment in `dragover` runs at pointer
frequency; put target highlighting in `dragenter`/`dragleave`, which fire once
per boundary crossing.

For long lists, reordering interacts with virtualisation — a drop target may not
be rendered. See `lwc/virtualized-lists`; the practical answer is usually an
explicit "move to position" control rather than drag across a virtualised
viewport.

---

## Architectural Tradeoffs

### Native API vs. third-party library

| | Native HTML5 | SortableJS / Dragula / similar |
|---|---|---|
| Code | ~80 lines including keyboard | ~10 lines of init |
| Shadow DOM | Works natively | Global queries cannot reach the shadow tree |
| Lightning Web Security | No interaction | Sandbox distortions apply; verify in a real org |
| Bundle weight | Zero | Counts against the performance budget |
| Keyboard support | You build it | You build it anyway |
| Nested trees, cross-window | Hard | Solved |

The decisive row is the keyboard one: the library does not save the work you
most need done. Take native for lists, boards, and drop zones. Take a library for
nested trees and cross-window drag, wrap it in a single component, and test it in
an org rather than only in Jest — Jest does not run LWS.

### Shadow DOM vs. light DOM for library integration

Light DOM makes a library's global queries work and discards style encapsulation
and the isolation guarantee. It is a real option and a real cost. If a library is
the reason for the switch, confirm the library is the only viable path first —
see `lwc/lwc-shadow-vs-light-dom-decision`.

### Drag-only vs. explicit controls vs. both

Both is the answer, and the order matters. Explicit controls serve keyboard,
touch, and screen readers; drag serves pointer users who expect it. Shipping only
the explicit controls is an acceptable, honest v1. Shipping only drag is not
shippable.

### Optimistic reorder vs. persist-then-render

Optimistic reordering feels instant and requires a rollback path when the save
fails — and a rollback that silently reverts the user's action is worse than a
brief spinner. Persist-first is slower and always consistent. For a
low-latency single-record update, optimistic with a visible error and an explicit
revert announcement is the better experience; for a batch reorder that can
partially fail, persist-first avoids reconciliation logic that will be wrong.

### Announcement verbosity

Terse announcements ("moved up") are quick and disorienting. Verbose ones
("Renewal Task moved to position 2 of 8") take longer to hear and are the only
form that actually orients someone who cannot see the list. Take verbose, and
include the total — it is the number that makes the position meaningful.

---

## Anti-Patterns

1. **`ondragover.prevent`.** Vue syntax that LWC ignores silently. The drop never
   fires and nothing reports it.

2. **No `dragover` handler at all.** Same outcome, different cause — the browser
   rejects drops by default.

3. **Drag-only.** Excludes keyboard, screen reader, and all touch users
   simultaneously.

4. **`aria-grabbed` / `aria-dropeffect`.** Deprecated in ARIA 1.1 with
   inconsistent support; a live region is what is actually heard.

5. **Bare arrows for reorder inside a listbox.** Removes the navigation the role
   promises.

6. **Cleanup in `drop` only.** Abandoned drags leave stuck visual state.

7. **In-place array mutation.** No re-render; the data is right and the DOM is
   not.

8. **A `div` drop zone with no file input.** Unusable without a mouse.

---

## Hygiene

- Jest asserts `preventDefault` was called on `dragover` — the only automated
  detector for the domain's most common defect.
- Jest covers both interaction paths, and asserts announcement text contains the
  position and the total.
- Keyboard path built before drag, not after.
- `dragend` handles cleanup; `drop` handles data.
- Server re-validates every client-side file check.

---

## Related

- `lwc/lwc-accessibility-patterns` — live regions, roles, and focus management.
- `lwc/lwc-jest-testing-with-accessibility` — the test harness these examples
  assume.
- `lwc/lwc-custom-event-patterns` — the `reorder` event contract emitted upward.
- `lwc/lwc-locker-to-lws-migration` — what LWS changes for third-party libraries.
- `lwc/lwc-shadow-vs-light-dom-decision` — the tradeoff if a library forces light
  DOM.
- `lwc/virtualized-lists` — reordering inside a virtualised viewport.
- `templates/lwc/component-skeleton/` — the bundle shape these examples extend.
- `templates/lwc/jest.config.js` — canonical Jest configuration.

---

## Official Sources Used

- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/platform/lwc/guide/
- Access Elements the Component Owns (`lwc:ref`, `this.refs`) — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html
- Shadow DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-dom.html
- Light DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html
- How LWS Works — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-architecture.html
- LWS Distortion Viewer — https://developer.salesforce.com/tools/lws-distortion-viewer
- LWS Limitations — https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-limitations.html
- LWC Recipes — https://github.com/trailheadapps/lwc-recipes
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
