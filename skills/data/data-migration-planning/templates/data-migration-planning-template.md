# Data Migration Planning — Migration Plan Template

Use this template to document all migration decisions before any load jobs are submitted. Complete every section and review with all stakeholders before cutover.

---

## 1. Migration Overview

**Project name:** _______________________________________________

**Target Salesforce org:** `[ ] Sandbox` `[ ] Production`  Org ID: _______________

**Source system:** _______________________________________________

**Migration type:** `[ ] One-time cutover` `[ ] Incremental / delta` `[ ] Parallel run`

**Planned migration window:** Start: _______________ End: _______________

**Migration owner (named individual):** _______________________________________________

**Technical lead:** _______________________________________________

**Stakeholder sign-off required from:** _______________________________________________

---

## 2. Source System Summary

| Source System Field | Value |
|---|---|
| System name | |
| System type (CRM / ERP / spreadsheet / other) | |
| Export format (CSV / API / database dump) | |
| Total estimated record volume (all objects) | |
| Source system natural key / primary key format | |
| Data quality notes (known blanks, duplicates, encoding issues) | |

---

## 3. Object Migration Sequence

List every object in the order it must be loaded. Parents must appear before children. Confirm all dependency relationships before finalizing this sequence.

| # | Object API Name | Record Count (approx.) | Depends On (parent objects) | Load Operation | Notes |
|---|---|---|---|---|---|
| 1 | | | None | Upsert | |
| 2 | | | | Upsert | |
| 3 | | | | Upsert | |
| 4 | | | | Upsert | |
| 5 | | | | Upsert | |
| 6 | | | | Upsert | |
| 7 | | | | Upsert | |
| 8 | | | | Upsert | |

Add rows as needed. Never use Insert as the load operation in production — always use Upsert.

**Circular self-references (if any):**

| Object | Field | Resolution (two-pass: first load without ref, second pass updates ref) |
|---|---|---|
| | | |

---

## 4. External ID Mapping

For each object being migrated, document the external ID field that links source records to Salesforce records.

| Object API Name | External ID Field API Name | Field Type | Source System Column | Case-Sensitive? | Notes |
|---|---|---|---|---|---|
| | Legacy_CRM_Id__c | Text(20) | source_id | Yes — normalize to UPPERCASE | |
| | Legacy_CRM_Id__c | Text(20) | source_id | Yes | |
| | | | | | |

**External ID field design confirmation:**
- [ ] All external ID fields are created in the target Salesforce org
- [ ] All external ID fields are marked as External ID AND Unique
- [ ] No external ID fields are formula fields
- [ ] External ID values in all load CSVs use consistent casing
- [ ] External ID limit (25 per object) not exceeded on any object

**Migration Batch ID field:**
- [ ] `Migration_Batch_Id__c` field (Text) exists on every migrated object
- Batch ID format to use: `{OBJECT_PREFIX}-{YYYY-MM-DD}-{NNN}` (e.g., `ACCT-2026-04-04-001`)

---

## 5. Tool Selection

**Primary migration tool:** `[ ] Data Loader (Bulk API mode)` `[ ] Bulk API 2.0 (direct)` `[ ] MuleSoft` `[ ] Informatica` `[ ] Jitterbit` `[ ] Other: ___`

**Rationale for tool selection:** _______________________________________________

**Bulk API batch size:** _______________ records per batch (max 10,000; default 10,000)

**Expected throughput:** _______________ records/hour (estimate based on object complexity)

**Estimated total load time:** _______________ hours

**Tool configuration verified in sandbox:** `[ ] Yes` `[ ] No — must verify before production run`

---

## 6. Validation Rule Bypass Approach

List every active validation rule on each migrated object. Document the bypass method for each.

| Object | Validation Rule Name | Active? | Bypass Method | Bypass Implemented? | Re-enabled After Migration? |
|---|---|---|---|---|---|
| | | Yes | Custom Permission | [ ] | [ ] |
| | | Yes | Custom Permission | [ ] | [ ] |
| | | Yes | Temporary Deactivation | [ ] | [ ] |

**Custom Permission details (if used):**
- Custom Permission API name: _______________________________________________
- Permission Set name: _______________________________________________
- Migration user assigned to Permission Set: _______________________________________________
- Permission Set removal after migration: Named owner: _______________

**Temporary deactivation details (if used):**
- Rules to deactivate: _______________________________________________
- Deactivation window: _______________________________________________
- Named owner responsible for re-enabling: _______________________________________________
- Re-enable confirmed after migration: `[ ] Yes` `[ ] Not yet`

---

## 7. Trigger and Flow Bypass Approach

| Object | Trigger / Flow Name | Type | Bypass Method | Bypass Implemented? | Bypass Cleared After? |
|---|---|---|---|---|---|
| | | Trigger | Custom Setting flag | [ ] | [ ] |
| | | Flow | Custom Setting flag | [ ] | [ ] |
| | | Trigger | Custom Setting flag | [ ] | [ ] |

**Custom Setting bypass flag details:**
- Custom Setting object: _______________________________________________
- Checkbox field: _______________________________________________
- Flag set to `true` before migration by: _______________
- Flag cleared to `false` after migration by: _______________
- Post-clear automation verified by: _______________

---

## 8. Record Owner Assignment Plan

| Source System Owner Field | Salesforce User (Active) | Action If User Inactive |
|---|---|---|
| | | Re-assign to placeholder: ___ |
| | | Re-assign to placeholder: ___ |

**Owner validation steps:**
- [ ] Exported active Salesforce user list: `SELECT Id, Name, IsActive, UserType FROM User WHERE IsActive = true`
- [ ] Cross-referenced all source owner values against active Salesforce users
- [ ] Placeholder owner defined for inactive/missing users: _______________
- [ ] Post-migration owner correction plan documented: _______________

---

## 9. Rollback Strategy

**Rollback trigger condition:** _______________________________________________
(e.g., error rate > 5%, critical object fails entirely, data integrity check fails)

**Rollback decision owner (named individual):** _______________________________________________

**Rollback procedure (reverse load sequence order):**

| Step | Object | Action | Command / Tool | Named Owner |
|---|---|---|---|---|
| 1 | | Delete by Migration_Batch_Id__c | Bulk API delete | |
| 2 | | Delete by Migration_Batch_Id__c | Bulk API delete | |
| 3 | | Delete by Migration_Batch_Id__c | Bulk API delete | |

**Delete operation type:** `[ ] Soft delete (recycle bin)` `[ ] Hard delete (requires Bulk API Hard Delete permission)`

**Rollback tested in sandbox:** `[ ] Yes` `[ ] No — must test before production cutover`

**Maximum rollback window (time from cutover start to rollback decision):** _______________ hours

---

## 10. Post-Migration Validation Checklist

Complete this section after all load jobs have finished. Do not sign off on the migration until all items pass.

### 10a. Record Count Reconciliation

| Object | Source Count | Salesforce Count (SOQL) | Match? | Notes |
|---|---|---|---|---|
| | | `SELECT COUNT(Id) FROM Account WHERE Legacy_CRM_Id__c != null` | [ ] | |
| | | | [ ] | |
| | | | [ ] | |

Acceptable variance: ___% (document any expected variance, e.g., records excluded by filter)

### 10b. Field-Level Spot Checks

Sample at least 1% of records (or minimum 50 records) per object. Compare source system values to Salesforce field values.

| Object | Sample Size | Fields Checked | Pass? | Issues Found |
|---|---|---|---|---|
| | | Name, Phone, Email, OwnerId | [ ] | |
| | | | [ ] | |

### 10c. Relationship Integrity Checks

Run these SOQL queries. Every result should return 0 records. Non-zero results indicate orphan or broken relationship records.

```sql
-- Contacts with no Account (when Account is expected for all contacts)
SELECT COUNT(Id) FROM Contact
WHERE AccountId = null AND Legacy_CRM_Id__c != null

-- Opportunities with no Account
SELECT COUNT(Id) FROM Opportunity
WHERE AccountId = null AND Legacy_CRM_Id__c != null

-- Opportunity Line Items with no Opportunity (should never occur for master-detail)
SELECT COUNT(Id) FROM OpportunityLineItem
WHERE OpportunityId = null

-- Cases with no Account (if Account is required for all cases)
SELECT COUNT(Id) FROM Case
WHERE AccountId = null AND Legacy_CRM_Id__c != null
```

Add object-specific integrity queries for any custom relationships in this migration.

| Query | Expected Result | Actual Result | Pass? |
|---|---|---|---|
| Contacts with no Account | 0 | | [ ] |
| Opportunities with no Account | 0 | | [ ] |
| OLIs with no Opportunity | 0 | | [ ] |

### 10d. Automation Re-enablement Verification

- [ ] Custom Permission bypass removed from migration user
- [ ] All temporarily deactivated validation rules re-enabled
- [ ] Custom Setting bypass flag cleared (`Migration_In_Progress__c = false`)
- [ ] Test record save performed on each migrated object — expected automation fired correctly

### 10e. Final Sign-Off

| Sign-off Item | Responsible | Signed Off | Date |
|---|---|---|---|
| Record count reconciliation complete | | [ ] | |
| Field-level spot checks pass | | [ ] | |
| Relationship integrity checks pass (all 0) | | [ ] | |
| Automation re-enabled and verified | | [ ] | |
| Rollback window expired or rollback decision made | | [ ] | |
| Migration declared complete | | [ ] | |

---

## 11. Notes and Deviations

Record any deviations from the standard migration pattern, issues encountered during execution, and decisions made during the migration window.

| Date/Time | Issue / Decision | Owner | Resolution |
|---|---|---|---|
| | | | |
| | | | |
