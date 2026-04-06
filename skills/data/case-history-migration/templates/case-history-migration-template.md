# Case History Migration — Work Template

Use this template when migrating historical Case records, emails, comments, and attachments into Salesforce Service Cloud.

## Scope

**Skill:** `case-history-migration`

**Request summary:** (fill in what the user asked for)

**Source system:** (Zendesk / ServiceNow / Dynamics / other legacy CRM)

**Migration scope:**
- [ ] Case records only
- [ ] Cases + CaseComments
- [ ] Cases + EmailMessages (inbound/outbound emails)
- [ ] EmailMessageRelation (Contact/User linkage for emails)
- [ ] Files/attachments (ContentVersion + ContentDocumentLink)
- [ ] Historical audit trail (CaseHistory approximation via Tasks)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Email-to-Case enabled:** Yes / No
- **External ID field on Case:** (e.g. `Legacy_Case_Id__c`)
- **Source user ID mapping to Salesforce UserId:** Complete / Partial / Not done
- **Estimated case count:** ___
- **Estimated email count:** ___
- **Estimated file/attachment count:** ___
- **ContentDocumentLink REST API load window estimate:** ___ hours (based on file count ÷ API rate limit)
- **Known constraints:** (e.g. validation rules to bypass, sharing rules, record type assignments)
- **CaseHistory approximation approach:** Task records / FeedItem / Custom object / Not required

---

## Load Sequence Decision

| Step | Object | Load Method | Row Count Estimate | Notes |
|---|---|---|---|---|
| 1 | Case | Bulk API 2.0 upsert | | External ID: Legacy_Case_Id__c |
| 2 | CaseComment | Bulk API 2.0 insert | | IsPublished flag: |
| 3 | EmailMessage | Bulk API 2.0 insert | | Status: inbound='1', outbound='2' (NEVER '3') |
| 4 | EmailMessageRelation | Bulk API 2.0 insert | | RelationObjectType: Contact / User |
| 5 | ContentVersion | Bulk API 2.0 insert | | VersionData base64-encoded |
| 6 | ContentDocumentLink | REST API only | | Query ContentDocumentId first |
| 7 | Task (CaseHistory approx.) | Bulk API 2.0 insert | | WhatId = Case cross-ref |

---

## EmailMessage Status Mapping

| Source System Status | Salesforce Status Value | Label | Notes |
|---|---|---|---|
| (fill in source status) | 1 | Read | Inbound/received emails |
| (fill in source status) | 2 | Replied | Outbound/sent emails |
| (fill in source status) | 0 | New | Draft or unknown status |
| **NEVER** | **3** | **Sent** | **Permanently locks record — do not use in migrations** |

---

## ContentDocumentLink REST API Load Plan

- **Total files to link:** ___
- **Parallel REST threads:** ___
- **Estimated time at N threads:** ___ hours
- **API rate limit headroom:** (check org API limits in Setup > API Usage)
- **Error handling approach:** (retry logic / manual retry log / skip with alert)

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] All Cases loaded and row counts verified before child objects
- [ ] EmailMessage Status confirmed — no Status='3' in load set
- [ ] EmailMessageRelation rows loaded for all To/CC/BCC addressees mapping to Contacts or Users
- [ ] CaseHistory insert NOT attempted directly
- [ ] ContentVersion loaded via Bulk API 2.0
- [ ] ContentDocumentId queried from ContentVersion after insert
- [ ] ContentDocumentLink loaded via REST API only
- [ ] ContentDocumentLink row count per case matches source attachment count
- [ ] CaseComment IsPublished flag set correctly
- [ ] Post-migration validation: comment counts, email counts, attachment linkage spot-checked

---

## Post-Migration Validation Queries

```sql
-- Case count verification
SELECT COUNT(Id) FROM Case WHERE Legacy_Case_Id__c != null

-- CaseComment count per case sample
SELECT ParentId, COUNT(Id) commentCount
FROM CaseComment
WHERE ParentId IN (SELECT Id FROM Case WHERE Legacy_Case_Id__c != null)
GROUP BY ParentId
ORDER BY commentCount DESC
LIMIT 20

-- EmailMessage count per case sample
SELECT ParentId, COUNT(Id) emailCount
FROM EmailMessage
WHERE ParentId IN (SELECT Id FROM Case WHERE Legacy_Case_Id__c != null)
GROUP BY ParentId
ORDER BY emailCount DESC
LIMIT 20

-- Check for any locked EmailMessage (Status='3') — should be zero for migrations
SELECT COUNT(Id) FROM EmailMessage WHERE Status = '3'
AND ParentId IN (SELECT Id FROM Case WHERE Legacy_Case_Id__c != null)

-- ContentDocumentLink count per case sample
SELECT LinkedEntityId, COUNT(Id) fileCount
FROM ContentDocumentLink
WHERE LinkedEntityId IN (SELECT Id FROM Case WHERE Legacy_Case_Id__c != null)
GROUP BY LinkedEntityId
ORDER BY fileCount DESC
LIMIT 20

-- Task records approximating CaseHistory
SELECT WhatId, COUNT(Id) auditTaskCount
FROM Task
WHERE Subject LIKE 'Historical Change:%'
AND WhatId IN (SELECT Id FROM Case WHERE Legacy_Case_Id__c != null)
GROUP BY WhatId
ORDER BY auditTaskCount DESC
LIMIT 20
```

---

## Notes

Record any deviations from the standard pattern and why.

- (e.g. "Skipped EmailMessageRelation — source system had no contact-email mapping data")
- (e.g. "Used FeedItem instead of Task for CaseHistory approximation — business uses Chatter")
- (e.g. "Files loaded directly via FirstPublishLocationId on ContentVersion — no CDL step needed for simple case attachment")
