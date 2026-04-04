# Field Audit Trail — Work Template

Use this template when configuring, auditing, or querying Shield Field Audit Trail for an org.

---

## Scope

**Skill:** `field-audit-trail`

**Request summary:** (fill in what the user or compliance team asked for)

**Driving compliance requirement:** (FINRA / HIPAA / GDPR / SOX / Internal Policy / Other)

**Required retention period:** _____ months (_____ years)

---

## Pre-Flight Context

Answer these before doing any FAT work:

| Question | Answer |
|---|---|
| Is Salesforce Shield licensed for this org? | Yes / No / Confirm |
| Is Field Audit Trail visible in Setup? | Yes / No |
| Which objects are in scope? | (list) |
| Which fields on each object require long-term tracking? | (list per object) |
| Is Field History Tracking already enabled on these fields? | Yes / Partial / No |
| Current FAT retention policy (if any)? | (months or "none set") |
| Target retention period (compliance-driven)? | (months) |
| Who will query archived data — admin, Apex, external tool? | (method) |

---

## Object and Field Coverage Matrix

For each in-scope object, complete this table:

| Object | Fields to Track (FAT) | Fields Already in FHT? | FAT Policy Status | Required Retention (months) | Compliant? |
|---|---|---|---|---|---|
| Account | | | | | |
| Contact | | | | | |
| Opportunity | | | | | |
| Case | | | | | |
| Lead | | | | | |
| [Custom Object] | | | | | |

**Notes:**
- FHT = Field History Tracking (must be enabled independently — FAT does not replace it)
- FAT supports up to 60 fields per object
- Standard Field History Tracking still limited to 20 fields per object

---

## Retention Policy Decisions

| Object | Policy Name (in Setup) | Retention Period Set (months) | Regulation/Requirement Driving This | Policy Set By | Date Set |
|---|---|---|---|---|---|
| | | | | | |

---

## Querying FieldHistoryArchive — Query Templates

**Query 1: All archived changes for a specific record**
```soql
SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = '[ObjectAPIName]'
  AND ParentId = '[RecordId]'
ORDER BY CreatedDate ASC
```

**Query 2: All archived changes for a specific field across a date range**
```soql
SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = '[ObjectAPIName]'
  AND FieldHistoryType = '[FieldAPIName]'
  AND CreatedDate >= [StartDate]T00:00:00Z
  AND CreatedDate <= [EndDate]T23:59:59Z
ORDER BY CreatedDate ASC
LIMIT 50000
```

**Query 3: Combined recent + archived history for a full timeline (Apex)**
```apex
Id recordId = '[RecordId]';
DateTime startDate = DateTime.newInstance([Year], [Month], [Day]);

// Recent — standard history sObject
List<[Object]History> recent = [
    SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
    FROM [Object]History
    WHERE [Object]Id = :recordId
    ORDER BY CreatedDate ASC
];

// Archived — FAT
List<FieldHistoryArchive> archived = [
    SELECT FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
    FROM FieldHistoryArchive
    WHERE SobjectType = '[ObjectAPIName]'
      AND ParentId = :recordId
      AND CreatedDate >= :startDate
    ORDER BY CreatedDate ASC
];
// Merge and deduplicate in caller
```

---

## Approach

Which pattern from SKILL.md applies? (check one)

- [ ] **Enabling FAT on high-sensitivity fields for regulatory compliance** — standard activation path
- [ ] **Querying FieldHistoryArchive for audit evidence** — extraction for auditors
- [ ] **Combining standard history and FieldHistoryArchive** — full timeline view

Why this pattern: ___________

---

## Checklist

Copy and track as you complete each step:

- [ ] Shield license confirmed active
- [ ] Target objects and fields confirmed with compliance/legal
- [ ] FAT enabled on all in-scope objects (Setup > Field Audit Trail)
- [ ] Field count per object confirmed <= 60
- [ ] Field History Tracking verified active on all FAT-covered fields
- [ ] Explicit retention policy set per object (not relying on defaults)
- [ ] Retention period matches or exceeds compliance minimum
- [ ] Validation query run against FieldHistoryArchive (allow 3–5 days after enabling)
- [ ] Async migration window communicated to stakeholders
- [ ] SOQL-only access limitation communicated — Report Builder not supported
- [ ] Audit extraction workflow documented (Data Loader / Apex Batch / Workbench)
- [ ] Compliance evidence matrix completed and signed off

---

## Compliance Evidence Map

| Regulation | Article / Rule | Retention Requirement | Objects Covered | Fields Covered | FAT Policy Active? |
|---|---|---|---|---|---|
| FINRA Rule 17a-4 | Securities order records | 6–7 years (72–84 months) | Opportunity | Amount, StageName, CloseDate | |
| HIPAA | PHI access logs | 6 years (72 months) | Contact | PHI_Status__c, etc. | |
| GDPR | Personal data changes | Varies (typically 6–7 years) | Contact, Lead | Name, Email, etc. | |
| SOX | Financial record changes | 7 years (84 months) | Account, Opportunity | Revenue fields | |
| Internal Policy | | | | | |

---

## Notes

Record any deviations from standard patterns, exceptions granted by compliance, or open items:

-
-
