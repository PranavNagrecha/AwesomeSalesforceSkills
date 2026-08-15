# LWC Focus Map

One of these per component that moves focus. Fill it before writing the focus
code — the rows you cannot complete are the transitions that will strand a
keyboard user.

Companion checker: `scripts/check_lwc_focus_management.py --src-dir <lwc dir>`.

## Component

- Bundle name:
- Role (modal / wizard / list / form / disclosure / widget):
- Trap decision:
  - [ ] `lightning/modal` — nothing to hand-roll
  - [ ] Hand-rolled, because this surface is not a modal. Reason:

## State Transitions Requiring Focus

One row per transition. "Restoration target" is where focus goes when the state
ends — a blank cell is a bug, not a blank cell.

| Transition | Focus target | Restoration target | Announcement (role) | Implemented in |
|---|---|---|---|---|
| Open overlay | first interactive element in body | opener's trigger button | dialog accessible name | |
| Close overlay | opener's trigger button | n/a | n/a | opener, not the overlay |
| Cancel / Escape | opener's trigger button | n/a | n/a | |
| Validation failure | error summary, `tabindex="-1"` | n/a | `role="alert"` | |
| Error-link click | the named field | n/a | n/a | |
| Async load complete | **no move** unless the focused element was replaced | n/a | `role="status"` | |
| Async load failed | error region | n/a | `role="alert"` | |
| Row added | the new row's first control | n/a | `role="status"` | |
| Row removed | next row → previous row → list heading | n/a | `role="status"` | |
| Wizard step forward | new step heading, `tabindex="-1"` | n/a | `role="status"` | |
| Wizard step back | previous step heading | n/a | `role="status"` | |
| List emptied | list heading, `tabindex="-1"` | n/a | `role="status"` | |

Add a row for every remaining transition this component has. Delete rows that do
not apply — but delete them deliberately, not because they were hard to fill in.

## Shadow DOM Boundaries

- Children this component focuses, and how each is made focusable:

| Child component | `delegatesFocus` | `@api focus()` | Notes |
|---|---|---|---|
| | | | |

- Targets addressed by `lwc:ref` (must not be inside `for:each`):
- Targets addressed by `data-*` + `this.template.querySelector` (dynamic rows):
- [ ] No `document.querySelector` anywhere in the bundle
- [ ] No `document.activeElement` — comparisons use `this.template.activeElement`
- [ ] No `.shadowRoot.` traversal into a child component

## Timing

- [ ] No `.focus()` in `connectedCallback`
- [ ] Every `renderedCallback` focus is behind a non-reactive boolean flag
- [ ] No reactive state (`@track` / `@api`) assigned inside `renderedCallback`

## Trap Integrity (if hand-rolled)

- Focusable-element selector used (custom element tags, not `input`/`button`):
- [ ] `Escape` handled **before** the `Tab` logic
- [ ] Trap removed on close (subtree inside `lwc:if`, or listener explicitly torn down)
- [ ] `Shift+Tab` from the first element wraps to the last
- [ ] `Tab` from the last element wraps to the first
- [ ] Disabled and hidden controls excluded from the focusable list

## Live Regions

| Region | `role` | Politeness | Blank-then-set implemented? |
|---|---|---|---|
| | | | |

- [ ] `role="alert"` used only for things the user must resolve now
- [ ] Repeated identical messages still announce

## Keyboard Walk

- [ ] `Tab` reaches every interactive element, in visual order
- [ ] `Shift+Tab` reverses that order correctly
- [ ] Every trapping surface can be left with `Escape`
- [ ] No transition leaves focus on `<body>`
- [ ] Focus indicator is visible at every stop (WCAG 2.4.7)
- Browser used:
- Screen reader used:

## Tests

- [ ] One Jest test per transition row above
- [ ] Each asserts `shadowRoot.activeElement` **identity**, not a `focus` spy call
- [ ] One test asserts focus does NOT move on an unrelated re-render
- [ ] Manual keyboard walk recorded, with browser and screen reader named

## Sign-Off

- [ ] Every state transition has a focus target AND a restoration target
- [ ] Restoration is performed by the opener, on its own element
- [ ] Every trap has an exit (WCAG 2.1.2)
- [ ] `tabindex` values are only `0` or `-1`, and never alongside `delegatesFocus`
- [ ] Live regions announce, including on repeat
- [ ] Jest suite green AND manual walk completed
