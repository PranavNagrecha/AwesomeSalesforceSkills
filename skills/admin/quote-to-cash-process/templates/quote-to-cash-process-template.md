# Quote-to-Cash Process (CPQ + Revenue Cloud) — Work Template

Use this template when mapping, designing, or troubleshooting the end-to-end Q2C process in a CPQ or Revenue Cloud org.

---

## Scope

**Skill:** `quote-to-cash-process`

**Request summary:** (fill in what the user asked for)

**In scope:**
- SBQQ__Quote__c and SBQQ__QuoteLine__c object chain
- Advanced Approvals (sbaa__) configuration and troubleshooting
- Contract creation and SBQQ__Subscription__c generation
- Order activation and blng__BillingSchedule__c generation
- blng__Invoice__c generation and billing run configuration
- Amendment and renewal flows

**Out of scope:**
- Standard Salesforce Quote / QuoteLineItem objects (use quote-to-cash-requirements skill)
- CPQ pricing rules, discount schedule configuration, or guided selling setup (use cpq-architecture-patterns skill)
- CPQ product catalog and bundle configuration (use cpq-data-model skill)

---

## Package Verification

Before proceeding, confirm the following managed packages are installed:

| Package | Namespace | Required For | Installed? |
|---|---|---|---|
| Salesforce CPQ | SBQQ | Quote, QuoteLine, Subscription objects | [ ] Yes / [ ] No |
| Revenue Cloud Billing | blng | BillingSchedule, Invoice objects | [ ] Yes / [ ] No |
| Advanced Approvals | sbaa | Multi-step conditional approval routing | [ ] Yes / [ ] No / [ ] Not required |

Verification SOQL:
```sql
SELECT NamespacePrefix, Status FROM PackageLicense WHERE NamespacePrefix IN ('SBQQ', 'blng', 'sbaa')
```

---

## Context Gathered

Answer these before proceeding:

- **Billing model:** [ ] One-time only / [ ] Recurring subscriptions / [ ] Usage-based / [ ] Hybrid
- **Approval requirements:** [ ] None / [ ] Single-level / [ ] Multi-tier (requires Advanced Approvals)
- **Approval trigger field:** Quote-level (e.g., SBQQ__NetAmount__c) / Line-level (e.g., SBQQ__Discount__c per line)
- **Contract creation:** [ ] Manual (business clicks button) / [ ] Automated via Flow / [ ] Automated via Apex
- **Order creation:** [ ] Manual from Contract / [ ] Automated on Contract creation
- **Amendment/Renewal in scope:** [ ] Yes / [ ] No

---

## Object Chain Map

Fill in the status values and trigger events for this org's configuration:

| Step | Object | Key Fields | Status Value / Trigger |
|---|---|---|---|
| 1 | SBQQ__Quote__c | SBQQ__Status__c | Needs Approval → Approved |
| 2 | sbaa__ApprovalRequest__c | sbaa__Status__c | Pending → Approved (if sbaa installed) |
| 3 | Contract | Status | Draft → Activated |
| 4 | SBQQ__Subscription__c | SBQQ__Status__c | Created by CPQ on Contract creation |
| 5 | Order | Status, SBQQ__Contracted__c | Draft → Activated + SBQQ__Contracted__c = true |
| 6 | blng__BillingSchedule__c | blng__Status__c | Created on Order activation |
| 7 | blng__Invoice__c | blng__InvoiceStatus__c | Draft → Posted (on billing run) |

---

## Approval Design (Advanced Approvals)

Complete if Advanced Approvals (sbaa__) is in scope:

**Chain name:** _______________

| Rule # | Condition Object | Condition Field | Operator | Value | Approver Source |
|---|---|---|---|---|---|
| 1 | SBQQ__Quote__c / SBQQ__QuoteLine__c | | | | User field / Queue / Role |
| 2 | | | | | |
| 3 | | | | | |

**Escalation behavior on no response:** [ ] Reassign / [ ] Remind only / [ ] Auto-approve after N days

---

## Contract Pivot Specification

| Field on Contract | Populated From | Notes |
|---|---|---|
| AccountId | SBQQ__Quote__c.SBQQ__Account__c | |
| StartDate | SBQQ__Quote__c.SBQQ__StartDate__c | |
| ContractTerm | SBQQ__Quote__c.SBQQ__SubscriptionTerm__c | In months |
| SBQQ__RenewalForecast__c | Org default or Quote field | Controls renewal quote auto-generation |

---

## Billing Configuration

| Check | Status |
|---|---|
| Each recurring product has blng__BillingRule__c assigned | [ ] Confirmed / [ ] Missing for: ___ |
| Billing run is scheduled (Setup > Billing Runs) | [ ] Confirmed / [ ] Not configured |
| Billing run frequency matches invoice cadence | [ ] Aligned / [ ] Mismatched |
| blng__BillingSchedule__c records exist after Order activation | [ ] Confirmed / [ ] Not created — investigate |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Advanced Approvals Chain for Tiered Discount Routing** — multi-level, line-level conditions required
- [ ] **Automated Contract Creation on Quote Approval** — Flow-based contracting on SBQQ__Status__c change
- [ ] **Troubleshooting billing schedule gap** — diagnose Contract pivot or Order activation issue
- [ ] **Amendment flow** — use Contract Amend action to generate Amendment Quote

Justification: (fill in why this pattern was selected)

---

## Review Checklist

- [ ] SBQQ, blng, and sbaa package installation confirmed (or absence noted and accounted for)
- [ ] No SOQL or Apex references the standard `Quote` or `QuoteLineItem` objects for CPQ data
- [ ] Contract creation step is explicitly included in the workflow — not assumed to be automatic
- [ ] Order activation (not just creation) confirmed as the billing schedule trigger
- [ ] Each recurring product has a blng__BillingRule__c — confirmed in sandbox
- [ ] Advanced Approvals approval status read from sbaa__ApprovalRequest__c, not ProcessInstance
- [ ] sbaa__Approver__c records use dynamic user sources (role hierarchy, queue) — no hardcoded User IDs
- [ ] End-to-end tested in sandbox: Quote → Approval → Contract → Order → BillingSchedule → Invoice
- [ ] Amendment and renewal paths tested if in scope

---

## Deviations and Notes

Record any deviations from the standard pattern and why:

(fill in)

---

## Diagnostic Queries

Use these to verify the chain at each stage:

```sql
-- Confirm CPQ packages installed
SELECT NamespacePrefix FROM PackageLicense WHERE NamespacePrefix IN ('SBQQ', 'blng', 'sbaa')

-- CPQ quotes pending approval
SELECT Id, Name, SBQQ__Status__c FROM SBQQ__Quote__c WHERE SBQQ__Status__c = 'Needs Approval'

-- Advanced Approvals requests for a quote
SELECT Id, sbaa__Status__c, sbaa__Approver__r.Name FROM sbaa__ApprovalRequest__c WHERE sbaa__TargetId__c = '<QuoteId>'

-- Subscriptions on a Contract
SELECT Id, SBQQ__Product__r.Name, SBQQ__Status__c FROM SBQQ__Subscription__c WHERE SBQQ__Contract__c = '<ContractId>'

-- Orders missing the Contracted flag
SELECT Id, Status, SBQQ__Contracted__c FROM Order WHERE SBQQ__Contracted__c = false AND Status = 'Activated'

-- Billing schedules on an Order
SELECT Id, blng__Status__c, blng__BillingFrequency__c FROM blng__BillingSchedule__c WHERE blng__Order__c = '<OrderId>'

-- Invoices generated for an Account
SELECT Id, blng__InvoiceStatus__c, blng__InvoiceDate__c, blng__TotalAmount__c FROM blng__Invoice__c WHERE blng__Account__c = '<AccountId>' ORDER BY blng__InvoiceDate__c DESC
```
