# NPSP API and Integration — Work Template

Use this template when working on tasks in this area.

---

## Scope

**Skill:** `npsp-api-and-integration`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before writing integration code.

**Integration source system:** _______________
(payment processor, event platform, peer-to-peer fundraising tool, wealth screening tool, other)

**Gift data structure in source system:**

| Gift Type | Present? | Notes |
|---|---|---|
| One-time online gift | [ ] Yes [ ] No | |
| Recurring gift / installment | [ ] Yes [ ] No | ERD integration required |
| Matching gift | [ ] Yes [ ] No | Soft credit via DataImport Contact2 fields |
| In-kind / non-cash | [ ] Yes [ ] No | Requires custom DataImport mapping or post-processing |
| Tribute / memorial | [ ] Yes [ ] No | |

**NPSP Enhanced Recurring Donations (ERD) enabled:**
- [ ] Yes — `npe03__Recurring_Donation__c` uses ERD schema; RD2_ApiService available
- [ ] No — legacy recurring donations in use (different object model — confirm before coding)

**NPSP Advanced Mapping enabled (for custom field mapping):**
- [ ] Yes — custom Opportunity, Contact, and Payment fields can be mapped through BDI
- [ ] No — only standard BDI DataImport fields available; custom fields require post-processing
- [ ] Unknown — must check NPSP Settings > Advanced Mapping before designing field mappings

**Salesforce Elevate in use:**
- [ ] Yes — payment processor IDs must be preserved through BDI for Elevate linkage
- [ ] No

**Wealth screening tool (if applicable):**
- Tool name: _______________
- [ ] AppExchange managed package available — use package, NOT custom HTTP callout
- [ ] No package available — custom integration required

---

## BDI DataImport Field Mapping

Map each source field to the corresponding `npsp__DataImport__c` staging field.

**Donor identity fields:**

| Source Field | DataImport__c Field | Notes |
|---|---|---|
| First name | npsp__Contact1_Firstname__c | Used for donor match |
| Last name | npsp__Contact1_Lastname__c | Used for donor match |
| Email | npsp__Contact1_Email__c | Primary match key |
| Donor ID (external) | npsp__Contact1_Personal_Email__c or custom via Advanced Mapping | |
| Org/company name | npsp__Account1_Name__c | For organizational donors |

**Gift fields:**

| Source Field | DataImport__c Field | Notes |
|---|---|---|
| Gift amount | npsp__Donation_Amount__c | Required |
| Gift date | npsp__Donation_Date__c | Required |
| Stage | npsp__Donation_Stage__c | Use 'Closed Won' for completed gifts |
| Campaign | npsp__Donation_Campaign_Name__c | Match by campaign name |
| Payment method | npsp__Payment_Method__c | Check/Credit Card/Online/Other |
| External transaction ID | npsp__Payment_Check_Reference_Number__c or custom | Elevate or processor reference |

**Fund allocation (GAU) fields:**

| Source Field | DataImport__c Field | Notes |
|---|---|---|
| Fund 1 name | npsp__GAU_Allocation_1_General_Accounting_Unit__c | Match by GAU name |
| Fund 1 amount | npsp__GAU_Allocation_1_Amount__c | Or use percentage |
| Fund 1 % | npsp__GAU_Allocation_1_Percent__c | Alternative to amount |
| Fund 2 name | npsp__GAU_Allocation_2_General_Accounting_Unit__c | |
| Fund 2 amount | npsp__GAU_Allocation_2_Amount__c | |

**Soft credit fields (matching gifts, in-kind donors):**

| Source Field | DataImport__c Field | Notes |
|---|---|---|
| Soft credit first name | npsp__Contact2_Firstname__c | Soft credit recipient |
| Soft credit last name | npsp__Contact2_Lastname__c | |
| Soft credit email | npsp__Contact2_Email__c | |
| Soft credit role | npsp__Opportunity_Contact_Role_1_Role__c | e.g., Matching Donor |

**Fields requiring Advanced Mapping (list custom fields not covered above):**

| Custom Field Need | Target Object | Notes |
|---|---|---|
| | | |

---

## Integration Architecture

**Processing pattern selected:**

- [ ] Real-time BDI processing — insert DataImport records and call `BDI_DataImport_API.processDataImportRecords()` synchronously (small batch, <200 records)
- [ ] Async batch processing — insert DataImport records; schedule NPSP Data Import batch job to process at configured frequency
- [ ] Chunked async — insert in batches of 50–200 records; enqueue processing via Queueable Apex

**Error handling design:**

| Failure Scenario | Detection Method | Remediation Action |
|---|---|---|
| DataImport Status = Failed | Query `npsp__FailureInformation__c` post-process | Route to error queue / notification |
| Donor match ambiguous (multiple contacts) | npsp__Status__c = 'Review Needed' | Assign to gift processor for manual review |
| GAU name not found | npsp__FailureInformation__c contains 'GAU' | Map to default fund; alert gift processor |
| Elevate payment ID not linking | Check Elevate integration settings | Confirm Elevate Connected App config |

**CRLP recalculation strategy (for bulk imports):**

- [ ] Automatic (NPSP scheduled CRLP batch handles it — acceptable latency for reporting)
- [ ] Manual trigger via NPSP CRLP batch after import completes
- [ ] Not applicable (small, incremental imports)

---

## ERD / Recurring Donation Integration (if applicable)

**Use of RD2 APIs:**

| Use Case | API Method | Notes |
|---|---|---|
| Display projected payment schedule to donor | `npsp.RD2_ApiService.getSchedules(rdId)` | Returns active schedule as JSON |
| Display upcoming installments | `npsp.RD2_ApiService.getInstallments(rdId, n)` | Returns projections, NOT persisted Opps |
| Create or update recurring donation | Standard DML on `npe03__Recurring_Donation__c` | Use NPSP field API names |

**Critical reminder:** `getInstallments()` returns calculated projections — NOT actual Opportunity records. Future installment Opportunities are created by the NPSP scheduled batch, not by the API call.

---

## Review Checklist

- [ ] No direct Opportunity or npe01__OppPayment__c inserts — all gifts routed through npsp__DataImport__c
- [ ] BDI Advanced Mapping enabled if custom fields are needed
- [ ] GAU allocation fields populated on DataImport records where required by grant or fund structure
- [ ] Soft credit recipient fields populated for matching gifts and in-kind donors
- [ ] Error handling checks `npsp__FailureInformation__c` on failed DataImport records
- [ ] CRLP batch recalculation triggered after large bulk imports
- [ ] ERD Installments API not confused with persisted Opportunity records
- [ ] Wealth screening uses AppExchange managed package, not custom HTTP callout (if tool has a package)

---

## Notes

(Record deviations from the standard pattern and justification)
