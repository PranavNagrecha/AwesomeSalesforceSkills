# Well-Architected Notes — Flow Large Data Volume Patterns

## Relevant Pillars

- **Performance** — Unbounded retrieval and large collections increase CPU time, heap use, and latency for the saving user or integration. Performance reviews should include worst-case row counts for each `Get Records`, not only “happy path” clicks.
- **Scalability** — LDV-safe Flow designs cap work per interview and avoid patterns that assume small related sets forever. Scalability means predictable behavior as parents and children accumulate.
- **Reliability** — Hitting query-row or heap limits fails the whole transaction in many contexts. Reliability requires explicit caps, fault handling, and monitoring on bulk entry points.
- **Operational Excellence** — Row-budget documentation, checker scripts on metadata, and volume tests belong in the same operational toolkit as deployments. Incidents from “sudden” automation failures are easier to prevent when volume assumptions are written down.

## Architectural Tradeoffs

- **Tight cap vs. complete business data** — A hard row cap keeps the org stable but may truncate what decision logic sees. The tradeoff should be explicit: either the business accepts “top N,” or processing must move to a system that can scan full history in chunks.
- **Flow vs. Apex/async** — Flow keeps declarative ownership and faster iteration; Apex or external batch adds engineering cost but is the correct tool for open-ended scans. This skill does not prescribe Apex implementations but flags when declarative retrieval is structurally insufficient.
- **Synchronous rollup vs. async eventual consistency** — Real-time rollups from massive child sets are expensive. Async rollups or platform-native summary mechanisms reduce synchronous pressure at the cost of latency.

## Anti-Patterns

1. **Unbounded related retrieval** — Loading “all” children for reporting or enrichment in a record-triggered path. Replace with caps, summaries, or async processing.
2. **Volume testing only with UI single-record saves** — Misses bulk API and integration behavior. Always test the flow under bulk entry conditions.
3. **Ignoring cumulative row totals** — Optimizing one `Get Records` while leaving several other wide queries in the same path.

## Official Sources Used

- Salesforce Well-Architected Overview — quality framing for scalability and operational tradeoffs — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Flow Builder — product behavior and builder capabilities for Flow design — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Flow Reference — element behavior, limits, and considerations tied to Flow runtime — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- General Flow Limits — per-transaction Flow limits including totals that apply alongside Apex governor limits — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm&type=5
- Flow Considerations — additional runtime considerations for automation at scale — https://help.salesforce.com/s/articleView?id=sf.flow_considerations.htm&type=5
- Metadata API Developer Guide — Flow metadata structure when reviewing `*.flow-meta.xml` in source control — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
