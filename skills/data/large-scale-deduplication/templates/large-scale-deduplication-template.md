# Large Scale Deduplication — Planning and Execution Template

Use this template when designing or executing a large-scale deduplication project in Salesforce.

---

## Scope

**Skill:** `data/large-scale-deduplication`

**Request summary:** (fill in what the user or data steward asked for)

**Target object(s):**
- [ ] Account
- [ ] Contact
- [ ] Lead
- [ ] Custom object: _______________

---

## Context Gathered

### Volume Estimate

| Metric | Value |
|---|---|
| Total records on target object | |
| Estimated duplicate record count | |
| Estimated duplicate pair count | |
| Confidence in estimate (sample-based / full scan) | |

### Survivorship Rules

Document the criteria for selecting the master record:

| Priority | Criterion | Logic |
|---|---|---|
| 1 | | e.g., Prefer record with most non-null key fields |
| 2 | | e.g., Prefer record with earliest CreatedDate |
| 3 | | e.g., Prefer record sourced from ERP (Source__c = 'ERP') |

**Survivorship rules reviewed and approved by:** _______________

### Downstream ID Dependencies

| External System | Stores Salesforce ID? | Follows REST redirect? | Action Required |
|---|---|---|---|
| | | | |
| | | | |

### Automation on Target Object

| Automation Name | Type (Flow/Trigger/WFR) | Fires On | Safe During Merge? | Bypass Method |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Approach Selected

- [ ] Batch Apex merge (under ~50K pairs, standard objects only)
- [ ] Third-party tool: DemandTools / Cloudingo / Other: _______________
- [ ] Bulk API 2.0 extraction + external matching engine
- [ ] Hybrid: external matching for identification + Batch Apex for merge

**Rationale for approach:**

---

## Execution Plan

### Phase 1: Extract and Match

- [ ] Bulk API 2.0 query job created for target object
- [ ] Export includes fields: Id, + key matching fields (Email, Phone, External\_Id, Name, etc.)
- [ ] Matching logic defined and documented
- [ ] (master\_id, losing\_id) pair list produced and reviewed
- [ ] Sample pairs manually validated for accuracy

### Phase 2: Pre-Merge Preparation

- [ ] Staging custom object or CSV loaded with pair list
- [ ] Automation bypass flags added or automation disabled
- [ ] Sandbox test run completed on a representative sample
- [ ] Production maintenance window communicated to stakeholders

### Phase 3: Merge Execution

- [ ] Batch Apex job (or third-party tool) executed in production
- [ ] Merge progress monitored via staging object Status__c counts
- [ ] Failed pairs logged and reviewed

### Phase 4: Post-Merge Validation

SOQL queries to run after the batch completes:

```sql
-- Confirm no duplicate pairs remain (spot-check by email)
SELECT Email, COUNT(Id) cnt FROM Contact
GROUP BY Email HAVING COUNT(Id) > 1 ORDER BY cnt DESC LIMIT 20

-- Confirm losing records were deleted
SELECT Id FROM Account WHERE Id IN (:losingIdList)  -- should return 0 rows

-- Confirm child record re-parenting (example: Opportunities)
SELECT COUNT() FROM Opportunity WHERE AccountId IN (:losingAccountIdList)  -- should return 0
```

- [ ] No duplicate pairs remain in spot-check queries
- [ ] Losing record IDs return zero rows
- [ ] Child record counts on master records increased as expected
- [ ] External system ID sync scheduled or completed

### Phase 5: Ongoing Prevention

- [ ] Duplicate Rules activated on target object (or existing rules verified as active)
- [ ] Scheduled Duplicate Jobs or third-party scan configured
- [ ] Data steward assigned to review Duplicate Job reports periodically

---

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them:

- [ ] Survivorship rules documented and reviewed by data steward
- [ ] Downstream ID dependencies identified and action plans documented
- [ ] Automation disabled or bypassed for the merge run
- [ ] Staging pair list loaded and validated in sandbox
- [ ] Batch job tested in sandbox before production run
- [ ] Post-merge child record re-parenting verified via SOQL
- [ ] Losing record ID redirects confirmed for integrated systems
- [ ] Ongoing duplicate prevention controls in place

---

## Notes

Record any deviations from the standard pattern and why:

---

## Outcome

| Metric | Value |
|---|---|
| Pairs submitted | |
| Pairs merged successfully | |
| Pairs failed (with reasons) | |
| Execution date | |
| Executed by | |
