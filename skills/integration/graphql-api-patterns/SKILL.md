---
name: graphql-api-patterns
description: "Use when designing or reviewing Salesforce GraphQL API usage, especially endpoint selection, field shaping, connection-based pagination, LWC wire adapters, and GraphQL vs REST tradeoffs. Triggers: 'GraphQL API', 'lightning/graphql', 'uiGraphQLApi', 'GraphQL pagination', 'GraphQL vs REST'. NOT for building a custom GraphQL server or for generic REST integration design with no GraphQL surface."
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
inputs:
  - "client type such as LWC, Experience Cloud, mobile, or server integration"
  - "query shape and whether pagination, aggregation, or mutation behavior is needed"
  - "offline support, payload size, and tracing expectations"
outputs:
  - "GraphQL versus REST recommendation"
  - "review findings for query design and adapter choice"
  - "request pattern for variables, pagination, and error handling"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Graphql Api Patterns

Use this skill when the integration question is really about query shape and client efficiency, not just about calling another endpoint. Salesforce GraphQL is strongest when a consumer needs flexible field selection from a single endpoint and wants to avoid a chain of UI API or REST requests.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the consumer an LWC, Experience Cloud page, mobile client, or server-side integration?
- Does the use case need flexible reads, aggregations, pagination, or mutation behavior that is supported in the target API version?
- Is mobile offline support required, or is standard online LWC behavior enough?

---

## Core Concepts

### GraphQL Is A Single Endpoint With Client-Shaped Responses

Salesforce GraphQL requests go to `/services/data/vXX.X/graphql`. The client controls the selection set, so payload size and nesting discipline matter more than they do with fixed REST resources.

### Variables Beat String-Built Query Text

Keep the query document stable and pass runtime values through GraphQL variables. This improves safety, readability, and cache behavior. String-building query text with user input is the wrong default.

### Adapter Choice Matters In LWC

For most new LWC use cases, prefer `lightning/graphql`. Use `lightning/uiGraphQLApi` only when Mobile Offline compatibility is the actual requirement. Treat adapter selection as an architectural decision, not just an import statement.

### Partial Data And Pagination Need Intentional Handling

GraphQL can return `data` and `errors` together. Connection-style pagination and cursor handling should be part of the design, not an afterthought added once result sets get large.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

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

Non-obvious platform behaviors that cause real production problems:

1. **GraphQL is easy to over-fetch** - one endpoint does not make huge nested payloads free.
2. **`lightning/uiGraphQLApi` is not the default choice** - use it when offline compatibility is required, not just because it exists.
3. **`data` and `errors` can coexist** - clients that only check one branch miss partial failures.
4. **Mutation assumptions drift by API version and surface** - validate supported behavior before promising write patterns.

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
