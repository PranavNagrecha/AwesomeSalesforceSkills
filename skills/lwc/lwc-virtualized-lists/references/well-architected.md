# Well-Architected Notes — LWC Virtualized Lists

## Relevant Pillars

- **Operational Excellence** — Profile evidence is the difference
  between "we built a virtual list because it felt right" and "we
  built a virtual list because the 5,000-row case rendered in 4
  seconds at p95". Custom virtualization adds complexity (observer
  wiring, key stability, scrollbar geometry); pay that cost only
  with profile evidence justifying it.
- **Reliability** — IntersectionObserver lifecycle (connect on
  render, disconnect on unmount) is the source of memory leaks in
  LWC virtual lists. Pairing creation with disconnection is the
  highest-yield reliability item — easy to spot in review.

## Architectural Tradeoffs

- **`lightning-datatable` vs custom virtual list.** Datatable is
  the platform-native answer; custom is a maintenance surface the
  team owns forever. The break point is roughly 10K rows or
  non-tabular row layout. Below that, datatable + infinite-loading
  wins on every dimension except column-model flexibility.
- **Append-only virtualization vs true windowing.** Append-only is
  much simpler (no scrollbar geometry, no spacer divs) but the DOM
  grows with the dataset. True windowing keeps DOM constant but is
  3-5× more code and is a real source of bugs (scrollbar jumps, key
  instability, off-by-one slice math). Use append-only unless the
  total DOM size is a real ceiling.
- **OFFSET pagination vs cursor pagination.** OFFSET is one line of
  Apex; cursor pagination requires composite key handling
  (`LastModifiedDate + Id`). For virtual lists with frequent
  re-paginations, cursor wins; for occasional pages, OFFSET is
  simpler.
- **In-memory client filter vs server re-fetch on filter change.**
  In-memory is instant (no network round-trip) but caps at the JS
  heap budget. Server re-fetch scales but adds latency on every
  filter change. Pick based on the typical filter cardinality and
  the user's interaction pattern.

## Anti-Patterns

1. **Skipping `lightning-datatable` and going straight to a custom
   virtual list.** Most "I need a virtual list" requests resolve
   with datatable + infinite-loading.
2. **`new IntersectionObserver(cb)` with no `root` option in
   Lightning shadow DOM.** Default `root: null` doesn't fire
   reliably inside the shadow tree.
3. **Wiring the observer in `connectedCallback` instead of
   `renderedCallback`.** Sentinel is null at connect time; observer
   silently no-ops.
4. **Computed / unstable `key={...}` on for-each items.** LWC tears
   down and rebuilds row components on every re-render; the per-row
   work multiplies.
5. **OFFSET-based pagination on long virtual lists.** Predicate
   re-evaluation cost grows linearly with offset.
6. **Observer creation without matching `disconnectedCallback`
   teardown.** Memory leak on every component unmount.

## Official Sources Used

- Improve Datatable Performance (LWC) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html
- LWC Performance Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- LWC Wire Service Reference — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- IntersectionObserver MDN — https://developer.mozilla.org/en-US/docs/Web/API/IntersectionObserver
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
