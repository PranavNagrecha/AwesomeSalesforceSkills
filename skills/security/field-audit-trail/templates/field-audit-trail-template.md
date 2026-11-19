# Field Audit Trail — Work Template

Use this template when configuring, auditing, or querying Shield Field Audit Trail for an org.

---

## Scope

**Skill:** `field-audit-trail`

**Request summary:** (fill in what the user or compliance team asked for)

**Driving compliance requirement:** (FINRA / HIPAA / GDPR / SOX / Internal Policy / Other)

**Required retention period:** _____ years (archived data is kept until you delete it; no maximum is documented)

---

## Pre-Flight Context

Answer these before doing any FAT work:

| Question | Answer |
|---|---|
| Is Salesforce Shield licensed for this org? | Yes / No / Confirm |
| Has Salesforce enabled Field Audit Trail for the org (enabled through your Salesforce representative)? | Yes / No |
| Which objects are in scope? | (list) |
| Which fields on each object require long-term tracking? | (list per object) |
| Is Field History Tracking already enabled on these fields? | Yes / Partial / No |
| Current HistoryRetentionPolicy (if any)? | (archiveAfterMonths / archiveRetentionYears, or "none set"; default is archive after 18 months in production) |
| Target retention period (compliance-driven)? | (years) |
| Who will query archived data — admin, Apex, external tool? | (method) |

---

## Object and Field Coverage Matrix

For each in-scope object, complete this table:

| Object | Fields to Track (FAT) | Fields Already in FHT? | FAT Policy Status | Required Retention (years) | Compliant? |
|---|---|---|---|---|---|
| Account | | | | | |
| Contact | | | | | |
| Opportunity | | | | | |
| Case | | | | | |
| Lead | | | | | |
| [Custom Object] | | | | | |

**Notes:**
- FHT = Field History Tracking (must be enabled independently — FAT does not replace it)
- FAT supports up to 200 fields per object
- Standard Field History Tracking still limited to 20 fields per object

---

## Retention Policy Decisions

| Object | HistoryRetentionPolicy (Metadata API) | archiveAfterMonths (1-18) / archiveRetentionYears | Regulation/Requirement Driving This | Policy Set By | Date Set |
|---|---|---|---|---|---|
| | | | | | |

---

## Querying FieldHistoryArchive — Query Templates

**Query 1: All archived changes for a specific record**
```soql
SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue, CreatedDate
FROM FieldHistoryArchive
WHERE FieldHistoryType = '[ObjectAPIName]'
  AND ParentId = '[RecordId]'
ORDER BY CreatedDate ASC
```

**Query 2: All archived changes for a specific field across a date range**
```soql
SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue, CreatedDate
FROM FieldHistoryArchive
WHERE FieldHistoryType = '[ObjectAPIName]'
  AND Field = '[FieldAPIName]'
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
    SELECT FieldHistoryType, Field, OldValue, NewValue, CreatedDate
    FROM FieldHistoryArchive
    WHERE FieldHistoryType = '[ObjectAPIName]'
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
- [ ] FAT enabled and HistoryRetentionPolicy deployed (Metadata API) on all in-scope objects
- [ ] Field count per object confirmed <= 200
- [ ] Field History Tracking verified active on all FAT-covered fields
- [ ] Explicit retention policy set per object (not relying on defaults)
- [ ] archiveRetentionYears matches or exceeds compliance minimum; manual deletion scheduled no earlier
- [ ] Validation query run against FieldHistoryArchive (allow 3–5 days after enabling)
- [ ] Async migration window communicated to stakeholders
- [ ] SOQL-only access limitation communicated — Report Builder not supported
- [ ] Audit extraction workflow documented (Data Loader / Apex Batch / Workbench)
- [ ] Compliance evidence matrix completed and signed off

---

## Compliance Evidence Map

| Regulation | Article / Rule | Retention Requirement | Objects Covered | Fields Covered | FAT Policy Active? |
|---|---|---|---|---|---|
| FINRA Rule 17a-4 | Securities order records | 6–7 years | Opportunity | Amount, StageName, CloseDate | |
| HIPAA | PHI access logs | 6 years | Contact | PHI_Status__c, etc. | |
| GDPR | Personal data changes | Varies (typically 6–7 years) | Contact, Lead | Name, Email, etc. | |
| SOX | Financial record changes | 7 years | Account, Opportunity | Revenue fields | |
| Internal Policy | | | | | |

---

## Notes

Record any deviations from standard patterns, exceptions granted by compliance, or open items:

-
-
