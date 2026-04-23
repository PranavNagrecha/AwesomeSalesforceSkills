# Agentforce Cost Optimization — Examples

## Example 1: Topic Instruction Trim

**Before:** Topic `Case_Status_Check` had 720-token instructions including a 4-paragraph company overview, tone rules, and 8 examples.

**After:** 240 tokens — company overview moved to system prompt, tone rules generalized to the agent level, 2 high-coverage examples.

**Result:** 480 tokens saved per turn; no quality regression in the eval set.

---

## Example 2: Grounding With Reranker

**Before:** Data Cloud retriever returned k=10 chunks at 1200 tokens each = ~12,000 grounding tokens per turn.

**After:** k=10 retrieved, reranker selects top 3 at 500 tokens each = ~1,500 grounding tokens per turn.

**Result:** 10,500 tokens saved per turn; answer quality improved because the reranker dropped noise.

---

## Example 3: Tiered Model Routing

Classification step (intent-to-topic mapping) switched from flagship to a smaller tier. Final response remained on flagship. Overall cost per conversation dropped 18% with no measurable quality change.

---

## Anti-Pattern: "One Huge Topic" Inflation

A single topic with 15 capabilities. Every conversation injected all its instructions. Splitting into 5 narrow topics reduced average instruction tokens per conversation by 60%.
