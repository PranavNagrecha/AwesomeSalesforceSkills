# LLM Anti-Patterns — RAG Patterns in Salesforce

Common mistakes AI coding assistants make when generating or advising on Retrieval-Augmented Generation (RAG) patterns in Salesforce using Data Cloud vector search.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Indexing Knowledge Article HTML Without Stripping Tags

**What the LLM generates:** "Map the Knowledge article Body__c field directly to the vector search index."

**Why it happens:** LLMs treat the Body field as clean text. Salesforce Knowledge stores article body as HTML, and training data does not consistently warn about markup contamination in embeddings.

**Correct pattern:**

```
Salesforce Knowledge stores article body as HTML. If Body__c is mapped directly
to the vector index without stripping HTML tags, the embedding model encodes
tag markup (<p>, <li>, &nbsp;, <div>) as semantic content. This degrades
similarity scores and retrieval quality.

Before indexing:
- Pre-process the Body field using a Data Cloud formula or transformation
  to strip HTML tags.
- Verify the cleaned text in the DMO before enabling the vector index.
- Test retrieval quality with a sample of representative queries after indexing.
```

**Detection hint:** If the advice maps a Knowledge article Body field directly to a vector index without HTML stripping, retrieval quality will be poor due to markup noise in embeddings.

---

## Anti-Pattern 2: Setting top-K Too High Without Considering Token Budget

**What the LLM generates:** "Set top_k to 10 to maximize retrieval coverage" without assessing the prompt token impact.

**Why it happens:** LLMs default to higher recall. Training data emphasizes retrieval completeness without modeling the downstream token budget constraint.

**Correct pattern:**

```
Each retrieved chunk consumes tokens in the final prompt. With top-K of 10 and
a chunk size of 512 tokens, retrieval alone consumes 5,000+ tokens.

For a model with a 16K context window, this leaves limited space for:
- System instructions
- Conversation history
- CRM record context from merge fields

Calculate: top_k * chunk_size_tokens = retrieval token budget.
Ensure this fits within the model's context window with room for all other
prompt components. For shorter-context models, use top_k of 3-5 with smaller
chunk sizes (256-384 tokens).
```

**Detection hint:** If the advice sets a high top-K without estimating the token impact against the model's context window, the prompt may crowd out conversation history or CRM context.

---

## Anti-Pattern 3: Assuming Vector Index Auto-Refreshes on Article Publish

**What the LLM generates:** "Publish the Knowledge article and the agent will immediately use the updated content."

**Why it happens:** LLMs assume real-time data freshness. The default Data Stream refresh cadence is scheduled batch, not continuous.

**Correct pattern:**

```
Near-real-time refresh is available for CRM Data Streams but requires EXPLICIT
configuration of the refresh trigger. By default, new Data Streams use scheduled
batch refresh.

A newly published Knowledge article will NOT appear in retrieval results until
the next scheduled refresh window unless the Data Stream is configured for
continuous mode.

After configuring the Data Stream:
- Verify the refresh cadence in Data Cloud Data Stream settings.
- For time-sensitive content, enable continuous/near-real-time refresh.
- For static document corpuses, scheduled batch is sufficient and lower overhead.
```

**Detection hint:** If the advice assumes new content is immediately available for retrieval without configuring the Data Stream refresh mode, there will be a lag between publication and agent awareness.

---

## Anti-Pattern 4: Using Exact-Match Metadata Filters on Free-Text Fields

**What the LLM generates:** "Add a metadata filter: Product_Name__c = '{!topic.product}'" where Product_Name__c is a free-text field with high cardinality.

**Why it happens:** LLMs generate filter syntax without assessing the field's data quality. Exact-match filters on free-text fields with inconsistent values produce empty candidate sets.

**Correct pattern:**

```
Metadata filters in the Grounding config are PRE-FILTERS applied before ANN
ranking. If the filter is too restrictive (exact match on a free-text field
with high cardinality or inconsistent values), the candidate set may be EMPTY
even when relevant chunks exist.

Best practices:
- Use categorical fields (picklists, standardized values) for metadata filters.
- Use LIKE or contains operators rather than exact match on text fields.
- Test the filter against the actual data in the DMO to confirm it returns
  candidates before deploying.
```

**Detection hint:** If the advice uses exact-match metadata filters on free-text fields without verifying data consistency, the retriever may return zero results.

---

## Anti-Pattern 5: Ignoring Trust Layer Masking Impact on Retrieved Chunks

**What the LLM generates:** RAG configuration without mentioning Trust Layer data masking behavior on retrieved content.

**Why it happens:** LLMs treat the RAG pipeline as a pure retrieval-to-prompt flow. The Trust Layer masking step between retrieval and prompt injection is specific to Salesforce and absent from general RAG training data.

**Correct pattern:**

```
Retrieved chunks pass through the Einstein Trust Layer before reaching the LLM.
If a chunk contains a field classified as PII under the Trust Layer data masking
policy, the value is replaced with a placeholder token.

The chunk still counts toward top-K but contributes NO useful content. This can
cause the agent to appear to ignore retrieved documents.

Before deploying RAG:
- Review which fields in the source DMO are classified as PII.
- Check the Trust Layer audit log during QA for masking events.
- If key fields are being masked, reclassify them or restructure the source
  content so critical information is not in masked fields.
```

**Detection hint:** If the advice configures RAG without considering Trust Layer masking, the agent may receive redacted chunks that appear to contain no useful content.

---

## Anti-Pattern 6: Not Validating Chunk Size and Overlap Against Use Case

**What the LLM generates:** "Use the default chunk size" or "Set chunk size to 1024 tokens for maximum context" without evaluating the use case requirements.

**Why it happens:** LLMs either defer to defaults or maximize a single dimension. Chunk size and overlap are use-case-dependent parameters that require explicit tradeoff analysis.

**Correct pattern:**

```
Chunk size and overlap directly affect retrieval precision and recall:

High-precision use cases (legal, compliance, narrow factual questions):
  - Smaller chunks: 256-384 tokens
  - Higher overlap: 20%
  - Lower top-K: 3
  - Reduces context dilution; each chunk is tightly focused

High-recall use cases (broad knowledge bases, exploratory queries):
  - Larger chunks: 512-768 tokens
  - Standard overlap: 10-15%
  - Higher top-K: 5-10
  - Each chunk carries more context; covers multi-faceted queries

Document the chunk size, overlap, and top-K choices in a decision record with
the rationale tied to the specific use case requirements.
```

**Detection hint:** If the advice uses default or arbitrary chunk sizes without relating the choice to the use case's precision/recall requirements, retrieval quality will be suboptimal.
