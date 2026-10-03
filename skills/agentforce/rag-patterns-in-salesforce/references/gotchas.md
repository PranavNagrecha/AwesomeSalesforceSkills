# Gotchas: RAG Patterns in Salesforce

Non-obvious behaviours that make retrieval return the wrong passages, nothing at all, or something that cannot be deployed. Each gotcha names its source. "Data Cloud Guide" means the Data Cloud guide, Summer '26 (data_cloud.pdf), chapters Use Search for AI, Automation, and Analytics, Use AI Models (Retrievers), and Data Cloud Limits and Guidelines. "GenAI Guide" means Quickstart Your Einstein Generative AI Solution, Spring '26 (generative_ai.pdf).

## Gotcha 1: Stripping HTML From Knowledge Removes the Chunk Boundaries

**What happens:** A team strips HTML from article bodies before indexing, and chunks start running across sections, mixing two procedures in one passage.

**When it occurs:** "Semantic-based passage extraction uses the semantic meaning inherent in HTML tags to chunk a document into passages. HTML elements such as headings (<h1>), lists (<ul>), or even bold text (<strong>) acting as a subheading, are considered logical boundaries." "Passage extraction chunking strategies work best for HTML files. For PDF files, passage-extraction chunking depends on how the text has been encoded." Text and HTML files "Can't chunk files with tabular data." Correction (2026-10-03): earlier versions of this skill said HTML corrupts embeddings and must be stripped.

**How to avoid:** Keep well-formed HTML with real headings and block tags. Fix articles that use line breaks instead of headings. Add the Title as a prepend field so every chunk carries its article's name. Convert tables to prose before indexing.

**Source:** Data Cloud Guide, Chunking Strategies (Semantic-based Passage Extraction; Window-based Passage Extraction; Prepend Field Chunking); Search Index Reference (Supported File Formats).

---

## Gotcha 2: Non-Latin Text Can Overflow the 512-Token Chunk

**What happens:** Japanese articles retrieve poorly while English ones work.

**When it occurs:** "In Data Cloud, the max token limit is set to 512 by default." Data Cloud estimates tokens from words for Latin-based languages and from punctuation marks for non-Latin languages, so "512 punctuation marks can exceed 512 tokens... not all text that is included in the chunk gets included in the embedding."

**How to avoid:** Set a max token limit below 512 for non-Latin content, and choose Multilingual E5-Large where content is multilingual (supported models: E5-Large V2, Multilingual E5-Large, Whisper-Large-V3).

**Source:** Data Cloud Guide, How the Max Token Setting Affects Chunking; Search Index Reference (Supported Embedding Models).

---

## Gotcha 3: Retriever Filters Only Work on the Index's Filter Fields

**What happens:** In Einstein Studio, the Filter Documents to Return option is missing, or the product field the team wants is not in the list.

**When it occurs:** "Retriever filters are available only if the search index that you selected has filter fields defined." A custom retriever takes "up to 10 conditions," and an index allows at most 10 pre-filter fields with text values up to 1,024 characters. In a prompt template, the retriever's Search Text "is limited to globals and prompt inputs. It can't use other sources, such as related list, Flow, or Apex," and is limited to 255 characters.

**How to avoid:** Design filter fields when creating the index (Advanced Setup), and keep search text short and built from prompt inputs. UNVERIFIED (2026-10-03): the earlier `{!topic.product}` filter syntax on a subagent "Grounding record" is not documented anywhere fetched.

**Source:** Data Cloud Guide, Create a Custom Retriever (step 3); Unstructured Data and Search Index Guidelines and Limits. GenAI Guide, Ground with Retrieval Augmented Generation (Retriever Settings; Considerations).

---

## Gotcha 4: Ten Search Indexes Per Data Cloud Instance, and Deletion Has an Order

**What happens:** A new project cannot create its index, and an admin cannot delete an old one.

**When it occurs:** The limit is 10 search indexes per Data Cloud instance. "Before a search index can be deleted, all retrievers associated with the search index, including the default retriever, must be deleted." A retriever can be deleted only "if it has no dependencies from prompt templates," and Prompt Builder requires removing references from "any version of any prompt templates that use it" before a retriever is deleted or deactivated. Deleting an unstructured data lake object with an index also requires deleting the retrievers, then the index.

**How to avoid:** Keep an index register with owners. Retire indexes by removing retriever references from every template version, deleting custom and default retrievers, then deleting the index.

**Source:** Data Cloud Guide, Unstructured Data and Search Index Guidelines and Limits; Delete a Retriever; Delete a UDLO With a Search Index. GenAI Guide, Ground with Retrieval Augmented Generation (Active Retrievers).

---

## Gotcha 5: Retrievers and Indexes Don't Deploy With the Prompt Template

**What happens:** A template deploys to production and fails because its retriever does not exist there.

**When it occurs:** "If a prompt uses an Einstein Search retriever, the change sets don't include the retriever or search index metadata. You must manually create the retriever in the destination org before deploying the retriever. This rule applies to change sets and Metadata API deployments." Search index configurations can be added to a data kit and recreated from it.

**How to avoid:** Deploy the index configuration through a data kit, create the retriever in the target org with the same API name, then deploy the templates. Keep the retriever settings (filters, output fields, number of results) in the decision record so they can be rebuilt exactly.

**Source:** GenAI Guide, Prompt Builder Limitations (Limitations for Einstein Search). Data Cloud Guide, Add a Search Index Configuration to a Data Kit; Create a Search Index Configuration from a Data Kit.

---

## Gotcha 6: Search Indexes Don't Support Customer-Managed Keys

**What happens:** A compliance review finds indexed content that policy says must be encrypted with the org's own key.

**When it occurs:** "Search indexes don't support encryption with customer managed keys. Data in search indexes cannot be encrypted with customer managed keys when customers enable this capability in Data Cloud."

**How to avoid:** Classify content before indexing, and keep content that requires customer-managed key encryption out of search indexes.

**Source:** Data Cloud Guide, Use Search for AI, Automation, and Analytics (note).

---

## Gotcha 7: Oversized Files Are Stored but Never Chunked

**What happens:** A 6 MB HTML manual uploads without error and is never retrieved.

**When it occurs:** Text or HTML files larger than 4 MB, and PDFs larger than 100 MB, "are added to unstructured data lake objects and unstructured data model objects, but they aren't chunked or vectorized." Data library uploads carry the same limits ("up to 4 MB for text or HTML files, or 100 MB for PDF files").

**How to avoid:** Split large documents before upload and check that each file produced chunks in the chunk DMO.

**Source:** Data Cloud Guide, Unstructured Data and Search Index Guidelines and Limits. GenAI Guide, Select Files to Upload (note).

---

## Gotcha 8: A Data Library's Data Space and Source Are Permanent

**What happens:** A team builds a library on uploaded files, later wants Knowledge, and has to start over.

**When it occurs:** "After you choose a data space, you can't change it later." "A data library can't support Knowledge and file uploads simultaneously... After you choose a library's data source, you can't change it later." "Each feature can use one data library at a time."

**How to avoid:** Decide the data space and source before creating the library. Use separate libraries for Knowledge and files, and remember each feature uses only one.

**Source:** GenAI Guide, Add a Data Library; Choose A Data Source for Your Library; Assign Data Libraries to Features.

---

## Gotcha 9: Masking Doesn't Clean Retrieved Text for Agents

**What happens:** A retrieved transcript containing a customer's phone number appears in an agent's prompt as written.

**When it occurs:** "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents." For prompt templates, pattern-based masking scans all prompt text but only for its listed data types, and field-based masking covers only record merge fields and related lists. Correction (2026-10-03): earlier versions said masked fields inside chunks are redacted and silently empty chunks.

**How to avoid:** Keep sensitive values out of indexed content, choose output fields deliberately, and review the GenAIGatewayRequest audit report for what was actually sent.

**Source:** GenAI Guide, Agentforce Agents (Einstein Trust Layer section); Large Language Model Data Masking; Generative AI Audit and Feedback Data (retrieved data collected).
