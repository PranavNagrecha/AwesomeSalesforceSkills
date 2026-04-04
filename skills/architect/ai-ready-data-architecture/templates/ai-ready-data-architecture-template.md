# AI-Ready Data Architecture — Assessment and Design Template

Use this template to assess an existing Salesforce data architecture for AI readiness or to design a new one. Fill in every section. Leave no placeholder text in the final deliverable.

---

## 1. Scope and AI Features

**Org name / project:**
[Enter org name or project identifier]

**Salesforce clouds licensed:**
[e.g., Sales Cloud, Service Cloud, Data Cloud, Marketing Cloud, Agentforce]

**AI features in scope:**
| Feature | Type | Target object(s) |
|---|---|---|
| [e.g., Einstein Opportunity Scoring] | [Predictive scoring / RAG / Classification / Recommendation] | [e.g., Opportunity] |
| | | |

**Out of scope:**
[Explicitly state what is NOT being assessed — e.g., Data Cloud initial setup, LWC implementation, external ML model training]

---

## 2. Data Completeness Audit

For each AI feature, list the source object and the fields that will be used as inputs (predictors or grounding sources).

### Object: [Object API Name]

| Field API Name | Field Type | Fill Rate (%) | Status | Remediation Action |
|---|---|---|---|---|
| [e.g., Industry] | [Picklist] | [e.g., 28%] | [Red / Amber / Green] | [e.g., Make required on edit via Flow] |
| | | | | |

**Fill rate thresholds:**
- Green: ≥ 70%
- Amber: 40–69%
- Red: < 40%

**Overall object AI-readiness status:** [Red / Amber / Green]

**Notes:**
[Document any fields where nulls are semantically meaningful rather than data quality gaps]

---

## 3. Data Placement Decisions

For each data category relevant to this implementation, specify where it will be stored.

| Data category | Example data | Placement decision | Rationale |
|---|---|---|---|
| Structured CRM records | Accounts, Contacts, Opportunities | [Salesforce objects / Data Cloud / External] | |
| High-volume event data | Email opens, web clicks, IoT events | [Salesforce objects / Data Cloud / External] | |
| Knowledge and policy content | Help articles, runbooks, product docs | [Salesforce Knowledge / External CMS / Data Cloud] | |
| Binary and media files | PDFs, images, audio recordings | [External store (S3 / Azure Blob) / Salesforce Files] | |
| Real-time streams | Live sensor data, payment events | [Data Cloud streaming / MuleSoft / External] | |

**Decision notes:**
[Document any non-standard placement decisions with justification]

---

## 4. Text Field Design for Embedding

Complete this section only if vector search or RAG grounding is in scope.

| Object | Field API Name | Field Type | Max Length | HTML Content? | Stripping Required? | Chunking Required? | Language(s) |
|---|---|---|---|---|---|---|---|
| [e.g., Knowledge__kav] | [Body] | [Rich Text Area] | [131,072] | [Yes] | [Yes] | [Yes — >2,000 chars] | [English] |
| | | | | | | | |

**Embedding pipeline transformation steps:**
1. [e.g., Strip HTML using String.stripHtmlTags() in Apex or BeautifulSoup in Python]
2. [e.g., Normalize whitespace — remove double spaces, non-breaking spaces]
3. [e.g., Chunk text at H2/H3 boundaries for articles; at 500-token windows for free-form text]
4. [e.g., Prepend article title and category metadata to each chunk for context]

---

## 5. Knowledge Article Structure (RAG)

Complete this section if Agentforce or another RAG system will ground on Salesforce Knowledge.

**Article template:**

```
Title: [One topic, declarative, ≤10 words]
Category: [From approved taxonomy]
Product: [From approved taxonomy]
Audience: [Retail / Advisor / Internal]
Topic: [From approved taxonomy]

Summary: [1–2 sentence declarative summary of what this article covers. This is the most important sentence for retrieval — make it explicit and specific.]

## [H2 Section — first major subtopic]
[200–400 words max per H2 section]

## [H2 Section — second major subtopic]
[200–400 words max per H2 section]

[Max total length: 800 words. If content exceeds this, split into a separate article.]
```

**Metadata taxonomy:**

| Dimension | Approved values |
|---|---|
| Product | [List product names] |
| Audience | [List audience segments] |
| Topic | [List topic categories] |

**Articles requiring immediate restructure (identified in audit):**
| Article title | Problem | Action |
|---|---|---|
| | | |

---

## 6. Data Freshness Requirements

| AI feature | Data source | Sync mechanism | Required cadence | Staleness tolerance | Owner |
|---|---|---|---|---|---|
| [e.g., Einstein Opp Scoring] | [Opportunity, Account] | [Scheduled batch] | [Daily] | [24 hours] | [CRM Ops] |
| [e.g., Agentforce Knowledge] | [Knowledge articles] | [Data Cloud connector] | [Hourly] | [4 hours] | [Content Ops] |
| | | | | | |

**Cadence gaps identified:**
[List any AI features where current sync cadence does not meet the required freshness SLA]

---

## 7. Data Cloud Configuration

Complete this section if Data Cloud is in scope.

### Identity Resolution Strategy

**Primary identity attributes:**
| Source | Identity attribute | Format | Notes |
|---|---|---|---|
| [e.g., Salesforce CRM] | [ContactId] | [18-char Salesforce ID] | |
| [e.g., Commerce platform] | [customer_email] | [Normalized to lowercase] | |

**Identity resolution ruleset configured:** [Yes / No / In progress]

**Test unification completed on sample set:** [Yes / No]

### Field Mapping and Harmonization

**Canonical field conflicts identified:**
| Concept | Source A field | Source B field | Resolution |
|---|---|---|---|
| [e.g., Customer value] | [AnnualRevenue] | [customer_ltv] | [Separate into two fields; document semantic difference] |

### Activation Configuration

**Activation targets:**
| Data Cloud attribute | CRM target object | CRM target field | DC attribute type | CRM field type | Type compatible? |
|---|---|---|---|---|---|
| | | | | | |

**Dry-activation test completed:** [Yes / No / Date]

---

## 8. Einstein Feature Store

Complete this section if Einstein predictive scoring is in scope.

**Scored objects:**
| Object | Einstein feature | Score field API name | Reason fields | Custom feature extractors? |
|---|---|---|---|---|
| [e.g., Opportunity] | [Opportunity Scoring] | [EinsteinScore__c] | [EinsteinScoreReason1__c, 2, 3] | [Yes / No] |

**Custom AIFeatureExtractor definitions (if applicable):**
[Document metadata type names, what signals they extract, and which API version they target]

**Confirmed: Score fields are NOT used in synchronous trigger or Flow logic:** [Yes / No]
[If No, document where they are used and the remediation plan]

---

## 9. AI-Ready Field Naming Conventions

**Naming convention adopted:**
[e.g., AI_ prefix for all AI-specific custom fields, ML_ for feature store fields, Score_ for output score fields]

**Fields requiring rename for convention compliance:**
| Current API name | Object | Recommended API name | Notes |
|---|---|---|---|
| | | | |

**Field description completion:**
All AI-relevant custom fields must have descriptions populated in the field metadata. Fields missing descriptions:
| Field | Object | Description needed |
|---|---|---|
| | | |

---

## 10. Data Quality Gate Checklist

Complete before activating any AI feature in production. All items must be Green before proceeding.

| Check | Criteria | Status | Evidence |
|---|---|---|---|
| Fill rate — all predictor fields | ≥ 70% fill rate | [Red / Amber / Green] | [Link to report or SOQL result] |
| Picklist consistency | No legacy/junk values; "Other" < 20% | [Red / Amber / Green] | |
| Training record volume | Meets minimum for each Einstein feature | [Red / Amber / Green] | [Count of qualifying records] |
| Sync cadence validated | All sync jobs running and within SLA | [Red / Amber / Green] | |
| No circular dependencies | Score fields not used as model inputs | [Red / Amber / Green] | |
| HTML stripping confirmed | All text fields stripped before embedding | [Red / Amber / Green] | |
| Identity resolution tested | Sample unification confirmed correct | [Red / Amber / Green] | |
| Activation type compatibility | All activation field types validated | [Red / Amber / Green] | |
| Knowledge article structure | Articles restructured to chunking standard | [Red / Amber / Green] | |
| Score fields excluded from sync logic | No Einstein score reads in triggers/Flows | [Red / Amber / Green] | |

**Overall AI-readiness status:** [Red — not ready / Amber — conditional / Green — ready for production activation]

**Sign-off:**
| Role | Name | Date |
|---|---|---|
| Data Architect | | |
| CRM Admin / Ops | | |
| AI Feature Owner | | |

---

## 11. Open Issues and Risks

| Issue | Impact | Owner | Target resolution date |
|---|---|---|---|
| | | | |
