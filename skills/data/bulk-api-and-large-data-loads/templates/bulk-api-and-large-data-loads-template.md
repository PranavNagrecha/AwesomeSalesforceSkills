# Bulk Load Planning Template

Use this template to plan, document, and review a Bulk API 2.0 load operation before implementation.

---

## 1. Scope

**Object being loaded:** _______________________________________________

**Operation:** [ ] insert  [ ] update  [ ] upsert  [ ] delete  [ ] hardDelete  [ ] query

**External ID field (upsert only):** _______________________________________________

**Source system / file:** _______________________________________________

---

## 2. Volume

**Estimated record count:** _______________________________________________

**Estimated CSV size (MB):** _______________________________________________

**Number of upload chunks needed** (each must be ≤100 MB raw):
- Chunk count: _______________

**Daily limit check:** Total records ≤ 150,000,000 per org per day? [ ] Yes  [ ] N/A

---

## 3. API Selection

**Recommended API:**
- [ ] Bulk API 2.0 — use when record count >2,000
- [ ] REST Composite — use when record count ≤2,000

**Rationale:** _______________________________________________

---

## 4. Concurrency Mode Decision

**Recommended mode:**
- [ ] Parallel (default) — recommended unless lock contention is a known risk
- [ ] Serial (Bulk API v1 only) — use when parallel causes UNABLE_TO_LOCK_ROW errors

**Object trigger complexity assessment:**
- Does the object have Apex triggers? [ ] Yes  [ ] No
- Do those triggers update parent records? [ ] Yes  [ ] No  [ ] Unknown
- Does the object use private sharing? [ ] Yes  [ ] No

**Rationale for mode choice:** _______________________________________________

**Mitigation if parallel is chosen:** _______________________________________________
(e.g., sort CSV by parent ID; defer sharing calculation)

---

## 5. Batch and Chunk Sizing Plan

**Upload chunk size:** _______________ MB per PUT request (must be ≤100 MB raw)

**Internal batch size:** Salesforce auto-creates one batch per 10,000 records — no manual action needed for Bulk API 2.0.

**Estimated number of internal batches:** (record count ÷ 10,000) = _______________

**Load window:** Start _______________ End _______________ (must complete before business hours or dependent processes start)

---

## 6. Monitoring Checklist

Complete these steps during and after the job run:

- [ ] Job created — note job ID: _______________
- [ ] All CSV chunks uploaded
- [ ] UploadComplete PATCH sent (MANDATORY — job does not start without this)
- [ ] Polling started — poll interval: _______________ seconds
- [ ] Terminal state reached: [ ] JobComplete  [ ] Failed  [ ] Aborted
- [ ] `successfulResults` retrieved — count: _______________
- [ ] `failedResults` retrieved — count: _______________
- [ ] `unprocessedRecords` retrieved — count: _______________
- [ ] Integrity check: successful + failed + unprocessed == total uploaded records? [ ] Yes  [ ] No (investigate if No)
- [ ] Source CSV archived until full success confirmed

---

## 7. Failed Record Retry Strategy

**If failedResults count > 0:**

1. Download `failedResults` CSV.
2. Inspect the `sf__Error` column — categorize errors by type (validation rule, duplicate, required field, etc.).
3. Fix root cause for each error category:
   - Validation rule: adjust source data or temporarily deactivate rule with change management approval.
   - Duplicate: resolve duplicate records or adjust duplicate rules.
   - Required field missing: backfill field value in source data.
4. Build a new CSV from the failed rows only.
5. Submit a NEW ingest job — do not reuse the original job ID.
6. Repeat monitoring checklist for the retry job.

**If unprocessedRecords count > 0:**

1. Download `unprocessedRecords` CSV.
2. Investigate batch timeout root cause (slow triggers, lock contention, peak org load).
3. Consider switching to serial mode or reducing chunk size.
4. Submit a NEW ingest job with the unprocessed rows.

**Maximum retry attempts planned:** _______________

**Escalation path if retries exhaust:** _______________________________________________

---

## 8. Post-Load Verification

- [ ] Record count in Salesforce matches expected total (run a SOQL COUNT query)
- [ ] Spot-check 10 randomly sampled records for data accuracy
- [ ] Sharing recalculation resumed (if deferred during load)
- [ ] Any disabled triggers or validation rules re-enabled
- [ ] Downstream processes released (reports, integrations, batch Apex that depends on this object)
- [ ] Job IDs and result CSVs archived for audit

---

## 9. Notes and Deviations

Record any deviations from the standard pattern and the reason:

_______________________________________________
_______________________________________________
_______________________________________________
