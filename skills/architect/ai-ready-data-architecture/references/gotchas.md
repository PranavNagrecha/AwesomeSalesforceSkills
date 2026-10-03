# Gotchas — AI-Ready Data Architecture

Non-obvious pitfalls when designing Salesforce data architectures for AI features.
Each gotcha names its source. "Generative AI guide" means *Quickstart Your Einstein Generative AI Solution* (`generative_ai.pdf`, Spring '26 edition under the 262 path). Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

---

## Gotcha 1: Einstein Scoring Silently Degrades Without Warning When Fill Rates Drop

**What happens:** Einstein predictive scoring models are retrained periodically, but there is no native alerting when model confidence degrades due to declining data quality. If a picklist field that was a strong predictor in the original model begins receiving inconsistent values after a process change (e.g., a new picklist value is added that absorbs traffic from two previously meaningful values), the model silently re-weights that field downward on the next training cycle. Scores may still be generated and displayed — they just become less accurate. UNVERIFIED (2026-10-03): the retraining and re-weighting behavior is described only in Salesforce Help. What the Object Reference does document is where to look: Opportunity Scoring model factors are exposed in `SalesAIScoreModelFactor` and score cycles in `SalesAIScoreCycle`, readable with a Sales Cloud Einstein license and the View Scoring Model Factors permission (not enabled by default).

**When it occurs:** After a process change adds or merges picklist values on a predictor field.

**How to avoid:** Build a monthly data quality monitoring report that tracks fill rates and picklist distribution for all fields known to be predictive inputs. Flag any field where value distribution shifts by more than 10 percentage points month-over-month. Treat Einstein score confidence ratings in the setup UI as a lagging indicator, not a proactive signal.

---

## Gotcha 2: Data Cloud Activation Mismatches Fail Silently

**What happens:** When Data Cloud activates a segment or calculated insight back to Salesforce CRM objects, field type mismatches between the Data Cloud attribute and the CRM target field cause individual record updates to fail without surfacing a bulk error. A Number field in Data Cloud mapped to a Text field in Salesforce CRM will often write successfully but strip precision (e.g., `1250.75` becomes `"1250.75"`, breaking downstream numeric SOQL comparisons). A Date/Time in UTC mapped to a Date-only field loses time-of-day information. UNVERIFIED (2026-10-03): the per-record failure and coercion behavior is field experience; the fetched *Data Cloud* guide was not checked for activation error handling.

**When it occurs:** First activations to CRM objects whose fields were created before the Data Cloud attribute types were known.

**How to avoid:** Before production activation, run a dry-activation on a 100-record test segment. Validate the activated field values in the target CRM object using SOQL. Confirm data types match — not just that activation completes without an error in the Data Cloud activation log.

---

## Gotcha 3: Rich Text Fields in Salesforce Knowledge Store HTML

**What happens:** Salesforce Knowledge's Body field is a Rich Text Area. When content is authored in the Knowledge editor, the platform stores HTML markup (`<p>`, `<ul>`, `<li>`, `<strong>`, `&amp;`, `&#160;` for non-breaking spaces, etc.) inside the field value. If this raw HTML is passed to an embedding model, the model treats markup tokens as part of the semantic content. The resulting embeddings cluster articles by their HTML structure rather than their semantic content — articles that both happen to use heavily nested lists will be more similar to each other than articles on the same topic but formatted differently. UNVERIFIED (2026-10-03): this applies to custom embedding pipelines. For the native path, the Generative AI guide ("Agent Topic: General FAQ" considerations for the Answer Questions with Knowledge action) lists Text Area (Rich) as a supported knowledge field type, so do not strip rich text before a Data Library indexes it without testing retrieval quality both ways. The Knowledge Guide (Classic) caps Text Area (Rich) and Text Area (Long) at 131,072 characters.

**When it occurs:** Custom RAG pipelines that send Knowledge field values to an external embedding model.

**How to avoid:** For custom pipelines, strip HTML before embedding. A server-side transformation step must parse the Rich Text field, extract plain text, and normalize whitespace before passing content to the embedding pipeline. BeautifulSoup (Python) or the Apex `String.stripHtmlTags()` method (Apex Reference Guide: "Removes HTML markup and returns plain text") can handle this. Build the stripping step into the Data Cloud ingestion transform, not as a post-hoc fix.

---

## Gotcha 4: Einstein Prediction Outputs Are Not Safe Inputs for Real-Time Decision Logic

**What happens:** Einstein scoring fields on CRM records (e.g., `EinsteinScore__c`, `EinsteinScoreReason1__c`, `EinsteinScoreReason2__c`) are updated asynchronously by the Einstein scoring service. UNVERIFIED (2026-10-03): those field names, and "Einstein Feature Store" as a product name, appear in no fetched guide. The Object Reference documents Einstein predictions as an `AIRecordInsight` record (with child `AIInsightAction`, `AIInsightFeedback`, `AIInsightReason`, `AIInsightValue`) created every time a feature such as Prediction Builder makes a prediction, naming the AI prediction field where results were written. The update can lag the triggering event by minutes to hours depending on org load. Trigger-based Apex or synchronous Flow that reads these fields immediately after a record save will frequently read stale values — including null before the first score is ever written.

An anti-pattern seen in the field: a before-save Flow that gates record routing logic on the Einstein score value. If the score is null (because it has not yet been written), the Flow branches to a default path that is incorrect for scored records. This creates a race condition where early-pipeline records are routed differently from re-scored records.

**When it occurs:** Before-save flows and triggers that branch on a score.

**How to avoid:** Einstein score fields should be consumed in asynchronous contexts only: reports, list views, dashboard components, scheduled jobs, and Agentforce prompt context. Never use them in synchronous record-save logic. If routing logic requires a score-influenced decision, use a scheduled Apex job or Flow scheduled path that runs after the scoring cycle completes.

---

## Gotcha 5: Data Cloud Harmonized Data Model Requires Consistent `primaryKey` Mapping Across All Ingested Data Streams

**What happens:** Data Cloud's identity resolution depends on a consistent `primaryKey` value being passed in every data stream for the same individual or account. If one data stream passes Salesforce `ContactId` as the primary key and another passes email address, Data Cloud will not automatically unify those records unless email address is also configured as an identity attribute for the `ContactId`-keyed stream — or vice versa.

UNVERIFIED (2026-10-03): the unification behavior described here was not checked against the *Data Cloud* guide's identity resolution chapters in this pass; its glossary defines a ruleset as the match and reconciliation rules that combine source records into unified profiles.

**When it occurs:** This is a frequent mistake during Data Cloud onboarding: the CRM connector correctly passes Salesforce IDs, while a custom-built commerce data stream passes customer email as the key. The result is two unresolved identity graphs — Einstein recommendations built on the unified profile see only half the customer's history.

**How to avoid:** Before connecting any new data stream, define the identity resolution strategy explicitly: which fields represent the same real-world person or account across all data sources. Add all candidate identity attributes (email, phone, CRM ID, loyalty ID) to the identity resolution ruleset. Test unification with a known set of records that have overlapping identities before activating the stream in production.

---

## Gotcha 6: Knowledge Article Reindexing Is Daily, So Agentforce Can Ground on Yesterday's Policy

**What happens:** Agentforce grounding via Data Cloud does not update instantaneously when a Knowledge article is updated in Salesforce CRM. The Generative AI guide (Answer Questions with Knowledge considerations) says using Knowledge with Agentforce triggers an initial indexing of knowledge articles and that articles are then reindexed daily. Correction (2026-10-03): earlier text gave a 4–24 hour lag that depended on a configurable connector schedule; the guide states a daily reindex and documents no faster schedule. During this window, Agentforce may ground responses on the previous version of the article.

**When it occurs:** Policy, pricing, or legal articles changed during the business day.

For policy-sensitive content (pricing, legal terms, compliance procedures), this lag is operationally significant. A price change published in Knowledge at 9 AM may not be available to the Agentforce knowledge base until the next evening sync.

**How to avoid:** For policy-critical articles, do not rely on grounding alone. UNVERIFIED (2026-10-03): earlier advice to set the Knowledge connector to hourly and to trigger a manual sync could not be confirmed. Put deterministic policy values (prices, limits) behind an action that reads the record live, and keep the article for explanation. Establish a process where Knowledge article authors flag policy-critical updates so support teams know the grounding lag. Document the lag SLA for AI grounding in the operational runbook so stakeholders have calibrated expectations.

---

## Gotcha 7: Some Knowledge Field Types and File Types Are Not Used for Grounding

**What happens:** An article's key content lives in an encrypted text field or a URL field, and the agent never uses it. The Generative AI guide says the Answer Questions with Knowledge action can use custom knowledge fields of type Text, Text Area, Text Area (Long) and Text Area (Rich); Text (Encrypted) and URL fields are not supported. For file uploads it supports text, HTML, and PDF files, up to 4 MB for text or HTML and 100 MB for PDF.

**When it occurs:** Orgs that moved sensitive article content into encrypted fields, or that link out to documents instead of storing the text.

**How to avoid:** Keep groundable content in supported field types. Decide per field whether it should be grounding content or protected content, because it cannot be both. Convert linked documents to PDF or text within the size limits before loading them into a data library.

---

## Gotcha 8: A Data Library Takes Knowledge or Files, Not Both

**What happens:** The design assumes one library for articles and uploaded policy PDFs. The Generative AI guide ("Setting Up Data Libraries") says a data library supports either Knowledge or file uploads as its data source, not both; it requires Data Cloud, creates the search index and retriever automatically, and lets you choose identifying fields, content fields, public-only articles, and data category filters. The action respects permissions and sharing, answering only from articles the agent can access.

**When it occurs:** Grounding designs that mix sources or forget that the agent user's access limits what can be retrieved.

**How to avoid:** Plan one library per source type and assign them deliberately. Choose concise identifying fields (summary, question) and detailed content fields (steps, product details), as the guide recommends. Check that the agent user can see the articles you expect it to cite.

---

## Gotcha 9: Data Cloud Stream Categories Cannot Be Changed After Ingestion

**What happens:** A web-events stream is ingested as Profile data and later needs to be Engagement data for time-based insights. The *Data Cloud* guide glossary says the data category (Profile, Engagement, or Other) is selected when importing data and cannot be edited after ingestion.

**When it occurs:** Pilots that ingest first and model later.

**How to avoid:** Decide the category for each stream in the data architecture document before the first ingestion, using the guide's definitions: Profile for consumer, business, account, or employee data; Engagement for time-based data; Other for everything else, such as products.

---

## Gotcha 10: Calculated Insights Are ANSI SQL, Not SOQL

**What happens:** A team writes calculated insights the way they write SOQL and hits unsupported syntax. The *Data Cloud* guide ("Use ANSI SQL Statements in Data Cloud") says calculated insights take an eligible ANSI SQL statement, with only certain aggregates and functions supported. Correction (2026-10-03): the SKILL.md earlier described calculated insights as "SOQL-like expressions".

**When it occurs:** CRM developers moving into Data Cloud feature engineering.

**How to avoid:** Write and review calculated insights as ANSI SQL against data model objects, and check each function against the guide's supported list before relying on it.

---

## Gotcha 11: AI Accelerator Use Case Metadata Needs Specific Licences

**What happens:** An architecture names `AIFeatureExtractor` for custom feature engineering, and the org cannot deploy it. The Metadata API Developer Guide (`AIUsecaseDefinition`) says the type is available when the admin settings for AI Accelerator and for the related product are enabled, and the org must have the CRM Plus licence and the product's CRM licence. `AIFeatureExtractor` is part of that type and takes its batch features from CRM Analytics or Data Cloud (`batchInputSourceType`).

**When it occurs:** Designs that treat custom Einstein feature extraction as available in every org.

**How to avoid:** Confirm the licences before designing on `AIUsecaseDefinition`. Otherwise compute features as plain fields (flows, batch jobs) or as Data Cloud calculated insights.

