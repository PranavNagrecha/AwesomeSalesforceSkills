# Gotchas: Data Cloud Grounding for Agentforce

Gotchas 1 to 7 are carried from the earlier version and now state what an official source supports. Gotchas 8 to 13 are cited platform facts.

## Gotcha 1: Retrievers do not follow CRM sharing

**What happens:** The agent grounds an answer in an article or file chunk that the CRM sharing model would have hidden from the user.

**When it occurs:** The design assumes record-level sharing applies to retrieved content.

**How to avoid:** Treat retriever access as a Data Cloud question: review the Data Cloud permission sets and the data space that govern each retriever, scope Knowledge libraries by data category, and keep restricted content out of shared libraries.

**Source:** Generative AI guide (Spring '26), Ground with Retrieval Augmented Generation: "Access to retrievers and their data is controlled by the Data Cloud permission sets"; Agentforce Developer Guide, Knowledge Library Example (data categories "restrict what the knowledge library is allowed to search").

---

## Gotcha 2: New content is not searchable the moment it is saved

**What happens:** An article published at 9:00 is not in answers at 9:05.

**When it occurs:** The library or its index is still processing, or the SLA assumed instant availability.

**How to avoid:** State a freshness window per subagent. For truly live data, use an action that reads the record at answer time instead of a retriever. After creating or changing a library, check its status before testing.

**Source:** Generative AI guide, Manage Data Sources ("it can take a few minutes for the preview conversation to update"); Agentforce Developer Guide, Knowledge Library Example (status moves to READY after chunking and embedding). UNVERIFIED (2026-10-03): ingestion latency figures for streaming versus batch data.

---

## Gotcha 3: Index updates are a pipeline, and you cannot edit mid-run

**What happens:** A library update fails, or recent edits are missing from answers.

**When it occurs:** Changes are made while indexing is running, or nobody re-indexes after content changes.

**How to avoid:** Wait for `READY` (or every stage `SUCCESS`) before changing a library. Schedule re-indexing as part of content operations.

**Source:** Agentforce Developer Guide, Knowledge Library Example ("You can't update a library while indexing is in progress"; READY requires chunking and embedding to complete for the search index).

---

## Gotcha 4: More results is not better results

**What happens:** Raising the number of results to "be safe" makes answers slower and less focused.

**When it occurs:** Number of Results is set high by default.

**How to avoid:** Start small and tune Number of Results and Output Fields per template; return only the fields the answer needs.

**Source:** Generative AI guide, Ground with Retrieval Augmented Generation (Retriever Settings: Number of Results, Output Fields; by default all fields defined in the retriever are added to the prompt). UNVERIFIED (2026-10-03): the earlier specific guidance of k=5 with reranking to 1 to 3, and the "lost in the middle" effect; no source read quantifies them.

---

## Gotcha 5: Grounded text is copied, logged and stored

**What happens:** Sensitive content placed in a library shows up in audit data, and deleting it from the source does not delete every copy.

**When it occurs:** Libraries are built over content with personal or regulated data.

**How to avoid:** Keep personal and regulated data out of libraries. If audit data collection is on, include its Data Cloud objects in your deletion procedure.

**Source:** Generative AI guide, Einstein Audit and Feedback Data (audit data includes "Retrieved data" and the hydrated prompt, stored in the default Data Cloud data space; delete by removing the data lake objects). UNVERIFIED (2026-10-03): the earlier claim that individuals can be re-identified from embeddings.

---

## Gotcha 6: Mixed-language content can degrade retrieval

**What happens:** Answers in one language cite chunks from another, or miss relevant content.

**When it occurs:** One library holds content in several languages.

**How to avoid:** Segment libraries by language or test multilingual retrieval explicitly before launch.

**Source:** UNVERIFIED (2026-10-03): no source read addresses multilingual retrieval quality. Related and documented: when adding agent languages, consider the regions and languages where the Trust Layer detects sensitive data (Generative AI guide, Update Language Settings).

---

## Gotcha 7: Source links break when content moves

**What happens:** A cited source opens a 404, or a public URL instead of the internal one.

**When it occurs:** Articles are archived but remain indexed, or the Knowledge domain URL was never configured.

**How to avoid:** Configure the Knowledge domain URL when you turn on Show sources, and re-index after archiving content.

**Source:** Generative AI guide, Select Data Library Fields ("To link to a source, your Knowledge domain URL is concatenated with the knowledge article URL ... If you don't include a specific Knowledge domain URL, Einstein uses the publicly available URL").

---

## Gotcha 8: A library's data space and source type are fixed at creation

**What happens:** A team needs to add uploaded PDFs to its Knowledge library, or move it to another data space, and has to rebuild it.

**When it occurs:** The library is created before the content plan is settled.

**How to avoid:** Choose the data space and the source (Knowledge or file upload) deliberately; create separate libraries for different sources. For Knowledge libraries, choose the two primary index fields with the same care, since they are immutable too.

**Source:** Generative AI guide, Add a Data Library ("After you choose a data space, you can't change it later") and Choose A Data Source for Your Library ("A data library can't support Knowledge and file uploads simultaneously ... After you choose a library's data source, you can't change it later"); Salesforce CLI `sf agent adl create --help` (primary index fields "immutable after creation").

---

## Gotcha 9: Each feature uses one library at a time

**What happens:** A design gives one agent a Knowledge library and a file library, and only one is used.

**When it occurs:** Libraries are planned per content source rather than per feature.

**How to avoid:** Plan one library per feature, or build a custom retriever and a retriever-type library when several sources must be searched together.

**Source:** Generative AI guide, Assign Data Libraries to Features ("each feature can use one data library at a time"); Salesforce CLI `sf agent adl create --help` (`retriever` source type for an existing active custom retriever).

---

## Gotcha 10: Retrievers and search indexes do not deploy

**What happens:** A prompt template that uses a retriever deploys to production and fails, because the retriever is not there.

**When it occurs:** Grounding is promoted with change sets or Metadata API like other metadata.

**How to avoid:** Create the library (and so the retriever and search index) in each target org with a script, then deploy the template.

**Source:** Generative AI guide, Limitations for Einstein Search: "the change sets don't include the retriever or search index metadata. You must manually create the retriever in the destination org before deploying ... This rule applies to change sets and Metadata API deployments."

---

## Gotcha 11: Retriever search text is short and comes only from prompt inputs

**What happens:** A team builds the retriever query from a flow output or a related list, and it cannot be configured; or a long case description is cut short as the query.

**When it occurs:** The search text design assumes any data source.

**How to avoid:** Build search text from globals and prompt inputs only, within 255 characters. Pass a short question or keyword input into the template rather than a long field.

**Source:** Generative AI guide, Ground with Retrieval Augmented Generation ("The search text input to the retriever is limited to 255 characters, globals, and prompt inputs"; "It can't use other sources, such as related list, Flow, or Apex").

---

## Gotcha 12: Retiring a retriever means cleaning every template version

**What happens:** A retriever cannot be deactivated or deleted, and the error points at prompt templates nobody uses any more.

**When it occurs:** Old template versions still reference the retriever.

**How to avoid:** Remove the retriever from every version of every template that uses it before retiring it. Track retriever usage in the design document.

**Source:** Generative AI guide, Ground with Retrieval Augmented Generation: "Deleting or deactivating a retriever in Einstein Studio requires that references to it are removed from any version of any prompt templates that use it."

---

## Gotcha 13: Upload size limits are per file type

**What happens:** Large text exports fail to upload while larger PDFs succeed.

**When it occurs:** File libraries are loaded without checking limits.

**How to avoid:** Keep text and HTML files at 4 MB or less and PDFs at 100 MB or less; split larger files.

**Source:** Generative AI guide, Select Files to Upload: "You can upload up to 4 MB for text or HTML files, or 100 MB for PDF files."
