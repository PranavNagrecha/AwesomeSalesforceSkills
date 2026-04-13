# Industries Communications Setup — Work Template

Use this template when working on Communications Cloud configuration tasks: org setup, EPC service catalog, order decomposition, account hierarchy, or contract lifecycle activation.

## Scope

**Skill:** `industries-communications-setup`

**Request summary:** (fill in what the user asked for)

**Setup phase in scope:**
- [ ] Initial org setup and permission sets
- [ ] EPC service catalog configuration
- [ ] Account record-type segmentation design
- [ ] Order decomposition rule configuration
- [ ] Contract lifecycle activation
- [ ] Subscriber management flow
- [ ] End-to-end validation

## Context Gathered

Record answers to the Before Starting questions:

- **Communications Cloud package installed?** (Yes / No — check Setup > Installed Packages)
- **Account model:** (Consumer B2C / Business B2B / Both)
- **EPC already partially configured?** (Yes — describe current state / No — greenfield)
- **Legacy product catalog to migrate?** (Yes — describe source / No)
- **Subscriber segment types in scope:** (Consumer / Business / Wholesale / Other)
- **Industries Order Management in scope?** (Yes / No)
- **External fulfillment or BSS system?** (Yes — describe integration / No)
- **Contract lifecycle activation required?** (Yes / No)

## Account Model Design

| RecordType DeveloperName | Purpose in This Org | Parent Account Type |
|---|---|---|
| `Billing_Account` | | (top of hierarchy) |
| `Service_Account` | | Billing Account |
| `Consumer_Account` | | (B2C only) |

**SOQL filter pattern to use in this org:**

```soql
-- Service Account example
SELECT Id, Name, ParentId
FROM Account
WHERE RecordType.DeveloperName = 'Service_Account'
```

## EPC Catalog Structure

| EPC Layer | Name | Notes |
|---|---|---|
| Catalog | | (e.g., "Consumer Catalog", "Business Catalog") |
| Product Specification | | (atomic service types) |
| Product Offering | | (market-facing offers with pricing) |
| Bundle Product Offering | | (multi-component bundles) |
| Catalog Assignment | | (links offering to catalog) |

**Bundle decomposition map** (list child items for each bundle):

| Bundle Name | Child Offering 1 | Child Offering 2 | Child Offering 3 |
|---|---|---|---|
| | | | |

## Permission Set Assignment Plan

| Permission Set | Assigned To | Assigned Before EPC Config? |
|---|---|---|
| Communications Cloud Admin | Implementing admin(s) | Yes — required before EPC |
| Communications Cloud User | End users | Yes — before order capture testing |
| OmniStudio Admin | OmniStudio configurers | If OmniStudio flows used |

## Order Decomposition Notes

**Industries Order Management decomposition rules configured:** (Yes / No / In progress)

**Test order result:** (Commercial order created — Yes/No; Technical order generated — Yes/No)

**Decomposition issue (if any):** (describe)

## Contract Lifecycle Notes

**Industries Contract Management activation action:** (configured / not configured)

**Activation sequence validated:** (Entitlement created — Yes/No; Provisioning order generated — Yes/No; Billing event fired — Yes/No)

## Approach

Which pattern from SKILL.md applies?

- [ ] EPC Service Catalog Initialization (greenfield)
- [ ] Account Hierarchy Setup (Billing → Service → Consumer)
- [ ] Order Decomposition Configuration
- [ ] Contract Lifecycle Activation
- [ ] End-to-end Subscriber Flow Validation

**Reason this pattern applies:** (explain)

## Checklist

- [ ] Communications Cloud managed package confirmed installed
- [ ] Communications Cloud Admin permission set assigned before EPC config
- [ ] EPC catalog has at least one Catalog, Product Specification, Product Offering, and Catalog Assignment
- [ ] Account RecordTypes (`Billing_Account`, `Service_Account`, `Consumer_Account`) confirmed present
- [ ] All Account SOQL queries include `RecordType.DeveloperName` filter
- [ ] No products created directly in Product2 without EPC Product Offering
- [ ] Industries Order Management used (not Salesforce Commerce Order Management)
- [ ] Order decomposition tested: commercial order → technical order records confirmed
- [ ] Contract activation uses Industries sequence (not direct `Status = 'Activated'` update)
- [ ] End-to-end subscriber flow tested and validated

## Notes

Record any deviations from the standard pattern and why:

(describe deviations, workarounds, or open questions here)
