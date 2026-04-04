# Well-Architected Notes — RAG Patterns in Salesforce

## Relevant Pillars

### Security

RAG introduces a retrieval surface that sits between the customer data store and the LLM. Every chunk returned from a vector index passes through the Einstein Trust Layer, which enforces zero data retention, data masking for classified fields, and full audit logging of retrieved content. Security posture for a RAG implementation requires: (1) classifying sensitive fields in the Data Cloud field taxonomy before indexing, (2) configuring org-level Grounding policies to restrict which agents can query which indexes, and (3) regularly auditing the Trust Layer log for unexpected masking events or retrieval of content that should be access-controlled. Access controls on the underlying source records (Salesforce Knowledge sharing, Data Cloud user permissions) do not automatically propagate to the vector index — the index is a denormalized copy. Index-level access must be controlled via Grounding policy configuration.

### Performance

RAG adds latency to every agent response that triggers retrieval. The retrieval round-trip (query embedding + ANN search + chunk return) adds measurable latency before the LLM call begins. Performance design decisions that directly affect latency: chunk size (smaller = more vectors to search), top-K (higher = more data transferred), and index size (larger indexes have higher ANN search cost). For customer-facing agents with latency SLAs, tune top-K conservatively (3–5) and use metadata pre-filters to reduce the ANN candidate set. Monitor p95 and p99 retrieval latency separately from LLM latency in production.

### Reliability

The retriever is a dependency in the agent's critical path. If the Data Cloud vector index is unavailable (e.g., during a Data Cloud maintenance window or index rebuild), the Grounding call fails and the agent must either fall back to an ungrounded response or surface an error. Design agent topics with explicit fallback behavior when zero chunks are retrieved — the agent should acknowledge the knowledge base is unavailable rather than hallucinate. Data Stream refresh cadence also affects reliability: a stale index means agents answer based on outdated information, which is a reliability failure for knowledge-dependent use cases.

### Operational Excellence

RAG systems require ongoing operational management that pure LLM agents do not. Key operational concerns: monitoring index freshness (refresh lag, failed Data Stream jobs), tracking retrieval quality over time (chunk hit rate, semantic similarity score distribution), and managing chunk quality as source content evolves (e.g., Knowledge articles being archived or restructured). Establish a runbook that documents: refresh schedule and acceptable staleness window, process for re-ingesting a full Knowledge corpus after a taxonomy change, and escalation path when Trust Layer masking unexpectedly degrades retrieved content. Include RAG-specific metrics in the agent's observability dashboard.

### Scalability

Data Cloud vector indexes scale with the volume of source content and the rate of retrieval queries. For large corpora (hundreds of thousands of articles or documents), index build time and storage costs grow proportionally. ANN search at scale requires attention to index sharding and approximate search accuracy tradeoffs. For high-query-volume deployments (e.g., a public-facing service agent with thousands of concurrent sessions), retrieval throughput limits apply. Review Salesforce Data Cloud vector search capacity documentation and engage a Salesforce account architect for pre-production capacity sizing on high-volume deployments.

---

## Architectural Tradeoffs

### Chunk Size vs. Retrieval Precision

Smaller chunks (128–256 tokens) produce embeddings with high specificity — they closely represent a narrow concept. This improves precision: a query for a specific procedure retrieves the exact chunk containing that procedure. However, small chunks fragment context, so the LLM may receive a chunk that answers the question but lacks the surrounding context needed to formulate a complete response. Larger chunks (512–768 tokens) preserve context but dilute the embedding signal, potentially lowering recall for specific queries. The recommended starting point is 512 tokens with 64-token overlap, tuned based on observed retrieval quality in agent preview testing.

### Single Index vs. Domain-Partitioned Indexes

A single shared index is simpler to manage (one Data Stream, one index, one Grounding config) but requires metadata filtering to prevent cross-domain contamination. Domain-partitioned indexes (one per product line, language, or content type) eliminate the need for filters and can be managed independently, but multiply operational overhead. For organizations with 2–4 clearly distinct content domains and separate ownership teams, partitioned indexes provide cleaner separation. For organizations with a single content team and homogeneous content, a single index with metadata filters is operationally simpler.

### Salesforce-Managed Embedding Model vs. Custom Model

The Salesforce-managed embedding model requires no additional configuration and is supported within the standard Einstein Trust Layer. Custom embedding models registered via Model Builder offer higher-dimensional representations and can be fine-tuned on domain-specific vocabulary (e.g., legal, medical, financial). Custom models add operational complexity: model versioning, re-embedding on model updates, and the need to manage the Model Builder BYO LLM configuration. Use the Salesforce-managed model unless domain-specific vocabulary is measurably degrading retrieval quality in QA testing.

---

## Anti-Patterns

1. **Indexing Without Content Quality Gates** — Ingesting all Knowledge articles into the vector index without filtering out draft, archived, or low-quality articles. Draft and archived articles have the same DMO presence as published articles unless the Data Stream filter explicitly excludes them. Retrieved chunks from unpublished or stale articles can surface incorrect or superseded information. Always apply a `PublishStatus = 'Online'` and `Language = 'en_US'` (or equivalent) filter on the Data Stream or DMO query that feeds the vector index.

2. **Setting top-K High "to Be Safe"** — Increasing top-K to 10 or 15 under the assumption that more context is always better. In practice, low-relevance chunks at position 8–15 introduce noise that the LLM must filter, increase total prompt token consumption, add retrieval latency, and can cause the LLM to anchor on irrelevant content in multi-hop reasoning tasks. Calibrate top-K empirically using a held-out test set of representative queries; for most service agent use cases 3–5 is optimal.

3. **Skipping Trust Layer Audit Review Before Go-Live** — Deploying a RAG-enabled agent to production without reviewing the Einstein Trust Layer audit log during QA. Masking events, unexpected chunk content, or retrieval of records the agent user should not access are only visible in the audit log. These issues will not surface as errors in the agent UI — they silently degrade response quality or create compliance exposure. Mandatory pre-go-live step: export and review audit log for a statistically representative sample of test retrieval queries.

---

## Official Sources Used

- Data Cloud Vector Search — https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search.htm
- Einstein Copilot Grounding — https://help.salesforce.com/s/articleView?id=sf.einstein_copilot_grounding.htm
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Data Cloud Developer Guide: Packages and Data Kits — https://developer.salesforce.com/docs/atlas.en-us.data_cloud_dev.meta/data_cloud_dev/data_cloud_packages.htm
