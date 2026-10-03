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

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Retrieval Augmented Generation (offline preparation, retrievers, online usage), Ground with Retrieval Augmented Generation (retriever settings, 255-character search text, Data Cloud permission sets, retiring retrievers), Limitations for Einstein Search (retrievers and search indexes not deployed), Einstein Data Library (What Are Data Libraries, Add a Data Library, Choose A Data Source, Select Data Library Fields, Select Files to Upload, Assign Data Libraries to Features), Manage Data Sources, Einstein Audit and Feedback Data, Trust and Agents: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0), GenAiPromptTemplate (fields, `isCitationEnabled`, sample) and GenAiFunction (`retriever` invocation target type): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Agentforce Developer Guide, Manage Data Libraries with ADL API: https://developer.salesforce.com/docs/ai/agentforce/guide/adl.html
- Agentforce Developer Guide, Get Started with ADL API (external client app, client credentials, JWT tokens): https://developer.salesforce.com/docs/ai/agentforce/guide/adl-get-started.html
- Agentforce Developer Guide, Knowledge Library Example (request body, data categories, indexing, status, immutable fields, update and delete rules): https://developer.salesforce.com/docs/ai/agentforce/guide/adl-get-started-knowledge-library.html
- Agentforce Developer Guide, Manage Data Libraries with Salesforce CLI: https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-adl.html
- Agentforce Developer Guide, Agent Script Blocks (runtime `citation` and `groundedness`): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Supported Models (`sfdc_ai__DefaultGPT41`): https://developer.salesforce.com/docs/ai/agentforce/guide/supported-models.html
- Salesforce CLI help text, `sf agent adl create --help` and `sf agent adl status --help` (CLI 2.151.7: source types, immutable primary index fields, data category flags, status artifacts)

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Agentforce Grounding — https://help.salesforce.com/s/articleView?id=sf.agentforce_grounding.htm
- Data Cloud Retriever — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud_retriever.htm
- Salesforce Well-Architected — Trusted — https://architect.salesforce.com/docs/architect/well-architected/trusted
