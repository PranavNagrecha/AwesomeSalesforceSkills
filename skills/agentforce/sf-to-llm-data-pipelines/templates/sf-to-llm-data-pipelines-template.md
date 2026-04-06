# SF-to-LLM Data Pipelines — Work Template

Use this template when designing or implementing a Salesforce-to-external-LLM data pipeline.

## Scope

**Skill:** `sf-to-llm-data-pipelines`

**Request summary:** (describe what the user needs — e.g., "nightly Knowledge article sync to Pinecone", "incremental case extraction for external chatbot")

---

## 1. Field Classification Matrix

Complete this before writing any SOQL or pipeline code.

| Object API Name | Field API Name | Field Label | Data Type | PII Classification | Treatment |
|---|---|---|---|---|---|
| (e.g. Case) | (e.g. Description) | (e.g. Description) | Long Text Area | ner-required | NER scrub before chunking |
| | | | | | |
| | | | | | |

**PII Treatment Key:**
- `safe` — no PII; include in SOQL and transmit as-is
- `pseudonymize` — direct identifier; replace with HMAC-SHA256 before transmission
- `scrub` — omit from SOQL SELECT entirely
- `ner-required` — free-text; run NER pass and replace detected entities with `[PERSON]`, `[EMAIL]`, `[PHONE]` before chunking

---

## 2. Legal and Compliance Confirmation

- [ ] DPA or equivalent legal instrument confirmed with external LLM/vector store provider: **[Provider name, DPA reference, date confirmed]**
- [ ] Data residency requirement for external store: **[Region/jurisdiction]**
- [ ] GDPR/CCPA/other regulation in scope: **[Yes/No — if yes, list applicable regulations]**
- [ ] Right-to-Erasure procedure required: **[Yes/No]**

---

## 3. Extraction Design

### Target Objects

| Object API Name | Record Volume (approx.) | Extraction Cadence | Pattern |
|---|---|---|---|
| (e.g. KnowledgeArticleVersion) | (e.g. 80,000) | (e.g. nightly full load) | (e.g. Bulk API v2 full load) |
| | | | |

### SOQL Queries

For each target object, write the validated SOQL (omitting `scrub`-classified fields):

**Object: ____________**
```sql
SELECT
  -- fields from classification matrix with treatment = safe or pseudonymize
  -- SystemModstamp is always required for watermark tracking
  Id,
  SystemModstamp,
  [add safe fields here]
FROM [ObjectAPIName]
WHERE [PublishStatus = 'Online' for KnowledgeArticleVersion]
  [AND SystemModstamp >= :last_sync for incremental runs]
```

### Extraction Pattern

- [ ] Full load (nightly or periodic)
- [ ] Incremental with SystemModstamp watermark
- [ ] Incremental + CDC for hard-delete propagation

**Watermark storage location:** (where is `last_sync` durably stored?)

**Watermark advancement rule:** (advance only after confirmed vector store write? document the logic)

---

## 4. Transformation Design

### HTML Stripping

Fields requiring HTML stripping before chunking (all Rich Text Area and Long Text Area fields from Knowledge):

| Object | Field | Strip Method |
|---|---|---|
| (e.g. KnowledgeArticleVersion) | (e.g. Body) | (e.g. html.parser + TAG_RE substitution) |

### Chunking Configuration

| Object / Field Group | Chunk Size (tokens) | Overlap (tokens) | Splitting Strategy | Rationale |
|---|---|---|---|---|
| (e.g. Knowledge Body) | (e.g. 512) | (e.g. 64) | (e.g. recursive sentence) | (e.g. article paragraphs avg 400 tokens; fixed split preserves paragraphs) |

### Metadata Envelope per Chunk

Every chunk stored in the external vector store must carry:

| Metadata Field | Source | Notes |
|---|---|---|
| `record_id` | Salesforce `Id` (pseudonymized if required) | Used for erasure targeting |
| `object_api_name` | Literal string | Enables cross-object queries |
| `field_api_name` | Literal string | Identifies source field |
| `chunk_index` | Sequential integer per record | Enables ordered reconstruction |
| `total_chunks` | Total chunk count per record | Enables completeness checks |
| `last_modified` | `SystemModstamp` value | Enables stale-chunk detection |
| [additional metadata] | | |

---

## 5. Embedding Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Embedding model | (e.g. text-embedding-3-small) | |
| Embedding dimensions | (e.g. 1536) | |
| Batch size per API call | (e.g. 512 texts) | |
| Rate limit (tokens/min) | (from provider documentation) | |
| Estimated tokens per run | (chunks × avg chunk token length) | |

---

## 6. Vector Store Configuration

| Parameter | Value |
|---|---|
| Vector store | (e.g. Pinecone, pgvector, Weaviate, OpenSearch) |
| Index name / namespace | |
| Similarity metric | (e.g. cosine) |
| Upsert key pattern | (e.g. `{record_id_pseudonym}_{chunk_index}`) |
| Erasure method | (e.g. delete by `record_id` metadata filter) |

---

## 7. Pseudonym Mapping (if pseudonymization is in scope)

- **Pseudonymization algorithm:** HMAC-SHA256 keyed with `PSEUDONYM_SECRET` environment variable
- **Mapping table storage:** (e.g. PostgreSQL table `sf_pseudonym_map`, AWS DynamoDB)
- **Mapping table schema:** `pseudonym VARCHAR(64) PK, sf_record_id VARCHAR(18), object_api_name VARCHAR(80), created_at TIMESTAMP`
- **Access controls on mapping table:** (who can read the mapping? document)
- **Retention policy:** Mapping entries retained until all corresponding vector chunks are deleted

---

## 8. Monitoring and Alerting

| Signal | Alert Threshold | Action |
|---|---|---|
| NER entities detected per `ner-required` field | Zero when historical average > 0 | Investigate scrubber failure; halt run |
| Records extracted vs. expected (incremental) | > 2x normal delta volume | Investigate automation churn on `SystemModstamp` |
| Bulk API v2 job state | `Failed` or `Aborted` | Alert on-call; re-submit job |
| Vector store upsert errors | Any | Retain batch; retry before advancing watermark |
| Cursor expiry (HTTP 404 on results endpoint) | Any | Re-submit Bulk API v2 job; do NOT resume from partial cursor |

---

## 9. Review Checklist

Copy the full review checklist from SKILL.md and tick items as you complete them.

- [ ] Every field has a documented PII classification
- [ ] DPA confirmed with external LLM/vector store provider
- [ ] SOQL projection contains no `scrub`-classified fields
- [ ] HTML stripping applied before chunking for all rich text fields
- [ ] PII pseudonymization applied in-process before any outbound call
- [ ] NER scrubbing applied to all `ner-required` fields; audit log confirms non-zero entity detection on test sample
- [ ] Every stored chunk carries `record_id` and `last_modified` metadata
- [ ] SystemModstamp watermark advances only after confirmed vector store write
- [ ] CDC subscription in place for hard-delete propagation (if required)
- [ ] End-to-end test: 5+ queries return traceable, PII-free results
- [ ] GDPR erasure procedure documented, tested in staging

---

## Notes

(Record any deviations from the standard patterns documented in SKILL.md and the reason for each deviation.)
