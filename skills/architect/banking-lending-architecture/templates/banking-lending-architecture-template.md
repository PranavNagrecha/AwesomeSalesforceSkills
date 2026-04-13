# Banking Lending Architecture — Work Template

Use this template when working on tasks in this area.

---

## Scope

**Skill:** `banking-lending-architecture`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before committing to a platform or pattern.

**FSC license type confirmed:**
- [ ] Base FSC only (no Digital Lending add-on)
- [ ] FSC + Digital Lending add-on provisioned

**OmniStudio availability:**
- [ ] OmniStudio licensed and provisioned — Digital Lending pre-built platform available
- [ ] OmniStudio NOT available — custom Screen Flow + ResidentialLoanApplication path required

**IndustriesSettings flags status:**
- [ ] `enableDigitalLending` confirmed enabled
- [ ] `loanApplicantAutoCreation` confirmed enabled (required to auto-create Person Account on LoanApplicant)
- [ ] Neither confirmed — must check Setup or metadata before proceeding

**`industriesdigitallending` namespace:**
- [ ] Namespace confirmed deployed in org
- [ ] Namespace not confirmed — Digital Lending APIs unavailable until confirmed

**External system landscape:**
- Core banking system (FIS, Fiserv, Temenos, other): _______________
- Payment processor: _______________
- Credit bureaus (Experian, Equifax, TransUnion): _______________
- Income verification (Plaid, Finicity, other): _______________
- System of record for loan servicing data: _______________
  - [ ] External core banking system (Salesforce = engagement layer)
  - [ ] Salesforce (post-origination servicing in SF)

**Loan product types in scope:**
- [ ] Residential mortgage
- [ ] Home equity / HELOC
- [ ] Auto / consumer installment loan
- [ ] Commercial / business lending
- [ ] Other: _______________

---

## Platform Selection Decision

| Option | Available | Selected | Reason |
|---|---|---|---|
| FSC Digital Lending (OmniScript + ResidentialLoanApplication) | [ ] Yes [ ] No | [ ] | OmniStudio licensed; pre-built guided intake |
| Custom Screen Flow + ResidentialLoanApplication | Always | [ ] | OmniStudio unavailable; custom UX required |

**Documented rationale for selection:**

---

## ResidentialLoanApplication Data Model

**Hierarchy for this implementation:**

```
ResidentialLoanApplication
  └── LoanApplicant (linked to Person Account — loanApplicantAutoCreation flag controls auto-creation)
      └── LoanApplicantAsset (declared assets)
      └── LoanApplicantLiability (declared liabilities)
      └── LoanApplicantIncome (income sources)
      └── LoanApplicantAddress (address history)
```

**Post-close representation:**
- [ ] FinancialAccount (Liability type) — represents the serviced loan after origination closes
- [ ] Serviced in external core banking only (Salesforce not used post-close)

**Custom fields needed on ResidentialLoanApplication:**

| Field Label | API Name | Type | Purpose |
|---|---|---|---|
| | | | |

---

## Integration Pattern Design

| External System | Integration Pattern | Async? | Notes |
|---|---|---|---|
| Credit bureau | Integration Procedure + HTTP callout | Yes | Called at application decision gate |
| Income verification | Integration Procedure + HTTP callout | Yes | Called at income verification step |
| Payment processor | IP callout + platform event callback | Yes (required) | Sync callout violates governor limits |
| Core banking (batch sync) | Bulk API 2.0 | Yes | Large-volume servicing data |
| Core banking (real-time status) | Remote Call-In (core banking calls SF REST) | N/A (inbound) | Status updates pushed to Salesforce |

**Payment architecture confirmation:**
- [ ] All payment initiation flows through async Integration Procedure
- [ ] Platform event or REST callback used for payment confirmation
- [ ] NO synchronous Apex callouts for payment processing
- [ ] Retry logic designed for failed payment callbacks

---

## OmniStudio Prerequisites Checklist (Digital Lending path only)

- [ ] OmniStudio license provisioned and active
- [ ] `enableDigitalLending` = true in IndustriesSettings
- [ ] `loanApplicantAutoCreation` = true in IndustriesSettings
- [ ] `industriesdigitallending` Apex namespace deployed
- [ ] Connected App configured for external service integrations
- [ ] OmniScript templates deployed (loan intake, status update, document collection)
- [ ] Integration Procedures deployed (credit bureau, income verification, payment initiation)
- [ ] FlexCard loan officer workspace configured

---

## Review Checklist

- [ ] OmniStudio confirmed available if Digital Lending platform is in scope
- [ ] `industriesdigitallending` namespace dependency documented
- [ ] `loanApplicantAutoCreation` IndustriesSettings flag strategy is deliberate (on or off with justification)
- [ ] All payment flows use async Integration Procedure + callback pattern
- [ ] No synchronous Apex callouts for payments or credit checks
- [ ] ResidentialLoanApplication hierarchy correctly mapped to requirements
- [ ] Post-close loan servicing represented as FinancialAccount (not ResidentialLoanApplication)
- [ ] IndustriesSettings flags listed in environment setup runbook

---

## Notes

(Record deviations from the standard pattern and justification)
