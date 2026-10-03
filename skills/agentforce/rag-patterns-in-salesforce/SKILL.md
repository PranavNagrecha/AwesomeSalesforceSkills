---
name: rag-patterns-in-salesforce
description: "Grounding Agentforce agents with retrieved knowledge using Data Cloud vector search: RAG pipeline design, vector search index configuration, chunking and embedding strategy, and how retrieved context flows through the Einstein Trust Layer into prompts. NOT for the Query API, Data Cloud access tokens, or Easy vs Advanced index mechanics — use agentforce/data-cloud-vector-search-dev. NOT for structured DMO retrievers, sharing enforcement at retrieval time and citations — use agentforce/data-cloud-grounding-for-agentforce."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I ground my Agentforce agent with company knowledge articles or documents?"
  - "My agent is hallucinating answers that should come from internal content — how do I connect it to a knowledge base?"
  - "How do I set up a Data Cloud vector search index for RAG with Einstein Copilot?"
  - "What chunking strategy should I use for Data Cloud vector embeddings?"
  - "How does the Einstein Trust Layer control what retrieved context reaches the LLM?"
  - "Agent gives generic answers instead of using our product documentation — how do I fix RAG grounding?"
  - "set up an Einstein Data Library so my agent answers from Knowledge articles"
  - "create a custom retriever that filters search index results by product line"
tags:
  - rag
  - data-cloud
  - vector-search
  - agentforce
  - einstein-trust-layer
  - prompt-grounding
inputs:
  - "Data Cloud org with a Data Cloud license (search index configurations are not available under Customer Data Platform licenses)"
  - "Source content: Salesforce Knowledge articles, Data Cloud DMOs, external documents ingested via Data Cloud connector"
  - "Agentforce agent or Einstein Copilot to which grounding will be attached"
  - "Embedding model choice (E5-Large V2, Multilingual E5-Large, or Whisper-Large-V3 for audio)"
  - "Chunking strategy, max tokens per chunk, filter fields, and number of results"
outputs:
  - "Configured Data Cloud vector search index with chosen embedding model and chunking settings"
  - "Retriever configuration (default or custom, in Einstein Studio) used by a prompt template or an Einstein Data Library"
  - "Access plan: Data Cloud permission sets for retriever authors and prompt runners"
  - "Validated end-to-end RAG flow: source content → chunked embeddings → semantic retrieval → grounded prompt → LLM response"
  - "Decision record documenting chunking strategy, max tokens, number of results, filters, and embedding model rationale"
dependencies:
  - prompt-builder-templates
  - einstein-trust-layer
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# RAG Patterns in Salesforce

This skill activates when an Agentforce agent or a Prompt Builder template needs to retrieve and incorporate content from a knowledge source at inference time using Data Cloud search. It covers the full RAG pipeline: ingesting source content into Data Cloud, configuring search indexes (vector or hybrid), choosing chunking and embedding settings, connecting a retriever to a prompt template or an Einstein Data Library, and how the Einstein Trust Layer treats retrieved content.

Correction (2026-10-03): earlier versions of this skill described a "Grounding record" on a subagent with `top_k` and a `{!topic.product}` filter, and a `{!grounding.chunks}` merge field. None of these appear in the Generative AI guide or the Data Cloud guide. The documented model is: a search index creates a default retriever, custom retrievers are built in Einstein Studio, and a retriever is added to a prompt template from the Resource picker; for agents, an Einstein Data Library creates the index, retriever, prompt template, and Answer Questions with Knowledge action.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Data Cloud is provisioned with a Data Cloud license. The Data Cloud feature table lists "Unstructured Data and Search Index Configurations" as available with Data Cloud licenses and not with Customer Data Platform licenses. UNVERIFIED (2026-10-03): the earlier claim that a "Vector Search add-on" on Data Cloud Starter is required.
- Identify the source content: Salesforce Knowledge, uploaded files (up to 4 MB text or HTML, 100 MB PDF), a DMO with text fields, or unstructured data from a connector.
- Decide whether an Einstein Data Library is enough. It creates the data stream, search index, retriever, prompt template, and standard action with defaults, which is the fastest path for agents.
- Clarify data residency and sensitivity. Data masking is disabled for agents, so retrieved text reaches the LLM as written; secure data retrieval follows the running user's access.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What is the content: Knowledge HTML, PDFs, transcripts, or DMO text?" | Passage extraction uses HTML structure, PDF chunking depends on encoding, and tables can't be chunked (Gotcha 1) | A chunking strategy per source | Chunks follow the document's real sections |
| "Which languages is the content in?" | Max tokens default to 512, and non-Latin text can exceed it, so text drops out of the embedding (Gotcha 2) | A max-token setting and embedding model per language | Japanese or Chinese content is fully embedded |
| "Which fields will narrow results (product, region, category)?" | Retriever filters only use fields defined as filter fields on the index, up to 10 conditions (Gotcha 3) | Filter fields designed into the index | Product-scoped answers without a second index |
| "How many search indexes already exist in this Data Cloud instance?" | The limit is 10 search indexes per instance (Gotcha 4) | An index budget across teams | The next team is not blocked by a forgotten test index |
| "How will the configuration reach production?" | Change sets and Metadata API deployments don't include the retriever or search index (Gotcha 5) | Data kit or rebuild steps for the target org | Templates deploy into an org where their retriever exists |
| "Does any content need customer-managed key encryption?" | Search indexes don't support encryption with customer-managed keys (Gotcha 6) | A decision on which content may be indexed | Compliance is checked before indexing, not after |

---

## Core Concepts

### 1. Search Index (Vector or Hybrid)

A search index "stores chunked and vectorized data that can be searched and retrieved from other applications." It lives in a data space and is associated with a DMO. Creating one makes a chunk DMO and an index DMO. Use vector search for semantic matches and hybrid search when queries include exact terms such as product codes.

| Setting | What the guides say |
|---|---|
| Chunking strategy | Semantic-based passage extraction (HTML headings, lists, and bold subheadings are passage boundaries), window-based passage extraction, conversation-based (audio and video transcripts), prepend fields (for example, Title on each Knowledge chunk) |
| Max tokens | "In Data Cloud, the max token limit is set to 512 by default." Use a lower limit for non-Latin languages |
| Embedding model | E5-Large V2, Multilingual E5-Large, Whisper-Large-V3. Easy Setup defaults: passage extraction, E5-Large V2, hybrid search. UNVERIFIED (2026-10-03): the earlier claim that custom embedding models can be registered through Model Builder |
| Chunk overlap | UNVERIFIED (2026-10-03): the earlier "10 to 20% overlap" guidance was not found in the Data Cloud guide, which documents no overlap setting |
| Pre-filter fields | Up to 10 fields; text values up to 1,024 characters |

### 2. Retrievers

"When a search index is created in Data Cloud, a default retriever is created automatically. You can't customize a default retriever." Custom retrievers are built in Einstein Studio: pick the data space, DMO, and index; add up to 10 filter conditions (only on the index's filter fields); choose output fields and the maximum number of results. Each save creates a new version, and "Only one version of a retriever can be active."

In a prompt template, add the retriever from the Resource field and tune it in the Configuration panel: Search Text (limited to 255 characters, globals, and prompt inputs; it can't use related lists, Flow, or Apex), Output Fields, and Number of Results. Retrieved data appears in the preview resolution as JSON.

> **Terminology.** Agent *topics* were renamed *subagents* in April 2026, with no
> change to functionality. This skill leads with *subagent* in prose, and keeps
> *topic* in metadata names, merge fields such as `{!topic.…}`, and search
> keywords, because those did not change.

### 3. Einstein Data Library (Agents)

A data library "automates several configuration steps across Data Cloud and Prompt Builder," creating data streams, a search index, and a retriever. The Answer Questions with Knowledge action answers from the library. A library uses Knowledge or file uploads, not both, and neither the data space nor the source can be changed later. Each feature uses one data library at a time. For Knowledge, choose identifying and content fields, optionally restrict to public articles or data categories, and turn on Show sources for citations.

### 4. Einstein Trust Layer and Retrieved Content

Grounding uses only data the running user can access. For prompt templates, pattern-based masking scans all prompt text, including retrieved chunks; field-based masking covers only record merge fields and related lists. For agents, masking is disabled. Audit data records the hydrated prompt, masked prompt, and retrieved data. UNVERIFIED (2026-10-03): the earlier claim that the Trust Layer can restrict which indexes an agent may query through org-level grounding policies.

---

## Common Patterns

### Pattern 1: Knowledge Grounding for a Service Agent With a Data Library

**When to use:** A service agent must answer from Salesforce Knowledge with citations.

**How it works:**
1. In Einstein Data Library setup, create a library in the right data space (it can't be changed later).
2. Choose Knowledge, select identifying fields (title, summary) and content fields (resolution steps), and filter by data categories if the base is large.
3. Turn on Show sources and set the Knowledge domain URL for citations.
4. Save; data streams, the search index, and the retriever are created. Assign the library to the agent in Agent Builder (Knowledge tab).
5. Test in the agent preview with real questions and check that sources point at the right articles.

**Why not the alternative:** Without retrieval the agent relies on training data, which does not reflect org-specific content.

### Pattern 2: Filtered Retrieval by Product Line

**When to use:** One index holds documents for several products, and answers must stay within one.

**How it works:**
1. Add `Product_Line__c` as a filter field when creating the search index (advanced setup).
2. In Einstein Studio, create a custom retriever with a condition `Product_Line__c` equals `CRM` (up to 10 conditions; All Conditions Are Met or Any Condition Is Met), output fields, and number of results. Activate it.
3. Use one retriever per product, or a dynamic retriever where a standard template supports one. UNVERIFIED (2026-10-03): passing a runtime value from the conversation into a retriever filter was not found in a fetched source.

**Why not the alternative:** Semantic similarity alone mixes products that share vocabulary.

### Pattern 3: Prompt Template With a Retriever Resource

**When to use:** A template must combine CRM fields and retrieved passages.

**How it works:**
1. In Prompt Builder, insert record merge fields for the context, then select Resource > Einstein Search > the DMO > the retriever.
2. In the Configuration panel, build the Search Text from prompt inputs (for example `account name: Input.Account.Name`), pick output fields such as Chunk, and set the number of results.
3. Put instructions after the context block and tell the model to answer only from the retrieved passages.
4. Preview and read the retriever's JSON output in the resolution.

**Why not the alternative:** Unbounded results crowd out the record context the template also needs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agent answers from Knowledge or uploaded files | Einstein Data Library | Creates index, retriever, template, and action with defaults |
| Source is HTML Knowledge with clear headings | Semantic-based passage extraction, keep the HTML | Headings and lists become passage boundaries |
| Queries include product codes or exact terms | Hybrid search index | Combines vector similarity with keyword precision |
| Multi-product content in one index | Filter fields on the index plus custom retrievers | Filters apply only to fields the index defines |
| Non-Latin content | Max tokens below 512, Multilingual E5-Large | Punctuation-based token estimates can exceed the embedding limit |
| Deploying to another org | Data kit for the search index configuration, then create the retriever before deploying templates | Change sets and Metadata API don't carry retrievers or indexes |

---

## Recommended Workflow

1. Answer the Questions table: content types and languages, filter fields, index budget, deployment path, and encryption constraints.
2. Choose the path: an Einstein Data Library for agents, or a search index (Easy or Advanced setup) plus a custom retriever for prompt templates.
3. Configure chunking (strategy, max tokens, prepend fields), the embedding model, and filter fields; record the choices in the decision record.
4. Build and activate the retriever, add it to the prompt template or library, and preview with representative questions; read the retrieved JSON.
5. Run `python3 scripts/check_rag_patterns_in_salesforce.py --manifest-dir <project>` to catch retriever search-text limits, number-of-results budgets, and leftover merge fields from older guidance.
6. Plan deployment: data kit for the index configuration, retriever recreated in the target org before templates deploy (`references/metadata-examples.md`), and a test as each persona.

---

## Review Checklist

Run through these before marking RAG grounding work complete:

- [ ] Data Cloud license confirmed; search index count under the 10-per-instance limit
- [ ] Chunking strategy fits the content (HTML kept for passage extraction; tables avoided in PDFs)
- [ ] Max tokens and embedding model fit the languages in the content
- [ ] Filter fields defined on the index for every retriever condition
- [ ] Retriever activated; search text within 255 characters using only globals and prompt inputs
- [ ] Number of results sized against the prompt's other context
- [ ] Preview tested with at least 5 representative queries as the target user
- [ ] Deployment plan covers the data kit and retriever creation in the target org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Stripping HTML removes the structure the chunker uses**: Correction (2026-10-03): earlier versions said to strip HTML from Knowledge bodies before indexing. Semantic-based passage extraction "uses the semantic meaning inherent in HTML tags to chunk a document into passages," and passage extraction "work[s] best for HTML files."

2. **Metadata Filters Are Pre-Filters, Not Post-Filters**: Filter fields are selected for pre-filtering on the index (up to 10). A filter that matches nothing leaves no candidates. UNVERIFIED (2026-10-03): the earlier advice to prefer `LIKE` over exact match; check the supported operators in the Search Index Reference.

3. **Masking does not clean retrieved chunks for agents**: Data masking is disabled for agents. For prompt templates, pattern-based masking scans retrieved text for its listed data types only.

4. **Index refresh follows the data stream**: UNVERIFIED (2026-10-03): the earlier statement that new data streams default to scheduled batch refresh and that continuous mode must be configured was not found in a fetched source. Test how soon a newly published article becomes retrievable.

5. **Number of results counts against the prompt**: Each retrieved chunk is added to the prompt. With max tokens at 512, ten results can add roughly 5,000 tokens before any other context.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search index configuration | Chunking strategy, max tokens, embedding model, search type, filter fields; deployable via data kit |
| Retriever | Default or custom retriever with filters, output fields, number of results, and active version |
| Decision record | Chunking, max tokens, embedding model, filters, number of results, and residency rationale |
| Prompt template or data library | The consumer of the retriever, with preview evidence |
| Agent preview test results | Minimum 5 representative queries with retrieved passages or sources |

---

## Related Skills

- `prompt-builder-templates` — Use alongside this skill to construct the prompt template that receives grounding merge fields; controls how retrieved chunks are positioned in the prompt body
- `einstein-trust-layer` — Governs masking, zero-retention, and audit logging policies that apply to retrieved chunks before they reach the LLM
- `agentforce-agent-creation` — Prerequisite skill for creating the subagent to which a Grounding configuration is attached
- `model-builder-and-byollm` — Use when the default Salesforce-managed embedding model is insufficient and a custom embedding model must be registered for the vector index
- `agent-topic-design` — Informs how subagents are scoped so that retrieval is triggered on the right turns and metadata filter merge fields are available at runtime
