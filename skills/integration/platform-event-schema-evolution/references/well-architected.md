# Well-Architected Notes — Platform Event Schema Evolution

## Relevant Pillars

- **Reliability** — Schema-incompatible changes break live integrations silently. The dual-publish-and-deprecate pattern keeps the system reliable across owner-independent deploy schedules.
- **Operational Excellence** — Treating event schemas as a public API (versioned, source-controlled, audited) prevents the most common avoidable production incidents in event-driven Salesforce.

## Architectural Tradeoffs

- **In-place evolution vs. versioning:** Additive changes are cheap; renames/type-changes require a v2 event with dual-publish complexity. The cost of dual-publish is real (extra publishers, extra storage, retirement coordination), but it is the only safe path for breaking changes across independent subscriber teams.
- **Required vs. optional fields:** Required-on-publish enforces data quality but locks publishers into the new shape immediately. Optional-with-subscriber-side-validation is more flexible but moves the validation responsibility downstream.
- **Replay window as feature vs. constraint:** The 72-hour replay window enables resilient subscribers but constrains schema-change cadence. Plan changes around it; never assume a change is "live" the moment it deploys.

## Anti-Patterns

1. **Treating event schema like internal code** — Live events are a published API. Apply API-evolution discipline (versioning, deprecation timelines, communication) the same way you would for a public REST endpoint.
2. **Renaming fields in place** — The old name is gone immediately; subscribers fail. Always v2-and-dual-publish.
3. **No subscriber inventory before changing** — Changing without knowing who consumes is the canonical recipe for "the warehouse went stale and no one noticed for two days."

## Official Sources Used

- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
