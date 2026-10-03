# Well-Architected Notes: Vector Database Management

## Relevant Pillars

- **Security**: every chunked field is copied into the chunk DMO and embedded. Keep personal and regulated fields out of the chunked-field list and use filter fields for scoping attributes. UNVERIFIED (2026-10-03): whether retrievers enforce the source object's field-level security; design as if any retriever consumer can read chunked text.

- **Performance**: retrieval quality depends on chunking strategy, max tokens, embedding model, search type, and filter fields. Passage extraction suits HTML; prepend fields add context; non-Latin content needs a max-token setting below 512; hybrid search covers exact terms that vector search misses. Chunking and model cannot be changed in place, so the cost of a wrong choice is a second index.

- **Reliability**: an index is usable at status Ready and then processes source changes incrementally. Replacements run as a parallel index followed by a retriever cutover, because chunking and model are view-only and deletion is blocked while retrievers reference the index. Rebuild recovers an index that failed to process.

- **Operational Excellence**: record the configuration (data space, object, chunked fields, chunking strategy, max tokens, model, search type, filter fields), watch status, and treat the data stream's refresh mode and schedule as part of the index design. Use data kits to move configurations between orgs.

---

## Architectural Tradeoffs

**Easy Setup vs Advanced Setup**

Easy Setup creates a hybrid index with passage extraction and E5-Large V2 in a few steps. Advanced Setup adds model choice, max tokens, prepend fields, transcription settings, and up to 10 filter fields. Choose Advanced Setup when content is multilingual, when retrievers must filter, or when chunks need extra context.

**Vector vs hybrid**

Vector search matches meaning; keyword search matches exact terms such as product codes. Hybrid fuses both and can weight recency or popularity. The cost of creating the index is the same for both.

**Freshness vs processing**

Incremental or Upsert data streams deliver only changed records. Full Refresh replaces all data each cycle. Pick the most frequent schedule the use case needs, not the most frequent one available.

**Index size vs query cost**

Data Queries billing for vector search counts the vectors in the index. Narrow, purpose-built indexes cost less per query than one index over everything, within the limit of 10 indexes per Data Cloud instance.

---

## Anti-Patterns

1. **Chunking every field on a customer DMO**: personal data lands in the chunk DMO and query cost grows with vector count.
2. **Easy Setup for a corpus that needs filtering**: retrievers cannot filter on fields the index does not define.
3. **No recorded configuration**: replacing an index means guessing the original chunking, model, and fields.

---

## Official Sources Used

- Data Cloud guide, Summer '26 (262), "Use Search for AI, Automation, and Analytics": "Chunk Data," "Chunking Strategies," "How the Max Token Setting Affects Chunking," "Chunk and Index Data Model Objects," "Vector Search," "Create a Vector Search Index Configuration with Advanced Setup," "Hybrid Search," "Create a Hybrid Search Index with Advanced Setup," "Run Vector Searches Using Query API," "Run Hybrid Search Queries with Query API," "Manage Search Indexes" (Easy Setup, View, Edit, Rebuild, Delete), "Search Index Reference," "Billing Considerations for Unstructured Data and Search Index." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/data_cloud.pdf
- Data Cloud guide, Summer '26 (262), "Data Cloud Limits and Guidelines" (Unstructured Data and Search Index), "Data Stream Settings and Refresh Modes," "Retrievers" and "Create a Custom Retriever," "Add a Search Index Configuration to a Data Kit." Same PDF as above.
- Metadata API Developer Guide, Summer '26 (262): "DataPackageKitDefinition," "DataPackageKitObject," "DataStreamTemplate" (`refreshMode`, `refreshFrequency`), "DataStreamDefinition." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Generative AI guide, Summer '26 (262), searched for retriever and chunking references. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Salesforce Help, Data Cloud Vector Search Overview: https://help.salesforce.com/s/articleView?id=sf.c360_a_vector_search.htm&type=5 (help.salesforce.com does not return article text to a fetch)
- Salesforce Help, Data 360 Limits and Guidelines: https://help.salesforce.com/s/articleView?id=sf.c360_a_limits_and_guidelines.htm&type=5 (the same limits were read in the 262 Data Cloud PDF)
- Salesforce Help, Data Cloud Setup and Administration: https://help.salesforce.com/s/articleView?id=sf.c360_a_admin_setup.htm&type=5
- Salesforce Help, Agentforce Retrieval Augmented Generation: https://help.salesforce.com/s/articleView?id=sf.agentforce_rag.htm&type=5
