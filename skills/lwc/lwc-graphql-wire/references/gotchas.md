# Gotchas — LWC GraphQL Wire

Non-obvious Salesforce platform behaviors that cause real production problems when working with the GraphQL wire adapter — both `lightning/graphql` (v2, recommended) and `lightning/uiGraphQLApi` (v1, Mobile Offline only). Where the two diverge, the module is called out.

## Gotcha 0: Reaching For v1 (`lightning/uiGraphQLApi`) By Default

**What happens:** A component imports `lightning/uiGraphQLApi` because that is what older examples and blog posts show, silently forgoing optional fields, dynamic queries, and `executeMutation` writes.

**When it occurs:** Any new GraphQL-wire component authored from memory or from pre-Winter-'26 sample code.

**How to avoid:** Default to `lightning/graphql` (v2). The official reference is explicit: "`lightning/graphql` (v2) supersedes the `lightning/uiGraphQLApi` (v1) module" and "We recommend that you use `lightning/graphql` (v2) where possible." Only stay on v1 when the component must run in Mobile Offline, which v2 "doesn't currently support."

---

## Gotcha 1: Reactive `${jsValue}` Interpolation Is A v1 Trap, Not A v2 Feature Mismatch

**What happens (v1):** Developers write `` gql`... Id: { eq: "${this.recordId}" }` `` expecting the value to re-interpolate when `recordId` changes. On v1 it does not — the value is parsed once at module load and the wire never re-fires.

**The v2 nuance:** v2 *does* support JS string interpolation inside the `gql` literal, but for **dynamic query construction** — varying the query's structure (an object name, a field set) at runtime — not for feeding reactive per-record filter values. Interpolating a value that changes per record still belongs in a declared `$` variable even on v2, because interpolated text is resolved when the query string is built, not tracked reactively like a wire variable.

**When it occurs:** Any time a `$`-prefixed reactive variable is available but the author reaches for JS template interpolation out of habit, or when a v2 developer assumes interpolation replaces declared variables entirely.

**How to avoid:** For reactive per-record filters on either module, declare the variable in the query signature — `query ($recordId: ID) { ... Id: { eq: $recordId } }` — and pass `variables: '$vars'` through the wire config with `vars` as a stable-identity object. Use v2 interpolation to shape the query, not to smuggle in reactive data.

---

## Gotcha 2: Scalars Are Wrapped As `{ value, displayValue }`

**What happens:** A template that renders `{record.Name}` shows `[object Object]`, because UI API GraphQL wraps every field in an object with both the raw `value` and the locale-formatted `displayValue`.

**When it occurs:** When porting a `getRecord` component that used flat field paths, or when an LLM-generated template reads fields as if they were bare primitives.

**How to avoid:** Always access `.value` (raw) or `.displayValue` (formatted). For currencies and dates, `.displayValue` usually matches what the user expects to see.

---

## Gotcha 3: The Refresh Call Differs Between v2 And v1

**What happens:** Code calls `refreshGraphQL(this.data)`, `refreshApex(this.wiredResult)`, or the wrong module's helper and nothing refreshes. On v2 there is no `refreshGraphQL` at all — refresh lives on the emitted result.

**When it occurs:** Immediately after a mutation (v2 `executeMutation`, or an imperative Apex / UI API write), when the component tries to re-read the graph.

**How to avoid:** Store the full wired result in the handler (`handleResult(result) { this.wiredResult = result; }`). On **v2**, call the `refresh` method on the emitted result — `this.wiredResult.refresh()`. On **v1**, call `refreshGraphQL(this.wiredResult)` imported from `lightning/uiGraphQLApi`. `refreshApex` is for `@wire(<apexMethod>)` only. Note the asymmetry after a v2 `executeMutation`: a **delete** is auto-removed from LDS ("Refreshes are not required for delete operations"), but a **create** "will not appear in existing GraphQL query results until the query is refreshed," so refresh after create/update and skip it after delete.

---

## Gotcha 4: Pagination Is Cursor-Based, Not Offset-Based

**What happens:** A `skip` / `offset` pattern copied from other GraphQL stacks either silently ignores the argument or returns inconsistent pages when rows are inserted between requests.

**When it occurs:** When migrating from a homegrown SOQL offset paginator to GraphQL, or when an LLM invents `offset` arguments.

**How to avoid:** Use `first: N` plus `after: $cursor`, read `pageInfo.endCursor` and `pageInfo.hasNextPage` after each fire, and accumulate `edges.node` into a tracked array keyed by `Id.value`.

---

## Gotcha 5: The *Wire* Is Read-Only — But v2 Writes Through `executeMutation`, Not A `mutation {}` Block In The Query

**What happens:** A wired `gql` literal containing `mutation { ... }` fails at runtime. Developers assume either that GraphQL is fully read-only on Salesforce (outdated for v2) or that they can embed a mutation in the wire query (wrong on both modules).

**When it occurs:** When a component tries to consolidate reads and writes, or when an LLM generates a `mutation` block because other GraphQL stacks expose one on the same query.

**How to avoid:** The wired query stays read-only on both modules. On **v2** (Spring '26+), perform writes with a separate `executeMutation` call: `import { gql, executeMutation } from 'lightning/graphql';` then `await executeMutation({ query, variables, operationName })` — it takes the same three properties as the wire and supports create/update/delete without Apex. On **v1**, there is no write path: keep writes on `lightning/uiRecordApi` (`createRecord`, `updateRecord`, `deleteRecord`) or imperative Apex. After a v2 create/update, refresh the wire; after a v2 delete, LDS auto-removes the record.

---

## Gotcha 6: Field-Level Security Trims Silently

**What happens:** A field the user cannot read comes back as `null` rather than raising an error. Tests pass as an admin and fail for restricted users with no obvious signal.

**When it occurs:** When profiles or permission sets differ from the developer's, especially with custom objects and custom fields still going through a permission-set rollout.

**How to avoid:** Treat `null` on required-looking fields as suspicious, add a permission-set-minimal test user in automated UI tests, and consider logging a warning in the wire handler when a field the UI depends on is `null`. On **v2**, if a subset of users legitimately lacks access to a field, mark it optional: "When you mark a field as optional, the query will succeed even if the user doesn't have permission to see it." That converts a potential query fault into a cleanly absent field the UI can branch on, which is a more explicit contract than relying on silent `null`.

---

## Gotcha 7: Unstable Variable Object Identity Thrashes The Cache

**What happens:** Every render creates a new `{ accountId, first: 25 }` object, giving the adapter a fresh variables identity even though the values have not changed. The cache key shifts, deduplication breaks, and the network is hit more than expected.

**When it occurs:** When the variables object is built inline in the wire decorator (not supported) or in a getter that always returns a new object, regardless of whether inputs changed.

**How to avoid:** Build the variables object from tracked fields and memoize it — either by caching it in a property updated only when inputs change, or by deriving it from primitive getters so the identity remains stable when the inputs do.
