# Examples — Banking and Lending Architecture

## Example 1: Digital Lending Prerequisite Checklist Prevents Go-Live Failure

**Context:** A regional bank is implementing FSC Digital Lending for mortgage origination. The project team designed a full OmniScript-based loan intake flow in a sandbox that had OmniStudio provisioned from a prior pilot project. The production org does not have OmniStudio.

**Problem:** At deployment to production, the Digital Lending OmniScripts fail to render. The `industriesdigitallending` namespace is unavailable. The loan officer workspace shows blank FlexCards. Three weeks before go-live, the project discovers a missing OmniStudio license for production.

**Solution:**

```text
Pre-Architecture Digital Lending Prerequisite Checklist:
1. Setup > Company Information > Permission Set Licenses
   → Confirm "OmniStudio User" PSL is present and has available seats
2. Setup > Installed Packages
   → Confirm OmniStudio managed package is installed (or standard runtime is enabled)
3. Apex Class search for "industriesdigitallending"
   → Confirm namespace classes are accessible
4. Setup > Digital Lending
   → Enable Digital Lending feature flag
5. IndustriesSettings metadata
   → Confirm enableDigitalLending = true
   → Confirm loanApplicantAutoCreation = true
6. Test OmniScript render with a single-step pilot script before committing to full build
```

**Why it works:** Digital Lending is a composed platform — OmniStudio provides the UI layer, `industriesdigitallending` provides the processing layer, and IndustriesSettings flags control activation. All three must be confirmed in every environment (sandbox and production) before any architecture commitment.

---

## Example 2: loanApplicantAutoCreation Flag Causes Orphan Applicant Records

**Context:** A credit union builds a custom integration that bulk-loads ResidentialLoanApplication and LoanApplicant records via Data Loader from their legacy system during a data migration. The `loanApplicantAutoCreation` IndustriesSettings flag is left at its default (disabled).

**Problem:** 15,000 LoanApplicant records are inserted successfully. None of them have an associated Person Account. The loan officer workspace shows applicants with no contact information, address, or FSC household data because the Person Account records were never created.

**Solution:**

```text
Fix options:
Option A: Enable loanApplicantAutoCreation before migration
  → IndustriesSettings.loanApplicantAutoCreation = true
  → Salesforce automatically creates Person Accounts on LoanApplicant insert
  → Requires Person Account to be enabled in the org

Option B: Post-migration Account creation script
  → For existing orphan LoanApplicant records, create Person Account records
  → Update LoanApplicant.ApplicantId (lookup to Account) with the new Account Ids
  → Verify via SOQL: SELECT COUNT() FROM LoanApplicant WHERE ApplicantId = null
```

**Why it works:** The `loanApplicantAutoCreation` flag triggers Salesforce's internal Person Account creation logic when a LoanApplicant is inserted. Without it, the integration must explicitly create Person Accounts and link them to LoanApplicant records — an additional step that is easily missed in bulk data migration scenarios.

---

## Anti-Pattern: Synchronous Apex Payment Callout on Trigger

**What practitioners do:** Architects design payment initiation as an after-insert trigger on a Payment__c custom object that makes an Apex HttpRequest to the payment processor API synchronously.

**What goes wrong:** When a loan officer processes multiple payments simultaneously (bulk action), the Apex trigger hits the 100-callout-per-transaction limit. Transactions fail with `System.LimitException: Too many callouts`. Partial failures leave some Payment records in an inserted state without corresponding payment processor records, causing data inconsistency.

**Correct approach:** Design payment initiation as an async Integration Procedure invoked from a FlexCard or OmniScript action. The Integration Procedure calls the payment processor and returns a pending transaction ID. A platform event or webhook callback from the payment processor updates the Payment record status when the transaction completes. This pattern scales to bulk operations, handles processor latency, and provides a retry mechanism for failed transactions.
