# Data Cloud Grounding — Examples

## Example 1: Order Status Subagent (Structured Retriever)

**User utterance:** "Where is my order?"

**Design:**
- Retriever: structured, against `Order_Engagement_DMO`.
- Filter: `UnifiedIndividualId = :contextUser` AND `Status != 'Delivered'` ORDER BY `OrderDate DESC` LIMIT 3.
- Subagent instruction (subagents were called topics before April 2026): "Use the retriever result. If none, say 'no recent open orders.' Do not guess."
- Citation: OrderId.

**Why:** small, focused, filtered, cheap, deterministic. UNVERIFIED (2026-10-03): the structured-retriever filter syntax shown here; if your org has no such retriever, implement this subagent with an action that queries the order at answer time.

---

## Example 2: Knowledge Retriever With Section Chunking

**User utterance:** "How do I reset my password?"

**Design:**
- Retriever: the one a Knowledge data library creates, over articles scoped to the support data categories.
- Number of Results: 3. (UNVERIFIED 2026-10-03: the earlier "rerank to 1" step; no reranking setting appears in the sources read.)
- Subagent instruction: "Quote the steps from the article; do not paraphrase policy language."
- Citation: article URL + section anchor.

Library configuration (ADL API request body; full procedure in `references/metadata-examples.md`):

```json
{
  "masterLabel": "Support How-To",
  "developerName": "Support_How_To",
  "groundingSource": {
    "sourceType": "KNOWLEDGE",
    "knowledgeConfig": {
      "primaryIndexField1": "Title",
      "primaryIndexField2": "Summary",
      "contentFields": ["UrlName"],
      "isDataCategoryRuleEnabled": true,
      "dataCategorySelectionNames": ["Support.Accounts"]
    }
  }
}
```

**Why:** a small result count keeps the prompt focused, and the data category rule keeps the library to the articles this subagent should use.

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
