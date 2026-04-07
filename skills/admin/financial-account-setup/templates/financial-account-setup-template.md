# Financial Account Setup — Work Template

Use this template when configuring FSC financial accounts, account types, holdings, goals, roles, or household rollup behavior.

## Scope

**Skill:** `financial-account-setup`

**Request summary:** (fill in the specific configuration request — e.g., "Configure brokerage and retirement account types for FSC org, including household rollup for joint accounts")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before proceeding:

- **FSC packaging model:** [ ] Managed-package (FinServ__ namespace)  [ ] Core FSC (no namespace, Winter '23+)
  - Confirmed by: (e.g., Setup > Installed Packages, or object API name check)
- **Account types in scope:**
  - [ ] Retirement (401k, IRA, Roth IRA, etc.)
  - [ ] Brokerage (individual, joint, trust)
  - [ ] Deposit (checking, savings, money market, CD)
  - [ ] Insurance (whole life, annuity)
  - [ ] Education savings (529, Coverdell)
  - [ ] Other: _______________
- **Held-away accounts in scope:** [ ] Yes  [ ] No
- **Household model in use:** [ ] Individual (Person Account only)  [ ] Household  [ ] Both
- **Cross-household joint owner rollup required:** [ ] Yes (custom rollup needed)  [ ] No (native rollup sufficient)
- **FinancialHolding (securities positions) in scope:** [ ] Yes  [ ] No
- **FinancialGoal tracking in scope:** [ ] Yes  [ ] No
- **Existing FinancialAccountType picklist values:** (list existing values — do not delete any in use)

---

## Namespace Reference

Use this section to record the correct API names for this specific org:

| Object / Field | Managed-Package API Name | Core FSC API Name | This Org Uses |
|---|---|---|---|
| Financial Account object | FinServ__FinancialAccount__c | FinancialAccount | |
| Balance field | FinServ__Balance__c | Balance | |
| Primary Owner field | FinServ__PrimaryOwner__c | PrimaryOwnerId | |
| Account Type field | FinServ__FinancialAccountType__c | FinancialAccountType | |
| Account Number field | FinServ__FinancialAccountNumber__c | FinancialAccountNumber | |
| Financial Account Role object | FinServ__FinancialAccountRole__c | FinancialAccountRole | |
| Role field on Role object | FinServ__Role__c | Role | |
| Financial Holding object | FinServ__FinancialHolding__c | FinancialHolding | |
| Financial Goal object | FinServ__FinancialGoal__c | FinancialGoal | |
| Primary Group (Household) field | FinServ__PrimaryGroup__c | PrimaryGroup | |

---

## Account Type and Record Type Matrix

Document the mapping before creating record types:

| FinancialAccountType Value | Record Type Name | Page Layout | Required Fields | Hidden Fields |
|---|---|---|---|---|
| (e.g., Individual Brokerage) | Brokerage Account | Brokerage Layout | Symbol, Quantity | RMD Age, Contribution Limit |
| (e.g., Traditional IRA) | Retirement Account | Retirement Layout | Beneficiary, Contribution Limit | N/A |
| (e.g., Checking) | Deposit Account | Deposit Layout | Routing Number | Holdings Section |

---

## Financial Account Role Configuration

| Role Value | Required? | Notes |
|---|---|---|
| Primary Owner | Yes — mandatory for rollup | Exactly one per account for rollup to work |
| Joint Owner | As needed | Cross-household visibility requires custom rollup |
| Beneficiary | As needed | Custom percentage field required if allocation % needed |
| Power of Attorney | As needed | Usually read-only in FSC display |
| Custodian | As needed | For custodial accounts (e.g., UTMA/UGMA) |

---

## Rollup Behavior Confirmation

- [ ] Tested in sandbox: same-household joint owner sees account in household balance rollup
- [ ] Tested in sandbox: cross-household joint owner does NOT see account in their household rollup
- [ ] Cross-household rollup workaround required and implemented: [ ] Yes  [ ] N/A
  - If yes, custom field used: `_______________`
  - Flow or Apex class name: `_______________`
- [ ] FSC rollup batch triggered after test data load and results verified

---

## Held-Away Account Configuration (if in scope)

- [ ] Held-away indicator field identified: `FinServ__HeldAway__c` or custom field `_______________`
- [ ] Validation rule created to prevent advisor edits to balance on held-away records
- [ ] Permission set created for data operations staff who may edit held-away balances: `_______________`
- [ ] Separate record type created for held-away accounts: [ ] Yes  [ ] No (using validation rule only)
- [ ] Data load job documented for periodic balance refresh: `_______________`

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Brokerage Account with Holdings and Roles (standard originated account setup)
- [ ] Pattern 2: Held-Away Account Configuration
- [ ] Custom: describe deviation: _______________

---

## Pre-Deployment Checklist

- [ ] All FinancialAccountType picklist values agreed with stakeholders; no values in use being deleted
- [ ] Record types and page layouts match the account type matrix documented above
- [ ] FinancialAccountRole Role picklist includes: Primary Owner, Joint Owner, Beneficiary, and any firm-specific values
- [ ] All API names in Apex, Flows, and metadata use the correct namespace for this org (see Namespace Reference table)
- [ ] Validation rules tested for held-away accounts (if in scope)
- [ ] Rollup batch behavior tested and documented for same-household and cross-household scenarios
- [ ] `scripts/check_financial_account.py` run against exported metadata — no blocking WARNs
- [ ] Page layouts reviewed by an advisor/end-user representative for usability

---

## Notes

Record any deviations from the standard pattern and why:

_____________________________________________

---

## Related Resources

- `skills/admin/financial-account-setup/references/gotchas.md` — non-obvious platform behaviors
- `skills/admin/financial-account-setup/references/examples.md` — worked examples for brokerage and joint account rollup
- `skills/admin/financial-account-setup/references/well-architected.md` — WAF pillar mapping and official sources
- FSC Financial Accounts Help: https://help.salesforce.com/s/articleView?id=sf.fsc_financial_accounts.htm
- FSC Financial Account Roles Help: https://help.salesforce.com/s/articleView?id=sf.fsc_financial_account_roles.htm
