---
name: banking-lending-architecture
description: "Architecture guidance for Salesforce FSC banking and Digital Lending: loan origination platform design, ResidentialLoanApplication data model, payment processing integration patterns, and account servicing workflow architecture. NOT for implementation-level OmniScript development, FSC Insurance Cloud, or generic CRM data modeling."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "how do I architect loan origination on Salesforce Financial Services Cloud"
  - "designing Digital Lending on FSC with OmniStudio and ResidentialLoanApplication"
  - "payment processing integration pattern for FSC banking workflows"
  - "what is the FSC Digital Lending data model and what IndustriesSettings flags do I need"
  - "architecting account servicing workflows for retail banking on Salesforce FSC"
tags:
  - banking
  - lending
  - fsc
  - digital-lending
  - loan-origination
  - financial-services-cloud
  - architecture
inputs:
  - "Banking capabilities required: loan origination, account servicing, payment processing"
  - "Org license type (base FSC vs Digital Lending add-on)"
  - "OmniStudio availability (required for Digital Lending)"
  - "External system landscape: core banking, payment processor, credit bureau integrations"
outputs:
  - "Lending architecture decision matrix"
  - "ResidentialLoanApplication data model design"
  - "Payment integration pattern selection"
  - "OmniStudio prerequisite checklist for Digital Lending"
dependencies:
  - fsc-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Banking and Lending Architecture

This skill activates when an architect or senior practitioner needs to design a Salesforce FSC banking or lending solution — covering loan origination platform selection, the ResidentialLoanApplication data model, payment processing integration patterns, and account servicing architecture. It does NOT cover FSC Insurance Cloud, implementation-level OmniScript development, or generic CRM configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Digital Lending requires OmniStudio** — FSC Digital Lending is built on OmniStudio (OmniScripts, FlexCards, Integration Procedures) and the `industriesdigitallending` Apex namespace. OmniStudio must be provisioned and active before Digital Lending workflows can function. This is the most commonly missed dependency at project kickoff.
- **IndustriesSettings flags** — `enableDigitalLending` and `loanApplicantAutoCreation` must be enabled in the IndustriesSettings metadata or Setup UI. Without `loanApplicantAutoCreation`, LoanApplicant records do not auto-create the associated Person Account.
- **Payment processing must be async** — Designing payment initiation as a synchronous Apex callout on record save violates the 100-callout-per-transaction limit. All payment calls must be async via Integration Procedures with platform event callbacks.
- **Core banking as system of record** — Most FSC banking implementations use an external core banking system (FIS, Fiserv, Temenos) as the servicing system of record. Salesforce is the engagement and origination layer. Design data flows accordingly.

---

## Core Concepts

### Digital Lending Platform

FSC Digital Lending is a pre-built loan origination platform requiring OmniStudio and the `industriesdigitallending` namespace. It provides OmniScript-driven loan intake, Integration Procedure hooks for credit bureau and income verification calls, and a FlexCard-based loan officer workspace. It is NOT a standalone set of standard objects — the full platform requires:

- OmniStudio license and provisioning
- `enableDigitalLending` IndustriesSettings flag enabled
- `industriesdigitallending` Apex namespace deployed
- Connected App configuration for external service integrations

If any prerequisite is missing, the Digital Lending UI does not render and APIs return errors.

### ResidentialLoanApplication Data Model

The `ResidentialLoanApplication` object anchors the FSC lending data model:

- **LoanApplicant** — child of ResidentialLoanApplication, linked to a Person Account. The `loanApplicantAutoCreation` flag controls automatic Account creation.
- **LoanApplicantAsset** — declared assets (real estate, vehicles, savings)
- **LoanApplicantLiability** — declared liabilities (mortgages, auto loans, credit cards)
- **LoanApplicantIncome** — income sources
- **LoanApplicantAddress** — address history

This hierarchy is separate from FSC's Financial Account objects. Loan origination lives in ResidentialLoanApplication; serviced loans (post-close) are represented as FinancialAccount records (Liability type).

### Async Payment Processing Pattern

Payment processing in banking workflows requires an async architecture:

1. User initiates payment from Salesforce UI
2. Integration Procedure makes outbound call to payment processor API
3. IP returns a pending transaction reference to the UI immediately
4. Payment processor sends confirmation callback via REST API or platform event
5. Salesforce platform event trigger or Flow updates the payment record

This pattern handles payment processor latency, avoids governor limit violations, and provides retry capability for failed transactions.

---

## Common Patterns

### OmniScript-Driven Loan Origination with Integration Procedures

**When to use:** FSC Digital Lending is licensed and OmniStudio is provisioned.

**How it works:**
1. OmniScript collects applicant data across multiple steps.
2. Integration Procedures call credit bureaus (Experian, Equifax) and income verification (Plaid, Finicity) at decision gates.
3. `industriesdigitallending` APIs evaluate eligibility and return a conditional approval.
4. ResidentialLoanApplication and child objects are created upon submission.
5. Loan officer FlexCard shows pipeline with real-time status from Integration Procedure polling.

**Why not Flow/Apex:** Digital Lending OmniScripts are pre-built and configurable for common loan products. Rebuilding in Flow requires creating the entire guided UX, integration hooks, and decisioning layer from scratch.

### Async Payment Initiation

**When to use:** Any payment action in FSC — mortgage payment, ACH transfer, wire.

**How it works:**
1. Integration Procedure calls payment processor API asynchronously.
2. Returns pending transaction ID to the user immediately.
3. Platform event or REST callback from processor updates payment status.
4. Triggered automation on status update notifies borrower and updates loan record.

**Why not synchronous callout:** The 100-callout-per-transaction limit, variable payment processor response times (up to 10+ seconds), and transaction rollback behavior on timeout make synchronous callout architecturally unsound for payment workflows.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Loan origination with OmniStudio available | FSC Digital Lending + OmniScript | Pre-built guided intake with Digital Lending data model |
| Loan origination without OmniStudio | Custom Screen Flow + ResidentialLoanApplication | Object model available without Digital Lending platform |
| Payment initiation | Async Integration Procedure + platform event callback | Avoids callout limits and handles processor latency |
| Core banking data sync | Batch Data Synchronization via Bulk API 2.0 | Handles large volumes; designed for banking batch patterns |
| Real-time payment status updates | Remote Call-In (processor calls SF REST API) | External system pushes status to Salesforce |
| Credit bureau integration | Integration Procedure + HTTP callout | Declarative, governor-safe, auditable |

---

## Recommended Workflow

1. **Prerequisites audit** — Confirm OmniStudio provisioning, `industriesdigitallending` namespace availability, and required IndustriesSettings flags before committing to Digital Lending platform.
2. **Platform selection** — Choose Digital Lending (full pre-built platform) or custom ResidentialLoanApplication (if OmniStudio unavailable). Document the choice and rationale.
3. **Data model design** — Map all loan application data requirements to the ResidentialLoanApplication hierarchy. Design post-close representation as FinancialAccount (Liability type).
4. **Integration pattern design** — Select pattern for each external system: async IP callout, batch Bulk API sync, or Remote Call-In.
5. **Payment architecture** — Design all payment flows as async IP calls with platform event callbacks. Document the callback endpoint and security configuration.
6. **IndustriesSettings documentation** — List all required flags and their values in the environment setup runbook.
7. **Review** — Verify no synchronous Apex payment callouts, `loanApplicantAutoCreation` flag strategy is deliberate, and Digital Lending prerequisites are fully documented.

---

## Review Checklist

- [ ] OmniStudio confirmed available if Digital Lending platform is in scope
- [ ] `industriesdigitallending` namespace dependency documented
- [ ] `loanApplicantAutoCreation` IndustriesSettings flag status confirmed
- [ ] All payment flows use async Integration Procedure + callback pattern
- [ ] No synchronous Apex callouts for payments or credit checks
- [ ] ResidentialLoanApplication hierarchy correctly mapped to requirements
- [ ] Post-close loan servicing represented as FinancialAccount (not ResidentialLoanApplication)

---

## Salesforce-Specific Gotchas

1. **OmniStudio is a hard prerequisite for Digital Lending** — FSC Digital Lending requires OmniStudio provisioning. Orgs purchasing FSC without OmniStudio cannot use the Digital Lending guided origination experience. This dependency is frequently missed at project kickoff when license procurement does not include OmniStudio.
2. **`loanApplicantAutoCreation` defaults to off** — Without this flag, creating a LoanApplicant via API or OmniScript does not auto-create the associated Person Account. Integration teams that bulk-load LoanApplicant records without enabling this flag produce orphan applicant records with no Account association.
3. **Payment callouts from Apex triggers violate the 100-callout limit** — Any synchronous payment initiation pattern in a trigger context will fail when multiple records are processed simultaneously, leaving payment records in an inconsistent state. Async Integration Procedure with callback is the required pattern.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lending platform decision matrix | Comparison of Digital Lending vs custom ResidentialLoanApplication with OmniStudio prerequisite documented |
| ResidentialLoanApplication data model | Hierarchy diagram covering loan applicant, financial details, and Account linkage |
| Payment integration architecture | Async payment flow diagram with platform event callback and retry pattern |

---

## Related Skills

- `fsc-architecture-patterns` — For broad FSC data model, sharing model, and integration strategy baseline
- `industries-data-model` — For cross-industry object model reference including FSC lending objects
