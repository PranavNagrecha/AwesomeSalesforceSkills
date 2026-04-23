# Data Cloud Grounding — Examples

## Example 1: Order Status Topic (Structured Retriever)

**User utterance:** "Where is my order?"

**Design:**
- Retriever: structured, against `Order_Engagement_DMO`.
- Filter: `UnifiedIndividualId = :contextUser` AND `Status != 'Delivered'` ORDER BY `OrderDate DESC` LIMIT 3.
- Topic instruction: "Use the retriever result. If none, say 'no recent open orders.' Do not guess."
- Citation: OrderId.

**Why:** small, focused, filtered, cheap, deterministic.

---

## Example 2: Knowledge Retriever With Section Chunking

**User utterance:** "How do I reset my password?"

**Design:**
- Retriever: vector, against Knowledge articles chunked by section heading.
- Top-k: 3, rerank to 1.
- Topic instruction: "Quote the steps from the article; do not paraphrase policy language."
- Citation: article URL + section anchor.

**Why:** semantic chunking preserves steps together; top-1 after rerank keeps prompt small.

---

## Example 3: Hybrid Retrieval For Account Summary

**User utterance (internal agent):** "Brief me on account X before the call."

**Design:**
- Retriever 1: structured DMO — last 5 cases, open opportunities, last 3 emails.
- Retriever 2: vector — last 2 call transcripts chunked by speaker turn.
- Fusion: agent action calls both in parallel, merges in a summary step.
- Citation: RecordIds + call segment ids.

**Why:** no single retriever can cover the ask; parallel calls keep latency flat.

---

## Anti-Pattern: "Just Vectorize Everything"

A team vectorized all Account and Contact fields "for search." Result: high
storage cost, poor recall for exact-match queries ("find contacts at ACME"),
and sharing became unenforceable. Fix: structured retriever on records,
vector only on unstructured.
