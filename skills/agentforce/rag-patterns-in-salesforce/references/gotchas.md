# Gotchas — RAG Patterns in Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: HTML Tags in Knowledge Article Body Corrupt Embeddings

**What happens:** When a `KnowledgeArticleVersion.Body` field is mapped to a Data Cloud DMO without HTML stripping, the embedding model receives raw HTML markup as part of the chunk text. Tags like `<p>`, `<ul>`, `<li>`, `<strong>`, and entities like `&nbsp;` are tokenized and encoded as semantic content. This skews cosine similarity scores — chunks with structurally similar HTML scaffolding score closer to each other than chunks with semantically related content.

**When it occurs:** Any time the Knowledge → Data Cloud CRM connector maps the `Body` field directly without a Data Transform stripping HTML. This is the default path if no transformation is applied, so it affects every standard Knowledge-RAG implementation that does not explicitly address it.

**How to avoid:** Create a Data Cloud Data Transform that applies a regex-based HTML strip to the `Body` field before writing to the DMO used for vector indexing. Test by inspecting a sample chunk in the Data Cloud UI — if angle brackets or entity codes appear in the stored text, stripping is not working.

---

## Gotcha 2: Metadata Pre-Filters Can Return Zero Candidates Silently

**What happens:** Metadata filters in the Grounding configuration are applied as pre-filters before ANN ranking. If the filter condition matches zero records in the index (e.g., a typo in a filter value, a merge field that resolves to null, or a case-sensitive mismatch), the vector search returns zero chunks. The agent then responds with no grounding context, appearing to ignore the knowledge base entirely. No error is surfaced to the agent user — the response simply looks ungrounded.

**When it occurs:** Most commonly when filter merge fields like `{!topic.productLine}` resolve to null because the context variable was not populated by the time the Grounding call executes (e.g., the account record was not loaded yet, or the agent topic action that sets the variable fires after the retrieval step). Also occurs when filter values are compared case-sensitively against DMO field values that were ingested with inconsistent casing.

**How to avoid:** In Agent Preview, check the Grounding tab for "0 chunks retrieved" results. Validate filter merge field values by adding a Debug action before the retrieval step to log the resolved value. Use case-insensitive filter operators where available, or normalize casing during Data Transform ingest. Add a fallback Grounding configuration without the filter as a secondary retriever for the same topic, triggered when the primary returns zero results.

---

## Gotcha 3: Einstein Trust Layer Masking Silently Degrades Chunk Content

**What happens:** The Einstein Trust Layer applies data masking to chunks that contain fields classified as sensitive (PII, financial, health data) under the org's field classification taxonomy. Masked values are replaced with placeholder tokens (e.g., `[MASKED]`) before the chunk reaches the LLM. The chunk still counts toward the top-K budget and appears in the Grounding tab as "retrieved," but the LLM receives a chunk with critical content redacted. The agent may generate a response acknowledging the document exists while being unable to use its content — or worse, may hallucinate the masked values.

**When it occurs:** When source DMO fields that appear in chunk text are classified as sensitive under Data Cloud's field taxonomy. Common examples: `Email__c`, `Phone__c`, `SSN__c` in a customer-facing knowledge DMO, or `Price__c` fields in a product spec DMO where pricing data is classified as confidential.

**How to avoid:** Before enabling RAG grounding in production, export the Trust Layer audit log for a representative set of retrieval queries and inspect for masking events. If content-critical fields are being masked, either: (1) reclassify the field as non-sensitive if that is appropriate given data governance policy, or (2) restructure the DMO to exclude sensitive fields from the text column that feeds the vector index, keeping them only as filterable metadata columns that are never chunked.

---

## Gotcha 4: Vector Index Does Not Refresh Automatically on Knowledge Article Publish

**What happens:** When a Knowledge article is published or updated, it does not immediately appear in vector search results. The Data Cloud Data Stream defaults to **scheduled batch refresh**, not near-real-time. New articles remain invisible to the retriever until the next scheduled refresh window executes, which may be hours later depending on the configured schedule.

**When it occurs:** Any org where the Knowledge → Data Cloud Data Stream was created without explicitly enabling continuous (near-real-time) refresh mode. The Salesforce UI does not warn that retrieval results may be stale.

**How to avoid:** Open the Data Stream configuration in Data Cloud and confirm the refresh mode. If Knowledge articles are published frequently and freshness matters for agent quality, switch to continuous mode. Document the refresh lag in the RAG system runbook so that support staff know not to expect newly published articles to be retrievable immediately.

---

## Gotcha 5: top-K Retrieved Chunks Consume Prompt Token Budget

**What happens:** Each retrieved chunk is inserted into the prompt payload before the LLM call. With `top_k = 10` and `chunk_size = 512 tokens`, retrieval alone contributes up to 5,120 tokens to the prompt. For agents using GPT-4 class models with a 128K context window this is rarely a problem, but for configurations with shorter windows, or when the prompt template also includes long CRM record fields and conversation history, total prompt size can exceed the model's context limit. When this happens, the platform silently truncates either the conversation history or the retrieved chunks — and the agent degrades without a clear error.

**When it occurs:** During load testing or when agent topics have complex system prompts combined with high top-K values and large chunk sizes. Also occurs when conversation history accumulates over a long multi-turn session.

**How to avoid:** During QA, monitor total prompt token consumption using the Einstein Trust Layer audit log (which records input and output token counts per call). Tune `top_k` and `chunk_size` together — reducing top-K from 10 to 5 halves retrieval token cost with minimal recall impact for most use cases. Set a prompt token budget guard in the agent topic's system prompt length design.

---

## Gotcha 6: Scratch Org Packaging Requires Data Kits for Vector Index Configuration

**What happens:** Vector search index configuration, DMO definitions, and Data Stream mappings are Data Cloud metadata artifacts. They are not automatically included in a 2GP package's metadata retrieval using standard `force:source:retrieve`. Attempting to deploy a RAG-enabled agent package to a scratch org without the Data Kit component results in a broken Grounding configuration — the agent deploys but the retriever references a non-existent index.

**When it occurs:** In any 2GP DevOps pipeline that does not explicitly include Data Cloud metadata via Data Kits. This catches teams who package the Agentforce agent and prompt template correctly but overlook the Data Cloud side of the RAG configuration.

**How to avoid:** Use Data Kits (introduced in Summer '24) to package Data Cloud components — DMO definitions, Data Streams, and vector search index configurations — alongside the agent package. The Data Cloud Developer Guide documents the Data Kit structure and `datakit.json` manifest format. Validate by deploying the full package to a new scratch org and running a test retrieval query before marking a CI build green.
