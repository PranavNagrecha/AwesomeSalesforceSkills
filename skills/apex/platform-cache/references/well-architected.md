# Well-Architected Notes — Platform Cache

## Relevant Pillars

### Performance

Platform Cache primarily exists to reduce repeated expensive lookups and improve response times.

Tag findings as Performance when:
- the same expensive data is repeatedly reloaded across transactions
- cache wrappers are missing around obvious shared reference-data lookups
- session or org cache would remove repeated computation cleanly

### Scalability

Shared caching can reduce query and compute load across the org when the data is suited for it.

Tag findings as Scalability when:
- many users need the same reference data
- repeated recalculation is putting pressure on limits or query load
- poor invalidation strategy causes teams to abandon caching entirely

### Reliability

Cached systems remain reliable only when misses and eviction are safe.

Tag findings as Reliability when:
- code assumes cache presence
- invalidation is undefined
- sensitive or user-specific data is stored in the wrong cache scope

## Architectural Tradeoffs

- **Org cache vs session cache:** shared reuse versus user-scoped isolation.
- **Aggressive TTL vs stale risk:** longer TTL can improve performance until it harms correctness.
- **Direct cache calls vs wrapper service:** wrappers improve consistency and invalidation discipline.

## Anti-Patterns

1. **Platform Cache treated as durable storage** — unsafe by design.
2. **Shared cache used for sensitive user context** — scope mismatch and security risk.
3. **No invalidation strategy** — stale data problems eventually outweigh performance wins.

## Official Sources Used

- Apex Developer Guide — Platform Cache overview
- Apex Reference Guide — cache partition APIs
- Platform Cache considerations guidance — limits, scope, and operational considerations
