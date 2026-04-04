# Data Storage Management — Work Template

Use this template when working on a storage management task in Salesforce.

## Scope

**Skill:** `data-storage-management`

**Request summary:** (fill in what the user asked for — e.g., "diagnose 90% storage alert", "plan file upload feature", "reclaim storage after bulk delete")

---

## 1. Storage State Snapshot

Capture current state from Setup > Storage Usage before making any changes.

| Pool | Used (GB) | Allocated (GB) | % Used |
|---|---|---|---|
| Data Storage | | | |
| File Storage | | | |
| Recycle Bin | | | |

**Top 5 objects by data storage consumption:**

| Object | Records | Estimated Storage |
|---|---|---|
| | | |
| | | |
| | | |
| | | |
| | | |

**Top file storage consumers:**

| Category | Storage Used |
|---|---|
| ContentDocument / Files | |
| Attachments | |
| Documents | |
| Other | |

---

## 2. Context Gathered

Answer each question before planning any action:

- **Org edition and license count:**
- **Allocated data storage (formula: base + per-user):**
- **Allocated file storage (formula: base + per-user):**
- **Which pool is the primary concern — data or file?**
- **Is Recycle Bin holding significant storage?** Yes / No — Amount:
- **Are Big Objects in use in this org?**
- **Are Attachments or ContentDocuments the primary file pattern?**
- **Known retention requirements for high-volume objects?**

---

## 3. Reclamation Opportunities

Assess each opportunity and estimate the storage freed.

| Action | Object / Target | Estimated Records | Estimated Storage Freed | Risk | Priority |
|---|---|---|---|---|---|
| Empty Recycle Bin | Recycle Bin | | | Low | |
| Delete orphaned ContentDocuments | ContentDocument | | | Low | |
| Delete old activity records | Task / Event | | | Medium | |
| Archive to Big Object | Custom object | | | Medium | |
| Migrate Attachments to ContentDocument | Attachment | | | High | |
| Other | | | | | |

---

## 4. Approach

Which pattern from SKILL.md applies?

- [ ] Storage Usage Triage After Alert
- [ ] Preventing Duplicate File Storage via ContentDocumentLink
- [ ] Other (describe):

**Specific actions planned:**

1.
2.
3.

---

## 5. Orphaned ContentDocument Audit

Run this query in Developer Console or Workbench before any file cleanup:

```soql
SELECT Id, Title, ContentSize, FileType, CreatedDate
FROM ContentDocument
WHERE Id NOT IN (SELECT ContentDocumentId FROM ContentDocumentLink)
ORDER BY ContentSize DESC
LIMIT 200
```

**Results:**
- Total orphans found:
- Total storage held by orphans:
- Action taken:

---

## 6. Monitoring Setup

**Limits API check:**

```bash
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
  https://{INSTANCE}.salesforce.com/services/data/v62.0/limits/ \
  | python3 -c "import json,sys; d=json.load(sys.stdin); ds=d['DataStorageMB']; fs=d['FileStorageMB']; print(f'Data: {ds[\"Remaining\"]}/{ds[\"Max\"]} MB remaining ({100*ds[\"Remaining\"]//ds[\"Max\"]}%)'); print(f'File: {fs[\"Remaining\"]}/{fs[\"Max\"]} MB remaining ({100*fs[\"Remaining\"]//fs[\"Max\"]}%)')"
```

**Alert thresholds configured?**
- [ ] Alert when data storage remaining < 25%
- [ ] Alert when file storage remaining < 25%
- [ ] Salesforce built-in alerts (75%, 90%, 100%) verified as reaching correct recipients

---

## 7. Review Checklist

- [ ] Setup > Storage Usage reviewed and per-object breakdown captured
- [ ] Recycle Bin storage checked and emptied if significant
- [ ] Orphaned ContentDocuments queried and deleted or confirmed none exist
- [ ] Attachment vs ContentDocument decision documented for any new file feature
- [ ] Limits API monitoring confirmed or set up (alert threshold ≤25% remaining)
- [ ] Big Object suitability assessed for any high-volume append-only objects
- [ ] No Rich Text Area fields storing embedded base64 images directly in field content
- [ ] Post-action storage snapshot taken to confirm reclamation

---

## 8. Notes

Record any deviations from the standard pattern and why:
