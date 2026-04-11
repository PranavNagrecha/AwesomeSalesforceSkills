# Industries Insurance Setup — Work Template

Use this template when configuring FSC Insurance / Industries Insurance for a Salesforce org.
Fill in each section as you work through the task.

## Scope

**Skill:** `industries-insurance-setup`

**Request summary:** (describe what the client or project requires — e.g., "enable insurance for a personal lines auto carrier, configure quoting OmniScript, set up claim intake")

**Lines of business in scope:**
- [ ] Personal lines — auto
- [ ] Personal lines — homeowners/renters
- [ ] Commercial lines
- [ ] Life / annuity
- [ ] Specialty / other: _______________

---

## Pre-Configuration Decisions (Complete Before Any Setup)

### Licensing Verification

| Check | Status | Notes |
|---|---|---|
| FSC Insurance PSL provisioned in org | | |
| FSC Insurance PSL assigned to all relevant users | | |
| OmniStudio licensed (required for quoting OmniScripts) | | |
| Platform path confirmed (managed-package or native-core) | | |

**Platform path:** [ ] Managed Package   [ ] Native Core   
**Confirmed by checking:** Setup > Installed Packages on: _______________

### Irreversible Insurance Settings Decisions

Document these decisions BEFORE opening Setup > Insurance Settings.

| Setting | Decision | Business Reason | Approved By |
|---|---|---|---|
| Enable Many-to-Many Policy Relationships | [ ] Yes  [ ] No | | |
| Enable Multiple Producers Per Policy | [ ] Yes  [ ] No | | |

**Settings enabled on (date):** _______________  
**Enabled by (name):** _______________  
**Reviewed by Solution Architect:** _______________

---

## Context Gathered

- **Org type / edition:** _______________
- **Insurance Settings panel visible in Setup:** [ ] Yes  [ ] No
- **Known platform constraints or limits:** _______________
- **Existing insurance configuration already in place:** _______________
- **Failure modes identified during discovery:** _______________

---

## Coverage Type Configuration

List each CoverageType record to be created:

| CoverageType Name | Line of Business | Notes |
|---|---|---|
| | | |
| | | |
| | | |

---

## InsurancePolicyParticipant Role Picklist

List all Role values to be configured (finalize before creating any participant records):

| Role Value (API Name) | Role Label | Use Case |
|---|---|---|
| NamedInsured | Named Insured | Primary policyholder |
| Producer | Producer | Agent/broker |
| | | |
| | | |

**Picklist finalized and approved:** [ ] Yes   **Date:** _______________

---

## OmniScript Quoting Flow Configuration

**OmniScript name:** _______________  
**OmniScript type:** _______________  
**Platform path namespace for InsProductService:** _______________

| Step Name | Step Type | Notes |
|---|---|---|
| AccountSearch | DataRaptor Extract | Resolve insured account |
| RiskInputs | Step | Capture coverage inputs |
| RateProducts | Remote Action | InsProductService.getRatedProducts |
| ProductSelection | LWC | insOsGridProductSelection |
| IssuePolicy | Integration Procedure / HTTP Action | POST /connect/insurance/policy-administration/policies |

**Remote Action class reference (confirm namespace):** _______________  
**Connect API version used:** _______________

---

## Policy Issuance Verification

After each test issuance, record results:

| Test # | Policy ID Created | InsurancePolicyCoverage Count | Expected Count | Pass/Fail |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

---

## Approach

**Patterns applied from SKILL.md:**
- [ ] OmniScript Quoting with Remote Action Rating
- [ ] Claim Setup with Coverage Linking
- [ ] Other: _______________

**Deviations from standard pattern (explain why):** _______________

---

## Review Checklist

Copy and tick items as you complete them:

- [ ] FSC Insurance PSL confirmed provisioned and assigned to all relevant users
- [ ] Insurance Settings panel visible; irreversible settings decision documented and approved
- [ ] CoverageType records created for all lines of business; ClaimType picklist values configured
- [ ] InsurancePolicy, InsurancePolicyCoverage, and Claim page layouts configured with relevant fields visible
- [ ] InsurancePolicyParticipant role picklist finalized before any participant records created
- [ ] OmniScript quoting flow tested end-to-end with InsProductService.getRatedProducts
- [ ] Policy issuance via Connect API tested; InsurancePolicyCoverage records verified
- [ ] Platform path (managed-package vs native-core) documented in org configuration register
- [ ] Insurance.settings-meta.xml tracked in source control

---

## Notes

Record any deviations, decisions, or issues discovered during implementation:

_______________
