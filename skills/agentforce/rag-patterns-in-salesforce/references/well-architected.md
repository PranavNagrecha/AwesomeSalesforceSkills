# Well-Architected Notes — RAG Patterns in Salesforce

## Relevant Pillars

### Security

RAG introduces a retrieval surface that sits between the customer data store and the LLM. Every chunk returned from a vector index passes through the Einstein Trust Layer, which enforces zero data retention, data masking for classified fields, and full audit logging of retrieved content. Security posture for a RAG implementation requires: (1) classifying sensitive fields in the Data Cloud field taxonomy before indexing, (2) configuring org-level Grounding policies to restrict which agents can query which indexes, and (3) regularly auditing the Trust Layer log for unexpected masking events or retrieval of content that should be access-controlled. Access controls on the underlying source records (Salesforce Knowledge sharing, Data Cloud user permissions) do not automatically propagate to the vector index — the index is a denormalized copy. Index-level access must be controlled via Grounding policy configuration.

### Performance

RAG adds latency to every agent response that triggers retrieval. The retrieval round-trip (query embedding + ANN search + chunk return) adds measurable latency before the LLM call begins. Performance design decisions that directly affect latency: chunk size (smaller = more vectors to search), the retriever's number of results (higher = more data transferred), and index size (larger indexes have higher ANN search cost). For customer-facing agents with latency SLAs, keep the number of results conservative (3 to 5) and use filter fields to reduce the candidate set. Monitor p95 and p99 retrieval latency separately from LLM latency in production.

### Reliability

The retriever is a dependency in the agent's critical path. If the Data Cloud vector index is unavailable (e.g., during a Data Cloud maintenance window or index rebuild), the Grounding call fails and the agent must either fall back to an ungrounded response or surface an error. Design subagents (called topics before April 2026) with explicit fallback behavior when zero chunks are retrieved — the agent should acknowledge the knowledge base is unavailable rather than hallucinate. Data Stream refresh cadence also affects reliability: a stale index means agents answer based on outdated information, which is a reliability failure for knowledge-dependent use cases.

### Operational Excellence

RAG systems require ongoing operational management that pure LLM agents do not. Key operational concerns: monitoring index freshness (refresh lag, failed Data Stream jobs), tracking retrieval quality over time (chunk hit rate, semantic similarity score distribution), and managing chunk quality as source content evolves (e.g., Knowledge articles being archived or restructured). Establish a runbook that documents: refresh schedule and acceptable staleness window, process for re-ingesting a full Knowledge corpus after a taxonomy change, and escalation path when Trust Layer masking unexpectedly degrades retrieved content. Include RAG-specific metrics in the agent's observability dashboard.

### Scalability

Data Cloud vector indexes scale with the volume of source content and the rate of retrieval queries. For large corpora (hundreds of thousands of articles or documents), index build time and storage costs grow proportionally. ANN search at scale requires attention to index sharding and approximate search accuracy tradeoffs. For high-query-volume deployments (e.g., a public-facing service agent with thousands of concurrent sessions), retrieval throughput limits apply. Review Salesforce Data Cloud vector search capacity documentation and engage a Salesforce account architect for pre-production capacity sizing on high-volume deployments.

---

## Architectural Tradeoffs

### Chunk Size vs. Retrieval Precision

Smaller chunks (128–256 tokens) produce embeddings with high specificity — they closely represent a narrow concept. This improves precision: a query for a specific procedure retrieves the exact chunk containing that procedure. However, small chunks fragment context, so the LLM may receive a chunk that answers the question but lacks the surrounding context needed to formulate a complete response. Larger chunks (512–768 tokens) preserve context but dilute the embedding signal, potentially lowering recall for specific queries. Data Cloud's default max token limit is 512, and it documents no overlap setting (the earlier "64-token overlap" starting point is UNVERIFIED, 2026-10-03); tune the chunking strategy and max tokens based on observed retrieval quality in preview testing.

### Single Index vs. Domain-Partitioned Indexes

A single shared index is simpler to manage (one data stream, one index, one set of retrievers) but requires filter fields and custom retrievers to prevent cross-domain contamination. Remember the limit of 10 search indexes per Data Cloud instance. Domain-partitioned indexes (one per product line, language, or content type) eliminate the need for filters and can be managed independently, but multiply operational overhead. For organizations with 2–4 clearly distinct content domains and separate ownership teams, partitioned indexes provide cleaner separation. For organizations with a single content team and homogeneous content, a single index with metadata filters is operationally simpler.

### Salesforce-Managed Embedding Model vs. Custom Model

Data Cloud lists E5-Large V2, Multilingual E5-Large, and Whisper-Large-V3 as supported embedding models; Easy Setup defaults to E5-Large V2. Choose Multilingual E5-Large for multilingual content. UNVERIFIED (2026-10-03): the earlier statement that custom embedding models can be registered through Model Builder for search indexes was not found in a fetched source; hybrid search is the documented lever when domain vocabulary or product codes matter.

---

## Anti-Patterns

1. **Indexing Without Content Quality Gates** — Ingesting all Knowledge articles into the vector index without filtering out draft, archived, or low-quality articles. Draft and archived articles have the same DMO presence as published articles unless the Data Stream filter explicitly excludes them. Retrieved chunks from unpublished or stale articles can surface incorrect or superseded information. Always apply a `PublishStatus = 'Online'` and `Language = 'en_US'` (or equivalent) filter on the Data Stream or DMO query that feeds the vector index.

2. **Setting the Number of Results High "to Be Safe"**: Increasing the retriever's number of results to 10 or 15 under the assumption that more context is always better. In practice, low-relevance chunks at position 8–15 introduce noise that the LLM must filter, increase total prompt token consumption, add retrieval latency, and can cause the LLM to anchor on irrelevant content in multi-hop reasoning tasks. Calibrate the number of results empirically using a held-out test set of representative queries; for most service agent use cases 3–5 is optimal.

3. **Skipping Trust Layer Audit Review Before Go-Live** — Deploying a RAG-enabled agent to production without reviewing the Einstein Trust Layer audit log during QA. Masking events, unexpected chunk content, or retrieval of records the agent user should not access are only visible in the audit log. These issues will not surface as errors in the agent UI — they silently degrade response quality or create compliance exposure. Mandatory pre-go-live step: export and review audit log for a statistically representative sample of test retrieval queries.

---

## Official Sources Used

Read for this revision (2026-10-03):

- Data Cloud guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/data_cloud.pdf. Use Search for AI, Automation, and Analytics (vector and hybrid search, customer-managed key note), Chunking Strategies, How the Max Token Setting Affects Chunking, Chunk and Index Data Model Objects, Create a Search Index Configuration with Easy Setup (defaults), Search Index Reference (embedding models, file formats), Add a Search Index Configuration to a Data Kit, Retrievers (default, custom, dynamic, versions, Create a Custom Retriever, Delete a Retriever), Unstructured Data and Search Index Guidelines and Limits, Feature Availability in Data Cloud and Customer Data Platform.
- Quickstart Your Einstein Generative AI Solution, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf. Retrieval Augmented Generation overview, Ground with Retrieval Augmented Generation (retriever settings, search text limits), Add a Retriever to a Prompt Template, Prompt Builder Limitations (Einstein Search deployment rule), Answer Questions with Knowledge Prompt Template, Einstein Data Library chapter, Einstein Trust Layer (masking disabled for agents).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. GenAiPromptTemplate data providers; searched for aiGrounding and topK (neither exists); DataObjectSearchIndexConf (Search Answers only, not RAG retrievers).

Listed in the original version and not re-read (Salesforce Help does not fetch; developer.salesforce.com returned 403 on 2026-10-03):

- Data Cloud Vector Search: https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search.htm (search index content read in the Data Cloud PDF above).
- Einstein Copilot Grounding: https://help.salesforce.com/s/articleView?id=sf.einstein_copilot_grounding.htm (source of the subagent "Grounding record" model, now corrected).
- Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm (read in the Generative AI PDF above).
- Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Data Cloud Developer Guide, Packages and Data Kits: https://developer.salesforce.com/docs/atlas.en-us.data_cloud_dev.meta/data_cloud_dev/data_cloud_packages.htm
