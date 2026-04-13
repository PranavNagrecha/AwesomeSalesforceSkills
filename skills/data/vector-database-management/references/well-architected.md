# Well-Architected Notes — Vector Database Management

## Relevant Pillars

- **Security** — PII fields must be explicitly excluded from vector indexes. Embeddings stored in the vector index are not protected by standard Salesforce field-level security (FLS) or object-level security (OLS) on the source DMO. Any PII embedded at index creation is accessible through the retrieval layer to any consumer of the index, regardless of their access to the source record. Practitioners must apply PII field exclusion as a mandatory governance step at index creation, and audit the field list whenever the source DMO schema changes.

- **Performance** — Chunking strategy is the primary performance lever for retrieval relevance. Chunk size must be tuned to match query length and document structure. Overly small chunks (Easy Setup default 500 characters) fragment semantic context; overly large chunks reduce ranking precision by including too much irrelevant content in a single embedding. Overlap (5–15%) at chunk boundaries prevents relevant passages from being missed due to arbitrary split points. Performance degradation from a wrong chunking strategy cannot be corrected without a full index rebuild.

- **Reliability** — Vector index availability depends on the rebuild lifecycle. Because changing chunking strategy or embedding model requires deleting and recreating the index, teams must plan for index unavailability windows during major configuration changes. A rebuild runbook that documents current configuration (chunk size, overlap, embedding model, field list, refresh mode) is required to execute a reliable rebuild. For business-critical indexes, a blue/green pattern (build replacement in parallel, validate, reroute) eliminates the availability gap.

- **Operational Excellence** — Refresh mode selection (batch vs. continuous) must be a deliberate operational decision, not a default left unchanged. Continuous mode has higher Data Cloud credit consumption and should be enabled only when retrieval freshness is a documented business requirement. Credit consumption alerts must be set before enabling continuous mode to prevent runaway costs. Index configuration should be tracked in a rebuild runbook and reviewed whenever the source DMO schema or the Agentforce retrieval use case changes.

---

## Architectural Tradeoffs

**Chunking strategy: Easy Setup vs. Advanced Setup**

Easy Setup is appropriate for short, uniform documents where rapid index creation is more important than retrieval precision. Advanced Setup requires more upfront configuration and a rebuild if parameters need adjustment, but is the correct choice for production knowledge bases, longer documents, or any use case where retrieval precision directly affects Agentforce answer quality. The cost of getting chunking wrong is a full index rebuild — there is no incremental fix.

**Refresh mode: Batch vs. Continuous**

Batch refresh is lower cost and appropriate for corpora that change infrequently. Continuous refresh maintains near-real-time index freshness but multiplies credit consumption in proportion to source data update frequency. The tradeoff is operational cost versus retrieval freshness. This decision should be revisited if the source DMO update pattern changes (e.g., ERP batch size increases, new real-time event stream feeds the DMO).

**Embedding model selection**

The embedding model determines the semantic quality of retrieval. Higher-quality or domain-specific models improve precision for specialized corpora (legal, medical, technical). However, every model change requires a full index rebuild. Model selection should be treated as a high-stakes, infrequent decision. Avoid switching models opportunistically — establish a clear quality bar and a planned migration window before executing a model change.

---

## Anti-Patterns

1. **Creating a vector index over all available DMO fields without PII review** — Including PII fields (names, email addresses, health data) in a vector index embeds that data in a form that bypasses standard Salesforce FLS/OLS protections. Any consumer of the index retrieval API can access the embedded PII regardless of their access to the source object. Always audit the field list for PII before creating an index, and document excluded fields in the rebuild runbook.

2. **Leaving batch refresh as default for a business-critical real-time use case** — The default Data Stream refresh mode is batch. For use cases where retrieval freshness directly affects business outcomes (inventory availability, live pricing, active incident status), leaving batch refresh in place means the vector index can lag hours behind reality. This pattern often surfaces in production when users report stale data from Agentforce, requiring an emergency configuration change. Establish the refresh mode requirement during index design, not after go-live.

3. **Skipping the rebuild runbook** — Vector index configuration (chunk size, overlap, embedding model, field list, refresh mode) is not surfaced prominently in the Setup UI after creation. When a precision problem requires a rebuild, or when an embedding model upgrade is needed, practitioners without a documented runbook must reconstruct the original configuration from memory or audit logs. A missed field, wrong chunk size, or incorrect overlap can silently degrade retrieval quality in the rebuilt index. Maintaining a runbook is a low-cost, high-reliability operational practice.

---

## Official Sources Used

- Data Cloud Vector Search Overview — https://help.salesforce.com/s/articleView?id=sf.c360_a_vector_search.htm&type=5
- Data 360 Limits and Guidelines — https://help.salesforce.com/s/articleView?id=sf.c360_a_limits_and_guidelines.htm&type=5
- Data Cloud Setup and Administration — https://help.salesforce.com/s/articleView?id=sf.c360_a_admin_setup.htm&type=5
- Agentforce Retrieval Augmented Generation — https://help.salesforce.com/s/articleView?id=sf.agentforce_rag.htm&type=5
