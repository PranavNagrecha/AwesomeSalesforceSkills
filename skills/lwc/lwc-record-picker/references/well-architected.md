# Well-Architected Notes — LWC Record Picker

## Relevant Pillars

Record selection is a UX primitive, but the architectural weight
comes from how the platform's base component enforces accessibility,
typeahead performance, and operational consistency that custom
combobox-plus-SOQL implementations almost always fail. Three pillars
carry real weight; the dominant one is Accessibility because the
default focus management, ARIA wiring, and keyboard navigation are
the difference between "passes WCAG 2.1 AA" and "fails the first
audit."

- **Accessibility (a sub-concern of Reliability + User Experience)** —
  `lightning-record-picker` ships with focus-trap behavior, keyboard
  navigation (Down/Up to walk options, Enter to select, Esc to
  dismiss), `aria-activedescendant` wiring, and a `required` /
  `reportValidity()` / `setCustomValidity()` validation triad that
  reads correctly to NVDA and VoiceOver. The `label` attribute is
  required and becomes the accessible name. Hand-rolled combobox
  patterns either miss focus-trap, omit `aria-activedescendant`, or
  expose a `<input>` + `<ul>` pair that screen readers announce as
  two unrelated controls. The accessibility audit (axe, Lighthouse,
  Salesforce Accessibility Audit) consistently flags custom lookups
  and consistently passes the base component.
- **Reliability** — The picker uses the GraphQL wire adapter under
  the hood, which leverages the SOSL search index for typeahead
  rather than SOQL LIKE scans. SOSL is cap-free against record
  volume and routinely returns results in <200ms even against
  multi-million-record orgs; SOQL LIKE on unindexed Name fields
  times out at scale. The picker also dispatches an `error` event
  when the underlying query fails (filter parse errors, FLS denial,
  network failures) — letting the parent surface a meaningful toast
  rather than the empty-dropdown silent-failure mode hand-rolled
  lookups produce.
- **Operational Excellence (via UX consistency)** — Every record
  lookup on a Lightning page should look and behave identically:
  same entity icon, same recent-items list, same typeahead delay,
  same keyboard contract, same chip rendering on selection. Teams
  that build custom lookups in three different LWCs end up with
  three different UX patterns — sometimes the icon is the wrong
  color, sometimes the recent-items list is missing, sometimes the
  X-to-clear is in a different corner. The base component gives the
  org one UX contract to QA, one place to fix accessibility
  regressions, and free improvements from Salesforce's seasonal
  releases (e.g., Spring '25 brought the picker into design-time
  parity with the `lightning-input-field` lookup variant — every
  consumer got that for free).

## Architectural Tradeoffs

The defining tradeoff is **which record-selection primitive to use**,
since Salesforce ships five different ways to let a user pick a
single record and the right choice depends on context:

| Dimension | `lightning-record-picker` | `lightning-combobox` + Apex SOQL | `lightning-input-field` (record form lookup) | Custom `lightning-datatable` + modal selection | Aura `force:lookup` / legacy `lightning:select` |
|---|---|---|---|---|---|
| Surface | LX, Mobile, Aura Exp Sites | Anywhere LWC runs | Inside `lightning-record-edit-form` only | Anywhere LWC runs | Aura-host pages only |
| Search backend | GraphQL + SOSL index | Apex SOQL (you write it) | UI API lookup config | Apex SOQL (you write it) | Aura lookup service |
| Recent-items | Yes, automatic | No (build it) | Yes, automatic | No (build it) | Yes, automatic |
| Filter shape | UI API filter JSON | SOQL (whatever you compose) | Lookup filter metadata + dependent fields | SOQL | Aura lookup filter |
| Multi-record select | No | Yes (with combobox-multiple) | No | Yes (with row-selection) | No |
| Polymorphic target | One object at a time | Yes (compose at query time) | Yes (when field is polymorphic) | Yes | Yes |
| External Object support | No | Yes | No | Yes | No |
| Accessibility default | Built-in (passes WCAG) | Manual (rarely correct) | Built-in | Built-in (datatable) | Built-in |
| Best for | Standalone lookups on LX records pages | Multi-select, external objects, LWR sites | Lookups inside a record-edit form | Complex multi-record workflows | Aura-only pages awaiting migration |

The handoff rule that works in practice: **use `lightning-record-picker`
by default for any single-record lookup outside a record-edit form.
Use `lightning-input-field` when the lookup IS a field on the record
being edited and `lightning-record-form` / `lightning-record-edit-form`
manages the form state. Use a custom combobox-plus-SOQL pattern (see
`lwc-custom-lookup`) when the surface is an LWR Experience site,
when the target is an external object, when multi-select is
required, or when search needs to span 3+ fields. Use a
`lightning-datatable`-plus-modal when the selection workflow needs
filtering/sorting/pagination of the candidate list. Never use raw
Aura `force:lookup` in new work.**

A second tradeoff: **declarative filter (`filter` prop) vs reactive
recomputation**. The `filter` attribute accepts a static or reactive
object; making it reactive (a getter that depends on a tracked field)
re-triggers the picker's internal query whenever the dependency
changes. The cost: every dependency mutation causes a fresh GraphQL
round-trip. For high-frequency parent state changes (e.g., a date
picker that updates twice per second during scrubbing), debouncing
the dependency before it flows into the filter is mandatory — the
picker itself doesn't debounce filter changes the way it debounces
keystrokes.

A third tradeoff: **single picker with type selector vs multiple
narrowly-scoped pickers** for polymorphic lookups (Task `WhatId`,
Event `WhatId`, FeedItem `ParentId`). The single-picker-plus-radio
pattern (see `gotchas.md` Gotcha 5) keeps the form layout simple and
matches Salesforce's own UI for Activity creation. The
multiple-pickers pattern (one per concrete target object, with
conditional rendering) is harder to maintain but supports per-target
filters and matching-info that the single-picker pattern can't (you
can't conditionally swap `matching-info` per type without re-rendering
the whole picker). Default to the single-picker pattern; switch to
multiple pickers only when per-target filters diverge significantly.

## Anti-Patterns

1. **Hand-rolling a lookup with `lightning-input` + Apex SOQL when
   `lightning-record-picker` would fit.** Loses typeahead optimization,
   recent-items, accessibility focus management, the entity icon, and
   the typed `change` event. See `examples.md` anti-pattern.
2. **Passing the filter as a SOQL string.** The `filter` attribute
   expects the UI API filter JSON shape (`{ criteria: [{ fieldPath,
   operator, value }], filterLogic }`) — SOQL strings are silently
   ignored and the picker returns zero results with no error.
3. **Reading the change event from `event.target.value` instead of
   `event.detail.recordId`.** Returns `undefined` or stale prop value,
   not the freshly selected Id. See `gotchas.md` Gotcha 3.
4. **Configuring 3+ entries in `matching-info.additionalFields`
   expecting them all to match.** The platform enforces exactly one
   `primaryField` + one entry in `additionalFields`; extras are
   silently dropped. Build a concatenated helper field or fall back
   to a custom lookup when more breadth is genuinely needed.
5. **Deploying `lightning-record-picker` into an LWR Experience site
   without verifying compatibility.** The component is unsupported in
   LWR — it renders broken or not at all because LWR doesn't expose
   the LDS/UI-API services the picker depends on. For LWR, build a
   custom picker (or use a community-maintained equivalent) and gate
   the surface compatibility in `targets` metadata.

## Official Sources Used

- `lightning-record-picker` Component Library Reference:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-record-picker/documentation
- `lightning-record-picker` Component Library Examples:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-record-picker/example
- `lightning-record-picker` Lightning Component Reference:
  https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-record-picker.html
- LWC Data Guidelines:
  https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- LWC UI API Wire Adapters:
  https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- GraphQL API — Filter Field Operators:
  https://developer.salesforce.com/docs/platform/graphql/guide/filter-fields.html
- Introducing the Lightning Record Picker Component (Salesforce
  Developers Blog, Oct 2023):
  https://developer.salesforce.com/blogs/2023/10/introducing-the-lightning-record-picker-component
- LWC Recipes — `recordPickerHello` and `recordPickerDynamicTarget`
  reference implementations:
  https://github.com/trailheadapps/lwc-recipes
