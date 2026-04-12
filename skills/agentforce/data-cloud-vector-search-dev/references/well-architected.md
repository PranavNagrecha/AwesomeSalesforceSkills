# Well-Architected Notes — Data Cloud Vector Search Dev

## Relevant Pillars

### Performance
Vector search adds a retrieval round-trip to every agent inference. The end-to-end latency includes: query embedding computation, ANN search across the index, chunk transfer to the grounding layer, and Trust Layer processing. The primary developer-controllable levers are top-K (fewer chunks = faster transfer), chunk size (smaller chunks = faster embedding computation per chunk), and index refresh mode (does not affect query latency but determines data currency). Practitioners must establish a latency budget before setting top-K and chunk size — for customer-facing agents with strict SLAs, start at topK=3 and raise only if recall testing demands it. Monitoring prompt token counts is also a Performance concern: each retrieved chunk consumes tokens, and large top-K with large chunk sizes can exhaust context windows.

### Security
Retrieval is a potential data exfiltration vector: if the vector index contains sensitive DMO fields and grounding is not scoped correctly, an agent could surface confidential information in response to manipulated queries. The Einstein Trust Layer provides the primary defense layer — it applies data masking to PII-classified fields and enforces zero retention at the LLM provider. However, masking only applies to fields explicitly classified in the Data Cloud field taxonomy. Developers must proactively classify sensitive source fields before indexing. Additionally, the Data Cloud Connected App used for Query API access must be restricted to the minimum required scopes and rotated on the standard credential rotation schedule.

### Reliability
A vector search index can be in a degraded or stale state without surfacing an obvious error to the end user — the agent will still respond, but responses will be ungrounded or based on stale content. Reliability controls include: monitoring index status in Data Cloud Setup (Active vs Degraded), alerting on Data Stream refresh failures, and running regular end-to-end retrieval tests with known-answer queries to detect silent index degradation. For production deployments, the index rebuild process (required after embedding model changes or chunking strategy changes) must be tested in a non-production environment first.

### Reliability (Packaging)
Vector search index configuration is a Data Kit component. Packaging errors — such as missing DMO definitions, incomplete Data Stream configuration, or omitting the vector index component from the Data Kit — cause deployment failures in scratch orgs or target sandboxes. The index configuration must be tested end-to-end in a scratch org before any managed package release.

---

## Architectural Tradeoffs

| Decision | Tradeoff |
|---|---|
| Easy Setup vs Advanced Setup | Easy Setup is faster but forfeits all chunking control. Advanced Setup requires more upfront configuration decisions but avoids costly rebuilds when precision is inadequate. |
| Small chunks (256 tokens) vs large chunks (768 tokens) | Small chunks improve retrieval precision but increase total vector count, index size, and search latency at scale. Large chunks reduce index size but dilute semantic focus, increasing false positives. |
| High top-K (10+) vs low top-K (3–5) | High top-K improves recall for broad queries but consumes more prompt token budget and increases retrieval latency. Low top-K is token-efficient but may miss relevant content for multi-faceted questions. |
| Salesforce-managed embedding model vs BYO via Model Builder | Salesforce-managed requires no configuration and is supported out of the box. BYO models may achieve better domain-specific accuracy but require Model Builder configuration, custom model hosting, and the ability to re-embed the full corpus if the model changes. |
| Single shared index vs per-category indexes | A single shared index is operationally simpler but requires metadata filters to scope retrieval. Per-category indexes allow independent chunking strategies per content type but multiply operational overhead. |

---

## Anti-Patterns

1. **Indexing Without Pre-Classifying Sensitive Fields** — Building a vector search index over a DMO that contains PII or confidential fields without first classifying those fields in the Data Cloud field taxonomy results in uncontrolled masking behavior at inference time. Developers assume retrieved chunks will look the same in the prompt as they do in the raw DMO, but Trust Layer masking silently replaces sensitive values before the LLM sees them, causing grounding to appear ineffective. Classify all sensitive fields before the index build and verify masking behavior in a controlled test before production launch.

2. **Using Easy Setup in Production Without Benchmarking Retrieval Quality** — Easy Setup is appropriate for prototyping but should not be promoted to production without a retrieval quality benchmark. Chunk size and strategy choices significantly affect the semantic accuracy of search results. Teams that skip this validation step often discover retrieval quality problems only after users complain about unhelpful agent responses, at which point a full index rebuild is required — potentially during business hours.

3. **Reusing CRM Connected App Credentials for Data Cloud API Calls** — Attempting to authenticate with the Data Cloud Query API using credentials from a standard CRM Connected App (without `cdpapi` scope) results in persistent `401 Unauthorized` errors. This wastes debugging time and sometimes leads developers to incorrectly blame the vector index or the grounding configuration. The fix is a separate Data Cloud Connected App — but this is an architectural decision (separate app, separate credentials rotation, separate secret management) that should be planned in advance.

---

## Official Sources Used

- Data Cloud Vector Search — https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search.htm
- Supported Chunking Strategies — https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search_chunking.htm
- Search Index Reference — Data Cloud — https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search_index_reference.htm
- Data 360 Developer Guide — Features Overview — https://developer.salesforce.com/docs/atlas.en-us.salesforce_cdp_api.meta/salesforce_cdp_api/cdp_api_features_overview.htm
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm
- Einstein Copilot Grounding — https://help.salesforce.com/s/articleView?id=sf.einstein_copilot_grounding.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
