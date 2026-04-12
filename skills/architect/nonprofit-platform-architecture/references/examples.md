# Examples — Nonprofit Platform Architecture

## Example 1: Community Health Network — Fundraising-First Phased Adoption

**Context:** A mid-size community health nonprofit with 50,000 constituent records is migrating from NPSP to Nonprofit Cloud. The organization's primary driver is the need for Gift Entry Manager and native recurring gift processing (Gift Commitments). They also plan to implement Program and Case Management for their social services arm in a later phase.

**Problem:** The implementation team proposed launching Fundraising and Program Management simultaneously in a single 6-month phase. During architecture review it became clear that the cross-module data model had not been designed: program participant records were planned as Contact records (NPSP habit), while the Fundraising module requires Person Accounts. The two approaches conflict.

**Solution:**

The architect restructured the rollout into two phases:

```
Phase 1 (Months 1–5): Foundation + Fundraising
- Enable Person Accounts (org-level, irreversible — do this in sandbox first)
- Load 50,000 constituents as Person Accounts via Data Loader with deduplication rules
- Configure Gift Entry Manager with payment processor via Connect API v59.0+
- Configure Gift Commitments for recurring donors
- Validate batch gift entry workflow with finance team
- Go-live with Fundraising only

Phase 2 (Months 6–10): Program and Case Management
- Map program participants to existing Person Account constituent records (no new record type needed — same constituents)
- Configure Programs, Program Cohorts, Benefits, and Benefit Assignments
- Build Case Plans for social service workflows
- Connect Program Cohort outcomes to Fundraising records for impact reporting
```

**Why it works:** Separating phases enforces the correct data model decision (Person Accounts) before program data is loaded. The cross-module linkage — program participants are the same Person Account records as donors — is only possible because the Fundraising phase established the correct constituent record type first. Launching simultaneously would have produced incompatible record architectures requiring costly rework.

---

## Example 2: Regional Foundation — Grantmaking Module Scope Clarification

**Context:** A family foundation with an annual grant-giving budget of $5M is implementing Nonprofit Cloud. The implementation partner initially scoped the Grantmaking and Fundraising modules together, assuming they were both needed. The foundation does not solicit individual donations — it manages an endowment and makes grants to other nonprofits.

**Problem:** The Fundraising module was being configured with Donation campaigns and Gift Entry workflows for which there was no use case. At the same time, the Grantmaking module's external-facing grant application portal (Experience Cloud) had not been scoped at all, meaning the architecture had no plan for how external nonprofits would submit grant applications.

**Solution:**

```
Correct Module Scope:
- REMOVE: Fundraising module (no inbound donations — the foundation does not fundraise)
- ADD: Grantmaking module as primary
- ADD: Experience Cloud (external applicant portal for grant submissions)
- KEEP: Program Management for tracking grant recipient progress

Architecture additions required:
- External Community User licenses for grant applicants (nonprofit organizations as Accounts)
- Experience Cloud site: Funding Opportunity listing + Funding Request submission form
- Sharing rules: grant applicants can only see their own Funding Request records
- Funding Award → Funding Disbursement workflow via Salesforce Flow
- Finance integration: Funding Disbursement records trigger payment scheduling in ERP via Platform Event
```

**Why it works:** Identifying the correct module scope early eliminated wasted Fundraising configuration work and revealed the Experience Cloud requirement that was absent from the original scope. The architectural principle — Grantmaking is for foundations making grants outward, Fundraising is for organizations receiving donations inward — prevented a significant licensing and configuration error.

---

## Example 3: National Volunteer Organization — Volunteer Management Scope Underestimation

**Context:** A national nonprofit with 3,000 active volunteers scoped Volunteer Management as a 3-week configuration workstream. The project plan allocated two weeks for "volunteer scheduling" without reviewing the full Volunteer Management object model.

**Problem:** Upon beginning configuration, the team discovered the Volunteer Management module has 19 distinct objects — including Volunteer Projects, Jobs, Shifts, Volunteer Shift Workers, Volunteer Capacity entries, Eligibility Rules, and Volunteer Time records. The 3-week estimate covered only Shifts and Shift Workers. The remaining objects needed for operational reporting, capacity planning, and eligibility filtering were undiscoped.

**Solution:**

Conducting an object-level scoping exercise upfront:

```
Volunteer Management 19-object inventory (partial — key architecture objects):
- Volunteer_Project__c → top-level campaign or initiative
- Volunteer_Job__c → specific role within a project
- Volunteer_Shift__c → time-bound occurrence of a job
- Volunteer_Shift_Worker__c → Person Account assigned to a Shift (the link to constituent model)
- Volunteer_Hours__c → logged and approved hours
- Volunteer_Capacity__c → planned capacity per Job/Shift
- Volunteer_Recurrence_Schedule__c → recurring shift pattern definition
- GW_Volunteers__Volunteer_Skills__c → skill tagging per volunteer (Person Account)

Architecture decisions per object:
- Record ownership: who can create/edit Shift Workers (site managers vs. central staff)
- Sharing model: are volunteer records visible org-wide or restricted by region
- Reporting: shift fill rate, hours by project, volunteer retention rate
```

The Volunteer Management workstream was re-scoped to 8 weeks with a dedicated data architect for the sharing model design.

**Why it works:** The 19-object scope is not obvious from product marketing or module naming. Treating Volunteer Management as a simple scheduling tool — rather than a full operational data model — is the most common cause of NPC Volunteer Management implementation failures.

---

## Anti-Pattern: Applying NPSP Configuration Conventions to Nonprofit Cloud

**What practitioners do:** Teams migrating from NPSP attempt to recreate NPSP configuration patterns in NPC — using NPSP field API names (npsp__*), replicating CRLP rollup fields manually on Person Account records, or building Household-Account-style Account hierarchies for family relationships.

**What goes wrong:** NPSP namespace objects (npsp__Allocation__c, npsp__General_Accounting_Unit__c, etc.) do not exist in NPC. Any Flow, Apex, or configuration that references npsp__ field API names will fail with object-not-found errors. NPC has its own rollup framework and its own object model for designations, gift commitments, and constituent relationships — none of which map 1:1 to NPSP objects.

**Correct approach:** Treat NPC as a new platform, not an upgraded version of NPSP. Begin architecture from the NPC Developer Guide and NPC Data Model Gallery. Do not port NPSP configuration patterns; design NPC configuration from the NPC object model documentation. The `architect/npsp-vs-nonprofit-cloud-decision` skill covers this transition point in detail.
