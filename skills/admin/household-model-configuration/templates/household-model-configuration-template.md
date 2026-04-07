# Household Model Configuration — Work Template

Use this template when configuring or troubleshooting the FSC household data model.

## Scope

**Skill:** `household-model-configuration`

**Request summary:** (fill in the specific configuration request — e.g., "Set up household structure for 50 client families migrated from legacy CRM" or "Troubleshoot: household rollup totals not updating for Insurance Policy records")

---

## Context Gathered

Answer these before making any changes:

- **FSC packaging model:** Managed-package (`FinServ__` namespace) / Core FSC (no namespace, GA since Winter '23) / Unknown
- **Org provisioning date (approximate):** _______________
- **Person Accounts enabled:** Yes / No
- **NPSP installed:** Yes / No — If Yes, STOP and resolve before proceeding (FSC and NPSP household models are incompatible)
- **Object types requiring household rollups:** FinancialAccount / Opportunity / Case / InsurancePolicy / Other: _______________
- **Rollups__c picklist values present (list all):** _______________
- **Known failure mode or trigger for this work:** _______________

---

## Rollups__c Picklist Audit

| Object Type | Picklist Value Present? | Action Required |
|---|---|---|
| FinancialAccount | Yes / No | Add if missing |
| Opportunity | Yes / No | Add if missing |
| Case | Yes / No | Add if missing |
| InsurancePolicy | Yes / No | Add if missing |
| (Custom object if applicable) | Yes / No | Add if missing |

**Where to add missing values:** Setup > Object Manager > Account > Fields & Relationships > Rollups__c > Manage Values > New

---

## Household Account Records

| Household Name | Record Type | ACR Members Count | Rollup Fields Verified? |
|---|---|---|---|
| (example) Smith Family | Household | 2 | Yes |
| | | | |

---

## ACR Membership Checklist

For each household member ACR record, verify:

- [ ] `AccountId` = Household Account Id
- [ ] `ContactId` = Person Account's `PersonContactId` (NOT `Account.Id`)
- [ ] `FinServ__PrimaryGroup__c` = `true` if this household is the member's primary group; `false` for secondary group memberships
- [ ] `FinServ__Primary__c` = `true` for exactly ONE member per household; `false` for all others
- [ ] `FinServ__IncludeInGroup__c` = `true` for members whose assets should roll up to this household

**Primary member designation per household:**

| Household | Primary Member (Person Account Name) | ACR Primary__c = true confirmed? |
|---|---|---|
| | | |

---

## Rollup Validation

**Sandbox validation:**

- [ ] Created test financial account for a household member
- [ ] Confirmed household `FinServ__TotalAssets__c` (or Core FSC equivalent) updated after save
- [ ] Confirmed member with `FinServ__IncludeInGroup__c = false` does NOT contribute to household rollup
- [ ] Confirmed member belonging to two households: primary household shows correct rollup; secondary household shows only shared assets

**Batch rollup job:**

- [ ] Ran `FinServ.RollupBatchJob` (or Core FSC equivalent) in sandbox
- [ ] Confirmed rollup totals match expected values after batch completion
- [ ] Batch job scheduled in production: Cron expression: _______________ (recommended: `0 0 2 * * ?` for 2 AM nightly)

---

## Configuration Applied

| Setting | Value | Notes |
|---|---|---|
| Namespace | FinServ__ / None | |
| Rollups__c values added | | List any newly added values |
| Batch job schedule | | Cron expression |
| ACR records created/updated | | Count |

---

## Deviations From Standard Pattern

(Record any deviations from the standard SKILL.md workflow and the business reason)

---

## Handoff Notes

(Record anything the next admin or developer needs to know about this household configuration — e.g., which households use non-standard `IncludeInGroup__c = false` memberships and why, any custom rollup logic added, or known gaps to address in a future sprint)
