# Well-Architected Notes — Data Cloud Grounding

## Relevant Pillars

- **Security** — sharing enforcement must happen at retrieval time, not in the LLM layer.
- **Reliability** — citations and stable ids enable quality measurement.
- **User Experience** — freshness SLA determines whether users trust the answer.

## Architectural Tradeoffs

- **Prompt-packing vs retriever:** packing facts into the prompt is faster per
  turn but does not scale; retriever adds a call and needs design.
- **Structured vs vector vs hybrid:** structured is exact and cheap for record
  lookups; vector is tolerant and necessary for unstructured; hybrid costs more.
- **Streaming ingestion vs batch:** streaming is expensive but essential when
  freshness SLA is minutes; batch is fine when daily is acceptable.
- **Index replication vs single source:** duplicating the index near the agent
  runtime reduces latency but adds a freshness hop.

## Official Sources Used

- Agentforce Grounding — https://help.salesforce.com/s/articleView?id=sf.agentforce_grounding.htm
- Data Cloud Retriever — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud_retriever.htm
- Salesforce Well-Architected — Trusted — https://architect.salesforce.com/docs/architect/well-architected/trusted
