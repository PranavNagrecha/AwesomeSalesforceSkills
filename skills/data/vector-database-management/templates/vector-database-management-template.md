# Vector Database Management: Design Template

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

**Source DMO / UDMO name (not mapped from external DLOs):** _____________________________

**Data Space:** _____________________________

**Text fields to index** (list only fields that answer questions; no personal data):

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

## 3. Setup Mode and Chunking

**Setup mode:**
- [ ] Easy Setup (defaults: passage extraction, E5-Large V2, hybrid search; no filter fields in the steps)
- [ ] Advanced Setup (choose search type, chunking per field or file type, prepend fields, max tokens, model, up to 10 filter fields)

| Parameter | Value | Rationale |
|---|---|---|
| Search type | Vector / Hybrid | (hybrid when text contains codes or domain terms) |
| Chunking strategy | Passage extraction / Conversation-based / other | |
| Prepend fields | | (for example Title) |
| Max tokens | 512 default | (lower for non-Latin text) |

Chunking strategy, max tokens, and model are view-only after creation. Changing them means a new index.

---

## 4. Embedding Model

**Selected model:** [ ] E5-Large V2   [ ] Multilingual E5-Large   [ ] Whisper-Large-V3 (listed in the Search Index Reference)

**Reason for selection:** (language mix, content type)

---

## 5. Filter Fields and Retrievers

| Filter field (max 10) | Source object or related object (1:1 or N:1) | Used by retriever |
|---|---|---|
| | | |

---

## 6. Freshness and Cost

- Source data stream refresh mode: [ ] Incremental   [ ] Upsert   [ ] Full Refresh (replaces all data each cycle)
- Data stream schedule: _____
- Estimated vector count: _____ (vector search query billing counts the vectors in the index)
- Expected queries per day: _____
- Search index count after this one (limit 10 per Data Cloud instance): _____

---

## 7. Configuration Record

| Configuration Item | Value |
|---|---|
| Index name and API name | |
| Data space | |
| Source DMO / UDMO | |
| Chunked fields | |
| Excluded fields (personal or regulated) | |
| Search type | |
| Chunking strategy and prepend fields | |
| Max tokens | |
| Embedding model | |
| Filter fields | |
| Custom retrievers that reference it | |
| Created date / created by | |

**Replacement procedure (chunking or model change):**
1. Create a second index with the new settings.
2. Wait for status Ready (Submitted, In-progress, Ready, Failed).
3. Run the validation queries in Section 8 against both indexes.
4. Point custom retrievers at the new index and activate the new versions.
5. Delete the old index (blocked while any retriever references it).
6. Update this record.

---

## 8. Validation Queries

List 5 to 10 representative questions. Run each with `vector_search` or `hybrid_search` joined to the chunk DMO.

| Question | Expected chunk (article / section) | Pass? |
|---|---|---|
| | | [ ] |
| | | [ ] |
| | | [ ] |
| | | [ ] |
| | | [ ] |

**Acceptance criteria:** _____ of _____ questions return the expected chunk in the top results.

---

## 9. Review Checklist

- [ ] Data space and source object recorded
- [ ] Chunked fields reviewed; personal and regulated fields excluded
- [ ] Setup mode, chunking, max tokens, and model justified
- [ ] Filter fields defined before retrievers need them
- [ ] Data stream refresh mode and schedule match the freshness need
- [ ] Vector count and query cost estimated
- [ ] `python3 scripts/check_vector_database_management.py --manifest-dir <retrieved metadata>` reviewed
- [ ] Validation queries passing before go-live
