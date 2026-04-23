# Well-Architected Notes — Agentforce Cost Optimization

## Relevant Pillars

- **Performance** — smaller contexts reduce latency and improve routing quality.
- **Operational Excellence** — cost model + dashboards turn spend into a managed dial.
- **Reliability** — tighter contexts reduce distraction, improving consistency.

## Architectural Tradeoffs

- **Quality vs cost:** cost cuts always risk quality; treat as an A/B exercise.
- **Tier routing vs single-tier simplicity:** tier routing saves cost but adds complexity.
- **Summarization vs verbatim history:** summarization saves tokens but can lose subtle context.

## Anti-Patterns

1. Blind cost cuts with no evaluation.
2. Optimizing tool output before topics and grounding (smaller potential win).
3. Changing model tier mid-quarter with no A/B.

## Official Sources Used

- Agentforce overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_overview.htm
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm
- Data Cloud retrievers — https://help.salesforce.com/s/articleView?id=sf.data_cloud_retrievers.htm
- Salesforce Well-Architected Performance — https://architect.salesforce.com/docs/architect/well-architected/trusted/performant
