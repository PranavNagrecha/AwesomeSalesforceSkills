# Well-Architected Notes — LWC GraphQL Wire

## Relevant Pillars

- **Performance** — One GraphQL query can replace several `getRecord` / `getListRecords` wires, which reduces round trips and lets the page share the LDS cache across components. The adapter also de-duplicates requests with identical query and variables shape, so stable variable identity is itself a performance concern.
- **Security** — The UI API GraphQL adapter enforces field-level security transparently: fields a user cannot access are returned as `null` rather than errored. That is a security win but a correctness risk — components must treat `null` defensively and should be exercised against least-privilege test users, not only admins. On `lightning/graphql` (v2), **optional fields** make this contract explicit: a field marked optional lets the query succeed even when the user lacks permission to see it, converting a possible query fault into a cleanly absent field the UI can branch on.
- **Reliability** — The adapter exposes a stable refresh contract. On `lightning/graphql` (v2) you call a `refresh` method on the emitted wire result; on `lightning/uiGraphQLApi` (v1) you call the standalone `refreshGraphQL(wiredResult)`. Paired with a disciplined "store the whole wired result" pattern, either gives a single, reliable handle to invalidate cached reads after writes or platform events. Reliability problems usually come from skipping that pattern, mixing the two modules' refresh calls, or using `refreshApex` by mistake. With v2 `executeMutation` writes, reliability also depends on honoring the refresh asymmetry — refresh after create/update, but not after delete (LDS removes deleted records automatically).

## Architectural Tradeoffs

The central tradeoff is chattiness versus query complexity. A single large query per screen is excellent for round-trip count and cache sharing, but the query grows tightly coupled to the UI, and any schema change ripples into one central place. Several small queries are easier to evolve independently but cost more requests and create independent refresh surfaces. Pick one query per screen when the fields fit comfortably; split when either the field list grows past what the UI renders or when different regions of the UI legitimately need different refresh cadences.

Cache granularity is another tradeoff. The adapter keys results by query + variables identity. Coarse variable shapes (one query serves many screens) maximize cache reuse but make the query harder to read; fine-grained, screen-specific queries are easier to reason about but share less. Memoize variables so identity only changes when values change, regardless of which approach you pick.

Finally, module choice is itself an architectural tradeoff. `lightning/graphql` (v2) is the recommended path and adds optional fields, dynamic queries, and `executeMutation` writes, but it does not currently support Mobile Offline; `lightning/uiGraphQLApi` (v1) is the reverse. A component destined for offline use is locked to v1 and its narrower feature set — decide the target runtime early, because retrofitting optional fields or GraphQL mutations onto a v1 component is a rewrite, not a tweak. On v2, writes can stay on the GraphQL/LDS path via `executeMutation` rather than being routed through a separate UI API or Apex bridge, which keeps the read and write models unified and preserves cache sharing.

## Anti-Patterns

1. **Embedding a `mutation {}` block in the wired query** — The *wire* is read-only on both modules; a mutation inside the wired `gql` query fails. On v2, writes are a separate `executeMutation` call (create/update/delete, no Apex); on v1, writes belong on `lightning/uiRecordApi` or imperative Apex. The anti-pattern is not "writing with GraphQL" (valid on v2) but conflating the write into the read query or hand-rolling an Apex bridge that loses cache sharing.
2. **Ignoring `displayValue` vs `value`** — Rendering `{record.Amount}` shows `[object Object]`; rendering `{record.Amount.value}` shows an unformatted number; rendering `{record.Amount.displayValue}` shows the locale-formatted currency. Mixing these produces inconsistent, hard-to-reproduce UI bugs, especially for dates and currencies.
3. **Building the variables object in the render path** — A getter that returns a fresh object literal on every access gives the adapter a new identity on every render, which defeats deduplication and causes cache thrash. Memoize the variables object so identity only changes when inputs change.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- GraphQL Wire Adapter Overview — https://developer.salesforce.com/docs/platform/lwc/guide/data-graphql.html
- GraphQL Wire Adapter Examples — https://developer.salesforce.com/docs/platform/lwc/guide/data-graphql-examples.html
- GraphQL Pagination — https://developer.salesforce.com/docs/platform/lwc/guide/data-graphql-pagination.html
- refreshGraphQL — https://developer.salesforce.com/docs/platform/lwc/guide/data-graphql-refresh.html
- lightning/uiGraphQLApi Module Reference — https://developer.salesforce.com/docs/component-library/bundle/lightning-graphql-api/documentation
- GraphQL API Module Comparison (v2 supersedes v1; Mobile Offline scope) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-graphql-api.html
- lightning/graphql Wire Adapter (v2) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-graphql-module.html
- GraphQL API for LWC (intro; v2 refresh method vs refreshGraphQL) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-graphql-intro.html
- GraphQL API for Lightning Web Components (GraphQL API guide) — https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc.html
- Winter '26 for Developers (lightning/graphql, optional fields, dynamic queries) — https://developer.salesforce.com/blogs/2025/09/winter26-developers
- GraphQL Mutations Now Available in LWC (executeMutation; create/update/delete; refresh asymmetry) — https://developer.salesforce.com/blogs/2026/05/graphql-mutations-now-available-in-lwc-create-update-and-delete-records
