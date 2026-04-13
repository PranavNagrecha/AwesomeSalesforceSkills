# Vector Database Management — Design Template

Use this template when designing a new vector index or planning a rebuild of an existing one.
Fill in every section before creating or modifying any index in Setup.

---

## 1. Use Case

**Request summary:** (what the Agentforce agent or search feature needs to retrieve)

**Query characteristics:**
- Typical query length: _____ characters / _____ words
- Query style: [ ] Short keyword-style   [ ] Full sentence   [ ] Multi-sentence natural language
- Expected answer type: [ ] Specific fact   [ ] Summary of a section   [ ] Multi-step procedure

---

## 2. Source Data

**Source DMO / UDLO name:** _____________________________

**Data Space:** _____________________________

**Text fields to index** (list only semantic content fields — no PII):

| Field API Name | Description | PII? (exclude if yes) |
|---|---|---|
| | | [ ] Yes  [ ] No |
| | | [ ] Yes  [ ] No |
| | | [ ] Yes  [ ] No |

**Fields explicitly excluded for PII reasons:**

| Field API Name | PII Classification |
|---|---|
| | |

---

## 3. Chunking Strategy

**Selection:**
- [ ] Easy Setup (500-character fixed chunks, no overlap) — appropriate for short, uniform documents only
- [ ] Advanced Setup — required for production knowledge bases, longer documents, or precision-sensitive use cases

**If Advanced Setup:**

| Parameter | Value | Rationale |
|---|---|---|
| Chunk size (characters) | | (match to average paragraph length or ~1.5× typical query length) |
| Chunk overlap (%) | | (typically 10%; prevents relevant passages from straddling chunk boundaries) |

**Justification for this chunk size:** (describe the source document structure that drove this choice)

---

## 4. Embedding Model

**Selected model:** _____________________________

**Reason for selection:** (general-purpose vs. domain-specific, quality tier)

**Note:** Changing the embedding model after index creation requires a full delete-and-rebuild. Record this selection for the rebuild runbook.

---

## 5. Refresh Mode

**Selected mode:**
- [ ] Batch (default) — appropriate for static corpora or infrequently updated DMOs
- [ ] Continuous — appropriate when retrieval freshness is a documented business requirement

**If Continuous:**
- Estimated source DMO update frequency: _____ updates/hour
- Data Cloud credit consumption alert set? [ ] Yes — alert threshold: _____   [ ] No (set before enabling)
- Business justification for continuous mode: _____________________________

---

## 6. Rebuild Runbook

Record this section after the index is created. It is the authoritative reference for any future rebuild.

| Configuration Item | Value |
|---|---|
| Index name | |
| Source DMO / UDLO | |
| Data Space | |
| Indexed field list | |
| Excluded fields (PII) | |
| Chunking strategy | Easy Setup / Advanced Setup |
| Chunk size (chars) | |
| Chunk overlap (%) | |
| Embedding model | |
| Refresh mode | Batch / Continuous |
| Index created date | |
| Last rebuilt date | |
| Rebuilt by | |

**Rebuild trigger conditions** (mark all that apply):
- [ ] Chunking strategy or parameters need to change
- [ ] Embedding model upgrade
- [ ] Source DMO schema change (new fields added/removed)
- [ ] Retrieval precision degraded and chunk strategy is the diagnosed cause

**Rebuild procedure:**
1. Notify stakeholders of expected index availability gap (estimated rebuild time: _____ minutes/hours).
2. In Data Cloud Setup > Vector Indexes, delete the existing index.
3. Create new index using the updated configuration recorded in this runbook.
4. Monitor index status until Active.
5. Run validation queries (see Section 7) before restoring production traffic.
6. Update this runbook with new configuration and rebuild date.

---

## 7. Validation Queries

List 5–10 representative queries that must return relevant results before the index is considered production-ready.

| Query | Expected top result (document section / chunk content summary) | Pass? |
|---|---|---|
| | | [ ] |
| | | [ ] |
| | | [ ] |
| | | [ ] |
| | | [ ] |

**Acceptance criteria:** _____ of _____ validation queries return a relevant top result.

---

## 8. Review Checklist

- [ ] Source DMO is active and Data Space is configured
- [ ] All indexed fields reviewed for PII; exclusions documented above
- [ ] Chunking strategy and parameters justified based on query characteristics and document structure
- [ ] Embedding model recorded in rebuild runbook
- [ ] Refresh mode set appropriately; credit alert configured if continuous
- [ ] Rebuild runbook complete with all configuration values
- [ ] Validation queries defined and passing before production go-live
