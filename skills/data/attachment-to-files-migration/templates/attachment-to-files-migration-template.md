# Attachment to Files Migration — Work Template

Use this template when planning and executing the migration of Classic Attachments and Notes to Salesforce Files.

---

## Scope

**Skill:** `attachment-to-files-migration`

**Source:** [ ] Attachments only  [ ] Notes only  [ ] Both

**Target volume:** _(count of records, total bytes)_

**Approach:** [ ] Batch Apex (in-org)  [ ] Bulk API 2.0 (external orchestration)  [ ] Live cutover (trigger + batch)

---

## Pre-Migration Profile

```sql
SELECT COUNT(Id) attCount, SUM(BodyLength) attBytes FROM Attachment;
SELECT COUNT(Id) noteCount FROM Note;
SELECT Parent.Type, COUNT(Id) cnt FROM Attachment GROUP BY Parent.Type ORDER BY cnt DESC;
```

| Metric | Value |
|---|---|
| Attachment count | |
| Total bytes | |
| Note count | |
| Distinct parent types | |
| Largest single Attachment (MB) | |
| Files storage allocation (MB) | |
| Files storage utilization (%) | |

---

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Batch scope size | _(typically 10; lower for files >5MB)_ | |
| Origin tracking field | `ContentVersion.Source_Attachment_Id__c` (External ID, Unique) | Enables idempotent re-runs |
| Inactive owner handling | [ ] Reassign to migration user [ ] Preserve [ ] Reassign to parent owner | |
| Visibility default | [ ] InternalUsers [ ] AllUsers (must check OWD per parent) | |
| `CreatedDate` preservation | [ ] Yes (requires "Set Audit Fields" perm) [ ] No | |
| EmailMessage parents | [ ] Migrate + delete source [ ] Migrate + retain source [ ] Skip entirely | |

---

## Sharing Translation Map

| Source Pattern | ContentDocumentLink.ShareType | ContentDocumentLink.Visibility |
|---|---|---|
| `Attachment.IsPrivate = true` | `V` | `InternalUsers` |
| `Attachment.IsPrivate = false`, parent OWD private | `V` | `InternalUsers` |
| `Attachment.IsPrivate = false`, parent OWD public | `V` | `AllUsers` |

---

## Cutover Plan

| Phase | Task | Owner | Date |
|---|---|---|---|
| 1 | Add `Source_Attachment_Id__c` to ContentVersion | | |
| 2 | Sandbox migration of 10K-record sample | | |
| 3 | Validate sample (counts, sharing, owner) | | |
| 4 | Production: deploy trigger (live cutover only) | | |
| 5 | Production: launch background batch | | |
| 6 | Reconciliation pass (zero pending) | | |
| 7 | Cleanup batch (gated on Cleanup_Approved__c) | | |
| 8 | Decommission Attachment creation (validation rule or perm removal) | | |

---

## Verification SOQL Pack

```sql
-- Pending
SELECT COUNT(Id) FROM Attachment
WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion);

-- Per parent type
SELECT LinkedEntity.Type, COUNT(Id)
FROM ContentDocumentLink
WHERE ContentDocumentId IN (SELECT ContentDocumentId FROM ContentVersion WHERE Source_Attachment_Id__c != null)
GROUP BY LinkedEntity.Type;

-- Failures
SELECT Status__c, Error__c, COUNT(Id)
FROM Migration_Log__c GROUP BY Status__c, Error__c;
```

---

## Sign-Off Checklist

- [ ] Source counts match destination counts (or differences are documented exclusions)
- [ ] Sharing visibility tested for at least one user per relevant role
- [ ] Inactive-owner policy applied consistently
- [ ] Reports / list views / LWCs updated to ContentDocumentLink relationships
- [ ] Cleanup gated on a separate approval flag, not auto-cascaded
- [ ] EmailMessage parent decision documented and applied
