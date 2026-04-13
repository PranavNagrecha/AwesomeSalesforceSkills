# Examples — Vector Database Management

## Example 1: Knowledge Base Vector Index for Agentforce — Poor Retrieval Fixed by Advanced Chunking

**Context:** A service cloud team has loaded product documentation PDFs into a Data Cloud DMO and created a vector index using Easy Setup (500-character fixed chunks). An Agentforce agent is answering customer product questions by retrieving from this index. Retrieval quality is poor — the agent frequently returns irrelevant document sections.

**Problem:** Easy Setup produces 500-character chunks with no overlap. Product documentation paragraphs average 600–900 characters. The fixed chunk boundary splits paragraphs mid-sentence, breaking semantic context. The most relevant passage for a given query is divided across two adjacent chunks, neither of which individually scores high enough to reach the top retrieval results. Increasing `topK` returns more candidates but does not surface the split passage because neither half ranks well independently.

**Solution:**

Delete the existing Easy Setup index and rebuild with Advanced Setup:

```text
Data Cloud Setup > Vector Indexes > Delete existing index

Create new Vector Index:
  Source DMO:        ProductDocumentation__dlm
  Embedding Model:   [current model — do not change during this fix]
  Setup Mode:        Advanced Setup
  Chunk Size:        800 characters
  Chunk Overlap:     10% (80 characters)
  Fields:            DocumentBody__c (exclude DocumentOwnerEmail__c — PII)
```

After the index reaches Active status, run representative test queries:

```text
Query: "What is the warranty period for the Model X refrigerator?"
Expected: chunk containing the warranty section of the Model X product guide
```

Monitor precision across 10–20 representative queries before restoring production traffic.

**Why it works:** 800-character chunks accommodate full paragraphs without splitting semantic units. 10% overlap preserves context at chunk boundaries — if a key sentence straddles a chunk boundary, it appears in both adjacent chunks, ensuring at least one scores high for relevant queries.

---

## Example 2: Stale Vector Index Fixed by Enabling Continuous Refresh on Inventory DMO

**Context:** A retail org uses a Data Cloud vector index over an inventory DMO to power a product availability chatbot. The inventory DMO receives batch updates from an ERP system several times per day. Users are reporting that the chatbot cites out-of-stock items as available.

**Problem:** The vector index Data Stream is configured in the default batch refresh mode. After each ERP batch load updates the inventory DMO, the vector index does not reflect the changes until the next scheduled batch refresh window, which can lag by two to four hours. The chatbot is retrieving stale embeddings and reporting outdated availability.

**Solution:**

Navigate to the Data Stream feeding the inventory DMO and switch refresh mode to continuous:

```text
Data Cloud Setup > Data Streams > InventoryDMO_Stream

Edit:
  Refresh Mode: Continuous  (was: Batch)

Save
```

After saving, verify the Data Stream shows the updated refresh mode. Set a credit consumption alert:

```text
Data Cloud Setup > Credit Usage Alerts
  Alert threshold: [appropriate for org's credit allocation]
  Alert recipient: [admin email]
```

Monitor credit usage for 48 hours after enabling continuous mode to confirm consumption is within budget.

**Why it works:** Continuous refresh mode triggers an index update each time a record changes in the source DMO, keeping embeddings near-real-time. The credit alert prevents runaway consumption if ERP batch behavior changes and update frequency spikes unexpectedly.

---

## Anti-Pattern: Raising topK to Fix Poor Retrieval Precision

**What practitioners do:** When an Agentforce agent returns off-topic results, the immediate instinct is to increase `topK` (the number of candidate chunks returned from the vector index) to "cast a wider net."

**What goes wrong:** Increasing `topK` returns more candidates, but the underlying problem is that the correct chunk does not exist in a form the embedding model can rank highly. If the relevant passage was split by a 500-character fixed chunk boundary, neither half scores well. Returning 20 or 50 candidates instead of 5 still does not surface a well-scored chunk containing the complete relevant passage. The agent receives more low-relevance noise, which can degrade answer quality further.

**Correct approach:** Diagnose the chunking strategy first. Inspect which chunks are actually being returned for a failing query. If the relevant content is split across adjacent low-scoring chunks, the fix is a chunking strategy rebuild using Advanced Setup with larger chunk size and overlap — not a `topK` increase.
