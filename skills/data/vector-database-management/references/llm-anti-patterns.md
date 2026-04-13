# LLM Anti-Patterns — Vector Database Management

Common mistakes AI coding assistants make when generating or advising on Vector Database Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending topK Increase to Fix Poor Retrieval Precision

**What the LLM generates:** "To improve retrieval precision and ensure the agent returns more relevant results, increase the `topK` parameter from 5 to 20. This will cast a wider net and capture the relevant document sections that are currently being missed."

**Why it happens:** LLMs trained on general RAG literature associate "missed relevant results" with an insufficient candidate pool. The topK-first reflex is common in open-source RAG tutorials where chunking is assumed to be correct and topK is the primary tuning knob. The Salesforce-specific constraint — that chunking strategy is immutable after index creation and is the primary precision lever — is underrepresented in training data.

**Correct pattern:**

```text
Diagnosis step first:
1. Inspect the actual chunks returned for a failing query.
2. If the relevant passage is split across adjacent low-scoring chunks,
   the root cause is the chunking strategy.
3. Delete the index and rebuild with Advanced Setup:
   - Chunk size: match to average document paragraph length (commonly 700–1000 chars)
   - Overlap: 10% of chunk size
4. Retest with representative queries.
5. Only adjust topK if the correct chunk now exists but is being cut off by too-low topK.
```

**Detection hint:** Any response that recommends increasing `topK` as a first or primary fix for "poor retrieval" or "irrelevant results" without first diagnosing chunking strategy.

---

## Anti-Pattern 2: Advising In-Place Chunking Strategy Change

**What the LLM generates:** "To update the chunking strategy, go to Data Cloud Setup > Vector Indexes, open the existing index, and change the chunk size from 500 to 800 characters in the Advanced Setup section."

**Why it happens:** LLMs default to "edit the existing record" as the natural update path. The Salesforce-specific behavior — that chunking configuration is locked at index creation and requires delete-and-rebuild — is not intuitive and is absent from most generic vector DB documentation. LLMs trained on Pinecone or Weaviate patterns where indexes can be re-configured in place will generate incorrect Salesforce guidance.

**Correct pattern:**

```text
To change chunking strategy on an existing vector index:
1. Document the current index configuration (embedding model, field list, chunk size, overlap).
2. Delete the existing vector index in Setup > Vector Indexes.
   WARNING: This removes all embeddings. Plan for a retrieval availability gap.
3. Create a new vector index on the same DMO/UDLO with the updated chunking configuration.
4. Wait for index status to reach Active.
5. Validate retrieval precision before restoring production traffic.
```

**Detection hint:** Phrases like "edit the existing index," "update the chunk size," or "modify the chunking settings" applied to an already-created index.

---

## Anti-Pattern 3: Assuming Embedding Model Can Be Swapped Without Index Rebuild

**What the LLM generates:** "To upgrade the embedding model, navigate to the vector index settings and select the new model from the dropdown. The index will automatically re-embed existing records using the new model."

**Why it happens:** Some vector database platforms (notably hosted services like Pinecone) support model version upgrades with automatic re-indexing triggered in the background. LLMs trained on those platforms assume Salesforce Data Cloud behaves similarly. It does not — every embedding model change requires a full delete-and-rebuild cycle.

**Correct pattern:**

```text
To change the embedding model on an existing vector index:
1. Note current index: DMO, field list, chunk size, overlap, refresh mode.
2. Delete the existing vector index (Setup > Vector Indexes > Delete).
3. Create a new vector index, selecting the updated embedding model.
4. Wait for full rebuild — time is proportional to corpus size.
5. Run retrieval precision tests before restoring production traffic.
6. Update the rebuild runbook with the new model name and rebuild date.
```

**Detection hint:** Any suggestion to "select a new model" or "update the model" on an existing, active vector index without mentioning a full delete-and-rebuild.

---

## Anti-Pattern 4: Treating Vector Search as a Standard SOQL Filter

**What the LLM generates:** "To find knowledge articles relevant to a customer query, add a WHERE clause to your SOQL: `WHERE Body LIKE '%warranty%'`. Alternatively, use a SOSL query for full-text search."

**Why it happens:** LLMs default to SOQL/SOSL as the Salesforce query paradigm. Vector search is a fundamentally different architecture — it converts a natural-language query into an embedding and ranks stored chunks by cosine similarity, not by keyword matching. SOQL LIKE patterns and SOSL full-text search return lexically matching results; they do not capture semantic similarity ("guarantee" vs. "warranty"), paraphrase matching, or conceptual proximity.

**Correct pattern:**

```text
Vector search is not SOQL. Use the Data Cloud vector search API or
Agentforce retrieval configuration:
- A natural-language query is embedded at query time using the same model as the index.
- The index returns the top-N chunks by cosine similarity to the query embedding.
- Semantic similarity (not keyword match) drives ranking.
- SOQL/SOSL is appropriate for structured, exact-match queries on standard fields.
- Vector search is appropriate for open-ended, natural-language, semantic queries.
Do not combine them as if they are equivalent alternatives.
```

**Detection hint:** SOQL LIKE, SOSL, or full-text search recommended as an alternative or equivalent to vector search for unstructured, natural-language retrieval scenarios.

---

## Anti-Pattern 5: Forgetting PII Field Exclusion from Vector Indexes

**What the LLM generates:** "Create the vector index over the CustomerProfile DMO, indexing the following fields: Name, Email, PhoneNumber, CaseNotes, ProductInterests."

**Why it happens:** LLMs optimizing for "include as many relevant fields as possible" do not apply data governance awareness by default. PII fields (names, email, phone) are readily available on customer DMOs, and including them seems to make retrieval richer. The critical constraint — that embedded PII in a vector store is a data governance risk regardless of field-level security on the source object — is not part of standard LLM RAG training.

**Correct pattern:**

```text
Before creating a vector index:
1. Review every field in the proposed field list against the org's PII taxonomy.
2. Exclude fields classified as PII (names, email addresses, phone numbers, SSNs,
   health data, financial identifiers).
3. Index only semantic content fields (case notes without PII, product descriptions,
   knowledge article body, etc.).
4. Document the exclusion list in the rebuild runbook for governance audit purposes.

Fields like Name, Email, PhoneNumber should NOT be in the vector index field list.
```

**Detection hint:** Vector index field lists that include Name, Email, Phone, SSN, DOB, or any field with "PII" or "Sensitive" in its description or classification tag.

---

## Anti-Pattern 6: Recommending Vector Search for Structured or Exact-Match Queries

**What the LLM generates:** "Use a vector index to look up a customer's account balance by account number" or "Build a vector index over the Product catalog to find products with SKU = 'ABC-123'."

**Why it happens:** When vector search is presented as a general-purpose retrieval mechanism, LLMs apply it indiscriminately. Vector search is optimized for semantic, open-ended natural-language queries over unstructured text. Structured lookups (account number, SKU, date range, status filter) are exact-match operations that SOQL handles correctly, deterministically, and at much lower cost and latency than vector retrieval.

**Correct pattern:**

```text
Use vector search ONLY for unstructured, semantic, natural-language queries:
  - "What is the return policy for electronics?" (knowledge retrieval)
  - "Find documents about renewable energy incentives" (semantic search)

Use SOQL for structured, exact-match, or filter-based queries:
  - Account balance by account number → SOQL WHERE AccountNumber = '...'
  - Products by SKU → SOQL WHERE SKU__c = 'ABC-123'
  - Cases opened in the last 30 days → SOQL WHERE CreatedDate = LAST_N_DAYS:30

Mixing these architectures (e.g., embedding a product SKU for vector retrieval)
wastes credits and produces non-deterministic results for queries that have
exact, deterministic answers.
```

**Detection hint:** Vector search recommended for ID lookups, numeric field queries, date ranges, status filters, or any scenario described as "find a specific record."
