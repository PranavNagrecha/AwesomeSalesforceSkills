---
name: vector-database-management
description: "Use this skill to design, configure, and maintain vector indexes in Salesforce Data Cloud via the Setup UI. Covers chunking strategy selection, index refresh mode, PII field exclusion, and index rebuild workflows. Does NOT cover developer-facing retrieval APIs, Apex vector search queries, or SOQL-based retrieval — see skills/agentforce/data-cloud-vector-search-dev for those."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Vector Database Management

This skill activates when a practitioner needs to create, tune, or maintain a Data Cloud vector index through the Salesforce Setup UI. It covers the admin-facing decisions — chunking strategy, refresh cadence, PII exclusion, and rebuild workflows — that determine whether an Agentforce retrieval pipeline returns relevant results.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that a Data Space is configured and that the target DMO or UDLO is active in Data Cloud. Vector indexes cannot be created without a Data Space.
- The most common wrong assumption is that poor retrieval precision is a `topK` tuning problem. It is almost always a chunking strategy mismatch. Identify query length and document structure before touching any index setting.
- Key platform constraints: changing a chunking strategy or swapping an embedding model requires deleting the existing index and rebuilding from scratch. There is no in-place edit. Plan for downtime or a blue/green approach if the index is in production use.

---

## Core Concepts

### Vector Indexes and Embeddings

A vector index stores numerical embeddings generated from text fields on a DMO or UDLO. The index is separate from the source data object — it is a derived artifact that must be explicitly created and maintained. Each index is tied to a specific embedding model; the model cannot be changed without rebuilding the index.

### Chunking Strategy

Chunking controls how source text is split into segments before embedding. Salesforce provides two options in Setup:

- **Easy Setup**: fixed 500-character chunks with no overlap. Fast to configure, appropriate for short, uniform documents.
- **Advanced Setup**: configurable chunk size (recommended range: 200–1500 characters) and overlap percentage (typically 5–20%). Required for longer documents, PDFs, or when retrieval precision matters.

The chunking strategy is set at index creation. It cannot be modified in-place — a strategy change requires deleting the index and rebuilding it.

### Refresh Mode

Vector indexes are fed by a Data Stream. Two refresh modes are available:

- **Batch (default)**: the index updates on a scheduled cadence, which can lag by hours after the source data changes.
- **Continuous**: the index updates near-real-time as records change in the source DMO. Higher Data Cloud credit consumption than batch.

Select continuous refresh only when retrieval freshness is a business requirement. For static or slowly changing corpora (product catalogs, policy documents), batch refresh is sufficient.

### PII Field Exclusion

Any field included in a vector index is embedded and stored in the index. PII fields (names, email addresses, SSNs, health data) should be explicitly excluded from the field list when creating an index. Salesforce does not auto-exclude PII fields — this is an admin responsibility. Failure to exclude PII from the index creates a data governance risk and may violate regulatory requirements.

---

## Common Patterns

### Advanced Chunking Rebuild for Improved Retrieval Precision

**When to use:** Agentforce is returning off-topic or fragmented results. The vector index was created with Easy Setup (500-character fixed chunks). Queries are longer than one or two sentences, or source documents have natural section boundaries.

**How it works:**
1. In Data Cloud Setup, navigate to **Vector Indexes**.
2. Note the current index name, DMO/UDLO, field list, and embedding model.
3. Delete the existing vector index. This removes the index artifact but does not affect source data.
4. Create a new vector index on the same DMO/UDLO using **Advanced Setup**.
5. Set chunk size to match average query length plus context (800–1000 characters is a common starting point for product documentation).
6. Set overlap to 10% of chunk size to preserve context at chunk boundaries.
7. Save and allow the index to build. Monitor index status in Setup until it shows Active.
8. Test retrieval precision with representative queries before re-enabling production traffic.

**Why not the alternative:** Increasing `topK` returns more candidate chunks but does not fix the root cause. If chunks are too small, the most relevant content is split across multiple chunks, none of which individually scores high enough to rank at the top.

### Continuous Refresh for High-Frequency Source Data

**When to use:** The source DMO is updated frequently (inventory, case data, pricing) and retrieval results must reflect recent changes within minutes rather than hours.

**How it works:**
1. Navigate to the Data Stream that feeds the vector index source DMO.
2. Change the refresh mode from **Batch** to **Continuous**.
3. Save the Data Stream configuration.
4. Monitor Data Cloud credit consumption after enabling — continuous mode has higher per-update credit cost than batch.
5. Set a credit consumption alert in Data Cloud Setup if the DMO update frequency is unpredictable.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Poor retrieval precision, queries are longer than one sentence | Rebuild index with Advanced Setup, increase chunk size and add overlap | Chunking strategy mismatch is the root cause; topK is not the fix |
| Embedding model must be changed (e.g., moving to a higher-quality model) | Delete index, update embedding model selection, rebuild | Model change always requires full rebuild; no in-place migration path |
| Source DMO updated hourly or more frequently and freshness matters | Enable continuous refresh on the Data Stream | Batch default can lag hours; continuous keeps index near-real-time |
| Source corpus is static (policy docs, product catalog updated weekly) | Keep batch refresh | Continuous mode consumes more credits without meaningful freshness benefit |
| Index includes fields with PII (names, emails, health data) | Remove PII fields from index field list before creation | Embedded PII in vector store is a data governance and regulatory risk |
| Chunking strategy needs to change on a live production index | Delete index, configure new strategy, rebuild, test, then restore production routing | In-place strategy change is not supported by the platform |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather context**: Identify the source DMO or UDLO, the use case (Agentforce knowledge base, search, classification), typical query length, and current index configuration if one exists.
2. **Audit field list for PII**: Review the fields selected for indexing against the org's PII taxonomy. Remove any sensitive fields before creating or rebuilding the index.
3. **Select chunking strategy**: If source documents are short and uniform, Easy Setup (500-char fixed) is acceptable. For longer documents or when retrieval precision matters, use Advanced Setup with chunk size tuned to query length and 5–15% overlap.
4. **Create or rebuild the index**: In Data Cloud Setup > Vector Indexes, create the index with the selected configuration. If an index already exists with the wrong strategy, delete it first, then create the new one.
5. **Configure refresh mode**: On the Data Stream feeding the DMO, set batch or continuous refresh based on required freshness. Monitor credit consumption after enabling continuous mode.
6. **Validate retrieval precision**: After the index reaches Active status, run representative test queries. Verify that top results are relevant. If precision is still poor, revisit chunk size and overlap rather than adjusting topK.
7. **Document rebuild runbook**: Record the index configuration (chunk size, overlap, embedding model, field list, refresh mode) in a runbook. Any future change to chunking strategy or embedding model will require a full rebuild — the runbook minimizes downtime.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Source DMO or UDLO is active in Data Cloud and a Data Space is configured
- [ ] PII fields are excluded from the vector index field list
- [ ] Chunking strategy matches the query length and document structure of the use case
- [ ] Refresh mode is set appropriately (batch for static corpora, continuous for high-frequency updates)
- [ ] Index status is Active before routing production traffic to it
- [ ] Rebuild runbook documents chunk size, overlap, embedding model, field list, and refresh mode

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Chunking strategy is immutable after index creation** — There is no in-place edit for chunking strategy or chunk size. If you need to change either, you must delete the entire index and rebuild it. This causes a gap in retrieval availability unless a blue/green approach (build new index, validate, reroute) is planned in advance.
2. **Embedding model change requires full index rebuild** — Switching the embedding model (e.g., upgrading to a higher-quality or domain-specific model) is not an incremental operation. The entire index must be deleted and rebuilt from scratch. Plan for rebuild time proportional to corpus size.
3. **Continuous refresh has meaningfully higher credit consumption** — Continuous mode triggers an embedding and index update for every source record change, not just on a schedule. On high-volume DMOs this can multiply Data Cloud credit usage. Always set a consumption alert before enabling continuous mode in production.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Vector index configuration record | Setup UI record specifying DMO/UDLO, field list, chunking strategy, chunk size, overlap, and embedding model |
| Data Stream refresh mode setting | Batch or continuous refresh configured on the Data Stream feeding the source DMO |
| PII exclusion list | Documented list of fields excluded from the index for data governance compliance |
| Rebuild runbook | Step-by-step record of the index configuration and rebuild procedure for future strategy or model changes |

---

## Related Skills

- skills/agentforce/data-cloud-vector-search-dev — developer lifecycle for querying vector indexes via Apex and retrieval APIs; use alongside this skill when building end-to-end Agentforce pipelines
