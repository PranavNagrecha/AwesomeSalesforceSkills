---
name: data-cloud-vector-search-dev
description: "Use this skill when developing Data Cloud vector search capabilities: configuring search indexes, selecting chunking strategies (Easy Setup vs Advanced Setup), generating embeddings via the Salesforce-managed model, calling the Query API with a Data Cloud access token, and wiring retrieval to Agentforce grounding. NOT for Data Cloud admin, data model design, or standard CRM Connected App token management."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "How do I configure a Data Cloud vector search index for my Agentforce agent grounding?"
  - "My RAG retrieval quality is poor and I think the chunking strategy is wrong — how do I tune it?"
  - "How do I call the Data Cloud vector search Query API from an external system or Apex?"
  - "What is the difference between Easy Setup and Advanced Setup for Data Cloud vector search?"
  - "How do I connect a Data 360 vector database search index to an Agentforce grounding configuration?"
tags:
  - Data-Cloud
  - vector-search
  - RAG
  - embeddings
  - Agentforce
  - grounding
  - Data-360
  - Query-API
  - chunking
inputs:
  - "Data Cloud org with Data Cloud Vector Search (Data 360) feature enabled"
  - "Source DMO or Unstructured Data Lake Object with a text field to embed"
  - "Decision on Easy Setup vs Advanced Setup (determines chunking strategy tuning capability)"
  - "Agentforce agent or Prompt Template that will receive retrieved chunks via a Grounding configuration"
  - "Data Cloud Connected App credentials for generating a Data Cloud access token (required for Query API)"
outputs:
  - "Configured Data Cloud vector search index with embedding model, chunking strategy, and refresh settings"
  - "Grounding configuration record linking the agent topic or prompt template to the search index"
  - "Data Cloud access token generation pattern for the Query API"
  - "Decision record documenting chunking strategy choice (Easy vs Advanced), top-K, and embedding model rationale"
  - "Validated end-to-end flow: source text → chunks → embeddings → search index → agent grounding → Einstein Trust Layer"
dependencies:
  - rag-patterns-in-salesforce
  - einstein-trust-layer
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Data Cloud Vector Search Dev

This skill activates when a developer or architect needs to configure, tune, or programmatically interact with Data Cloud vector search (branded as the Data 360 vector database). It covers the full developer lifecycle: enabling the feature, choosing between Easy Setup and Advanced Setup chunking, generating embeddings via the Salesforce-managed model, wiring the search index to Agentforce grounding, and calling the Query API with a dedicated Data Cloud access token. It is distinct from the `rag-patterns-in-salesforce` skill, which covers RAG patterns broadly; this skill goes deeper into the specific platform mechanics a developer must understand to configure and debug the vector search layer correctly.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that **Data Cloud Vector Search** is enabled in the org. Navigate to Data Cloud Setup → Vector Search and verify the feature toggle is on and the Salesforce-managed embedding model shows as active. This feature requires a Data Cloud Starter or higher SKU with the Vector Search add-on.
- Determine whether the practitioner is using **Easy Setup** or **Advanced Setup**. Easy Setup automatically selects chunking parameters and the Salesforce-managed embedding model — chunk size and strategy are not tunable in this mode. Advanced Setup exposes chunking strategy options (fixed-size, paragraph, sentence) and lets you change the embedding model. Misunderstanding this distinction is the most common cause of unexpected retrieval quality.
- Identify the source object type. Data Cloud vector search can index text fields on **Data Model Objects (DMOs)** and on **Unstructured Data Lake Objects**. The ingestion path, field mapping, and refresh cadence differ between the two.
- Confirm that a **Data Cloud Connected App** exists with the correct OAuth scopes if the Query API will be called from outside Salesforce. The Query API requires a Data Cloud access token obtained separately from the standard CRM Connected App token — the two are not interchangeable.
- Clarify the latency and precision requirements. Chunking strategy and top-K directly affect retrieval latency and result relevance. These must be decided before index creation because changing chunking strategy after index creation requires re-indexing.

---

## Core Concepts

### 1. Vector Search Index and the Data 360 Vector Database

Data Cloud's vector search capability is underpinned by the **Data 360 vector database**, which stores dense embedding vectors alongside the source text chunks. At search time, the platform computes the query embedding and performs approximate nearest-neighbor (ANN) search to return the top-K most semantically similar chunks.

The index is created from a source DMO or Unstructured Data Lake Object. Configuration decisions made at index creation time include:

- **Source object and text field** — the field whose content will be chunked and embedded.
- **Embedding model** — the Salesforce-managed model (no additional license or configuration required) or a custom model registered via Model Builder.
- **Chunking strategy** — only exposed in Advanced Setup. Options include fixed-size (by token count), paragraph-based, and sentence-based. Easy Setup auto-selects the strategy.
- **Index refresh cadence** — batch (scheduled) or near-real-time, depending on the underlying Data Stream configuration.

Source: [Data Cloud Vector Search (Salesforce Help)](https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search.htm)

### 2. Easy Setup vs Advanced Setup — The Chunking Control Boundary

**Easy Setup** is the default path for creating a vector search index. It:
- Automatically selects the Salesforce-managed embedding model.
- Automatically determines chunk size and overlap (parameters are not exposed to the user).
- Is the fastest path to a working index but provides no tuning capability.

**Advanced Setup** unlocks:
- Explicit chunking strategy selection (fixed-size, paragraph, sentence).
- Chunk size and overlap parameter inputs.
- Alternative embedding model selection via Model Builder.

A developer who creates an index using Easy Setup and later finds retrieval quality insufficient cannot adjust chunk parameters in-place. The index must be deleted and recreated using Advanced Setup with explicit chunking configuration. This is the single most common source of retrieval quality complaints in early-stage Data Cloud vector search implementations.

Source: [Supported Chunking Strategies (Salesforce Help)](https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search_chunking.htm)

### 3. Query API and Data Cloud Access Token

The **Data Cloud Vector Search Query API** allows external systems (and Apex code calling an external endpoint) to execute semantic searches against a vector index programmatically. Key constraints:

- **Separate access token required.** The Query API accepts a Data Cloud access token, not the standard Salesforce CRM session token or Connected App OAuth token. The Data Cloud token is obtained by posting to the Data Cloud token endpoint (`/services/a360/token`) with the Connected App credentials scoped to the Data Cloud API.
- **Token scope.** The Connected App used for Query API access must include the `cdpapi` scope (or equivalent Data Cloud API permission). A standard CRM Connected App without this scope will be rejected at the token endpoint.
- **Request structure.** Query API calls are REST POST requests to the Data Cloud vector search endpoint, passing the search text (or pre-computed query vector), the index name, top-K, and any metadata filter expressions.

Source: [Search Index Reference — Data Cloud (Salesforce Help)](https://help.salesforce.com/s/articleView?id=sf.data_cloud_vector_search_index_reference.htm); [Data 360 Developer Guide — Features Overview (developer.salesforce.com)](https://developer.salesforce.com/docs/atlas.en-us.salesforce_cdp_api.meta/salesforce_cdp_api/cdp_api_features_overview.htm)

### 4. Grounding Configuration and Einstein Trust Layer

Retrieved chunks flow from the vector search index to the LLM through a **Grounding configuration** record attached to an agent topic or Prompt Template. At inference time:

1. The Agentforce framework extracts a semantic query from the user turn.
2. The platform calls the configured vector index via the Grounding configuration, specifying top-K and any metadata filters.
3. Top-K chunks are returned and injected into the prompt payload.
4. The **Einstein Trust Layer** processes the combined prompt, applying data masking rules to any PII-classified fields present in the retrieved chunks before the payload reaches the LLM.
5. The Trust Layer enforces zero data retention at the LLM provider.

Masking is silent — a chunk containing a masked field still counts toward top-K but contributes a placeholder token instead of the original value. Developers must classify sensitive DMO fields in the Data Cloud field taxonomy before indexing to control masking behavior deliberately.

Source: [Einstein Trust Layer (Salesforce Help)](https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm)

---

## Common Patterns

### Pattern 1: Developer-Tuned Index via Advanced Setup

**When to use:** The initial Easy Setup index produces poor retrieval precision — either chunks are too long and dilute semantic focus, or results are topically scattered. The developer needs to control chunk size and strategy.

**How it works:**
1. Navigate to Data Cloud Setup → Vector Search → existing index → confirm it was created with Easy Setup.
2. Note the source DMO and text field.
3. Delete the existing Easy Setup index (this does not delete the source DMO data).
4. Re-create the index via **Advanced Setup**. Select the chunking strategy appropriate for the content type:
   - Fixed-size (256–512 tokens with 10–20% overlap) for dense technical prose or product documentation.
   - Paragraph-based for knowledge articles where paragraph boundaries carry semantic meaning.
   - Sentence-based for FAQ content where each sentence is an independent answer unit.
5. Select the Salesforce-managed embedding model (or a BYO model via Model Builder if required).
6. Trigger an initial full index build and monitor the index status until it moves to Active.
7. Update the Grounding configuration to reference the rebuilt index and re-test retrieval in the Agent Preview panel.

**Why not the alternative:** Attempting to improve retrieval quality by changing only the top-K value in the Grounding config while leaving an Easy Setup index intact does not address chunking-level problems. Retrieval quality is determined primarily by chunk granularity and embedding quality, not by how many chunks are returned.

### Pattern 2: Query API Call with Data Cloud Access Token

**When to use:** An external integration, middleware service, or Apex callout needs to query the vector search index directly — for example, to build a custom retrieval pipeline outside the Agentforce grounding framework.

**How it works:**

```http
# Step 1: Obtain a Data Cloud access token
POST https://<instance>.salesforce.com/services/a360/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=<Data Cloud Connected App consumer key>
&client_secret=<Data Cloud Connected App consumer secret>

# Response includes:
# { "access_token": "...", "instance_url": "https://<dc-instance>.c360a.salesforce.com", ... }

# Step 2: Call the Vector Search Query API
POST https://<dc-instance>.c360a.salesforce.com/api/v1/vector-search/<index-name>/query
Authorization: Bearer <access_token from step 1>
Content-Type: application/json

{
  "query": "How do I reset my account password?",
  "topK": 5,
  "filter": { "field": "product_line", "operator": "eq", "value": "Commerce Cloud" }
}
```

**Why it works:** The Data Cloud token endpoint is separate from the CRM token endpoint because Data Cloud runs on a different tenant infrastructure. Using a CRM session token against the Data Cloud API endpoint will produce a 401 — the two credential systems do not share session state.

### Pattern 3: Grounding Configuration with Metadata Filter

**When to use:** A single vector index contains documents spanning multiple product lines, departments, or languages. An agent topic should retrieve only chunks relevant to the current user's context (e.g., only documents for the product in the active CRM record).

**How it works:**
1. Ensure the source DMO includes a low-cardinality categorical field that can serve as the filter dimension (e.g., `Product_Line__c`, `Language__c`, `Department__c`).
2. In Agentforce Setup, open the agent topic and navigate to the Grounding configuration.
3. Add a **metadata filter** expression referencing the field: `Product_Line__c = '{!topic.productLine}'` where the merge field resolves from the agent topic context at runtime.
4. Validate the merge field resolution by checking the Agent Preview Grounding tab — if the filter produces zero results, the merge field may be resolving to null or the field value casing may not match the DMO field values exactly.

**Why not the alternative:** Semantic similarity alone does not reliably separate multi-product content when products share overlapping vocabulary. A product knowledge base spanning Commerce Cloud and Service Cloud will produce cross-product contamination without an explicit metadata filter.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time index creation, no precision requirements yet | Easy Setup | Fastest path; acceptable for proof-of-concept work |
| Retrieval precision is inadequate after Easy Setup | Delete and rebuild with Advanced Setup | Chunk parameters cannot be changed on an existing Easy Setup index |
| Content type is structured FAQ (one Q&A per entry) | Advanced Setup + sentence-based chunking | Each sentence is an independent retrieval unit; fixed-size chunking may split Q from A |
| Content type is long-form technical documentation | Advanced Setup + fixed-size 512 tokens, 10% overlap | Fixed-size chunks maintain predictable token counts for prompt budget management |
| External system needs to query the index | Data Cloud Query API + Data Cloud access token | Query API is the only supported programmatic access path; standard CRM tokens are rejected |
| Source DMO contains PII fields (e.g., customer names in case descriptions) | Classify PII fields in Data Cloud field taxonomy before indexing | Trust Layer masking applies post-retrieval; unclassified PII passes through to the LLM prompt |
| Multi-lingual knowledge base | Separate indexes per language, metadata filter in Grounding | The Salesforce-managed embedding model is multilingual but filtering by language prevents cross-language rank contamination |
| Packaging for scratch org or ISV distribution | Include vector index in Data Kit with DMO and Data Stream definitions | Vector search index configuration is a Data Kit component; it cannot be deployed via standard mdapi |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on Data Cloud vector search development:

1. **Confirm prerequisites** — verify that Data Cloud Vector Search is enabled, the source DMO or Unstructured Data Lake Object is populated, and a Data Cloud Connected App with `cdpapi` scope exists if the Query API will be used.
2. **Decide on setup path** — determine whether Easy Setup or Advanced Setup is appropriate. If retrieval precision matters or content structure warrants a specific chunking strategy, choose Advanced Setup from the start to avoid a costly rebuild later.
3. **Create and configure the vector search index** — in Data Cloud Setup → Vector Search, create the index against the target text field. In Advanced Setup, explicitly set the chunking strategy, chunk size, and overlap. Document these choices and their rationale in the decision record.
4. **Configure the Grounding record** — in Agentforce Setup, attach a Grounding configuration to the agent topic or Prompt Template referencing the new index. Set top-K to 3–7 (start at 5) and add metadata filters if multi-dimensional content is indexed.
5. **Obtain a Data Cloud access token and validate Query API access** (if applicable) — test the token endpoint with the Data Cloud Connected App credentials and execute a test query against the index before integrating into application code.
6. **Run end-to-end retrieval tests** — in the Agent Preview panel, submit at least five representative queries and review the Grounding tab to confirm chunk retrieval. Check the Einstein Trust Layer audit log for unexpected masking events.
7. **Review the checklist below** and confirm generated artifacts match the packaging and data residency requirements before marking the work complete.

---

## Review Checklist

Run through these before marking work complete:

- [ ] Data Cloud Vector Search feature is enabled and the Salesforce-managed embedding model shows as active in Setup
- [ ] Chunking strategy decision (Easy Setup vs Advanced Setup, strategy type, chunk size, overlap) is documented in a decision record
- [ ] If Easy Setup was used initially and precision is inadequate, index has been rebuilt with Advanced Setup
- [ ] Data Cloud Connected App has `cdpapi` scope and Data Cloud access token generation is tested if Query API access is required
- [ ] Grounding configuration references the correct vector index with appropriate top-K and metadata filters
- [ ] Einstein Trust Layer audit log reviewed for at least one end-to-end retrieval turn — masking events investigated if present
- [ ] Agent Preview tested with 5+ representative queries; Grounding tab confirms retrieved chunks are relevant
- [ ] Source DMO PII fields classified in Data Cloud field taxonomy before index build if sensitive data is present
- [ ] If packaging: vector search index, DMO definition, and Data Stream configuration are all included in the Data Kit

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Easy Setup Chunk Parameters Are Not Tunable Post-Creation** — Easy Setup automatically selects chunk size and strategy, and these are locked at creation time. There is no UI control to adjust them afterward. If retrieval quality is poor, the only remedy is to delete the index and rebuild with Advanced Setup. Developers who don't know this assumption waste time adjusting top-K and metadata filters trying to fix a chunking-level problem.

2. **Query API Requires a Data Cloud Access Token, Not a CRM Token** — The Data Cloud vector search Query API endpoint uses a separate authentication system from the standard Salesforce CRM. Posting a standard OAuth access token from a CRM Connected App to the Data Cloud API returns a 401. The correct token is obtained from the Data Cloud token endpoint (`/services/a360/token`) using a Connected App scoped with `cdpapi`. Many developers discover this only after a frustrating round of 401 debugging.

3. **Einstein Trust Layer Masking Silently Replaces Chunk Content** — If a retrieved chunk contains a field classified as PII in the Data Cloud field taxonomy, the Trust Layer replaces the field value with a masking placeholder before the chunk reaches the LLM. The chunk still counts toward top-K but delivers no useful content for the masked portion. Developers who index DMOs with sensitive fields without pre-classifying them may see the agent ignore retrieved context without understanding why.

4. **Changing the Embedding Model Requires Full Re-Indexing** — Switching from the Salesforce-managed embedding model to a BYO model (or vice versa) after the index is built invalidates all existing vectors. The index must be rebuilt from scratch. This is an expensive operation for large corpora and should be planned for in advance.

5. **Near-Real-Time Refresh Requires Explicit Data Stream Configuration** — The vector index refresh cadence is inherited from the underlying Data Stream. New Data Streams default to batch/scheduled refresh. Without explicit continuous-mode configuration, newly ingested or updated source records do not appear in search results until the next scheduled batch window, which can be hours later in default configurations.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Cloud vector search index | Configured index with embedding model, chunking strategy (strategy type, chunk size, overlap), and refresh settings — packageable via Data Kit |
| Grounding configuration record | Retriever definition linking the agent topic or prompt template to the vector index, including top-K and metadata filter expressions |
| Data Cloud access token generation pattern | Documented OAuth flow for obtaining a Data Cloud token from the `/services/a360/token` endpoint using a `cdpapi`-scoped Connected App |
| Decision record | Chunking strategy rationale, chunk size/overlap values, embedding model choice, top-K selection, and data residency notes |
| Einstein Trust Layer audit log excerpt | QA evidence confirming retrieval events are logged and masking behavior is deliberate |

---

## Related Skills

- `rag-patterns-in-salesforce` — Covers the broader RAG architecture and pattern library; use this skill first for a high-level view, then this skill for vector search developer specifics
- `einstein-trust-layer` — Governs masking, zero-retention, and audit logging policies that apply to grounded chunks
- `agentforce-agent-creation` — Prerequisite for creating the agent topic to which a Grounding configuration is attached
- `model-builder-and-byollm` — Use when a custom embedding model must be registered to replace the Salesforce-managed model in Advanced Setup
