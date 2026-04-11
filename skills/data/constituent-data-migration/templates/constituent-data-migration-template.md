# Constituent Data Migration — Work Template

Use this template when planning or executing a constituent data migration into an NPSP org.

## Scope

**Skill:** `constituent-data-migration`

**Request summary:** (describe what the user asked for — e.g., "migrate 8,000 contacts and their household data from Excel into NPSP")

---

## Pre-Migration Context

Answer these questions before touching any data:

- **NPSP version installed:** _________________________
- **Household Account model confirmed active (not Person Accounts):** [ ] Yes / [ ] No
- **Approximate record count:** _______ contacts / _______ households / _______ donations
- **Source system / file format:** _________________________
- **Contact Matching Rule currently configured:** (e.g., First Name + Last Name + Email)
- **Known duplicate risk in source data:** [ ] High / [ ] Medium / [ ] Low
- **Source data includes household pairs (two contacts per household):** [ ] Yes / [ ] No
- **Source data includes historical donations:** [ ] Yes / [ ] No / [ ] Some rows

---

## Staging CSV Column Mapping

Map source fields to `npsp__DataImport__c` field API names:

| Source Column | npsp__DataImport__c Field | Notes |
|---|---|---|
| First Name (primary) | `npsp__Contact1_Firstname__c` | Required |
| Last Name (primary) | `npsp__Contact1_Lastname__c` | Required |
| Email (primary) | `npsp__Contact1_Personal_Email__c` | Used for matching |
| First Name (secondary) | `npsp__Contact2_Firstname__c` | Only if household pair |
| Last Name (secondary) | `npsp__Contact2_Lastname__c` | Only if household pair |
| Email (secondary) | `npsp__Contact2_Personal_Email__c` | Used for matching |
| Street Address | `npsp__HH_Street__c` | Shared household address |
| City | `npsp__HH_City__c` | |
| State | `npsp__HH_State__c` | |
| Zip Code | `npsp__HH_Zip__c` | |
| Donation Amount | `npsp__Donation_Amount__c` | If including giving history |
| Donation Date | `npsp__Donation_Date__c` | If including giving history |
| Donation Stage | `npsp__Donation_Stage__c` | Required if donation included |
| Existing HH Account ID | `npsp__HH_Account_Id__c` | Only for adding to existing household |

---

## Pilot Batch Plan

- **Pilot batch size:** _______ rows (recommend 50–100)
- **Selection criteria for pilot rows:** (e.g., random sample, highest-risk records, all household pairs)
- **Pilot batch file name:** _________________________
- **Expected outcomes to verify after pilot:**
  - [ ] No unexpected duplicate Contacts created
  - [ ] Household Accounts created with correct names
  - [ ] Both contacts in a pair linked to same Household Account
  - [ ] Address records created and linked to both contacts
  - [ ] Donation Opportunities created and linked to Household Account (if applicable)
  - [ ] Rollup fields populated on Household Accounts (total giving, last gift date)

---

## Migration Run Plan

- **Total rows to import:** _______
- **Chunk size per run:** _______ rows (reduce if CPU limit errors occur; start at 50)
- **Number of chunks:** _______
- **Estimated batch processing time per chunk:** _______ minutes
- **Batch size setting in NPSP Settings > Data Import:** _______ (default 50)

| Chunk | Row Range | File Name | Status | Notes |
|---|---|---|---|---|
| 1 | 1 – _____ | | Pending | |
| 2 | _____ – _____ | | Pending | |
| 3 | _____ – _____ | | Pending | |

---

## Post-Import Validation Checklist

Run through these after each chunk and after the full migration:

- [ ] `npsp__DataImport__c` rows for this chunk show `npsp__Status__c = Imported`
- [ ] No rows stuck in `npsp__Status__c = Failed` (investigate and remediate)
- [ ] Spot-check 10 Contact records — correct household, address, and relationship records present
- [ ] Spot-check 5 Household Account records — rollup fields (total giving, last gift date) populated
- [ ] No unexpected duplicate Contact records found (run duplicate jobs or SOQL spot-check)
- [ ] No orphaned one-contact Household Accounts created for contacts that should be paired
- [ ] Processed staging rows cleaned up (deleted or archived) before next chunk run

---

## Error Log

Track failed rows and remediation:

| Staging Row ID | Error Message | Root Cause | Remediation | Status |
|---|---|---|---|---|
| | | | | |

---

## Approach Notes

Which pattern from SKILL.md applies?

- [ ] Bulk constituent load from CSV via NPSP Data Importer UI (one-time migration)
- [ ] Programmatic ETL via BDI_DataImport Apex batch (automated pipeline)

Deviations from standard pattern and reasons:

_________________________

---

## Sign-Off

- [ ] All rows imported or accounted for (imported / intentionally excluded / error-logged)
- [ ] Post-import data quality validation completed
- [ ] Processed `npsp__DataImport__c` staging rows cleaned up
- [ ] Migration results documented and shared with org owner
