# LLM Anti-Patterns: Data Cloud Grounding for Agentforce

Mistakes AI assistants make when designing grounding for an agent, why they make them, and the correct move.

## Anti-Pattern 1: Pack Facts Into the Subagent Prompt

**What the LLM generates:** A subagent instruction that embeds lists of policies, SKUs or account statuses.

**Why it happens:** The subagent prompt feels like the obvious place for context.

**Correct pattern:** Facts go in a retriever or an action; subagents hold rules and behaviour. This lets facts change without a new agent version. The guide's own advice is to start with minimal instructions and add them one by one.

## Anti-Pattern 2: Vectorize Structured Data

**What the LLM generates:** "Create vector embeddings of all Account fields."

**Why it happens:** Retrieval is treated as a single hammer.

**Correct pattern:** Read structured records with an action at answer time; use retrieval for unstructured content such as articles, files and transcripts. RAG in Data Cloud is described as grounding prompts with content from a search index built by chunking and vectorizing unstructured data.

## Anti-Pattern 3: Skip Citations

**What the LLM generates:** An agent response with no source.

**Why it happens:** Citations feel like UX polish.

**Correct pattern:** Turn on sources for the library (with the Knowledge domain URL configured), enable citations on prompt templates (`isCitationEnabled`), and leave the Agent Script `citation` runtime switch on for knowledge-grounded agents. Citations are debugging infrastructure as much as transparency.

## Anti-Pattern 4: Trust the LLM to Redact

**What the LLM generates:** "Prompt the model to hide fields the user should not see."

**Why it happens:** Defense-in-depth is confused with a primary control.

**Correct pattern:** Never let restricted content reach the prompt. Control retriever access through Data Cloud permission sets and data spaces, scope libraries by data category, and choose Output Fields narrowly. For agents, Trust Layer data masking is disabled, so there is no masking backstop either.

## Anti-Pattern 5: Large Number of Results Everywhere

**What the LLM generates:** Number of Results set high "because more context is better".

**Why it happens:** It sounds safe.

**Correct pattern:** Start low and tune per template, and limit Output Fields; by default every field defined in the retriever is added to the prompt.

## Anti-Pattern 6: No Freshness Contract

**What the LLM generates:** A retriever over batch-ingested content with no documented staleness window.

**Why it happens:** Freshness is invisible until users complain.

**Correct pattern:** Write the window into the subagent design, check library status after content changes, and use an action for anything that must be live.

## Anti-Pattern 7: Assuming the Retriever Deploys With the Template

**What the LLM generates:** A release plan that moves a retriever-backed prompt template with a change set or `sf project deploy` and stops there.

**Why it happens:** Every other dependency travels with the metadata.

**Correct pattern:** Create the library, and therefore the retriever and search index, in each target org with a script (`sf agent adl create` or the ADL API), then deploy the template. The Generative AI guide states that change sets and Metadata API deployments do not include retriever or search index metadata.

## Anti-Pattern 8: Building Retriever Search Text From Apex or Flow Output

**What the LLM generates:** "Call a flow to build the search query, then pass its output into the retriever's search text."

**Why it happens:** Assistants assume any merge source is allowed.

**Correct pattern:** Search text accepts globals and prompt inputs only, up to 255 characters. Compute the query upstream and pass it in as a prompt input.

## Anti-Pattern 9: One Library for Knowledge and Files

**What the LLM generates:** A plan to add uploaded PDFs to an existing Knowledge library.

**Why it happens:** A library sounds like a folder.

**Correct pattern:** A library supports either Knowledge or file uploads, and the choice cannot change after creation. Create one library per source, and remember each feature uses one library at a time; use a custom retriever library when sources must be searched together.
