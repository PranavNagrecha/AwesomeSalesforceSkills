---
name: ai-ready-data-architecture
description: "Use when designing or auditing a Salesforce data architecture to support AI features — Einstein, Agentforce, Data Cloud, or custom ML models. Covers field-level data quality requirements, structured vs unstructured data placement, embedding-ready text field design, knowledge article structure for RAG grounding, Data Cloud harmonized data model, Einstein Feature Store patterns, grounding data for Agentforce actions, AI-ready field naming conventions, and data freshness requirements for model retraining. Trigger phrases: design data model for AI, make Salesforce data AI-ready, data quality for Einstein, grounding data for Agentforce, Data Cloud for AI, RAG data architecture Salesforce. NOT for Data Cloud initial setup and licensing, not for LWC or Flow implementation, not for general data migration, not for Einstein Analytics dashboard design."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
tags:
  - ai
  - data-cloud
  - agentforce
  - einstein
  - machine-learning
  - rag
  - data-architecture
  - data-quality
  - vector-search
  - feature-store
triggers:
  - "design our data model to support AI features"
  - "how do we make our Salesforce data AI-ready"
  - "data quality requirements for Einstein scoring"
  - "grounding data architecture for Agentforce"
  - "Data Cloud as AI data layer"
  - "knowledge article structure for RAG retrieval"
  - "field design for vector search in Salesforce"
  - "data freshness requirements for model retraining"
  - "Einstein Feature Store design patterns"
  - "AI-ready field naming and data completeness"
inputs:
  - Salesforce clouds and editions licensed (Sales Cloud, Service Cloud, Data Cloud, Agentforce)
  - Current data model overview (key objects and relationships)
  - AI or ML features being enabled (Einstein Scoring, Agentforce, custom ML, RAG)
  - Known data quality concerns (null rates, inconsistent picklist values, free-text sprawl)
  - Data volume per key object (record counts and growth rate)
  - Sync cadence and freshness requirements for AI features
outputs:
  - AI-readiness assessment per key object (field fill rates, completeness gaps)
  - Field design recommendations (text field length, naming conventions, structured vs free-text)
  - Data placement decision (Salesforce object vs Data Cloud vs external store)
  - Knowledge article template for RAG-friendly chunking
  - Data freshness and sync cadence recommendation per AI feature
  - Data quality gate checklist before AI feature activation
  - Einstein Feature Store field mapping recommendations
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when designing or auditing a Salesforce data architecture to ensure it can reliably support AI features — including Einstein predictive scoring, Agentforce generative actions, Data Cloud-powered insights, and custom ML integrations. This is not a skill about enabling individual Einstein features; it is about making the underlying data model, field design, and data quality posture capable of feeding AI reliably. The difference between an org where Einstein Opportunity Scoring works and one where it produces junk predictions is almost always data architecture, not configuration.

---

## Why AI-Readiness Is an Architecture Problem

AI features consume data. The quality of their output is directly bounded by the quality of their input. Salesforce AI features fail silently when:

- Key predictive fields have fill rates below 70% — Einstein models depersonalize predictions and revert to global averages.
- Text fields used for RAG retrieval are written in inconsistent formats, contain HTML markup, or are truncated — the retrieval model cannot chunk or embed them reliably.
- Data freshness is misaligned — a model trained on 90-day-old data scores against live pipeline records and produces stale recommendations.
- Fields are named inconsistently across objects — Data Cloud's harmonized data model cannot map them without manual field mapping on every ingestion run.
- Knowledge articles are structured for human readability rather than machine chunking — large monolithic articles with embedded tables and images do not retrieve well.

This skill addresses all five failure modes before they reach production.

---

## Key Design Areas

### 1. Data Completeness for ML

Einstein predictive models require sufficient field fill rates to produce meaningful predictions. The minimum threshold for a field to influence a model is approximately 70% fill rate across training records. Fields below 40% fill rate are typically ignored by the model during feature selection, which means sparse data silently degrades prediction quality.

**Assessment approach:** For each object targeted by an Einstein feature, calculate fill rates for all candidate predictor fields. Use a SOQL aggregate query or CRM Analytics recipe. Flag fields below 70% for remediation before enabling scoring.

**Null handling strategies:**
- Structured defaults: Use Flows or validation rules to enforce minimum values on fields that are operationally required (e.g., Industry, AnnualRevenue on Account).
- Picklist curation: Replace open-ended text fields with picklists wherever values are enumerable. Picklist fields are categorical features that Einstein handles natively; free text requires NLP processing and adds noise.
- Graceful nulls vs meaningful blanks: Not all nulls are equal. A null LeadSource may mean "not captured" (data quality problem) or "organic" (valid state). Document which nulls are meaningful and which are gaps before applying defaults.

### 2. Structured vs Unstructured Data Placement

Not all data belongs in Salesforce standard objects. AI features have different optimal data sources:

| Data type | Optimal location | Reason |
|---|---|---|
| Structured CRM records (Accounts, Opportunities, Cases) | Salesforce standard/custom objects | Native Einstein feature extraction; Data Cloud harmonization |
| High-volume interaction data (emails, web events, clicks) | Data Cloud | Volume tolerance, calculated insights, identity resolution |
| Long-form knowledge content (articles, runbooks, policies) | Salesforce Knowledge or external CMS | RAG retrieval via Data Cloud knowledge base |
| Binary files, images, audio | External store (S3, Azure Blob) with URL reference in Salesforce | Salesforce storage limits; vector embedding happens externally |
| Real-time sensor or IoT data | MuleSoft or streaming pipeline to Data Cloud | Event volume exceeds platform API limits |

### 3. Embedding-Ready Text Field Design

Text fields that will be embedded for vector search require deliberate design. Key rules:

- **Minimum length for meaningful embedding:** 50 characters. Fields shorter than this rarely produce discriminating embeddings.
- **Maximum practical length:** 2,000 characters per chunk. Fields beyond 4,000 characters should be chunked before embedding. Salesforce Long Text Area fields support up to 131,072 characters — these must be chunked server-side before passing to an embedding model.
- **Format discipline:** Strip HTML before storing. Rich Text fields in Salesforce Knowledge store HTML markup by default. The embedding model treats `<p>`, `<strong>`, and `&amp;` as tokens, which pollutes the vector space.
- **Language consistency:** Mixed-language fields produce low-quality embeddings. If the org supports multiple languages, store language as a metadata field and route to language-specific embedding models.
- **Semantic density:** Fields that mix unrelated topics (e.g., a Description field that contains installation instructions, billing notes, and escalation history concatenated) produce generic embeddings. Split concerns into separate fields.

### 4. Knowledge Article Structure for RAG

Agentforce grounds responses using Data Cloud knowledge base retrieval. The quality of retrieval is determined by how articles are structured.

**Chunking-friendly article structure:**
- One topic per article. Do not combine related but distinct concepts in a single article.
- Lead with a declarative summary sentence (the first 150 characters are the most heavily weighted by most retrieval systems).
- Use H2/H3 headers to create natural chunk boundaries — retrieval systems often split on heading boundaries.
- Avoid tables for information that could be prose — tables do not chunk cleanly and lose context when split across chunks.
- Tag articles with structured metadata: product, version, audience, topic category. Metadata filters in retrieval reduce false positives.
- Maximum recommended article length before mandatory chunking: 1,500 words.

### 5. Data Freshness Requirements

AI models decay. The sync cadence for AI-relevant data should be designed based on the velocity of the underlying business data:

| AI feature | Recommended sync cadence | Staleness tolerance |
|---|---|---|
| Einstein Opportunity Scoring | Daily batch | 24 hours |
| Einstein Case Classification | Near-real-time (CDC-triggered) | 1 hour |
| Agentforce RAG grounding | Near-real-time knowledge sync | 4 hours |
| Data Cloud calculated insights | Hourly for high-velocity streams | 1 hour |
| Custom ML model retraining | Weekly or on significant data drift | Org-specific |

### 6. Einstein Feature Store

Einstein's Feature Store is the mechanism by which Salesforce stores computed ML features alongside CRM records. Key design decisions:

- Feature values are stored as custom fields on the scored object (e.g., `EinsteinScoreReason1__c` on Opportunity). These fields are system-managed when Einstein scoring is enabled — do not repurpose them.
- Custom feature extractors defined via `AIFeatureExtractor` metadata allow Salesforce Industries Einstein to use domain-specific signals. Define extractors in a dedicated metadata set and version-control them.
- Avoid writing business logic that reads Einstein score fields at runtime — scores update asynchronously. Read them in reporting and recommendations, not in trigger-based decision gates.

### 7. Data Cloud as AI Data Layer

Data Cloud provides the harmonized data layer that connects disparate Salesforce and external data sources for AI consumption:

- **Harmonized data model:** Data Cloud maps ingested data to a canonical data model (individual, contact point, engagement, etc.). Field mapping quality directly affects identity resolution and calculated insight accuracy. Invest in mapping before ingestion, not after.
- **Calculated insights:** Define calculated insights (SOQL-like expressions on Data Cloud data) to pre-compute features at the data layer rather than in real-time Apex. Pre-computed features are faster and more reliable than runtime calculation.
- **Activation targets:** Data Cloud can activate segments and calculated insights back to Salesforce CRM objects. Design the activation schema to match the target object's field structure — mismatched types cause silent activation failures.

### 8. AI-Ready Field Naming

Consistent field naming enables automated field mapping in Data Cloud and reduces manual mapping effort on every ingestion run:

- Use consistent prefixes for AI-relevant fields: `AI_`, `ML_`, `Score_`, `Feature_`.
- Avoid spaces and special characters in API names — underscores only.
- Document the semantic meaning of each field in the field description — Data Cloud's schema mapping UI uses descriptions as hints during automated mapping.
- Mirror field names across related objects where semantically equivalent (e.g., `Industry__c` on Lead and Account should map to the same canonical field in Data Cloud).

### 9. Data Quality Gates Before AI Activation

Before activating any Einstein or Agentforce feature, verify:

1. **Completeness:** Fill rate ≥ 70% on all planned predictor fields.
2. **Consistency:** Picklist values are clean (no duplicates from legacy migration, no "Other" comprising >20% of values).
3. **Timeliness:** Sync jobs are confirmed running and within target cadence.
4. **Volume:** Sufficient historical records exist for model training (Einstein requires at least 1,000 closed records for Opportunity Scoring; Case Classification requires 1,000 closed cases with populated target fields).
5. **No circular dependencies:** AI scoring fields are not used as inputs to the same model that produces them.

---

## Recommended Workflow

1. **Identify AI features and their data dependencies.** For each Einstein, Agentforce, or custom ML feature in scope, list the source objects, predictor fields, and target fields. Build a dependency map: Feature → Object → Fields → Fill Rate.

2. **Run a data completeness audit.** For each object and field in scope, calculate fill rates using SOQL aggregate queries or a CRM Analytics recipe. Flag fields below 70%. This is the single highest-value diagnostic step.

3. **Classify data placement.** For each data category (structured CRM records, high-volume events, knowledge content, binary files), apply the placement decision matrix to determine whether data belongs in Salesforce objects, Data Cloud, or an external store.

4. **Remediate field design.** Address identified gaps: enforce defaults via Flow or validation rules, curate picklist values, strip HTML from text fields destined for embedding, split monolithic text fields where semantic mixing is detected.

5. **Design knowledge article structure.** If Agentforce RAG grounding is in scope, audit existing Knowledge articles against the chunking-friendly structure guidelines. Create or update the Knowledge article template. Apply metadata tagging taxonomy.

6. **Define and validate sync cadence.** For each AI feature, specify the required data freshness SLA and confirm the sync mechanism (CDC, scheduled batch, MuleSoft, Data Cloud connector) can meet it. Test with a representative data volume before go-live.

7. **Run data quality gate checklist.** Complete the pre-activation checklist (completeness, consistency, timeliness, volume, no circular dependencies). Document results. Obtain sign-off before enabling AI features in production.
