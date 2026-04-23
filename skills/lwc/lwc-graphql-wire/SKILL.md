---
name: lwc-graphql-wire
description: "Use when an LWC needs to read related records across multiple sObjects in one request, paginate a related list with cursors, or replace several overlapping `@wire(getRecord)` calls with a single shared-cache query. Triggers: 'read account and related contacts in one request', 'paginate a graphql wire', 'graphql wire not refreshing after apex mutation', 'too many @wire calls for related records', 'what fields does ui api graphql support'. NOT for single-record CRUD or write operations — the GraphQL wire adapter is read-only; use UI API (`updateRecord`, `createRecord`, `deleteRecord`) or imperative Apex for writes, and use `getRecord` when a single record with a known id is all you need."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "need to read account and related contacts in one request"
  - "how to paginate a graphql wire with cursors"
  - "graphql wire not refreshing after an imperative apex mutation"
  - "too many @wire(getRecord) calls for parent plus related list"
  - "what fields does ui api graphql support and how do i filter"
  - "why does my graphql field value come back as an object with value and displayValue"
  - "how do i pass a reactive variable into a gql template literal"
tags:
  - lwc-graphql-wire
  - graphql
  - ui-api
  - multi-entity-reads
  - cursor-pagination
  - refresh-graphql
  - reactive-variables
inputs:
  - "target sObjects and the relationship shape (parent-to-child, child-to-parent, polymorphic)"
  - "field selection the UI actually renders — not the full layout"
  - "pagination strategy: page size, starting cursor, and how 'load more' or filter changes reset state"
  - "filter and sort shape, including any reactive variables that change at runtime"
  - "refresh triggers — which imperative writes or platform events should invalidate the cache"
outputs:
  - "gql query template sized to the rendered UI with stable variable shape"
  - "cursor paginator pattern using `edges`, `node`, and `pageInfo.endCursor` / `hasNextPage`"
  - "refresh hook plan that calls `refreshGraphQL(this.wiredResult)` after mutations"
  - "review notes on cache sharing with LDS and FLS-trimmed field handling"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC GraphQL Wire

Use this skill when an LWC needs to read across more than one sObject or more than one related list in a single request, or when a component currently runs three or four overlapping `@wire(getRecord)` calls that could collapse into one cache-shared query. The GraphQL wire adapter (`lightning/uiGraphQLApi`) is a read-only data path that shares the Lightning Data Service cache, enforces field-level security, and returns a structured response shaped around the `uiapi` root, `edges`, and `node`.

---

## Before Starting

Gather this context before authoring the component:

- Which sObjects and relationships does the UI render, and which fields are actually displayed? GraphQL is a shape-matching tool — over-selection here negates the payload win.
- Is the component read-only, or does it also create/update/delete? GraphQL wire is read-only. Writes still go through UI API or imperative Apex.
- Is pagination needed, and if so, is a cursor-based model acceptable? The connection pattern exposes `pageInfo.endCursor` and `hasNextPage`; classic offset pagination is not the first-class model.
- What invalidates the view? A PE, a CDC event, an imperative Apex mutation — each implies a different refresh strategy built around `refreshGraphQL(this.wiredResult)`.

---

## Core Concepts

Three ideas carry most GraphQL-wire work: the adapter response shape, reactive variables, and the connection-based pagination model.

### Adapter Shape And The `uiapi` Root

Importing `{ gql, graphql }` from `lightning/uiGraphQLApi` and wiring `@wire(graphql, { query, variables, operationName })` gives you a provisioned result whose `data` is rooted at `uiapi`. Field scalar values are returned as `{ value, displayValue }` objects, not bare primitives, because Salesforce exposes both raw storage values and locale-formatted display values. Templates must render `{record.Name.value}` or `{record.Name.displayValue}`, not `{record.Name}`. The adapter shares the LDS cache: if another component has already fetched the same record and fields, this wire is a cache hit.

### Reactive Variables And The `gql` Template Literal

`gql` is a tagged template literal that parses the query at module load. String interpolation into the literal does not make the query reactive — it bakes a frozen value into the query text. Runtime variables must be declared in the `query` block (for example `query ($id: ID) { ... }`) and passed through the wire config as a plain object referenced with a leading `$` (for example `variables: '$vars'`). Rebuilding the variables object on every render creates a new identity and defeats cache dedup; stabilize it in a getter or derive it from tracked fields so identity only changes when a value actually changes.

### Connection Pagination Via `edges`, `node`, `pageInfo`

List queries return a connection: `edges { node { ... } cursor } pageInfo { endCursor hasNextPage startCursor hasPreviousPage }`. To implement "Load more", pass `first: N` and `after: $cursor` into the query and append new `node` values into a local array keyed by `Id.value`. The wire fires for each cursor change; accumulate rather than replace to preserve already-rendered rows. Offset pagination is not the adapter's native model — emulating it forces the adapter to discard cache benefits.

---

## Common Patterns

### Single-Query Replacement For Overlapping `getRecord` Calls

**When to use:** The component currently runs a parent `getRecord` plus one or more related-list or parent-of-parent wires, and the combined payload is still small enough to fit a single query.

**How it works:** Write one `gql` query that selects only the fields the UI renders, wire it once, and destructure in getters. The LDS cache still de-dupes parent-record access for other components on the page.

**Why not the alternative:** Multiple independent wires each have their own provisioning lifecycle, refresh hooks, and identity. They rerender independently, multiplying the surface area of cache-miss bugs.

### Cursor-Paginated "Load More"

**When to use:** The UI shows a related list that can grow beyond a reasonable first-paint size (typically >20 rows).

**How it works:** Track `cursor` as a reactive variable, bind it into `after: $cursor` in the query, and in the wire handler append `data.uiapi.query.<Entity>.edges` into a tracked array. Update `cursor` from `pageInfo.endCursor` only when the user clicks "Load more".

**Why not the alternative:** Replacing the accumulator on each wire fire causes list flicker and scroll-position loss. Treating `hasNextPage` as implicit from `edges.length` is unreliable because server-side filters may return a short page that is still not the last one.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single record, id already known, UI renders a handful of fields | `@wire(getRecord)` from `lightning/uiRecordApi` | Simpler config, full LDS cache hit, no query parsing cost |
| Parent record plus one or more related lists in the same UI | GraphQL wire with a single `gql` query | One round trip, shared cache, consistent refresh handle |
| Component needs to write (create/update/delete) | UI API (`createRecord`, `updateRecord`, `deleteRecord`) or imperative Apex | GraphQL wire is read-only by design |
| List that grows and needs "Load more" or infinite scroll | GraphQL wire with cursor pagination via `pageInfo` | Native shape of the connection pattern |
| Complex server-side aggregation or cross-org joins | Imperative Apex returning a DTO | GraphQL wire does not cover arbitrary aggregation or callouts |
| Single sObject list with standard filters rendered in a simple card | `@wire(getListRecords)` or `lightning-datatable` with LDS | Less boilerplate; GraphQL is overkill |

---

## Recommended Workflow

1. Confirm scope — is this a read-only screen or does it also write? Writes disqualify the adapter.
2. Enumerate the minimal field list the UI actually renders and the relationships that join them.
3. Draft the `gql` query with a `query ($vars: ...)` signature and validate it against the official UI API GraphQL examples.
4. Stabilize the variables object in a getter so its identity only changes when a value changes; reference it as `$vars`.
5. Store `this.wiredResult` in the wire handler and plan a `refreshGraphQL(this.wiredResult)` call after every imperative mutation.
6. Add cursor-paginated accumulation only if the list can grow; key accumulated rows by `Id.value`.
7. Run `scripts/check_lwc_graphql_wire.py --manifest-dir force-app/main/default/lwc` and resolve every finding.

---

## Review Checklist

- [ ] The component reads only. All writes go through UI API or imperative Apex.
- [ ] Every scalar access in the template uses `.value` or `.displayValue`; no bare `{record.Field}` reads.
- [ ] `gql` literal contains no `${...}` JS interpolation — all runtime values flow through declared query variables.
- [ ] Variables object identity is stable across renders; it is not rebuilt in the template or in `renderedCallback`.
- [ ] Pagination uses `pageInfo.endCursor` and `hasNextPage`; "Load more" appends instead of replaces.
- [ ] `refreshGraphQL(this.wiredResult)` is called after imperative mutations that change the queried data.
- [ ] The query selects only the fields the UI renders; no speculative "include everything we might need" selection.

---

## Salesforce-Specific Gotchas

1. **`gql` is a tagged template literal, not a string builder** — `${jsValue}` inside the literal is not reactive and will not re-fetch when the value changes; declare a variable and pass it through the wire config.
2. **Scalars are wrapped objects** — `Name` comes back as `{ value, displayValue }`. Forgetting `.value` in the template silently renders `[object Object]`.
3. **`refreshGraphQL` is not `refreshApex`** — it takes the wired result object, not the data, and comes from `lightning/uiGraphQLApi`, not `@salesforce/apex`.
4. **Pagination is cursor-based** — the connection shape exposes `pageInfo.endCursor`/`hasNextPage`. Emulating offset pagination defeats caching and drifts on inserts.
5. **FLS is enforced silently** — inaccessible fields return `null` without an error; tests on a privileged admin user can mask data loss that production users will hit.
6. **Unstable variables thrash the cache** — rebuilding `{ ids: [...], limit: 25 }` on every getter call creates a new identity each render; memoize it.
7. **The adapter is read-only** — there is no `mutation` support on this wire. Generating a `mutation { ... }` block will fail at runtime.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `gql` query template | A minimal query sized to the rendered UI, with declared variables and an `operationName` for telemetry |
| Paginator pattern | A `loadMore()` handler that appends new `edges` and advances the cursor from `pageInfo.endCursor` |
| Refresh hook plan | A documented list of imperative mutations paired with `refreshGraphQL(this.wiredResult)` calls |
| Checker report | Line-numbered findings for JS interpolation inside `gql`, wrong refresh helper, missing `pageInfo`, and mutation attempts |

---

## Related Skills

- `lwc/wire-service-patterns` — use when the decision is how to provision data generally; this skill is the GraphQL-specific deep dive.
- `lwc/lwc-imperative-apex` — use when writes or complex server-side logic disqualify the GraphQL wire.
- `lwc/lwc-wire-refresh-patterns` — use when the core problem is invalidating cached data after a mutation across wire types.
