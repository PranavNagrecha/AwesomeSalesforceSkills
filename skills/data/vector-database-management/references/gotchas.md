# Gotchas: Vector Database Management

Non-obvious Data Cloud behaviors that cause real production problems with search indexes. Each one names the official source it rests on. Page references are to the Data Cloud guide PDF (release 262).

## Gotcha 1: Chunking strategy and embedding model are view-only after creation

**What happens:** A team opens an existing index to change the chunking strategy or embedding model and finds only fields and file extensions can be added.

**When it occurs:** When retrieval quality problems are traced to chunking after the index is live, or a better model is adopted.

**How to avoid:** Decide chunking, max tokens, and model before creation. To change them, build a second index, validate it, move retrievers, then delete the old one.

**Source:** Data Cloud guide (262), "Edit Search Index Configurations": "you can edit search index configurations to add fields or file extensions for chunking. You can view but not modify other existing settings."

---

## Gotcha 2: Easy Setup is not a fixed-character chunker

**What happens:** Teams expect Easy Setup to cut 500-character chunks and tune around that number. Easy Setup actually applies passage extraction, the E5-Large V2 model, and hybrid search.

**When it occurs:** When guidance written from memory (including version 1.0.0 of this skill) is trusted over the guide.

**How to avoid:** Treat Easy Setup as "passage extraction, E5-Large V2, hybrid." Use Advanced Setup when you need a different model, max tokens, prepend fields, or filter fields.

**Source:** Data Cloud guide (262), "Create a Search Index Configuration with Easy Setup" (defaults list).

---

## Gotcha 3: Non-Latin text can overflow the token limit and be cut from the embedding

**What happens:** Japanese or other non-Latin content is merged into chunks by punctuation count. A chunk can exceed 512 tokens, and the embedding model ignores text past its limit, so part of the chunk never affects retrieval.

**When it occurs:** On non-Latin corpora left at the default max tokens of 512.

**How to avoid:** Lower the max-token setting for non-Latin content and use Multilingual E5-Large where the content is not English.

**Source:** Data Cloud guide (262), "How the Max Token Setting Affects Chunking."

---

## Gotcha 4: An index cannot be deleted while a retriever references it

**What happens:** Deleting an old index during a cutover fails.

**When it occurs:** When custom retrievers in Einstein Studio still point at the old index.

**How to avoid:** Move or delete every dependent retriever first, then delete the index. Remember that deleting the configuration ends vector search on its index DMO.

**Source:** Data Cloud guide (262), "Delete Search Index Configurations."

---

## Gotcha 5: Filter fields must exist before retrievers can filter

**What happens:** A retriever cannot filter by category or region because the index was created without filter fields.

**When it occurs:** When the index is built with Easy Setup and filtering is needed later.

**How to avoid:** Choose up to 10 filter fields in Advanced Setup. Related-object filter fields need a 1:1 or N:1 relationship. Data Cloud picks up filter values when embeddings are generated or refreshed.

**Source:** Data Cloud guide (262), "Create a Vector Search Index Configuration with Advanced Setup," step 11; "Create a Custom Retriever" ("Retriever filters are available only if the search index that you selected has filter fields defined"); Data Cloud Limits ("Maximum number of fields that can be selected for pre-filtering: 10").

---

## Gotcha 6: Large files are stored but never chunked

**What happens:** Some documents never appear in results even though they are in the UDMO.

**When it occurs:** TXT or HTML files over 4 MB, or PDF files over 100 MB, are added to unstructured DLOs and DMOs but are not chunked or vectorized. PDF and HTML files with tabular data cannot be chunked.

**How to avoid:** Split oversized files before ingestion and check file sizes during intake.

**Source:** Data Cloud guide (262), "Unstructured Data and Search Index Guidelines and Limits"; "Search Index Reference," supported file formats.

---

## Gotcha 7: Vector search queries are billed by index size

**What happens:** Query costs climb as the corpus grows, even with flat query volume.

**When it occurs:** Data Queries billing for vector search against unstructured data counts the number of vectors in the search index.

**How to avoid:** Index only fields that answer questions, keep separate indexes for separate use cases within the 10-index limit, and estimate cost from vector count times query volume.

**Source:** Data Cloud guide (262), "Billing Considerations for Unstructured Data and Search Index," Data Queries row.

---

## Gotcha 8: Full Refresh on the source data stream replaces all data

**What happens:** The source data lake object is wiped and reloaded every cycle.

**When it occurs:** When the data stream feeding the indexed object uses Full Refresh, the default when no other mode is available.

**How to avoid:** Use Incremental (connectors with a last-modified Datetime field) or Upsert (file connectors) where possible. UNVERIFIED (2026-10-03): whether a Full Refresh makes the search index reprocess every record; measure processing after the first refresh.

**Source:** Data Cloud guide (262), "Data Stream Settings and Refresh Modes."

---

## Gotcha 9: topK is a retriever setting, and raising it is not a chunking fix

**What happens:** More results are returned, but the right passage still ranks low because it was split or diluted.

**When it occurs:** When poor answers are blamed on the number of results.

**How to avoid:** Inspect the returned chunks and scores with a `vector_search` or `hybrid_search` query first. Fix chunking (new index) or add filter fields before raising the result count in the retriever.

**Source:** Data Cloud guide (262), "Run Vector Searches Using Query API" (`k` is the number of most similar results) and "Create a Custom Retriever" (the retriever sets how many results it returns).
