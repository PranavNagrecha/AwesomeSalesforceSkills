---
name: vector-database-management
description: "Use this skill to design, configure, and maintain vector indexes in Salesforce Data Cloud via the Setup UI. Covers chunking strategy selection, index refresh mode, PII field exclusion, and index rebuild workflows. Trigger keywords: vector index, Data Cloud vector database, chunking strategy, index refresh mode, search index rebuild, embedding model selection, create a search index, choose vector or hybrid search. NOT for developer-facing retrieval APIs, Apex vector search queries, or SOQL-based retrieval - use agentforce/data-cloud-vector-search-dev."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "vector index returning irrelevant results or poor retrieval precision in Agentforce"
  - "how to configure chunking strategy for Data Cloud vector search"
  - "vector index is stale after data updates — how to enable continuous refresh"
  - "create a Data Cloud search index for our knowledge articles"
  - "change the chunking strategy on an existing Data Cloud search index"
  - "choose between a vector and a hybrid search index in Data Cloud"
tags:
  - vector-database-management
  - data-cloud
  - vector-search
  - agentforce
  - embeddings
  - chunking
inputs:
  - "Data Model Objects (DMOs) or Unified Data Layer Objects (UDLOs) containing text to index"
  - "Agentforce or search use case driving retrieval requirements (query length, expected precision)"
  - "PII field taxonomy for the org"
  - "Data Stream refresh mode and ingestion frequency"
outputs:
  - "Vector index configuration decisions (chunking strategy, chunk size, overlap)"
  - "Index refresh mode recommendation (batch vs continuous)"
  - "PII field exclusion list for the index"
  - "Rebuild runbook when chunking strategy or embedding model must change"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Vector Database Management

This skill covers creating, tuning, and maintaining Data Cloud search indexes (the vector store behind Agentforce and Prompt Builder retrieval) through the Data Cloud UI: setup mode, chunking, embedding model, filter fields, freshness, cost, and rebuilds. The 262 Data Cloud guide calls the object a "search index configuration"; this skill uses "search index" and "vector index" for the same thing.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which data space and which DMO or unstructured DMO (UDMO) holds the text? A search index is defined in a data space and tied to one object. A DMO mapped from external data lake objects cannot be selected.
- How many search indexes already exist? The limit is 10 per Data Cloud instance.
- Which language is the content in? Max tokens and the embedding model choice depend on it.
- Which fields will users filter on (category, product, region, status)? Up to 10 filter fields, chosen at setup.
- Plan the chunking strategy and embedding model before creating the index. After creation you can add fields or file extensions; other settings are view-only.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is the content in English, another Latin-script language, or a non-Latin language?" | Max tokens default to 512, and Data Cloud approximates tokens by words (Latin) or punctuation (non-Latin); non-Latin chunks can exceed the limit and lose text | Embedding model (E5-Large V2 or Multilingual E5-Large) and a max-token setting below 512 where needed | Chunks that are fully embedded instead of silently truncated |
| "Will queries use product codes, error numbers, or other exact terms?" | Easy Setup builds a hybrid index; vector-only search lacks domain vocabulary | Hybrid vs vector-only decision | Exact-term questions that still find the right passage |
| "What will retrievers filter on?" | Filter fields are chosen at setup (up to 10, 1:1 or N:1 relationships), and only defined filter fields can be used by retrievers | The filter field list | Retrievers scoped to the right subset without rebuilding |
| "Which fields hold personal or regulated data?" | Every field you chunk is copied into the chunk DMO and embedded | A field list that excludes those fields | No personal data sitting in a chunk DMO that the retriever can return |
| "How fresh must answers be, and how is the source data stream refreshed?" | A Ready index processes source changes incrementally, but only after the data stream ingests them; Full Refresh replaces all data each cycle | The data stream refresh mode and schedule | Freshness that matches the business need without reprocessing the whole corpus |
| "How many vectors will this index hold, and how often will it be queried?" | Data Queries billing for vector search counts the number of vectors in the index | A cost estimate per query volume | No surprise credit consumption after go-live |

What a proper configuration adds over clicking Easy Setup and moving on: the chunking and model fit the content, filter fields exist before retrievers need them, sensitive fields are kept out, and the team knows what a rebuild or a query costs.

---

## Core Concepts

### What a search index creates

Creating a search index configuration creates two Semantic DMOs: a chunk DMO (`Chunk__c`, `ChunkSequenceNumber__c`, source references) and an index DMO (`RecordId__c`, `VectorEmbedding__c`). It also creates a default retriever that cannot be customized; custom retrievers are built in Einstein Studio.

### Easy Setup vs Advanced Setup

| Setting | Easy Setup | Advanced Setup |
|---|---|---|
| Chunking strategy | Passage extraction (default) | Choose per field or file type; optional prepend fields |
| Embedding model | E5-Large V2 | E5-Large V2, Multilingual E5-Large, or Whisper-Large-V3 (as listed in the Search Index Reference) |
| Search type | Hybrid | Vector or hybrid, chosen on the Select Source Object page; hybrid adds ranking factors such as recency or popularity |
| Filter fields | Not part of the Easy Setup steps | Up to 10 |
| Transcription (audio, video) | Not part of the Easy Setup steps | Default transcription model, optional timestamps |

### Chunking is token-based

Data Cloud splits content into sentences, merges sentences up to the max-token setting (default 512), and embeds each chunk. Semantic-based passage extraction uses HTML structure (headings, lists, bold subheadings) as boundaries and works best for HTML; PDF results depend on how the text is encoded. Conversation-based chunking splits transcripts by speaker. Prepend fields add context such as a title to every chunk. UNVERIFIED (2026-10-03): a configurable chunk overlap setting; the 262 Data Cloud guide does not describe one.

### What you can change later

Edit lets you add fields (DMO) or file extensions (UDMO). Other settings, including chunking strategy and embedding model, are view-only. Changing them means a new index. Rebuild re-runs the full index for a configuration that did not process correctly.

### Freshness

Index status moves Submitted, In-progress, Ready, or Failed. In Ready, the indexing job runs incrementally on changes in the source object. The source object is fed by a data stream whose refresh mode is Incremental, Upsert, or Full Refresh; Full Refresh deletes and replaces all data each cycle.

### Cost

Unstructured Data Processed is billed once per file across transcription, chunking, and vectorization, and costs the same for vector and hybrid indexes. Data Queries for vector search count the number of vectors in the search index.

---

## Common Patterns

### Replace an index whose chunking does not fit

1. Record the current configuration: data space, object, fields, chunking strategy, max tokens, embedding model, filter fields.
2. Create a second index with Advanced Setup and the new settings (count it against the 10-index limit).
3. Wait for Ready, then compare results with the validation queries in `references/examples.md`.
4. Point custom retrievers at the new index and activate the new retriever versions.
5. Delete the old index. Deletion is blocked while any retriever references it.

### Keep an index fresh without reprocessing everything

Use Incremental (or Upsert for file connectors) on the source data stream instead of Full Refresh, and set the refresh schedule to the freshness the use case needs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Queries mix natural language and exact codes | Hybrid index | Keyword search covers vocabulary that vector search misses |
| Non-English or mixed-language corpus | Multilingual E5-Large, max tokens below 512 for non-Latin text | Token approximation differs by script |
| Poor results on long HTML articles | Passage extraction plus a title prepend field | Uses document structure and adds context |
| Need to change chunking or the embedding model | Build a new index in parallel, then cut over | Those settings are view-only after creation |
| Index stuck in Failed | Rebuild from the configuration page | Rebuild re-runs the full index |
| Source data stream uses Full Refresh on a large corpus | Switch to Incremental or Upsert where the connector allows | Full Refresh replaces all data each cycle |
| Fields contain personal data | Leave them out of the chunked fields | Chunked text is stored in the chunk DMO |

---

## Recommended Workflow

1. **Scope.** Record the data space, object, language, query style, filter needs, and expected query volume in `templates/vector-database-management-template.md`.
2. **Choose fields.** Pick text fields to chunk and exclude personal or regulated fields; pick up to 10 filter fields.
3. **Choose setup and model.** Easy Setup for a quick hybrid index on English content; Advanced Setup for language, max tokens, prepend fields, or filters.
4. **Create and wait for Ready.** Watch the status; use Rebuild if it fails.
5. **Validate.** Run the `vector_search` or `hybrid_search` queries in `references/examples.md` against representative questions and inspect the returned chunks and scores.
6. **Set freshness and cost guardrails.** Confirm the data stream refresh mode and schedule; estimate query cost from the vector count.
7. **Record the configuration.** Keep the template current and, where the index must move between orgs, add it to a data kit.

---

## Review Checklist

- [ ] Data space and source object recorded; object is not mapped from external DLOs
- [ ] Index count stays within 10 per Data Cloud instance
- [ ] Personal and regulated fields are not chunked
- [ ] Language, embedding model, and max tokens fit the content
- [ ] Filter fields defined before retrievers need them
- [ ] Index status is Ready before retrievers point at it
- [ ] Data stream refresh mode and schedule match the freshness need
- [ ] Configuration recorded; replacement plan uses a parallel index

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The two that cause the most rework: chunking strategy and embedding model are view-only after creation, and an index cannot be deleted while a retriever still references it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search index configuration record | Data space, object, fields, chunking, max tokens, model, search type, filter fields |
| Validation query set | `vector_search` or `hybrid_search` queries with expected chunks |
| Freshness and cost note | Data stream refresh mode, schedule, and vector-count query cost |
| Data kit entry | When the index must be deployed to another org |

---

## Related Skills

- `agentforce/data-cloud-vector-search-dev`: developer lifecycle for querying search indexes from code and retrieval APIs
- `agentforce/rag-patterns-in-salesforce`: retrieval-augmented generation design on top of the index
- `agentforce/data-cloud-grounding-for-agentforce`: grounding agents and prompts in Data Cloud data
