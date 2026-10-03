# LLM Anti-Patterns: RAG Patterns in Salesforce

Common mistakes AI coding assistants make when advising on Retrieval-Augmented Generation (RAG) in Salesforce with Data Cloud search indexes, retrievers, and Einstein Data Libraries, with the correct move for each. Correction (2026-10-03): earlier versions of this file told readers to strip Knowledge HTML, tune `top_k` and chunk overlap on a subagent "Grounding config," and use `{!topic.product}` filters. Those settings are not documented; the entries below are rewritten against the Generative AI guide and the Data Cloud guide (Summer '26).

## Anti-Pattern 1: Stripping Knowledge HTML Before Indexing

**What the LLM generates:** "Strip all HTML tags from the article body before you create the vector index."

**Why it happens:** Generic RAG advice treats markup as noise.

**Correct pattern:**

```
Semantic-based passage extraction "uses the semantic meaning inherent in HTML
tags to chunk a document into passages" (headings, lists, bold subheadings).
Passage extraction "work[s] best for HTML files."

Before indexing:
- Keep well-formed HTML with real headings and block tags.
- Prepend the Title field so every chunk carries its article name.
- Convert tables to prose (tabular data can't be chunked).
```

**Detection hint:** Any instruction to remove HTML from Knowledge or HTML files before indexing.

---

## Anti-Pattern 2: Setting Number of Results High Without a Token Budget

**What the LLM generates:** "Set the retriever to return 15 results for maximum coverage."

**Why it happens:** Models default to higher recall and ignore what else the prompt must hold.

**Correct pattern:**

```
Each retrieved chunk is added to the prompt. Max tokens per chunk default to 512,
so 10 results can add roughly 5,000 tokens before record context and instructions.

- Set Number of Results in the retriever (Einstein Studio) or the prompt
  template's Configuration panel.
- Choose Output Fields deliberately (Chunk plus a title), not every field.
- Preview and read the retriever JSON in the resolution to see what is sent.
```

**Detection hint:** A results count above 10 with no estimate of prompt size.

---

## Anti-Pattern 3: Promising That Published Content Is Retrievable Immediately

**What the LLM generates:** "Publish the Knowledge article and the agent will use it right away."

**Why it happens:** Models assume real-time freshness.

**Correct pattern:**

```
Content reaches retrieval through data streams, chunking, and vectorization.
UNVERIFIED (2026-10-03): the exact refresh cadence for Knowledge-backed data
library streams was not found in a fetched source.

- Test the lag: publish a marker article and time when the agent can cite it.
- Tell stakeholders the measured lag, not "immediately."
```

**Detection hint:** "immediately" or "real time" attached to newly published content.

---

## Anti-Pattern 4: Filtering on Fields the Index Does Not Define

**What the LLM generates:** "In the retriever, filter where Product_Name__c equals the product the customer mentioned."

**Why it happens:** Models assume any DMO field can be filtered and that conversation values flow into filters.

**Correct pattern:**

```
"Retriever filters are available only if the search index that you selected has
filter fields defined." A custom retriever takes up to 10 conditions; an index
allows up to 10 pre-filter fields.

- Add the filter field (a categorical value, not free text) when creating the index.
- Build one retriever per scope, or use a dynamic retriever where a standard
  template supports one.
- UNVERIFIED (2026-10-03): passing a runtime conversation value into a filter.
```

**Detection hint:** A filter on a field that is not a filter field of the index, or `{!topic.…}` inside a filter.

---

## Anti-Pattern 5: Assuming the Trust Layer Masks Retrieved Chunks for Agents

**What the LLM generates:** "Retrieved PII is masked by the Trust Layer before it reaches the LLM."

**Why it happens:** Models generalize masking from prompt templates to agents.

**Correct pattern:**

```
"Data masking through the Einstein Trust Layer is disabled to improve the
performance and accuracy of agents." For prompt templates, pattern-based masking
scans all prompt text for its listed data types; field-based masking covers only
record merge fields and related lists.

- Keep sensitive values out of indexed content.
- Pick output fields that do not carry sensitive data.
- Review the GenAIGatewayRequest audit report (prompt and masked prompt) in QA.
```

**Detection hint:** A RAG design for an agent that relies on masking for privacy.

---

## Anti-Pattern 6: Inventing Chunk Overlap and Size Recipes

**What the LLM generates:** "Use 256-token chunks with 20% overlap for compliance content and 768 tokens with 15% overlap for broad content."

**Why it happens:** Recipes from other vector databases are repeated as if they were Data Cloud settings.

**Correct pattern:**

```
Data Cloud documents chunking strategies (semantic and window-based passage
extraction, conversation-based, prepend fields) and a max token limit (512 by
default, lower for non-Latin languages). No overlap setting is documented.

- Pick the strategy for the content type.
- Lower max tokens for non-Latin text.
- Record the choice and test retrieval with representative questions.
```

**Detection hint:** Overlap percentages presented as Data Cloud configuration.

---

## Anti-Pattern 7: Expecting the Retriever to Deploy With the Template

**What the LLM generates:** "Add the prompt template to the change set; the retriever goes with it."

**Why it happens:** Models assume dependencies travel together.

**Correct pattern:**

```
"If a prompt uses an Einstein Search retriever, the change sets don't include the
retriever or search index metadata... This rule applies to change sets and
Metadata API deployments."

- Move the index configuration with a data kit.
- Create and activate the retriever in the target org first.
- Then deploy the template.
```

**Detection hint:** A deployment plan for a retriever-backed template with no retriever creation step.
