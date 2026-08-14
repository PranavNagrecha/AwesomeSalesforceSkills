---
name: industries-public-sector-setup
description: "Public Sector Solutions (PSS) setup: licensing, permits, inspections, benefits, case management for government, citizen portals, and grant management. NOT for standard Service Cloud cases — use admin/case-management-setup. NOT for a plain portal site — use admin/experience-cloud-site-setup."
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
  - "pss contact centric model programs and applications"
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
status: stub
---

# Industries Public Sector Setup

Activate when configuring Salesforce Public Sector Solutions (PSS) for a government agency: issuing licenses or permits, routing citizen cases, managing benefit enrollments, running inspections, or standing up grant programs. PSS is not a single feature — it is a licensed industry bundle that layers on top of Service Cloud, Experience Cloud, and OmniStudio.

## Before Starting

- **Confirm the PSS license is provisioned.** Features like `BenefitDisbursement`, `BusinessLicenseApplication`, and the out-of-the-box OmniScripts ship only when PSS is enabled.
- **Identify the regulatory framework.** Public-sector programs usually have statutory timelines, audit requirements, and disclosure rules that drive field-level encryption and audit trail decisions.
- **Decide the citizen channel mix early.** PSS expects a mix of portal, phone, email, and paper; each channel implies different intake automation (OmniScript vs Web-to-Case vs Email-to-Case).

## Core Concepts

### PSS-specific data model

"The Public Sector Solutions data models provide objects and fields to support licensing and permitting, inspections and assessments, case and program management, benefit management, grantmaking, and other features for your organization." All of it is **standard**. You do NOT recreate these with custom objects; you configure the shipped ones.

- **Licensing and permitting:** `BusinessLicense`, `BusinessLicenseApplication`, `BusinessLicenseCodeSet`, `BusinessProfile`, `BusinessType`, `BusRegAuthorizationType`, `BusRegAuthTypeDependency`, `RegulatoryAuthority`, `RegulatoryAuthorizationType`, `RegulatoryCode` ("the regulation code enforced by the regulatory body", API 49.0+), `RegAuthorizationTypeProduct`, `Examination`, `TrnCourse`, `InspectionType`. Individual-side intake is `IndividualApplication` — "an application form submitted by an individual or organization" (API 50.0+).
- **Inspections and assessments:** `Visit`, `Visitor`, `VisitedParty`, `AssessmentTask`, `AssessmentTaskDefinition`, `AssessmentIndicatorDefinition`, `AssessmentIndValue`, `RegulatoryCodeViolation`, `ViolationType`, `ViolationEnforcementAction`, `RegCodeAssessmentInd`.
- **Benefit management:** `Benefit`, `BenefitType`, `BenefitAssignment`, `BenefitAssignmentAdjustment`, `BenefitDisbursement`, `BenefitDisbursementAdj`, `BenefitSchedule`, `BenefitScheduleAssignment`, `BenefitSession`, `BenefitItemCode`.
- **Grantmaking:** `FundingOpportunity`, `FundingAward`, `FundingAwardAmendment`, `FundingAwardParticipant`, `FundingAwardRequirement`, `FundingDisbursement`.
- **Case and program management:** `Program`, `ProgramEnrollment`, `ProgramCohortMember`, `CarePlan`, `CarePlanTemplate`, `CaseParticipant`, `CaseProceeding`, `CaseProgram`, `CaseEpisode`.

### OmniStudio is mandatory

PSS intake, decisioning, and citizen journeys ship as OmniScripts, Integration Procedures, and DataRaptors. Admin work that would be Flow-first in Sales/Service is Omni-first in PSS. Do not replace a shipped OmniScript with a Flow unless you have a specific reason — you will inherit upgrade drift.

### Multi-jurisdiction sharing

Public-sector agencies almost always have nested jurisdictional ownership (state → county → municipal). PSS uses a combination of Role Hierarchy, Account hierarchies on `Account` with record type `Agency`, and criteria-based sharing on regulatory objects. Build the org with jurisdiction in mind before loading the first case — retrofitting is painful.

## Common Patterns

### Pattern: License application with fee and approval

Use the shipped `BusinessLicenseApplication` object (or `IndividualApplication` for an individual applicant), Approval Process, and payment integration. Drive intake through OmniScript → DataRaptor → Apex invocable that creates the application record; the granted artefact is a `BusinessLicense`, typed by `RegulatoryAuthorizationType`. Fees flow through a Payment Gateway external credential, not custom Apex HTTP callouts.

### Pattern: Inspections with offline-capable mobile

Inspectors need Field Service Mobile or the PSS Inspector mobile experience. Inspections use the shipped visit/assessment model — `InspectionType` classifies them, `Visit` records the site call, `AssessmentTask` and `AssessmentIndicatorDefinition` carry the checklist, `AssessmentIndValue` the captured values. Findings become `RegulatoryCodeViolation` (classified by `ViolationType`), and follow-up is a `ViolationEnforcementAction`. Use Field Service scheduling if dispatch is needed; plain task assignments if routes are self-planned.

### Pattern: Benefit enrollment with eligibility decisioning

`IndividualApplication` → `BenefitAssignment` → `BenefitDisbursement`, with `Benefit` and `BenefitType` as the catalogue and `BenefitSchedule` / `BenefitScheduleAssignment` setting the disbursement cadence. Eligibility rules ship as a Business Rules Engine (BRE) expression set — do NOT hand-code eligibility in Apex or Flow; BRE is auditable, versioned, and expected by the shipped OmniScripts.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| License or permit with fee | `BusinessLicenseApplication` + Approval + BRE | Shipped flow; avoids custom rebuild |
| Citizen case intake | OmniScript + Case record type | Matches PSS intake templates |
| Eligibility scoring | Business Rules Engine (BRE) | Auditable, versioned, shipped expectation |
| Multi-agency data partitioning | Role hierarchy + criteria sharing on Agency Account | Matches jurisdictional reality |
| Inspector field work | Field Service + `InspectionType` / `Visit` / `AssessmentTask` | Offline-capable, dispatch ready |

## Recommended Workflow

1. Confirm PSS license is active and all dependent permission set groups (`PublicSectorAccess`, `OmniStudioUser`) are available.
2. Activate the PSS-required objects via `Setup → Public Sector → Feature Settings` before any data load.
3. Build or clone the shipped OmniScripts for the intake channels actually in use; deactivate the ones you do not use to reduce upgrade noise.
4. Configure Role Hierarchy and Agency account hierarchy BEFORE loading any case, license, or party data — these drive all downstream sharing.
5. Stand up the citizen portal with guest user hardened per Experience Cloud guest security guide; wire OmniScripts to the portal pages.
6. Load reference data (`RegulatoryCode`, `RegulatoryAuthority`, `RegulatoryAuthorizationType`, `BusinessType`, `InspectionType`, `ViolationType`, `BenefitType`) before transactional data.
7. Smoke test a citizen journey end-to-end (intake → approval → payment → disbursement or issuance) before go-live.

## Review Checklist

- [ ] PSS license provisioned and feature settings activated
- [ ] Role hierarchy + Agency account hierarchy reflect jurisdictional model
- [ ] Shipped OmniScripts either used or explicitly deactivated (not silently duplicated)
- [ ] Eligibility logic in BRE, not Apex or Flow
- [ ] Citizen portal guest user follows guest-user hardening guide
- [ ] Audit field history enabled on `BusinessLicenseApplication`, `IndividualApplication`, `BenefitDisbursement`, `RegulatoryCodeViolation`
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

- `admin/case-management-setup` — underlying Service Cloud case layer
- `admin/experience-cloud-site-setup` — citizen portal foundations
- `omnistudio/omniscript-design-patterns` — PSS intake layer (pair with `omnistudio/flexcard-design-patterns` for the case-worker UX)
- `security/guest-user-security` — portal security
