# LLM Anti-Patterns: Vector Database Management

Common mistakes AI coding assistants make when advising on Data Cloud search indexes. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Raising topK as the first fix for poor retrieval

**What the LLM generates:** "Increase `topK` from 5 to 20 to cast a wider net."

**Why it happens:** General RAG tutorials assume chunking is correct and treat the result count as the main knob.

**Correct pattern:**

```text
1. Run the failing question as a vector_search or hybrid_search query joined to
   the chunk DMO and read the chunks and scores (references/examples.md).
2. If the right passage is split or buried, the fix is chunking: a new index with
   a different strategy, max tokens, or a prepend field such as Title.
3. If the right passage is mixed with off-topic records, add filter fields and a
   custom retriever filter.
4. Raise the retriever's result count only when the right chunk exists and ranks
   just below the cutoff.
```

**Detection hint:** A topK increase recommended before anyone has looked at the returned chunks.

---

## Anti-Pattern 2: Editing chunking or the embedding model in place

**What the LLM generates:** "Open the index, change the chunk size, and pick the new embedding model from the dropdown; it will re-embed automatically."

**Why it happens:** Other vector databases re-index in the background, and "edit the record" is the default instinct.

**Correct pattern:**

```text
Edit Search Index Configurations allows adding fields (DMO) or file extensions
(UDMO). Other settings are view-only (Data Cloud guide 262).

1. Record the current configuration.
2. Create a second index with Advanced Setup and the new settings.
3. Wait for status Ready (statuses: Submitted, In-progress, Ready, Failed).
4. Validate with test queries, then move custom retrievers to the new index.
5. Delete the old index; deletion is blocked while any retriever references it.
```

**Detection hint:** "Change the chunk size" or "select a new model" on an existing index, or a cutover plan that waits for "Active."

---

## Anti-Pattern 3: Inventing character-based chunk sizes and overlap percentages

**What the LLM generates:** "Easy Setup uses 500-character chunks with no overlap; set Advanced Setup to 800 characters with 10% overlap."

**Why it happens:** The model imports settings from generic text splitters. Version 1.0.0 of this skill made the same claim.

**Correct pattern:** Easy Setup applies passage extraction, E5-Large V2, and hybrid search. Advanced Setup chunking is driven by a max-token setting (default 512), with strategies such as semantic-based passage extraction, conversation-based chunking, and prepend fields. UNVERIFIED (2026-10-03): any overlap setting; the 262 Data Cloud guide does not describe one.

**Detection hint:** Chunk sizes in characters or an overlap percentage attributed to Data Cloud.

---

## Anti-Pattern 4: Offering SOQL or SOSL as the equivalent of vector search

**What the LLM generates:** "Add `WHERE Body LIKE '%warranty%'` or use SOSL instead of a vector index."

**Why it happens:** SOQL and SOSL are the default Salesforce query paradigm.

**Correct pattern:**

```text
Search indexes are queried through Data Cloud: vector_search() for semantic
similarity, hybrid_search() for semantic plus keyword with fusion ranking, or a
retriever in Prompt Builder and Agentforce. Results carry similarity scores
(score__c, or vector_score__c, keyword_score__c, hybrid_score__c).

Use SOQL for structured, exact-match lookups on records.
Use a hybrid index when unstructured text contains product codes or domain terms
that vector search alone matches poorly.
```

**Detection hint:** SOQL `LIKE` or SOSL proposed as the retrieval layer for an Agentforce knowledge use case.

---

## Anti-Pattern 5: Chunking personal data

**What the LLM generates:** "Index Name, Email, PhoneNumber, CaseNotes, and ProductInterests from the CustomerProfile DMO."

**Why it happens:** More fields look like richer retrieval.

**Correct pattern:**

```text
Every chunked field is copied into the chunk DMO and embedded.
1. Review each proposed field against the org's data classification.
2. Chunk only fields that answer questions (article body, product description,
   case resolution text with personal data removed).
3. Put category, product, or region in filter fields instead of chunking them.
4. Record the excluded fields with the index configuration.
UNVERIFIED (2026-10-03): whether retrievers enforce the source object's
field-level security; treat chunked text as readable by any retriever consumer.
```

**Detection hint:** A chunked-field list that includes names, email addresses, phone numbers, government IDs, or health data.

---

## Anti-Pattern 6: Using vector search for exact lookups

**What the LLM generates:** "Build a vector index over the product catalog to find SKU = 'ABC-123'."

**Why it happens:** Vector search gets presented as a general retrieval tool.

**Correct pattern:**

```text
Use SOQL for exact, structured lookups (IDs, SKUs, dates, statuses).
Use vector search for natural-language questions over unstructured text.
Use hybrid search when that text also contains codes and domain terms.
Every vector in an index adds to Data Queries billing for vector search.
```

**Detection hint:** A search index proposed for ID lookups, numeric filters, or date ranges.

---

## Anti-Pattern 7: Describing refresh as "batch or continuous"

**What the LLM generates:** "Switch the data stream from Batch to Continuous so the vector index updates in real time."

**Why it happens:** The model invents a two-mode switch. Version 1.0.0 of this skill described it that way.

**Correct pattern:** A Ready index processes source changes incrementally. The source data stream's refresh mode is Incremental, Upsert, or Full Refresh (Data Cloud guide), and its schedule decides how soon changes arrive. Full Refresh replaces all data each cycle. The Metadata API `DataStreamTemplate.refreshMode` enum also lists values such as `NEAR_REAL_TIME_INCREMENTAL` and `STREAMING`; UNVERIFIED (2026-10-03): which connectors offer them in the UI.

**Detection hint:** "Continuous refresh mode" attributed to a data stream or a search index.
