---
name: sf-to-llm-data-pipelines
description: "Use this skill when extracting Salesforce data for consumption by external LLMs or vector stores outside the Salesforce ecosystem — covering Bulk API v2 extraction patterns, PII scrubbing before transmission, chunking and embedding pipelines that run in external infrastructure, and non-Data-Cloud vector store ingestion (Pinecone, pgvector, Weaviate, OpenSearch). Trigger keywords: export Salesforce data to external LLM, Bulk API extract for embeddings, send Salesforce records to OpenAI, pipe Salesforce data to Pinecone, PII scrubbing before LLM, external vector store ingestion. NOT for Data Cloud vector search or grounding within Salesforce (use rag-patterns-in-salesforce), NOT for Data Cloud data model or harmonized schema design (use ai-ready-data-architecture), NOT for Agentforce agent creation or topic design (use agentforce-agent-creation), NOT for BYO LLM registration inside Salesforce (use model-builder-and-byollm)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I export Salesforce records to an external vector database for our own LLM pipeline?"
  - "We are building a RAG system outside Salesforce and need to pull data from our org via Bulk API — what is the right approach?"
  - "How do I scrub PII from Salesforce data before sending it to OpenAI or another external embedding model?"
  - "Our team wants to sync Salesforce Knowledge articles to Pinecone nightly — what extraction and chunking pipeline should we build?"
  - "We need incremental extraction of Salesforce data changes for an external ML pipeline using the API — what is the recommended pattern?"
tags:
  - bulk-api-v2
  - external-llm
  - pii-scrubbing
  - vector-store
  - data-extraction
  - embedding-pipeline
  - agentforce
  - integration
inputs:
  - "Target objects and fields to extract (object API names, field API names)"
  - "External LLM or vector store endpoint and credentials (e.g., OpenAI Embeddings API, Pinecone index)"
  - "PII classification for each extracted field (what must be scrubbed or pseudonymized)"
  - "Data volume estimate (record count, field count, average record size)"
  - "Extraction cadence: full load vs incremental delta extraction"
  - "Salesforce connected app credentials for Bulk API v2 OAuth flow"
outputs:
  - "Bulk API v2 query job configuration (SOQL, content type, operation parameters)"
  - "PII scrubbing specification documenting field-level treatment (omit, mask, pseudonymize)"
  - "Chunking and embedding pipeline design (chunk size, overlap, embedding model choice)"
  - "External vector store ingestion schema (document ID, chunk text, metadata fields)"
  - "Incremental extraction strategy using SystemModstamp or a CDC channel"
  - "Monitoring and error handling runbook for the extraction pipeline"
dependencies:
  - einstein-trust-layer
  - rag-patterns-in-salesforce
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Salesforce-to-External-LLM Data Pipelines

This skill activates when a team needs to extract Salesforce data and route it through an external pipeline — outside the Salesforce Einstein platform — to feed an LLM or populate a vector store they own and operate. It covers the Bulk API v2 extraction layer, PII scrubbing requirements before data leaves the org boundary, chunking and embedding pipelines built on external infrastructure, and ingestion schemas for non-Data-Cloud vector stores. This is the skill for teams that have chosen to build or run their own AI infrastructure rather than use Salesforce's native Data Cloud vector search.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm data residency and contractual constraints.** Salesforce data leaving the org boundary is subject to the customer's Salesforce Master Subscription Agreement (MSA), any applicable data processing addenda, and jurisdiction-specific regulations (GDPR, CCPA, HIPAA). Verify whether a Data Processing Agreement (DPA) is in place with the external LLM provider before designing the pipeline. This is not optional; it is a legal precondition.
- **Identify every field that contains PII, quasi-identifiers, or regulated data.** Common Salesforce fields that require scrubbing include `Email`, `Phone`, `MobilePhone`, `Name` on Contact and Lead, `SSN__c` or similar custom fields, any field in a Health Cloud or Financial Services Cloud org that maps to PHI or MNPI. PII scrubbing must be applied before the record leaves the Salesforce API response — scrubbing at the vector store layer is too late.
- **Determine the extraction pattern: full load or incremental delta.** Full loads are simpler to implement but become impractical above ~5 million records per object due to Bulk API v2 job duration limits. Incremental extraction requires a reliable high-watermark field (`SystemModstamp` or a custom `LastSyncedAt__c` field) and a strategy for detecting hard deletes separately.
- **Establish the volume and velocity envelope.** Bulk API v2 supports up to 100 million records per 24-hour rolling window per connected app. A single Bulk API v2 query job supports up to 100 MB of compressed CSV output per result batch. Large-volume orgs may require job partitioning by date range or by a high-cardinality indexed field.

---

## Core Concepts

### 1. Bulk API v2 Query Jobs

Bulk API v2 is the correct API for extracting large volumes of Salesforce records for external pipelines. It is asynchronous: the caller submits a SOQL query, Salesforce processes it in the background, and the caller polls for completion before downloading result sets as paginated CSV batches.

Key behaviors:
- **Content type is `CSV` only for query jobs** — unlike ingest jobs which support JSON and XML, Bulk API v2 query results are always returned as RFC 4180 CSV.
- **Result sets are paginated.** Each call to the results endpoint returns up to `maxRecords` rows (default 50,000). Callers must follow the `Sfdclocator` cursor header to retrieve subsequent pages until the response body is empty.
- **Job state machine:** `UploadComplete` → `InProgress` → `JobComplete` (or `Failed` / `Aborted`). Poll the job status endpoint; do not assume completion based on time elapsed.
- **Query jobs do not consume API request limits in the standard sense** — they consume Bulk API v2 daily byte limits, not the per-org 24-hour API call limit that REST and SOAP calls consume.
- **SOQL in Bulk API v2 query jobs cannot use relationship traversal in the SELECT clause** (e.g., `SELECT Account.Name FROM Contact` is not supported). Pre-join fields must be resolved either by querying parent objects separately and joining client-side, or by using formula fields that denormalize the parent value at the Salesforce schema layer.

Source: [Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm)

### 2. PII Scrubbing Before Transmission

Once a Salesforce record is returned by the API, it exists in the calling process's memory. If the process transmits the record to an external LLM endpoint before removing PII, there is no further enforcement point — the data has left the org boundary. PII scrubbing must therefore be a synchronous step in the extraction pipeline between the Bulk API result decode and any outbound network call.

Scrubbing strategies by field type:
- **Direct identifiers (name, email, phone):** Omit from the SOQL query altogether if not needed by the LLM pipeline. If needed for deduplication, replace with a deterministic pseudonym (e.g., HMAC-SHA256 of the original value keyed with a secret). Do not use MD5 — it is reversible with rainbow tables for common values.
- **Quasi-identifiers (ZIP code, date of birth, job title):** Apply k-anonymity generalization where the field is needed semantically but exact value is not (e.g., truncate ZIP to 3 digits, reduce DOB to birth year).
- **Free-text fields containing incidental PII (case descriptions, notes, chatter):** Apply a named-entity recognition (NER) pass before chunking. Salesforce does not provide an out-of-platform NER service; this must be implemented in the extraction pipeline using an open-source library (e.g., spaCy `en_core_web_sm`) or a privacy-preserving NER endpoint.

Source: [Salesforce Security Guide — Data Security](https://help.salesforce.com/s/articleView?id=sf.security_data_access.htm)

### 3. Chunking and Embedding for External Vector Stores

Text extracted from Salesforce must be chunked and embedded before it can be stored in an external vector store. The chunking strategy depends on the source field type:

- **Structured text (short text areas, picklists concatenated into a document):** Fixed-size chunking with 256–512 tokens per chunk and 10% overlap. Small chunks improve precision for structured fact retrieval.
- **Long-form content (Knowledge article body, case description, rich text):** Recursive character text splitting on semantic boundaries (paragraph breaks, sentence ends) is preferred over fixed-size splitting. This preserves paragraph coherence and reduces mid-sentence chunk boundaries.
- **HTML content (Knowledge article `Body` field, rich text areas):** HTML must be stripped before chunking. The raw HTML of a Salesforce Knowledge article body contains `<p>`, `<ul>`, `<li>`, `&nbsp;`, and embedded image `<img>` tags. Embedding models encode tag markup as semantic tokens, which degrades similarity score fidelity. Use an HTML-to-plain-text library as the first transformation step.

Every chunk stored in the external vector store must carry metadata that enables traceability back to the source Salesforce record: minimally `record_id` (Salesforce 18-character ID), `object_api_name`, `field_api_name`, `chunk_index`, and `last_modified` (from `SystemModstamp`). This metadata supports incremental re-embedding and audit trail requirements.

Source: [Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm)

### 4. Incremental Extraction with SystemModstamp

`SystemModstamp` is a system-maintained field on every Salesforce object that records the last time any field on the record was modified by any user or system process. It is indexed and available in Bulk API v2 SOQL queries, making it the correct high-watermark field for incremental extraction.

Implementation pattern:
1. On the first full extraction, record the pipeline run's start timestamp as the `last_sync` watermark.
2. On subsequent runs, query with `WHERE SystemModstamp >= :last_sync` to retrieve only changed records.
3. Store the watermark durably (e.g., a database row, a file in cloud storage) and update it only after the current batch is successfully ingested into the vector store — never before.
4. Hard deletes are NOT captured by `SystemModstamp` filtering. Use the Salesforce Change Data Capture (CDC) API to subscribe to `ObjectDeleted` events for objects where hard deletes must be propagated to the external vector store.

**Important:** `LastModifiedDate` is user-visible and can be frozen by certain import operations (e.g., Data Loader with `--setbulkheader` disabling trigger logic). `SystemModstamp` is always updated by any modification, including system-initiated changes, and is the reliable choice for ETL watermarks.

Source: [Change Data Capture Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm)

---

## Common Patterns

### Pattern 1: Nightly Full-Extract Knowledge Article Pipeline

**When to use:** A team runs an external RAG system (e.g., using LangChain + Pinecone) and needs a nightly refresh of Salesforce Knowledge article content. Volume is under 500,000 articles. Latency tolerance is same-day freshness.

**How it works:**
1. A scheduled job (e.g., GitHub Actions, AWS Lambda cron) authenticates to Salesforce via OAuth 2.0 JWT Bearer flow using a connected app.
2. Submit a Bulk API v2 query job with SOQL: `SELECT Id, Title, Summary, Body, ArticleNumber, LastPublishedDate, SystemModstamp FROM KnowledgeArticleVersion WHERE PublishStatus = 'Online' AND Language = 'en_US'`.
3. Poll job status every 30 seconds; download result CSV batches using the `Sfdclocator` cursor.
4. For each row: strip HTML from `Body`, split into chunks (512 tokens, 64 token overlap), prepend `Title + ": "` to each chunk for context coherence.
5. Run each chunk through the embedding model (e.g., `text-embedding-3-small` via OpenAI Embeddings API).
6. Upsert vectors into Pinecone using `Id + "_chunk_" + chunk_index` as the document ID, with metadata: `{record_id, article_number, title, last_published_date}`.
7. Delete vectors from Pinecone where `record_id` is no longer present in the current extraction (requires maintaining a prior-run ID set or using Pinecone's metadata filtering to purge stale records).

**Why not the alternative:** Using the REST API with individual record GETs is limited by the per-org API call limit (typically 1–5 million calls/24 hours depending on license count). A 300,000-article org would exhaust a significant fraction of daily API quota on extraction alone. Bulk API v2 is the correct tool for this volume.

### Pattern 2: Incremental Delta Pipeline for Case Data

**When to use:** A team runs a customer-facing chatbot grounded on Salesforce Case resolution notes. Cases are created and resolved continuously; the external vector store must reflect changes within 1 hour. Full nightly extraction is insufficient for the freshness requirement.

**How it works:**
1. Store the last successful extraction timestamp (`last_sync`) in a durable store (e.g., AWS SSM Parameter Store, a PostgreSQL row).
2. On each pipeline run (scheduled every 15–30 minutes): submit a Bulk API v2 query job with SOQL: `SELECT Id, CaseNumber, Subject, Description, Resolution__c, SystemModstamp FROM Case WHERE SystemModstamp >= :last_sync AND Status = 'Closed'`.
3. Apply PII scrubbing: omit `ContactEmail` from the SOQL projection; mask `ContactPhone` if present in `Description` via regex substitution before chunking.
4. Chunk each case record (concatenate `Subject + "\n" + Description + "\n" + Resolution__c`), embed, and upsert.
5. Update `last_sync` to the pipeline run's start timestamp only after successful upsert. If the upsert fails, do not advance the watermark — retry on the next run to avoid losing records.
6. Separately, subscribe to the Case CDC channel (`CaseChangeEvent`) to capture hard-deleted or merged cases and remove their vectors from the external store.

**Why not the alternative:** Streaming via CDC alone is unreliable as a sole extraction mechanism — CDC event replay is limited to 3 days, and a pipeline outage longer than 72 hours causes event gap. Bulk API v2 incremental extraction is the durable backstop; CDC handles deletes and provides a lower-latency supplement.

### Pattern 3: PII-Safe Contact Enrichment for External Personalization Model

**When to use:** A team wants to use Salesforce Contact and Account data to enrich an external personalization model without transmitting PII to the external service. The model needs company, role, and segment data — not individual identity.

**How it works:**
1. Construct the SOQL to project only non-PII fields: `SELECT Id, Account.Industry, Account.AnnualRevenue, Account.NumberOfEmployees, Title, Department, LeadSource, SystemModstamp FROM Contact WHERE ...`.
2. Replace the Salesforce `Id` with a HMAC-SHA256 pseudonym before transmission: `pseudonym = hmac_sha256(secret_key, contact_id)`. Store the mapping table internally for re-identification if needed.
3. Transmit only the pseudonymized record to the external model endpoint. The external model never receives the Salesforce record ID or any direct identifier.
4. When the external model returns a segment score, look up the pseudonym-to-ID mapping table to write the score back to Salesforce via the REST API.

**Why not the alternative:** Omitting the pseudonymization step and transmitting raw Salesforce IDs creates a re-identification path: any party with access to both the external model's input log and Salesforce can join on the raw ID and recover the individual's identity. Pseudonymization severs that linkage at the data-leaving boundary.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Volume under 100K records, freshness tolerance is daily | Bulk API v2 full load nightly | Simplest to operate; full load avoids watermark drift issues |
| Volume over 1M records, freshness tolerance is daily | Bulk API v2 incremental with SystemModstamp watermark | Full load becomes slow and expensive above 1M; incremental scoped to changed records |
| Freshness requirement under 1 hour | Bulk API v2 incremental + CDC event subscription for deletes | Bulk API v2 at short intervals is reliable; CDC fills the hard-delete gap |
| Source field is HTML (Knowledge Body, rich text) | Strip HTML before chunking, not after | Embedding model encodes HTML tags as semantic tokens; must be removed before the text reaches the tokenizer |
| Free-text fields with potential incidental PII (case notes, chatter) | NER-based scrubbing before chunking | Field-level omission is insufficient; PII can appear in any free-text field; NER catches entity mentions |
| External LLM is a third-party SaaS (OpenAI, Anthropic) | Pseudonymize all direct identifiers before transmission | Third-party SaaS providers are not Salesforce sub-processors; PII transmission requires separate DPA |
| Need to detect record deletions in external store | Subscribe to CDC ObjectDeleted events for each object | SystemModstamp watermark only captures modifications; hard deletes leave stale vectors in the external store |
| Org has GDPR Right-to-Erasure obligation | Maintain record_id metadata on every vector chunk | Enables targeted deletion of all chunks for a specific individual across the vector store without full re-index |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Classify fields and confirm legal basis.** For each target object, list every field in scope. Mark each field as: `safe` (no PII), `pseudonymize` (direct identifier needed for join keys), `scrub` (omit from extraction), or `ner-required` (free-text that may contain incidental PII). Confirm that a DPA exists with the external LLM/vector store provider. Do not proceed without this classification.

2. **Design the SOQL projection.** Write the SOQL query omitting all `scrub`-classified fields from the SELECT clause. Add `SystemModstamp` to the SELECT for watermark tracking. Verify the SOQL runs successfully in the Developer Console with a LIMIT 10 sanity check before submitting a bulk job.

3. **Implement the extraction job.** Authenticate via OAuth 2.0 JWT Bearer flow (not username/password). Submit a Bulk API v2 query job. Poll job status until `JobComplete`. Download all result batches using the `Sfdclocator` cursor header; do not assume a single batch contains all results.

4. **Apply PII scrubbing in-process.** Before writing any record to disk or transmitting to an external endpoint: pseudonymize fields marked `pseudonymize`, run NER on fields marked `ner-required` and replace detected entities with placeholder tokens (`[PERSON]`, `[EMAIL]`, `[PHONE]`). Log a scrubbing audit record (field name, entity count detected, timestamp) for compliance evidence.

5. **Chunk and embed.** Strip HTML from rich text fields. Apply the chosen chunking strategy (fixed-size or recursive semantic). For each chunk, construct the metadata envelope: `{record_id_pseudonym, object_api_name, field_api_name, chunk_index, total_chunks, last_modified}`. Submit chunks to the embedding model in batches to stay within rate limits (e.g., OpenAI Embeddings API: 1M tokens/minute for tier-2).

6. **Upsert to the external vector store.** Use the `record_id_pseudonym + "_" + chunk_index` as the upsert key. For incremental runs, the upsert is idempotent — re-embedding a chunk that has not changed is wasteful but not incorrect. Advance the SystemModstamp watermark only after all chunks for the current run are confirmed written.

7. **Validate end-to-end.** Query the external vector store with a representative set of 5+ test queries. Verify that results are traceable back to source Salesforce records via the metadata envelope. Confirm no PII appears in the stored chunk text. Review the scrubbing audit log for unexpected zero-entity counts on fields expected to contain PII (which may indicate the scrubber silently failed).

---

## Review Checklist

Run through these before marking pipeline work complete:

- [ ] Every field in the extraction has a documented PII classification (`safe`, `pseudonymize`, `scrub`, `ner-required`)
- [ ] A DPA or equivalent legal instrument is confirmed with the external LLM/vector store provider
- [ ] SOQL projection contains no `scrub`-classified fields
- [ ] HTML stripping is applied before chunking for all rich text or long text area fields
- [ ] PII pseudonymization is applied in-process before any outbound network call
- [ ] NER scrubbing is applied to all `ner-required` fields; audit log confirms entity detection is non-zero on a test sample
- [ ] Every stored chunk carries a `record_id` (pseudonymized if required) and `last_modified` metadata
- [ ] SystemModstamp watermark is updated only after successful write confirmation
- [ ] CDC subscription is in place for hard-delete propagation if the use case requires it
- [ ] End-to-end test: 5+ queries against the vector store return traceable, PII-free results
- [ ] GDPR Right-to-Erasure deletion procedure is documented and tested (delete by `record_id` metadata filter)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Bulk API v2 Query Jobs Cannot Traverse Relationships in SELECT** — Unlike SOQL in the REST or SOAP APIs, Bulk API v2 query jobs do not support cross-object field references in the SELECT clause (e.g., `SELECT Account.Name FROM Contact`). The job will fail with a `QUERY_TIMEOUT` or `INVALID_FIELD` error at submission. Workaround: use formula fields on the child object to denormalize parent field values at the schema layer, or run separate query jobs per object and join client-side.

2. **`LastModifiedDate` Can Be Frozen by Data Loader Imports** — When records are imported via Data Loader or Bulk API ingest jobs with the `setbulkheader` option disabling update of `LastModifiedDate`, the field is not advanced. `SystemModstamp`, by contrast, is always updated by the platform on any write, including system-initiated ones. Pipeline watermarks built on `LastModifiedDate` will silently miss records imported this way. Always use `SystemModstamp` for ETL watermarks.

3. **Bulk API v2 Result Cursor Expires After 10 Minutes of Inactivity** — After a query job reaches `JobComplete`, the result set cursor (tracked via the `Sfdclocator` response header) expires if not consumed within 10 minutes of the last GET request. If the consumer process pauses between batches — due to rate limiting, downstream backpressure, or a crash — the cursor is lost and the entire job must be re-submitted. Design the consumer to pipeline result downloads without pause, or download all batches to local storage before processing downstream.

4. **Change Data Capture Replay Window Is 3 Days** — CDC event replay (reading past events from the event bus) is limited to a 72-hour window. If the extraction pipeline is offline for more than 3 days, CDC events for that gap are permanently lost. CDC alone is therefore not a reliable extraction mechanism for pipelines with any possibility of extended downtime. Use Bulk API v2 incremental extraction as the primary mechanism and CDC only as a supplement for near-real-time delete propagation.

5. **Knowledge Article Body Returns HTML Even for Plain-Text Content** — `KnowledgeArticleVersion.Body` is a rich text area. Even when an author types plain text, Salesforce's Knowledge editor wraps it in `<p>` tags and applies `&nbsp;` for spacing. Downstream embedding of the raw `Body` field will encode these HTML entities as semantic content. Strip HTML before chunking using a proper HTML parser, not a simple regex — nested tags and malformed markup will cause regex-based stripping to leave residual fragments.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PII classification matrix | Table mapping each extracted field to its scrubbing treatment (`safe`, `pseudonymize`, `scrub`, `ner-required`) and the rationale |
| Bulk API v2 SOQL queries | Validated SOQL queries for each target object with PII fields excluded from the SELECT |
| Extraction pipeline code/config | Implementation of the Bulk API v2 query job, result download, PII scrubbing, chunking, embedding, and vector store upsert |
| Pseudonym mapping table spec | Schema and storage design for the pseudonym-to-Salesforce-ID mapping used for re-identification and Right-to-Erasure |
| Chunking configuration record | Documents chunk size, overlap, HTML stripping policy, and embedding model with rationale |
| Scrubbing audit log | Per-run record of fields scrubbed, entity counts detected by NER, and any anomalies |
| Watermark state store spec | Documents where the SystemModstamp watermark is stored, how it is advanced, and the failure recovery procedure |
| End-to-end test results | 5+ query results against the external vector store with traceability back to source records confirmed |

---

## Related Skills

- `rag-patterns-in-salesforce` — Use instead of this skill when grounding must remain within the Salesforce platform using Data Cloud vector search and the Einstein Trust Layer; use alongside this skill when comparing platform-native vs. external pipeline tradeoffs
- `ai-ready-data-architecture` — Prerequisite for designing the Salesforce-side schema and field quality before extraction; ensures fields being extracted have adequate fill rates, clean text, and correct data types
- `einstein-trust-layer` — Governs what data Salesforce's own AI features can access; provides the policy context that motivates why certain fields must be scrubbed before leaving the platform
- `model-builder-and-byollm` — Use when the goal is to register an external LLM inside Salesforce rather than building an extraction pipeline to feed external infrastructure
- `bulk-api-patterns` — Covers Bulk API v2 ingest, error handling, and job management patterns in depth; complements this skill's extraction-specific guidance
