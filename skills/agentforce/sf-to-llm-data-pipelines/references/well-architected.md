# Well-Architected Notes — SF-to-LLM Data Pipelines

## Relevant Pillars

### Security

This skill is primarily a security discipline. Data leaving the Salesforce org boundary is outside the protection of the Einstein Trust Layer, Salesforce field-level security, sharing rules, and permission sets. Every security control that normally applies inside the org must be replicated in the extraction pipeline or replaced by an equivalent external control. Key security requirements:

- **Data classification before extraction.** Every field must be classified as safe, pseudonymize, scrub, or NER-required before the pipeline is designed. Classification drives SOQL field projection (omit scrub fields) and in-process transformations (pseudonymize and NER).
- **PII must be scrubbed in-process, not deferred to the vector store.** Once a record is transmitted over the network to an external endpoint, it is outside the org security boundary. Scrubbing at the vector store layer is too late — the data has already transited the network in plaintext (or encrypted-in-transit but containing PII in the payload).
- **Connected app credentials must use certificate-based JWT Bearer flow, not username/password.** Username/password OAuth flows embed credentials in pipeline configuration, which may be logged, committed to source control, or exposed in environment variable dumps. JWT Bearer flow uses an asymmetric key pair; the private key never leaves the extraction host.
- **Pseudonym mapping tables are sensitive.** The mapping from HMAC pseudonym to Salesforce record ID is itself PII-adjacent: it enables re-identification of pseudonymized data. The mapping table requires access controls equivalent to the original PII.

Source: [Salesforce Security Guide — Data Security](https://help.salesforce.com/s/articleView?id=sf.security_data_access.htm)

### Performance

Bulk API v2 is the correct performance pattern for large-volume extraction. Key performance design points:

- **Separate download from processing.** Downloading result batches and running embedding model API calls in the same synchronous loop creates head-of-line blocking: embedding rate limits stall result downloads, risking cursor expiry. Download all batches to a local buffer first; process from the buffer.
- **Batch embedding API calls.** Most embedding APIs (OpenAI, Cohere, AWS Bedrock) support batch requests. Sending individual chunks as single API calls wastes network round-trip time. Batch at the maximum allowed size per request (e.g., OpenAI Embeddings API: 2048 input texts per request for text-embedding-3-small).
- **Upsert in bulk to the vector store.** Vector stores (Pinecone, pgvector, Weaviate) support batch upsert operations. Single-document upserts at high volume create write amplification and connection pool exhaustion.

### Scalability

Extraction pipelines must be designed for data volumes that grow over time, not just current state:

- **Partition large full-load jobs by date range or record ID range.** A Bulk API v2 query job for an object with 50 million records may take hours and consume the full daily byte quota. Partition by `CreatedDate` year or by the first character of the record ID to spread the load across multiple job submissions and multiple days.
- **Incremental extraction scales better than full loads.** Above approximately 5 million records per object, full nightly loads become impractical. Design the pipeline for incremental extraction from the start, with a periodic full reconciliation (e.g., monthly) to catch any records missed by watermark drift.
- **Chunk count grows faster than record count.** A 1-million-record extraction with an average of 5 chunks per record produces 5 million vectors. Vector stores have index size limits and per-query latency characteristics that degrade at high vector counts. Plan the index capacity with the chunking multiplier accounted for.

### Reliability

Extraction pipelines are long-running asynchronous jobs. Reliability requires explicit failure handling:

- **Idempotent upserts.** Every vector store write must be idempotent: re-running the pipeline for the same time window must produce the same result, not duplicate vectors. Use composite document IDs (`record_id + "_chunk_" + chunk_index`) as upsert keys.
- **Watermark must advance only on confirmed write.** If the pipeline advances the `SystemModstamp` watermark before the vector store write is confirmed, a crash between watermark advance and write completion causes a silent data gap — records changed in that window will never be re-extracted.
- **CDC event replay window is 3 days.** Design for graceful recovery from outages shorter than 72 hours via Bulk API v2 incremental re-extraction. Design a runbook for the >72-hour outage scenario (typically: run a bounded full load for the affected time window).

### Operational Excellence

- **Structured logging with scrubbing audit records.** Each pipeline run should produce a structured log including: job ID, records extracted, chunks produced, entities scrubbed per field (from NER), watermark before and after, duration per phase. This log is both operational visibility and compliance evidence.
- **Alerting on unexpected scrubbing zeros.** If a NER scrubber reports zero entities detected in a `Description` field that historically averages 2.3 entities per record, it likely indicates the scrubber silently failed (e.g., model not loaded, regex not applied). Alert on statistically anomalous zero-entity rates.
- **GDPR erasure runbook must be tested before go-live.** The Right-to-Erasure procedure (look up pseudonym from mapping table, delete vectors by `record_id` metadata filter, confirm deletion count) must be exercised in a staging environment before the pipeline is promoted to production. Discovering the erasure procedure is broken after the first erasure request is a compliance incident.

---

## Architectural Tradeoffs

### Platform-Native (Data Cloud + Einstein) vs. External Pipeline

The fundamental choice this skill represents is: use Salesforce's native AI infrastructure (Data Cloud vector search, Einstein Trust Layer, Agentforce grounding) or build and operate an external pipeline. The tradeoffs:

| Dimension | Platform-Native | External Pipeline |
|---|---|---|
| Security | Trust Layer enforces zero-retention, masking, audit | Must be reimplemented by the pipeline team |
| PII scrubbing | Automatic via Trust Layer field classification | Must be explicitly implemented in the pipeline |
| Ops burden | Managed service; no infra to operate | Team owns extraction host, embedding infra, vector store |
| Cost | Data Cloud licensing (can be significant) | External API costs (embedding, vector store) |
| Flexibility | Constrained to Salesforce's supported models and index config | Any embedding model, any vector store, any chunking strategy |
| Vendor lock-in | High — deeply integrated with Salesforce platform | Low — pipeline is portable to any CRM or data source |

Choose the external pipeline approach when: (a) the team has an existing external AI platform that predates Agentforce; (b) the required embedding model is not available in Model Builder; (c) the team needs to combine Salesforce data with non-Salesforce sources in the same vector index; or (d) cost constraints make Data Cloud licensing impractical.

### Full Load vs. Incremental Extraction

Full load is simpler to implement and guarantees completeness. Incremental extraction with a `SystemModstamp` watermark is more efficient but requires durable watermark state management, automation-churn awareness, and a separate mechanism (CDC) for hard-delete propagation. The right choice depends on data volume and freshness requirements; the recommended decision table is in SKILL.md.

---

## Anti-Patterns

1. **Scrubbing PII at the Vector Store Layer, Not at the API Boundary** — Some teams implement PII scrubbing as a post-processing step: they write raw (PII-containing) chunks to the vector store and then update or filter them. This is wrong for two reasons: the PII-containing record has already transited the network to the external service, and the external service's ingestion logs may have captured the raw content. Scrubbing must occur in-process, after the Bulk API result is decoded and before any outbound network call. This is non-negotiable.

2. **Using the Same Connected App for Extraction That Is Used for User-Facing Integrations** — Extraction pipelines can consume significant API quota, especially during initial full loads. Using a shared connected app means quota consumption by the extraction pipeline appears in the same API usage bucket as user-facing integrations. If the extraction pipeline hits limits, it causes failures in unrelated integrations. Create a dedicated connected app for the extraction pipeline with its own OAuth credentials and monitor its usage independently.

3. **Treating `LastModifiedDate` as Equivalent to `SystemModstamp` for Watermarks** — As documented in the Gotchas file, `LastModifiedDate` can be frozen by import operations. Pipelines built on `LastModifiedDate` watermarks will silently miss records updated by Data Loader imports. Always use `SystemModstamp`.

---

## Official Sources Used

- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_data_access.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
