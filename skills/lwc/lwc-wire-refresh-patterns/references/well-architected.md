# Well-Architected Notes — LWC Wire Refresh Patterns

## Relevant Pillars

Wire refresh is a tactical concern with strategic blast radius — it
touches the user-perceived freshness of data, the bandwidth cost of
record pages, and the maintainability of cross-component coordination.
Three pillars matter; the others (Security, Scalability of backend
load) are downstream effects.

- **Performance** — Each refresh primitive has a different
  network cost profile. `refreshApex` issues one targeted call to
  the wired Apex method. `notifyRecordUpdateAvailable` invalidates
  one or more record-level cache entries and triggers one re-fetch
  per affected component. `RefreshEvent` is broadcast — every
  refresh-aware component in the view fires its own re-fetches.
  Picking the wrong primitive can multiply network volume by 10×
  on a busy record page.
- **Reliability** — Stale data on record pages is a top driver of
  "the system is wrong" support tickets. The refresh pattern an LWC
  uses determines whether the user sees correct values after a save.
  Components that ship without an explicit refresh strategy
  ship with a known reliability gap.
- **Operational Excellence** — Refresh ownership (which component
  triggers which refresh) is invisible in static code but visible
  in production support. A team that documents the refresh chain
  ("Save → updateRecord → RefreshEvent → these 4 components
  re-fetch") can debug a stale-data report in minutes; a team that
  doesn't faces a multi-hour reverse-engineering session.

## Architectural Tradeoffs

The primary tradeoff is **scope vs. precision** of the refresh
signal:

| Scope | Primitive | Pros | Cons |
|---|---|---|---|
| Single wire | `refreshApex` | Cheapest network. Exact. | Only works for custom Apex wires; same component. |
| Specific record(s) | `notifyRecordUpdateAvailable` | Targeted, multi-component. | UI API wires only; doesn't refresh related-list adapters. |
| Whole view | `RefreshEvent` | Catches every component. Works for unknown side effects. | Highest network cost. No way to opt out per component. |
| Reactive parameter | Reassign `$param` | Native LWC reactivity. No imperative call. | Only fits param-driven context changes. |

A secondary tradeoff is **refresh ownership at the boundary vs.
distributed**:

- **Boundary ownership.** A single coordinator component (the
  record page tab host, or a "save controller" LWC) handles all
  refresh signaling. Other components stay refresh-naive — they
  just emit save-completed events. Pros: single place to debug,
  consistent UX. Cons: more wiring; the coordinator becomes a
  god-component.
- **Distributed ownership.** Every component that saves data is
  also responsible for its own refresh signaling. Pros: components
  are self-contained. Cons: scope decisions get re-litigated
  per component; users see inconsistent refresh behavior across
  the same page.

The right call depends on the size of the LWC suite and the
team's capacity for governance. Smaller suites (≤5 LWCs per page)
do better with distributed ownership; larger suites (10+ on a
record page) almost always need a boundary coordinator.

A third tradeoff: **wire vs. imperative for fresh-data
requirements**. If a piece of data must always be fresh on every
visit (e.g., financial balances, current quote prices), don't
fight the wire cache — switch to an imperative `@AuraEnabled`
(not `cacheable=true`) Apex call invoked from `connectedCallback`.
Wires are great for read-mostly data that benefits from client-side
caching; they fight you when freshness is critical (see
`gotchas.md` § 4).

## Anti-Patterns

1. **Param-nulling hack to force wire re-run.** Brittle, depends on
   reactivity-engine internals, often a silent no-op. See
   `examples.md` anti-pattern.
2. **Storing only the destructured `data` instead of the raw wire
   result.** Breaks `refreshApex` because the cache identity lives
   on the wire result envelope, not the data array. Always use the
   function-form `@wire` if you intend to refresh.
3. **Calling `refreshApex` from `connectedCallback` before the wire
   has emitted.** No-op at best, warning at worst. See
   `gotchas.md` § 3.
4. **Using `RefreshEvent` for high-frequency triggers** (keystroke,
   slider drag). Multiplies network volume across the entire
   record page. Drive the specific wire with a reactive parameter
   instead.
5. **`getRecordNotifyChange` in new code.** Deprecated; use the
   `RefreshEvent` API (`lightning/refresh`) or
   `notifyRecordUpdateAvailable` from `lightning/uiRecordApi`
   depending on scope.

## Official Sources Used

- LWC Reference — `lightning/refresh` (`RefreshEvent`, `RefreshView`):
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-refresh.html
- LWC Reference — `lightning/uiRecordApi` (`notifyRecordUpdateAvailable`):
  https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-ui-api-record.html
- LWC Guide — Refresh Cached Data:
  https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-refresh.html
- Apex Developer Guide — `@AuraEnabled(cacheable=true)`:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_AuraEnabled.htm
- Salesforce Well-Architected — Adaptable (Resilient):
  https://architect.salesforce.com/well-architected/adaptable/resilient
