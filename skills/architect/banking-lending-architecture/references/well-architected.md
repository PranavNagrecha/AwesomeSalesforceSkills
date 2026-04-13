# Well-Architected Notes — Banking and Lending Architecture

## Relevant Pillars

- **Security** — Loan application data (SSN, income, credit score) is regulated under FCRA, GLBA, and state privacy laws. FSC Compliant Data Sharing must control access to ResidentialLoanApplication and LoanApplicant records. Field-level security must restrict PII fields from loan officers in markets where they have no need to see applicant SSN or full income details.
- **Reliability** — Payment processing integrations must include retry logic and idempotency keys. Platform event-driven payment callbacks must handle duplicate delivery (platform events have at-least-once delivery semantics). Credit bureau integration failures must not block loan application progression — failed checks should produce a pending state, not an error state.
- **Performance Efficiency** — ResidentialLoanApplication queries for loan officer workspaces in high-volume origination environments require selective indexes on status, close date, and assigned officer. SOQL on large LoanApplicant datasets with multi-hop joins (LoanApplicant → Account → Contact) need query plan analysis.
- **Operational Excellence** — IndustriesSettings flags and OmniStudio provisioning must be part of every deployment runbook. Post-deployment validation scripts should verify Digital Lending activation and `loanApplicantAutoCreation` flag status in each target environment.

## Architectural Tradeoffs

**Digital Lending (pre-built) vs. Custom ResidentialLoanApplication:** Digital Lending provides a pre-built, configurable origination platform but requires OmniStudio licensing. If OmniStudio is unavailable or the loan product is simple, a custom Screen Flow + ResidentialLoanApplication approach avoids the OmniStudio dependency at the cost of building the guided UX from scratch.

**Salesforce as system of record vs. engagement layer:** Designing Salesforce as the loan servicing system of record (tracking balances, payments, statements) requires significant custom development to match core banking capabilities. Most architectures position Salesforce as the engagement and origination layer, with post-close loan data syncing from the core banking system into FinancialAccount records.

## Anti-Patterns

1. **Designing Digital Lending without confirming OmniStudio provisioning** — OmniStudio is a separate license from FSC. Architectures that assume Digital Lending is available because FSC is licensed lead to go-live failures when production lacks OmniStudio.
2. **Synchronous Apex payment callouts** — Payment processing designed as synchronous Apex callouts on record save violates the 100-callout-per-transaction governor limit and cannot handle payment processor latency. Async Integration Procedure with platform event callback is the required pattern.
3. **Using ResidentialLoanApplication for post-close loan servicing** — ResidentialLoanApplication models the origination application lifecycle. Serviced loans require FinancialAccount (Liability type) for FSC household summaries and standard banker relationship views to function correctly.

## Official Sources Used

- Financial Services Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_dev.meta/financial_services_cloud_dev/fsc_dev_intro.htm
- Financial Services Cloud Data Model Gallery — https://architect.salesforce.com/diagrams/framework/financial-services-cloud-data-model
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- FSC Digital Lending Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/digital_lending_overview.htm
