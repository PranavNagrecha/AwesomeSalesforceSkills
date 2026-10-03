# Well-Architected Mapping — AI-Ready Data Architecture

This skill maps to the Salesforce Well-Architected Framework (WAF) pillars as follows.

---

## Scalability

AI workloads amplify data volume requirements. Embedding pipelines, identity resolution, and calculated insights in Data Cloud are computationally expensive at scale. Well-Architected scalability guidance requires that architecture decisions account for future growth, not just current state.

**Skill application:**
- Data placement decisions (Salesforce objects vs Data Cloud vs external store) are made with volume tolerance in mind. High-velocity event data (clicks, emails, IoT) is routed to Data Cloud or external pipelines from the outset, not retrofitted when Salesforce storage limits become a constraint.
- Text fields destined for embedding are sized to avoid chunking complexity where possible (≤2,000 characters per logical unit), reducing compute load on the embedding pipeline.
- Calculated insights are pre-computed at the data layer rather than calculated at query time, following the WAF principle of pushing complexity down to the infrastructure layer where it scales more efficiently.
- Einstein Feature Store fields are treated as read-heavy, write-rare artifacts — consistent with WAF guidance on designing for the dominant access pattern.

**Official sources:** Salesforce Well-Architected — Reliable/Data guidance emphasizes designing data architecture for the full lifecycle of expected growth, not just initial deployment volume.

---

## Reliability

AI features degrade unreliably when data quality is inconsistent. A system that produces confident-looking scores on bad data is more dangerous than one that fails visibly. WAF reliability guidance requires that systems behave predictably and that degradation is observable.

**Skill application:**
- Data quality gates (fill rate checks, picklist consistency, volume thresholds) are mandatory before AI feature activation. These gates surface unreliability before it reaches users rather than after.
- Sync cadence requirements are defined per AI feature with explicit staleness tolerances, following WAF reliability guidance on SLA definition.
- Einstein score fields are explicitly excluded from synchronous decision logic, eliminating a class of race conditions where unreliable asynchronous state is read at the wrong time.
- Data Cloud activation is validated against a test segment before production rollout, following WAF guidance on change validation before broad deployment.
- Knowledge article sync lag is treated as an operational reliability concern with a defined runbook, not an undocumented behavior.

**Official sources:** Salesforce Well-Architected — Reliable/Data (https://architect.salesforce.com/well-architected/reliable/data).

---

## Operational Excellence

AI-ready data architectures require ongoing operational discipline. The data model is not "done" at go-live — model retraining, data drift, and changing business processes continuously affect AI feature quality. WAF operational excellence guidance requires that systems are observable, maintainable, and supported by documented operational processes.

**Skill application:**
- Monthly data quality monitoring reports are recommended for all Einstein predictor fields, making data quality observable as an ongoing operational metric rather than a one-time pre-launch check.
- Sync cadences are documented in the operational runbook with ownership assigned to a named team (typically Data/CRM Ops).
- Field naming conventions and semantic documentation reduce the operational burden of re-mapping fields on Data Cloud ingestion runs.
- Knowledge article metadata taxonomy reduces the operational cost of keeping the RAG knowledge base relevant as the article corpus grows.
- AI feature store field usage is documented so that future admins do not inadvertently repurpose system-managed fields.

**Official sources:** Salesforce Well-Architected Overview (https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html).

---

## Official Sources Used

The following official Salesforce sources were used to inform this skill:

- **Salesforce Well-Architected — Reliable / Data**
  https://architect.salesforce.com/well-architected/reliable/data (returned 404 Not Found on 2026-10-03; dead link kept for history, not used as grounding)
  Primary authority for data reliability patterns and data lifecycle design guidance.

- **Salesforce Well-Architected Overview**
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (on 2026-10-03 this URL redirected to the architect.salesforce.com home page, so the guide was not re-read; pillar framing follows `standards/well-architected-mapping.md`)
  Primary authority for the Trusted / Easy / Adaptable pillar model and operational excellence guidance.

- **Data Cloud Overview (Salesforce Help)**
  https://help.salesforce.com/s/articleView?id=sf.data_cloud_overview.htm (help.salesforce.com does not fetch; the *Data Cloud* PDF below was read instead)
  Primary authority for Data Cloud capabilities, harmonized data model, identity resolution, and activation behavior.

- **Salesforce Architects Blog**
  https://architect.salesforce.com/content (returned 404 Not Found on 2026-10-03; dead link kept for history, not used as grounding)
  Pattern guidance for data architecture decisions in large-scale Salesforce implementations.

- **Einstein AI Documentation (Salesforce Help)**
  https://help.salesforce.com/s/articleView?id=sf.einstein_sales_scoring.htm (help.salesforce.com does not fetch; training-volume figures resting on it are marked UNVERIFIED)
  Authority for Einstein Opportunity Scoring behavior, training requirements, and model confidence levels.

- **Salesforce Industries Developer Guide — Scoring Framework**
  Local knowledge import: `knowledge/imports/salesforce-industries-dev-guide.md`
  Authority for `AIFeatureExtractor` and `AIScoringModelDefinition`. Note (2026-10-03): the import documents `AIFeatureExtractor` under AI Accelerator; "Einstein Feature Store" as a named type was not found in it.

- **Quickstart Your Einstein Generative AI Solution (Spring '26 edition, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
  "Grounding, Chunking, and Indexing", "Setting Up Data Libraries" (Data Cloud required; Knowledge or files, not both; identifying and content fields; public-article and data-category filters), "Agent Topic: General FAQ" considerations (supported field types, file types and sizes, daily reindex, respects permissions and sharing).

- **Data Cloud (Summer '26, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/data_cloud.pdf
  Glossary (category fixed after ingestion, chunking, chunk DMO, contact point, Customer 360 Data Model, search index configuration, UDLO, SQL for insights) and "Use ANSI SQL Statements in Data Cloud".

- **Object Reference (Summer '26, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  `AIRecordInsight` and child insight objects, `SalesAIScoreCycle`, `SalesAIScoreModelFactor` (licence and permission rules).

- **Metadata API Developer Guide (Summer '26, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  `AIUsecaseDefinition` and `AIFeatureExtractor` (AI Accelerator, CRM Plus licence, batch input from CRM Analytics or Data Cloud).

- **SOQL and SOSL Reference (Summer '26, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf
  Aggregate functions: `COUNT(fieldName)` ignores nulls; `COUNT()` and `COUNT(Id)` do not.

- **Apex Reference Guide (Summer '26, PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf
  `String.stripHtmlTags()`: removes HTML markup and returns plain text.

- **Salesforce Knowledge Guide (Classic), Spring '26 (PDF)**
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_knowledge_implementation_guide.pdf
  Article field types: Text Area (Long) and Text Area (Rich) up to 131,072 characters.

