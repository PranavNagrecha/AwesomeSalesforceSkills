# Template — LWC Component Events Catalog

Use this template to document the events a Lightning Web Component **dispatches** and **listens for**. Drop it into the component folder as `events.md` (or paste the relevant section into the component README). Every component that fires more than one event should have one of these.

The catalog is the single source of truth for the dispatch contract. Reviewers, downstream component authors, and AI assistants should be able to answer "what events does this component emit, what is in the payload, and who is supposed to listen?" without reading the source.

---

## Component Identity

| Field | Value |
|---|---|
| Component name | `c-<component-name>` |
| Folder | `force-app/main/default/lwc/<componentName>/` |
| Owner | `<team or person>` |
| Last reviewed | `<YYYY-MM-DD>` |

---

## Events Dispatched

One row per event the component **fires** via `dispatchEvent(new CustomEvent(...))`.

| Event name | When dispatched | `bubbles` | `composed` | `cancelable` | Detail payload (shape) | Intended listener | Notes |
|---|---|---|---|---|---|---|---|
| `rowselect` | User clicks a row in the list | `false` | `false` | `false` | `{ recordId: string }` | Direct parent (`c-row-list`) | Same shadow tree; defaults are correct |
| `recordsavefailure` | Save call rejects | `true` | `true` | `false` | `{ recordId: string, errorMessage: string }` | Aura host (`MyApp.cmp`) | `composed: true` because Aura is across a shadow boundary |
| `beforeclose` | User clicks the close button | `false` | `false` | `true` | `{ reason: 'user-clicked-x' \| 'esc-key' }` | Direct parent | Cancelable; dispatcher checks `defaultPrevented` after dispatch |

### Detail payload shape rules

- Document every field, type, and optionality.
- Mark mutable fields (arrays, nested objects) with **(snapshot)** to indicate the dispatcher freezes / clones them.
- IDs and primitives only when possible — never send a full SObject record up the tree.

### Naming check

- [ ] Every event name above is **single lowercase token** — no hyphens, no `on` prefix, no camelCase.
- [ ] Every name is a verb or verb phrase concatenated as one word (`rowclick`, `recordsavefailure`).

### Flag-combination check

- [ ] Every event whose listener lives outside this component's shadow root has `composed: true`.
- [ ] Every event used for ancestor signalling has `bubbles: true`.
- [ ] Every cancelable event has a documented `if (event.defaultPrevented) return;` path on the dispatcher side.

---

## Events Listened For

One row per event the component **handles** via `on<eventname>` template attribute or `addEventListener`.

| Event name | Source component | Wiring style | Handler method | Notes |
|---|---|---|---|---|
| `rowselect` | `c-row-item` (children) | `onrowselect={handleRowSelect}` | `handleRowSelect(event)` | Reads `event.detail.recordId` |
| `formconfirm` | slotted content (`c-confirmation-form`) | `onformconfirm={handleFormConfirm}` on the slot wrapper | `handleFormConfirm(event)` | Slotted content must dispatch with `composed: true` |

### Listener defensive-read check

- [ ] Handlers read `event.currentTarget` (not `event.target`) for `dataset` / DOM access.
- [ ] Handlers treat `event.detail` as read-only — no `.push`, `.splice`, or property assignment on it.
- [ ] No handler is doing work that re-dispatches the same event without a re-entrancy guard.

---

## Cross-Boundary Notes

If the component is **slotted** into another component, or **wrapped in Aura**, list the boundaries here:

- [ ] Aura host: `<MyApp.cmp>` listens for `recordsavefailure` — requires `composed: true`.
- [ ] Slot host: `<c-modal>` listens for `formconfirm` from slotted content — requires `composed: true`.

---

## Lightning Message Service Channels

If this component publishes or subscribes to LMS, list the channels here (LMS replaces CustomEvent for cross-region traffic):

| Channel | Direction | When |
|---|---|---|
| `Cart_Updated__c` | publish | After cart mutation |
| `Inventory_Updated__c` | subscribe | To refresh stock counts |

---

## Verification

Before merging changes that touch this component's events:

- [ ] All rows in **Events Dispatched** correspond to a real `dispatchEvent` call in the source.
- [ ] All rows in **Events Listened For** correspond to a real handler.
- [ ] No event name violates the lowercase-single-word rule.
- [ ] No detail payload field is mutated by the dispatcher after dispatch (immutable / frozen / cloned).
- [ ] `python3 skills/lwc/lwc-custom-event-patterns/scripts/check_lwc_custom_event_patterns.py <component-folder>` exits 0.
