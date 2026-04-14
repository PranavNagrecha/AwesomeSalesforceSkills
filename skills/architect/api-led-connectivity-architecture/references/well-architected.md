# Well-Architected Notes — API-Led Connectivity Architecture

## Relevant Pillars

- **Reliability** — API-led connectivity isolates backend failures to the System API layer; downstream consumers are shielded from backend outages and schema changes. Without this isolation, a single backend change can cascade to all consumers simultaneously.
- **Operational Excellence** — Exchange catalog entries, versioning policies, and deprecation timelines are operational governance artifacts. Without them, integration teams cannot know what is deployed, who depends on it, or when it is safe to change. Rate limit design is an operational reliability control.
- **Security** — Dedicated OAuth credentials per consumer (especially for Agentforce agents) enable per-consumer audit logs, independent revocation, and rate limit enforcement. Shared credentials make it impossible to isolate agent traffic from human-initiated traffic in audit logs.
- **Performance** — Rate limits designed top-down prevent cascade exhaustion when multiple consumers fan into shared Process and System APIs simultaneously. Bottom-up rate limit design consistently fails at peak load.
- **Scalability** — The Experience API layer absorbs consumer-specific growth without requiring changes to Process or System APIs. Adding a new consumer type requires only a new Experience API — the underlying layers are unchanged.

## Architectural Tradeoffs

**All three tiers vs. System API only:** A full three-tier design provides maximum change isolation and consumer flexibility but adds latency (three network hops), maintenance cost (three catalog entries, three versioning policies), and organizational overhead (potentially three teams). For single-consumer, pass-through integrations with no orchestration logic, a System API only is the correct choice. The decision must be documented in the Architecture Decision Log with a re-evaluation trigger.

**Shared vs. dedicated Experience APIs:** Sharing one Experience API across multiple consumer types reduces the number of APIs to maintain but forces all consumers to accept the most complex response shape, applies a single rate limit to all consumers, and makes it impossible to revoke one consumer's access without impacting others. Dedicated Experience APIs per consumer type are the correct default for any consumer with distinct rate limit, schema, or authentication requirements.

**Governance documentation vs. governance enforcement:** Documenting versioning policy in a spreadsheet or wiki is insufficient — it is not governance. Governance requires tooling enforcement: Exchange catalog entries with SLA policies, automated consumer notification on MAJOR version bumps, and policy-enforced deprecation timelines. Teams that document governance without enforcing it produce the same breaking-change incidents as teams with no governance.

## Anti-Patterns

1. **Prescribing all three tiers universally** — Applying System + Process + Experience layers to every integration regardless of consumer count or orchestration need creates unnecessary latency, maintenance overhead, and organizational friction. The correct application is context-dependent and must be documented when layers are skipped.

2. **Bottom-up rate limit design** — Setting System API limits from backend capacity and dividing downward does not account for concurrent consumer fanout. Multiple Experience APIs firing simultaneously can exhaust a System API limit that appeared safe when each was evaluated individually. Always design rate limits from consumer traffic patterns downward.

3. **Salesforce as consumer-only** — Designing outbound integrations from Salesforce while leaving inbound reads from Salesforce as direct REST API calls creates hidden coupling. External systems hardcoding Salesforce REST endpoints are broken by Salesforce schema changes with no integration team visibility.

## Official Sources Used

- MuleSoft API-Led Connectivity Whitepaper — https://www.mulesoft.com/lp/whitepaper/api/api-led-connectivity
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- MuleSoft Anypoint Exchange Documentation — https://docs.mulesoft.com/exchange/
- Agentforce Agent Fabric Documentation — https://developer.salesforce.com/docs/einstein/genai/guide/agent-fabric.html

## Cross-Skill References

- `integration/integration-pattern-selection` — upstream pattern selection before layer design
- `integration/api-error-handling-design` — HTTP error response contracts within layers
- `integration/error-handling-in-integrations` — orchestration-layer error handling after API layer design
