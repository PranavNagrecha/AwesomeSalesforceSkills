# Well-Architected Notes — Apex CPU And Heap Optimization

## Relevant Pillars

### Performance

This skill is directly about transaction efficiency and throughput under real load.

Tag findings as Performance when:
- algorithmic cost is too high for the transaction budget
- heap pressure comes from unnecessarily retained data
- large payload handling or logging consumes disproportionate resources

### Scalability

CPU- and heap-heavy patterns often work for tiny data sets and fail at production scale.

Tag findings as Scalability when:
- performance collapses as record or payload counts rise
- the design assumes single-record or small-list behavior
- async chunking or caching should be considered

### Reliability

Limit failures cause user-visible rollbacks and brittle background processing.

Tag findings as Reliability when:
- CPU or heap exceptions are already causing transaction failures
- diagnostics are too weak to isolate hotspots
- the workload is too heavy for one transaction boundary

## Architectural Tradeoffs

- **Micro-optimization vs structural refactor:** most wins come from changing data shape, not syntax trivia.
- **Single transaction vs async decomposition:** sometimes the cheapest optimization is to split the workload.
- **Rich diagnostics vs extra overhead:** instrumentation helps until it becomes the bottleneck itself.

## Anti-Patterns

1. **Nested-loop brute force after bulkification** — database-safe but still CPU-expensive.
2. **Large payload duplication** — heap pain with little business value.
3. **Blind tuning without measurement** — changes risk without confidence.

## Official Sources Used

- Apex Developer Guide — governor limits and performance guidance
- Apex Reference Guide — `Limits` methods
- Salesforce Well-Architected Overview — performance, scalability, and reliability framing
