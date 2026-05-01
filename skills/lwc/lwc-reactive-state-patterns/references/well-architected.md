# Well-Architected Notes — LWC Reactive State Patterns

## Relevant Pillars

- **Performance** — The reactivity pattern chosen drives render
  frequency. Reassignment-based updates with cached getters keep render
  cost predictable; in-place mutation with `@track` plus expensive
  uncached getters can recompute the same derived list on every
  unrelated re-render. The wrong pattern shows up as input lag and
  jank long before it shows up in profiling.
- **Operational Excellence** — Code that follows the post–Spring '20
  contract reads as the LWC team intended: reactive primitives are
  undecorated; `@track` is reserved for genuine deep observation.
  Reviewers can scan a component and tell at a glance which fields
  participate in reactivity and how. A codebase that decorates every
  field with `@track` loses that signal.

## Architectural Tradeoffs

- **Reassignment vs `@track`.** Reassignment is the modern default — it
  composes well, communicates intent, and avoids the Date/Set/Map
  trap. `@track` is the right escape hatch for deeply nested form
  state where readability is the primary constraint. Picking
  reassignment by default and `@track` by exception keeps the
  codebase grep-able for "where deep observation matters".
- **Reactive getters vs cached backing fields.** Getters in LWC do not
  memoize. For cheap derivations, getters are simpler. For expensive
  derivations (filtering, sorting, regex), cache via setter on the
  source field; the writes happen far less often than renders.
- **Component-local state vs Lightning Message Service.** Reactive
  class fields are the right shape for state owned by a single
  component subtree. Anything shared across DOM trees, across page
  navigations, or across an Aura host belongs in LMS or a shared
  module — not in synced reactive props between distant components.

## Anti-Patterns

1. **`@track` everywhere.** Decorating every reactive field "to be
   safe" is noise that hides genuine deep-observation requirements
   and gives the developer a false sense of security around
   Date/Set/Map. Drop `@track` from primitives and from fields
   updated via reassignment.
2. **Writing reactive fields in `renderedCallback` without a guard.**
   The infinite-loop trap. Always guard with `_hasRenderedOnce` or
   compare-then-set.
3. **Reaching for third-party state libraries before exhausting
   platform tools.** Custom events, shared ES modules, and LMS solve
   most cross-component cases. Adding Redux to an LWC bundle is a
   bundle-size and cognitive cost that should be the last resort.

## Official Sources Used

- LWC Reactivity for Fields, Objects, and Arrays — https://developer.salesforce.com/docs/platform/lwc/guide/reactivity-fields.html
- LWC Decorators Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-decorators.html
- LWC Lifecycle Hooks — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
