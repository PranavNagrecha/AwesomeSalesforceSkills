# LLM Anti-Patterns — Data Cloud Grounding For Agentforce

## Anti-Pattern 1: Pack Facts Into The Topic Prompt

**What the LLM generates:** a topic instruction that embeds lists of policies,
SKUs, or account statuses.

**Why it happens:** the topic prompt feels like the obvious place.

**Correct pattern:** facts go in a retriever. Topics hold rules. This
separation lets facts change without redeploying topics.

## Anti-Pattern 2: Vectorize Structured Data

**What the LLM generates:** "create vector embeddings of all Account fields."

**Why it happens:** treats retrieval as a single hammer.

**Correct pattern:** structured retriever for records, vector for unstructured.
Vectorizing structured fields kills exact-match and sharing enforcement.

## Anti-Pattern 3: Skip Citations

**What the LLM generates:** agent response with no source ids.

**Why it happens:** citations feel like a UX polish step.

**Correct pattern:** citations are debug infrastructure. Every grounded answer
must carry stable source ids.

## Anti-Pattern 4: Trust The LLM To Redact

**What the LLM generates:** "prompt the model to hide fields the user should
not see."

**Why it happens:** defense-in-depth confusion.

**Correct pattern:** never return to the model data it should not emit. Filter
at the retriever, then trust the output.

## Anti-Pattern 5: Large Top-K Everywhere

**What the LLM generates:** k=20 default because "more context is better."

**Why it happens:** intuitive but wrong.

**Correct pattern:** k=5 with a reranker to 1-3 beats k=20 raw on both quality
and latency.

## Anti-Pattern 6: No Freshness Contract

**What the LLM generates:** a retriever hooked to batch ingestion with no
documented staleness window.

**Why it happens:** freshness is invisible until users complain.

**Correct pattern:** write the SLA into the topic design. Align ingestion and
cache TTLs to the SLA.
