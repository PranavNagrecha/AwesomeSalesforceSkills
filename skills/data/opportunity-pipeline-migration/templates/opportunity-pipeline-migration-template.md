# Opportunity Pipeline Migration — Work Template

Use this template when planning or executing an Opportunity pipeline migration into Salesforce.

---

## Scope

**Skill:** `opportunity-pipeline-migration`

**Request summary:** (fill in what the user asked for)

**Migration type:** (check all that apply)
- [ ] Opportunities only (no products, no splits)
- [ ] Opportunities + Products / Line Items (OpportunityLineItem)
- [ ] Opportunities + Team Members (OpportunityTeamMember)
- [ ] Opportunities + Revenue Splits (OpportunitySplit)
- [ ] Historical stage history preservation

---

## Source System Context

- **Source CRM:** (e.g., Dynamics 365, HubSpot, Pipedrive, SAP CRM)
- **Approximate Opportunity count:**
- **Approximate OpportunityLineItem count:**
- **Average stage transitions per opportunity (for history planning):**
- **Price Book structure in source:** (single list price / multiple price tiers / contract-specific)
- **Revenue splits used in source?** Yes / No

---

## Target Org Prerequisite Checklist

Run these verifications before any load begins.

### Price Books
- [ ] Active Price Books identified: (list Name and Id)
  - Standard Price Book Id: `<QUERY: SELECT Id FROM Pricebook2 WHERE IsStandard = true>`
  - Custom Price Book Id(s): ___________________________
- [ ] Custom Price Book confirmed active: Setup > Products > Price Books

### Sales Process / Stage Validation
- [ ] All unique StageName values from source export documented:
  (paste list here)
- [ ] All source stages mapped to active target org stages:
  | Source Stage | Target StageName | Notes |
  |---|---|---|
  | | | |
- [ ] Stage mapping verified against: `SELECT StageName FROM OpportunityStage WHERE IsActive = true`

### OpportunitySplits (if applicable)
- [ ] Feature enabled: Setup > Opportunity Splits > Enabled (check)
- [ ] At least one SplitType is Active: `SELECT Id, MasterLabel, IsActive FROM OpportunitySplitType WHERE IsActive = true`
- [ ] SplitType Id captured for CSV: ___________________________

### External ID Fields
- [ ] `Legacy_Opportunity_Id__c` (Text, External ID, Unique) created on Opportunity
- [ ] `Legacy_Product_Id__c` (Text, External ID, Unique) created on Product2
- [ ] `Legacy_Account_Id__c` (Text, External ID, Unique) created on Account (if using cross-reference)

### Migration User Permissions
- [ ] Migration user has required object permissions (CRUD on all target objects)
- [ ] Validation rule bypass configured: Custom Permission `Bypass_Migration_Validation` on relevant rules
- [ ] Custom Permission permission set assigned to migration user before load

---

## Load Sequence Plan

Document the actual load sequence with file names and batch sizes.

| Step | Object | Operation | CSV File | Batch Size | Dependencies |
|---|---|---|---|---|---|
| 1 | Product2 | Upsert (Legacy_Product_Id__c) | `product2.csv` | 10,000 | None |
| 2 | PricebookEntry (Standard) | Insert | `pbe_standard.csv` | 10,000 | Product2 |
| 3 | PricebookEntry (Custom) | Insert | `pbe_custom.csv` | 10,000 | Standard PBE |
| 4 | Opportunity | Upsert (Legacy_Opportunity_Id__c) | `opportunity.csv` | 10,000 | Account, User |
| 5 | OpportunityLineItem | Insert | `oli.csv` | 10,000 | Opportunity, PBE |
| 6 | OpportunityTeamMember | Insert | `otm.csv` | 10,000 | Opportunity, User |
| 7 | OpportunitySplit | Insert | `split.csv` | 10,000 | OTM, SplitType |
| 8 | Task (stage history) | Insert | `stage_history_tasks.csv` | 10,000 | Opportunity |

---

## Stage History Approach

- [ ] **Option A: Task records** — one Task per stage transition (recommended for high volume)
  - Task Subject pattern: `Historical Stage: <StageName>`
  - Task ActivityDate: stage change date from source
  - Task Status: `Completed`
  - Task WhatId: cross-reference via `Opportunity.Legacy_Opportunity_Id__c`

- [ ] **Option B: Sequential StageName updates** — one Bulk API update wave per stage transition (produces native Stage History entries)
  - Estimated total Opportunity × transition count: ___________________________
  - Estimated number of update waves: ___________________________
  - Confirm this is within Bulk API daily limit (150M rows/24h): Yes / No

---

## CSV Column Mapping

### Opportunity CSV Columns

| Source Field | CSV Column Header | Notes |
|---|---|---|
| Source Opp ID | `Legacy_Opportunity_Id__c` | External ID for upsert |
| Account ref | `Account.Legacy_Account_Id__c` | Cross-reference |
| Stage | `StageName` | Must match active Sales Process stage |
| Amount | `Amount` | Do not set if OLIs will drive Amount |
| Close Date | `CloseDate` | Format: YYYY-MM-DD |
| Owner | `Owner.Username` | Cross-reference to User |
| Price Book | `Pricebook2Id` | Required if OLIs will be loaded |

### OpportunityLineItem CSV Columns

| Source Field | CSV Column Header | Notes |
|---|---|---|
| Opp ref | `Opportunity.Legacy_Opportunity_Id__c` | Cross-reference |
| Product ref | `PricebookEntry.Product2.Legacy_Product_Id__c` | Nested cross-reference |
| Quantity | `Quantity` | Decimal |
| Unit price | `UnitPrice` | Must match PricebookEntry price book |
| Total price | `TotalPrice` | Optional if Quantity × UnitPrice = TotalPrice |

---

## Rollback Plan

Define rollback steps in reverse load sequence order.

| Step | Object | Rollback Action | Query |
|---|---|---|---|
| 8 | Task (stage history) | Delete by Migration_Batch_Id__c | `SELECT Id FROM Task WHERE Migration_Batch_Id__c = '<batch>'` |
| 7 | OpportunitySplit | Delete by OpportunityId batch | `SELECT Id FROM OpportunitySplit WHERE Opportunity.Migration_Batch_Id__c = '<batch>'` |
| 6 | OpportunityTeamMember | Delete by OpportunityId batch | `SELECT Id FROM OpportunityTeamMember WHERE Opportunity.Migration_Batch_Id__c = '<batch>'` |
| 5 | OpportunityLineItem | Delete by OpportunityId batch | `SELECT Id FROM OpportunityLineItem WHERE Opportunity.Migration_Batch_Id__c = '<batch>'` |
| 4 | Opportunity | Delete by Migration_Batch_Id__c | `SELECT Id FROM Opportunity WHERE Migration_Batch_Id__c = '<batch>'` |
| 3 | PricebookEntry (Custom) | Delete by External ID | `SELECT Id FROM PricebookEntry WHERE Product2.Legacy_Product_Id__c IN (...)` |
| 2 | PricebookEntry (Standard) | Delete after Custom PBE removed | See above |
| 1 | Product2 | Delete by Legacy_Product_Id__c | `SELECT Id FROM Product2 WHERE Legacy_Product_Id__c IN (...)` |

---

## Post-Migration Validation Checklist

- [ ] **Opportunity count**: `SELECT COUNT() FROM Opportunity WHERE Migration_Batch_Id__c = '<batch>'` matches source export row count
- [ ] **Amount spot-check**: Sample 20 Opportunities and compare Amount to source; investigate discrepancies > 1%
- [ ] **OLI count**: `SELECT COUNT() FROM OpportunityLineItem WHERE Opportunity.Migration_Batch_Id__c = '<batch>'` matches source line item row count
- [ ] **Price Book assignment**: `SELECT COUNT() FROM Opportunity WHERE Pricebook2Id = null AND Migration_Batch_Id__c = '<batch>'` returns 0
- [ ] **Stage history**: Sample 5 Opportunities in source with known stage history; confirm corresponding Tasks or Stage History entries in Salesforce
- [ ] **Team member coverage**: `SELECT COUNT() FROM OpportunityTeamMember WHERE Opportunity.Migration_Batch_Id__c = '<batch>'` matches source
- [ ] **Split totals**: `SELECT OpportunityId, SplitTypeId, SUM(SplitPercentage) total FROM OpportunitySplit WHERE Opportunity.Migration_Batch_Id__c = '<batch>' GROUP BY OpportunityId, SplitTypeId HAVING SUM(SplitPercentage) != 100` returns 0 rows
- [ ] **Error file review**: All Bulk API error files reviewed; any failures investigated and documented

---

## Deviations and Notes

Record any deviations from the standard pattern and the reason for each.

| Deviation | Reason | Impact |
|---|---|---|
| | | |
