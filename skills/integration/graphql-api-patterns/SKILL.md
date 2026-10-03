---
name: graphql-api-patterns
description: "Use when designing or reviewing Salesforce GraphQL API usage, especially endpoint selection, field shaping, connection-based pagination, LWC wire adapters, and GraphQL vs REST tradeoffs. Triggers: 'GraphQL API'. NOT for building a custom GraphQL server or for generic REST integration design with no GraphQL component — use integration/rest-api-patterns."
category: integration
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - graphql
  - lightning-graphql
  - uiGraphQLApi
  - pagination
  - api-design
triggers:
  - "when should I use Salesforce GraphQL instead of REST"
  - "lightning graphql versus uiGraphQLApi"
  - "GraphQL connection pagination in Salesforce"
  - "GraphQL query variables and field selection"
  - "Salesforce GraphQL aggregation or mutation design"
  - "lightning graphql isn't working"
  - "write a paginated GraphQL query in a Lightning web component"
  - "create or update records with a Salesforce GraphQL mutation"
inputs:
  - "client type such as LWC, Experience Cloud, mobile, or server integration"
  - "query shape and whether pagination, aggregation, or mutation behavior is needed"
  - "offline support, payload size, and tracing expectations"
outputs:
  - "GraphQL versus REST recommendation"
  - "review findings for query design and adapter choice"
  - "request pattern for variables, pagination, and error handling"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Graphql Api Patterns

Use this skill when the integration question is really about query shape and client efficiency, not just about calling another endpoint. Salesforce GraphQL is strongest when a consumer needs flexible field selection from a single endpoint and wants to avoid a chain of UI API or REST requests.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the consumer an LWC, Experience Cloud page, mobile client, or server-side integration?
- Does the use case need flexible reads, aggregations, pagination, or mutation behavior that is supported in the target API version?
- Is mobile offline support required, or is standard online LWC behavior enough?

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is the client an LWC, a mobile offline app, or a server integration?" | LWC uses `lightning/graphql` (v2) by default; Mobile Offline must use `lightning/uiGraphQLApi` (v1); servers POST to `/services/data/vXX.X/graphql` | The adapter or endpoint per client | No v1-only code where v2 features are needed, and no broken offline priming |
| "Which API version will the client pin?" | Mutations are GA from v66.0 (beta v59.0 to v65.0); upper-bound pagination needs v59.0, switching to it mid-query v60.0; five-level parent traversal needs v58.0 | The minimum version for each feature used | Features that exist in the pinned version instead of runtime schema errors |
| "How many records per view, and does the UI need totals?" | Default page is 10; up to 2,000 records per subquery; without `upperBound` relay paging stops at 4,000; `totalCount` can be expensive | The `first`, `after`, and `upperBound` plan | Predictable payloads and no silent truncation at 4,000 rows |
| "Will the query write data, and must related writes succeed together?" | Mutations default to `allOrNone: true`; with `false`, failed operations and their dependents roll back while others commit; creating a record with child relationships is not supported | The `allOrNone` choice and the write order | Writes that fail the way the business expects |
| "Which users run it, including guest users?" | The schema honors each user's object and field access, so two users see different schemas; guest access is controlled in API Access Controls | A test user per persona | Queries that work for every audience, not just the developer |
| "How will the client treat a 200 response that carries errors?" | GraphQL returns 200 with an `errors` array for syntax, validation, and fetch errors; 503 signals rate limiting | An error-handling contract | Partial failures that surface instead of rendering empty components |

What a proper configuration adds over "just writing a query": the adapter and API version match the features used, paging is planned past the 4,000-row relay limit, writes have explicit transaction behavior, and partial errors reach the user.

---

## Core Concepts

### GraphQL Is A Single Endpoint With Client-Shaped Responses

Salesforce GraphQL requests go to `/services/data/vXX.X/graphql`. The client controls the selection set, so payload size and nesting discipline matter more than they do with fixed REST resources.

### Variables Beat String-Built Query Text

Keep the query document stable and pass runtime values through GraphQL variables. This improves safety, readability, and cache behavior. String-building query text with user input is the wrong default.

### Adapter Choice Matters In LWC

For most new LWC use cases, prefer `lightning/graphql`. Use `lightning/uiGraphQLApi` only when Mobile Offline compatibility is the actual requirement. Treat adapter selection as an architectural decision, not just an import statement.

| Capability (LWC Developer Guide, GraphQL API Wire Adapter Comparison) | `lightning/uiGraphQLApi` (v1) | `lightning/graphql` (v2) |
|---|---|---|
| Mobile Offline | Supported | Not currently supported |
| Optional fields | Not supported | Supported |
| Dynamic query construction, including `${}` interpolation in `gql` (for example composing a fragment from another component) | Not supported | Supported |
| Variables in directives such as `@skip` and `@include` | Not supported | Listed as supported in the LWC guide; the GraphQL API guide's wire adapter limitations page says it is not (UNVERIFIED which is current) |
| Recommendation | Only for Mobile Offline | "We recommend that you use lightning/graphql (v2) where possible" |

`gql` is not reactive: runtime values belong in `variables`, exposed through a getter, so the wire re-runs when they change.

### Limits That Shape the Query

| Limit (GraphQL API Developer Guide, Query Limitations and Pagination) | Value |
|---|---|
| Subqueries per GraphQL query | 10, each counted as one request for rate limiting |
| Records per subquery | Up to 2,000; default page size is 10 |
| Relay pagination without `upperBound` | Up to 4,000 records in total |
| `upperBound` pagination | API v59.0+; `first` must be 200 to 2,000; switching to it in a later request needs v60.0 |
| Child-to-parent relationships | Up to 55 per query; up to 5 levels (v58.0+), 2 levels in v57.0 and earlier |
| Parent-to-child relationships | Up to 20 per query; 1 level |
| Objects | Only those User Interface API supports |
| Rate limiting | Shares Connect API limits; exceeding them returns 503 |

### Partial Data And Pagination Need Intentional Handling

GraphQL can return `data` and `errors` together, and the HTTP status is usually 200 even when the request contains an invalid object or field name (`ValidationError`), a syntax error (`InvalidSyntax`), or a fetch failure (`DataFetchingException`). Connection-style pagination and cursor handling should be part of the design, not an afterthought added once result sets get large.

### Mutations Exist and Have Transaction Rules

Mutations are beta in v59.0 to v65.0 and generally available from v66.0; the LWC wire adapter supports them from v66.0. The `uiapi` mutation field takes `allOrNone` (default `true`). Creating a record together with child relationships is not supported, and update and delete requests cannot return queried fields. An earlier version of this skill's anti-patterns file called the API read-only; that is out of date.

---

## Common Patterns

### LWC Query Adapter Pattern

**When to use:** An LWC needs flexible reads with fewer round trips than separate wire adapters or Apex endpoints.

**How it works:** Define a static `gql` document, pass runtime values through `variables`, and keep the selection set intentionally small.

**Why not the alternative:** Raw `fetch()` calls to the endpoint duplicate logic the platform adapter already handles.

### GraphQL For View Models, REST For Operational Actions

**When to use:** The UI needs shaped read data, but writes or side effects are clearer in REST or Apex services.

**How it works:** Use GraphQL to gather the read model and keep operational commands on dedicated APIs.

### Cursor-Based Pagination

**When to use:** Result sets can exceed a single page and the client needs stable incremental loading.

**How it works:** Use the connection model and track cursors instead of assuming offset-style paging.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Client needs flexible read shape from one endpoint | GraphQL | Reduces over-fetching and request fan-out |
| Team needs explicit endpoint contracts for operational actions | REST or Apex REST | Better fit for command-style APIs |
| LWC needs GraphQL and offline support | `lightning/uiGraphQLApi` | Adapter exists for that narrower requirement |
| LWC needs GraphQL without offline requirement | `lightning/graphql` | Preferred default adapter for most new work |

---


## Recommended Workflow

1. Identify the client and pin the API version; check the version-gated features (mutations, `upperBound`, relationship depth) against it.
2. Choose the surface: `lightning/graphql` for LWC, `lightning/uiGraphQLApi` only for Mobile Offline, `POST /services/data/vXX.X/graphql` for servers.
3. Write a named operation (`query accountsByIndustry`) with a minimal selection set and runtime values in `variables`; keep `gql` documents static except for fragment composition in v2.
4. Plan paging: `first` plus `after` cursors for small sets, `upperBound` for more than 200 rows and anything that may exceed 4,000.
5. Handle both `data` and `errors` on every response, including 200 responses with errors, and back off on 503.
6. Test with each persona, because each user's schema reflects their object and field access. A deployable component is in [`references/request-examples.md`](references/request-examples.md).
7. Run `python3 skills/integration/graphql-api-patterns/scripts/check_graphql_api_patterns.py --manifest-dir force-app/main/default` and resolve every finding.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Query text is stable and runtime values move through variables.
- [ ] Selection sets are minimal and not over-fetching nested data.
- [ ] Adapter choice is justified, especially if `uiGraphQLApi` is used.
- [ ] Pagination and partial-error handling are part of the design.
- [ ] Mutation support is validated against the target API version before rollout.
- [ ] REST, Composite, and GraphQL are compared deliberately instead of by trend.

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Over-fetching | One endpoint does not make large nested payloads free; `totalCount` costs a full lookup |
| Adapter choice | `lightning/graphql` is the default; `uiGraphQLApi` only for Mobile Offline |
| Errors on 200 | Clients that check only the HTTP status miss validation and fetch errors |
| 4,000-row ceiling | Relay paging without `upperBound` stops at 4,000 records |
| Mutations | GA from v66.0; `allOrNone` defaults to true; no child-relationship creates |
| Per-user schema | Fields a user cannot access are not in that user's schema |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API choice review | Recommendation for GraphQL versus REST or Composite |
| Query design review | Findings on variables, selection sets, pagination, and adapter use |
| GraphQL request scaffold | Stable query document and variables pattern for the chosen client |

---

## Related Skills

- `lwc/lifecycle-hooks` - use when the real problem is LWC state, rendering, or cleanup rather than the GraphQL contract.
- `integration/oauth-flows-and-connected-apps` - use when authentication and connected-app design are the real blockers around the API.
- `apex/apex-rest-services` - use when the org needs a custom command API rather than a client-shaped read surface.
