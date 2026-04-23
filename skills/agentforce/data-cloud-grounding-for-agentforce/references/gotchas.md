# Data Cloud Grounding — Gotchas

## 1. Retrievers Do Not Inherit CRM Sharing Automatically

Data Cloud sharing and CRM sharing are separate. You must explicitly design
retriever filters or Data Space scoping to honor CRM visibility.

## 2. Ingestion Lag ≠ Zero

Even a streaming ingestion job has minutes of latency. If your SLA says "live"
you need an action (REST callout) not a retriever.

## 3. Vector Index Freshness Trails Source Updates

Re-embedding is not instantaneous. Knowledge edits can take time to surface.
Tell stakeholders the window.

## 4. Large Top-K Kills Latency And Quality

k=20 sends 20 chunks into the prompt. Both latency and "lost in the middle"
problems spike. Default to k=5 and rerank down.

## 5. PII In Embeddings Is Still PII

Embedding a field does not obscure it — re-identification from embeddings is
feasible. Treat the vector store as a copy of the source data.

## 6. Mixing Languages In One Index Degrades Retrieval

If your content spans languages, segment indexes by language or use an
embedding model built for multilingual retrieval. Do not mix silently.

## 7. Stale Ids Break Citations

If the source doc is deleted but the vector shard is not pruned, the agent
will cite a 404. Schedule index janitors.
