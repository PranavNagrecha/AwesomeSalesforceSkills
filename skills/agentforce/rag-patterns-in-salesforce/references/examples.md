# Examples: RAG Patterns in Salesforce

Steps and limits come from the Generative AI guide (Einstein Data Library; Ground with Retrieval Augmented Generation; Add a Retriever to a Prompt Template) and the Data Cloud guide (Chunking Strategies; Create a Custom Retriever; Search Index Reference), Summer '26. Correction (2026-10-03): earlier versions of these examples used a subagent "Grounding record," `Top-K`, a `{!topic.currentProductLine}` filter, `{!grounding.chunks}`, and HTML stripping. None of those are documented; the procedures below replace them.

## Example 1: Grounding a Service Agent With Salesforce Knowledge Through a Data Library

**Context:** A telecom contact center runs an Agentforce service agent with 2,400 published Knowledge articles. Without grounding, the agent describes a generic router reset instead of the device-specific firmware procedure.

**Solution (configuration procedure):**

1. Setup > Einstein Data Library > New Library. Choose the data space carefully; it can't be changed later. Name it `Support_Knowledge`.
2. Edit the library, open the Knowledge tab (a library holds Knowledge or files, never both, and the choice is permanent).
3. Identifying fields: Title and Summary. Content fields: the article body field that holds troubleshooting steps.
4. Knowledge Settings: turn on Filter by Knowledge Data Categories and select the Technical Support categories; turn on Show sources and enter the Knowledge domain URL.
5. Save. Data streams, a search index, and a retriever are created and visible in Data Cloud.
6. In Agent Builder, Knowledge tab, select `Support_Knowledge` as the data library and save. The Answer Questions with Knowledge action now answers from it.
7. Preview with real questions ("How do I reset the firmware on the X200 modem?") and confirm the cited sources are the X200 articles.

**Why it works:** The library uses passage extraction on the article HTML, so headings and lists become chunk boundaries, and data categories keep billing articles out of technical answers. Keep the article HTML intact; stripping it would remove those boundaries.

---

## Example 2: Product-Scoped Retrieval With a Custom Retriever

**Context:** One `ProductDoc` DMO holds documentation for CRM, ERP, and HR products. "How do I reset my password" returns a mix of all three.

**Solution (configuration procedure):**

1. Create the search index with Advanced Setup on the `ProductDoc` DMO and add `Product_Line__c` as a filter field (up to 10 filter fields per index).
2. In Einstein Studio > Retrievers > New Retriever, select the data space, the DMO, and the index.
3. Filter Documents to Return: one condition, `Product_Line__c` Equals `CRM`, with All Conditions Are Met.
4. Return: maximum 5 results; output fields Chunk (label "Passage") and Title (label "Source title").
5. Save as `ProductDoc_CRM` and activate it (only one version of a retriever can be active). Repeat for ERP and HR.
6. Use the CRM retriever in the CRM support template, and so on.

**Why it works:** Filters run only on fields the index defines as filter fields, so the field must be designed in at index creation. UNVERIFIED (2026-10-03): feeding a runtime value from the conversation into a retriever filter was not found in a fetched source, which is why this example uses one retriever per product.

---

## Example 3: Prompt Template With a Retriever Resource

**Context:** A financial services firm wants case summaries that cite internal policy passages.

**Solution:** Create a Flex template with a `Case` input, then:

1. Write the context block with record merge fields: `{!$Input:Case.CaseNumber}`, `{!$Input:Case.Subject}`, `{!$Input:Case.Description}`.
2. Resource > Einstein Search > the policy DMO > the `Policy_Passages` retriever.
3. In the Configuration panel, Search Text: `case subject: Input.Case.Subject` (search text is limited to 255 characters, globals, and prompt inputs). Output Fields: Chunk. Number of Results: 5.
4. After the context and the retrieved passages, add the instructions block:

```text
Instructions:
"""
Summarize the case in three sentences. Then list which policy passages above apply,
quoting the passage title. If no passage applies, say "No matching policy."
Use only the passages provided; do not add policy details that are not in them.
"""
```

5. Preview with a real case and read the retriever output in the resolution (shown as JSON).

**Why it works:** The guide recommends separating context from instructions with an `Instructions:` line and triple quotes, and the retriever's number of results bounds how much of the prompt the passages take.

---

## Anti-Pattern: Stripping HTML From Knowledge Before Indexing

**What practitioners do:** Run a transform that removes every HTML tag from the article body so "embeddings are not polluted by markup."

**What goes wrong:** Semantic-based passage extraction uses headings, lists, and bold subheadings as passage boundaries. Without them, Data Cloud falls back to block or sentence aggregation, and "there is no guarantee that passages are meaningfully grouped."

**Correct approach:** Keep well-formed HTML, fix articles that fake headings with line breaks, and prepend the Title field so every chunk names its source.
