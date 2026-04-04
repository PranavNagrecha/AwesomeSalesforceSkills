# Bulk API Patterns — Work Template

Use this template when implementing or reviewing a Bulk API 2.0 integration.

---

## 1. Scope

**Object being loaded / queried:** _______________________________________________

**Operation:**
- [ ] insert
- [ ] update
- [ ] upsert (external ID field: ___________________)
- [ ] delete
- [ ] hardDelete
- [ ] query

**Source system / file:** _______________________________________________

**Estimated record count:** _______________________________________________

---

## 2. API Version Selection

**Selected API:**
- [ ] Bulk API 2.0 — REST, OAuth 2.0, CSV only, auto-batching (recommended for all new work)
- [ ] Bulk API v1 — SOAP, session ID, CSV/XML/JSON, manual batching, serial mode available

**Reason for v1 if chosen:**
- [ ] Serial concurrency mode required (lock contention that cannot be resolved by CSV sort order)
- [ ] Non-CSV content type required (XML, JSON, or binary attachments)

---

## 3. CSV Format Declaration

**Line ending in source file:**
- [ ] LF (Unix/macOS) — declare `"lineEnding": "LF"` at job creation
- [ ] CRLF (Windows/DOS) — declare `"lineEnding": "CRLF"` at job creation

**Column delimiter:**
- [ ] COMMA (default) — no `columnDelimiter` needed unless explicit
- [ ] Other: ___________________ — declare `"columnDelimiter"` at job creation

**Null handling confirmed:**
- [ ] Empty cells verified not to be used for null — using `#N/A` to null fields

**Date/time format confirmed:** ISO 8601 (`YYYY-MM-DDTHH:MM:SS.sssZ`)

---

## 4. Job Creation Method

**Method:**
- [ ] Standard: POST /jobs/ingest/ → upload chunks → PATCH UploadComplete
- [ ] Multipart: POST /jobs/ingest/ with multipart body (auto-completes UploadComplete)

**If multipart:**
- [ ] Payload confirmed under 100,000 characters of CSV
- [ ] Pipeline logic does NOT send a second UploadComplete PATCH

**If standard:**
- [ ] Upload chunk sizes confirmed under 100 MB raw (150 MB base64)
- [ ] Number of chunks: _______________
- [ ] UploadComplete PATCH included in pipeline (mandatory — job never starts without it)

---

## 5. Job Monitoring

**Poll interval:** _______________ seconds (recommended: 15–30 seconds)

**Terminal state handling:**
- [ ] JobComplete — proceed to result retrieval
- [ ] Failed — investigate batch timeout cause; submit new job for all records
- [ ] Aborted — determine who/what aborted and resubmit if appropriate

**Job ID recorded:** _______________________________________________

---

## 6. Result Retrieval Checklist

Complete all three after every terminal state:

- [ ] `GET .../successfulResults/` retrieved — count: _______________
- [ ] `GET .../failedResults/` retrieved — count: _______________
- [ ] `GET .../unprocessedRecords/` retrieved — count: _______________

**Integrity check:** successful + failed + unprocessed == total uploaded?
- Expected total: _______________
- Actual sum: _______________
- [ ] Check passes

---

## 7. Query Job Pagination (if applicable)

- [ ] First result page retrieved
- [ ] Sforce-Locator header checked with **string equality** to `"null"` (not `None`, not empty)
- [ ] All pages downloaded and written to output files (header row only from page 1)
- [ ] Final page count: _______________
- [ ] Total records across all pages: _______________

---

## 8. Failed Record Retry Plan

**If failedResults count > 0:**

| Error category (from sf__Error) | Count | Fix required |
|---|---|---|
| ___________________ | ___ | ___________________ |
| ___________________ | ___ | ___________________ |

- [ ] Root cause fixed for each error category
- [ ] New job created for failed records (do not reuse original job ID)
- [ ] Retry job completed and verified

**If unprocessedRecords count > 0:**

- [ ] Root cause investigated (batch timeout, lock contention, peak org load)
- [ ] Mitigation applied (CSV sort by parent ID, deferred sharing calculation, etc.)
- [ ] New job created for unprocessed records

---

## 9. Hard Delete Verification (if applicable)

- [ ] Running user has "Bulk API Hard Delete" permission confirmed
- [ ] Data verified before submission — hard-deleted records cannot be recovered
- [ ] Change management approval obtained

---

## 10. Notes and Deviations

Record any deviations from the standard pattern and the reason:

_______________________________________________
_______________________________________________
_______________________________________________
