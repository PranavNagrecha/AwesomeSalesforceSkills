# Service Data Archival Plan

Use this template to plan and document a Case-related archival engagement. Fill every section before executing any deletions.

---

## 1. Scope

**Skill:** `service-data-archival`

**Request summary:** (What is the business driver? Storage limit approaching? Compliance requirement? Cost reduction?)

**Objects in scope:**

- [ ] Case
- [ ] EmailMessage
- [ ] ContentDocumentLink
- [ ] ContentDocument / ContentVersion
- [ ] Other: _______________

**Objects explicitly out of scope:** (list any objects that must NOT be touched)

---

## 2. Storage Baseline

Run Setup > Company Information > Storage Usage before any changes. Record:

| Storage Pool | Current Usage (GB) | Limit (GB) | % Used |
|---|---|---|---|
| Data Storage | | | |
| File Storage | | | |

Run aggregate queries and record:

| Object | Record Count | Estimated Storage |
|---|---|---|
| Case (total) | | |
| EmailMessage (total) | | |
| ContentDocument (total) | | |
| ContentDocumentLink (total) | | |

**Primary storage driver identified:** (Data storage / File storage / Both)

**Root cause object:** (e.g., EmailMessage from Email-to-Case)

---

## 3. Retention Policy Matrix

Confirm with legal/compliance before proceeding. Fill one row per object type in scope.

| Object | Minimum Retention Period | Delete-Eligible After | Export Required Before Delete? | Notes |
|---|---|---|---|---|
| Case | | | Yes / No | |
| EmailMessage | | | Yes / No | |
| ContentDocument | | | Yes / No | |

**Legal-hold criteria:** (How are legal-hold records identified? Field name? Feature?)

**Legal-hold field / mechanism:** `_________________________`

---

## 4. Legal-Hold Exclusion List

**Date list was last refreshed:** _______________

**Source of truth for legal-hold list:** (e.g., Legal team Quip doc, custom object, platform Legal Hold feature)

**Record count currently under hold:**
- Cases: _______________
- EmailMessage records (via parent Case): _______________

**Confirmation that hold list is applied in all SOQL WHERE clauses:** [ ] Yes

---

## 5. Export / Archive Plan

For each object in scope that requires export-before-delete, document the export destination and confirm completion before any deletions run.

| Object | Export Destination | Format | Export Confirmed? |
|---|---|---|---|
| Case | | | [ ] |
| EmailMessage | | | [ ] |
| ContentDocument blobs | | | [ ] |

---

## 6. Deletion Sequence

Execute in this order. Check off each step only after validating the row count is zero.

**Step 1 — ContentDocumentLink deletion**

```soql
-- Query ContentDocumentLink records for target Cases (exclusively linked)
SELECT Id FROM ContentDocumentLink
WHERE LinkedEntityId IN :targetCaseIds
  AND ContentDocumentId IN (
    SELECT ContentDocumentId FROM ContentDocumentLink
    GROUP BY ContentDocumentId HAVING COUNT(Id) = 1
  )
```

- Target record count: _______________
- Bulk API 2.0 job ID: _______________
- Post-deletion count (should be 0): _______________
- [ ] Confirmed

**Step 2 — ContentDocument deletion**

```soql
-- Query now-orphaned ContentDocument records (no remaining links)
SELECT Id FROM ContentDocument
WHERE Id IN :targetContentDocIds
```

- Target record count: _______________
- Bulk API 2.0 job ID: _______________
- Post-deletion count (should be 0): _______________
- [ ] Confirmed

**Step 3 — EmailMessage deletion**

```soql
SELECT Id FROM EmailMessage
WHERE CaseId IN :targetCaseIds
  AND Parent.Legal_Hold__c = false
```

- Target record count: _______________
- Bulk API 2.0 job ID: _______________
- Post-deletion count (should be 0): _______________
- [ ] Confirmed

**Step 4 — Case deletion** (if Cases are in scope)

```soql
SELECT Id FROM Case
WHERE ClosedDate < :retentionThresholdDate
  AND IsClosed = true
  AND Legal_Hold__c = false
```

- Target record count: _______________
- Bulk API 2.0 job ID: _______________
- Post-deletion count (should be 0): _______________
- [ ] Confirmed

---

## 7. Recycle Bin

- [ ] Recycle Bin explicitly emptied via hard-delete OR via `Database.emptyRecycleBin()` Apex job
- Date emptied / date to wait until: _______________

---

## 8. Post-Deletion Storage Report

Re-run Setup > Storage Usage after Recycle Bin is cleared. Record:

| Storage Pool | Pre-Deletion (GB) | Post-Deletion (GB) | Delta (GB) |
|---|---|---|---|
| Data Storage | | | |
| File Storage | | | |

**Expected reclaim matches actual reclaim:** [ ] Yes — [ ] No (investigate if No)

---

## 9. Orphan Scan

Run `scripts/check_service_data_archival.py` and record output:

```
(paste script output here)
```

Orphaned ContentDocumentLink records found: _______________
Orphaned ContentDocument records found: _______________
EmailMessage records for deleted Cases found: _______________

**All counts zero:** [ ] Yes — [ ] No (investigate if No)

---

## 10. Sign-Off

| Role | Name | Date | Sign-Off |
|---|---|---|---|
| Data Admin | | | [ ] |
| Legal / Compliance | | | [ ] |
| Salesforce Admin | | | [ ] |

**Notes:** (Record any deviations from the standard sequence, exceptions granted, or issues encountered)
