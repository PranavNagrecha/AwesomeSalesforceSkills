# Gotchas — LWC GraphQL Wire

Non-obvious Salesforce platform behaviors that cause real production problems when working with `lightning/uiGraphQLApi`.

## Gotcha 1: `gql` Is A Tagged Template Literal, Not A String Template

**What happens:** Developers write `` gql`... Id: { eq: "${this.recordId}" }` `` expecting the value to re-interpolate when `recordId` changes. It does not. The value is parsed once at module load and the wire never re-fires when `recordId` updates.

**When it occurs:** Any time a `$`-prefixed reactive variable is available but the author reaches for JS template interpolation out of habit.

**How to avoid:** Declare the variable in the query signature — `query ($recordId: ID) { ... Id: { eq: $recordId } }` — and pass `variables: '$vars'` through the wire config with `vars` as a stable-identity object.

---

## Gotcha 2: Scalars Are Wrapped As `{ value, displayValue }`

**What happens:** A template that renders `{record.Name}` shows `[object Object]`, because UI API GraphQL wraps every field in an object with both the raw `value` and the locale-formatted `displayValue`.

**When it occurs:** When porting a `getRecord` component that used flat field paths, or when an LLM-generated template reads fields as if they were bare primitives.

**How to avoid:** Always access `.value` (raw) or `.displayValue` (formatted). For currencies and dates, `.displayValue` usually matches what the user expects to see.

---

## Gotcha 3: `refreshGraphQL` Takes The Whole Wired Result, Not The Data

**What happens:** Code calls `refreshGraphQL(this.data)` or `refreshApex(this.wiredResult)` and nothing refreshes. Either the argument shape is wrong or the helper comes from the wrong module.

**When it occurs:** Immediately after an imperative Apex or UI API mutation, when the component tries to re-read the graph.

**How to avoid:** Store the full wired result in the handler (`handleResult(result) { this.wiredResult = result; }`) and call `refreshGraphQL(this.wiredResult)` imported from `lightning/uiGraphQLApi`. `refreshApex` is for `@wire(<apexMethod>)` only.

---

## Gotcha 4: Pagination Is Cursor-Based, Not Offset-Based

**What happens:** A `skip` / `offset` pattern copied from other GraphQL stacks either silently ignores the argument or returns inconsistent pages when rows are inserted between requests.

**When it occurs:** When migrating from a homegrown SOQL offset paginator to GraphQL, or when an LLM invents `offset` arguments.

**How to avoid:** Use `first: N` plus `after: $cursor`, read `pageInfo.endCursor` and `pageInfo.hasNextPage` after each fire, and accumulate `edges.node` into a tracked array keyed by `Id.value`.

---

## Gotcha 5: The Adapter Is Read-Only — There Is No `mutation`

**What happens:** A `gql` literal containing `mutation { ... }` fails at runtime with an unclear error. Developers assume GraphQL implies a read/write API; on Salesforce UI API GraphQL, it does not.

**When it occurs:** When a component tries to consolidate reads and writes into one adapter, or when an LLM generates a `mutation` block because other GraphQL stacks expose one.

**How to avoid:** Keep writes on `lightning/uiRecordApi` (`createRecord`, `updateRecord`, `deleteRecord`) or imperative Apex. After the write returns, call `refreshGraphQL(this.wiredResult)` to re-read.

---

## Gotcha 6: Field-Level Security Trims Silently

**What happens:** A field the user cannot read comes back as `null` rather than raising an error. Tests pass as an admin and fail for restricted users with no obvious signal.

**When it occurs:** When profiles or permission sets differ from the developer's, especially with custom objects and custom fields still going through a permission-set rollout.

**How to avoid:** Treat `null` on required-looking fields as suspicious, add a permission-set-minimal test user in automated UI tests, and consider logging a warning in the wire handler when a field the UI depends on is `null`.

---

## Gotcha 7: Unstable Variable Object Identity Thrashes The Cache

**What happens:** Every render creates a new `{ accountId, first: 25 }` object, giving the adapter a fresh variables identity even though the values have not changed. The cache key shifts, deduplication breaks, and the network is hit more than expected.

**When it occurs:** When the variables object is built inline in the wire decorator (not supported) or in a getter that always returns a new object, regardless of whether inputs changed.

**How to avoid:** Build the variables object from tracked fields and memoize it — either by caching it in a property updated only when inputs change, or by deriving it from primitive getters so the identity remains stable when the inputs do.
