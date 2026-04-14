# Well-Architected Notes — Integration Pattern Selection

## Relevant Pillars

- **Reliability** — Pattern selection directly determines integration failure modes; choosing synchronous for high-latency or high-volume scenarios creates systemic reliability risks.
- **Security** — Pattern selection affects data exposure surface; synchronous callouts require Named Credentials and mTLS considerations; event-driven patterns introduce event replay security considerations.
- **Operational Excellence** — Documented pattern decision records provide the rationale that future maintainers need when changing the integration; undocumented pattern choices create maintenance debt.
- **Performance** — Volume threshold analysis (REST vs Bulk API 2.0) is a performance decision that must be made at pattern selection time.
- **Scalability** — Event-driven patterns (Platform Events, CDC) scale better than synchronous point-to-point for growing volumes; pattern selection is a scalability investment.

## Architectural Tradeoffs

**Synchronous vs Asynchronous:** Synchronous provides immediate confirmation and simpler error handling but creates latency coupling between systems. Asynchronous decouples systems and handles variable latency better but requires more complex error recovery design.

**Point-to-Point vs Event-Driven vs Hub-and-Spoke:** Point-to-point is simplest but creates a web of dependencies. Event-driven decouples producers and consumers. Hub-and-spoke provides centralized visibility but Salesforce cannot be the hub for cross-system transactions.

**Native Salesforce vs Middleware:** Not every integration requires middleware. For simple bidirectional REST API integrations, native Salesforce mechanisms (callouts, REST API, Platform Events) are sufficient. Middleware is required for orchestration, protocol conversion, and cross-system transactions.

## Anti-Patterns

1. **Hub-and-spoke orchestration in Apex** — Apex cannot coordinate cross-system transactions with rollback. Multi-system orchestration with transactional integrity requires middleware.

2. **Synchronous REST for high-volume or high-latency scenarios** — Synchronous callouts have a 120-second timeout and per-transaction call limits. High-volume batch sync must use Bulk API 2.0.

3. **Skipping pattern framework and defaulting to familiarity** — Choosing REST because "we always use REST" or Platform Events because "we want real-time" without applying the two-axis framework leads to mismatched patterns that require costly redesigns.

## Official Sources Used

- Integration Patterns and Practices — Pattern Selection Guide — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Architects Integration Patterns Fundamentals — https://architect.salesforce.com/content/1508/integration-patterns-fundamentals
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `integration/event-driven-architecture-patterns` — implementation for event-driven pattern
- `architect/api-led-connectivity-architecture` — governance architecture for multi-system integration
- `integration/error-handling-in-integrations` — error recovery for selected pattern
