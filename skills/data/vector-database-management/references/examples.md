# Examples: Vector Database Management

## Example 1: Replace an Easy Setup index whose results are noisy

**Context:** A service team created a search index on the Knowledge article DMO with Easy Setup (passage extraction, E5-Large V2, hybrid). Articles are long HTML pages in English and German. Agents get passages from the wrong product line and from German articles when the question is in English.

**Problem:** The index has no filter fields, so the default retriever cannot narrow by product or language, and passages lose the article title that gives them context.

**Solution:** Build a second index with Advanced Setup, validate it with queries, move the retriever, then delete the old index.

```text
Data Cloud app > Search Index > New > Advanced Setup
  Search type:      Hybrid
  Data space:       default
  Object:           Knowledge article DMO (not mapped from external DLOs)
  Chunking:         Semantic-based passage extraction on the article body field
                    Prepend fields: Title
                    Max tokens: 512 (English and German are Latin-script)
  Embedding model:  Multilingual E5-Large (two languages)
  Filter fields:    Language, Product_Line (2 of the 10 allowed)
  Chunked fields exclude: author email, internal reviewer notes
```

Wait for status Ready, then run validation queries in Data Cloud Query Editor. Replace the DMO names with the index and chunk DMO API names shown on the configuration record; the names below are illustrative.

```sql
-- Hybrid search with a pre-filter; quotes inside the filter string are doubled.
select h.hybrid_score__c, h.vector_score__c, h.keyword_score__c, c.Chunk__c
from hybrid_search(
        table(Knowledge_v2_index__dlm),
        'How do I reset the LaserPrinter TX 440 to factory settings',
        'Language=''English'' and Product_Line=''Printers''',
        10) h
join Knowledge_v2_chunk__dlm c on h.SourceRecordId__c = c.RecordId__c
order by h.hybrid_score__c desc
limit 10
```

```sql
-- Vector-only comparison on the same question, joined to the chunk DMO.
select v.score__c, c.Chunk__c
from vector_search(
        TABLE(Knowledge_v2_index__dlm),
        'How do I reset the LaserPrinter TX 440 to factory settings',
        'Language="English"',
        10) v
join Knowledge_v2_chunk__dlm c on v.RecordId__c = c.RecordId__c
order by 1 desc
limit 10
```

Run 10 to 20 representative questions and record, for each, whether the expected article appears in the top results. Then in Einstein Studio, point each custom retriever at the new index, add filters (up to 10 conditions), and activate the new retriever version. Finally delete the old index; Data Cloud blocks the delete while any retriever still references it.

**Grounding:** Easy Setup defaults, Advanced Setup steps, filter-field limit, max tokens, statuses, delete rule, and the `vector_search` and `hybrid_search` syntax (including result fields and doubled quotes in filters) are from the Data Cloud guide (262), "Manage Search Indexes," "Chunking Strategies," "Run Vector Searches Using Query API," and "Run Hybrid Search Queries with Query API." Retriever steps are from "Create a Custom Retriever." UNVERIFIED (2026-10-03): the exact join key between the hybrid result and the chunk DMO in your org; the guide says `SourceRecordId__c` identifies the chunk DMO record, so confirm against your chunk DMO's primary key before relying on the join.

**Why it works:** Prepending the title keeps context on every passage, the multilingual model fits two languages, and filter fields let the retriever scope results instead of hoping ranking sorts them out.

---

## Example 2: Answers lag a day behind source changes

**Context:** An index on a product-documentation DMO is Ready, but answers cite instructions that were corrected the previous morning.

**Problem:** The data stream feeding the DMO runs once a day in Full Refresh mode, so changes arrive late and every run replaces all data.

**Solution:**

```text
Data Cloud app > Data Streams > Product_Docs stream > Edit settings
  Refresh mode:  Incremental (the source has a last-modified Datetime field)
  Schedule:      every hour (or the most frequent option the connector offers)
Then: confirm the next run processes only changed records, and watch the index
record; a Ready index processes source changes incrementally.
```

**Grounding:** Data Cloud guide (262), "Data Stream Settings and Refresh Modes" (Incremental, Upsert, Full Refresh) and "View Search Index Configurations" (Ready status runs incrementally). UNVERIFIED (2026-10-03): the schedule options for your connector.

**Why it works:** Freshness is decided upstream by the data stream. The index follows once the data lands.

---

Moving a search index configuration to another org through a data kit, with the retrieval manifest, is in `metadata-examples.md`.
