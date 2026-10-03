---
name: grant-management-setup
description: "Use when configuring grant tracking in a Salesforce nonprofit org: NPSP Outbound Funds Module (open-source outfunds managed package) or Nonprofit Cloud for Grantmaking (separate license). Trigger keywords: grant management, funding awards, disbursement tranches, grantmaking setup, OFM, FundingAward, FundingDisbursement, FundingAwardRequirement. NOT for recording donor gifts and receipts, use admin/gift-entry-and-processing. NOT for reporting program outcomes to a funder, use admin/program-outcome-tracking-design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up grant tracking in our NPSP org?"
  - "We need to track funding award disbursements by tranche — which Salesforce platform should we use?"
  - "What is the difference between NPSP Outbound Funds Module and Nonprofit Cloud for Grantmaking?"
  - "turn on Grantmaking and set up funding awards with disbursement schedules and report requirements"
  - "block the next grant payment until the grantee's report is approved"
tags:
  - npsp
  - grants
  - funding-awards
  - disbursements
  - nonprofit
  - grantmaking
inputs:
  - "Whether the org is running NPSP (managed package) or Nonprofit Cloud (NPC)"
  - "License entitlements — specifically whether Nonprofit Cloud for Grantmaking is provisioned"
  - "Grant lifecycle requirements: single payment vs. multi-tranche disbursements, deliverable tracking"
  - "Volume of grants and disbursements per year (affects data model choice)"
outputs:
  - "Platform path recommendation (NPSP OFM vs. Nonprofit Cloud for Grantmaking) with rationale"
  - "Configured FundingAward, FundingDisbursement, and FundingAwardRequirement setup guidance"
  - "Grant lifecycle and status workflow documentation"
  - "Decision matrix for platform selection"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Grant Management Setup

This skill activates when a practitioner needs to configure grant tracking in a Salesforce nonprofit org. It covers both available platform paths — NPSP Outbound Funds Module (OFM) and Nonprofit Cloud for Grantmaking — and provides the decision logic, object model orientation, and configuration steps for each.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which platform is installed?** Check Installed Packages for `npsp` (NPSP), `outfunds` (Outbound Funds Module), and the Grants Management managed package, and check Setup > Grantmaking Settings. These products do not share objects. Do not mix guidance between them.
- **Is Grantmaking licensed and turned on?** Grantmaking objects need the Grantmaking licence, the feature turned on, and the Manage Funding Awards system permission. Turning Grantmaking on cannot be undone (`references/gotchas.md`, Gotchas 1 and 2).
- **What is the disbursement model?** Single payment or scheduled tranches. Both products model tranches: `FundingDisbursement` in Grantmaking, `outfunds__Disbursement__c` in Outbound Funds.
- **Which deliverables gate which payments?** Both products have a requirement object that can point at a disbursement: `FundingAwardRequirement.FundingDisbursementId` and `outfunds__Requirement__c.Disbursement__c`. (Corrected: an earlier version said Outbound Funds has no deliverable-tracking object.)

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which grants product is installed or licensed today: Outbound Funds, Grants Management, or Grantmaking?" | The products share no objects, and Grantmaking cannot be turned off once on (Gotcha 1) | A named platform path, confirmed from installed packages and Setup | No automation is built against objects the org does not have |
| "Who needs to create awards, who reviews reports, and do grantees use a portal?" | Access needs the licence, the feature, and Manage Funding Awards; portals use a separate permission set (Gotcha 2) | A permission set group per persona, including Experience Cloud users | Users see the objects on day one without hand-built permissions |
| "Which requirement status means what: the grantee's state, the review decision, or both?" | Requirements carry `Status` and `ApprovalStatus`, and Rejected is standard (Gotcha 3) | A field-meaning table and the standard values in use | Reports and automation read the same field for the same question |
| "Which payments wait for which reports, and who releases them?" | The requirement-to-disbursement link exists, but enforcement is your automation (Gotcha 5) | Requirement-to-tranche mapping and a release rule | A tranche cannot be marked Paid before its report is approved |
| "Do applications come through Individual Application or the Spring '26 Application Form model?" | Individual Application gets no future enhancements and needs an Application RecordType Config (Gotcha 7) | A chosen application model and its record type setup | New programmes start on the model that will keep improving |
| "How are amendments and multi-year terms recorded?" | One agreement is one award with master-detail tranches; changes go on amendments (Gotcha 8) | An amendment process and the award `Status` rule | Committed totals report once, not once per tranche |

What proper configuration adds over "just creating awards": one award per agreement with its tranches and requirements as children, statuses whose meaning is written down, and payment release tied to the reports that should gate it.

---

## Core Concepts

### Platform Path 1: NPSP Outbound Funds Module (OFM)

The Outbound Funds Module is a managed package, namespace `outfunds`, published as "a community developed and maintained Open Source Commons project." Its objects are `Funding_Program__c`, `Funding_Request__c`, `Funding_Request_Role__c`, `Disbursement__c`, `Requirement__c`, and `Review__c`. A grant is a Funding Request (with `Requested_Amount__c`, `Awarded_Amount__c`, `Status__c`, term dates, and rollups such as `Total_Disbursed__c`); disbursements and requirements are its children, and a requirement can look up the disbursement it relates to. An NPSP extension package (`outfundsnpspext`) links disbursements to NPSP General Accounting Units through `GAU_Expenditure__c`.

Key constraints of OFM:
- Status fields are package picklists; transitions are not governed by the platform.
- Support comes from the Open Source Commons community, not a Salesforce product line.
- OFM is not compatible with Grantmaking objects: moving between them is a data transformation.
- (Corrected: the earlier text said OFM ties grants to the Opportunity through a lookup and has no requirement object; the package source shows neither an Opportunity field on `Funding_Request__c` nor a missing requirement object.)

### Platform Path 2: Nonprofit Cloud for Grantmaking (Grantmaking)

Grantmaking is a platform feature available in Nonprofit Cloud for Grantmaking and Public Sector Solutions. Its standard objects include `FundingOpportunity`, `FundingAward`, `FundingAwardAmendment`, `FundingDisbursement`, `FundingAwardRequirement`, `FundingAwardRqmtSection`, `Budget` and related budget objects, and the application objects. The three objects most grant setups touch:

| Object | Key fields | Notes |
|---|---|---|
| `FundingAward` | `Amount` (total award), `AwardeeId` (business or person account), `ContactId`, `FundingOpportunityId`, `IndividualApplicationId` or `ApplicationFormId`, `StartDate`, `EndDate`, `Status` (Active, Cancelled, Completed) | One record per grant agreement |
| `FundingDisbursement` | `FundingAwardId` (master-detail), `Amount`, `ScheduledDate`, `DisbursementDate`, `IsApproved`, `PaymentMethodType`, `Status` (Scheduled, Pending Approval, Approved, Processing, Paid, Returned, Cancelled) | A payment "made or scheduled to be made"; no Draft value |
| `FundingAwardRequirement` | `FundingAwardId` (master-detail), `FundingDisbursementId`, `Type` (Combined Report, Contract, Financial Report, Narrative Report), `DueDate`, `AssignedContactId`, `AssignedUserId`, `Status` (Open, In Progress, Submitted, Delayed, Approved, Rejected), `ApprovalStatus` (New, In Review, Approved, Rejected), `IsSubmitted`, `SubmittedDate` | A deliverable or milestone for an award or a disbursement |

These are standard objects without package prefixes, available only with the Grantmaking licence, Grantmaking turned on, and the Manage Funding Awards permission. UNVERIFIED (2026-10-03): the earlier statement that Grantmaking is "part of the Agentforce Nonprofit product line as of 2024" was not found in a fetched source.

### Requirement Status Model

The earlier version of this skill described a fixed Open, Submitted, Approved lifecycle with no Rejected state; the NPC Guide documents six `Status` values and a separate `ApprovalStatus`. A workable convention: `Status` tracks where the deliverable is (Open, In Progress, Submitted, Delayed), and the reviewer's decision is recorded both in `ApprovalStatus` (In Review, Approved, Rejected) and by moving `Status` to Approved or Rejected. A rejected deliverable goes back to Open or In Progress for resubmission, with feedback in `Description`. Document whichever convention you choose.

### Architectural Incompatibility Between Platforms

OFM and Grantmaking share no common objects, no shared APIs, and no native migration path. An org moving from OFM to Grantmaking must:
1. Transform `outfunds__Funding_Request__c` → `FundingAward`
2. Transform `outfunds__Disbursement__c` → `FundingDisbursement`
3. Transform `outfunds__Requirement__c` → `FundingAwardRequirement`, mapping `Status__c` and `Type__c` values to the standard picklists
4. Re-map all Flows, reports, and automation that reference OFM API names

This is a data migration project, not a configuration toggle.

---

## Common Patterns

### Pattern: Multi-Tranche Disbursement Schedule in Grantmaking

**When to use:** The award pays in several scheduled tranches and the org uses Grantmaking.

**How it works:**
1. Create one `FundingAward` with `Amount` = the total award, `AwardeeId` = the grantee account, and `Status` = Active.
2. Create one `FundingDisbursement` per tranche with `Amount`, a future `ScheduledDate`, and `Status` = Scheduled.
3. Move each tranche through Pending Approval, Approved, Processing, and Paid, setting `DisbursementDate` when paid.
4. Set `FundingAward.Status` to Completed when every tranche is Paid or Cancelled (a Flow can do this).

**Why not the alternative:** Do not model tranches as separate `FundingAward` records: this breaks parent-child reporting and duplicates requirements.

### Pattern: Deliverable Tracking and Payment Gating With FundingAwardRequirement

**When to use:** Grantees must submit reports before later tranches are released.

**How it works:**
1. At award setup, create one `FundingAwardRequirement` per deliverable with `Type`, `DueDate`, `AssignedContactId` (grantee) or `AssignedUserId`, `Status` = Open, and `FundingDisbursementId` = the tranche it gates.
2. When the grantee submits, set `IsSubmitted`, `SubmittedDate`, and `Status` = Submitted; notify the grants manager.
3. The reviewer sets `ApprovalStatus` and `Status` to Approved or Rejected.
4. Enforce the gate: validation rules for same-record rules, and a record-triggered flow on `FundingDisbursement` that blocks `Status` = Paid while any requirement pointing at it is not Approved (`references/examples.md`, Example 3).

**Why not the alternative:** Tasks or Chatter posts produce no structured data, cannot be reported in aggregate, and cannot gate automation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is on NPSP, no Grantmaking licence | Outbound Funds Module (plus `outfundsnpspext` for GAU accounting) | Purpose-built package with requests, disbursements, and requirements |
| Org has the Grantmaking licence | Grantmaking (`FundingAward`, `FundingDisbursement`, `FundingAwardRequirement`) | Standard objects, applications, budgets, amendments, Experience Cloud components |
| Org is on Nonprofit Cloud but Grantmaking is NOT licensed | Do not use Grantmaking objects; evaluate OFM or buy the licence | The objects are not accessible without the licence |
| Org has the Grants Management managed package | Do not turn on Grantmaking in that org without a plan | Salesforce recommends against running both; Grantmaking cannot be turned off |
| Org needs to migrate from OFM to Grantmaking | Full data transformation project | No native migration path |
| New nonprofit org evaluating Salesforce for grantmaking | Grantmaking on the Spring '26 Application Form model | No migration cost; the model receiving enhancements |

---

## Recommended Workflow

1. **Identify the platform path**: Confirm installed namespaces (`npsp`, `outfunds`, Grants Management) and the Grantmaking licence; do not proceed until the path is unambiguous.
2. **Assess grant requirements**: Document tranches, deliverables and the tranches they gate, grantee portal access, application model, and reporting needs. Match them to the decision table above.
3. **Turn on and grant access**: For Grantmaking: Setup > Quick Find "Grantmaking" > Grantmaking Settings > turn on (irreversible); assign Grantmaking Manager (and Grantmaking for Experience Cloud for portal users) through permission set groups; configure the application model and, for Individual Application, the Application RecordType Config.
4. **Configure the data model**: Page layouts, field sets, and record types for awards, disbursements, and requirements; write down the requirement status convention.
5. **Build lifecycle automation**: Validation rules for same-record rules and a record-triggered flow for the disbursement gate (`references/examples.md`, Example 3); a flow to complete awards.
6. **Validate end to end and document**: Create a test award with tranches and requirements, walk every status, confirm reports, then record the platform path, picklist conventions, and automation for future support and migrations.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform path (OFM vs. Grantmaking vs. Grants Management) is confirmed in writing, not assumed
- [ ] Grantmaking licence, feature switch, and Manage Funding Awards permission are verified if Grantmaking objects are in use
- [ ] `FundingDisbursement` tranches are children of the correct `FundingAward` (not separate awards)
- [ ] Requirement status convention (`Status` and `ApprovalStatus`) is documented and automation follows it
- [ ] Gating requirements reference their tranche through `FundingDisbursementId`, and a Paid tranche cannot bypass them
- [ ] No OFM API names (`outfunds__`) appear in automation built for Grantmaking, and vice versa
- [ ] Reports and dashboards reference the correct object set for the chosen platform

---

## Salesforce-Specific Gotchas

The full list with sources is in `references/gotchas.md`. The ones that most often break a grants setup:

| Gotcha | Consequence |
|---|---|
| Three different grants products; Grantmaking cannot be turned off (Gotcha 1) | Enabling it in the wrong org is permanent and confuses users |
| Two requirement status fields, with Rejected standard (Gotcha 3) | The earlier "Open, Submitted, Approved only" model was wrong; reports disagree if fields are mixed |
| Disbursement statuses have no Draft (Gotcha 4) | Automation built on Draft never fires; use Scheduled |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform path decision record | Written confirmation of OFM vs. NC Grantmaking choice, with licensing and requirement rationale |
| FundingAward / OFM Funding Request configuration | Page layouts, field sets, record types, and picklist values for the chosen platform |
| FundingDisbursement tranche setup | Disbursement records per award with scheduled dates and status automation |
| FundingAwardRequirement workflow | Requirement records, status lifecycle automation, and disbursement gating logic |
| Grant management reports and dashboards | Standard reports on award pipeline, disbursement schedule, and requirement completion |

---

## Related Skills

- `npsp-vs-nonprofit-cloud-decision` — Use this skill first if the org has not yet decided between NPSP and Nonprofit Cloud; this grant skill assumes the platform path is already determined
- `npsp-program-management` — For tracking program delivery funded by grants (PMM Service Delivery vs. grant award records are separate data stacks)
- `gift-entry-and-processing` — For donor gift processing in NPSP; grant awards are not the same as donor gifts and use different objects
