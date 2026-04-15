# Industries Data Migration — Work Template

Use this template when executing a migration into Salesforce Insurance, Energy and Utilities Cloud, or Communications Cloud. Complete every section before any load job starts.

---

## Scope

**Skill:** `industries-data-migration`

**Target Industries cloud:** [ ] Insurance  [ ] Energy and Utilities  [ ] Communications

**Request summary:** (fill in what the user asked for)

**Objects in scope:**
- [ ] Account / PersonAccount
- [ ] (Insurance) InsurancePolicy
- [ ] (Insurance) InsurancePolicyParticipant
- [ ] (Insurance) InsurancePolicyAsset
- [ ] (Insurance) InsurancePolicyCoverage
- [ ] (Insurance) InsurancePolicyTransaction
- [ ] (Insurance) BillingStatement
- [ ] (E&U) Premise
- [ ] (E&U) ServicePoint
- [ ] (E&U) ServiceAccount
- [ ] Other: ___________________

---

## Context Gathered

- **Org type (sandbox / production):**
- **Target org API version:**
- **Data volume estimate (rows per object):**
- **Cutover window (date / duration):**
- **ETL tool:** [ ] Bulk API 2.0 (direct)  [ ] Data Loader  [ ] MuleSoft  [ ] Other: ___

---

## External ID Field Inventory

Create all fields below in the target org before any load begins.

| Object | External ID Field API Name | Type | Unique? | Created? |
|---|---|---|---|---|
| Account | `Account_External_ID__c` | Text(36) | Yes | [ ] |
| InsurancePolicy | `Policy_External_ID__c` | Text(36) | Yes | [ ] |
| InsurancePolicyAsset | `Asset_External_ID__c` | Text(36) | Yes | [ ] |
| InsurancePolicyCoverage | `Coverage_External_ID__c` | Text(36) | Yes | [ ] |
| InsurancePolicyTransaction | `Transaction_External_ID__c` | Text(36) | Yes | [ ] |
| Premise | `Premise_External_ID__c` | Text(36) | Yes | [ ] |
| ServicePoint | `ServicePoint_External_ID__c` | Text(36) | Yes | [ ] |
| ServiceAccount | `ServiceAccount_External_ID__c` | Text(36) | Yes | [ ] |

*(Delete rows for objects not in scope. Add rows for any additional objects.)*

---

## Automation Bypass Specification

| Object | Rule / Trigger / Flow Name | Bypass Method | Restoration Step | Done? |
|---|---|---|---|---|
| InsurancePolicy | (list validation rules referencing Status) | Add `Migration_Bypass__c = true` condition | Update `Migration_Bypass__c = false` post-load | [ ] |
| BillingStatement | (list rules referencing policy status) | Same bypass flag approach | Same restoration | [ ] |
| (add rows as needed) | | | | |

---

## Load Sequence and Gate Confirmation Log

Fill in after each job completes. **Do not start the next tier until the current tier shows 0 error rows.**

### Insurance Load Sequence

| Tier | Object | Job ID | Total Rows | Success | Errors | Gate Confirmed? |
|---|---|---|---|---|---|---|
| 1 | Account | | | | | [ ] |
| 2 | InsurancePolicy | | | | | [ ] |
| 3a | InsurancePolicyParticipant | | | | | [ ] |
| 3b | InsurancePolicyAsset | | | | | [ ] |
| 4 | InsurancePolicyCoverage | | | | | [ ] |
| 5a | InsurancePolicyTransaction | | | | | [ ] |
| 5b | BillingStatement | | | | | [ ] |

### E&U Load Sequence

| Tier | Object | Job ID | Total Rows | Success | Errors | Gate Confirmed? |
|---|---|---|---|---|---|---|
| 1 | Account | | | | | [ ] |
| 2 | Premise | | | | | [ ] |
| 3 | ServicePoint | | | | | [ ] |
| 4 | ServiceAccount | | | | | [ ] |

---

## Post-Load Steps

- [ ] Clear all `Migration_Bypass__c = true` values (run update job)
- [ ] Re-enable any suppressed Apex triggers or flows
- [ ] Confirm automation restoration: create one test record manually and verify all triggers fire
- [ ] Run post-load validation queries (see below)

---

## Post-Load Validation Queries

```sql
-- Record count verification (run for each object in scope)
SELECT COUNT() FROM InsurancePolicy
SELECT COUNT() FROM InsurancePolicyCoverage
SELECT COUNT() FROM Premise
SELECT COUNT() FROM ServicePoint

-- Orphan check: coverages without a valid policy
SELECT Id, InsurancePolicyId FROM InsurancePolicyCoverage WHERE InsurancePolicyId = null

-- Orphan check: service points without a valid premise
SELECT Id, PremiseId FROM ServicePoint WHERE PremiseId = null

-- Spot-check: confirm child counts for sample policies
SELECT InsurancePolicyId, COUNT(Id) coverage_count
FROM InsurancePolicyCoverage
GROUP BY InsurancePolicyId
LIMIT 10
```

---

## Approach Notes

*(Which pattern from SKILL.md applies? Any deviations from the standard pattern and why.)*

---

## Rollback Plan

*(If a tier fails with errors that cannot be resolved within the cutover window, document the delete order and approach here before load begins.)*

- Object delete order (reverse of load order):
  1. BillingStatement / InsurancePolicyTransaction
  2. InsurancePolicyCoverage
  3. InsurancePolicyAsset / InsurancePolicyParticipant
  4. InsurancePolicy
  5. Account (only if Account was loaded in this migration)

- Delete method: Bulk API 2.0 hard delete job using the Salesforce IDs from the load job result files
