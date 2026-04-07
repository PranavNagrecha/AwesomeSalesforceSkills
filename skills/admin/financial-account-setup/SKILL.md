---
name: financial-account-setup
description: "Use when configuring Financial Services Cloud (FSC) financial accounts — including account types, FinancialHolding positions, FinancialGoal records, FinancialAccountRole assignments (Primary Owner, Joint Owner, Beneficiary), and household balance rollup behavior. Triggers: configure financial accounts in FSC, set up financial account roles Financial Services Cloud, FSC household balance rollup not working, add holdings to financial account, FinancialAccountType picklist setup, FSC brokerage or retirement account configuration. NOT for standard Account objects, NOT for Salesforce standard financial-services industry templates unrelated to FinancialAccount, NOT for Accounting Subledger or Revenue Cloud."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "configure financial accounts in FSC"
  - "set up financial account roles Financial Services Cloud"
  - "FSC household balance rollup not working for joint account owner"
  - "add holdings or positions to a financial account in FSC"
  - "FinancialAccountType picklist values and record types"
  - "difference between held-away and originated accounts in Financial Services Cloud"
tags:
  - financial-services-cloud
  - fsc
  - financial-accounts
  - rollup
  - financial-account-roles
  - holdings
inputs:
  - FSC org type (managed-package org with FinServ__ namespace, or Core FSC Winter '23+ without namespace)
  - List of account types to configure (retirement, brokerage, deposit, insurance, education savings, etc.)
  - Whether held-away accounts (externally held, manually entered) are in scope
  - Household model in use (individual, household, or both)
  - "Role types required: Primary Owner, Joint Owner, Beneficiary, Power of Attorney, etc."
  - Whether rollup to household is required for joint-owner households
outputs:
  - Financial account type configuration plan (FinancialAccountType picklist values, record types, page layouts)
  - FinancialAccountRole setup guidance for Primary Owner, Joint Owner, and Beneficiary roles
  - Household balance rollup behavior explanation and workaround for cross-household joint owners
  - Held-away vs originated account permission and field design recommendation
  - Financial holdings (FinancialHolding) and FinancialGoal record setup guidance
  - Validation checklist for FSC financial account configuration
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Financial Account Setup

Use this skill when configuring Financial Services Cloud (FSC) financial accounts and their related data model — account types, holdings, financial goals, account roles, and household rollup behavior. This skill covers the end-to-end setup of the `FinancialAccount` object (API name: `FinServ__FinancialAccount__c` in managed-package orgs, `FinancialAccount` in Core FSC Winter '23+ orgs) and all directly dependent objects.

This skill does NOT cover standard Salesforce Account objects, Revenue Cloud, or Accounting Subledger. When you see "financial account" in a non-FSC context, do not activate this skill.

---

## Before Starting

- **Confirm the FSC packaging model.** Managed-package FSC orgs use the `FinServ__` namespace (e.g., `FinServ__FinancialAccount__c`). Core FSC orgs (General Availability since Winter '23) use standard API names without the namespace (e.g., `FinancialAccount`). Mixing the two naming conventions in code or metadata will cause deployment failures.
- **Identify which household model is in use.** FSC supports individual (Person Account), household (Account with type = Household), and both. Rollup behavior is driven by the Primary Owner's household — if joint owners belong to a different household, balances will not roll up to them by default.
- **Clarify held-away vs originated accounts.** Held-away accounts represent assets held at another institution, entered manually or imported. Originated accounts are accounts the advising firm services directly. These require different permission designs, field layouts, and data governance rules.
- **Determine account types.** The `FinancialAccountType` picklist drives record type selection, page layout rendering, and validation rules. Agreeing on required types (401k, IRA, Roth IRA, brokerage, checking, savings, 529, whole life) before configuration avoids mid-project rework.

---

## Core Concepts

### FinancialAccount Object and API Name Variance

The `FinancialAccount` object is the central object for all FSC financial account data. In managed-package (ISV-packaged) FSC orgs — the most common deployment prior to Winter '23 — the object is a custom object with the namespace prefix: `FinServ__FinancialAccount__c`. All related fields also carry the `FinServ__` prefix (e.g., `FinServ__Balance__c`, `FinServ__PrimaryOwner__c`).

In Core FSC orgs (the re-architected industry cloud available since Winter '23), `FinancialAccount` is a standard platform object with no namespace prefix. All field API names drop the `FinServ__` prefix. Code or metadata written for one model will not deploy to the other without modification. Always establish the packaging model before writing any Apex, SOQL, Flow, or metadata that references FinancialAccount fields.

### FinancialAccountType Picklist and Record Types

The `FinancialAccountType` picklist (or the equivalent standard field in Core FSC) categorizes accounts into major types: retirement (401k, 403b, Traditional IRA, Roth IRA, SEP IRA, SIMPLE IRA), brokerage (individual, joint, trust), deposit (checking, savings, money market, CD), insurance (whole life, annuity), and education savings (529 plan, Coverdell ESA).

Record types map to account types and control which page layouts and fields are visible. A brokerage account layout should show holdings-related fields; a retirement account layout should surface beneficiary designation fields; a deposit account layout may show linked debit card and overdraft fields. Mismatching the `FinancialAccountType` picklist value with the wrong record type produces confusing layouts and can break validation rules that test account type.

### FinancialAccountRole and Household Rollup Logic

`FinancialAccountRole` (API: `FinServ__FinancialAccountRole__c` in managed-package) links a person (Contact or Person Account) to a financial account in a specific capacity: Primary Owner, Joint Owner, Beneficiary, Power of Attorney, Custodian, or Trustee. FSC uses the **Primary Owner** role to determine which household the account balance rolls up to.

The rollup mechanism works as follows: FSC reads the Primary Owner's `FinServ__PrimaryGroup__c` (the household) and writes the aggregate balance to the household's rollup fields. Joint owners in the same household also see the aggregated balance because they share the household record. However, if a Joint Owner belongs to a different household, their household will not receive the rollup — only the Primary Owner's household does. This is by design in the managed-package rollup engine, and it means that cross-household joint account visibility requires a custom rollup, scheduled Apex, or a Flow-based workaround.

### FinancialHolding and FinancialGoal

`FinancialHolding` (API: `FinServ__FinancialHolding__c`) represents an individual security position or holding within a financial account — a specific number of shares of a stock or mutual fund at a given market value. Brokerage and retirement accounts typically have many FinancialHolding child records. Holdings are read-only for display in FSC's Account Summary component; they are updated via data integration from a custodian or portfolio management system, not via the UI.

`FinancialGoal` (API: `FinServ__FinancialGoal__c`) represents a client's financial objective (retirement at 65, college fund by 2034, emergency fund). Goals are linked to financial accounts and to the Contact/Person Account. A financial goal does not drive automation by itself — it is a data capture object used for advisor planning and reporting.

---

## Common Patterns

### Pattern 1: Brokerage Account with Holdings and Roles

**When to use:** Setting up a brokerage or investment account that holds securities and has a primary owner and one or more joint owners.

**How it works:**
1. Create the `FinancialAccount` record with `FinancialAccountType` set to the appropriate brokerage value (e.g., `Individual Brokerage` or `Joint Brokerage`).
2. Assign the correct record type so the brokerage page layout renders with holdings-related fields and hides retirement-only fields (beneficiary designation, RMD age, contribution limit).
3. Create a `FinancialAccountRole` record linking the primary owner Contact/Person Account with `Role = Primary Owner`. This role triggers household rollup.
4. For each joint owner, create an additional `FinancialAccountRole` record with `Role = Joint Owner`.
5. Load `FinancialHolding` records as child records of the `FinancialAccount`, with `Symbol`, `Quantity`, `CurrentPrice`, and `MarketValue` populated from the custodian data feed.
6. Verify the primary owner's household rollup fields update to reflect the new account balance (allow the FSC rollup batch to run, or trigger it manually in a sandbox via the FSC Admin app).

**Why not the alternative:** Creating accounts without `FinancialAccountRole` records leaves the account unassigned to a person — it will not appear in the household balance rollup and will not surface in the FSC client summary. Do not rely on the `FinServ__PrimaryOwner__c` lookup field alone; that field is a direct lookup for display, while the role record drives rollup and the relationship data model.

### Pattern 2: Configuring Held-Away Accounts

**When to use:** The firm manages client relationships where the client holds assets at another custodian (held-away assets), and advisors need visibility without the firm being the custodian.

**How it works:**
1. Create the `FinancialAccount` with the `FinServ__SourceSystemId__c` field populated with the external system identifier for reconciliation.
2. Set a custom field or use `FinServ__HeldAway__c` (if the field is present in the managed package version) to flag the account as externally held.
3. Define a separate permission set or profile configuration that restricts who can create and edit held-away account records versus originated accounts — typically advisors can view but not modify held-away balances entered by data operations staff.
4. Implement a data import job (Data Loader, MuleSoft, or an ETL pipeline) to update balance and holding data on a scheduled basis, since held-away accounts receive no real-time feed from the firm's own systems.
5. Ensure page layouts for held-away accounts hide fields that are only relevant for originated accounts (account number linked to internal systems, linked product, origination date).

**Why not the alternative:** Treating held-away and originated accounts identically in one record type creates permission confusion — advisors may inadvertently edit balances they should not modify, and compliance audit trails become unreliable. Separate record types or at minimum a controlling picklist field with validation rules prevents this.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Joint owner is in the same household as primary owner | Standard FSC rollup configuration — no custom work needed | FSC rolls up to the primary owner's household; joint owner shares that household and sees the aggregated balance |
| Joint owner is in a different household | Custom rollup via Flow or scheduled Apex to write balance to the second household | FSC managed-package rollup does not cross household boundaries for Joint Owner roles |
| Org is on managed-package FSC (pre-Winter '23 upgrade path) | Use `FinServ__` namespace in all API names, SOQL, and metadata | Core FSC API names break in managed-package orgs; namespace mismatch causes runtime errors |
| Org has migrated to Core FSC (Winter '23+) | Drop `FinServ__` prefix from all references | Standard object names — no namespace prefix |
| Account has multiple beneficiaries with percentage allocations | Use one `FinancialAccountRole` record per beneficiary with a custom percentage field | FSC does not ship a native beneficiary percentage field; add a custom field to `FinancialAccountRole` |
| Held-away accounts require balance updates nightly | Scheduled data import job (Data Loader or integration platform) targeting `FinancialAccount` and `FinancialHolding` | Held-away accounts have no real-time custodian feed in standard FSC |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on financial account configuration:

1. **Confirm the FSC packaging model** — query `SELECT NamespacePrefix FROM PackageSubscriber WHERE NamespacePrefix = 'FinServ'` in the org (or check Setup > Installed Packages) to determine whether the org uses the managed package or Core FSC. This determines all subsequent API names.
2. **Audit existing FinancialAccountType picklist values** — navigate to Setup > Object Manager > FinancialAccount (or FinServ__FinancialAccount__c) > Fields & Relationships > FinancialAccountType and document existing values. Do not delete picklist values that are referenced by existing records.
3. **Design the record type and page layout matrix** — for each account type (retirement, brokerage, deposit, insurance, education savings), define which record type applies, which fields are required, and which sections are visible. Document this matrix before creating record types.
4. **Configure FinancialAccountRole values** — confirm the Role picklist includes all required values (Primary Owner, Joint Owner, Beneficiary, Custodian, Power of Attorney, Trustee). Add custom values if the firm uses non-standard relationship types.
5. **Test rollup behavior in a sandbox** — create test accounts with Primary Owner and Joint Owner roles in the same household and in different households. Run the FSC rollup batch (FSC Admin app > Run Rollup) and verify household balance fields update correctly. Document the cross-household gap for stakeholders.
6. **Define the held-away account permission model** — if held-away accounts are in scope, create a separate permission set restricting edit access to held-away account records. Apply validation rules to enforce read-only behavior for non-privileged users.
7. **Validate and deploy** — run the `scripts/check_financial_account.py` checker against your exported metadata. Confirm no references use the wrong namespace prefix, all required role values exist, and page layouts match the record type matrix.

---

## Review Checklist

Run through these before marking financial account configuration complete:

- [ ] FSC packaging model confirmed (managed-package with `FinServ__` namespace vs Core FSC without namespace); all API names in code, Flows, and metadata use the correct form
- [ ] `FinancialAccountType` picklist values match all required account types; no orphaned values without a corresponding record type
- [ ] Record types and page layouts configured per account type matrix; brokerage layouts show holding fields, retirement layouts show beneficiary fields
- [ ] `FinancialAccountRole` picklist includes Primary Owner, Joint Owner, Beneficiary, and any firm-specific role values
- [ ] At least one `FinancialAccountRole` with `Role = Primary Owner` exists for every financial account that should appear in household rollup
- [ ] Household rollup tested in sandbox: same-household joint owners see aggregated balance; cross-household joint owners do not (and workaround is documented if required)
- [ ] Held-away account permission model defined and tested — advisors cannot accidentally edit externally-sourced balances
- [ ] `FinancialHolding` load process tested end-to-end for brokerage and retirement accounts (if holdings are in scope)
- [ ] `FinancialGoal` record types and required fields configured (if goal tracking is in scope)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Primary Owner rollup boundary** — FSC's managed-package rollup engine writes aggregate balances only to the Primary Owner's household. A Joint Owner who belongs to a different household will not see the account balance in their household summary. This surprises advisors who expect all named account owners to see the same rollup figure. Document this limitation to stakeholders before go-live and implement a custom rollup if cross-household visibility is a requirement.

2. **Namespace mismatch breaks everything silently** — Managed-package orgs require `FinServ__FinancialAccount__c`; Core FSC orgs require `FinancialAccount`. A Flow or Apex class using the wrong name will fail at runtime with a cryptic "invalid field" or "object not found" error. There is no compile-time warning in the UI for incorrect object references in Flows.

3. **FinancialAccountType picklist deletion causes data corruption** — Deleting a picklist value that is in use on existing records does not blank out those records — it leaves the field in an invalid state where the value is stored but not selectable. Existing records show the old value in read mode but cannot be edited until the field is cleared. Always replace, not delete, picklist values that have existing record usage.

4. **Held-away vs originated account permissions diverge over time** — Without explicit permission enforcement (validation rules, permission sets), advisors gain edit access to held-away account balance fields as their profiles are broadened for other purposes. Compliance auditors treat unauthorized balance edits as a data integrity violation. Implement a validation rule on `FinancialAccount` that prevents non-privileged users from modifying the balance on held-away records from day one.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Account type and record type matrix | Mapping of FinancialAccountType picklist values to record types, page layouts, and required fields |
| FinancialAccountRole configuration plan | Role picklist values, guidance on one-Primary-Owner-per-account constraint, and cross-household rollup workaround documentation |
| Held-away account permission design | Validation rule logic, permission set configuration, and data load job specification for externally held accounts |
| Household rollup test results | Sandbox test evidence confirming rollup behavior for same-household and cross-household joint owner scenarios |
| `scripts/check_financial_account.py` output | Automated metadata validation report flagging namespace errors, missing role values, and layout mismatches |

---

## Related Skills

- `admin/household-model-configuration` — configure the FSC household data model, Primary Group assignment, and household rollup batch settings
- `admin/fsc-data-model` — broader FSC data model overview covering all FSC objects and their relationships
- `integration/fhir-integration-patterns` — if financial data arrives from an external system via API integration
- `architect/fsc-architecture-patterns` — FSC solution architecture decisions including managed-package vs Core FSC migration planning
