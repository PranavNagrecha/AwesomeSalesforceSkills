# Well-Architected Notes — Flow Batch Alternatives

## Relevant Pillars

- **Scalability** — the escalation point from Flow to Apex is the load-bearing
  decision.
- **Reliability** — partial failure handling is the #1 gap in Flow-only jobs.
- **Operational Excellence** — admin-visible orchestration plus dev-owned
  heavy lifting beats either alone.

## Architectural Tradeoffs

- **In-Flow chunking vs Apex escalation:** in-Flow preserves admin ownership
  but hits a ceiling; Apex scales but adds a dev dependency.
- **Platform Event fan-out vs Scheduled Path chunking:** events add governor
  headroom per chunk; schedule chunking is simpler to reason about.
- **Queueable vs Batch:** Queueable is easier for modest volumes and supports
  finalizers; Batch is the right tool for million-record scans.

## Official Sources Used

- Flow Limits — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Apex Async — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_async_overview.htm
- async-selection decision tree — `standards/decision-trees/async-selection.md`
