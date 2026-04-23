# Well-Architected Notes — LWC GraphQL Wire

## Relevant Pillars

- **Performance** — One GraphQL query can replace several `getRecord` / `getListRecords` wires, which reduces round trips and lets the page share the LDS cache across components. The adapter also de-duplicates requests with identical query and variables shape, so stable variable identity is itself a performance concern.
- **Security** — The UI API GraphQL adapter enforces field-level security transparently: fields a user cannot access are returned as `null` rather than errored. That is a security win but a correctness risk — components must treat `null` defensively and should be exercised against least-privilege test users, not only admins.
- **Reliability** — The adapter exposes a stable refresh contract through `refreshGraphQL(wiredResult)`. Paired with a disciplined "store the whole wired result" pattern, this gives a single, reliable handle to invalidate cached reads after imperative writes or platform events. Reliability problems usually come from skipping that pattern or using `refreshApex` by mistake.

## Architectural Tradeoffs

The central tradeoff is chattiness versus query complexity. A single large query per screen is excellent for round-trip count and cache sharing, but the query grows tightly coupled to the UI, and any schema change ripples into one central place. Several small queries are easier to evolve independently but cost more requests and create independent refresh surfaces. Pick one query per screen when the fields fit comfortably; split when either the field list grows past what the UI renders or when different regions of the UI legitimately need different refresh cadences.

Cache granularity is another tradeoff. The adapter keys results by query + variables identity. Coarse variable shapes (one query serves many screens) maximize cache reuse but make the query harder to read; fine-grained, screen-specific queries are easier to reason about but share less. Memoize variables so identity only changes when values change, regardless of which approach you pick.

Finally, GraphQL is read-only on the platform. Any architecture that pretends otherwise — routing writes through a "GraphQL-like" Apex wrapper, for instance — either duplicates the UI API write path or loses the cache-sharing benefit the adapter exists to provide.

## Anti-Patterns

1. **Using GraphQL wire for writes** — The adapter does not support `mutation`. Attempting to consolidate reads and writes into one adapter adds a failure mode and usually produces a hand-rolled Apex bridge that loses cache sharing. Writes belong on `lightning/uiRecordApi` or imperative Apex; GraphQL is the read path.
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
