---
name: education-cloud-eda-setup
description: "Education Cloud (EDA — Education Data Architecture) setup: student success hub, advisor workflows, enrollment management, academic data model. NOT for the EDA object model in depth (Affiliations, Course_Connection__c) — use data/eda-data-model-and-patterns. NOT for SIS enrollment sync — use integration/sis-integration-patterns."
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
status: stub
---

# Education Cloud EDA Setup

Activate when configuring Salesforce Education Cloud / EDA for a school, university, or other learning institution. EDA is a contact-centric data model layered on standard objects, wired to the Student Success Hub and Advisor Link applications. Getting the foundational records (Account record types, Affiliations, Program Plans) right on day one prevents years of downstream reporting pain.

## Before Starting

- **Confirm which model the institution is on.** "Education Cloud" and EDA are two different data models, not two names for one. EDA is a managed package of custom objects — "a community-driven data architecture that supports the entire K-20 student journey" — while modern Education Cloud ships **standard** objects (`AcademicTerm`, `AcademicTermEnrollment`, `CourseOfferingParticipant`, `LearningProgram`, `LearningProgramPlan`, `LearnerProgram`). Establish which one is installed before writing a single API name.
- **Confirm EDA package version.** Student Success Hub and Advisor Link assume a minimum EDA version; a stale managed package will leave fields and triggers missing. Because EDA objects live in a managed package, every API name carries the package namespace prefix and a `__c` suffix — copy the exact name from the installed package rather than assuming the label form resolves.
- **Decide the Account model.** EDA uses FOUR Account record types: Academic Program, Household, Business Organization, Administrative. You must pick the model before any Contact load — Account defaults are used by the EDA triggers for auto-creation.
- **Know the academic cadence.** Term/Course/Course Offering/Course Connection modeling depends on whether the institution runs semesters, trimesters, quarters, or rolling enrollment.

## Core Concepts

### Contact-centric model

In EDA, the Contact is the primary record. Students, advisors, parents, faculty, and staff are all Contacts with different Affiliations. A Contact can have many Account relationships through the **Affiliation** object, including Primary Academic, Primary Business, Household, and Sports affiliations. Which affiliation types auto-populate is not hard-coded — it is configuration held in the **Affiliation Mappings** object, alongside **Hierarchy Settings**, **Relationship Auto-Create**, and **Relationship Lookup**.

### Program Plan / Plan Requirement

Academic programs are modeled as **Program Plan** records with nested **Plan Requirement** children. This is how EDA expresses "to graduate, a student must complete these courses." Advisor Link uses this structure to generate checklists. On the Education Cloud standard model the equivalents are `LearningProgramPlan` ("details of a plan created to execute a Learning Program") and `LearningProgramPlanRqmt`, with `LearnerProgram` holding the per-learner instance.

### Term / Course / Course Offering / Course Connection

**Term** defines the academic period. **Course** is the catalog-level record. **Course Offering** is a specific instance of a course in a specific Term. **Course Connection** links a Contact (student or faculty) to a Course Offering. This is a four-level model and all four are required; skipping the split breaks Advisor Link reports. The Education Cloud standard model expresses the same four levels differently — `AcademicTerm` ("Defines an academic period which may hold other more defined time periods"), `Learning` / `LearningCourse`, `CourseOfferingSchedule`, and `CourseOfferingParticipant` ("information about a student's enrollment in a Course Offering") — with `AcademicTermEnrollment` carrying per-term enrollment status.

## Common Patterns

### Pattern: Applicant to student conversion

Represent applicants as `Contact` with an Affiliation whose status is `Prospect` to the target Academic Program. On admission, flip it to `Current` and add the Primary Academic Account. Do NOT create a separate `Applicant__c` custom object — it breaks Advisor Link assumptions. (On the standard Education Cloud model, admissions has its own object family: `ApplicationStageDefinition`, `ApplicationSectionDefinition`, `ApplicationReview`, `ApplicationDecision` — "information about the academic standing of an applicant" — and `ApplicationTimeline`.)

### Pattern: Term rollover

At term-end, Course Connection records carry grades. Do not delete them — new connections for the next term are net-new inserts. A term-rollover Flow creates next-term Course Offering records from the catalog Course and pulls forward enrolled students.

### Pattern: Advisor caseload

Advisors are related to their students through an Affiliation or a caseload junction, depending on the institution's model — confirm the exact object in the installed package rather than assuming a name. Sharing on Contact respects the Household + Academic hierarchy; advisors are given caseload-based sharing through an Apex-managed sharing trigger or criteria-based rules. On the standard model, `SuccessTeam` "Records details about a success team in Salesforce Scheduler" and `WatchlistedLearner` "Represents information for a learner that needs to be monitored for support."

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New program launch | Program Plan + Plan Requirement tree (EDA) / `LearningProgramPlan` + `LearningProgramPlanRqmt` (standard) | Advisor Link discovers programs this way |
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
2. **Course Connection is the grade holder.** Copying prior-term grades onto Course Offering is a common LLM mistake; grade history lives only on Course Connection. On the standard model the equivalents are `CourseOfferingPtcpResult` ("the outcome of a student's participation in a course") and `CourseOfrPtcpActvtyGrd`.
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
- `architect/nonprofit-cloud-vs-npsp-migration` — sibling industry model context
- `data/eda-data-model-and-patterns` — data loader patterns for EDA
- `security/guest-user-security` — applicant portal safety
