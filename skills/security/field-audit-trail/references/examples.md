# Examples — Field Audit Trail

## Example 1: Financial Services Firm — FINRA 7-Year Field Audit Trail for Opportunity Fields

**Context:** A wealth management firm uses Salesforce to manage client opportunities and AUM (assets under management) records. FINRA Rule 17a-4 requires broker-dealers to preserve records of securities orders and account data for 6–7 years. The compliance team needs a verifiable audit trail showing which advisor changed an Opportunity's `Amount`, `StageName`, `CloseDate`, and any custom fields storing account category data — retained for 7 years (84 months).

**Problem:** Standard Field History Tracking only retains history for 18 months. After 18 months, the records roll off and cannot be retrieved. The firm cannot demonstrate a complete audit trail to FINRA examiners for periods older than 18 months, creating a regulatory compliance gap.

**Solution:**

Step 1 — Confirm Shield is active and enable FAT on Opportunity:

```
Setup > Field Audit Trail > New Policy
Object: Opportunity
Fields: Amount, StageName, CloseDate, AUM_Category__c, Advisory_Team__c
Retention Period: 84 months (7 years)
```

Step 2 — Ensure Field History Tracking is also enabled on the same fields:

```
Setup > Object Manager > Opportunity > Fields & Relationships > Set History Tracking
Enable: Amount, StageName, CloseDate, AUM_Category__c, Advisory_Team__c
```

Step 3 — After migration window (allow 3–5 business days), validate archived data via SOQL:

```soql
SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = 'Opportunity'
  AND CreatedDate >= 2022-01-01T00:00:00Z
  AND CreatedDate <= 2022-12-31T23:59:59Z
ORDER BY CreatedDate ASC
LIMIT 500
```

Step 4 — For audit delivery, export results via Data Loader or Workbench (SOQL export). `FieldHistoryArchive` is not reportable in Report Builder.

**Why it works:** FAT extends retention of the same field change data that Field History Tracking captures, moving it from the standard `OpportunityHistory` sObject (18-month window) to `FieldHistoryArchive` (84-month window). The SOQL query gives the compliance team a timestamped, user-attributed record of every value change across the 7-year window, which satisfies FINRA's record retention requirements.

---

## Example 2: Healthcare Organization — HIPAA PHI Field Audit Trail on Contact

**Context:** A healthcare organization stores Protected Health Information (PHI) on the Contact object using custom fields (`PHI_Status__c`, `Treatment_Program__c`, `Insurance_Plan__c`). HIPAA requires covered entities to retain records of who accessed or changed PHI for at least 6 years from creation or last effective date.

**Problem:** Field History Tracking is enabled but the org only captures changes for the past 18 months. During a HIPAA audit, the compliance officer is asked to produce a log of all changes to `Treatment_Program__c` for a specific patient over the past 5 years. The standard history records are incomplete — records older than 18 months have rolled off.

**Solution:**

Step 1 — Enable FAT on Contact with a 72-month (6-year) retention policy:

```
Setup > Field Audit Trail > New Policy
Object: Contact
Fields: PHI_Status__c, Treatment_Program__c, Insurance_Plan__c, Patient_Category__c
Retention Period: 72 months (6 years)
```

Step 2 — Query archived data for a specific patient record (scoped by ParentId for performance):

```soql
SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = 'Contact'
  AND ParentId = '003XXXXXXXXXXXX'
ORDER BY CreatedDate ASC
```

Step 3 — For bulk extraction across all PHI contacts in a date range, anchor on CreatedDate:

```soql
SELECT ParentId, FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE SobjectType = 'Contact'
  AND FieldHistoryType = 'Treatment_Program__c'
  AND CreatedDate >= 2019-01-01T00:00:00Z
ORDER BY CreatedDate ASC
LIMIT 50000
```

Step 4 — Export via Apex batch or Data Loader for offline delivery to auditors. Combine with `ContactHistory` query for complete timeline:

```apex
// Combine recent + archived history for a full timeline
List<ContactHistory> recent = [
    SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
    FROM ContactHistory
    WHERE ContactId = :contactId
    AND Field IN ('PHI_Status__c', 'Treatment_Program__c')
    ORDER BY CreatedDate ASC
];

List<FieldHistoryArchive> archived = [
    SELECT FieldHistoryType, OldValue, NewValue, CreatedById, CreatedDate
    FROM FieldHistoryArchive
    WHERE SobjectType = 'Contact'
      AND ParentId = :contactId
      AND FieldHistoryType IN ('Treatment_Program__c', 'PHI_Status__c')
    ORDER BY CreatedDate ASC
];

// Merge and deduplicate in caller — overlap possible during migration window
```

**Why it works:** Anchoring on `ParentId` keeps the `FieldHistoryArchive` query efficient. The 72-month retention policy satisfies HIPAA's 6-year minimum. Combining `ContactHistory` (recent) with `FieldHistoryArchive` (archived) gives the compliance officer a complete, gap-free timeline across the required period.

---

## Anti-Pattern: Enabling FAT Without Enabling Field History Tracking on the Same Fields

**What practitioners do:** Administrators activate FAT in Setup > Field Audit Trail and configure a retention policy, but do not verify that Field History Tracking is also enabled for the same fields. They assume FAT is a replacement for Field History Tracking.

**What goes wrong:** No data flows into `FieldHistoryArchive`. FAT policies govern retention and archival of data that Field History Tracking captures — FAT does not independently capture field changes. If Field History Tracking is off for a field, there is nothing for FAT to archive. The org passes the FAT configuration check but has zero compliance coverage for those fields.

**Correct approach:** Always verify that Field History Tracking is active on the same fields you configure in FAT. In Setup > Object Manager > [Object] > Fields & Relationships > Set History Tracking, confirm the checkbox is enabled for each FAT-covered field. Run the `check_field_audit_trail.py` script against the org's metadata to detect this mismatch before deploying.
