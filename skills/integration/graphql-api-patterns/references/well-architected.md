# Well-Architected Notes - Graphql Api Patterns

## Relevant Pillars

- **Performance** - GraphQL is valuable only if field selection and pagination are disciplined.
- **Reliability** - request contracts and error handling must stay predictable.

## Architectural Tradeoffs

- **GraphQL vs REST:** flexible reads versus explicit endpoint contracts.
- **Platform adapter vs raw HTTP:** more native behavior versus more transport control.
- **Wide query vs multiple smaller views:** fewer round trips versus harder tracing and payload control.

## Anti-Patterns

1. **String-built GraphQL documents** - unsafe and hard to maintain.
2. **Adapter choice by habit** - especially `uiGraphQLApi` without offline need.
3. **Single-endpoint mythology** - assuming one endpoint means no architecture work remains.

## Official Sources Used

Fetched and read on 2026-10-03 unless marked.

- GraphQL API Developer Guide, Get Started and Introduction to GraphQL API (editions, per-user schema, guest access). https://developer.salesforce.com/docs/platform/graphql/guide/graphql-about.html and https://developer.salesforce.com/docs/platform/graphql/guide/intro-graphql-api.html
- GraphQL API Developer Guide, Query Limitations (10 subqueries, 2,000 records per subquery, relationship limits, UI API objects only). https://developer.salesforce.com/docs/platform/graphql/guide/query-limits.html
- GraphQL API Developer Guide, Rate Limiting and Status Codes and Error Responses (503 on rate limit, 200 with errors). https://developer.salesforce.com/docs/platform/graphql/guide/rate-limit.html and https://developer.salesforce.com/docs/platform/graphql/guide/query-status.html
- GraphQL API Developer Guide, Pagination, Use Pagination, Paginate with an Upper-Bound Limit (4,000-record relay ceiling, upperBound rules). https://developer.salesforce.com/docs/platform/graphql/guide/paginate.html, https://developer.salesforce.com/docs/platform/graphql/guide/paginate-use.html, https://developer.salesforce.com/docs/platform/graphql/guide/paginate-use-upperbound.html
- GraphQL API Developer Guide, Mutations, Use Mutations, Create and Update Records, Mutation Limitations (v59.0 to v65.0 beta, v66.0 GA, allOrNone). https://developer.salesforce.com/docs/platform/graphql/guide/mutations-intro.html, https://developer.salesforce.com/docs/platform/graphql/guide/mutations-use.html, https://developer.salesforce.com/docs/platform/graphql/guide/mutations-create.html, https://developer.salesforce.com/docs/platform/graphql/guide/mutations-limitations.html
- GraphQL API Developer Guide, Requests and Responses, Authorization, Get Started with Altair (endpoint, body parts, host format). https://developer.salesforce.com/docs/platform/graphql/guide/requests-and-responses.html, https://developer.salesforce.com/docs/platform/graphql/guide/authorization.html, https://developer.salesforce.com/docs/platform/graphql/guide/get-started-graphql.html
- GraphQL API Developer Guide, wire adapter pages: Use, When to Use, Best Practices, Limitations. https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc-use.html, https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc-when.html, https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc-best.html, https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc-limitations.html
- Lightning Web Components Developer Guide: lightning/graphql Wire Adapter (v2), lightning/uiGraphQLApi (v1), GraphQL API Wire Adapter Comparison, lightning/graphql reference, executeMutation. https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-graphql-module.html, https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-graphql-api.html, https://developer.salesforce.com/docs/platform/lwc/guide/reference-graphql-intro.html, https://developer.salesforce.com/docs/platform/lwc/guide/reference-graphql.html, https://developer.salesforce.com/docs/platform/lwc/guide/reference-graphql-mutation.html
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill: GraphQL Queries and Mutations, https://developer.salesforce.com/docs/platform/graphql/guide/graphql-queries.html (returned 404 on 2026-10-03; the mutation pages above replace it).
