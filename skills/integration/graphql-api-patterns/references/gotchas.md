# Gotchas - Graphql Api Patterns

Non-obvious behaviors that cause real production problems. "GraphQL guide" means the GraphQL API Developer Guide at developer.salesforce.com/docs/platform/graphql/guide (pages Query Limitations, Rate Limiting, Pagination, Mutations, Requests and Responses, Query Status, Introduction, Wire Adapter Limitations, Best Practices), fetched 2026-10-03. "LWC guide" means the Lightning Web Components Developer Guide pages for `lightning/graphql` (v2) and `lightning/uiGraphQLApi` (v1).

## Gotcha 1: HTTP 200 Does Not Mean the Query Worked

**What happens:** A client checks only the status code, renders an empty component, and never surfaces that the query named a field that does not exist.

**When it occurs:** "GraphQL API can also return a 200 OK in cases where the request contains an error, such as an invalid object name or field." Error types include `InvalidSyntax`, `ValidationError`, `DataFetchingException`, `OperationNotSupported`, and `ExecutionAborted`. A 200 is also returned for no matches or an invalid record ID, whereas UI API returns 404 for a missing record.

**How to avoid:** Inspect `errors` on every response, log the error type, and treat a missing record as "empty edges", not as an HTTP error. In LWC, the wire returns `errors` (plural), not `error`.

**Source:** GraphQL guide, Status Codes and Error Responses; Requests and Responses; LWC guide, lightning/graphql (errors property).

---

## Gotcha 2: Relay Paging Stops at 4,000 Records

**What happens:** An export walks cursors until `hasNextPage` is false and silently stops at 4,000 rows.

**When it occurs:** "Using pagination without an upper-bound limit lets you retrieve up to 4,000 records only." For more than 200 records the guide recommends `upperBound` (API v59.0+), where `first` must be between 200 and 2,000. From v60.0 a later request can add `upperBound` to switch an existing relay paging session. Records created after paging starts are not included.

**How to avoid:** Use `upperBound` for any list that can exceed 4,000, set a generous value, keep it constant for a paginated collection in the wire adapter, and restart paging to pick up new records. For bulk extracts, prefer Bulk API 2.0.

**Source:** GraphQL guide, Pagination; Paginate with an Upper-Bound Limit; Wire Adapter Limitations.

---

## Gotcha 3: Each Subquery Counts Against Rate Limits

**What happens:** A dashboard with one large GraphQL query consumes API capacity faster than expected and starts getting 503 responses.

**When it occurs:** "Each GraphQL query can contain up to 10 subqueries. Each subquery counts as one request for rate limiting." GraphQL "uses the same API limits as other Connect API limits. When you exceed the rate limit, the endpoint returns a 503 Service Unavailable error code."

**How to avoid:** Keep queries to the subqueries the view needs, cache with the wire adapter, and back off on 503.

**Source:** GraphQL guide, Query Limitations; Rate Limiting.

---

## Gotcha 4: `lightning/uiGraphQLApi` Is Not the Default Choice

**What happens:** A new component imports `lightning/uiGraphQLApi`, then cannot use optional fields or compose a fragment, or the team rewrites working v2 code into v1 because an outdated example said `lightning/graphql` was wrong.

**When it occurs:** The LWC guide says `lightning/graphql` (v2) "supersedes the lightning/uiGraphQLApi (v1) module. We recommend that you use lightning/graphql (v2) where possible." v1 "supports Mobile Offline use cases, but it doesn't support newer features, such as optional fields and dynamic query construction." The GraphQL guide adds: "If you're supporting Mobile Offline use cases, you must use the lightning/uiGraphQLApi LWC module."

**How to avoid:** Default to `lightning/graphql`; use v1 only when Mobile Offline is a stated requirement. The skill checker reports v1 imports for review.

**Source:** LWC guide, lightning/graphql Wire Adapter (v2) and lightning/uiGraphQLApi (v1); GraphQL guide, Wire Adapter Limitations.

---

## Gotcha 5: String Interpolation in `gql` Behaves Differently per Module

**What happens:** A component built on v1 uses `${fragment}` inside `gql` and fails; or a v2 component interpolates a user's search text into the query and never re-runs when the text changes.

**When it occurs:** For `lightning/uiGraphQLApi`, the LWC guide lists "String interpolation constructs using ${}" and "Dynamic construction of GraphQL queries at runtime, such as referencing a fragment from another component" as unsupported, and recommends `lightning/graphql` instead. In both modules `gql` "isn't reactive", so values interpolated at load time do not change the query later.

**How to avoid:** Use interpolation only to compose static fragments in v2. Pass every runtime value through `variables` returned by a getter.

**Source:** LWC guide, lightning/graphql reference (unsupported use cases in uiGraphQLApi; `gql` isn't reactive).

---

## Gotcha 6: Mutations Exist, With Transaction Rules That Differ From REST

**What happens:** A team writes everything through REST because an old note said GraphQL is read-only, or uses mutations and is surprised that one bad record rolled back the whole batch.

**When it occurs:** Mutations are beta in API v59.0 to v65.0 and generally available from v66.0, and the GraphQL wire adapter supports them from v66.0. The `uiapi` mutation input has `allOrNone`, default `true`; with `false`, "only operations that fail are rolled back along with any operations that depend on those failed operations". Creating a record with child relationships is not supported, and update and delete requests cannot query fields. In v59.0 to v65.0, `RecordUpdatePayload` returns only `success`.

**How to avoid:** Pin v66.0 or later for production mutations, choose `allOrNone` deliberately, use `@{alias}` references for dependent operations, and create parents and children in separate operations.

**Source:** GraphQL guide, Mutations, Use Mutations, Mutation Limitations.

---

## Gotcha 7: Each User Sees a Different Schema

**What happens:** A query works for the developer and fails with a validation error for a sales user.

**When it occurs:** GraphQL exposes "UI API Enabled sObjects, honoring the object-level security and field-Level security of the context user. Therefore, two different users can have two different views of the GraphQL schema based on their access permissions." A field missing from a user's schema produces an error such as "Field 'FieldName' in type 'ObjectName' is undefined". UNVERIFIED (2026-10-03): that an FLS-hidden field produces exactly this error, rather than another validation message, is inferred from the per-user schema statement and the filter-field example.

**How to avoid:** Test each persona. In v2, consider optional fields for data that some users cannot see. Guest user access is controlled in Setup under API Access Controls (the guide gives v67.0 in one place and v68.0 in another).

**Source:** GraphQL guide, Introduction to GraphQL API; Query Limitations (filter-field error); Status Codes (403 for guest users).

---

## Gotcha 8: Relationship Depth and Object Coverage Are Bounded

**What happens:** A query that traverses `Contact.Account.Owner.Manager.Name` works in one org and fails in another, or an object is missing from the schema.

**When it occurs:** Up to 55 child-to-parent relationships per query and up to five levels (API v58.0+; two levels in v57.0 and earlier); up to 20 parent-to-child relationships, one level deep. "You can query only objects that User Interface API supports." Some fields are not filterable in `where`.

**How to avoid:** Pin v58.0+ for deep parent traversal, check object support against UI API, and check field filterability in the Object Reference before building filters.

**Source:** GraphQL guide, Query Limitations.

---

## Gotcha 9: `totalCount` Costs a Full Lookup

**What happens:** A component that shows five rows and a total is slow on large objects.

**When it occurs:** "Including the totalCount field makes the query look up all existing records, even though it returns only the first 5." "Requesting totalCount can have performance implications for large or complex queries."

**How to avoid:** Request `totalCount` only where the UI shows it, and never inside frequently refreshed components.

**Source:** GraphQL guide, GraphQL Wire Adapter Best Practices.

---

## Gotcha 10: Offline and Mobile Prefetch Need Care

**What happens:** A component works in the browser and fails to prefetch in the Salesforce mobile app or Field Service.

**When it occurs:** "Most Salesforce mobile environments ... can't prefetch undefined queries", so a getter that returns `undefined` until `recordId` arrives cannot be primed. Queries that fail prefetch must keep metaschema directives for referential integrity and priming. Fragments on custom objects and fields break referential integrity if the object or field is renamed.

**How to avoid:** For mobile and offline targets, use v1, avoid fragments on custom metadata, and make delayed queries reactive through `query` and `variables` getters as the guide shows.

**Source:** GraphQL guide, GraphQL Wire Adapter Best Practices; Wire Adapter Limitations; LWC guide, lightning/graphql reference.
