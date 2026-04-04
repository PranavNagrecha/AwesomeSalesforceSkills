# Examples — RAG Patterns in Salesforce

## Example 1: Grounding a Service Agent with Salesforce Knowledge Articles

**Context:** A telecommunications company runs an Agentforce service agent to handle billing and technical support questions. The contact center has 2,400 published Knowledge articles. Without grounding, the agent gives generic answers and cannot reference org-specific troubleshooting steps.

**Problem:** The agent responds with LLM training data rather than the company's actual resolution procedures. When a customer asks about a specific modem model's firmware reset process, the agent describes a generic router reset that does not match the device.

**Solution:**

Step 1 — Connect Knowledge to Data Cloud via CRM connector. Map `KnowledgeArticleVersion` to a DMO named `KnowledgeArticle__dlm`. Include fields: `Title`, `Body__c` (HTML-stripped via transformation), `ArticleType`, `Language`.

Step 2 — Create a vector search index on `KnowledgeArticle__dlm.Body__c`:
```
Index name:       knowledge_rag_index
Embedding model:  Salesforce managed (sfdc-text-embedding-ada-002 equivalent)
Chunk size:       512 tokens
Chunk overlap:    64 tokens
Refresh mode:     Continuous (near-real-time)
```

Step 3 — In Agentforce Setup, open the "Technical Support" agent topic and add a Grounding record:
```
Vector Index:     knowledge_rag_index
Top-K:            5
Metadata filter:  ArticleType = 'Technical'
```

Step 4 — Test in Agent Preview. The Grounding tab shows which article chunks were retrieved. Confirm retrieved chunks cite the correct modem model documentation.

**Why it works:** The semantic query derived from the customer's message ("modem firmware reset") matches the embedding of the relevant article body at a high cosine similarity score, ranking it above generic content. The `ArticleType = 'Technical'` filter prevents billing articles from appearing in technical queries.

---

## Example 2: Filtered Retrieval Across a Multi-Product Knowledge Base

**Context:** A software company supports three distinct product lines (CRM, ERP, HR). All product documentation is stored in a single Data Cloud vector index on a `ProductDoc__dlm` DMO. A single Agentforce agent handles all product lines, but the current conversation context establishes which product the customer is using.

**Problem:** Without filtering, a query like "how do I reset my password" retrieves chunks from all three product lines. The top-5 results may include two CRM chunks, two ERP chunks, and one HR chunk. The agent's response blends instructions from different UIs and confuses the customer.

**Solution:**

Step 1 — Ensure the DMO includes a `Product_Line__c` field populated during ingest (e.g., derived from the source folder or document tag).

Step 2 — In the agent topic context variables, resolve the current product line from the CRM record (e.g., `Account.Product_Line__c` from the linked account).

Step 3 — Configure the Grounding metadata filter:
```
Product_Line__c = '{!topic.currentProductLine}'
```

Where `topic.currentProductLine` is a context variable resolved from the active case or account record at topic invocation.

Step 4 — Verify with the Grounding tab in Agent Preview: submit "reset my password" with `currentProductLine = 'CRM'` — confirm all 5 returned chunks are CRM-specific.

**Why it works:** The pre-filter reduces the ANN candidate set to only CRM documents before similarity ranking. The agent receives a clean, product-scoped context and generates a product-accurate response.

---

## Example 3: Prompt Template with Explicit Grounding Merge Field Placement

**Context:** A financial services firm uses a Flex prompt template in Prompt Builder to generate case summaries. The template must include both CRM record fields (case details) and retrieved chunks from an internal policy document index.

**Problem:** Without explicit merge field placement, retrieved policy chunks appear at the top of the system prompt, above the role-framing instruction. The LLM treats the policy text as part of its persona rather than as reference material, producing responses that blend policy language into the agent's voice inappropriately.

**Solution:**

Prompt template structure (Flex template in Prompt Builder):
```
You are a financial services case assistant. Your role is to summarize cases accurately
and cite internal policy when relevant. Do not invent policy details not present in the
provided context.

## Case Details
Account: {!$Record.Account.Name}
Case Number: {!$Record.CaseNumber}
Subject: {!$Record.Subject}
Description: {!$Record.Description}

## Relevant Policy Context
{!grounding.chunks}

## Task
Summarize the case and identify which policy sections, if any, apply to the customer's
situation. If no policy chunk is relevant, state that explicitly.
```

The `{!grounding.chunks}` merge field is placed after CRM record fields and before the task instruction, ensuring the LLM treats retrieved content as reference material within the established role frame.

**Why it works:** The LLM processes the system prompt sequentially. Role and instruction framing precede the retrieved context, so the model applies the role frame to its interpretation of the retrieved policy text rather than being role-framed by the policy text itself.

---

## Anti-Pattern: Indexing Raw HTML from Knowledge Article Body

**What practitioners do:** Map the `Body` field from `KnowledgeArticleVersion` directly to the vector index without any transformation, treating it as plain text.

**What goes wrong:** Knowledge article bodies contain HTML markup (`<p>`, `<ul>`, `<li>`, `<strong>`, `&nbsp;`, inline styles). The embedding model encodes HTML tags as semantic content. Chunks become dominated by tag tokens, lowering the signal-to-noise ratio of embeddings. Similarity scores for semantically relevant articles drop, and irrelevant articles with structurally similar HTML patterns may score higher than content-relevant ones.

**Correct approach:** Apply an HTML-stripping transformation in the Data Cloud Data Transform before the field is written to the DMO used for indexing. Data Cloud supports JavaScript-style string transformations in Data Transforms; use a regex or parse-based strip to remove all HTML tags and decode HTML entities before the `Body` field value reaches the vector index.
