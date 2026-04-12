# Data Cloud Vector Search Dev — Implementation Checklist Template

Use this template when implementing or reviewing a Data Cloud vector search configuration for an Agentforce grounding use case.

---

## Scope

**Skill:** `data-cloud-vector-search-dev`

**Request summary:** (fill in what the user or project requires)

**Use case type:** (e.g., Agentforce grounding / Query API integration / index rebuild / packaging)

---

## Context Gathered

Answer these before starting any configuration work:

- **Data Cloud Vector Search enabled?** Yes / No / Unknown
- **Source object type:** DMO / Unstructured Data Lake Object / Other
- **Source object name and text field:**
- **Setup mode decision:** Easy Setup (prototype only) / Advanced Setup (production)
- **Chunking strategy (Advanced Setup):** Fixed-size / Paragraph / Sentence
- **Chunk size and overlap (if Fixed-size):** `___` tokens / `___` tokens overlap
- **Embedding model:** Salesforce-managed / BYO via Model Builder (specify model):
- **Estimated source record count:**
- **Query API required?** Yes / No — if Yes, Data Cloud Connected App with cdpapi scope exists: Yes / No
- **Grounding configuration target:** Agent topic name / Prompt Template name
- **top-K value:**
- **Metadata filters required?** Yes / No — if Yes, filter field and expression:
- **PII or sensitive fields in source DMO?** Yes / No — if Yes, classified in DC field taxonomy: Yes / No / Pending

---

## Index Configuration Record

| Parameter | Value | Rationale |
|---|---|---|
| Index name | | |
| Source DMO / UDLO | | |
| Source text field | | |
| Setup mode | Easy Setup / Advanced Setup | |
| Chunking strategy | | |
| Chunk size (tokens) | | |
| Chunk overlap (tokens) | | |
| Embedding model | | |
| Refresh cadence | Batch / Near-real-time | |
| Index region | | (must match org data residency requirement) |

---

## Query API Configuration (if applicable)

| Parameter | Value |
|---|---|
| Data Cloud Connected App name | |
| OAuth scope confirmed (cdpapi) | Yes / No |
| Token endpoint | `<org-url>/services/a360/token` |
| Data Cloud instance URL (from token response) | |
| Index name used in Query API path | |
| Test query executed and response validated | Yes / No |

---

## Grounding Configuration Record

| Parameter | Value |
|---|---|
| Grounding config name | |
| Target (agent topic or prompt template) | |
| Vector index referenced | |
| top-K | |
| Metadata filter expression | (or N/A) |
| Merge fields in filter (if any) | (or N/A) |

---

## Implementation Checklist

### Prerequisites

- [ ] Data Cloud Vector Search feature is enabled in Setup → Data Cloud → Vector Search
- [ ] Salesforce-managed embedding model shows as Active
- [ ] Source DMO or UDLO is populated with at least representative test data
- [ ] Data Cloud Connected App with `cdpapi` scope exists (if Query API required)
- [ ] PII/sensitive fields in source DMO have been classified in the Data Cloud field taxonomy

### Index Creation

- [ ] Advanced Setup selected (if production or precision-sensitive use case)
- [ ] Chunking strategy explicitly chosen and documented in the decision record above
- [ ] Chunk size and overlap values set (Advanced Setup only) with rationale recorded
- [ ] Embedding model selected
- [ ] Index refresh cadence configured (batch or near-real-time) based on content currency requirements
- [ ] Initial index build triggered and index Status confirmed as Active before proceeding

### Query API (if applicable)

- [ ] Data Cloud access token obtained from `/services/a360/token` (NOT from `/services/oauth2/token`)
- [ ] Data Cloud `instance_url` from token response used as base URL for all Query API calls
- [ ] Test query executed with expected input; response includes `results` array with chunks and scores
- [ ] Error handling implemented for 401 (token expired), 404 (index name mismatch), and 429 (rate limit)

### Grounding Configuration

- [ ] Grounding configuration record created and references the correct vector index
- [ ] top-K set to starting value of 3–5 (raise only after recall testing)
- [ ] Metadata filters validated: filter expression syntax correct and merge field resolves at runtime
- [ ] Grounding configuration attached to the correct agent topic or Prompt Template

### Validation and QA

- [ ] Agent Preview tested with 5+ representative queries; Grounding tab confirms relevant chunks retrieved
- [ ] Einstein Trust Layer audit log reviewed for at least one end-to-end retrieval turn
- [ ] Any masking events in the audit log investigated and confirmed intentional
- [ ] Prompt token budget checked: topK × chunk_size_estimate should not exceed 30% of model context window
- [ ] Retrieval latency measured for at least 3 queries; within acceptable SLA range

### Packaging (if applicable)

- [ ] Vector search index configuration added to Data Kit (not standard SFDX metadata)
- [ ] Source DMO definition and Data Stream configuration also included in the Data Kit
- [ ] Data Kit validated in scratch org: index created, Active, and returns results for a test query

---

## Decision Record

Document key decisions for audit and future tuning:

**Why Advanced Setup (or Easy Setup):**

**Chunking strategy rationale:**

**Chunk size / overlap rationale:**

**Embedding model rationale:**

**top-K rationale:**

**Metadata filter rationale (if used):**

**Data residency notes:**

**Known limitations or deferred optimizations:**

---

## Notes

Record any deviations from the standard pattern and the reason for each deviation.
