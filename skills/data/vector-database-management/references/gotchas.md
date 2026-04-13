# Gotchas — Vector Database Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Chunking Strategy Cannot Be Changed In-Place

**What happens:** When a practitioner tries to edit an existing vector index to change the chunking strategy (e.g., from Easy Setup 500-character fixed chunks to Advanced Setup with custom size and overlap), they find there is no in-place edit option for chunking configuration. The only path is to delete the index and create a new one from scratch.

**When it occurs:** Any time a retrieval precision problem is diagnosed as a chunking mismatch after the index is already live in production. Also occurs when migrating from a proof-of-concept Easy Setup index to a production-grade Advanced Setup configuration.

**How to avoid:** Plan the chunking strategy before creating the index. Run a small-scale test with representative queries on a non-production Data Space using Advanced Setup before promoting to production. If an in-production rebuild is unavoidable, build the replacement index in parallel (if a second Data Space or index is available), validate precision, then reroute traffic and delete the old index to minimize availability gaps.

---

## Gotcha 2: Embedding Model Change Requires Full Index Rebuild

**What happens:** Swapping the embedding model on an existing vector index — for example, upgrading to a higher-quality or domain-specific model — is not an incremental update. The platform requires the entire index to be deleted and rebuilt. All existing embeddings are discarded; every chunk must be re-embedded with the new model.

**When it occurs:** When Salesforce releases a new embedding model and administrators want to adopt it, or when a domain-specific model becomes available that is expected to improve retrieval for a specialized corpus (legal, medical, technical). Rebuild time is proportional to corpus size — large indexes can take hours to rebuild.

**How to avoid:** Treat embedding model selection as a high-stakes decision at index creation time. Document the model in the rebuild runbook. When a model change is planned, schedule the rebuild during a low-traffic window. If the index is business-critical, maintain a parallel index during the transition period before cutting over.

---

## Gotcha 3: topK Adjustment Does Not Fix Poor Retrieval Precision — Chunking Strategy Is the Correct Lever

**What happens:** Practitioners increase `topK` (the number of candidate chunks returned) hoping to capture the relevant content that is not appearing in results. This does not fix the precision problem. It can actually make answer quality worse by flooding the retrieval context with low-relevance chunks, which dilutes the signal available to the LLM generating the final answer.

**When it occurs:** Any time the underlying problem is that source documents are chunked in a way that splits semantically meaningful passages (e.g., 500-character fixed chunks on documents with 800-character paragraphs). Increasing `topK` returns more of the same poorly-scored, context-fragmented chunks.

**How to avoid:** Before adjusting any retrieval parameter, inspect the actual chunks returned for a failing query. If the relevant passage is visibly split across adjacent chunks with neither half scoring well, the root cause is the chunking strategy. Delete the index, rebuild with Advanced Setup using a larger chunk size and overlap, and retest. Reserve `topK` tuning for cases where the correct chunk exists and ranks but is being cut off by a too-low `topK` limit.

---

## Gotcha 4: Continuous Refresh Mode Has Higher Credit Consumption Than Batch

**What happens:** Enabling continuous refresh mode on the Data Stream feeding a vector index triggers an embedding and index update for every source record change, not just on a periodic schedule. On high-volume DMOs (inventory, case records, event streams), this can multiply Data Cloud credit consumption significantly compared to batch mode.

**When it occurs:** Immediately after continuous mode is enabled on a DMO that receives frequent updates. The impact is proportional to update frequency — a DMO receiving thousands of updates per hour consumes orders of magnitude more credits than a daily batch refresh.

**How to avoid:** Set a Data Cloud credit consumption alert before enabling continuous mode in production. Review ERP or upstream system batch behavior to estimate per-hour update volume. Only enable continuous mode when retrieval freshness is a genuine business requirement, not as a default setting. For static or slowly changing corpora, batch refresh is the correct choice.
