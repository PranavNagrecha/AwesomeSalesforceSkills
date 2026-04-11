---
name: grant-management-setup
description: "Use when configuring grant tracking in a Salesforce nonprofit org — covers both NPSP Outbound Funds Module (Opportunity-based, managed package path) and Nonprofit Cloud for Grantmaking (FundingAward, FundingDisbursement, FundingAwardRequirement objects, separate license). Trigger keywords: grant management, funding awards, disbursement tranches, grantmaking setup, OFM, FundingAward, FundingDisbursement, FundingAwardRequirement. NOT for standard Opportunity tracking or fundraising donor gifts."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up grant tracking in our NPSP org?"
  - "We need to track funding award disbursements by tranche — which Salesforce platform should we use?"
  - "What is the difference between NPSP Outbound Funds Module and Nonprofit Cloud for Grantmaking?"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Grant Management Setup

This skill activates when a practitioner needs to configure grant tracking in a Salesforce nonprofit org. It covers both available platform paths — NPSP Outbound Funds Module (OFM) and Nonprofit Cloud for Grantmaking — and provides the decision logic, object model orientation, and configuration steps for each.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which platform is installed?** Run a SOQL query or check Installed Packages: NPSP (managed package `npsp`) vs. Nonprofit Cloud (NPC). These are architecturally incompatible. Do not mix guidance between them.
- **Is Nonprofit Cloud for Grantmaking licensed?** This is a separately licensed product within NPC. Even orgs on NPC may not have it provisioned. Verify in Setup → Company Information → Licenses or confirm with the org's Account Executive.
- **What is the grant disbursement model?** Single lump-sum payment vs. multi-tranche scheduled disbursements determines whether the simpler OFM path suffices or whether FundingDisbursement tranches are needed.
- **Are deliverables or requirements tracked per award?** FundingAwardRequirement exists only in Nonprofit Cloud for Grantmaking. OFM has no native deliverable-tracking object.

---

## Core Concepts

### Platform Path 1: NPSP Outbound Funds Module (OFM)

The Outbound Funds Module is a separate managed package (originally open-source, now Salesforce-maintained) that runs on top of NPSP. It uses the `outfunds__Funding_Request__c` and `outfunds__Disbursement__c` objects and ties grant tracking to the Opportunity record via a lookup. The data model is Opportunity-centric: a grant award is represented as a Funding Request linked to an Opportunity, and disbursements are child records of the Funding Request.

Key constraints of OFM:
- No native deliverable/requirement tracking object — organizations must build custom objects or use Chatter/Tasks for deliverable management.
- Status fields on Funding Request are picklists with no enforced lifecycle; transitions are not platform-governed.
- Reporting surfaces through standard NPSP dashboards only if relationships are correctly mapped.
- OFM is not compatible with Nonprofit Cloud for Grantmaking objects — you cannot migrate data between them without full data transformation.

### Platform Path 2: Nonprofit Cloud for Grantmaking (NC Grantmaking)

Nonprofit Cloud for Grantmaking (part of the Agentforce Nonprofit product line as of 2024) uses three purpose-built objects that replace the OFM data model entirely:

- **FundingAward** — the top-level grant award record. Stores the awarded amount, funding source, grantee (Account), and overall status. Replaces `outfunds__Funding_Request__c`.
- **FundingDisbursement** — a child of FundingAward representing a single payment tranche. One FundingAward can have many FundingDisbursements, each with its own scheduled date, amount, and payment status. This is the correct object for multi-tranche grant disbursements.
- **FundingAwardRequirement** — a child of FundingAward representing a deliverable, report, or compliance condition tied to the award. Has a platform-governed status lifecycle: **Open → Submitted → Approved**. Each requirement has a due date, assignee, and type (e.g., Progress Report, Final Report, Site Visit).

These objects are standard Salesforce objects on the NPC data model, not custom objects from a managed package. They are governed by Salesforce's object permission model and can be used in standard reports, flows, and Apex without managed-package API name prefixes.

### FundingAwardRequirement Status Lifecycle

The status field on FundingAwardRequirement follows a fixed, platform-intended progression:

1. **Open** — the requirement has been created and is pending action from the grantee or internal staff.
2. **Submitted** — the grantee has submitted the deliverable (e.g., uploaded a report); internal review is pending.
3. **Approved** — the deliverable has been reviewed and accepted; the requirement is closed.

There is no "Rejected" terminal state in the standard lifecycle — rejected submissions should revert to Open with notes, or organizations can extend the picklist. Do not treat this lifecycle as freely customizable without documenting the deviation.

### Architectural Incompatibility Between Platforms

OFM and Nonprofit Cloud for Grantmaking share no common objects, no shared APIs, and no native migration path. An org running NPSP + OFM that migrates to NPC must:
1. Transform `outfunds__Funding_Request__c` → `FundingAward`
2. Transform `outfunds__Disbursement__c` → `FundingDisbursement`
3. Build net-new `FundingAwardRequirement` records (no OFM equivalent)
4. Re-map all Flows, reports, and automation that reference OFM API names

This is a data migration project, not a configuration toggle.

---

## Common Patterns

### Pattern: Multi-Tranche Disbursement Schedule in NC Grantmaking

**When to use:** The grant award requires multiple scheduled payments (quarterly disbursements, milestone-based tranches) and the org is on Nonprofit Cloud for Grantmaking.

**How it works:**
1. Create a `FundingAward` record with total awarded amount and grantee Account.
2. Create one `FundingDisbursement` child record per tranche. Set `ScheduledDate`, `DisbursementAmount`, and `Status` (Draft → Scheduled → Paid).
3. Build a Flow or approval process to update `FundingAward.Status` when all `FundingDisbursement` records reach "Paid."
4. Report on disbursement pipeline using standard FundingDisbursement list views filtered by ScheduledDate.

**Why not the alternative:** Do not model tranches as separate FundingAward records — this breaks parent-child rollup reporting and severs the link between award terms and disbursements.

### Pattern: Deliverable Tracking Using FundingAwardRequirement

**When to use:** Grants require grantees to submit interim reports, final reports, or site visit confirmations before disbursements are released.

**How it works:**
1. Create `FundingAwardRequirement` records linked to the parent `FundingAward` at award setup time.
2. Assign each requirement a `Type` (Progress Report, Final Report, Site Visit), a `DueDate`, and an `AssignedTo` user or queue.
3. Use a Flow triggered on `FundingAwardRequirement.Status = Submitted` to notify the grants manager for review.
4. Grants manager approves — status advances to Approved. Gate disbursement release using a validation rule or Flow that checks all requirements are Approved before a FundingDisbursement can move to "Paid."

**Why not the alternative:** Using Tasks or Chatter posts for deliverable tracking produces no structured data, cannot be reported on in aggregate, and cannot be used as a gating condition in automation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is on NPSP (managed package), no NPC license | NPSP Outbound Funds Module (OFM) | OFM is the only purpose-built grant tracking tool available on the NPSP platform |
| Org is on Nonprofit Cloud with Grantmaking license | Nonprofit Cloud for Grantmaking (FundingAward/FundingDisbursement/FundingAwardRequirement) | Purpose-built objects, enforced status lifecycle, native platform governance |
| Org is on Nonprofit Cloud but Grantmaking is NOT licensed | Do not use NC Grantmaking objects; evaluate OFM on NPC or custom objects | FundingAward and related objects are not accessible without the Grantmaking license |
| Org needs multi-tranche disbursements with deliverable gating | Nonprofit Cloud for Grantmaking | FundingDisbursement + FundingAwardRequirement provide native tranche and deliverable tracking; OFM requires heavy customization for the same |
| Org needs to migrate from OFM to NC Grantmaking | Full data transformation project required | No native migration path; all OFM objects and automation must be rebuilt on NC objects |
| New nonprofit org evaluating Salesforce for grantmaking | Implement Nonprofit Cloud for Grantmaking directly | No migration cost; immediately accesses purpose-built Grantmaking data model |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the platform path** — Confirm whether the org runs NPSP (check for `npsp` namespace in Installed Packages) or Nonprofit Cloud (check for NPC license). Confirm whether Nonprofit Cloud for Grantmaking is separately licensed. Do not proceed until the platform path is unambiguous.
2. **Assess grant requirements** — Document whether the org needs: (a) single lump-sum vs. multi-tranche disbursements, (b) deliverable/requirement tracking per award, (c) grantee portal access, and (d) reporting integration with fundraising data. Match requirements to the decision matrix above.
3. **Configure the data model for the chosen path** — For OFM: install the Outbound Funds Module managed package, configure Funding Request and Disbursement page layouts, and map the Funding Request lookup to the Opportunity. For NC Grantmaking: configure FundingAward, FundingDisbursement, and FundingAwardRequirement page layouts, field sets, and record types per award program.
4. **Build status lifecycle automation** — For NC Grantmaking: build Flows to govern FundingAwardRequirement status transitions (Open → Submitted → Approved) and to block FundingDisbursement payment release until requirements are met. For OFM: build Flows on Funding Request and Disbursement status picklists (no platform-enforced lifecycle).
5. **Validate with end-to-end test data** — Create a test FundingAward (or OFM Funding Request), add disbursement tranches, create requirements, walk through the full status lifecycle, and confirm reporting surfaces correctly in standard reports and dashboards.
6. **Document the platform path and customizations** — Record which platform path the org uses, all customized picklist values, all automation built on top of the standard lifecycle, and any deviations from the standard FundingAwardRequirement progression. This documentation is critical for future migrations and support.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Platform path (OFM vs. NC Grantmaking) is confirmed in writing — not assumed
- [ ] Nonprofit Cloud for Grantmaking license is verified if NC objects are in use
- [ ] FundingDisbursement tranches are linked to the correct parent FundingAward (not separate awards)
- [ ] FundingAwardRequirement status lifecycle (Open → Submitted → Approved) is not bypassed by automation
- [ ] No OFM API names (outfunds__) appear in automation built for NC Grantmaking, and vice versa
- [ ] Reports and dashboards reference the correct object set for the chosen platform
- [ ] Migration incompatibility is documented if there is any future plan to move between platforms

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Nonprofit Cloud for Grantmaking requires a separate license** — Being on Nonprofit Cloud (NPC) does not automatically grant access to FundingAward, FundingDisbursement, or FundingAwardRequirement objects. These are gated behind a separate Grantmaking product license. Attempting to use these objects in an unlicensed org produces object-not-found errors that are indistinguishable from misconfiguration.
2. **OFM and NC Grantmaking are architecturally incompatible** — There is no supported migration path between the two platforms. Data transformation is required for every object type, and all automation, reports, and Flows must be rebuilt from scratch. Do not plan an "upgrade" as if it is a configuration change.
3. **FundingAwardRequirement status is a fixed picklist, not a configurable workflow** — The Open → Submitted → Approved progression is the standard intended lifecycle. Adding custom picklist values (e.g., "Rejected," "On Hold") is technically possible but breaks standard Flow templates and Trailhead guidance. Deviations must be intentional and documented.

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
