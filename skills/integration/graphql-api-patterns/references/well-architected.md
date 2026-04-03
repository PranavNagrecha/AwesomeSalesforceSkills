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

- Salesforce GraphQL API Developer Guide - https://developer.salesforce.com/docs/platform/graphql/guide/graphql-about.html
- GraphQL Queries and Mutations - https://developer.salesforce.com/docs/platform/graphql/guide/graphql-queries.html
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
