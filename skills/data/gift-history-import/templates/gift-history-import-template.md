# Gift History Import — Work Template

Use this template when planning or executing an NPSP gift history import using the BDI (Batch Data Importer).

## Scope

- Total gift records to import: ___________
- Number of batches required (≤50,000 per batch): ___________
- Custom payment fields in scope: [ ] Yes  [ ] No
- GAU allocations in scope: [ ] Yes  [ ] No (max ___ splits per gift)
- Soft credits in scope: [ ] Yes  [ ] No

---

## Pre-Import Checklist

- [ ] Advanced Mapping enabled in NPSP Settings > Data Import (required if custom fields in scope)
- [ ] Custom field mappings configured in NPSP Settings > Data Import > Field Mappings
- [ ] GAU record names/IDs validated against org data
- [ ] Contact matching strategy confirmed (name+email vs. External ID)
- [ ] Source data deduplicated against existing donor records

---

## DataImport__c Column Mapping

| Source Field | DataImport__c API Name | Notes |
|---|---|---|
| Donor First Name | `npsp__Contact1_Firstname__c` | Required for Contact matching |
| Donor Last Name | `npsp__Contact1_Lastname__c` | Required for Contact matching |
| Donor Email | `npsp__Contact1_Personal_Email__c` | Used in NPSP matching rules |
| Gift Amount | `npsp__Donation_Amount__c` | |
| Gift Close Date | `npsp__Donation_Date__c` | |
| Gift Stage | `npsp__Donation_Stage__c` | e.g., Closed Won |
| Campaign | `npsp__Donation_Campaign_Name__c` | |
| Payment Method | `npsp__Payment_Method__c` | |
| Check/Reference | `npsp__Payment_Check_Reference_Number__c` | |
| GAU 1 Name | `npsp__GAU_Allocation_1_GAU__c` | |
| GAU 1 Amount | `npsp__GAU_Allocation_1_Amount__c` | Do not mix with percent in same row |
| Soft Credit Contact | `npsp__Contact2_Lastname__c` + `npsp__Contact2_Firstname__c` | |

---

## Batch Execution Plan

| Batch # | Record Range | DataImport__c Insert Date | BDI Run Date | Status |
|---|---|---|---|---|
| 1 | 1–50,000 | | | |
| 2 | 50,001–100,000 | | | |

---

## Post-Import Validation SOQL

```sql
-- Count imported Opportunities
SELECT COUNT() FROM Opportunity WHERE Name LIKE 'Gift Import%'

-- Confirm payment records created
SELECT COUNT() FROM npe01__OppPayment__c WHERE npe01__Opportunity__r.CloseDate >= LAST_YEAR

-- Confirm soft credits (OCRs) created
SELECT COUNT() FROM OpportunityContactRole WHERE Role = 'Soft Credit'

-- Confirm GAU allocations created
SELECT COUNT() FROM npsp__Allocation__c WHERE npsp__Opportunity__r.CloseDate >= LAST_YEAR

-- Check for failed DataImport rows
SELECT npsp__Status__c, npsp__FailureInformation__c FROM npsp__DataImport__c 
WHERE npsp__Status__c = 'Failed' LIMIT 200
```

---

## Notes

_Capture org-specific field names, matching rule configurations, error patterns encountered._
