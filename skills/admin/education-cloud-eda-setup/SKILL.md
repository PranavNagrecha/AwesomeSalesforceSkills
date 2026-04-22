---
name: education-cloud-eda-setup
description: "Education Cloud (EDA — Education Data Architecture) setup: student success hub, advisor workflows, enrollment management, academic data model. NOT for standard Service Cloud case management (use service-cloud-core-setup). NOT for Nonprofit Cloud data model (use nonprofit-cloud-vs-npsp-migration)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
tags:
  - education-cloud
  - eda
  - student-success
  - enrollment
  - industries
  - affiliation
  - program-plan
triggers:
  - "how do i set up education cloud eda in salesforce"
  - "student success hub advisor workflow configuration"
  - "eda account record types academic household business"
  - "contact-centric data model for higher education"
  - "program plan course connection term hierarchy"
  - "enrollment management and applicant-to-student conversion"
inputs:
  - EDA managed package version and intended Education Cloud features
  - Institution type (K-12, higher-ed, continuing-ed, multi-campus)
  - Academic cadence (terms vs trimesters vs rolling enrollment)
  - Advising model (caseload, cohort, or appointment-based)
outputs:
  - EDA account record type activation plan (Academic / Household / Business / Administrative)
  - Affiliation and Program Plan configuration for target programs
  - Term, Course, Course Offering, Course Connection object wiring
  - Advisor caseload sharing and case-routing scaffold
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Education Cloud EDA Setup

Activate when configuring Salesforce Education Cloud / EDA for a school, university, or other learning institution. EDA is a contact-centric data model layered on standard objects, wired to the Student Success Hub and Advisor Link applications. Getting the foundational records (Account record types, Affiliations, Program Plans) right on day one prevents years of downstream reporting pain.

## Before Starting

- **Confirm EDA package version.** Education Cloud features and Student Success Hub assume a minimum EDA version; a stale managed package will leave fields and triggers missing.
- **Decide the Account model.** EDA uses FOUR Account record types: Academic Program, Household, Business Organization, Administrative. You must pick the model before any Contact load — Account defaults are used by the EDA triggers for auto-creation.
- **Know the academic cadence.** Term/Course/Course Offering/Course Connection modeling depends on whether the institution runs semesters, trimesters, quarters, or rolling enrollment.

## Core Concepts

### Contact-centric model

In EDA, the Contact is the primary record. Students, advisors, parents, faculty, and staff are all Contacts with different Affiliations. A Contact can have many Account relationships through `Affiliation__c`, including Primary Academic, Primary Business, Household, and Sports affiliations.

### Program Plan / Plan Requirement

Academic programs are modeled as `Program_Plan__c` records with nested `Plan_Requirement__c` children. This is how EDA expresses "to graduate, a student must complete these courses." Advisor Link uses this structure to generate checklists.

### Term / Course / Course Offering / Course Connection

`Term__c` defines the academic period. `Course__c` is the catalog-level record. `Course_Offering__c` is a specific instance of a course in a specific Term. `Course_Connection__c` links a Contact (student or faculty) to a `Course_Offering__c`. This is a four-level model and all four are required; skipping the split breaks Advisor Link reports.

## Common Patterns

### Pattern: Applicant to student conversion

Represent applicants as `Contact` with `Affiliation__c.Status = 'Prospect'` to the target Academic Program. On admission, flip `Status = 'Current'` and add the Primary Academic Account. Do NOT create a separate `Applicant__c` custom object — it breaks Advisor Link assumptions.

### Pattern: Term rollover

At term-end, `Course_Connection__c` records carry grades. Do not delete them — new connections for the next term are net-new inserts. A term-rollover Flow creates next-term `Course_Offering__c` records from the catalog `Course__c` and pulls forward enrolled students.

### Pattern: Advisor caseload

Advisors have a `Caseload__c` junction to Contacts. Sharing on Contact respects the Household + Academic hierarchy; advisors are given Caseload-based sharing through an Apex-managed sharing trigger or criteria-based rules.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New program launch | Program_Plan + Plan_Requirement tree | Advisor Link discovers programs this way |
| Multi-campus institution | Separate Academic Program Accounts per campus | Enables reporting by campus |
| K-12 vs higher-ed | Same EDA model, different record type usage | Avoid forking the schema |
| Alumni engagement | Keep Contact + Affiliation Status = 'Former' | Preserves history without deleting |

## Recommended Workflow

1. Verify EDA managed package is installed and at the supported version; review release notes for upgrade-impacting trigger changes.
2. Activate the four Account record types and set defaults for auto-Household creation (EDA Settings → Accounts).
3. Configure Affiliation mappings: Primary Academic, Primary Business, Household — these drive auto-population on Contact.
4. Load Academic Program Accounts and Program Plans before any student data.
5. Import Contacts with a staged ETL: prospects → admitted → enrolled; each stage triggers Affiliation changes that EDA automation expects.
6. Set up Term, Course, Course Offering, Course Connection objects; deploy a term-rollover Flow before the first term-end.
7. Install Student Success Hub / Advisor Link apps, configure caseload sharing, and run a round-trip advisor check.

## Review Checklist

- [ ] Four Account record types active and default behavior verified
- [ ] Affiliation settings mapped to correct primary types
- [ ] Program Plan + Plan Requirement hierarchy created for every active program
- [ ] Term rollover automation in place before first term boundary
- [ ] Advisor caseload sharing resolves to expected Contact set for a test advisor
- [ ] Field History tracking on Affiliation Status (audit trail for FERPA)
- [ ] Guest user hardening on any applicant-facing Experience Cloud portal

## Salesforce-Specific Gotchas

1. **EDA triggers run on Contact insert.** A bulk Contact load without the Primary Academic Account resolved in advance creates orphan Affiliations that advisors cannot see.
2. **`Course_Connection__c` is the grade holder.** Copying prior-term grades to `Course_Offering__c` is a common LLM mistake; grade history lives only on Course Connection.
3. **Household Account auto-creation is irreversible at scale.** Once EDA creates Household accounts for a Contact batch, turning it off does not tear them down — test on a sandbox sample first.

## Output Artifacts

| Artifact | Description |
|---|---|
| EDA activation runbook | Ordered steps, package version gate, record type plan |
| Term rollover Flow | Automates course offering generation each term |
| Affiliation mapping table | Institution-specific Primary Account mapping |
| Advisor caseload sharing spec | Apex-managed or criteria-based sharing rules |

## Related Skills

- `admin/experience-cloud-site-setup` — student/applicant portal
- `admin/nonprofit-cloud-vs-npsp-migration` — sibling industry model context
- `data/eda-data-model-and-patterns` — data loader patterns for EDA
- `security/experience-cloud-guest-user-hardening` — applicant portal safety
