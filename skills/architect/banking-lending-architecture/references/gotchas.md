# Gotchas — Banking and Lending Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OmniStudio Is Required for Digital Lending — Not Bundled with FSC

**What happens:** A project purchases FSC for banking and begins Digital Lending design work in a sandbox that has OmniStudio from a prior engagement. Production deployment fails because the production org does not have OmniStudio provisioned. The `industriesdigitallending` namespace is inaccessible.

**When it occurs:** Any Digital Lending implementation where the production license procurement is handled separately from sandbox provisioning, or where the project team assumes OmniStudio is included in FSC.

**How to avoid:** Treat OmniStudio as a separate license item and confirm provisioning in every target environment (all sandboxes + production) before starting Digital Lending design. Add OmniStudio confirmation to the architecture prerequisites checklist.

---

## Gotcha 2: `loanApplicantAutoCreation` Defaults to Off

**What happens:** LoanApplicant records inserted via API or OmniScript do not automatically create the associated Person Account when `loanApplicantAutoCreation` is disabled (the default). Integration teams bulk-loading applicant data produce orphan LoanApplicant records with no Account association, breaking loan officer workspaces and FSC household rollups.

**When it occurs:** During data migrations, integration imports, or any programmatic LoanApplicant creation without explicit Person Account handling.

**How to avoid:** Set `loanApplicantAutoCreation = true` in IndustriesSettings before any LoanApplicant data load. If the flag cannot be enabled, the integration must explicitly create Person Account records and link them via `ApplicantId` on each LoanApplicant record.

---

## Gotcha 3: ResidentialLoanApplication and FinancialAccount Are Different Objects

**What happens:** Architects design the full loan lifecycle — origination through servicing — entirely on ResidentialLoanApplication. After loan close, post-close account servicing (balance tracking, payment history, statement generation) requires FinancialAccount (Liability type), not ResidentialLoanApplication. Using ResidentialLoanApplication for serviced loan data causes incorrect FSC household financial summaries and breaks FSC's standard Banker relationship model.

**When it occurs:** When the same team handles both origination and servicing design and incorrectly extends ResidentialLoanApplication for post-close use cases.

**How to avoid:** Design a clear state transition: ResidentialLoanApplication represents the origination application through funding. Upon funding, create a FinancialAccount (Liability subtype) record representing the serviced loan. The two objects are related but separate in the FSC data model.

---

## Gotcha 4: Sandbox Refreshes Reset IndustriesSettings Flags

**What happens:** IndustriesSettings flags (`enableDigitalLending`, `loanApplicantAutoCreation`) set in a full sandbox are not preserved after a sandbox refresh. The refreshed sandbox has the default flag values, causing Digital Lending to fail on the first test run after refresh.

**When it occurs:** After every sandbox refresh in a project that relies on Digital Lending. Particularly disruptive when the QA team discovers the issue after already loading test data.

**How to avoid:** Include IndustriesSettings configuration in the sandbox post-refresh runbook. Consider scripting flag verification with a SOQL query or Setup audit to confirm settings are active before handing the sandbox to the test team.

---

## Gotcha 5: Core Banking Sync Conflicts When Salesforce Creates Duplicate FinancialAccount Records

**What happens:** When both Salesforce (via account servicing workflows) and the core banking integration create FinancialAccount records for the same loan, duplicate records appear in the FSC household summary. Existing deduplication rules for Accounts do not automatically apply to FinancialAccount records — custom duplicate handling is required.

**When it occurs:** During initial integration setup when the team has not explicitly decided whether Salesforce or the core banking system is the system of record for FinancialAccount creation.

**How to avoid:** Establish a single source of FinancialAccount creation at the start of integration design. The recommended pattern is the core banking system creating FinancialAccount records via the Remote Call-In integration pattern. Salesforce-side automation should not independently create FinancialAccount records for the same loan identifiers.
