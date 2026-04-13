# Examples — Insurance Cloud Architecture

## Example 1: Module Licensing Audit Before Architecture Design

**Context:** A P&C insurer is rolling out Salesforce FSC for agent-facing policy management, FNOL intake, and claims adjudication. The project team has begun designing Claim and ClaimParticipant workflows before confirming their license includes Claims Management.

**Problem:** The project team discovers in UAT that Claim objects are unavailable. They had purchased the base FSC license and the Industries Insurance Add-On but did not activate the Claims Management module. Three months of workflow design must be rescheduled pending license provisioning.

**Solution:**

```text
Pre-Architecture License Audit Steps:
1. Navigate to Setup > Company Information > Permission Set Licenses
2. Confirm "Financial Services Insurance" PSL exists and has available seats
3. Confirm "Claims Management" module PSL is provisioned
4. Navigate to Setup > Insurance Settings
5. Enable Claims Management explicitly — licensing alone does not activate the module
6. Verify Claim and ClaimParticipant objects appear in Schema Builder
```

**Why it works:** Insurance Cloud modules are independently provisioned even after the master license is in place. Running a license audit as the first architecture step prevents module-not-found failures in late-stage UAT.

---

## Example 2: InsurancePolicyParticipant Relationship Modeling for Person Accounts

**Context:** An architect is designing a policyholder data model for an FSC org using Person Accounts. The requirement is to capture one policyholder, up to three named insureds, and one beneficiary per auto policy.

**Problem:** The architect models InsurancePolicyParticipant with a Contact lookup, following standard Salesforce relationship conventions. This breaks because InsurancePolicyParticipant.ParticipantAccountId is a lookup to Account, not Contact. In an FSC Person Account org, each person IS an Account record.

**Solution:**

```soql
-- Correct: query participants via Account
SELECT Id, InsurancePolicyId, PrimaryParticipantAccountId, RoleInPolicy
FROM InsurancePolicyParticipant
WHERE InsurancePolicyId = :policyId

-- Wrong: no ContactId field exists on InsurancePolicyParticipant
-- SELECT Id, ContactId FROM InsurancePolicyParticipant  -- FAILS
```

Data model design:
- Each person (policyholder, named insured, beneficiary) must be a Person Account record in FSC.
- InsurancePolicyParticipant uses `PrimaryParticipantAccountId` (or `SecondaryParticipantAccountId` for co-policyholders) to link Account records to the policy.
- SOQL and reports must join via Account, not Contact.

**Why it works:** FSC Person Accounts merge Account and Contact into a single record. The Insurance object model was designed for this architecture — it links to Account, which in a Person Account org is the person. Architects must communicate this to reporting and integration teams who default to Contact-based queries.

---

## Anti-Pattern: Putting Underwriting Logic in Flow Decision Tables

**What practitioners do:** Architects familiar with Flow build underwriting eligibility rules using Decision elements in Screen Flows — checking property age, credit score buckets, and coverage limits via Flow formulas.

**What goes wrong:** Flow decision logic for underwriting is not managed by the InsuranceUnderwritingRule lifecycle (Active/Inactive/Draft). It cannot be audited via standard Insurance APIs. Business analysts cannot update eligibility criteria without a developer editing the Flow. Refreshed product rules require a new Flow version and deployment. External rating engines cannot consume Flow decisions via API.

**Correct approach:** Model underwriting eligibility criteria as InsuranceUnderwritingRule records with Active/Draft lifecycle management. Invoke the Insurance Product Administration APIs from an Integration Procedure for rating and eligibility evaluation. Flow orchestrates the user-facing guided experience (collect inputs, display decisions) but delegates the underwriting evaluation to the rules framework.
