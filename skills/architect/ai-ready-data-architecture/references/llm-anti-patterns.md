# LLM Anti-Patterns — AI-Ready Data Architecture

Common mistakes AI coding assistants make when generating or advising on Salesforce AI-ready data architecture. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending Einstein Be Enabled Without Assessing Fill Rates First

**What goes wrong:** The assistant recommends enabling Einstein Opportunity Scoring or Case Classification as a step in a broader implementation plan without first auditing whether the predictor fields have sufficient fill rates. The recommendation treats feature enablement as a configuration task rather than a data quality dependency.

**Why it matters:** Einstein models require approximately 70% fill rate on key predictor fields to produce meaningful, personalized scores. Enabling Einstein with sparse data produces low-confidence models that behave as global averages — giving all opportunities similar scores and eroding rep trust in the feature. Rebuilding trust after a poor initial rollout is significantly more expensive than the pre-launch audit.

**Correct approach:** Always include a data completeness audit step before recommending Einstein feature activation. The audit should cover fill rates per field on the target object. Only recommend activation when fill rates meet the threshold for the fields known to be predictive for the business context.

---

## Anti-Pattern 2: Passing Raw Salesforce Rich Text / HTML to an Embedding Pipeline

**What goes wrong:** The assistant generates or describes a vector embedding pipeline that reads Knowledge article Body fields directly and passes their values to an embedding API without an HTML stripping step. The code looks correct (reads the field, calls the API, stores the vector) but produces poor-quality embeddings.

**Why it matters:** Salesforce Knowledge Body fields are Rich Text Areas that store HTML markup. Embedding HTML-tagged content pollutes the semantic vector space with structural tokens (`<p>`, `<li>`, `&amp;`, `&#160;`). Articles cluster by formatting style rather than semantic content, and cosine similarity searches return false matches.

**Correct approach:** Always include an HTML stripping transformation before embedding. In Apex, use `String.stripHtmlTags()`. In Python-based pipelines, use BeautifulSoup or the `html.parser` stdlib module. The stripped plain text should also be deduplicated for whitespace and normalized to UTF-8 before passing to the embedding model.

---

## Anti-Pattern 3: Treating Einstein Score Fields as Synchronous in Trigger or Flow Logic

**What goes wrong:** The assistant writes trigger-based Apex or a before-save Flow that reads `EinsteinScore__c` or similar Einstein-managed fields to make routing or assignment decisions at save time. The logic looks correct in unit tests (where the field can be set in test data) but fails in production.

**Why it matters:** Einstein score fields are updated asynchronously by the Einstein scoring service. At the moment a record is saved or created, the score field will be null (for new records) or stale (for re-scored records). Synchronous logic that branches on a null score will take the default branch for all records before their first score is written, producing incorrect routing for a significant percentage of early-pipeline records.

**Correct approach:** Einstein score fields must only be consumed in asynchronous contexts: scheduled jobs, Flow scheduled paths, reports, dashboard components, and Agentforce prompt context. If a business process requires score-driven routing, implement it as a nightly or near-real-time scheduled batch that runs after the Einstein scoring cycle completes.

---

## Anti-Pattern 4: Designing Knowledge Articles for Human Readability Without Considering RAG Chunking

**What goes wrong:** The assistant advises structuring Knowledge articles for comprehensiveness and human readability — long, thorough, cross-referential articles that cover multiple related topics in a single document. This is good practice for human documentation but directly conflicts with the requirements of RAG retrieval systems.

**Why it matters:** RAG retrieval splits long documents into chunks (typically 300–600 tokens each). When a chunk is split mid-topic, it loses the surrounding context that gives it meaning. A 4,000-word article covering account types, fees, eligibility, and tax treatment will produce chunks that each contain fragments of multiple topics. Retrieval returns these fragments as grounding context, and the generative model produces answers that mix concepts from different parts of the article — a primary cause of Agentforce answer hallucination.

**Correct approach:** Design Knowledge articles for chunking first, human readability second. One article per discrete topic. Maximum 600–800 words. Lead with a declarative summary. Use H2/H3 headers to create natural split points. Represent tabular data as prose. Apply metadata tags for retrieval pre-filtering.

---

## Anti-Pattern 5: Assuming Data Cloud Identity Resolution Automatically Unifies All Sources

**What goes wrong:** The assistant describes a Data Cloud implementation where multiple data sources are connected (CRM, commerce, marketing, support) and assumes that Data Cloud will automatically unify customer records across all sources once connected. The implementation plan skips the identity resolution configuration step.

**Why it matters:** Data Cloud's identity resolution requires an explicit configuration of which fields represent the same real-world entity across sources. If one source uses Salesforce `ContactId` and another uses email address as the customer identifier, Data Cloud treats these as separate individuals unless email is explicitly added as an identity attribute in the resolution ruleset. The resulting unified profile is incomplete, and AI recommendations built on it are based on a partial view of the customer.

**Correct approach:** Before connecting any new data stream, explicitly define the identity resolution strategy: list all candidate identity attributes across all sources (CRM ID, email, phone, loyalty ID, cookie ID, etc.) and configure the Data Cloud identity resolution ruleset to match on all of them. Test unification on a known sample set before activating the stream.

---

## Anti-Pattern 6: Recommending Custom Fields for Data Cloud Activation Without Validating Type Compatibility

**What goes wrong:** The assistant recommends activating a Data Cloud calculated insight or segment attribute back to a Salesforce CRM object by mapping the Data Cloud attribute to a custom field, without checking that the Salesforce custom field type is compatible with the Data Cloud attribute type.

**Why it matters:** Data Cloud activation silently fails at the record level when field types are incompatible. A Number attribute mapped to a Text field in CRM will write as a string, breaking numeric SOQL comparisons and aggregations. A Date/Time attribute mapped to a Date field loses time-of-day precision. These failures do not generate a bulk error in the activation log — they appear as individual record-level silent failures, making them hard to detect without targeted validation queries.

**Correct approach:** Before creating activation configuration, cross-reference the Data Cloud attribute type against the target CRM field type. Run a dry-activation on a 100-record test segment and validate the activated values using SOQL before enabling production activation.

---

## Anti-Pattern 7: Ignoring Data Freshness Requirements When Designing AI Sync Cadences

**What goes wrong:** The assistant designs a Data Cloud or Einstein sync architecture with a single daily batch cadence for all data streams, treating data freshness as a uniform concern. This works for some features but silently degrades others that require near-real-time data.

**Why it matters:** Different AI features have different staleness tolerances. Agentforce RAG grounding on Knowledge articles can tolerate a 4-hour lag for most content but must be near-real-time for policy-sensitive articles. Einstein Case Classification using case metadata fields should be near-real-time to correctly route inbound cases. A 24-hour batch cadence for case data means new case categories added in the morning are not available for classification until the next day.

**Correct approach:** Define sync cadences per AI feature based on the velocity of the underlying data and the business impact of staleness. Document the cadence requirements in the operational runbook. Configure separate data stream schedules for high-velocity and low-velocity sources rather than applying a single cadence uniformly.
