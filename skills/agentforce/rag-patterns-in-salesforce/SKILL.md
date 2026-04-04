---
name: rag-patterns-in-salesforce
description: "Use this skill when grounding Agentforce agents with retrieved knowledge using Data Cloud vector search, configuring vector search indexes, selecting chunking and embedding strategies, or controlling how retrieved context flows through the Einstein Trust Layer into prompts. NOT for Data Cloud data model setup (use a Data Cloud skill), NOT for Agentforce agent creation or topic design (use agentforce-agent-creation or agent-topic-design), and NOT for BYO LLM configuration (use model-builder-and-byollm)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I ground my Agentforce agent with company knowledge articles or documents?"
  - "My agent is hallucinating answers that should come from internal content — how do I connect it to a knowledge base?"
  - "How do I set up a Data Cloud vector search index for RAG with Einstein Copilot?"
  - "What chunking strategy should I use for Data Cloud vector embeddings?"
  - "How does the Einstein Trust Layer control what retrieved context reaches the LLM?"
  - "Agent gives generic answers instead of using our product documentation — how do I fix RAG grounding?"
tags:
  - rag
  - data-cloud
  - vector-search
  - agentforce
  - einstein-trust-layer
  - prompt-grounding
inputs:
  - "Data Cloud org with Data Cloud Vector Search enabled (requires Data Cloud Starter or higher)"
  - "Source content: Salesforce Knowledge articles, Data Cloud DMOs, external documents ingested via Data Cloud connector"
  - "Agentforce agent or Einstein Copilot to which grounding will be attached"
  - "Embedding model choice (Salesforce-managed or BYO via Model Builder)"
  - "Desired chunk size, overlap, and retrieval top-K values"
outputs:
  - "Configured Data Cloud vector search index with chosen embedding model and chunking settings"
  - "Retriever configuration connecting the agent topic or prompt template to the vector index"
  - "Grounding policy in the Einstein Trust Layer specifying which indexes are accessible per agent"
  - "Validated end-to-end RAG flow: source content → chunked embeddings → semantic retrieval → grounded prompt → LLM response"
  - "Decision record documenting chunk size, overlap, top-K, and embedding model rationale"
dependencies:
  - prompt-builder-templates
  - einstein-trust-layer
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# RAG Patterns in Salesforce

This skill activates when an Agentforce agent or Einstein Copilot needs to retrieve and incorporate content from a grounded knowledge source at inference time using Data Cloud vector search. It covers the full RAG pipeline: ingesting source content into Data Cloud, configuring vector indexes and embedding models, connecting a retriever to an agent or prompt template, and enforcing access controls through the Einstein Trust Layer.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Data Cloud is provisioned and that the **Data Cloud Vector Search** feature is enabled in the org. Vector search is not available in all Data Cloud SKUs — it requires at least the Data Cloud Starter license with the Vector Search add-on enabled.
- Identify the source content type: Salesforce Knowledge, a Data Cloud Data Model Object (DMO), or an external file store ingested via a Data Cloud connector. The source type determines which ingestion path and field mappings apply.
- Understand the agent's latency budget. RAG adds a retrieval round-trip before the LLM call. If the agent is customer-facing with a strict SLA, chunk count and top-K directly affect response time.
- Clarify data residency and sensitivity classification. The Einstein Trust Layer controls which vector indexes an agent can query, and retrieved chunks are subject to the same zero-retention and masking policies as the rest of the prompt payload.

---

## Core Concepts

### 1. Data Cloud Vector Search Index

A **vector search index** in Data Cloud stores dense embedding vectors alongside source text chunks. When a retrieval query arrives, Data Cloud computes the query embedding, runs approximate nearest-neighbor (ANN) search against the index, and returns the top-K most semantically similar chunks.

Configuration options (set at index creation):
- **Embedding model** — Salesforce provides a built-in embedding model; custom models can be registered via Model Builder.
- **Chunk size** — the maximum token length of each chunk written to the index. Smaller chunks improve precision but increase total vector count and search latency.
- **Chunk overlap** — the number of tokens shared between adjacent chunks to preserve context across boundaries. Typical production values are 10–20% of chunk size.
- **Index refresh cadence** — batch (scheduled) or near-real-time, depending on the underlying Data Stream configuration.

Source: [Data Cloud Vector Search](https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search.htm)

### 2. Knowledge Grounding and the Retriever

**Grounding** is the mechanism by which Agentforce agents receive contextually relevant documents before generating a response. A **retriever** is the platform-managed component that bridges an agent topic or prompt template with a vector search index.

At runtime:
1. The agent framework extracts a semantic query from the user turn (or uses the full user message).
2. The retriever calls the configured Data Cloud vector index with that query.
3. Top-K chunks are returned and injected into the prompt as grounding context before the LLM call.

The retriever is configured inside a **Grounding** record linked to the agent topic or directly to a Prompt Template. It specifies which vector index to query, the top-K value, and any metadata filters to narrow results (e.g., filter by `product_line` field on the source DMO).

Source: [Einstein Copilot Grounding](https://help.salesforce.com/s/articleView?id=sf.einstein_copilot_grounding.htm)

### 3. Einstein Trust Layer Grounding Controls

Retrieved chunks pass through the Einstein Trust Layer before reaching the LLM. The Trust Layer:
- Enforces **zero data retention** — chunks are not persisted by the LLM provider.
- Applies **data masking** rules to PII fields that may appear in retrieved text.
- Respects **audit logging** so every retrieved chunk and its source record ID is traceable.
- Can **restrict which indexes** an agent is permitted to query based on org-level grounding policies.

Any chunk returned from a vector index that contains a masked field will have that field redacted before it reaches the LLM. This means sensitive fields in the source DMO must be explicitly classified if they should not appear in agent responses.

Source: [Einstein Trust Layer](https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm)

### 4. Data Streams Feeding the Vector Index

The vector index consumes content from a **Data Stream** in Data Cloud. Common source patterns:
- **Salesforce Knowledge** — ingested via the CRM connector; article body and metadata become DMO fields; the `Body` field is the canonical chunk source.
- **File-based content** — PDFs and documents ingested via Salesforce Files or an S3 connector; chunking is applied by Data Cloud during ingest.
- **Custom DMO** — structured data (e.g., product specs, SOPs) modeled as a Data Model Object and then enrolled in a vector index on a selected text field.

The Data Stream refresh cadence controls how quickly new or updated source records appear in the vector index. Near-real-time streaming is available for CRM-connected sources.

---

## Common Patterns

### Pattern 1: Knowledge Article Grounding for a Service Agent

**When to use:** A service or support Agentforce agent needs to answer customer questions using content from Salesforce Knowledge, with answers grounded in the actual article body rather than generated from training data.

**How it works:**
1. Enable the Salesforce Knowledge → Data Cloud CRM connector and create a Data Stream mapping `KnowledgeArticleVersion` to a DMO (e.g., `KnowledgeArticle__dlm`).
2. In Data Cloud, create a vector search index on the `Body__c` field of that DMO. Set chunk size to 512 tokens, overlap to 64 tokens.
3. Select the Salesforce-managed embedding model (no additional license required).
4. In Agentforce Setup, open the agent topic and add a **Grounding** configuration pointing to the new vector index with `top_k = 5`.
5. Test by submitting queries in the Agent Preview panel — the Grounding tab shows which chunks were retrieved per turn.

**Why not the alternative:** Without a retriever, the agent relies entirely on LLM training data, which does not reflect org-specific article content and drifts as articles are updated.

### Pattern 2: Filtered Retrieval by Product Line

**When to use:** A single vector index contains articles or documents for multiple products. An agent should only retrieve chunks relevant to the product the customer is currently discussing, reducing irrelevant context noise in the prompt.

**How it works:**
1. Ensure the source DMO includes a filterable metadata field — e.g., `Product_Line__c` — populated during ingestion.
2. In the Grounding configuration, add a **metadata filter**: `Product_Line__c = '{!topic.product}'` where `{!topic.product}` is a merge field resolved from the agent topic context.
3. The retriever passes the filter to Data Cloud's vector search, which applies it as a pre-filter before ANN ranking — only chunks matching the product line are candidates.

**Why not the alternative:** Relying on semantic similarity alone to implicitly separate product content fails when different product lines use similar vocabulary, causing cross-product chunk contamination.

### Pattern 3: Prompt Template with Explicit Retrieval Merge Fields

**When to use:** A Flex or Field Generation prompt template needs to incorporate retrieved chunks alongside CRM record fields, with precise control over where retrieved context appears in the prompt structure.

**How it works:**
1. In Prompt Builder, create a Flex prompt template.
2. Add a **Grounding** resource that references the vector index.
3. In the template body, insert the merge field `{!grounding.chunks}` at the position where retrieved context should appear (typically before the instruction section).
4. The platform renders each chunk sequentially in the order returned by the retriever, separated by system-defined delimiters.
5. Tune the template instruction to direct the LLM to cite or prefer the grounding content.

**Why not the alternative:** Without explicit merge field placement, the platform inserts chunks at the default position (top of system prompt), which can conflict with role-framing instructions and degrade instruction-following behavior.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Source is Salesforce Knowledge, updated frequently | CRM connector Data Stream + near-real-time refresh | Keeps index current without custom ETL; Knowledge article lifecycle events trigger stream updates |
| Source is a static PDF corpus | File connector ingestion + scheduled batch refresh | Near-real-time is not needed; batch is lower overhead for infrequently changing documents |
| Multi-product agent with a single shared index | Metadata filter in Grounding config | Avoids maintaining separate indexes per product; filter is applied server-side, not post-retrieval |
| High-precision requirement (legal, compliance) | Smaller chunk size (256–384 tokens), higher overlap (20%), lower top-K (3) | Smaller chunks reduce context dilution; lower top-K prevents unrelated chunks from appearing in prompt |
| High-recall requirement (broad knowledge base) | Larger chunk size (512–768 tokens), top-K of 5–10 | Larger chunks carry more context per result; higher top-K ensures coverage of multi-faceted queries |
| PII in source documents | Classify sensitive fields in Data Cloud field taxonomy before indexing | Trust Layer masking operates on classified fields; unclassified PII fields pass through unmasked |
| Scratch org or packaging scenario | Use Data Kits to package Data Cloud vector index configuration | Vector indexes and DMO mappings are packageable via Data Kits in 2GP scratch org development |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking RAG grounding work complete:

- [ ] Data Cloud Vector Search feature is enabled and the embedding model is confirmed as active
- [ ] Source DMO field mapped for chunking contains clean, deduplicated text (HTML stripped from Knowledge article body if applicable)
- [ ] Chunk size and overlap values are documented in the decision record with rationale
- [ ] Grounding configuration specifies the correct vector index, top-K, and any required metadata filters
- [ ] Einstein Trust Layer audit log reviewed for at least one test retrieval turn — confirm chunks are logged and no unexpected masking is dropping needed content
- [ ] Agent preview tested with at least 5 representative queries; retrieved chunks visible in Grounding tab and answers are factually grounded
- [ ] Data residency confirmed: vector index region matches org data residency requirements
- [ ] If packaging: Data Kit includes DMO definition, Data Stream configuration, and vector index settings

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HTML in Knowledge Article Body Pollutes Chunks** — Salesforce Knowledge stores article body as HTML. If the `Body__c` field is mapped directly to the vector index without stripping HTML tags, the embedding model encodes tag markup (`<p>`, `<li>`, `&nbsp;`) as semantic content, degrading similarity scores. Pre-process the field using a Data Cloud formula or transformation to strip HTML before indexing.

2. **Metadata Filters Are Pre-Filters, Not Post-Filters** — Metadata filters in the Grounding config are applied before ANN ranking, not after. If the filter is too restrictive (e.g., an exact match on a field with high cardinality), the candidate set may be empty even when relevant chunks exist, resulting in the agent responding with no grounding context. Use `LIKE` or categorical filters rather than exact-match on free-text fields.

3. **Trust Layer Masking Silently Drops Chunk Content** — If a retrieved chunk contains a field classified as PII under the Trust Layer data masking policy, the masked value is replaced with a placeholder token. The chunk still counts toward top-K but contributes no useful content. This can cause the agent to appear to ignore retrieved documents. Always review the Trust Layer audit log for masking events during QA.

4. **Vector Index Does Not Auto-Refresh on Knowledge Article Publish** — Near-real-time refresh is available for CRM Data Streams but requires explicit configuration of the refresh trigger. By default, new Data Streams use scheduled batch refresh. A newly published Knowledge article will not appear in retrieval results until the next scheduled refresh window unless the Data Stream is configured for continuous mode.

5. **top-K Counts Against Prompt Token Budget** — Each retrieved chunk consumes tokens in the final prompt. With top-K of 10 and a chunk size of 512 tokens, retrieval alone can consume 5,000+ tokens. For models with a 16K context window this is manageable, but for shorter-context configurations it can crowd out conversation history or CRM record context. Monitor total prompt token usage during load testing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Cloud vector search index | The configured index including embedding model, chunk size, and overlap settings; deployable via Data Kit in packaging scenarios |
| Grounding configuration record | The retriever definition linking the agent topic or prompt template to the vector index, including top-K and any metadata filters |
| Decision record | Documents chunk size, overlap, top-K, embedding model choice, and data residency rationale for audit and future tuning |
| Einstein Trust Layer audit log excerpt | QA evidence that retrieval events are logged and masking behavior is as expected |
| Agent preview test results | Minimum 5 representative queries with retrieved chunk traces from the Grounding tab |

---

## Related Skills

- `prompt-builder-templates` — Use alongside this skill to construct the prompt template that receives grounding merge fields; controls how retrieved chunks are positioned in the prompt body
- `einstein-trust-layer` — Governs masking, zero-retention, and audit logging policies that apply to retrieved chunks before they reach the LLM
- `agentforce-agent-creation` — Prerequisite skill for creating the agent topic to which a Grounding configuration is attached
- `model-builder-and-byollm` — Use when the default Salesforce-managed embedding model is insufficient and a custom embedding model must be registered for the vector index
- `agent-topic-design` — Informs how agent topics are scoped so that retrieval is triggered on the right turns and metadata filter merge fields are available at runtime
