---
name: industries-public-sector-setup
description: "Public Sector Solutions (PSS) setup: licensing, permits, inspections, benefits, case management for government, citizen portals, and grant management. NOT for standard Service Cloud case management (use service-cloud-core-setup). NOT for generic Experience Cloud portals (use experience-cloud-site-setup)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - public-sector
  - industries
  - licensing
  - permits
  - benefits
  - grants
  - omnistudio
triggers:
  - "how do i set up public sector solutions in salesforce"
  - "licensing and permitting module configuration"
  - "citizen case intake and benefits management"
  - "grant management object model in pss"
  - "pss license application approval workflow"
  - "public sector inspections and enforcement setup"
inputs:
  - Target cloud/edition (PSS license assigned, base Service Cloud present)
  - Business process in scope (license, permit, inspection, benefit, grant)
  - Agency jurisdictional levels and record ownership model
  - Citizen channel list (portal, phone, paper, email)
outputs:
  - PSS object model activation checklist
  - License/permit type and approval routing configuration
  - Omni-Channel and case queue setup for citizen intake
  - Citizen portal profile, sharing, and guest-user hardening notes
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Industries Public Sector Setup

Activate when configuring Salesforce Public Sector Solutions (PSS) for a government agency: issuing licenses or permits, routing citizen cases, managing benefit enrollments, running inspections, or standing up grant programs. PSS is not a single feature — it is a licensed industry bundle that layers on top of Service Cloud, Experience Cloud, and OmniStudio.

## Before Starting

- **Confirm the PSS license is provisioned.** Features like `BenefitDisbursement`, `LicenseApplication`, and the out-of-the-box OmniScripts ship only when PSS is enabled.
- **Identify the regulatory framework.** Public-sector programs usually have statutory timelines, audit requirements, and disclosure rules that drive field-level encryption and audit trail decisions.
- **Decide the citizen channel mix early.** PSS expects a mix of portal, phone, email, and paper; each channel implies different intake automation (OmniScript vs Web-to-Case vs Email-to-Case).

## Core Concepts

### PSS-specific data model

PSS adds purpose-built objects: `LicenseApplication`, `RegulatoryCode`, `Case` record types for permit/inspection/enforcement, `Authorization`, `BusinessLicense`, `Party`, `PartyRelationship`, plus benefit objects (`IndividualApplication`, `Benefit`, `BenefitDisbursement`). You do NOT recreate these with custom objects; you configure the shipped objects.

### OmniStudio is mandatory

PSS intake, decisioning, and citizen journeys ship as OmniScripts, Integration Procedures, and DataRaptors. Admin work that would be Flow-first in Sales/Service is Omni-first in PSS. Do not replace a shipped OmniScript with a Flow unless you have a specific reason — you will inherit upgrade drift.

### Multi-jurisdiction sharing

Public-sector agencies almost always have nested jurisdictional ownership (state → county → municipal). PSS uses a combination of Role Hierarchy, Account hierarchies on `Account` with record type `Agency`, and criteria-based sharing on regulatory objects. Build the org with jurisdiction in mind before loading the first case — retrofitting is painful.

## Common Patterns

### Pattern: License application with fee and approval

Use the shipped `LicenseApplication` object, Approval Process, and payment integration. Drive applicant intake through OmniScript → DataRaptor → Apex invocable that creates the `LicenseApplication`. Fees flow through a Payment Gateway external credential, not custom Apex HTTP callouts.

### Pattern: Inspections with offline-capable mobile

Inspectors need Field Service Mobile or the PSS Inspector mobile experience. Inspections are `Case` records with record type `Inspection`, tied to an `Asset` (the inspected facility or permit). Use Field Service scheduling if dispatch is needed; use plain task assignments if routes are self-planned.

### Pattern: Benefit enrollment with eligibility decisioning

`IndividualApplication` → `Benefit` → `BenefitDisbursement`. Eligibility rules ship as a Business Rules Engine (BRE) expression set — do NOT hand-code eligibility in Apex or Flow; BRE is auditable, versioned, and expected by the shipped OmniScripts.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| License or permit with fee | LicenseApplication + Approval + BRE | Shipped flow; avoids custom rebuild |
| Citizen case intake | OmniScript + Case record type | Matches PSS intake templates |
| Eligibility scoring | Business Rules Engine (BRE) | Auditable, versioned, shipped expectation |
| Multi-agency data partitioning | Role hierarchy + criteria sharing on Agency Account | Matches jurisdictional reality |
| Inspector field work | Field Service + Case record type `Inspection` | Offline-capable, dispatch ready |

## Recommended Workflow

1. Confirm PSS license is active and all dependent permission set groups (`PublicSectorAccess`, `OmniStudioUser`) are available.
2. Activate the PSS-required objects via `Setup → Public Sector → Feature Settings` before any data load.
3. Build or clone the shipped OmniScripts for the intake channels actually in use; deactivate the ones you do not use to reduce upgrade noise.
4. Configure Role Hierarchy and Agency account hierarchy BEFORE loading any case, license, or party data — these drive all downstream sharing.
5. Stand up the citizen portal with guest user hardened per Experience Cloud guest security guide; wire OmniScripts to the portal pages.
6. Load reference data (`RegulatoryCode`, license types, permit types) before transactional data.
7. Smoke test a citizen journey end-to-end (intake → approval → payment → disbursement or issuance) before go-live.

## Review Checklist

- [ ] PSS license provisioned and feature settings activated
- [ ] Role hierarchy + Agency account hierarchy reflect jurisdictional model
- [ ] Shipped OmniScripts either used or explicitly deactivated (not silently duplicated)
- [ ] Eligibility logic in BRE, not Apex or Flow
- [ ] Citizen portal guest user follows guest-user hardening guide
- [ ] Audit field history enabled on `LicenseApplication`, `BenefitDisbursement`, `Case`
- [ ] Reference data loaded before transactional data

## Salesforce-Specific Gotchas

1. **PSS shipped OmniScripts get overwritten on upgrade.** Customizing them in place means upgrades silently revert your changes. Always clone and use versioning.
2. **Business Rules Engine is licensed separately in some editions.** Confirm BRE entitlement before designing eligibility around it.
3. **Agency Account record type is mandatory.** Converting existing `Account` records to use the Agency hierarchy after the fact triggers a sharing recalculation that can take hours on large orgs.

## Output Artifacts

| Artifact | Description |
|---|---|
| PSS activation runbook | Ordered steps from license confirmation to go-live |
| Jurisdiction model diagram | Role + Account hierarchy matched to the agency's statutory structure |
| Intake OmniScript catalog | List of shipped OmniScripts in use vs deactivated |
| BRE expression set inventory | Eligibility rules by program |

## Related Skills

- `admin/service-cloud-core-setup` — underlying Service Cloud layer
- `admin/experience-cloud-site-setup` — citizen portal foundations
- `omnistudio/omniscript-flexcard-basics` — PSS intake/UX layer
- `security/experience-cloud-guest-user-hardening` — portal security
