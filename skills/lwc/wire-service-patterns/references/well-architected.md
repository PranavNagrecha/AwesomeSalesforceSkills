# Well-Architected Notes — Wire Service Patterns

## Relevant Pillars

### Performance

The wire service is a performance tool when used well because it aligns with LDS caching and reactive data provisioning.

### Reliability

Reactive parameters, refresh behavior, and immutable handling all determine whether the component shows trustworthy data.

### User Experience

Users experience stale data as a broken app. A deliberate wire strategy keeps the UI current without unnecessary loading or duplicate calls.

## Architectural Tradeoffs

- **Wire convenience vs imperative control:** Wire is excellent for reads, while imperative patterns are clearer for writes and explicit user actions.
- **UI API simplicity vs custom Apex flexibility:** UI API is safer and cheaper for standard record access, while Apex is justified only for logic UI API cannot express.
- **Single-purpose wires vs GraphQL read models:** GraphQL can simplify complex reads, but it introduces a different response shape and should stay focused on read scenarios.

## Anti-Patterns

1. **Using custom Apex for ordinary record reads** — needless maintenance and weaker default platform protections.
2. **Mutating wired data directly** — blurs immutable input and local state.
3. **Assuming wires auto-refresh after every server-side change** — stale UI remains until an explicit refresh strategy exists.

## Official Sources Used

- Understand the Wire Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- GraphQL Wire Adapter for LWC — https://developer.salesforce.com/docs/platform/graphql/guide/graphql-wire-lwc
