---
name: lwc-slots-composition
description: "Use when a Lightning Web Component needs to let a parent inject markup into predefined regions using `<slot>` — default and named slots, `slotchange` wiring, fallback content, and detecting slot emptiness. NOT for rendering a dynamic component whose tag name is chosen at runtime — that is `lwc-dynamic-components` — and NOT for cross-component messaging via Lightning Message Service."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "how do i pass markup into a child lwc"
  - "lwc slot fallback content not rendering"
  - "named slot not receiving content in lwc"
  - "slotchange event not firing in my component"
  - "how to check if an lwc slot has content"
  - "child lwc needs the parent to inject a footer"
  - "multiple slots in one lwc template"
  - "::slotted css selector does not work in lwc"
tags:
  - lwc-slots-composition
  - slot
  - named-slots
  - composition
  - slotchange
  - shadow-dom
inputs:
  - "parent component markup intent — what regions the parent wants to fill"
  - "child API surface — which regions are content holes and which are data props"
  - "reusability goal — how many distinct parents will compose this child"
  - "rendering context — shadow DOM or light DOM child component"
outputs:
  - "slot structure plan — default vs named slots and their contracts"
  - "fallback strategy — what renders when a slot is empty"
  - "slotchange handlers that detect assignment and toggle wrapper state"
  - "review findings on slot naming, assignment placement, and styling scope"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC Slots Composition

Use this skill when you are designing a reusable Lightning Web Component whose internal structure is stable but whose content varies by caller — cards with custom headers and footers, modals with user-supplied bodies, list wrappers with injected row templates, or layout shells with optional toolbars. Slots are the right tool when the variation is *markup*, not data.

---

## Before Starting

Gather this context before writing slot markup:

- Is the variation markup that the parent owns, or is it structured data the child should render itself? Slots are for markup; data belongs on `@api` props or events.
- Is the child a shadow-DOM component (default) or a light-DOM component? Slot semantics and styling scope differ between the two.
- How many distinct regions does the parent need to fill? One content hole means a default slot; multiple distinct regions mean named slots.
- Does the child need to react when assigned content changes, or is first-render enough? Reactive cases need `slotchange` wiring.
- Who owns the styling of the slotted content — the parent or the child? Slotted content is styled by the parent's CSS because it lives in the parent's scope.

---

## Core Concepts

A small number of facts explain almost every real slot bug.

### Default Slots And Named Slots

A `<slot>` with no `name` attribute is the default slot. Any child element in the parent's markup that does not have a `slot="..."` attribute lands there. A `<slot name="header">` is a named slot, and only parent-supplied elements carrying `slot="header"` are assigned to it. A template is allowed one default slot and any number of named slots; multiple default slots in the same template is an error because assignment becomes ambiguous.

### Slot Assignment Lives In The Parent

Slot assignment is declared in the *parent's* markup, on the child elements passed to the custom element, not inside the child template. `<c-card><span slot="header">Hi</span></c-card>` is correct. Placing `slot="header"` on the child's own `<slot>` element is a common mistake — the attribute on `<slot>` does not mean "this slot receives the header"; slot naming is done with the `name` attribute.

### Fallback Content

Any markup nested inside `<slot>...</slot>` in the child template is fallback content. It renders when, and only when, no nodes are assigned to that slot. Fallback is perfect for default placeholders, empty states, and optional chrome. Whitespace-only assignment still counts as "assigned" for some cases, so do not rely on fallback to hide accidental blank lines.

### Detecting Whether A Slot Has Content

To conditionally render a wrapper only when a slot has real content, query the `<slot>` element with `lwc:ref` and call `assignedNodes()` (or `assignedElements({ flatten: true })`) in a `slotchange` handler. The `slotchange` event fires on initial render and every time the assigned nodes change, so toggle a reactive boolean from inside the handler rather than polling the DOM in `renderedCallback`.

### Shadow Boundary And Styling

Slot composition sits next to — but is not the same as — the shadow boundary. Slotted content is *projected* into the child's tree but stays in the parent's DOM scope for styling and event retargeting. That is why the parent's CSS styles the slotted elements and why `::slotted()` is not the LWC pattern inside shadow-DOM children. Light-DOM components render slots into the real DOM without a shadow root, so selectors behave as in plain HTML.

### Scoped Slots Are Light-DOM Only

`lwc:slot-data` (on the parent's slotted content) and `lwc:slot-bind` (on the child's `<slot>`) let a child pass iteration or computed data back up to the parent's template — scoped slots. They are limited to light DOM components today. Reach for them only when the child owns the iteration but the parent owns the per-row markup.

---

## Common Patterns

### Named-Slot Layout Shell

**When to use:** A reusable card, panel, or modal where the parent should supply a header, body, and footer independently.

**How it works:** The child template declares `<slot name="header">`, a default `<slot>` for the body, and `<slot name="footer">` with sensible fallback. The parent passes `<span slot="header">`, `<div slot="footer">`, and any remaining children default to the body.

**Why not the alternative:** Exposing three `@api` string properties forces the parent to stringify markup, loses accessibility semantics, and blocks nested components.

### Conditional Wrapper On Slot Emptiness

**When to use:** An optional toolbar or actions bar should collapse its container entirely when the parent passes nothing.

**How it works:** Give the child `<slot name="actions" lwc:ref="actionsSlot" onslotchange={handleSlotChange}></slot>`, wrap it in an element toggled by a reactive `hasActions` property, and set `hasActions = this.refs.actionsSlot.assignedNodes().length > 0` inside the handler.

**Why not the alternative:** Polling in `renderedCallback` runs on every render tick and misses the signal; `@api hasActions` pushes boilerplate onto every caller.

### Composition Over `@api innerHTML`

**When to use:** A parent would otherwise inject a chunk of markup via a string or `lwc:dom="manual"`.

**How it works:** Replace the string prop with a `<slot>` and have the parent place real LWC elements inside the custom element tag. Nested components, scoped CSS, and event bubbling all keep working.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Child needs one content hole | Default `<slot>` with fallback content | Simplest contract; parents pass children directly |
| Child needs multiple distinct regions | Named slots (`<slot name="header">`) | Disambiguates assignment and lets parents fill regions independently |
| Wrapper must collapse when slot is empty | `slotchange` + `assignedNodes()` via `lwc:ref` | Reactive, event-driven, survives dynamic content |
| Parent needs to pass structured data, not markup | `@api` property or public method | Slots are for markup; data on props preserves type safety |
| Child owns the iteration, parent owns the row markup | Scoped slots with `lwc:slot-data` / `lwc:slot-bind` in a light-DOM child | Only primitive for passing per-iteration bindings into parent markup |
| Parent needs to respond to child state changes | Events dispatched by the child | Slots project downward; events flow upward |

---

## Recommended Workflow

1. Identify whether the variation the parent needs is markup or data. If it is data, stop and use `@api`.
2. Count the distinct regions. One region means a default slot; multiple regions mean named slots with explicit names.
3. Author fallback content for every optional slot so the component looks finished when composed empty.
4. If a wrapper must hide when a slot is empty, wire `lwc:ref` + `onslotchange` and flip a reactive boolean inside the handler.
5. Validate that slot-assigned markup is being styled from the parent's CSS, not attempted via `::slotted()` in the child's shadow-DOM stylesheet. Run `scripts/check_lwc_slots_composition.py --manifest-dir <path>`.

---

## Review Checklist

- [ ] Every `<slot>` with more than one sibling slot has a `name` attribute.
- [ ] There is at most one default (unnamed) slot per template.
- [ ] Slot assignment uses the `slot="..."` attribute on child elements *inside the parent's custom-element tag*, not on the child's own `<slot>`.
- [ ] Optional slots have fallback content, and the fallback matches the final look-and-feel.
- [ ] Any wrapper that must collapse on empty slots has a `slotchange` handler that reads `assignedNodes()` via `lwc:ref`.
- [ ] No `::slotted()` selectors exist in a shadow-DOM child's CSS; slotted styling lives in the parent.
- [ ] Scoped slots (`lwc:slot-data`, `lwc:slot-bind`) appear only in light-DOM components.

---

## Salesforce-Specific Gotchas

1. **Named-slot fallback renders only when assignment is empty** — passing a whitespace-only text node can still count as assignment and suppress fallback. Inspect `assignedNodes()` in devtools if fallback "mysteriously" disappears.
2. **`slot="..."` belongs on the parent's children, not the child's `<slot>`** — writing `<slot slot="header">` inside the child template is a silent no-op; use `<slot name="header">`.
3. **Slotted content is in the parent's style scope** — the child's component CSS cannot reach it and `::slotted()` is not supported in LWC shadow DOM. Style the slotted markup from the parent.
4. **`slotchange` fires more often than you expect** — it runs on initial render and on every subsequent assignment change, so expensive handlers need idempotence or a diff check against the last snapshot.
5. **Light DOM and shadow DOM slot differently** — in light DOM there is no shadow boundary, `::slotted()` is unnecessary, and scoped slots (`lwc:slot-data`/`lwc:slot-bind`) are available; in shadow DOM they are not.
6. **Slots do not transport primitive data** — trying to pass an object or number via a slot instead of an `@api` property is an API-design bug, not a slot bug.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Slot structure plan | Named + default slot inventory with fallback content and owner (parent vs child) |
| `slotchange` handler sketch | Reactive toggle pattern for wrapper collapse and empty-state UI |
| Checker report | File-level findings on multi-default slots, misplaced `slot="..."`, and `::slotted()` in shadow-DOM CSS |

---

## Related Skills

- `lwc/component-communication` — use when the parent needs to pass structured data or receive events from the child instead of injecting markup.
- `lwc/lwc-dynamic-components` — use when the child's *tag name* is chosen at runtime, not when the child has fixed markup with content holes.
- `lwc/lwc-light-dom` — use when slot styling, scoped slots, or third-party CSS selectors require light-DOM rendering instead of shadow DOM.
